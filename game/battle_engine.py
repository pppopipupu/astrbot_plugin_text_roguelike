import random
from typing import Optional, List, Dict
from .models import GameRun, PlayerState, EnemyState, MinionState, AmuletState, Card

class BattleEngine:
    def __init__(self, save_manager):
        self.save_manager = save_manager

    def is_battle_won(self, run: GameRun) -> bool:
        if not run.enemies:
            return True
        if all(e.hp <= 0 for e in run.enemies):
            return True
        alive_enemies = [e for e in run.enemies if e.hp > 0]
        if all(e.is_summon for e in alive_enemies):
            return True
        return False

    def _get_first_alive_enemy(self, run: GameRun) -> str:
        for idx, enemy in enumerate(run.enemies, 1):
            if enemy.hp > 0:
                return f"e{idx}"
        return "e1"

    def _get_target_name(self, run: GameRun, target: str) -> str:
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                return run.enemies[idx].name
            return "未知敌人"
        elif target == "p0":
            return "玩家领主"
        elif target.startswith("p"):
            grid = target[1:]
            if grid in run.player.minions:
                return run.player.minions[grid].name
            return "我方随从"
        return "未知"

    def _damage_target(self, run: GameRun, target: str, dmg: int):
        if target.startswith("e"):
            try:
                idx = int(target[1:]) - 1
                if idx < 0: idx = 0
            except ValueError:
                idx = 0
            if 0 <= idx < len(run.enemies):
                e = run.enemies[idx]
                if e.shield >= dmg:
                    e.shield -= dmg
                else:
                    e.hp -= (dmg - e.shield)
                    e.shield = 0
                if e.hp <= 0:
                    run.player.graveyard.append("enemy:" + e.name)
                    run.enemies.pop(idx)

    def _heal_target(self, run: GameRun, target: str, heal: int):
        p = run.player
        if target == "p0":
            if "wither_seed" in p.relics:
                return
            will_buff = next((b for b in p.buffs if b.id == "iron_will"), None)
            will_stacks = will_buff.stacks if will_buff else 0
            cur_max = p.max_hp + will_stacks * 10
            p.hp = min(cur_max, p.hp + heal)
        elif target.startswith("p"):
            grid = target[1:]
            if grid in p.minions:
                p.minions[grid].hp = min(p.minions[grid].max_hp, p.minions[grid].hp + heal)

    def _add_buff_to(self, entity, buff_id: str, buff_name: str, desc: str, count: int = 1):
        from .models import BuffState
        for b in entity.buffs:
            if b.id == buff_id:
                b.stacks += count
                return
        entity.buffs.append(BuffState(buff_id, buff_name, count, desc))

    def _get_free_grid(self, p: PlayerState) -> Optional[str]:
        for i in range(1, 6):
            s = str(i)
            if s not in p.minions and s not in p.amulets:
                return s
        return None

    def _draw_cards(self, p: PlayerState, count: int):
        max_hand = 9 if "mask_of_void" in p.relics else 12
        for _ in range(count):
            if not p.draw_pile:
                p.draw_pile = p.discard_pile.copy()
                random.shuffle(p.draw_pile)
                p.discard_pile.clear()
            if p.draw_pile and len(p.hand) < max_hand:
                p.hand.append(p.draw_pile.pop())

    def _roll_enemy_intent(self, run: GameRun):
        from .enemy_impl import get_enemy_template
        for enemy in run.enemies:
            template = get_enemy_template(enemy.name)
            itype, val, desc = template.roll_intent(run, self, enemy)
            enemy.intent_a_type = itype
            enemy.intent_a_val = val
            enemy.intent_a_desc = desc
            
            if enemy.max_bonus_actions >= 1:
                itype_ba, val_ba, desc_ba = template.roll_intent_ba(run, self, enemy)
                enemy.intent_ba_type = itype_ba
                enemy.intent_ba_val = val_ba
                enemy.intent_ba_desc = desc_ba
            else:
                enemy.intent_ba_type = ""
                enemy.intent_ba_val = 0
                enemy.intent_ba_desc = ""
                
            if enemy.max_bonus_actions >= 2:
                itype_ba2, val_ba2, desc_ba2 = template.roll_intent_ba2(run, self, enemy)
                enemy.intent_ba2_type = itype_ba2
                enemy.intent_ba2_val = val_ba2
                enemy.intent_ba2_desc = desc_ba2
            else:
                enemy.intent_ba2_type = ""
                enemy.intent_ba2_val = 0
                enemy.intent_ba2_desc = ""

    def _init_battle_node(self, run: GameRun, difficulty: str):
        p = run.player
        p.buffs.clear()
        p.exhaust_pile.clear()
        p.graveyard.clear()
        run.node_data["cards_played_this_turn"] = 0
        p.draw_pile = p.deck.copy()
        random.shuffle(p.draw_pile)
        p.discard_pile.clear()
        p.hand.clear()
        p.actions = 2
        p.bonus_actions = 1
        p.shield = (8 if "heavy_armor" in p.relics else 0) + (4 if "leather_armor" in p.relics else 0)
        if "rust_shackle" in p.relics:
            p.hp = max(1, p.hp - 4)
        if "greedy_contract" in p.relics:
            p.hp = max(1, p.hp - 3)
        if "ancient_page" in p.relics:
            p.hp = max(1, p.hp - 4)
        if "ready_pack" in p.relics:
            p.bonus_actions += 1
        init_draw = 5 + (2 if "ancient_eye" in p.relics else 0) + (1 if "ready_pack" in p.relics else 0)
        if "blind_spot" in p.relics:
            init_draw = max(0, init_draw - 2)
        self._draw_cards(p, init_draw)
        if "ancient_page" in p.relics:
            max_hand = 9 if "mask_of_void" in p.relics else 12
            for _ in range(2):
                if len(p.hand) < max_hand:
                    p.hand.append("arcane_spark")

        run.node_data["difficulty"] = difficulty

        if difficulty == "boss":
            run.enemies = [EnemyState(
                name="远古红龙",
                hp=60,
                max_hp=60,
                shield=0,
                actions=1,
                bonus_actions=2,
                max_actions=1,
                max_bonus_actions=2
            )]
        elif difficulty == "elite":
            elite_pool = [
                ("地精百夫长", 30, 4),
                ("石像鬼祭司", 38, 3),
                ("狂暴兽王", 32, 5),
                ("黑曜石巨灵", 45, 5),
                ("幽灵大魔法师", 36, 4),
                ("暗影影魔", 34, 5)
            ]
            base_name, base_hp, base_atk = random.choice(elite_pool)
            hp_scale = base_hp + (p.stage * 3)
            
            run.enemies = [EnemyState(
                name=base_name,
                hp=hp_scale,
                max_hp=hp_scale,
                shield=0,
                actions=1,
                bonus_actions=1,
                max_actions=1,
                max_bonus_actions=1
            )]
            if random.random() < 0.5:
                enemies_pool = [
                    ("地精突袭者", 12, 2),
                    ("石像鬼守卫", 18, 1),
                    ("堕落学徒", 14, 2),
                    ("狂暴野兽", 15, 3),
                    ("幽灵法师", 16, 2),
                    ("冰霜史莱姆", 10, 1),
                    ("骷髅弓箭手", 12, 2),
                    ("剧毒蜘蛛", 10, 2),
                    ("黑曜石巨人", 22, 3),
                    ("暗影刺客", 14, 3)
                ]
                normal_name, normal_hp, normal_atk = random.choice(enemies_pool)
                n_hp = (normal_hp + p.stage * 2) // 2
                run.enemies.append(EnemyState(
                    name=normal_name,
                    hp=n_hp,
                    max_hp=n_hp,
                    shield=0,
                    actions=1,
                    bonus_actions=0,
                    max_actions=1,
                    max_bonus_actions=0
                ))
        else:
            enemies_pool = [
                ("地精突袭者", 12, 2),
                ("石像鬼守卫", 18, 1),
                ("堕落学徒", 14, 2),
                ("狂暴野兽", 15, 3),
                ("幽灵法师", 16, 2),
                ("冰霜史莱姆", 10, 1),
                ("骷髅弓箭手", 12, 2),
                ("剧毒蜘蛛", 10, 2),
                ("黑曜石巨人", 22, 3),
                ("暗影刺客", 14, 3)
            ]
            run.enemies = []
            num_enemies = random.randint(1, 3)
            for i in range(num_enemies):
                base_name, base_hp, base_atk = random.choice(enemies_pool)
                hp_scale = base_hp + (p.stage * 2)
                name = f"{base_name} {chr(65 + i)}" if num_enemies > 1 else base_name
                run.enemies.append(EnemyState(
                    name=name,
                    hp=hp_scale,
                    max_hp=hp_scale,
                    shield=0,
                    actions=1,
                    bonus_actions=0,
                    max_actions=1,
                    max_bonus_actions=0
                ))
        self._roll_enemy_intent(run)

    def play_card(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能使用卡牌。"
        if hand_idx < 1 or hand_idx > len(p.hand):
            return "❌ 无效的手牌序号。"

        cid = p.hand[hand_idx - 1]
        from .card_impl import ALL_CARDS
        card = ALL_CARDS.get(cid)
        if not card:
            return "❌ 卡牌不存在。"

        if card.type == "spell":
            if target is None:
                if card.id in ("dagger_throw", "fire_bolt", "fireball", "thunderwave", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                    target = self._get_first_alive_enemy(run)
                else:
                    target = "p0"
            if target == "0" or target == "e0":
                target = "e1"
            elif target == "p":
                target = "p0"
            if target.startswith("e"):
                try:
                    grid = int(target[1:]) - 1
                except ValueError:
                    grid = 0
                if grid < 0 or grid >= len(run.enemies):
                    return f"❌ 敌方格子 [{target}] 没有敌人。"
            elif target == "p0":
                pass
            elif target.startswith("p"):
                grid = target[1:]
                if grid not in p.minions:
                    return f"❌ 我方格子 [{grid}] 没有随从。"
            else:
                return "❌ 无效的目标选择。"

        if card.type in ("minion", "amulet") and self._get_free_grid(p) is None:
            return "❌ 你的战场格子已满，无法召唤随从或部署护符。"

        req_a = card.cost_a
        req_ba = card.cost_ba
        if card.type == "spell":
            quicken_buff = next((b for b in p.buffs if b.id == "quicken"), None)
            quicken_stacks = quicken_buff.stacks if quicken_buff else 0
            req_ba = max(0, req_ba - quicken_stacks)

        if p.actions < req_a or p.bonus_actions < req_ba:
            return f"❌ 你的动作资源不足（需要 {req_a}A {req_ba}BA，当前 {p.actions}A {p.bonus_actions}BA）。"

        p.actions -= req_a
        p.bonus_actions -= req_ba
        p.hand.pop(hand_idx - 1)
        if getattr(card, "fleeting", False):
            if cid in p.deck:
                p.deck.remove(cid)
        elif getattr(card, "exhaust", False):
            p.exhaust_pile.append(cid)
        else:
            p.discard_pile.append(cid)

        res = self._execute_card_effect(run, card, target)
        if card.type == "spell":
            if "unstable_crystal" in p.relics:
                p.hp = max(1, p.hp - 1)
                res += " ⚡ [不稳定水晶] 受到 1 点法术反噬伤害。"
            if "vampiric_touch" in p.relics and card.id in (
                "dagger_throw", "fire_bolt", "fireball", "thunderwave",
                "magic_missile", "quick_strike", "arcane_spark", "doomsday_judgment", "meteor_swarm"
            ):
                old_hp = p.hp
                self._heal_target(run, "p0", 1)
                if p.hp > old_hp:
                    res += " ❤️ [吸血之触] 回复了 1 点生命值。"

        echo_buff = next((b for b in p.buffs if b.id == "echo_form"), None)
        echo_stacks = echo_buff.stacks if echo_buff else 0
        played_count = run.node_data.get("cards_played_this_turn", 0)
        if played_count == 0 and echo_stacks > 0:
            for _ in range(echo_stacks):
                extra_res = self._execute_card_effect(run, card, target)
                res += f" 🔁 [回响触发] {extra_res}"
        run.node_data["cards_played_this_turn"] = played_count + 1

        surge_buff = next((b for b in p.buffs if b.id == "spell_surge"), None)
        surge_stacks = surge_buff.stacks if surge_buff else 0
        if surge_stacks > 0 and card.color == "wizard":
            self._draw_cards(p, surge_stacks)

        from .amulet_impl import ALL_AMULETS
        for ak, av in list(p.amulets.items()):
            template = ALL_AMULETS.get(av.id)
            if template and card.type == "spell":
                template.on_spell_played(run, ak, card, self)
        if card.type == "spell":
            net_buff = next((b for b in p.buffs if b.id == "magic_network"), None)
            if net_buff:
                for enemy in list(run.enemies):
                    self._damage_target(run, f"e{run.enemies.index(enemy)+1}", 3)
                p.shield += 3
                res += " ⚡ [魔网天成] 对所有敌人造成了 3 点伤害，获得了 3 点护盾。"
        self.save_manager.save_save(run.user_id, run)
        return res

    def play_special_action(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能使用卡牌的特殊行动。"
        if hand_idx < 1 or hand_idx > len(p.hand):
            return "❌ 无效的手牌序号。"

        cid = p.hand[hand_idx - 1]
        from .card_impl import ALL_CARDS
        card = ALL_CARDS.get(cid)
        if not card:
            return "❌ 卡牌不存在。"

        req_a = card.cost_a
        req_ba = card.cost_ba
        if p.actions < req_a or p.bonus_actions < req_ba:
            return f"❌ 你的动作资源不足（需要 {req_a}A {req_ba}BA，当前 {p.actions}A {p.bonus_actions}BA）。"

        if target is None:
            if card.id in ("dagger_throw", "fire_bolt", "fireball", "thunderwave", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                target = self._get_first_alive_enemy(run)
            else:
                target = "p0"

        if target == "0" or target == "e0":
            target = "e1"
        elif target == "p":
            target = "p0"

        p.actions -= req_a
        p.bonus_actions -= req_ba
        p.hand.pop(hand_idx - 1)
        if getattr(card, "fleeting", False):
            if cid in p.deck:
                p.deck.remove(cid)
        else:
            p.discard_pile.append(cid)

        res = card.special_action(run, target)
        self.save_manager.save_save(run.user_id, run)
        return res

    def minion_attack(self, run: GameRun, my_grid: str, opp_grid: str) -> str:
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能控制随从攻击。"
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        if m.attack_actions < 1:
            return "❌ 该随从本回合已经没有可用的攻击动作（AA）点。"

        m.attack_actions -= 1
        try:
            opp_idx = int(opp_grid.replace("e", "")) - 1
            if opp_idx < 0:
                opp_idx = 0
        except ValueError:
            opp_idx = 0

        if opp_idx < 0 or opp_idx >= len(run.enemies):
            return f"❌ 敌方格子 [{opp_grid}] 没有合法的敌人目标。"

        enemy = run.enemies[opp_idx]
        atk = m.atk + (1 if "whetstone" in p.relics else 0)
        if enemy.shield >= atk:
            enemy.shield -= atk
            dmg_msg = f"造成 {atk} 点护盾伤害"
        else:
            take = atk - enemy.shield
            enemy.hp -= take
            enemy.shield = 0
            dmg_msg = f"造成 {take} 点生命伤害"
            
        res = f"我方随从【{m.name}】攻击了敌人【{enemy.name}】，{dmg_msg}。"
        if enemy.hp <= 0:
            res += f" 敌人【{enemy.name}】已被击败！"
            run.player.graveyard.append("enemy:" + enemy.name)
            run.enemies.pop(opp_idx)
        self.save_manager.save_save(run.user_id, run)
        return res

    def minion_skill(self, run: GameRun, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        p = run.player
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能发动随从技能。"
        if my_grid not in p.minions:
            return f"❌ 我方格子 [{my_grid}] 没有随从。"
        m = p.minions[my_grid]
        from .minion_impl import ALL_MINIONS
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
        if m.id == "mercenary" and skill_idx == 1:
            needs_target = True
        elif m.id == "shield_guard" and skill_idx == 2:
            needs_target = True
        elif m.id == "water_elemental" and skill_idx == 2:
            needs_target = True

        if needs_target:
            if target is None:
                target = self._get_first_alive_enemy(run)
            if target == "0" or target == "e0":
                target = "e1"
            if target.startswith("e"):
                try:
                    idx = int(target[1:]) - 1
                except ValueError:
                    idx = 0
                if idx < 0 or idx >= len(run.enemies):
                    return f"❌ 敌方目标 [{target}] 不存在。"
            else:
                return "❌ 无效的目标。该技能只能对敌方目标释放。"

        m.actions -= cost_a
        m.bonus_actions -= cost_ba
        msg = f"随从【{m.name}】发动了技能【{skill.name}】！"
        effect_msg = skill.execute(run, my_grid, target, self)
        msg += effect_msg

        self.save_manager.save_save(run.user_id, run)
        return msg

    def _execute_card_effect(self, run: GameRun, card: Card, target: Optional[str] = None) -> str:
        return card.execute(run, target, self)

    def _discard_card(self, run: GameRun, cid: str) -> str:
        p = run.player
        from .card_impl import ALL_CARDS
        card = ALL_CARDS.get(cid)
        if not card:
            p.discard_pile.append(cid)
            return ""

        if getattr(card, "agile", False):
            target = None
            if card.type == "spell":
                if card.id in ("dagger_throw", "fire_bolt", "fireball", "thunderwave", "magic_missile", "quick_strike", "arcane_spark", "agile_strike", "fleeting_spark"):
                    target = self._get_first_alive_enemy(run)
                else:
                    target = "p0"
                if target == "0" or target == "e0":
                    target = "e1"
            res = self._execute_card_effect(run, card, target)
            if getattr(card, "fleeting", False):
                if cid in p.deck:
                    p.deck.remove(cid)
            elif getattr(card, "exhaust", False):
                p.exhaust_pile.append(cid)
            else:
                p.discard_pile.append(cid)
            return f"✨ 触发[灵巧]：丢弃【{card.name}】时自动打出！效果：{res}"
        else:
            p.discard_pile.append(cid)
            return ""

    def end_turn(self, run: GameRun) -> str:
        if run.node_type != "battle":
            return "❌ 只有在战斗中才能结束回合。"
        p = run.player

        from .amulet_impl import ALL_AMULETS
        for ak, av in list(p.amulets.items()):
            template = ALL_AMULETS.get(av.id)
            if template:
                template.on_end_turn(run, ak, self)
            av.countdown -= 1
            if av.countdown <= 0:
                del p.amulets[ak]

        if self.is_battle_won(run):
            self._handle_battle_win(run)
            return "战斗胜利！敌方单位已被全部击败。"

        enemy_actions = self._enemy_turn(run)
        if p.hp <= 0:
            self.save_manager.delete_save(run.user_id)
            return f"{enemy_actions}\n💀 冒险结束。你被击败了！存档已被清除。"

        decay_msgs = []
        if p.shield > 0:
            lost = p.shield - (p.shield // 2)
            p.shield = p.shield // 2
            if lost > 0:
                decay_msgs.append(f"玩家失去 {lost} 点护盾")
        else:
            p.shield = 0

        for enemy in run.enemies:
            if enemy.shield > 0:
                lost = enemy.shield - (enemy.shield // 2)
                enemy.shield = enemy.shield // 2
                if lost > 0:
                    decay_msgs.append(f"【{enemy.name}】失去 {lost} 点护盾")
            else:
                enemy.shield = 0

        decay_info = ""
        if decay_msgs:
            decay_info = "🛡️ 护盾流失：" + "，".join(decay_msgs) + "\n"

        p.buffs = [b for b in p.buffs if b.id != "magic_network"]
        p.actions = 2 + (1 if "energy_core" in p.relics else 0)
        p.bonus_actions = 1 + (1 if "unstable_crystal" in p.relics else 0)
        focus_buff = next((b for b in p.buffs if b.id == "tactical_focus"), None)
        focus_stacks = focus_buff.stacks if focus_buff else 0
        p.bonus_actions += focus_stacks
        for mk, mv in p.minions.items():
            mv.actions += 1
            mv.bonus_actions += 1 if mv.id == "arcane_golem" else 0
            mv.attack_actions = 1
            if mv.id == "mercenary":
                mv.atk = 4
            elif mv.id == "arcane_golem":
                mv.atk = 6

        self._draw_cards(p, 3)
        self._roll_enemy_intent(run)
        run.node_data["cards_played_this_turn"] = 0
        self.save_manager.save_save(run.user_id, run)
        return f"{enemy_actions}\n{decay_info}进入玩家回合。已重置动作并抽取手牌。"

    def _trigger_take_damage_amulets(self, run, source: str, amount: int, logs: List[str]):
        from .amulet_impl import ALL_AMULETS
        for ak, av in list(run.player.amulets.items()):
            template = ALL_AMULETS.get(av.id)
            if template:
                msg = template.on_take_damage(run, ak, source, amount, self)
                if msg:
                    logs.append(msg)

    def _enemy_turn(self, run: GameRun) -> str:
        logs = []
        active_enemies = list(run.enemies)
        for idx, enemy in enumerate(active_enemies):
            if enemy.hp <= 0:
                continue
            stun_buff = next((b for b in enemy.buffs if b.id == "stun"), None)
            if stun_buff:
                stun_buff.stacks -= 1
                if stun_buff.stacks <= 0:
                    enemy.buffs.remove(stun_buff)
                logs.append(f"【{enemy.name}】处于眩晕状态，本回合无法行动。")
                continue
            from .enemy_impl import get_enemy_template
            template = get_enemy_template(enemy.name)
            
            if enemy.hp > 0 and enemy.actions >= 1 and enemy.intent_a_type:
                enemy.actions -= 1
                enemy.intent_type = enemy.intent_a_type
                enemy.intent_val = enemy.intent_a_val
                template.execute_intent(run, self, enemy, logs)
                
            if enemy.hp > 0 and enemy.bonus_actions >= 1 and enemy.intent_ba_type:
                enemy.bonus_actions -= 1
                enemy.intent_type = enemy.intent_ba_type
                enemy.intent_val = enemy.intent_ba_val
                template.execute_intent(run, self, enemy, logs)
                
            if enemy.hp > 0 and enemy.bonus_actions >= 1 and enemy.intent_ba2_type:
                enemy.bonus_actions -= 1
                enemy.intent_type = enemy.intent_ba2_type
                enemy.intent_val = enemy.intent_ba2_val
                template.execute_intent(run, self, enemy, logs)

        for enemy in run.enemies:
            enemy.actions = enemy.max_actions
            enemy.bonus_actions = enemy.max_bonus_actions
        return "\n".join(logs)

    def _handle_battle_win(self, run: GameRun):
        p = run.player
        p.buffs.clear()
        p.hp = min(p.max_hp, p.hp)
        if "dragon_blood" in p.relics:
            p.hp = min(p.max_hp, p.hp + 5)
        difficulty = run.node_data.get("difficulty", "normal")
        quest = run.node_data.get("quest")
        quest_bonus = ""
        if quest == "knight_cave":
            p.deck.append("shield_guard")
            p.relics.append("heavy_armor")
            quest_bonus = "\n🗡️ 任务完成！你帮奥术骑士夺回了长剑。作为谢礼，【盾卫】加入了你的卡组，你还获得了一个遗物【重装甲片】！"
        elif quest == "maze_fight":
            got_relic = random.choice(["whetstone", "ready_pack", "arcane_rune"])
            p.relics.append(got_relic)
            from .relic_impl import get_relic_name
            quest_bonus = f"\n🔥 任务完成！你击败了火元素守卫，在石门后获得稀有遗物【{get_relic_name(got_relic)}】！"
        if difficulty == "elite":
            reward_gold = 25 + random.randint(10, 20)
        else:
            reward_gold = 10 + random.randint(5, 15)
        p.gold += reward_gold
        if p.stage == 20:
            run.node_type = "victory"
            self.save_manager.delete_save(run.user_id)
        else:
            run.node_type = "reward"
            from .card_impl import ALL_CARDS
            card_pool = list(ALL_CARDS.keys())
            normal_cards = [cid for cid in card_pool if ALL_CARDS[cid].rarity != "legendary"]
            reward_cards = random.sample(normal_cards, 3)
            run.node_data = {"cards": reward_cards, "quest_bonus": quest_bonus}
            self.save_manager.save_save(run.user_id, run)
