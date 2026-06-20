from .neutral_card_data import NEUTRAL_CARD_CONFIG
from .wizard_card_data import WIZARD_CARD_CONFIG
from .warrior_card_data import WARRIOR_CARD_CONFIG

DUEL_CHARACTER_CONFIG = {
    "战士": {
        "hp": 200,
        "max_hp": 200,
        "deck": ["duel_warrior_strike", "duel_warrior_strike", "duel_warrior_strike", "duel_warrior_strike", "duel_warrior_defend", "duel_warrior_defend", "duel_warrior_defend", "duel_warrior_bash"]
    },
    "法师": {
        "hp": 200,
        "max_hp": 200,
        "deck": ["duel_magic_missile", "duel_magic_missile", "duel_magic_missile", "duel_fireball", "duel_shield", "duel_shield", "duel_shield", "duel_mage_ward"]
    }
}

DUEL_CARD_CONFIG = {}

FACE_DAMAGE_CARDS = {
    "strike", "heavy_strike", "execut", "counterstrike",
    "fireball", "sunburst",
    "warrior_strike", "heavy_blade", "bludgeon",
    "arcane_torrent", "warrior_bash", "warrior_anger", "body_slam",
    "meteor_swarm", "doomsday_judgment"
}

RUSH_MINIONS = {
    "officer_recruit_vanguard", "water_elemental"
}

CHARGE_MINIONS = {
    "officer_squad_skirmisher"
}

def _transform_configs():
    source_configs = [
        (NEUTRAL_CARD_CONFIG, "neutral"),
        (WIZARD_CARD_CONFIG, "wizard"),
        (WARRIOR_CARD_CONFIG, "warrior")
    ]
    for cfg, color in source_configs:
        for cid, val in cfg.items():
            dcid = f"duel_{cid}"
            cost_a = val.get("cost_a", 0)
            cost_ba = val.get("cost_ba", 0)
            if cost_a != -1:
                cost_a = min(3, cost_a)
            if cost_ba != -1:
                cost_ba = min(1, cost_ba)
            
            dval = {
                "name": f"对决·{val.get('name', '')}",
                "color": color,
                "type": val.get("type", "spell"),
                "cost_a": cost_a,
                "cost_ba": cost_ba,
                "rarity": val.get("rarity", "common"),
                "exhaust": val.get("exhaust", False),
                "fleeting": val.get("fleeting", False),
                "agile": val.get("agile", False),
                "retain": val.get("retain", False)
            }
            
            if "base_dmg" in val:
                dval["base_dmg"] = max(3, int(val["base_dmg"] * 0.7))
            if "damage" in val:
                dval["damage"] = max(3, int(val["damage"] * 0.7))
            if "shield" in val:
                dval["shield"] = max(3, int(val["shield"] * 0.7))
            if "heal_amount" in val:
                dval["heal_amount"] = max(3, int(val["heal_amount"] * 0.7))
            for k in ("countdown", "minion_hp", "minion_atk", "damage_type", "amulet_desc"):
                if k in val:
                    dval[k] = val[k]
            
            is_face = (cid in FACE_DAMAGE_CARDS)
            is_damage = ("base_dmg" in dval or "damage" in dval or "damage_type" in val)
            
            if is_damage and dval["type"] == "spell":
                has_fixed_dmg = False
                dmg_val = 0
                if "base_dmg" in val and val["base_dmg"] > 0:
                    has_fixed_dmg = True
                    dmg_val = dval["base_dmg"]
                elif "damage" in val and val["damage"] > 0:
                    has_fixed_dmg = True
                    dmg_val = dval["damage"]
                
                if has_fixed_dmg:
                    if is_face:
                        dval["desc"] = f"（可选择领主或随从）造成 {dmg_val} 点伤害。"
                        dval["face_target"] = True
                    else:
                        dval["desc"] = f"（只能选择随从）造成 {dmg_val} 点伤害。"
                        dval["face_target"] = False
                else:
                    orig_desc = val.get("desc", "")
                    if is_face:
                        dval["desc"] = f"（可选择领主或随从）{orig_desc}"
                        dval["face_target"] = True
                    else:
                        dval["desc"] = f"（只能选择随从）{orig_desc}"
                        dval["face_target"] = False
            else:
                dval["desc"] = val.get("desc", "")
            
            if cid in RUSH_MINIONS:
                dval["rush"] = True
                dval["desc"] = "突进。" + dval["desc"]
            if cid in CHARGE_MINIONS:
                dval["charge"] = True
                dval["desc"] = "冲锋。" + dval["desc"]
                
            DUEL_CARD_CONFIG[dcid] = dval

_transform_configs()

QUEST_CONFIGS = {
    "duel_quest_temporal_mystery": {
        "name": "时序之谜",
        "color": "wizard",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "法师任务。打出挂起。当你在单回合内打出至少 4 张法术牌时完成，奖励：时序扭曲。"
    },
    "duel_quest_fire_trial": {
        "name": "火焰审判",
        "color": "wizard",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "法师任务。打出挂起。当你对敌方领主累计造成 30 点法术伤害时完成，奖励：超级火球。"
    },
    "duel_quest_ancient_resonance": {
        "name": "远古共鸣",
        "color": "wizard",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "法师任务。打出挂起。当你累计部署 3 个护符时完成，奖励：秘钥绽放。"
    },
    "duel_quest_master_of_arms": {
        "name": "兵器大师",
        "color": "warrior",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "战士任务。打出挂起。当你累计使用 5 张物理伤害牌时完成，奖励：终结巨剑。"
    },
    "duel_quest_unbreakable_wall": {
        "name": "不落坚壁",
        "color": "warrior",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "战士任务。打出挂起。当你的护盾值累计达到 20 点以上时完成，奖励：叹息之墙。"
    },
    "duel_quest_bloody_fury": {
        "name": "浴血狂暴",
        "color": "warrior",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "战士任务。打出挂起。当你的生命值低于 25 点时完成，奖励：狂暴。"
    },
    
    "duel_reward_temporal_distortion": {
        "name": "时序扭曲",
        "color": "wizard",
        "type": "spell",
        "cost_a": 0,
        "cost_ba": 0,
        "rarity": "legendary",
        "exhaust": True,
        "desc": "获得一个额外回合。消耗。"
    },
    "duel_reward_super_fireball": {
        "name": "超级火球",
        "color": "wizard",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "legendary",
        "base_dmg": 25,
        "face_target": True,
        "exhaust": True,
        "desc": "（可选择领主或随从）造成 25 点火焰伤害。消耗。"
    },
    "duel_reward_ancient_resonance": {
        "name": "秘钥绽放",
        "color": "wizard",
        "type": "spell",
        "cost_a": 0,
        "cost_ba": 0,
        "rarity": "legendary",
        "exhaust": True,
        "desc": "使在场所有我方护符立刻吟唱结束触发谢幕曲。消耗。"
    },
    "duel_reward_master_blade": {
        "name": "终结巨剑",
        "color": "warrior",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 1,
        "rarity": "legendary",
        "base_dmg": 22,
        "face_target": True,
        "exhaust": True,
        "desc": "（可选择领主或随从）造成 22 点物理伤害。消耗。"
    },
    "duel_reward_wall_of_sighs": {
        "name": "叹息之墙",
        "color": "warrior",
        "type": "spell",
        "cost_a": 0,
        "cost_ba": 0,
        "rarity": "legendary",
        "exhaust": True,
        "desc": "获得 15 点护盾，最大生命值永久提升 15 点。消耗。"
    },
    "duel_reward_fury": {
        "name": "狂暴",
        "color": "warrior",
        "type": "spell",
        "cost_a": 0,
        "cost_ba": 0,
        "rarity": "legendary",
        "exhaust": True,
        "desc": "物理伤害加成永久额外 +6。消耗。"
    }
}

DUEL_CARD_CONFIG.update(QUEST_CONFIGS)
