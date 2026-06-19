from typing import Optional
from ...models.state import Card, BuffState, AmuletState
from .duel_registry import register_duel_card

class DuelGenericCard(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.duel_card_data import DUEL_CARD_CONFIG
        except ImportError:
            from game.data.duel_card_data import DUEL_CARD_CONFIG
        cfg = DUEL_CARD_CONFIG.get(self.id, {})
        face_target = cfg.get("face_target", True)
        is_damage = ("base_dmg" in cfg or "damage" in cfg or "damage_type" in cfg)
        
        if is_damage and not face_target:
            if target == "e1":
                return "❌ 该卡牌只能以随从为目标"
                
        dmg_val = cfg.get("base_dmg", cfg.get("damage", 0))
        if dmg_val > 0:
            dtype = cfg.get("damage_type", "effect")
            engine._damage_target(run, target, dmg_val, damage_type=dtype, card=self)
            
        shield_val = cfg.get("shield", 0)
        if shield_val > 0:
            engine._gain_shield(run, "p0", shield_val)
            
        heal_val = cfg.get("heal_amount", 0)
        if heal_val > 0:
            engine._heal_target(run, "p0", heal_val)
            
        draw_val = cfg.get("draw", 0)
        if draw_val > 0:
            engine._draw_cards(run.player, draw_val, run, ignore_focus=True)
            
        minion_hp = cfg.get("minion_hp", 0)
        if minion_hp > 0:
            minion_atk = cfg.get("minion_atk", 1)
            minion_id = self.id.replace("duel_", "")
            engine._summon_minion(run, minion_id, self.name.replace("对决·", ""), minion_hp, minion_atk, 0)
            
        if self.type == "amulet":
            grid = engine._get_free_grid(run.player)
            if grid:
                cd = cfg.get("countdown", self.countdown)
                run.player.amulets[grid] = AmuletState(self.id, self.name, cd, cfg.get("amulet_desc", self.desc))
            
        return ""

@register_duel_card("duel_double_tap")
class DuelDoubleTap(Card):
    def execute(self, run, target, engine) -> str:
        stacks = 2 if self.upgraded else 1
        engine._add_buff_to(run.player, "double_tap_buff", "双发", "下一次物理伤害卡将触发额外打出", stacks)
        return ""

@register_duel_card("duel_arcane_torrent")
class DuelArcaneTorrent(Card):
    def execute(self, run, target, engine) -> str:
        X = run.node_data.get("last_x_cost_a", 0)
        single_dmg = 4 if self.upgraded else 3
        if X <= 2:
            count = X * 2
        else:
            count = X * 4
        for idx in range(len(run.enemies)):
            enemy = run.enemies[idx]
            if enemy.hp > 0:
                for _ in range(count):
                    engine._damage_target(run, f"e{idx+1}", single_dmg, damage_type="true", card=self)
        return ""

@register_duel_card("duel_quest_temporal_mystery")
class DuelQuestTemporalMystery(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["temporal_quest_progress"] = 0
        engine._add_buff_to(run.player, "temporal_quest", "时序之谜", "单回合使用4张法术牌(0/4)")
        return "🔮 [任务] 时序之谜已打出！"

@register_duel_card("duel_quest_fire_trial")
class DuelQuestFireTrial(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["fire_quest_progress"] = 0
        engine._add_buff_to(run.player, "fire_quest", "火焰审判", "对敌方领主造成法伤(0/30)")
        return "🔥 [任务] 火焰审判已打出！"

@register_duel_card("duel_quest_ancient_resonance")
class DuelQuestAncientResonance(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["ancient_quest_progress"] = 0
        engine._add_buff_to(run.player, "ancient_quest", "远古共鸣", "部署3个护符(0/3)")
        return "🔔 [任务] 远古共鸣已打出！"

@register_duel_card("duel_quest_master_of_arms")
class DuelQuestMasterOfArms(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["arms_quest_progress"] = 0
        engine._add_buff_to(run.player, "arms_quest", "兵器大师", "使用5张物理伤害牌(0/5)")
        return "🗡️ [任务] 兵器大师已打出！"

@register_duel_card("duel_quest_unbreakable_wall")
class DuelQuestUnbreakableWall(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["wall_quest_progress"] = 0
        engine._add_buff_to(run.player, "wall_quest", "不落坚壁", "护盾值达到20点(0/20)")
        return "🛡️ [任务] 不落坚壁已打出！"

@register_duel_card("duel_quest_bloody_fury")
class DuelQuestBloodyFury(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["fury_quest_progress"] = 0
        engine._add_buff_to(run.player, "fury_quest", "浴血狂暴", "生命值低于25点(0/1)")
        return "🩸 [任务] 浴血狂暴已打出！"

@register_duel_card("duel_reward_temporal_distortion")
class DuelRewardTemporalDistortion(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["extra_turns_left"] = run.node_data.get("extra_turns_left", 0) + 1
        return "⏳ [时序扭曲] 获得了 1 个额外回合！"

@register_duel_card("duel_reward_super_fireball")
class DuelRewardSuperFireball(Card):
    def execute(self, run, target, engine) -> str:
        engine._damage_target(run, target, 25, damage_type="fire", card=self)
        return ""

@register_duel_card("duel_reward_ancient_resonance")
class DuelRewardAncientResonance(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.amulet_data import AMULET_CONFIG
        except ImportError:
            from game.data.amulet_data import AMULET_CONFIG
        p = run.player
        triggered = []
        for ak, av in list(p.amulets.items()):
            del p.amulets[ak]
            p.minion_graveyard.append(av.id)
            base_id = av.id[:-1] if av.id.endswith("+") else av.id
            if base_id.startswith("duel_"):
                base_id = base_id[5:]
            cfg = AMULET_CONFIG.get(base_id)
            if cfg:
                lw_msg = ""
                is_upgraded = av.id.endswith("+")
                dmg_val = cfg.get("damage", 0)
                if dmg_val > 0:
                    if is_upgraded:
                        dmg_val += 3
                    opp_target = engine._get_first_alive_enemy(run)
                    engine._damage_target(run, opp_target, dmg_val, damage_type="thunder")
                    lw_msg = f"对敌方造成了 {dmg_val} 点雷鸣伤害"
                heal_val = cfg.get("heal", 0)
                if heal_val > 0:
                    if is_upgraded:
                        heal_val += 2
                    engine._heal_target(run, "p0", heal_val)
                    lw_msg = f"玩家恢复了 {heal_val} 点生命值"
                shield_val = cfg.get("shield", 0)
                if shield_val > 0:
                    if is_upgraded:
                        shield_val += 2
                    engine._gain_shield(run, "p0", shield_val)
                    lw_msg = f"玩家获得了 {shield_val} 点护盾"
                if lw_msg:
                    triggered.append(f"【{av.name}】:{lw_msg}")
        return "🔔 [秘钥绽放] " + "，".join(triggered)

@register_duel_card("duel_reward_master_blade")
class DuelRewardMasterBlade(Card):
    def execute(self, run, target, engine) -> str:
        engine._damage_target(run, target, 22, damage_type="slashing", card=self)
        return ""

@register_duel_card("duel_reward_wall_of_sighs")
class DuelRewardWallOfSighs(Card):
    def execute(self, run, target, engine) -> str:
        engine._gain_shield(run, "p0", 15)
        run.player.max_hp += 15
        run.player.hp += 15
        return "🛡️ [叹息之墙] 获得了 15 点护盾，最大生命值上限提升了 15 点！"

@register_duel_card("duel_reward_fury")
class DuelRewardFury(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "duel_fury_buff", "狂怒", "物理伤害额外加 6", 6)
        return "🩸 [狂暴] 获得了狂怒 Buff，物理伤害永久 +6！"

class DuelCardRegistryDict(dict):
    def _lazy_load_card(self, key):
        from ...data.duel_card_data import DUEL_CARD_CONFIG
        if key in DUEL_CARD_CONFIG:
            cfg = DUEL_CARD_CONFIG[key]
            name = cfg["name"]
            color = cfg["color"]
            ctype = cfg["type"]
            cost_a = cfg["cost_a"]
            cost_ba = cfg["cost_ba"]
            desc = cfg["desc"]
            rarity = cfg.get("rarity", "common")
            exhaust = cfg.get("exhaust", False)
            fleeting = cfg.get("fleeting", False)
            agile = cfg.get("agile", False)
            retain = cfg.get("retain", False)
            
            from ...models.state import Card
            from .duel_registry import DUEL_CARD_CLASS_REGISTRY
            import inspect
            
            if key in DUEL_CARD_CLASS_REGISTRY:
                cls, decorator_kwargs = DUEL_CARD_CLASS_REGISTRY[key]
            else:
                cls = DuelGenericCard
                decorator_kwargs = {}
                
            inst_kwargs = {
                "id": key,
                "name": name,
                "color": color,
                "type": ctype,
                "cost_a": cost_a,
                "cost_ba": cost_ba,
                "desc": desc,
            }
            for prop in ("base_dmg", "heal_amount", "countdown", "amulet_desc", "minion_hp", "minion_atk", "exhaust", "damage_type"):
                if prop in cfg:
                    inst_kwargs[prop] = cfg[prop]
            inst_kwargs.update(decorator_kwargs)
            
            sig = inspect.signature(cls.__init__)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            if has_kwargs:
                filtered = inst_kwargs
            else:
                filtered = {k: v for k, v in inst_kwargs.items() if k in sig.parameters}
                
            inst = cls(**filtered)
            inst.rarity = rarity
            inst.exhaust = exhaust
            inst.fleeting = fleeting
            inst.agile = agile
            inst.retain = retain
            inst.innate = cfg.get("innate", False)
            inst.ethereal = cfg.get("ethereal", False)
            inst.unplayable = cfg.get("unplayable", False)
            inst.damage_type = cfg.get("damage_type", "effect")
            inst.fragile = cfg.get("fragile", 0)
            if inst.fragile > 0:
                if " (易碎 " not in inst.name:
                    inst.name = f"{inst.name} (易碎 {inst.fragile})"
            self[key] = inst
            return inst
        return None

    def __getitem__(self, key):
        if isinstance(key, str) and key.endswith("+"):
            base_key = key[:-1]
            if not super().__contains__(base_key):
                self._lazy_load_card(base_key)
            if not super().__contains__(base_key):
                raise KeyError(key)
            import copy
            base_card = super().__getitem__(base_key)
            upgraded_card = copy.copy(base_card)
            upgraded_card.id = key
            if " (易碎 " in upgraded_card.name:
                parts = upgraded_card.name.split(" (易碎 ")
                name_part = parts[0]
                fragile_part = " (易碎 " + parts[1]
                upgraded_card.name = name_part + "+" + fragile_part
            else:
                if not upgraded_card.name.endswith("+"):
                    upgraded_card.name += "+"
            upgraded_card.upgraded = True
            
            from ...data.card_upgrade_data import CARD_UPGRADE_CONFIG
            up_cfg = CARD_UPGRADE_CONFIG.get(base_key, {})
            if "cost_a" in up_cfg:
                upgraded_card.cost_a = up_cfg["cost_a"]
            if "cost_ba" in up_cfg:
                upgraded_card.cost_ba = up_cfg["cost_ba"]
            if "desc" in up_cfg:
                upgraded_card.desc = up_cfg["desc"]
            if "innate" in up_cfg:
                upgraded_card.innate = up_cfg["innate"]
            if "exhaust" in up_cfg:
                upgraded_card.exhaust = up_cfg["exhaust"]
            for prop in ("base_dmg", "heal_amount", "shield_amount", "minion_hp", "minion_atk", "countdown", "amulet_desc"):
                if prop in up_cfg:
                    setattr(upgraded_card, prop, up_cfg[prop])
            return upgraded_card
            
        if not super().__contains__(key):
            self._lazy_load_card(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        if isinstance(key, str) and key.endswith("+"):
            base_key = key[:-1]
            if super().__contains__(base_key):
                return True
            from ...data.duel_card_data import DUEL_CARD_CONFIG
            return base_key in DUEL_CARD_CONFIG
        if super().__contains__(key):
            return True
        from ...data.duel_card_data import DUEL_CARD_CONFIG
        return key in DUEL_CARD_CONFIG

from ...data.duel_card_data import DUEL_CARD_CONFIG
ALL_DUEL_CARDS = DuelCardRegistryDict()
