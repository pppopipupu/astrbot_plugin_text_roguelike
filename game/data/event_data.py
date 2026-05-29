EVENT_CONFIG = {
    "fountain": {
        "description": "你在荒野中发现了一座泛着蓝光的神秘喷泉。喷泉中央有一座双手捧杯的雕像。",
        "options": [
            {
                "text": "饮用泉水 (回复 10 生命值)",
                "action": "drink_fountain"
            },
            {
                "text": "投入金币 (消耗 10 金币，获得一张随机蓝色卡牌)",
                "action": "coin_fountain"
            },
            {
                "text": "仔细观察泉底 (进入下一阶段)",
                "action": "observe_fountain"
            },
            {
                "text": "悄悄离开 (什么都不发生)",
                "action": "leave_event"
            }
        ]
    },
    "fountain_observe": {
        "description": "你凑近水面，透过蓝光发现池底有一具古代法师的骸骨，骸骨的脖子上挂着一根闪闪发光的【奥术项链】(遗物)。但骸骨周围隐约有符文法阵在闪烁，似乎有防盗陷阱。",
        "options": [
            {
                "text": "冒险捞取项链 (50%获得奥术符文，50%触发陷阱失去3生命值并获得1张晕眩)",
                "action": "take_necklace"
            },
            {
                "text": "尊重死者，静静离开 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "knight": {
        "description": "一位受伤的奥术骑士靠在树旁，他的盔甲已经破损，正虚弱地向你求助。",
        "options": [
            {
                "text": "施以援手 (消耗 1张 绷带包扎，获得 随从卡: 盾卫)",
                "action": "help_knight"
            },
            {
                "text": "趁火打劫 (获得 25 金币)",
                "action": "rob_knight"
            },
            {
                "text": "询问他的来历 (进入下一阶段)",
                "action": "ask_knight"
            },
            {
                "text": "置之不理 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "knight_story": {
        "description": "骑士虚弱地告诉你，他在此处讨伐潜伏在附近洞穴里的魔仆，但不慎踩入陷阱身负重伤。他遗失了他的佩剑。他承诺若你能帮他找回长剑，他将作为你的追随者并为你效力。",
        "options": [
            {
                "text": "帮他去洞穴取回长剑 (前往洞穴战斗)",
                "action": "cave_quest"
            },
            {
                "text": "表示无能为力并离开 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "knight_cave": {
        "description": "你走入黑暗的洞穴。突然，一只狂暴的魔仆从阴影中扑了过来！你必须击败它以获取佩剑。",
        "options": [
            {
                "text": "进入战斗 (与魔仆决一死战)",
                "action": "cave_fight"
            }
        ]
    },
    "altar": {
        "description": "前方是一处古老的法师祭坛，祭坛上的水晶依然散发着狂暴的奥术波动。",
        "options": [
            {
                "text": "汲取奥术 (获得一张能力卡: 奥术充能)",
                "action": "absorb_altar"
            },
            {
                "text": "摧毁水晶 (获得 20 金币，但失去 4 点生命值)",
                "action": "break_altar"
            },
            {
                "text": "在祭坛前冥想 (进入下一阶段)",
                "action": "meditate_altar"
            },
            {
                "text": "绕道而行 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "altar_portal": {
        "description": "你在祭坛前坐下，静静感受虚空中的奥术脉动。随着你的冥想，祭坛中央狂暴的水晶产生了共鸣，一道幽蓝色的奥术虚空之门在你面前缓缓开启，里面隐隐传来宝物的波动，但也十分不稳定。",
        "options": [
            {
                "text": "跨入传送门 (50%进入奇妙商店且购买半价，50%遭遇精英战)",
                "action": "enter_portal"
            },
            {
                "text": "摧毁传送门 (引起爆炸，获得 40 金币，失去 3 生命值并获得1张苦恼)",
                "action": "shatter_portal"
            }
        ]
    },
    "lost_maze": {
        "description": "你步入了一座由古老符文石墙构成的巨大迷宫。石墙上爬满了发光的青苔，通道向各个方向延伸。你只能选择一条路前行。",
        "options": [
            {
                "text": "循着远处的微弱火光走 (进入火光分支)",
                "action": "maze_fire"
            },
            {
                "text": "沿着潺潺的水流声走 (进入水流分支)",
                "action": "maze_water"
            },
            {
                "text": "在墙壁做标记，小心翼翼前行 (获得 10 金币并离开)",
                "action": "maze_mark"
            }
        ]
    },
    "maze_guard": {
        "description": "你沿着温暖的火光走去，突然石门落下，一个燃烧着的【火元素守卫】挡住了去路。它发出隆隆的声响，似乎不允许你通过，除非你向它进献财物。",
        "options": [
            {
                "text": "贿赂守卫 (消耗 20 金币，获得随机普通/稀有遗物并离开)",
                "action": "bribe_guard"
            },
            {
                "text": "与守卫战斗 (进入精英战，胜利获得稀有遗物)",
                "action": "fight_guard"
            },
            {
                "text": "趁它不注意逃跑 (无事发生并离开)",
                "action": "leave_event"
            }
        ]
    },
    "maze_pool": {
        "description": "你沿着水流，来到了一处流淌着生命能量的纯澈池塘。池底散落着一些冒险者的遗物，但池水散发着古老而圣洁的压迫感。",
        "options": [
            {
                "text": "在泉水中沐浴 (生命上限+3并回复 15 点生命值)",
                "action": "bathe_pool"
            },
            {
                "text": "捞取水底的遗物 (50%获得随机遗物，50%被池中水怪袭击失去 5 生命上限)",
                "action": "fish_pool"
            }
        ]
    },
    "abandoned_mine": {
        "description": "前方是一处荒废的地下矿区，巨大的矿坑深不见底。锈迹斑斑的矿车轨道一路延伸下去，一旁还有半坍塌的木质旋转扶梯。",
        "options": [
            {
                "text": "坐上生锈矿车滑入矿坑 (进入矿车分支)",
                "action": "ride_cart"
            },
            {
                "text": "沿着破旧梯子慢慢爬下去 (进入梯子分支)",
                "action": "climb_ladder"
            }
        ]
    },
    "mine_cart_crash": {
        "description": "矿车呼啸着向深处疾驰，速度越来越快！突然，前方的轨道断裂，矿车即将坠入黑暗深渊！",
        "options": [
            {
                "text": "果断跳车 (摔伤失去 3 生命值并获得1张晕眩，但在碎石堆中获得 40 金币)",
                "action": "jump_cart"
            },
            {
                "text": "使用法术或盾牌强行刹车 (要求卡组有火球术/雷鸣波/盾卫之一，无伤着陆并获得遗物；否则坠车失去10生命获得10金币)",
                "action": "stop_cart_spell"
            }
        ]
    },
    "mine_ladder_body": {
        "description": "你小心地沿着木梯向下爬。在半路上的一处木质平台上，你发现了一具古代矿工的干尸，他的怀里死死抱着一个发光的密封铁盒。",
        "options": [
            {
                "text": "搜刮干尸 (获得 25 金币，但遭遇诅咒获得1张苦恼)",
                "action": "loot_body"
            },
            {
                "text": "用重火力法术轰开矿坑底部的矿墙 (有火球术/雷鸣波获得50金币，否则徒手挖矿获得15金币)",
                "action": "dig_ore"
            }
        ]
    },
    "phantom_mage": {
        "description": "你在荒野道路中央遇到了一位若隐若现的幻影法师。他手中正握着一卷闪烁着奥术幽光的残卷，用空洞的眼神注视着你。",
        "options": [
            {
                "text": "解读残卷 (50%获得奥术涌动，50%被狂暴奥术反噬获得1张晕眩)",
                "action": "read_scroll"
            },
            {
                "text": "用魔网产生共鸣 (消耗 15 金币，获得一张随机法术牌)",
                "action": "resonate_scroll"
            },
            {
                "text": "驱散残影 (获得 15 生命值回复)",
                "action": "dispel_phantom"
            },
            {
                "text": "悄悄离开 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "goblin_gamble": {
        "description": "一个贼眉鼠眼的哥布林商人坐在路边，抛玩着几枚金币。看到你走来，他露出了贪婪的笑容：“嘿，冒险者，来玩一把刺激的猜硬币游戏吗？赢了双倍，输了可就什么都没了！”",
        "options": [
            {
                "text": "小赌一把 (消耗 15 金币，50%获得 30 金币，50%失去投入)",
                "action": "gamble_small"
            },
            {
                "text": "豪赌一把 (消耗 30 金币，40%获得 60 金币，60%失去投入)",
                "action": "gamble_large"
            },
            {
                "text": "强行抢劫 (70%抢得 40 金币，30%被其陷阱炸伤失去 8 生命值)",
                "action": "rob_goblin"
            },
            {
                "text": "拒绝并离开 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "fairy_tea": {
        "description": "在静谧的林间空地上，几只花妖精正在举办茶会。她们看到你，热情地邀请你加入，并呈上了五彩缤纷的茶点。",
        "options": [
            {
                "text": "饮用红色花蜜茶 (回复 12 生命值)",
                "action": "drink_nectar"
            },
            {
                "text": "享用绿色坚果饼 (最大生命值上限+4)",
                "action": "eat_cookie"
            },
            {
                "text": "倾听妖精的八音盒 (获得一张随机的灵巧卡牌)",
                "action": "listen_music"
            },
            {
                "text": "婉言谢绝并离开 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "void_contract": {
        "description": "空气突然变得冰冷，一个由紫黑色虚空能量凝聚而成的无面商人从阴影中浮现。他张开双臂，向你展示着闪烁着暗影波动的强大力量，但他的契约总是伴随着沉痛的代价。",
        "options": [
            {
                "text": "献祭生命换取遗物 (失去 10 生命值，获得随机遗物)",
                "action": "contract_relic"
            },
            {
                "text": "以血肉之躯汲取奥法 (失去 6 最大生命值，获得一张随机传奇卡牌)",
                "action": "contract_legend"
            },
            {
                "text": "将虚空吞噬 (失去 3 生命值，获得 35 金币并获得1张苦恼)",
                "action": "absorb_void"
            },
            {
                "text": "拒绝契约并离开 (离开事件)",
                "action": "leave_event"
            }
        ]
    },
    "leave_default": {
        "text": "离开事件",
        "action": "leave_event"
    }
}
