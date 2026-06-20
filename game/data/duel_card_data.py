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

AOE_CARDS = {
    "meteor_swarm", "doomsday_judgment", "glacier_tempest", "frost_nova",
    "abyss_collapse", "shockwave"
}

DUEL_SPECIFIC_OVERRIDES = {
    "duel_meteor_swarm": {
        "cost_a": 2,
        "cost_ba": 1,
        "desc": "对所有敌人造成 6d6 随机火焰伤害。消耗。",
        "aoe": True
    },
    "duel_doomsday_judgment": {
        "cost_a": 3,
        "cost_ba": 0,
        "desc": "对所有敌人造成 12 点黯蚀伤害并眩晕他们 1 回合。消耗。",
        "aoe": True
    },
    "duel_glacier_tempest": {
        "cost_a": 2,
        "cost_ba": 0,
        "desc": "对所有敌人造成 8 点冰霜伤害。若场上存在任何我方随从，则获得等同于本次造成总伤害值 50% 的护盾。消耗。",
        "aoe": True
    },
    "duel_frost_nova": {
        "cost_a": 2,
        "cost_ba": 0,
        "desc": "对所有敌人造成 10 点冰霜伤害，对所有敌人施加 2 层轻度寒冷易伤并使所有敌人眩晕 1 回合。消耗。",
        "aoe": True
    },
    "duel_abyss_collapse": {
        "cost_a": 2,
        "cost_ba": 0,
        "desc": "对所有敌人造成 18 点黯蚀伤害。若目标被眩晕，则造成双倍伤害。消耗。",
        "aoe": True
    },
    "duel_shockwave": {
        "cost_a": 1,
        "cost_ba": 0,
        "desc": "对所有敌人施加 2 层轻度易伤和 2 层虚弱。消耗。",
        "aoe": True
    },
    "duel_arcane_intellect": {
        "cost_a": 2,
        "cost_ba": 0
    },
    "duel_calculated_gamble": {
        "cost_a": 2,
        "cost_ba": 0
    },
    "duel_mana_overload": {
        "name": "能量逆载",
        "color": "wizard",
        "type": "spell",
        "cost_a": 2,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "（只能选择随从）造成 10 点伤害。如果你当前没有额外动作点（0BA），则伤害翻倍；如果击杀了随从，获得 2BA。",
        "face_target": False
    },
    "duel_destiny_scales": {
        "name": "命运天平",
        "color": "wizard",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 1,
        "rarity": "rare",
        "desc": "（只能选择随从）将一个随从的攻击力与生命值对调。如果该随从被眩晕或易伤，则对其额外造成 8 点真实伤害并抽 1 张牌。",
        "face_target": False
    },
    "duel_ancient_blessing": {
        "name": "古老祈福",
        "color": "neutral",
        "type": "spell",
        "cost_a": 1,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "随机强化一个我方随从（+2/+2）。如果你拥有多于 2 个随从，则全体强化且你获得 8 点护盾；如果你没有任何随从，则改为抽 2 张牌。",
        "aoe": True
    },
    "duel_storm_barrier": {
        "name": "雷雨屏障",
        "color": "neutral",
        "type": "spell",
        "cost_a": 2,
        "cost_ba": 0,
        "rarity": "rare",
        "desc": "获得 12 点护盾。如果你当前的生命值低于 80 点，获得护盾值增加 8 点；如果敌方场上有随从，则随机对敌方一个随从造成 6 点雷鸣伤害并施加 2 层虚弱。",
        "aoe": True
    }
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
                "name": val.get('name', ''),
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
                    
            dval["desc"] = val.get("desc", "")
            
            if cid in AOE_CARDS:
                dval["aoe"] = True
            
            is_face = (cid in FACE_DAMAGE_CARDS)
            is_damage = ("base_dmg" in dval or "damage" in dval or "damage_type" in val)
            
            if dcid in DUEL_SPECIFIC_OVERRIDES:
                dval.update(DUEL_SPECIFIC_OVERRIDES[dcid])
            else:
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

    for cid in ("duel_mana_overload", "duel_destiny_scales", "duel_ancient_blessing", "duel_storm_barrier"):
        if cid in DUEL_SPECIFIC_OVERRIDES:
            cfg = DUEL_SPECIFIC_OVERRIDES[cid]
            DUEL_CARD_CONFIG[cid] = {
                "name": cfg["name"],
                "color": cfg["color"],
                "type": cfg["type"],
                "cost_a": cfg["cost_a"],
                "cost_ba": cfg["cost_ba"],
                "rarity": cfg["rarity"],
                "desc": cfg["desc"],
                "aoe": cfg.get("aoe", False),
                "face_target": cfg.get("face_target", True)
            }

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
