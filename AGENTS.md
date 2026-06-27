# 魔法肉鸽卡牌游戏插件开发规范指引 (AGENTS.md)

> [!IMPORTANT]
> ## AI 助手强制阅读指令 (MANDATORY PRE-FLIGHT READ INSTRUCTION)
>
> **在开始开发、修改或测试本项目代码之前，你必须根据待修改的文件路径，优先调用 view_file 完整阅读对应的子模式规范文档！** 未经阅读直接修改代码属于违规行为。
>
> ### 1. 肉鸽模式 / 主城模式 / 咖啡馆模式 (Rogue, Town & Cafe)
> - **适用文件路径**：
>   - game/core/battle_engine.py
>   - game/core/explore_engine.py
>   - game/core/map_engine.py
>   - game/core/cafe_engine.py
>   - game/core/town_engine.py
>   - game/core/battle/ 目录
>   - game/core/town/ 目录
>   - game/entities/ 目录（除对决卡牌 cards/duel.py 外）
>   - game/data/ 目录中除对决外的静态配置文件
>   - scratch/rogue_tests/ 目录
> - **必须优先读取的子规范**：[game/core/battle/AGENTS.md](file:///c:/Users/pppop/Desktop/azuki/astrbot_plugin_text_roguelike/game/core/battle/AGENTS.md)
>
> ### 2. 对决模式 (Duel Mode / TCG)
> - **适用文件路径**：
>   - game/core/duel_engine.py
>   - game/core/duel_router.py
>   - game/core/duel/ 目录
>   - game/entities/cards/duel.py
>   - game/data/duel_card_data.py
>   - game/data/duel_template_data.py
>   - scratch/duel_tests/ 目录
> - **必须优先读取的子规范**：[game/core/duel/AGENTS.md](file:///c:/Users/pppop/Desktop/azuki/astrbot_plugin_text_roguelike/game/core/duel/AGENTS.md)

---

## 1. 项目目录结构

整个插件的目录结构设计如下：

- `main.py`: 插件主要入口，用于注册 /rogue 命令，进行多级子指令分发并截获未处理异常（已兼容无 AstrBot 纯 Python 环境下直接导入）。
- `play_rogue.py`: 项目根目录下的控制台游戏入口，提供免前缀快捷命令行交互游玩。
- `metadata.yaml`: 插件元数据配置文件，声明插件版本、唯一标识等。
- `AGENTS.md`: 本项目规范指引文档（本文档）。
- `game/`: 游戏核心逻辑包。
  - `__init__.py`: 包初始化空文件。
  - `cards.py`: 静态卡牌配置桥接与数据导出。
  - `engine.py`: 顶层游戏引擎接口。
  - `core/`: 核心引擎包。
    - `battle_engine.py`: 战斗引擎 Facade 门面接口，委派执行实际战斗动作。
    - `cafe_engine.py`: 咖啡馆模式核心逻辑引擎。
    - `town_engine.py`: 主城模式核心逻辑引擎。
    - `cli_router.py`: 用户命令行分发路由，委派具体的处理器完成命令与动作。
    - `duel_engine.py`: 对决模式核心 TCG 逻辑引擎，独立处理双人对局状态。
    - `duel_router.py`: 对决模式指令与动作分发路由器，在重构后仅作为门面 Facade，委派牌组和查询功能。
    - `cli/`: 命令行指令逻辑子包。
      - `base.py`: 指令与动作处理器基类，提供 `__init_subclass__` 自动注册机制。
      - `actions.py`: 具体动作处理器实现。
      - `commands.py`: 具体命令处理器实现。
    - `battle/`: 战斗引擎解耦子包。
      - `base.py`: 战斗引擎基类和事件总线创建。
      - `combat_resolver.py`: 负责伤害结算、生命治疗、护盾及随从召唤。
      - `card_player.py`: 负责出牌、抽牌、弃牌及回合更替。
      - `enemy_controller.py`: 负责敌人意图判定与回合状态处理。
      - `observers.py`: 被动的遗物、Buff、护符触发观察者类定义。
      - `AGENTS.md`: 肉鸽模式开发规范文档。
    - `duel/`: 对决模式专属规范及逻辑子包。
      - `deck_manager.py`: 对决模式牌组管理器，独立负责牌组创建、校验、导入导出与分享码处理。
      - `query_manager.py`: 对决模式查询管理器，负责对决状态查询、抽牌堆、弃牌堆、随从墓地等信息查询。
      - `AGENTS.md`: 对决模式开发规范文档。
    - `town/`: 主城模式子逻辑包.
      - `dialog_handler.py`: NPC 对话交互逻辑处理器。
      - `quest_manager.py`: 任务承接、进度追踪与奖励发放管理器.
    - `event_bus.py`: 事件总线订阅与广播机制。
    - `explore_engine.py`: 荒野探索、宝箱房、奇妙商店、篝火等节点逻辑。
    - `map_engine.py`: 关卡地图网络拓扑结构生成、节点移动和路由控制。
  - `data/`: 静态配置与文本模板数据字典。
    - `card_data.py`: 全体卡牌的基础映射字典与卡牌桥接属性配置。
    - `duel_card_data.py`: 全体对决卡牌静态映射属性、Quest与奖励卡配置。
    - `duel_template_data.py`: 全体对决系统广播、提示和错误反馈的静态文本模板配置文件.
    - `neutral_card_data.py`: 中立卡牌基础字典。
    - `neutral_card_data_spell.py`: 中立卡牌法术效果配置。
    - `neutral_card_data_minion.py`: 中立卡牌随从效果配置.
    - `neutral_card_data_amulet.py`: 中立卡牌护符效果配置.
    - `wizard_card_data.py`: 法师职业卡牌的属性、伤害/护盾/治疗参数与反馈模板数据。
    - `warrior_card_data.py`: 战士职业卡牌的属性、伤害/护盾/治疗参数与反馈模板数据.
    - `card_upgrade_data.py`: 全体卡牌升级后的属性与效果模板数据。
    - `minion_data.py`: 随从基础字典。
    - `minion_data_basic.py`: 基础随从属性与技能效果模板配置。
    - `minion_data_officer.py`: 高阶将领随从属性与技能效果模板配置.
    - `enemy_data.py`: 敌方全体角色基础意图字典。
    - `enemy_data_normal.py`: 普通敌人行动意图与行动数据配置。
    - `enemy_data_boss.py`: 领主 BOSS 行动意图与行动数据配置。
    - `gem_data.py`: 宝石合成及强化属性配置。
    - `keyword_data.py`: 卡牌词条解释说明配置。
    - `amulet_data.py`: 全体护符的默认吟唱时间与结算效果参数。
    - `buff_data.py`: 全体战斗 Buff 的展示名称与效果描述配置。
    - `trash_talk_data.py`: 会说话的智力怪物及切磋对手在各语境下的垃圾话文本数据配置。
    - `event_data.py`: 荒野事件的场景叙述、选项参数及选项触发反馈模板。
    - `relic_data.py`: 全体遗物的属性、稀有度、售价与效果描述配置.
    - `town/`: 主城静态配置文件目录，包含 zh_cn_global.json、zh_cn_npcs.json 及各房间独立 json 配置文件。
  - `models/`: 数据模型及底层管理。
    - `state.py`: 玩家、敌人、随从、卡牌、护符等实体状态的 Dataclass 模型。
    - `events.py`: 包含 BattleStartEvent 等原子事件的定义。
    - `manager.py`: 本地存档序列化、载入及销毁管理。
  - `entities/`: 实体行为与逻辑多态实现。
    - `effects.py`: 原子游戏效果定义。
    - `cards/`: 卡牌逻辑包，包含 registry.py，base.py，neutral.py，wizard.py，warrior.py，legendary.py，curse.py 以及 duel.py 等对决卡牌具体打出效果类实现。
    - `buffs/`: 战斗 Buff 逻辑包，包含 registry.py 提供装饰器注册机制，以及 buffs.py 继承自 BuffImpl 的各种 Buff 响应逻辑。
    - `relics/`: 遗物逻辑包，包含 registry.py 提供装饰器注册机制，以及 relics.py 包含各种遗物的被动监听逻辑实现。
    - `minions/`: 随从技能子类多态逻辑。
    - `amulets/`: 护符特有钩子回调实现。
    - `enemies/`: 各种怪物与 Boss 意图的具体执行逻辑。
      - `__init__.py`: 通过 pkgutil 动态遍历并加载子包及模块，自动装载实体模板类。
      - `base.py`: 敌人模板基类及注册器 @register_enemy 声明.
      - `boss.py`: 游戏各阶段 Boss 怪物逻辑实现.
      - `town_enemies.py`: 主城敌人逻辑实现.
      - `trash_talk_actions.py`: 智力怪物与切磋对手战斗中垃圾话台词核心及动态生成逻辑。
      - `normal/`: 普通怪物行为包，包含各阶段普通怪物的独立行为模块。
      - `elite/`: 精英怪物行为包，包含各阶段精英怪物的独立行为模块。
      - `summon/`: 召唤物行为包，包含各类召唤物的独立行为模块。
    - `events/`: 随机事件选项逻辑子包.
      - `base.py`: 事件选项及模板基类定义。
      - `registry.py`: 事件选项注册器桥接。
      - `fountain.py`, `knight.py` 等具体事件选项的多态模块实现。
  - `renderer/`: 游戏状态文本渲染层。
    - `__init__.py`: 代理至各渲染子模块的 GameRenderer.
    - `menu.py`: 菜单、卡牌库及玩家牌组渲染。
    - `battle.py`: 战斗界面及简要战斗状态渲染.
    - `duel_renderer.py`: 对决模式公开战局脱敏与各自私密详情渲染。
    - `map.py`: 地图路线预览及可达节点渲染。
    - `explore.py`: 荒野事件、奇妙商店、古老宝箱、战利品等界面渲染.
    - `query.py`: 随从、遗物、Buff及卡牌模糊匹配查询效果渲染。
- `scratch/`: 本地临时测试与仿真目录。
  - `test_flow.py`: 自动化测试入口（肉鸽模式），采用自动扫描机制，加载运行 rogue_tests/ 下的所有测试用例。
  - `test_duel.py`: 自动化测试入口（对决模式），采用自动扫描机制，加载运行 duel_tests/ 下的所有测试用例。
  - `test_game.py`: 包含交互式与自动随机仿真的控制台测试程序。
  - `test_astrbot_load.py`: 用于在宿主机验证 Docker 容器内插件加载与依赖导入状况。
  - `run_tests_docker.bat`: 依次在容器中运行上述核心测试文件。
  - `rogue_tests/`: 肉鸽模式拆分后的高内聚单元与集成测试包。
    - `base.py`: 基础 Dummy 测试桩与环境配置。
    - `test_rogue_basic.py`: 基础游戏流程、选择主/子职业、中英文指令别名等基础用例。
    - `test_rogue_card_mech1.py`: 护盾与保留、回响形态及死亡律动交互、钢铁意志卡牌升级与护盾治疗叠加等机制测试。
    - `test_rogue_card_mech2.py`: 0 费消耗牌、多重重放、Arcane Torrent 伤害判定与法术黑名单限制、冲击波与回响形态交互等机制测试.
    - `test_rogue_minions.py`: 随从受击、攻击机制、佣兵在队伍中的索引重组等随从用例。
    - `test_rogue_enemy_stage.py`: 伤害结算及真实伤害判定、怪物行动与晕眩、状态压缩和关卡胜利结算等敌人与关卡用例。
    - `test_rogue_explore.py`: 荒野事件选项（如老兵房、古泉等）、遗物与护符结算、篝火 forge 卡牌强化与跳过等非战斗探索用例。
    - `test_rogue_system.py`: 局外持久化存档与恢复、牌组完备性、以及不同子命令间执行状态的强隔离用例。
    - `test_rogue_town.py`: 主城任务承接、商店购买、切磋交互流程测试用例.
    - `test_rogue_cafe.py`: 咖啡馆日常经营、菜单升级、顾客接待逻辑测试用例.
    - `test_rogue_chaos_update.py`: 复杂混乱战局下的机制联动与状态更新测试用例。
  - `duel_tests/`: 对决模式拆分后的高内聚单元与集成测试包。
    - `base.py`: 对决模式基础 Dummy 测试桩与环境配置。
    - `test_duel_basic.py`: 局外牌组创建校验（25-50张、同名卡上限4张）、卡组导出导入分享码、对决菜单等用例.
    - `test_duel_flow.py`: 对局开始、使用卡牌能量扣除、指令队列执行、双人多轮交替回合流转的完整生命周期用例.
    - `test_duel_advanced.py`: 力量 Buff 数值伤害缩放、双击及回响多重打出检测、随从召唤与技能效果触发用例。
    - `test_duel_minions_spells.py`: 随从死亡、AOE 伤害对空方格过滤、生命上限与护盾变动、对决模式查询与隔离用例。

---

## 2. 全局通用开发规范

为确保多端运行顺畅与规范统一，在编写代码时必须严格遵守以下规范：

### 2.1 注释约束
- 绝对不要在 Python 源代码（包括 main.py, game/*.py, scratch/*.py）及 JSON 配置文件中编写任何注释。

### 2.2 视觉与渲染规范
- 游戏中的渲染逻辑全部集中于 game/renderer/ 模块包中。
- 游戏渲染给机器人的交互文本输出中，禁止使用任何 Markdown 标记（例如加粗 **, 斜体 *, 表格符 |, 代码块包围 ```）及 LaTeX 公式，防止在 QQ OneBot 平台无法正常显示。
- 游玩过程中可以使用 Emoji 和 Unicode 符号进行界面美化与排版对齐。
- **全面本地化防裸露原则**：除了查询 (query) 模式允许在括号中附带展示英文注册名 (ID) 之外，所有玩家可交互的游戏逻辑（如商店购买、事件描述、对话选项、菜单界面、探索状态等）绝对禁止在输出文本中裸露任何实体（卡牌、随从、遗物、Buff 等）的英文 ID 或未翻译注册名。必须确保在向用户展示的每一处都进行正确的本地化解析，若出现未翻译裸露，即视为严重 Bug。
- **本地化文本括号限制规范**：所有本地化文本（如NPC名字、卡牌/随从/遗物名称及各类系统播报文本等）在非必要情况下，绝对禁止添加任何解释性的括号后缀（例如，禁止在咖啡馆客串角色名字后方拼接“（主城客串）”等解释性括号），保持文案的纯净与沉浸感。

### 2.3 核心数据与状态规范
- 数据结构须继承 models/state.py 中的 Dataclass，状态更新均须通过 models/manager.py 中的 SaveManager 完成序列化存盘。
- **卡牌ID及修饰彻底解耦规范**：卡牌大循环堆（deck, hand, draw_pile, discard_pile, exhaust_pile, graveyard）中的卡牌彻底解耦为非 `str` 继承的 `@dataclass CardState`。所有卡牌状态变更（如升级、镶嵌宝石、重放、易碎等）只修改 `CardState` 对象的属性。
- **from_cid 弃用及卡牌 ID 禁改规范**：新写的代码中**绝对禁止使用 `from_cid`**（已标记为弃用方法，仅在加载旧存档或测试用例兼容时由底层库静默使用），且**绝对禁止更改卡牌 id 或为卡牌 id 拼接任何后缀**（如升级不能修改 ID，不能为卡牌 ID 追加 `+` 或 `:gems` 等后缀，ID 必须保持其原始注册名不变，通过 `upgraded` 布尔值等属性标识状态）。
- 引入 0 动作消耗牌机制，当卡牌的 cost_a 与 cost_ba 为 0 时打出不扣除动作资源.
- 改变卡牌效果与状态的机制不应更改卡牌名称：诸如重放（replay）、易碎（fragile）等修饰卡牌效果或状态的机制，不能在卡牌 the name 属性中拼接带有修饰状态（例如 (重放 X) 等）的后缀，卡牌的原有名称在发生此类修饰时必须保持不变，修饰状态仅以词条形式追加或修改在卡牌描述（desc）的末尾。
- 卡牌与护符描述称呼规范：静态数据中定义的卡牌与护符描述文本（desc / amulet_desc）中，禁止使用“玩家”来指代主角，必须统一称呼为“你”（例如：“你获得 3 点护盾”而不是“玩家获得 3 点护盾”）。
- 禁止大规模后处理“玩家”替换：严禁在后处理中采用任何形式的程序大规模匹配“玩家”并暴力替换为玩家名字的逻辑，以防导致遗物描述、Buff说明、怪物意图等被误替换。必须且仅在真正需要显示玩家昵称的界面（如战斗状态条、探索状态条等）中，显式通过 player_name / run.player.name 等变量或占位符进行精确格式化渲染。
- **伤害结算与类型规范**：游戏中包含 14 种具体的伤害类型（挥砍 slashing、穿刺 piercing、钝击 bludgeoning、火焰 fire、寒冷 cold、闪电 lightning、雷鸣 thunder、强酸 acid、毒素 poison、黯蚀 necrotic、光耀 radiant、心灵 psychic、力场 force、真实 true）。允许在宏观描述（如卡牌描述、遗物机制、Buff 状态说明、任务目标）中继续使用“物理伤害”（作为挥砍、穿刺、钝击的合称）和“魔法伤害”作为宏观代指；但在具体的伤害计算、伤害播报、战斗日志和结算文字中，严禁出现诸如“造成了 X 点物理伤害”或“造成了 X 点魔法伤害”的描述，实际造成的每一笔伤害必须精细到上述 14 种具体伤害类型之一（例如，随从和怪物普通物理攻击必须直接调用并显示为“钝击伤害”，狂暴撕咬等动作归为“穿刺伤害”）。


### 2.4 指令调度与全局命令规范
- 指令分支由 main.py 的统一分发器 _execute_sub_action 路由。所有指令以元组 (res_text, should_terminate) 形式返回。
- 指令前缀配置项 shortcut_prefix 类型变更为 list 以支持多个前缀别名。匹配时对所有前缀按长度由长至短倒序排列，规避较短的前缀提前截断损坏指令单词。
- 提供“帮助”及“help”专用子命令，调用 GameRenderer.render_help() 列出全量指令的使用教程 and 中英文别名（包含免前缀模式提示），当输入未知指令时系统应当引导用户使用帮助指令。
- 新增命令设计规范：系统在添加任何新指令时，必须同步添加对应的纯英文命令变体，并且必须支持至少一个快捷命令（如英文缩写、别名或单字快捷指令）。同时，必须在 main.py 的免前缀拦截白名单（如 valid_cmds 或 town_cmds）中同步补全注册这些新增命令及其英文别名，强制确保新命令的免前缀快捷支持。
- **始终豁免指令规范**：确立“队列”（queue/q）、“查询”（query/info/i）、“任务”（quest/quests）和“背包”（bag/inventory/inv）为系统级的始终豁免指令。这些指令在包含当前及未来可能引入的所有游戏状态中（如战斗、探索、主城、对话、主菜单等）均被允许执行；并且在对话等特殊输入拦截状态中，必须作为系统指令优先处理，绝对禁止作为非指令文本或对话选项被消费。

### 2.5 数据驱动与配置分离规范
- 静态配置数据化：所有卡牌、随随、怪物、护符、遗物、Buff、事件一律禁止硬编码，必须存放在 game/data/ 的独立数据字典中。
- 反馈模板化：各实现类利用 .format() 动态渲染 feedback 模板并进行回填。

### 2.6 开闭原则 (OCP) 与事件驱动扩展规范
- 严格遵循开闭原则：对扩展开放，对修改封闭。
- 当引入新的遗物、Buff 或卡牌特性时，绝对禁止直接修改核心战斗引擎 (battle_engine.py) 或其它基础状态逻辑。
- 新增逻辑必须通过实现独立的监听器，并在加载时将其绑定 to event_bus.py 定义 of 原子事件（如 BattleStartEvent、CardPlayedEvent、DamageCalculateEvent）上来完成交互。确保任何特异性的判断和数值加成都内聚在具体实体类的回调中，不污染基础流转逻辑。

### 2.7 卡牌、遗物、Buff与指令注册规范
- 卡牌注册使用装饰器模式自动完成注册。全局统一在 game/entities/cards/registry.py 中导出 @register_card(cid, **kwargs)，在具体卡牌类声明处使用，并在 base.py 中自动装配实例化，禁止任何硬编码的卡牌注册分支。
- 遗物与 Buff 注册使用声明式装饰器注册与动态扫描反射机制实现。全局通过 game/entities/relics/registry.py 的 @register_relic 与 game/entities/buffs/registry.py 的 @register_buff 将具体类发布到全局注册表 RELIC_CLASS_REGISTRY 与 BUFF_CLASS_REGISTRY 中。特例（如 GenericMinorVulnerableBuff 等）在声明时使用 @register_buff 手动标注，其余普通实体在文件加载完毕后通过全局 globals() 按照类名驼峰自动转蛇形规则由系统自适应装载，彻底消灭 RELIC_IMPLS 与 BUFF_MAP 静态硬编码字典。
- 命令行路由使用命令模式（Command Pattern）。全局将具体子动作和指令分别拆分为继承自 ActionHandler 和 CommandHandler 的命令类，在 CLIRouter 内部由映射字典分发，解耦并消除庞大的 if-else 结构，完全符合开闭原则。

### 2.8 上帝类拆分与现代化 OOP 规范
- **包与文件细粒度拆分原则（禁止堆叠逻辑）**：绝对禁止在单个 Python 源代码文件内混合堆叠两个或以上不同职责/业务维度的逻辑。在设计与开发时优先遵循“能分就分，能拆就拆”的去上帝类化思想，且单个非二进制文件总行数超过 1000 行时必须强制物理拆分与重构。
- **禁止无限将逻辑堆叠进单个类**：核心引擎类（如 BattleEngine、CLIRouter、ExploreEngine）禁止无限膨胀。如果某个类的代码行数或职责过多，必须根据单一职责原则（SRP）进行重构，将相关业务逻辑组合委派给专门的子战略类（如 CombatResolver、CardPlayer、EnemyTurnController），由原上帝类作为 Facade 门面对外提供一致 of API 兼容。
- **被管监听与被动反应机制解耦**：遗物（Relic）、战斗 Buff、护符（Amulet）等具有监听游戏动作（如战斗开始、摸牌、受到伤害等）并产生被动副作用特性的系统，绝对禁止在战斗主循环中硬编码查询。必须将这些被动逻辑解耦为独立的事件观察者（Observer，如 RelicTriggerHandler），通过订阅 event_bus 实施原子交互.
- **避免编写大量重复逻辑**：严禁采用复制粘贴形式编写相似的游戏控制或效果逻辑。通用的判断、数值伤害缩放、文字排版等基础规则，必须抽象封装为基类核心流程（Template Method）或共享工具函数（Utility Functions）。
- **声明式自动注册**：对于新增加的事件分支、指令动作或卡牌种类，禁止手动硬编码关联的 if-else 或全局字典映射。统一使用 Python 的 __init_subclass__ 或装饰器机制，在子类文件被加载时自动将类实例或类对象发布到全局注册表，确保完全的开闭原则（OCP）支持。

### 2.9 新机制与新事件开发规范
- **禁止在执行类中硬编码数值和文案**：
  - 新增随机事件的所有场景描述、选项文本、反馈文案，必须定义在 game/data/event_data.py 中，禁止在执行类（EventOption 子类）中硬编码文字串或奖励数值参数.
  - 新机制（如怪兽动作、新随从或护符状态）的所有文本与参数也必须统一放于 game/data/ 目录的对应独立文件中，由运行时动态反射加载，实现数据与机制代码的彻底分离。
- **高复用性的通用生命周期接口**：
  - 新增事件的所有回调选项均应继承自 EventOption 并利用基类提供的模板方法执行。
  - 涉及通用且常见的业务逻辑（例如：展示三选一卡牌且支持跳过、移除牌组卡牌、给予/扣除金币或生命值上限变动），禁止在具体事件选项类中以复制粘贴等形式编写实现，必须直接调用核心引擎中已公开并测试的复用接口（如 ExploreEngine 的奖励生成接口、CombatResolver 的状态属性增减接口）。
- **可扩展的新机制设计**：
  - 添加新战斗或底层机制时，必须定义新的原子事件（继承自 GameEvent 并由 event_bus 调度），并对外提供可由 Relic 或 Buff 修改机制参数的标准化字段。
  - 核心处理引擎在进行机制计算时，应只依赖该事件的最终结算数据，以便后续的新卡牌、新被动能够通过订阅该事件完成逻辑扩展，禁止在核心流程中加入特定卡牌或状态的 if 逻辑。
  - 任何怪物或 Boss 特异性的生存被动、死亡拦截或形态觉醒逻辑（如“尤格-索托斯”濒死时进入觉醒形态），绝对禁止在核心结算机制 CombatResolver 中硬编码。必须完全通过在具体 EnemyTemplate 模板中订阅 EnemyBeforeDeathEvent 并执行 event.cancel() 拦截，进而自适应重组其属性状态，保证核心引擎纯净、高复用。

### 2.10 版本控制与命令规范
- 除非明确提及，否则绝对不能使用任何 git 相关命令。

### 2.11 中文编码与多端兼容规范
- 字符串与文件编码：项目中所有 Python 源代码文件、测试文件以及静态配置文件的读写操作，必须显式指定字符编码为 utf-8（例如使用 open() 时添加 encoding='utf-8' 参数）。
- 环境变量配置：在 Windows 本地运行测试脚本或插件交互验证时，需在终端显式指定 PYTHONPATH="." 以及 PYTHONIOENCODING="utf-8" 环境变量，确保中文字符集正常输出而不发生 UnicodeEncodeError 崩溃。
- 中文文案与语法纯正性：在编写或生成中文本地化文本（如卡牌/护符描述、系统播报、NPC对话和随机事件文案等）时，必须确保中文语法的纯正性，严禁出现非预期的中英混杂介词（如将中文助词“的”误写为英文介词“of”）。

### 2.12 文档与规范同步更新规范
- **强制双向同步规则**：AI 助手在开发、重构或修改代码后，必须主动评估是否影响了主规范或各子规范的描述。
- **主规范同步**：如果开发中更改了全局结构、目录布局、通用设计原则或全局架构，必须同步更新根目录 AGENTS.md（即本文档）。
- **子规范同步**：如果修改了肉鸽模式（Rogue Mode）、主城/咖啡馆模式、或者对决模式（Duel Mode）的具体业务逻辑、机制、卡牌、指令或测试场景，**必须无条件一并更新对应的子规范文档（game/core/battle/AGENTS.md 或 game/core/duel/AGENTS.md）**。绝对禁止规范内容落后于代码行为。

### 2.13 调试与辅助分析脚本规范
- **禁止在项目工作区残留非测试性辅助脚本**：项目根目录及其子目录（包括项目根目录下的 scratch/ 目录）只允许存放核心开发源码、正式的集成/系统测试及单元测试用例。绝对禁止把任何临时性的辅助数据分析、词条提取、语法检查等开发阶段临时脚本留在项目工作区中。
- **强制使用会话脑区进行调试存储**：任何开发或调试过程中所编写的非正式测试用途辅助脚本，必须且仅能存储在会话脑区 (Brain) 的 scratch 目录（即 <appDataDir>\brain\<conversation-id>/scratch/）中，确保项目工作区的绝对整洁，规避造成不必要的脚本堆叠。

---

## 3. 代码编辑与扩展指引

### 3.1 文字冒险（主城）模式本地化修改指引
- 主城所有系统提示、菜单交互、物品及房间渲染、切磋胜负结算文案等均已实现完全的本地化分离，统一定义在 game/data/town/ 目录下（如 zh_cn_global.json、zh_cn_npcs.json 等）。
- 逻辑代码（包括 town_engine.py 等）严禁硬编码任何中文字符串。所有交互文本和渲染提示必须通过加载相应的 JSON 本地化配置文件，并以获取键值的方式进行动态回填或格式化渲染。

---

## 4. 测试与运行异常规范

### 4.1 Windows 本地命令行测试运行异常提示
- 在 Windows 环境下使用 PowerShell 或 CMD 直接运行测试脚本时，可能遇到以下两类环境问题：
  1. 模块导入失败（ModuleNotFoundError）：若遇到无法导入 game 的错误，需在运行前显式指定 PYTHONPATH 环境变量（例如在 PowerShell 中执行：$env:PYTHONPATH="."）。
  2. 控制台字符集编码错误（UnicodeEncodeError）：若在控制台打印带有各类圆形字符等 Unicode 符号时发生编码报错，需在执行前将 Python 的控制台编码指定为 utf-8（例如在 PowerShell 中执行：$env:PYTHONIOENCODING="utf-8"）。
  3. 别名挂起与高 CPU 占用问题：在 Windows 环境下，严禁使用 python 命令运行脚本，必须统一使用 py 命令行启动器工具（例如 py scratch/test_flow.py），以规避触发 Windows 系统默认的 App Execution Aliases 机制，防止外壳包装进程静默死循环挂起并持续耗费 CPU 资源。

### 4.2 测试豁免规则
- 针对仅涉及纯数值微调或修正的改动（例如修改卡牌的伤害、护盾、治疗数值等静态数据配置，而不涉及控制流、游戏状态逻辑修改或新功能开发），无需运行自动化仿真及流验证测试。

### 4.3 单元测试编写规范
- 源码零注释约束：所有的测试脚本（包括 scratch/test_flow.py 和 scratch/test_duel.py）同样被视为 Python 源码，其中绝对禁止包含任何以井号字符开头的注释和 docstring 文档字符串。
