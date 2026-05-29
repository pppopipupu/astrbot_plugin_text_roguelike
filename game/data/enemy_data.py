ENEMY_CONFIG = {
    "远古红龙": {
        "name": "远古红龙",
        "intents": [
            {"id": "attack", "val": 12, "desc": "喷吐火焰 (造成 12 伤害)"},
            {"id": "defend", "val": 10, "desc": "龙鳞防护 (获得 10 护盾)"},
            {"id": "summon", "val": 0, "desc": "召唤魔仆"},
            {"id": "attack_all", "val": 6, "desc": "扫尾 (造成 6 伤害，并攻击我方所有随从)"}
        ],
        "summon_goblin": {
            "name": "魔仆",
            "hp": 5,
            "max_hp": 5,
            "intent_val": 1,
            "intent_desc": "准备攻击 (造成 1 伤害)"
        }
    },
    "腐化之心": {
        "name": "腐化之心",
        "intents": [
            {"id": "debuff", "val": 0, "desc": "邪恶之语 (将晕眩与苦恼放入玩家牌组)"},
            {"id": "multi_attack", "val": 2, "desc": "血弹喷射 (造成 2 点伤害，重复 8 次)"},
            {"id": "big_attack", "val": 20, "desc": "毁灭之痛 (造成 20 点伤害)"},
            {"id": "strength_buff", "val": 2, "desc": "充能 (获得 2 层力量，使后续伤害增加 2)"}
        ]
    },
    "地精百夫长": {
        "name": "地精百夫长",
        "intents": [
            {"id": "heavy_strike", "val": 8, "desc": "重击 (造成 8 伤害)"},
            {"id": "defend", "val": 6, "desc": "举盾 (获得 6 护盾)"},
            {"id": "command", "val": 0, "desc": "咆哮 (下回合获得 1 个动作)"}
        ]
    },
    "石像鬼祭司": {
        "name": "石像鬼祭司",
        "intents": [
            {"id": "attack", "val": 5, "desc": "惩戒 (造成 5 伤害)"},
            {"id": "defend", "val": 8, "desc": "暗影护盾 (获得 8 护盾)"},
            {"id": "drain", "val": 4, "desc": "生命汲取 (造成 4 伤害，并回复 4 生命)"}
        ]
    },
    "狂暴兽王": {
        "name": "狂暴兽王",
        "intents": [
            {"id": "attack", "val": 6, "desc": "鞭笞 (造成 6 伤害)"},
            {"id": "summon_beast", "val": 0, "desc": "野兽召唤 (召唤一只狂暴猎犬)"},
            {"id": "defend", "val": 5, "desc": "猎手防线 (获得 5 护盾)"}
        ],
        "summon_hound": {
            "name": "狂暴猎犬",
            "hp": 8,
            "max_hp": 8,
            "intent_val": 2,
            "intent_desc": "扑咬 (造成 2 伤害)"
        }
    },
    "黑曜石巨灵": {
        "name": "黑曜石巨灵",
        "intents": [
            {"id": "quake", "val": 5, "desc": "大地崩裂 (造成 5 伤害，并剥夺玩家 1BA)"},
            {"id": "defend", "val": 12, "desc": "黑曜石防护 (获得 12 护盾)"}
        ]
    },
    "幽灵大魔法师": {
        "name": "幽灵大魔法师",
        "intents": [
            {"id": "spell_burst", "val": 8, "desc": "奥术闪电 (造成 8 伤害)"},
            {"id": "mana_drain", "val": 4, "desc": "魔力虹吸 (造成 4 伤害，并丢弃手牌)"}
        ]
    },
    "暗影影魔": {
        "name": "暗影影魔",
        "intents": [
            {"id": "shadow_strike", "val": 6, "desc": "影袭 (造成 6 伤害，且无视玩家护盾)"},
            {"id": "defend", "val": 6, "desc": "虚化 (获得 6 护盾)"}
        ]
    }
}
