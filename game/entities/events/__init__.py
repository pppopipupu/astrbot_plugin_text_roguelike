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
    )
]

def get_option_by_action(action: str) -> Optional[EventOption]:
    cls = EVENT_OPTIONS_REGISTRY.get(action)
    if cls:
        return cls()
    return None
