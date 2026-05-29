ENEMY_CONFIG = {
    "Icerainboww": {
        "name": "Icerainboww",
        "type": "boss",
        "hp": "160",
        "actions": "2A 0BA",
        "intents": [
            {"id": "icerain_shoot", "val": 2, "desc": "冰雨弓射击 (造成 2 寒冷伤害，使玩家下回合失去 1A)"},
            {"id": "fury", "val": 1, "desc": "愤怒 (获得 1 层愤怒buff，被打出珍奇或传奇卡牌激怒时自身增伤)"},
            {"id": "smash_attack", "val": 10, "desc": "粉碎攻击 (造成 10 寒冷伤害，并使玩家受到轻度寒冷易伤)"},
            {"id": "aurora_shield", "val": 12, "desc": "极光屏障 (获得 12 护盾并净化 1 负面 Buff，无负面时额外获得 4 护盾)"},
            {"id": "winter_gaze", "val": 4, "desc": "寒冬凝视 (造成 4 心灵伤害，并使玩家受到轻度寒冷易伤)"},
            {"id": "frost_blast", "val": 6, "desc": "冰霜爆震 (对玩家与所有我方随从造成 6 寒冷伤害)"}
        ]
    },
    "远古红龙": {
        "name": "远古红龙",
        "type": "boss",
        "hp": "60",
        "actions": "1A 2BA",
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
        "type": "boss",
        "hp": "120",
        "actions": "1A 2BA",
        "passive": "死亡律动 (每当玩家打出一张牌，玩家受到 1 点力场伤害)",
        "intents": [
            {"id": "debuff", "val": 0, "desc": "邪恶之语 (将晕眩与苦恼放入玩家牌组)"},
            {"id": "multi_attack", "val": 2, "desc": "血弹喷射 (造成 2 点伤害，重复 8 次)"},
            {"id": "big_attack", "val": 20, "desc": "毁灭之痛 (造成 20 点伤害)"},
            {"id": "strength_buff", "val": 2, "desc": "充能 (获得 2 层力量，使后续伤害增加 2)"},
            {"id": "defend_large", "val": 15, "desc": "暗影护盾 (获得 15 或 20 护盾)"},
            {"id": "defend_normal", "val": 10, "desc": "护盾 (获得 10 护盾)"},
            {"id": "drain_ba", "val": 1, "desc": "虚空之歌 (使玩家下回合失去 1BA)"},
            {"id": "heart_strike", "val": 4, "desc": "心跳重击 (造成 4 伤害)"},
            {"id": "gaze_discard", "val": 1, "desc": "虚无凝视 (迫使玩家随机丢弃 1 张手牌)"},
            {"id": "heart_heal", "val": 10, "desc": "回潮 (恢复 10 生命)"}
        ],
        "cycle_info": [
            "第一回合: 邪恶之语 (将晕眩与苦恼放入玩家牌组) + 暗影护盾(获得 15 护盾) + 虚空之歌 (使玩家下回合失去 1BA)",
            "第二回合: 血弹喷射 (造成 2 点伤害，重复 8 次) + 护盾(获得 10 护盾) + 心跳重击 (造成 4 伤害)",
            "第三回合: 毁灭之痛 (造成 20 点伤害) + 护盾(获得 10 护盾) + 虚无凝视 (迫使玩家随机丢弃 1 张手牌)",
            "第四回合: 充能 (获得 2 层力量，使后续伤害增加 2) + 暗影护盾(获得 20 护盾) + 回潮 (恢复 10 生命)"
        ]
    },
    "地精百夫长": {
        "name": "地精百夫长",
        "type": "elite",
        "hp": "30 (+ 3 * 关卡数)",
        "actions": "1A 1BA",
        "intents": [
            {"id": "heavy_strike", "val": 8, "desc": "重击 (造成 8 伤害)"},
            {"id": "defend", "val": 6, "desc": "举盾 (获得 6 护盾)"},
            {"id": "command", "val": 0, "desc": "咆哮 (下回合获得 1 个动作)"}
        ]
    },
    "石像鬼祭司": {
        "name": "石像鬼祭司",
        "type": "elite",
        "hp": "38 (+ 3 * 关卡数)",
        "actions": "1A 1BA",
        "intents": [
            {"id": "attack", "val": 5, "desc": "惩戒 (造成 5 伤害)"},
            {"id": "defend", "val": 8, "desc": "暗影护盾 (获得 8 护盾)"},
            {"id": "drain", "val": 4, "desc": "生命汲取 (造成 4 伤害，并回复 4 生命)"}
        ]
    },
    "狂暴兽王": {
        "name": "狂暴兽王",
        "type": "elite",
        "hp": "32 (+ 3 * 关卡数)",
        "actions": "1A 1BA",
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
        "type": "elite",
        "hp": "45 (+ 3 * 关卡数)",
        "actions": "1A 1BA",
        "intents": [
            {"id": "quake", "val": 5, "desc": "大地崩裂 (造成 5 伤害，并剥夺玩家 1BA)"},
            {"id": "defend", "val": 12, "desc": "黑曜石防护 (获得 12 护盾)"}
        ]
    },
    "幽灵大魔法师": {
        "name": "幽灵大魔法师",
        "type": "elite",
        "hp": "36 (+ 3 * 关卡数)",
        "actions": "1A 1BA",
        "intents": [
            {"id": "spell_burst", "val": 8, "desc": "奥术闪电 (造成 8 伤害)"},
            {"id": "mana_drain", "val": 4, "desc": "魔力虹吸 (造成 4 伤害，并丢弃手牌)"}
        ]
    },
    "暗影影魔": {
        "name": "暗影影魔",
        "type": "elite",
        "hp": "34 (+ 3 * 关卡数)",
        "actions": "1A 1BA",
        "intents": [
            {"id": "shadow_strike", "val": 6, "desc": "影袭 (造成 6 伤害，且无视玩家护盾)"},
            {"id": "defend", "val": 6, "desc": "虚化 (获得 6 护盾)"}
        ]
    },
    "地精突袭者": {
        "name": "地精突袭者",
        "type": "normal",
        "hp": "12 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "石像鬼守卫": {
        "name": "石像鬼守卫",
        "type": "normal",
        "hp": "18 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "堕落学徒": {
        "name": "堕落学徒",
        "type": "normal",
        "hp": "14 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "狂暴野兽": {
        "name": "狂暴野兽",
        "type": "normal",
        "hp": "15 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "幽灵法师": {
        "name": "幽灵法师",
        "type": "normal",
        "hp": "16 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "冰霜史莱姆": {
        "name": "冰霜史莱姆",
        "type": "normal",
        "hp": "10 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "骷髅弓箭手": {
        "name": "骷髅弓箭手",
        "type": "normal",
        "hp": "12 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "剧毒蜘蛛": {
        "name": "剧毒蜘蛛",
        "type": "normal",
        "hp": "10 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "黑曜石巨人": {
        "name": "黑曜石巨人",
        "type": "normal",
        "hp": "22 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "暗影刺客": {
        "name": "暗影刺客",
        "type": "normal",
        "hp": "14 (+ 2 * 关卡数)",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "攻击 (造成随机伤害，基于关卡数: 3 + 关卡数//2 + 随机值)"},
            {"id": "defend", "desc": "防御 (获得随机护盾，基于关卡数: 3 + 关卡数 + 随机值)"}
        ]
    },
    "魔仆": {
        "name": "魔仆",
        "type": "summon",
        "hp": "5",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "准备攻击 (造成 1 伤害)"}
        ]
    },
    "狂暴猎犬": {
        "name": "狂暴猎犬",
        "type": "summon",
        "hp": "8",
        "actions": "1A 0BA",
        "intents": [
            {"id": "attack", "desc": "扑咬 (造成 2 伤害)"}
        ]
    }
}
