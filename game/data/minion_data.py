MINION_CONFIG = {
    "mercenary": {
        "name": "雇佣兵",
        "skills": [
            {
                "id": "heavy_strike",
                "name": "重击",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 6 点伤害。",
                "damage": 6,
                "feedback": "对【{target}】造成了 {damage} 点伤害。"
            },
            {
                "id": "battlecry",
                "name": "战吼",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，本回合随从攻击力增加 4。",
                "atk_buff": 4,
                "feedback": "本回合攻击力提升了 {atk_buff} 点。"
            }
        ]
    },
    "shield_guard": {
        "name": "盾卫",
        "skills": [
            {
                "id": "defend",
                "name": "重整防线",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为玩家提供 2 点护盾。",
                "shield": 2,
                "feedback": "为玩家提供了 {shield} 点护盾。"
            },
            {
                "id": "bash",
                "name": "持盾撞击",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 3 点伤害，玩家获得 1 点护盾。",
                "damage": 3,
                "shield": 1,
                "feedback": "对【{target}】造成了 {damage} 点伤害，并为玩家提供了 {shield} 点护盾。"
            }
        ]
    },
    "find_familiar": {
        "name": "召唤魔宠",
        "skills": [
            {
                "id": "assist",
                "name": "奥术协助",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，玩家抽 1 张牌。",
                "draw": 1,
                "feedback": "玩家抽取了 {draw} 张牌。"
            },
            {
                "id": "charge",
                "name": "法力充能",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为玩家提供 1BA。",
                "ba_gain": 1,
                "feedback": "玩家获得了 {ba_gain} 个附赠动作点 (BA)。"
            }
        ]
    },
    "water_elemental": {
        "name": "寒冰元素",
        "skills": [
            {
                "id": "touch",
                "name": "寒冰触碰",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，扣除敌方领主下回合 1BA。",
                "feedback": "扣除了敌人【{target}】下回合 1 个附赠动作点。"
            },
            {
                "id": "lance",
                "name": "霜冻冰枪",
                "cost_a": 3,
                "cost_ba": 0,
                "desc": "消耗 3A，造成 4 点伤害，若目标是随从则使其本回合无法攻击，若为领主则扣除其下回合 1A。",
                "damage": 4,
                "feedback": "对【{target}】造成了 {damage} 点伤害。",
                "feedback_boss": "对【{target}】造成了 {damage} 点伤害，并扣掉了其下回合 1 个动作点。"
            }
        ]
    },
    "arcane_golem": {
        "name": "奥术傀儡",
        "skills": [
            {
                "id": "overload",
                "name": "能量过载",
                "cost_a": 0,
                "cost_ba": 2,
                "desc": "消耗 2BA，自身失去 4 生命，本回合攻击力 +3。",
                "self_damage": 4,
                "atk_buff": 3,
                "feedback": "自身失去 {self_damage} 点生命值，本回合攻击力增加 {atk_buff} 点。",
                "feedback_dead": "自身失去 {self_damage} 点生命值并过载死亡，本回合攻击力增加 {atk_buff} 点。"
            },
            {
                "id": "repair",
                "name": "自我修复",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，恢复自身 6 点生命值。",
                "heal": 6,
                "feedback": "恢复了自身 {heal} 点生命值，当前生命 {hp}/{max_hp}。"
            }
        ]
    },
    "minion_icerainboww": {
        "name": "Icerainboww",
        "skills": [
            {
                "id": "icerain_spray",
                "name": "冰雨散射",
                "cost_a": 1,
                "cost_ba": 1,
                "desc": "消耗 1A 1BA，对所有敌人造成 4 点寒冷伤害，并使所有敌人受到 1 层轻度寒冷易伤。",
                "damage": 4,
                "feedback": "降下漫天冰雨散射攻击敌人。"
            },
            {
                "id": "aurora_shield",
                "name": "极光屏障",
                "cost_a": 0,
                "cost_ba": 1,
                "desc": "消耗 1BA，为玩家提供 8 点护盾，且我方所有随从和玩家均获得 4 点护盾（随从获得 4 点生命恢复，玩家共获得 12 点护盾）。",
                "shield": 8,
                "feedback": "凝聚极光屏障，为所有人附加防护效果。"
            }
        ]
    },
    "mercenary+": {
        "name": "雇佣兵+",
        "skills": [
            {
                "id": "heavy_strike",
                "name": "重击+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 10 点伤害。",
                "damage": 10,
                "feedback": "对【{target}】造成了 {damage} 点伤害。"
            },
            {
                "id": "battlecry",
                "name": "战吼+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，本回合随从攻击力增加 6。",
                "atk_buff": 6,
                "feedback": "本回合攻击力提升了 {atk_buff} 点。"
            }
        ]
    },
    "shield_guard+": {
        "name": "盾卫+",
        "skills": [
            {
                "id": "defend",
                "name": "重整防线+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为玩家提供 5 点护盾。",
                "shield": 5,
                "feedback": "为玩家提供了 {shield} 点护盾。"
            },
            {
                "id": "bash",
                "name": "持盾撞击+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 5 点伤害，玩家获得 3 点护盾。",
                "damage": 5,
                "shield": 3,
                "feedback": "对【{target}】造成了 {damage} 点伤害，并为玩家提供了 {shield} 点护盾。"
            }
        ]
    },
    "find_familiar+": {
        "name": "召唤魔宠+",
        "skills": [
            {
                "id": "assist",
                "name": "奥术协助+",
                "cost_a": 1,
                "cost_ba": 0,
                "desc": "消耗 1A，玩家抽 1 张牌。",
                "draw": 1,
                "feedback": "玩家抽取了 {draw} 张牌。"
            },
            {
                "id": "charge",
                "name": "法力充能+",
                "cost_a": 1,
                "cost_ba": 0,
                "desc": "消耗 1A，为玩家提供 1BA。",
                "ba_gain": 1,
                "feedback": "玩家获得了 {ba_gain} 个附赠动作点 (BA)。"
            }
        ]
    },
    "water_elemental+": {
        "name": "寒冰元素+",
        "skills": [
            {
                "id": "touch",
                "name": "寒冰触碰+",
                "cost_a": 1,
                "cost_ba": 0,
                "desc": "消耗 1A，扣除敌方领主下回合 1BA。",
                "feedback": "扣除了敌人【{target}】下回合 1 个附赠动作点。"
            },
            {
                "id": "lance",
                "name": "霜冻冰枪+",
                "cost_a": 3,
                "cost_ba": 0,
                "desc": "消耗 3A，造成 7 点伤害，若目标是随从则使其本回合无法攻击，若为领主则扣除其下回合 1A 并使其眩晕 1 回合。",
                "damage": 7,
                "stun": 1,
                "feedback": "对【{target}】造成了 {damage} 点伤害并使其陷入眩晕！",
                "feedback_boss": "对【{target}】造成了 {damage} 点伤害，并扣掉了其下回合 1 个动作点，且使其陷入眩晕！"
            }
        ]
    },
    "arcane_golem+": {
        "name": "奥术傀儡+",
        "skills": [
            {
                "id": "overload",
                "name": "能量过载+",
                "cost_a": 0,
                "cost_ba": 1,
                "desc": "消耗 1BA，自身失去 3 生命，本回合攻击力 +4。",
                "self_damage": 3,
                "atk_buff": 4,
                "feedback": "自身失去 {self_damage} 点生命值，本回合攻击力增加 {atk_buff} 点。",
                "feedback_dead": "自身失去 {self_damage} 点生命值并过载死亡，本回合攻击力增加 {atk_buff} 点。"
            },
            {
                "id": "repair",
                "name": "自我修复+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，恢复自身 10 点生命值。",
                "heal": 10,
                "feedback": "恢复了自身 {heal} 点生命值，当前生命 {hp}/{max_hp}。"
            }
        ]
    },
    "minion_icerainboww+": {
        "name": "Icerainboww+",
        "skills": [
            {
                "id": "icerain_spray",
                "name": "冰雨散射+",
                "cost_a": 1,
                "cost_ba": 1,
                "desc": "消耗 1A 1BA，对所有敌人造成 7 点寒冷伤害，并使所有敌人受到 2 层轻度寒冷易伤。",
                "damage": 7,
                "vulnerable_layers": 2,
                "feedback": "降下漫天冰雨散射攻击敌人。"
            },
            {
                "id": "aurora_shield",
                "name": "极光屏障+",
                "cost_a": 0,
                "cost_ba": 1,
                "desc": "消耗 1BA，为玩家提供 12 点护盾，且我方所有随从和玩家均获得 6 点护盾（随从获得 6 点生命恢复，玩家共获得 18 点护盾）。",
                "player_shield": 12,
                "minion_heal": 6,
                "feedback": "凝聚极光屏障，为所有人附加防护效果。"
            }
        ]
    },
    "gate_guard": {
        "name": "门扉守卫",
        "skills": [
            {
                "id": "gate_strike",
                "name": "守卫痛击",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 6 点钝击伤害并使目标下回合动作 A 减少 1。",
                "damage": 6,
                "feedback": "对【{target}】造成了 {damage} 点钝击伤害并使其下回合动作点 A 减少 1。"
            }
        ]
    },
    "gate_guard+": {
        "name": "门扉守卫+",
        "skills": [
            {
                "id": "gate_strike",
                "name": "守卫痛击+",
                "cost_a": 1,
                "cost_ba": 0,
                "desc": "消耗 1A，造成 8 点钝击伤害并使目标下回合动作 A 减少 1。",
                "damage": 8,
                "feedback": "对【{target}】造成了 {damage} 点钝击伤害并使其下回合动作点 A 减少 1。"
            }
        ]
    },
    "officer_recruit_vanguard": {
        "name": "新兵前锋",
        "skills": []
    },
    "officer_recruit_vanguard+": {
        "name": "新兵前锋+",
        "skills": []
    },
    "officer_banner_bearer": {
        "name": "执旗辅佐官",
        "skills": [
            {
                "id": "banner_buff",
                "name": "执旗振奋",
                "cost_a": 1,
                "cost_ba": 0,
                "desc": "消耗 1A，本回合使我方另一个随从攻击力 +2。",
                "feedback": "使我方另一个随从本回合攻击力提升了 2 点。"
            }
        ]
    },
    "officer_banner_bearer+": {
        "name": "执旗辅佐官+",
        "skills": [
            {
                "id": "banner_buff",
                "name": "执旗振奋+",
                "cost_a": 1,
                "cost_ba": 0,
                "desc": "消耗 1A，本回合使我方另一个随从攻击力 +3，且自身获得 3 护盾。",
                "feedback": "使我方另一个随从本回合攻击力提升了 3 点，且自身获得 3 护盾。"
            }
        ]
    },
    "commander_patrol_captain": {
        "name": "巡逻队队长",
        "skills": [
            {
                "id": "patrol_order",
                "name": "巡逻指令",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为我方所有随从恢复 3 点生命值，并获得 3 点护盾。",
                "feedback": "发布巡逻指令，为我方所有随从恢复了 3 生命并提供了 3 点护盾。"
            }
        ]
    },
    "commander_patrol_captain+": {
        "name": "巡逻队队长+",
        "skills": [
            {
                "id": "patrol_order",
                "name": "巡逻指令+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为我方所有随从恢复 5 点生命值，并获得 5 点护盾。",
                "feedback": "发布巡逻指令+，为我方所有随从恢复了 5 生命并提供了 5 点护盾。"
            }
        ]
    },
    "officer_royal_guard": {
        "name": "近卫铁骑",
        "skills": []
    },
    "officer_royal_guard+": {
        "name": "近卫铁骑+",
        "skills": []
    },
    "commander_garrison_leader": {
        "name": "要塞卫队长",
        "skills": [
            {
                "id": "garrison_wall",
                "name": "要塞铁壁",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为玩家提供 6 护盾，若有士兵则使其回复 3 生命。",
                "feedback": "为玩家提供了 6 点护盾，并为士兵随从回复了 3 生命值。"
            }
        ]
    },
    "commander_garrison_leader+": {
        "name": "要塞卫队长+",
        "skills": [
            {
                "id": "garrison_wall",
                "name": "要塞铁壁+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，为玩家提供 9 护盾，若有士兵则使其回复 5 生命。",
                "feedback": "为玩家提供了 9 点护盾，并为士兵随从回复了 5 生命值。"
            }
        ]
    },
    "officer_squad_skirmisher": {
        "name": "突击轻步兵",
        "skills": []
    },
    "officer_squad_skirmisher+": {
        "name": "突击轻步兵+",
        "skills": []
    },
    "commander_valiant_herald": {
        "name": "英勇传令官",
        "skills": [
            {
                "id": "charge_signal",
                "name": "冲锋信号",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，使我方全体随从本回合攻击力 +2。",
                "feedback": "发出冲锋信号，我方全体随从本回合攻击力 +2。"
            }
        ]
    },
    "commander_valiant_herald+": {
        "name": "英勇传令官+",
        "skills": [
            {
                "id": "charge_signal",
                "name": "冲锋信号+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，使我方全体随从本回合攻击力 +3。",
                "feedback": "发出冲锋信号+，我方全体随从本回合攻击力 +3。"
            }
        ]
    },
    "commander_steelclad_tactician": {
        "name": "重甲战术家",
        "skills": [
            {
                "id": "tactical_strike",
                "name": "战术压制",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 6 钝击伤害，斩杀时召唤两个【步兵轻卒】。",
                "feedback": "执行战术压制对【{target}】造成了 6 点伤害。"
            }
        ]
    },
    "commander_steelclad_tactician+": {
        "name": "重甲战术家+",
        "skills": [
            {
                "id": "tactical_strike",
                "name": "战术压制+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成 9 钝击伤害，斩杀时召唤两个【步兵轻卒+】。",
                "feedback": "执行战术压制+对【{target}】造成了 9 点伤害。"
            }
        ]
    },
    "officer_blade_dancer": {
        "name": "双刃轻卫",
        "skills": [
            {
                "id": "double_slash",
                "name": "双重斩击",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成两次 4 点伤害。",
                "feedback": "对【{target}】发动双重斩击！"
            }
        ]
    },
    "officer_blade_dancer+": {
        "name": "双刃轻卫+",
        "skills": [
            {
                "id": "double_slash",
                "name": "双重斩击+",
                "cost_a": 2,
                "cost_ba": 0,
                "desc": "消耗 2A，造成两次 6 点伤害。",
                "feedback": "对【{target}】发动双重斩击+！"
            }
        ]
    },
    "commander_aurora_emperor": {
        "name": "极光圣帝·阿奎斯",
        "skills": [
            {
                "id": "aurora_judgment",
                "name": "极光审判",
                "cost_a": 3,
                "cost_ba": 0,
                "desc": "消耗 3A，对所有敌人造成 8 点光耀伤害，若协作达到 15 以上，则转为 15 点真伤。",
                "feedback": "降下极光审判净化敌方全体！"
            }
        ]
    },
    "commander_aurora_emperor+": {
        "name": "极光圣帝·阿奎斯+",
        "skills": [
            {
                "id": "aurora_judgment",
                "name": "极光审判+",
                "cost_a": 3,
                "cost_ba": 0,
                "desc": "消耗 3A，对所有敌人造成 12 点光耀伤害，若协作达到 15 以上，则转为 22 点真伤。",
                "feedback": "降下极光审判+净化敌方全体！"
            }
        ]
    },
    "officer_soldier_token": {
        "name": "步兵轻卒",
        "skills": []
    },
    "officer_soldier_token+": {
        "name": "步兵轻卒+",
        "skills": []
    }
}
