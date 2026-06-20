import random
import os
import json
from typing import Optional, List
from ..models.state import GameRun, PlayerState, EnemyState, Card, MinionState, AmuletState, BuffState
from .battle.base import BaseBattleEngine
from .battle.combat_resolver import CombatResolver
from .battle.card_player import CardPlayer
from .battle.duel_observers import BuffTriggerHandler, AmuletTriggerHandler, MinionTriggerHandler
from ..models.events import DamageCalculateEvent, CardPlayedEvent, DamageTakeEvent, ShieldGainEvent

class DuelEngine(BaseBattleEngine):
    def __init__(self, save_manager):
        super().__init__(save_manager)
        self.combat_resolver = CombatResolver(self)
        self.card_player = CardPlayer(self)
        self.buff_handler = BuffTriggerHandler(self.event_bus, self)
        self.amulet_handler = AmuletTriggerHandler(self.event_bus, self)
        self.minion_handler = MinionTriggerHandler(self.event_bus, self)
        self.event_bus.subscribe(CardPlayedEvent, self.on_card_played_quests_and_double_tap)
        self.event_bus.subscribe(DamageTakeEvent, self.on_damage_take_quests)
        self.event_bus.subscribe(ShieldGainEvent, self.on_shield_gain_quests)

    def is_battle_won(self, run: GameRun) -> bool:
        return run.player.hp <= 0 or run.player2.hp <= 0

    def get_modified_spell_damage(self, run: GameRun, card: Card, damage: int) -> int:
        return self.combat_resolver.get_modified_spell_damage(run, card, damage)

    def _get_first_alive_enemy(self, run: GameRun) -> str:
        return self.combat_resolver.get_first_alive_enemy(run)

    def _discard_card(self, run: GameRun, cid: str) -> str:
        return self.card_player.discard_card(run, cid)

    def _execute_card_effect(self, run: GameRun, card: Card, target: Optional[str] = None) -> str:
        res = card.execute(run, target, self)
        for p in (run.player, run.player2):
            for pile_name in ("hand", "draw_pile", "discard_pile", "exhaust_pile"):
                pile = getattr(p, pile_name)
                for idx, cid in enumerate(pile):
                    if isinstance(cid, str) and not cid.startswith("duel_"):
                        base_cid = cid
                        suffix = ""
                        for s_tag in (":replay:", ":fragile:"):
                            if s_tag in cid:
                                parts = cid.split(s_tag, 1)
                                base_cid = parts[0]
                                suffix = s_tag + parts[1]
                                break
                        is_upgraded = base_cid.endswith("+")
                        core_cid = base_cid[:-1] if is_upgraded else base_cid
                        duel_core_cid = f"duel_{core_cid}"
                        try:
                            from ..data.duel_card_data import DUEL_CARD_CONFIG
                        except ImportError:
                            from game.data.duel_card_data import DUEL_CARD_CONFIG
                        if duel_core_cid in DUEL_CARD_CONFIG:
                            new_base = duel_core_cid + ("+" if is_upgraded else "")
                            pile[idx] = new_base + suffix
        if res:
            if res.startswith("❌") or "不足" in res or "超出范围" in res or "无法" in res or "未找到" in res:
                return res
            else:
                self._log_event(run, res)
                return ""
        return ""



    def on_card_played_quests_and_double_tap(self, event):
        p = event.run.player
        card = event.card
        try:
            from ..data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from game.data.duel_card_data import DUEL_CARD_CONFIG
        cfg = DUEL_CARD_CONFIG.get(card.id, {})
        dtype = cfg.get("damage_type", "")
        is_spell = (card.type == "spell" and dtype not in ("slashing", "bludgeoning", "piercing", "attack"))
        
        temporal_buff = next((b for b in p.buffs if b.id == "temporal_quest"), None)
        if temporal_buff and is_spell:
            progress = event.run.node_data.get("temporal_quest_progress", 0) + 1
            event.run.node_data["temporal_quest_progress"] = progress
            temporal_buff.desc = f"单回合使用4张法术牌({progress}/4)"
            if progress >= 4:
                p.buffs.remove(temporal_buff)
                p.hand.append("duel_reward_temporal_distortion")
                self._log_event(event.run, "🎉 [任务达成] 时序之谜完成！获得了奖励卡【时序扭曲】！")
                
        ancient_buff = next((b for b in p.buffs if b.id == "ancient_quest"), None)
        if ancient_buff and card.type == "amulet":
            progress = event.run.node_data.get("ancient_quest_progress", 0) + 1
            event.run.node_data["ancient_quest_progress"] = progress
            ancient_buff.desc = f"部署3个护符({progress}/3)"
            if progress >= 3:
                p.buffs.remove(ancient_buff)
                p.hand.append("duel_reward_ancient_resonance")
                self._log_event(event.run, "🎉 [任务达成] 远古共鸣完成！获得了奖励卡【秘钥绽放】！")
                
        is_physical = (dtype in ("slashing", "bludgeoning", "piercing", "attack"))
        arms_buff = next((b for b in p.buffs if b.id == "arms_quest"), None)
        if arms_buff and is_physical:
            progress = event.run.node_data.get("arms_quest_progress", 0) + 1
            event.run.node_data["arms_quest_progress"] = progress
            arms_buff.desc = f"使用5张物理伤害牌({progress}/5)"
            if progress >= 5:
                p.buffs.remove(arms_buff)
                p.hand.append("duel_reward_master_blade")
                self._log_event(event.run, "🎉 [任务达成] 兵器大师完成！获得了奖励卡【主宰之刃】！")
                
        if is_physical:
            dt_buff = next((b for b in p.buffs if b.id == "double_tap_buff"), None)
            if dt_buff:
                p.buffs.remove(dt_buff)
                self._log_event(event.run, f"⚡ [双发] 复制并再次重放了卡牌 【{card.name}】！")
                card.execute(event.run, event.target, self)

    def on_damage_take_quests(self, event):
        p = event.run.player
        if event.target == "e1" and event.damage_type in ("fire", "cold", "force", "lightning", "radiant"):
            fire_buff = next((b for b in p.buffs if b.id == "fire_quest"), None)
            if fire_buff:
                progress = event.run.node_data.get("fire_quest_progress", 0) + event.amount
                event.run.node_data["fire_quest_progress"] = progress
                fire_buff.desc = f"对敌方领主造成法伤({progress}/30)"
                if progress >= 30:
                    p.buffs.remove(fire_buff)
                    p.hand.append("duel_reward_super_fireball")
                    self._log_event(event.run, "🎉 [任务达成] 火焰审判完成！获得了奖励卡【超级火球术】！")
                    
        if event.target == "p0" and p.hp < 25:
            fury_buff = next((b for b in p.buffs if b.id == "fury_quest"), None)
            if fury_buff:
                p.buffs.remove(fury_buff)
                p.hand.append("duel_reward_fury")
                self._log_event(event.run, "🎉 [任务达成] 浴血狂暴完成！获得了奖励卡【浴血狂怒】！")

    def on_shield_gain_quests(self, event):
        p = event.run.player
        if event.target == "p0" and p.shield >= 20:
            wall_buff = next((b for b in p.buffs if b.id == "wall_quest"), None)
            if wall_buff:
                p.buffs.remove(wall_buff)
                p.hand.append("duel_reward_wall_of_sighs")
                self._log_event(event.run, "🎉 [任务达成] 不落坚壁完成！获得了奖励卡【叹息之墙】！")

    def _log_event(self, run: Optional[GameRun], msg: str):
        if run is None:
            return
        if "battle_logs" not in run.node_data:
            run.node_data["battle_logs"] = []
        run.node_data["battle_logs"].append(msg)

    def _append_logs_to_res(self, run: GameRun, res: str) -> str:
        if "battle_logs" in run.node_data:
            logs = run.node_data.pop("battle_logs", [])
            if logs:
                res = res.rstrip() + "\n" + "\n".join(logs)
        return res

    def _sync_forward(self, run: GameRun):
        p2 = run.player2
        enemies = []
        enemies.append(EnemyState(
            name=run.node_data.get("player2_name", "对手"),
            hp=p2.hp,
            max_hp=p2.max_hp,
            shield=p2.shield,
            buffs=p2.buffs
        ))
        for i in range(1, 7):
            key = str(i)
            if key in p2.minions:
                m = p2.minions[key]
                enemies.append(EnemyState(
                    name=m.name,
                    hp=m.hp,
                    max_hp=m.max_hp,
                    shield=0,
                    buffs=m.buffs,
                    is_summon=True
                ))
            else:
                enemies.append(EnemyState(name="空", hp=0, max_hp=0, shield=0))
        run.enemies = enemies

    def _damage_target(self, run: GameRun, target: str, dmg: int, source: str = "effect", damage_type: str = "effect", card: Optional[Card] = None):
        self._sync_forward(run)
        p = run.player
        p2 = run.player2
        if target.startswith("p") and target != "p0":
            if target[1:] not in p.minions:
                return
        if target.startswith("e") and target != "e1":
            try:
                g = str(int(target[1:]) - 1)
                if g not in p2.minions:
                    return
            except ValueError:
                return
        if source == "effect":
            if run.node_data.get("current_acting_minion_grid"):
                source = f"p{run.node_data['current_acting_minion_grid']}"
            else:
                source = "p0"
        from ..models.events import DamageCalculateEvent, DamageTakeEvent
        calc_evt = DamageCalculateEvent(run, card, source, target, damage_type, dmg, dmg)
        self.event_bus.dispatch(calc_evt)
        final_dmg = max(0, calc_evt.modified_damage)
        
        p = run.player
        p2 = run.player2
        is_true = (damage_type in ("true", "TRUE"))
        shield_dmg = 0
        hp_dmg = 0
        is_fatal = False
        target_name = "未知"
        
        if target == "p0":
            target_name = run.node_data.get("player1_name" if run.user_id == run.node_data["player1_id"] else "player2_name", "自己")
            if is_true:
                hp_dmg = final_dmg
                p.hp -= final_dmg
            else:
                if p.shield >= final_dmg:
                    p.shield -= final_dmg
                    shield_dmg = final_dmg
                else:
                    shield_dmg = p.shield
                    hp_dmg = final_dmg - p.shield
                    p.hp -= hp_dmg
                    p.shield = 0
            if p.hp <= 0:
                is_fatal = True
                
        elif target.startswith("p"):
            grid = target[1:]
            if grid in p.minions:
                m = p.minions[grid]
                target_name = m.name
                hp_dmg = final_dmg
                m.hp -= final_dmg
                if m.hp <= 0:
                    is_fatal = True
                    p.minion_graveyard.append(m.id)
                    del p.minions[grid]
                    from ..models.events import MinionDeathEvent
                    self.event_bus.dispatch(MinionDeathEvent(run, m.id, target, m.name, False))
                    
        elif target == "e1":
            target_name = run.node_data.get("player2_name" if run.user_id == run.node_data["player1_id"] else "player1_name", "对手")
            if is_true:
                hp_dmg = final_dmg
                p2.hp -= final_dmg
            else:
                if p2.shield >= final_dmg:
                    p2.shield -= final_dmg
                    shield_dmg = final_dmg
                else:
                    shield_dmg = p2.shield
                    hp_dmg = final_dmg - p2.shield
                    p2.hp -= hp_dmg
                    p2.shield = 0
            if p2.hp <= 0:
                is_fatal = True
                
        elif target.startswith("e") and len(target) > 1:
            grid = str(int(target[1:]) - 1)
            if grid in p2.minions:
                m = p2.minions[grid]
                target_name = m.name
                hp_dmg = final_dmg
                m.hp -= final_dmg
                if m.hp <= 0:
                    is_fatal = True
                    p2.minion_graveyard.append(m.id)
                    del p2.minions[grid]
                    from ..models.events import MinionDeathEvent
                    self.event_bus.dispatch(MinionDeathEvent(run, m.id, target, m.name, True))
                    
        take_evt = DamageTakeEvent(run, source, target, final_dmg, is_fatal, damage_type)
        self.event_bus.dispatch(take_evt)
        
        from .battle.combat_resolver import DAMAGE_TYPE_NAMES
        damage_type_str = damage_type.value if hasattr(damage_type, "value") else str(damage_type)
        type_name = DAMAGE_TYPE_NAMES.get(damage_type_str, "物理" if damage_type_str == "attack" else "效果")
        log_msg = f"对【{target_name}】造成 {final_dmg} 点{type_name}伤害"
        if shield_dmg == 0 and hp_dmg == 0:
            log_msg += f"（但{target_name}免疫了这次攻击！）"
        else:
            if shield_dmg > 0:
                log_msg += f"，对护盾造成 {shield_dmg} 伤害"
            if hp_dmg > 0:
                log_msg += f"，对生命造成 {hp_dmg} 伤害"
        self._log_event(run, log_msg)
        self._sync_forward(run)

    def _heal_target(self, run: GameRun, target: str, heal: int):
        self._sync_forward(run)
        from ..models.events import HealEvent, HealCalculateEvent
        heal_evt = HealEvent(run, target, heal)
        self.event_bus.dispatch(heal_evt)
        if heal_evt.cancelled:
            return
        heal = heal_evt.amount
        
        target_name = "未知"
        if target == "p0":
            p = run.player
            calc_evt = HealCalculateEvent(run, "p0", p.max_hp, p.max_hp)
            self.event_bus.dispatch(calc_evt)
            p.hp = min(calc_evt.modified_max_hp, p.hp + heal)
            target_name = "自己"
        elif target.startswith("p") and len(target) > 1:
            grid = target[1:]
            if grid in run.player.minions:
                m = run.player.minions[grid]
                m.hp = min(m.max_hp, m.hp + heal)
                target_name = m.name
        elif target == "e1":
            p2 = run.player2
            calc_evt = HealCalculateEvent(run, "e1", p2.max_hp, p2.max_hp)
            self.event_bus.dispatch(calc_evt)
            p2.hp = min(calc_evt.modified_max_hp, p2.hp + heal)
            target_name = "对手"
        elif target.startswith("e") and len(target) > 1:
            grid = str(int(target[1:]) - 1)
            if grid in run.player2.minions:
                m = run.player2.minions[grid]
                m.hp = min(m.max_hp, m.hp + heal)
                target_name = m.name
                
        self._log_event(run, f"【{target_name}】恢复了 {heal} 点生命值。")
        self._sync_forward(run)

    def _gain_shield(self, run: GameRun, target: str, amount: int):
        self._sync_forward(run)
        from ..models.events import ShieldGainEvent
        evt = ShieldGainEvent(run, target, amount, amount)
        self.event_bus.dispatch(evt)
        final_amount = evt.modified_amount
        if final_amount <= 0:
            return
        
        target_name = "未知"
        if target == "p0":
            run.player.shield += final_amount
            target_name = "自己"
        elif target == "e1":
            run.player2.shield += final_amount
            target_name = "对手"
            
        self._log_event(run, f"【{target_name}】获得了 {final_amount} 点护盾。")
        self._sync_forward(run)

    def _get_target_name(self, run: GameRun, target: Optional[str]) -> str:
        if not target:
            return "未知"
        target = target.lower()
        if target == "p0" or target == "p":
            p1_id = run.node_data["player1_id"]
            return run.node_data.get("player1_name" if run.user_id == p1_id else "player2_name", "玩家")
        if target == "e1" or target == "e":
            p1_id = run.node_data["player1_id"]
            return run.node_data.get("player2_name" if run.user_id == p1_id else "player1_name", "对手")
        if target.startswith("p") and len(target) > 1:
            grid = target[1:]
            if grid in run.player.minions:
                return run.player.minions[grid].name
        if target.startswith("e") and len(target) > 1:
            try:
                grid = str(int(target[1:]) - 1)
                if grid in run.player2.minions:
                    return run.player2.minions[grid].name
            except ValueError:
                pass
        return "未知"

    def _summon_minion(self, run: GameRun, minion_id: str, name: str, hp: int, atk: int, ba: int) -> Optional[str]:
        grid = self.combat_resolver.summon_minion(run, minion_id, name, hp, atk, ba)
        if grid:
            m = run.player.minions[grid]
            try:
                from ..data.duel_card_data import RUSH_MINIONS, CHARGE_MINIONS
            except ImportError:
                from game.data.duel_card_data import RUSH_MINIONS, CHARGE_MINIONS
            if minion_id in RUSH_MINIONS:
                m.attack_actions = 1
                self._add_buff_to(m, "rush_buff", "突进", "本回合可立即攻击敌方随从。")
            elif minion_id in CHARGE_MINIONS:
                m.attack_actions = 1
            else:
                m.attack_actions = 0
        return grid

    def _draw_cards(self, p: PlayerState, count: int, run: Optional[GameRun] = None, ignore_focus: bool = False):
        self.card_player.draw_cards(p, count, run, ignore_focus)

    def _add_buff_to(self, entity, buff_id: str, buff_name: str, desc: str, count: int = 1, count2: Optional[int] = None):
        if getattr(entity, "name", "") == "空":
            return
        self.combat_resolver.add_buff_to(entity, buff_id, buff_name, desc, count, count2)

    def _get_free_grid(self, p: PlayerState) -> Optional[str]:
        return self.combat_resolver.get_free_grid(p)

    def init_duel(self, run: GameRun):
        p1 = run.player
        p2 = run.player2
        
        p1.hp = 200
        p1.max_hp = 200
        p1.shield = 0
        p1.gold = 0
        p1.hand.clear()
        p1.draw_pile = p1.deck.copy()
        random.shuffle(p1.draw_pile)
        p1.discard_pile.clear()
        p1.exhaust_pile.clear()
        p1.minion_graveyard.clear()
        p1.enemy_graveyard.clear()
        p1.minions.clear()
        p1.amulets.clear()
        p1.buffs.clear()
        
        p2.hp = 200
        p2.max_hp = 200
        p2.shield = 0
        p2.gold = 0
        p2.hand.clear()
        p2.draw_pile = p2.deck.copy()
        random.shuffle(p2.draw_pile)
        p2.discard_pile.clear()
        p2.exhaust_pile.clear()
        p2.minion_graveyard.clear()
        p2.enemy_graveyard.clear()
        p2.minions.clear()
        p2.amulets.clear()
        p2.buffs.clear()
        
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        
        run.node_data["turn_count"] = 1
        run.node_data["current_turn_id"] = p1_id
        
        run.node_data["p1_coins"] = 0
        run.node_data["p2_coins"] = 2
        
        run.node_data["p1_evolve_points"] = 4
        run.node_data["p2_evolve_points"] = 4
        
        run.node_data["p1_evolved_this_turn"] = False
        run.node_data["p2_evolved_this_turn"] = False
        
        run.node_data["p1_turns_count"] = 1
        run.node_data["p2_turns_count"] = 0
        
        run.node_data["p1_a_cap"] = 1
        run.node_data["p1_ba_cap"] = 1
        run.node_data["p2_a_cap"] = 1
        run.node_data["p2_ba_cap"] = 1
        
        p1.actions = 1
        p1.bonus_actions = 1
        p2.actions = 0
        p2.bonus_actions = 0
        
        self._draw_cards(p1, 6, run, ignore_focus=True)
        self._draw_cards(p2, 6, run, ignore_focus=True)
        
        self._sync_forward(run)
        
        from ..models.events import BattleStartEvent
        self.event_bus.dispatch(BattleStartEvent(run))

    def start_turn(self, run: GameRun):
        p = run.player
        p1_id = run.node_data["player1_id"]
        is_p1 = (run.user_id == p1_id)
        prefix = "p1" if is_p1 else "p2"
        
        turns = run.node_data.get(f"{prefix}_turns_count", 0) + 1
        run.node_data[f"{prefix}_turns_count"] = turns
        
        if is_p1:
            run.node_data["turn_count"] = turns
            
        a_cap = min(10, 1 + (turns - 1) // 2)
        ba_cap = min(10, 1 + (turns - 1) // 3)
        run.node_data[f"{prefix}_a_cap"] = a_cap
        run.node_data[f"{prefix}_ba_cap"] = ba_cap
        
        p.shield = p.shield // 2
        
        stunned = False
        for b in list(p.buffs):
            if b.id == "stun":
                stunned = True
                b.stacks -= 1
                if b.stacks <= 0:
                    p.buffs.remove(b)
                break
                
        if stunned:
            p.actions = 0
            p.bonus_actions = 0
            self._log_event(run, "🌀 你处于眩晕状态，本回合无法行动！")
        else:
            p.actions = a_cap
            p.bonus_actions = ba_cap
            
        self._draw_cards(p, 1, run, ignore_focus=False)
        
        for k, m in list(p.minions.items()):
            minion_stunned = False
            for b in list(m.buffs):
                if b.id == "stun":
                    minion_stunned = True
                    b.stacks -= 1
                    if b.stacks <= 0:
                        m.buffs.remove(b)
                    break
            if minion_stunned:
                m.attack_actions = 0
                m.actions = 0
                m.bonus_actions = 0
            else:
                m.attack_actions = 1
                m.actions += 1
                
            for b in list(m.buffs):
                if b.id == "rush_buff":
                    m.buffs.remove(b)
                    
        run.node_data[f"{prefix}_evolved_this_turn"] = False
        
        for b in list(p.buffs):
            if b.id == "tactical_focus":
                b.stacks -= 1
                if b.stacks <= 0:
                    p.buffs.remove(b)
                    
        
        from ..models.events import TurnStartEvent
        self.event_bus.dispatch(TurnStartEvent(run, is_player=True))

    def _trigger_amulet_last_words(self, run: GameRun, amulet_id: str):
        try:
            from ..data.amulet_data import AMULET_CONFIG
        except ImportError:
            from game.data.amulet_data import AMULET_CONFIG
        base_id = amulet_id[:-1] if amulet_id.endswith("+") else amulet_id
        cfg = AMULET_CONFIG.get(base_id)
        if not cfg:
            return
        is_upgraded = amulet_id.endswith("+")
        lw_msg = ""
        dmg_val = cfg.get("damage", 0)
        if dmg_val > 0:
            if is_upgraded:
                dmg_val += 3
            opp_target = "e1"
            for i in range(1, 7):
                if str(i) in run.player2.minions:
                    opp_target = f"e{i+1}"
                    break
            self._damage_target(run, opp_target, dmg_val, damage_type="thunder")
            lw_msg = f"对敌方造成了 {dmg_val} 点雷鸣伤害"
            
        heal_val = cfg.get("heal", 0)
        if heal_val > 0:
            if is_upgraded:
                heal_val += 2
            self._heal_target(run, "p0", heal_val)
            lw_msg = f"玩家恢复了 {heal_val} 点生命值"
            
        shield_val = cfg.get("shield", 0)
        if shield_val > 0:
            if is_upgraded:
                shield_val += 2
            self._gain_shield(run, "p0", shield_val)
            lw_msg = f"玩家获得了 {shield_val} 点护盾"
            
        if lw_msg:
            self._log_event(run, f"🔔 护符【{cfg.get('name', amulet_id)}】销毁，谢幕曲触发：{lw_msg}")

    def end_turn(self, run: GameRun):
        from ..models.events import TurnEndEvent
        self.event_bus.dispatch(TurnEndEvent(run, is_player=True))
        
        p1_id = run.node_data["player1_id"]
        p2_id = run.node_data["player2_id"]
        
        if run.user_id == p1_id:
            run.player, run.player2 = run.player2, run.player
            run.user_id = p2_id
            run.node_data["current_turn_id"] = p2_id
        else:
            run.player, run.player2 = run.player2, run.player
            run.user_id = p1_id
            run.node_data["current_turn_id"] = p1_id
            
        self.start_turn(run)

    def use_coin(self, run: GameRun, user_id: str) -> str:
        current_turn_id = run.node_data.get("current_turn_id")
        if user_id != current_turn_id:
            return "❌ 现在不是你的回合，无法使用幸运币。"
            
        p1_id = run.node_data["player1_id"]
        prefix = "p1" if user_id == p1_id else "p2"
        coins = run.node_data.get(f"{prefix}_coins", 0)
        if coins <= 0:
            return "❌ 你没有幸运币了。"
            
        run.node_data[f"{prefix}_coins"] = coins - 1
        run.player.actions += 1
        self._log_event(run, f"🪙 玩家使用了幸运币，获得了 1 点动作点 (A)。")
        return "✅ 使用幸运币成功，动作点增加 1A。"

    def evolve_card(self, run: GameRun, user_id: str, target: str) -> str:
        current_turn_id = run.node_data.get("current_turn_id")
        if user_id != current_turn_id:
            return "❌ 现在不是你的回合，无法进化卡牌。"
            
        tc = run.node_data.get("turn_count", 1)
        if tc < 3:
            return "❌ 进化点第 3 回合起才可使用（当前第 {} 回合）。".format(tc)
            
        p1_id = run.node_data["player1_id"]
        prefix = "p1" if user_id == p1_id else "p2"
        
        if run.node_data.get(f"{prefix}_evolved_this_turn", False):
            return "❌ 每回合只能进化一张牌。"
            
        ev = run.node_data.get(f"{prefix}_evolve_points", 4)
        if ev <= 0:
            return "❌ 你的进化点已用完。"
            
        p = run.player
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(p.hand):
                cid = p.hand[idx]
                if cid.endswith("+"):
                    return "❌ 该卡牌已经是强化版本了。"
                p.hand[idx] = cid + "+"
                run.node_data[f"{prefix}_evolved_this_turn"] = True
                run.node_data[f"{prefix}_evolve_points"] = ev - 1
                self._log_event(run, f"✨ 进化了手牌中的卡牌为强化版！")
                return f"✨ 成功将手牌 [{idx+1}] 进化为强化版。"
            else:
                return "❌ 序号超出范围。"
                
        if target.startswith("p") and len(target) > 1:
            grid = target[1:]
            if grid in p.minions:
                m = p.minions[grid]
                if m.name.endswith("+"):
                    return "❌ 该随从已经是进化形态。"
                m.max_hp += 2
                m.hp = m.max_hp
                m.atk += 2
                m.name += "+"
                run.node_data[f"{prefix}_evolved_this_turn"] = True
                run.node_data[f"{prefix}_evolve_points"] = ev - 1
                self._log_event(run, f"✨ 进化了随从 【{m.name[:-1]}】！")
                return f"✨ 成功将随从 【{m.name[:-1]}】 进化为强化形态 【{m.name}】（生命补满并上限+2，攻击力+2）。"
            elif grid in p.amulets:
                a = p.amulets[grid]
                if a.name.endswith("+"):
                    return "❌ 该护符已经是强化形态。"
                a.name += "+"
                run.node_data[f"{prefix}_evolved_this_turn"] = True
                run.node_data[f"{prefix}_evolve_points"] = ev - 1
                self._log_event(run, f"✨ 进化了护符 【{a.name[:-1]}】！")
                return f"✨ 成功将护符 【{a.name[:-1]}】 进化为 【{a.name}】。"
            else:
                return "❌ 我方格子中不存在可进化的实体。"
                
        return "❌ 进化的目标不合法（请提供手牌序号或我方格子，如 1 或 p1）。"

    def minion_attack(self, run: GameRun, my_grid: str, opp_grid: Optional[str] = None) -> str:
        p = run.player
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随随从。"
        m = p.minions[my_grid]
        if m.attack_actions < 1:
            return "❌ 该随从本回合已经没有可用的攻击动作（AA）点。"
            
        has_rush = any(b.id == "rush_buff" for b in m.buffs)
        
        if opp_grid is None:
            for i in range(1, 7):
                if str(i) in run.player2.minions:
                    opp_grid = f"e{i+1}"
                    break
            if not opp_grid:
                opp_grid = "e1"
                
        if opp_grid == "e1" and has_rush:
            return f"❌ 随从【{m.name}】本回合处于突进状态，只能攻击敌方随从，无法直接攻击领主。"
            
        m.attack_actions -= 1
        m.actions -= 1
        
        target_name = "未知"
        if opp_grid == "e1":
            p1_id = run.node_data["player1_id"]
            target_name = run.node_data.get("player2_name" if run.user_id == p1_id else "player1_name", "对手")
            self._damage_target(run, "e1", m.atk, source=f"p{my_grid}", damage_type="attack")
            res = f"我方随从【{m.name}】攻击了敌方领主【{target_name}】。"
        elif opp_grid.startswith("e") and len(opp_grid) > 1:
            try:
                opp_idx = int(opp_grid[1:]) - 1
            except ValueError:
                opp_idx = 0
            opp_grid_clean = str(opp_idx)
            p2 = run.player2
            if opp_grid_clean not in p2.minions:
                return f"❌ 敌方战场对应格子 [{opp_grid_clean}] 没有随从存在。"
            enemy_m = p2.minions[opp_grid_clean]
            target_name = enemy_m.name
            
            res = f"我方随从【{m.name}】攻击了敌方随从【{target_name}】。"
            
            self._damage_target(run, opp_grid, m.atk, source=f"p{my_grid}", damage_type="attack")
            if opp_grid_clean in p2.minions:
                self._damage_target(run, f"p{my_grid}", enemy_m.atk, source=opp_grid, damage_type="attack")
        else:
            return "❌ 攻击目标非法，随从只能攻击 e1-e7。"
            
        return res

    def minion_skill(self, run: GameRun, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        p = run.player
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        try:
            from ..entities.minions.minions import ALL_MINIONS
        except ImportError:
            from game.entities.minions.minions import ALL_MINIONS
        if m.id not in ALL_MINIONS:
            return f"❌ 随从【{m.name}】没有任何可用技能。"
        template = ALL_MINIONS[m.id]
        skills_list = template.skills
        if skill_idx < 1 or skill_idx > len(skills_list):
            skills_desc = "\n".join([f" [{idx}] {s.name}: {s.desc}" for idx, s in enumerate(skills_list, 1)])
            return f"❌ 无效的技能序号。随从【{m.name}】的可用技能有：\n{skills_desc}"
        skill = skills_list[skill_idx - 1]
        cost_a = skill.cost_a
        cost_ba = skill.cost_ba
        if m.actions < cost_a or m.bonus_actions < cost_ba:
            return f"❌ 随从资源不足（需要 {cost_a}A {cost_ba}BA，当前 {m.actions}A {m.bonus_actions}BA）。"
        needs_target = False
        base_id = m.id.rstrip("+")
        if base_id == "mercenary" and skill_idx == 1:
            needs_target = True
        elif base_id == "shield_guard" and skill_idx == 2:
            needs_target = True
        elif base_id == "water_elemental" and skill_idx == 2:
            needs_target = True
        if needs_target:
            if target is None:
                for i in range(1, 7):
                    if str(i) in run.player2.minions:
                        target = f"e{i+1}"
                        break
                if not target:
                    target = "e1"
            if isinstance(target, str) and target.isdigit():
                target = f"e{target}"
            if target == "0" or target == "e0":
                target = "e1"
            if target.startswith("e"):
                if target == "e1":
                    pass
                else:
                    try:
                        opp_grid = str(int(target[1:]) - 1)
                    except ValueError:
                        opp_grid = "0"
                    if opp_grid not in run.player2.minions:
                        return f"❌ 敌方目标 [{target}] 不存在。"
            else:
                return "❌ 无效的目标。该技能只能对敌方目标释放。"
        m.actions -= cost_a
        m.bonus_actions -= cost_ba
        msg = f"随从【{m.name}】发动了技能【{skill.name}】！"
        effect_msg = skill.execute(run, my_grid, target, self)
        msg += effect_msg
        return msg
