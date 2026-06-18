from typing import Optional
from ...models.state import Card, BuffState
from .registry import register_card

class DuelGenericCard(Card):
    def execute(self, run, target, engine) -> str:
        try:
            from ...data.card_data import CARD_CONFIG
        except ImportError:
            from game.data.card_data import CARD_CONFIG
        cfg = CARD_CONFIG.get(self.id, {})
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
            
        return ""

@register_card("duel_quest_temporal_mystery")
class DuelQuestTemporalMystery(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["temporal_quest_progress"] = 0
        engine._add_buff_to(run.player, "temporal_quest", "时序之谜", "单回合使用4张法术牌(0/4)")
        return "🔮 [任务] 时序之谜已打出！"

@register_card("duel_quest_fire_trial")
class DuelQuestFireTrial(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["fire_quest_progress"] = 0
        engine._add_buff_to(run.player, "fire_quest", "火焰审判", "对敌方领主造成法伤(0/30)")
        return "🔥 [任务] 火焰审判已打出！"

@register_card("duel_quest_ancient_resonance")
class DuelQuestAncientResonance(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["ancient_quest_progress"] = 0
        engine._add_buff_to(run.player, "ancient_quest", "远古共鸣", "部署3个护符(0/3)")
        return "🔔 [任务] 远古共鸣已打出！"

@register_card("duel_quest_master_of_arms")
class DuelQuestMasterOfArms(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["arms_quest_progress"] = 0
        engine._add_buff_to(run.player, "arms_quest", "兵器大师", "使用5张物理伤害牌(0/5)")
        return "🗡️ [任务] 兵器大师已打出！"

@register_card("duel_quest_unbreakable_wall")
class DuelQuestUnbreakableWall(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["wall_quest_progress"] = 0
        engine._add_buff_to(run.player, "wall_quest", "不落坚壁", "护盾值达到20点(0/20)")
        return "🛡️ [任务] 不落坚壁已打出！"

@register_card("duel_quest_bloody_fury")
class DuelQuestBloodyFury(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["fury_quest_progress"] = 0
        engine._add_buff_to(run.player, "fury_quest", "浴血狂暴", "生命值低于25点(0/1)")
        return "🩸 [任务] 浴血狂暴已打出！"

@register_card("duel_reward_temporal_distortion")
class DuelRewardTemporalDistortion(Card):
    def execute(self, run, target, engine) -> str:
        run.node_data["extra_turns_left"] = run.node_data.get("extra_turns_left", 0) + 1
        return "⏳ [时序扭曲] 获得了 1 个额外回合！"

@register_card("duel_reward_super_fireball")
class DuelRewardSuperFireball(Card):
    def execute(self, run, target, engine) -> str:
        engine._damage_target(run, target, 25, damage_type="fire", card=self)
        return ""

@register_card("duel_reward_ancient_resonance")
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

@register_card("duel_reward_master_blade")
class DuelRewardMasterBlade(Card):
    def execute(self, run, target, engine) -> str:
        engine._damage_target(run, target, 22, damage_type="slashing", card=self)
        return ""

@register_card("duel_reward_wall_of_sighs")
class DuelRewardWallOfSighs(Card):
    def execute(self, run, target, engine) -> str:
        engine._gain_shield(run, "p0", 15)
        run.player.max_hp += 15
        run.player.hp += 15
        return "🛡️ [叹息之墙] 获得了 15 点护盾，最大生命值上限提升了 15 点！"

@register_card("duel_reward_fury")
class DuelRewardFury(Card):
    def execute(self, run, target, engine) -> str:
        engine._add_buff_to(run.player, "duel_fury_buff", "狂怒", "物理伤害额外加 6", 6)
        return "🩸 [狂暴] 获得了狂怒 Buff，物理伤害永久 +6！"

def get_duel_card_class(cid: str):
    if cid.startswith("duel_"):
        if cid in ("duel_quest_temporal_mystery", "duel_quest_fire_trial", "duel_quest_ancient_resonance",
                  "duel_quest_master_of_arms", "duel_quest_unbreakable_wall", "duel_quest_bloody_fury",
                  "duel_reward_temporal_distortion", "duel_reward_super_fireball", "duel_reward_ancient_resonance",
                  "duel_reward_master_blade", "duel_reward_wall_of_sighs", "duel_reward_fury"):
            return None
        return DuelGenericCard
    return None
