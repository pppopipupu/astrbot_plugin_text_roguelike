# 事件静态配置数据

EVENT_CONFIG = {
    "fountain": {
        "description": "你在荒野中发现了一座泛着蓝光的神秘喷泉。喷泉中央有一座双手捧杯 of 雕像。",
        "options": {
            "drink_fountain": {
                "text": "饮用泉水 (回复 10 生命值)",
                "action": "drink_fountain",
                "heal_amount": 10,
                "feedback": "你喝下了泉水，生命值回复了 {heal_amount} 点。已前往下一关。"
            },
            "coin_fountain": {
                "text": "投入金币 (消耗 10 金币，获得一张随机蓝色卡牌)",
                "action": "coin_fountain",
                "gold_cost": 10,
                "feedback": "你在泉水中投入了 {gold_cost} 金币，泉水闪烁，你获得了【{card_name}】。已前往下一关。",
                "feedback_insufficient": "❌ 你的金币不足 10。"
            },
            "leave_event": {
                "text": "悄悄离开 (什么都不发生)",
                "action": "leave_event",
                "feedback": "你决定不节外生枝，继续赶路。已前往下一关。"
            }
        }
    },
    "knight": {
        "description": "一位受伤 of 奥术骑士靠在树旁，他的盔甲已经破损，正虚弱地向你求助。",
        "options": {
            "help_knight": {
                "text": "施以援手 (消耗 1张 绷带包扎，获得 随随从卡: 盾卫)", # 等等，这里原先是“随随从卡”还是“随从卡”？
                # 原版第 101 行是“随从卡: 盾卫”，我们还是遵循原版，保持效果不变：
                "text": "施以援手 (消耗 1张 绷带包扎，获得 随从卡: 盾卫)",
                "action": "help_knight",
                "consume_card": "first_aid",
                "reward_card": "shield_guard",
                "feedback": "你将绷带给予骑士治疗。为了答谢，【盾卫】加入了你的卡组。已前往下一关。",
                "feedback_insufficient": "❌ 你的卡组中没有【绷带包扎】卡牌！"
            },
            "rob_knight": {
                "text": "趁火打劫 (获得 25 金币)",
                "action": "rob_knight",
                "gold_gain": 25,
                "feedback": "你不顾骑士的反抗夺走了他的财物，获得 {gold_gain} 金币。已前往下一关。"
            },
            "leave_event": {
                "text": "置之不理 (继续赶路)",
                "action": "leave_event",
                "feedback": "你决定不节外生枝，继续赶路。已前往下一关。"
            }
        }
    },
    "altar": {
        "description": "前方是一处古老的法师祭坛，祭坛上的水晶依然散发着狂暴 of 奥术波动。",
        "options": {
            "absorb_altar": {
                "text": "汲取奥术 (获得一张能力卡: 奥术充能)",
                "action": "absorb_altar",
                "reward_card": "arcane_charge",
                "feedback": "你吸收了奥术波动的力量，将【奥术充能】加入卡组。已前往下一关。"
            },
            "break_altar": {
                "text": "摧毁水晶 (获得 20 金币，但失去 4 点生命值)",
                "action": "break_altar",
                "gold_gain": 20,
                "hp_loss": 4,
                "feedback": "你用法杖敲碎了祭坛上的水晶并收集了碎片（获得 {gold_gain} 金币），但被震荡的爆风伤及（失去 {hp_loss} 点生命值）。已前往下一关。"
            },
            "leave_event": {
                "text": "绕道而行 (绕开祭坛)",
                "action": "leave_event",
                "feedback": "你决定不节外生枝，继续赶路。已前往下一关。"
            }
        }
    },
    # 离开事件时的全局回退选项
    "leave_default": {
        "text": "离开事件",
        "action": "leave_event",
        "feedback": "你决定不节外生枝，继续赶路。已前往下一关。"
    }
}
