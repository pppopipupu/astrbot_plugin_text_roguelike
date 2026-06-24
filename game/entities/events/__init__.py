from typing import Optional
from .base import EventOption, EventTemplate
from .registry import EVENT_OPTIONS_REGISTRY
from ...data.event_data import EVENT_CONFIG

from .fountain import *
from .knight import *
from .altar import *
from .lost_maze import *
from .abandoned_mine import *
from .phantom_mage import *
from .goblin_gamble import *
from .fairy_tea import *
from .void_contract import *
from .forge_furnace import *
from .leave import *
from .portal_chamber import *
from .chaos_events import *


ALL_EVENTS = [
    EventTemplate(
        "fountain",
        EVENT_CONFIG["fountain"]["description"],
        [
            DrinkFountainOption("饮用泉水", "drink_fountain"),
            CoinFountainOption("投入金币", "coin_fountain"),
            ObserveFountainOption("仔细观察泉底", "observe_fountain"),
            LeaveEventOption("悄悄离开", "leave_event", "fountain")
        ]
    ),
    EventTemplate(
        "knight",
        EVENT_CONFIG["knight"]["description"],
        [
            HelpKnightOption("施以援手", "help_knight"),
            RobKnightOption("趁火打劫", "rob_knight"),
            AskKnightOption("询问他的来历", "ask_knight"),
            LeaveEventOption("置之不理", "leave_event", "knight")
        ]
    ),
    EventTemplate(
        "altar",
        EVENT_CONFIG["altar"]["description"],
        [
            AbsorbAltarOption("汲取奥术", "absorb_altar"),
            BreakAltarOption("摧毁水晶", "break_altar"),
            MeditateAltarOption("在祭坛前冥想", "meditate_altar"),
            LeaveEventOption("绕道而行", "leave_event", "altar")
        ]
    ),
    EventTemplate(
        "lost_maze",
        EVENT_CONFIG["lost_maze"]["description"],
        [
            MazeFireOption("循着远处的微弱火光走", "maze_fire"),
            MazeWaterOption("沿着潺潺的水流声走", "maze_water"),
            MazeMarkOption("在墙壁做标记，小心翼翼前行", "maze_mark")
        ]
    ),
    EventTemplate(
        "abandoned_mine",
        EVENT_CONFIG["abandoned_mine"]["description"],
        [
            RideCartOption("坐上生锈矿车滑入矿坑", "ride_cart"),
            ClimbLadderOption("沿着破旧梯子慢慢爬下去", "climb_ladder")
        ]
    ),
    EventTemplate(
        "phantom_mage",
        EVENT_CONFIG["phantom_mage"]["description"],
        [
            ReadScrollOption("解读残卷", "read_scroll"),
            ResonateScrollOption("用魔网产生共鸣", "resonate_scroll"),
            DispelPhantomOption("驱散残影", "dispel_phantom"),
            LeaveEventOption("悄悄离开", "leave_event", "phantom_mage")
        ]
    ),
    EventTemplate(
        "goblin_gamble",
        EVENT_CONFIG["goblin_gamble"]["description"],
        [
            GambleSmallOption("小赌一把", "gamble_small"),
            GambleLargeOption("豪赌一把", "gamble_large"),
            RobGoblinOption("强行抢劫", "rob_goblin"),
            LeaveEventOption("拒绝并离开", "leave_event", "goblin_gamble")
        ]
    ),
    EventTemplate(
        "fairy_tea",
        EVENT_CONFIG["fairy_tea"]["description"],
        [
            DrinkNectarOption("饮用红色花蜜茶", "drink_nectar"),
            EatCookieOption("享用绿色坚果饼", "eat_cookie"),
            ListenMusicOption("倾听妖精的八音盒", "listen_music"),
            LeaveEventOption("婉言谢绝并离开", "leave_event", "fairy_tea")
        ],
        min_stage=2,
        max_stage=9
    ),
    EventTemplate(
        "void_contract",
        EVENT_CONFIG["void_contract"]["description"],
        [
            ContractRelicOption("献祭生命换取遗物", "contract_relic"),
            ContractLegendOption("以血肉之躯汲取奥法", "contract_legend"),
            AbsorbVoidOption("将虚空吞噬", "absorb_void"),
            LeaveEventOption("拒绝契约并离开", "leave_event", "void_contract")
        ],
        min_stage=12,
        max_stage=19
    ),
    EventTemplate(
        "forge_furnace",
        EVENT_CONFIG["forge_furnace"]["description"],
        [
            ForgeFireOption("使用常规重铸", "forge_fire"),
            OverloadForgeOption("过载重铸", "overload_forge"),
            ForgeBackfireOption("汲取熔炉余温", "forge_backfire"),
            ShatterForgeOption("强行破坏熔炉", "shatter_forge"),
            LeaveEventOption("安全离开", "leave_event", "forge_furnace")
        ],
        min_stage=2,
        max_stage=19
    ),
    EventTemplate(
        "portal_chamber",
        EVENT_CONFIG["portal_chamber"]["description"],
        [
            ContractPortalOption("献祭最大生命的 10%，获得遗物【门扉碎片】", "contract_portal"),
            ArcanePortalOption("获得卡牌【万能钥匙】，但卡组中会被塞入一张诅咒卡【空间撕裂】", "arcane_portal"),
            LeaveEventOption("悄然离开", "leave_event", "portal_chamber")
        ],
        min_stage=21,
        max_stage=24
    ),
    EventTemplate(
        "void_library",
        EVENT_CONFIG["void_library"]["description"],
        [
            ReadVoidTomeOption("强行阅读虚空秘典", "read_void_tome"),
            BurnVoidBooksOption("点燃禁忌书架", "burn_void_books"),
            SacrificeMindOption("献祭部分心智", "sacrifice_mind")
        ],
        min_stage=6,
        max_stage=12
    ),
    EventTemplate(
        "goblin_blackmarket",
        EVENT_CONFIG["goblin_blackmarket"]["description"],
        [
            BuyBlackmarketRelicOption("强行买下神秘包裹", "buy_blackmarket_relic"),
            RobBlackmarketOption("强行抢劫黑市", "rob_blackmarket"),
            SellFleshOption("出售血肉", "sell_flesh")
        ],
        min_stage=13,
        max_stage=20
    ),
    EventTemplate(
        "time_fountain_trial",
        EVENT_CONFIG["time_fountain_trial"]["description"],
        [
            DrinkTimeSandOption("吞食时间光沙", "drink_time_sand"),
            AccelerateCinderOption("加速自身薪火", "accelerate_cinder"),
            TouchTimeRiftOption("触碰时间裂隙", "touch_time_rift")
        ],
        min_stage=21,
        max_stage=25
    ),
    EventTemplate(
        "astral_caravan_disaster",
        EVENT_CONFIG["astral_caravan_disaster"]["description"],
        [
            LootWreckageOption("强行搜刮飞船残骸", "loot_wreckage"),
            RepairEngineOption("修复动力源并带走", "repair_engine"),
            BraveStormOption("穿越虚空风暴逃跑", "brave_storm")
        ],
        min_stage=27,
        max_stage=30
    ),
    EventTemplate(
        "nameless_tombstone",
        EVENT_CONFIG["nameless_tombstone"]["description"],
        [
            DigGraveOption("掘开墓穴底下的陪葬品", "dig_grave"),
            ReadEpitaphOption("强行解读墓碑碑文", "read_epitaph"),
            CarveOwnNameOption("在碑文刻上自己的名字避邪", "carve_own_name")
        ],
        min_stage=30,
        max_stage=31
    )
]

def get_option_by_action(action: str) -> Optional[EventOption]:
    cls = EVENT_OPTIONS_REGISTRY.get(action)
    if cls:
        return cls()
    return None
