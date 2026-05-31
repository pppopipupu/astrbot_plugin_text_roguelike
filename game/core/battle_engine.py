import random
from typing import Optional
from ..models.state import GameRun, PlayerState, EnemyState, Card
from .battle.base import BaseBattleEngine
from .battle.combat_resolver import CombatResolver
from .battle.card_player import CardPlayer
from .battle.enemy_controller import EnemyTurnController
from .battle.observers import RelicTriggerHandler, BuffTriggerHandler, AmuletTriggerHandler

class BattleEngine(BaseBattleEngine):
    def __init__(self, save_manager):
        super().__init__(save_manager)
        self.combat_resolver = CombatResolver(self)
        self.card_player = CardPlayer(self)
        self.enemy_controller = EnemyTurnController(self)
        self.relic_handler = RelicTriggerHandler(self.event_bus, self)
        self.buff_handler = BuffTriggerHandler(self.event_bus, self)
        self.amulet_handler = AmuletTriggerHandler(self.event_bus, self)

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
        return self.combat_resolver.get_first_alive_enemy(run)

    def _get_target_name(self, run: GameRun, target: Optional[str]) -> str:
        return self.combat_resolver.get_target_name(run, target)

    def _damage_target(self, run: GameRun, target: str, dmg: int, source: str = "effect", damage_type: str = "effect", card: Optional[Card] = None):
        self.combat_resolver.damage_target(run, target, dmg, source, damage_type, card)

    def _heal_target(self, run: GameRun, target: str, heal: int):
        self.combat_resolver.heal_target(run, target, heal)

    def _summon_minion(self, run: GameRun, minion_id: str, name: str, hp: int, atk: int, ba: int) -> Optional[str]:
        return self.combat_resolver.summon_minion(run, minion_id, name, hp, atk, ba)

    def _gain_shield(self, run: GameRun, target: str, amount: int):
        self.combat_resolver.gain_shield(run, target, amount)

    def _sync_enemy_intents(self, enemy: EnemyState):
        self.enemy_controller.sync_enemy_intents(enemy)

    def _add_buff_to(self, entity, buff_id: str, buff_name: str, desc: str, count: int = 1, count2: Optional[int] = None):
        self.combat_resolver.add_buff_to(entity, buff_id, buff_name, desc, count, count2)

    def _get_free_grid(self, p: PlayerState) -> Optional[str]:
        return self.combat_resolver.get_free_grid(p)

    def _draw_cards(self, p: PlayerState, count: int, run: Optional[GameRun] = None):
        self.card_player.draw_cards(p, count, run)

    def _init_battle_node(self, run: GameRun, difficulty: str = "normal"):
        p = run.player
        p.hand.clear()
        p.draw_pile = p.deck.copy()
        import random
        random.shuffle(p.draw_pile)
        p.discard_pile.clear()
        p.exhaust_pile.clear()
        p.minion_graveyard.clear()
        p.enemy_graveyard.clear()
        p.minions.clear()
        p.amulets.clear()
        p.buffs.clear()
        p.actions = 2
        p.bonus_actions = 1
        p.shield = 0
        run.node_data["cards_played_this_turn"] = 0

        from ..models.events import BattleStartEvent, TurnStartEvent
        evt_start = BattleStartEvent(run)
        self.event_bus.dispatch(evt_start)

        if getattr(p, "subclass", "") == "时序法师":
            if random.random() < 0.25:
                p.bonus_actions += 1
                self._log_event(run, "⏳ [时序被动] 触发时间跳跃，初始额外获得 1 个附赠动作（BA）！")
        init_draw = 6
        for r in p.relics:
            from ..entities.relics.relics import get_relic_impl
            impl = get_relic_impl(r)
            if impl:
                init_draw = impl.modify_initial_draw(run, init_draw, self)
        self._draw_cards(p, init_draw, run)
        run.node_data["difficulty"] = difficulty

        if difficulty == "boss":
            if p.stage == 20:
                boss_cfg = self.save_manager.load_admin_config()
                boss_setting = boss_cfg.get("final_boss", "random")
                if boss_setting == "random":
                    boss_name = random.choice(["腐化之心", "Icerainboww"])
                else:
                    boss_name = boss_setting

                if boss_name == "腐化之心":
                    run.enemies = [EnemyState(
                        name="腐化之心",
                        hp=120,
                        max_hp=120,
                        shield=0,
                        actions=1,
                        bonus_actions=2,
                        max_actions=1,
                        max_bonus_actions=2
                    )]
                    self._add_buff_to(run.enemies[0], "beat_of_death", "死亡律动", "玩家每使用一张牌，受到 1 点力场伤害。")
                    run.node_data["boss_name"] = "腐化之心"
                else:
                    run.enemies = [EnemyState(
                        name="Icerainboww",
                        hp=160,
                        max_hp=160,
                        shield=0,
                        actions=2,
                        bonus_actions=0,
                        max_actions=2,
                        max_bonus_actions=0
                    )]
                    run.node_data["boss_name"] = "Icerainboww"
                    run.node_data["icerainboww_turn"] = 1
            else:
                boss_name = random.choice(["远古红龙", "雷霆领主"])
                if boss_name == "远古红龙":
                    run.enemies = [EnemyState(
                        name="远古红龙",
                        hp=140,
                        max_hp=140,
                        shield=0,
                        actions=1,
                        bonus_actions=2,
                        max_actions=1,
                        max_bonus_actions=2
                    )]
                else:
                    run.enemies = [EnemyState(
                        name="雷霆领主",
                        hp=130,
                        max_hp=130,
                        shield=0,
                        actions=1,
                        bonus_actions=2,
                        max_actions=1,
                        max_bonus_actions=2
                    )]
                    run.node_data["thunder_lord_turn"] = 1
        elif difficulty == "elite":
            from ..data.enemy_data import ENEMY_CONFIG
            elite_pool = [
                "地精百夫长", "石像鬼祭司", "狂暴兽王",
                "黑曜石巨灵", "幽灵大魔法师", "暗影影魔",
                "末日守卫", "亡灵巫师"
            ]
            run.enemies = []
            base_name = random.choice(elite_pool)
            cfg = ENEMY_CONFIG.get(base_name, {})
            import re
            hp_str = cfg.get("hp", "30")
            base_hp = 30
            match = re.match(r"^(\d+)", hp_str)
            if match:
                base_hp = int(match.group(1))
            hp_final = base_hp + p.stage * 3

            actions_str = cfg.get("actions", "1A 1BA")
            act_match = re.search(r"(\d+)A", actions_str)
            ba_match = re.search(r"(\d+)BA", actions_str)
            actions = int(act_match.group(1)) if act_match else 1
            bonus_actions = int(ba_match.group(1)) if ba_match else 1

            run.enemies.append(EnemyState(
                name=base_name,
                hp=hp_final,
                max_hp=hp_final,
                shield=0,
                actions=actions,
                bonus_actions=bonus_actions,
                max_actions=actions,
                max_bonus_actions=bonus_actions
            ))
        else:
            from ..data.enemy_data import ENEMY_CONFIG
            normal_pool = [
                "地精突袭者", "石像鬼守卫", "堕落学徒", "狂暴野兽",
                "幽灵法师", "冰霜史莱姆", "骷髅弓箭手", "剧毒蜘蛛",
                "黑曜石巨人", "暗影刺客"
            ]
            run.enemies = []
            num_enemies = random.randint(1, 3)
            selected_names = [random.choice(normal_pool) for _ in range(num_enemies)]
            for i, base_name in enumerate(selected_names):
                cfg = ENEMY_CONFIG.get(base_name, {})
                import re
                hp_str = cfg.get("hp", "12")
                base_hp = 12
                match = re.match(r"^(\d+)", hp_str)
                if match:
                    base_hp = int(match.group(1))
                hp_final = base_hp + p.stage * 2

                actions_str = cfg.get("actions", "1A 0BA")
                act_match = re.search(r"(\d+)A", actions_str)
                ba_match = re.search(r"(\d+)BA", actions_str)
                actions = int(act_match.group(1)) if act_match else 1
                bonus_actions = int(ba_match.group(1)) if ba_match else 0

                name = f"{base_name} {chr(65 + i)}" if num_enemies > 1 else base_name
                run.enemies.append(EnemyState(
                    name=name,
                    hp=hp_final,
                    max_hp=hp_final,
                    shield=0,
                    actions=actions,
                    bonus_actions=bonus_actions,
                    max_actions=actions,
                    max_bonus_actions=bonus_actions
                ))

        evt_turn = TurnStartEvent(run, is_player=True)
        self.event_bus.dispatch(evt_turn)
        self._roll_enemy_intent(run)

    init_battle = _init_battle_node

    def play_card(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        return self.card_player.play_card(run, hand_idx, target)

    def play_special_action(self, run: GameRun, hand_idx: int, target: Optional[str] = None) -> str:
        return self.card_player.play_special_action(run, hand_idx, target)

    def minion_attack(self, run: GameRun, my_grid: str, opp_grid: Optional[str] = None) -> str:
        return self.card_player.minion_attack(run, my_grid, opp_grid)

    def minion_skill(self, run: GameRun, my_grid: str, skill_idx: int = 1, target: Optional[str] = None) -> str:
        return self.card_player.minion_skill(run, my_grid, skill_idx, target)

    def _execute_card_effect(self, run: GameRun, card: Card, target: Optional[str] = None) -> str:
        return card.execute(run, target, self)

    def get_modified_spell_damage(self, run: GameRun, card: Card, damage: int) -> int:
        return self.combat_resolver.get_modified_spell_damage(run, card, damage)

    def _discard_card(self, run: GameRun, cid: str) -> str:
        return self.card_player.discard_card(run, cid)

    def end_turn(self, run: GameRun) -> str:
        return self.card_player.end_turn(run)

    def _enemy_turn(self, run: GameRun) -> str:
        return self.enemy_controller.enemy_turn(run)

    def _handle_battle_win(self, run: GameRun):
        self.card_player.handle_battle_win(run)

    def _roll_enemy_intent(self, run: GameRun):
        self.enemy_controller.roll_enemy_intent(run)
