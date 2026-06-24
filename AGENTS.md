# 魔法肉鸽卡牌游戏插件开发规范指引 (AGENTS.md)

本文档定义了本项目的目录结构、全局通用开发规范，并指引开发人员及 AI Agent 阅读对应的模式专有规范文档。

本项目的专有开发规范与测试准则已按游戏模式进行拆分，请根据您当前开发或修改的模块，阅读对应的规范文档：

- **肉鸽模式 (Rogue Mode)**：包含战斗引擎、随机事件、探索地图、职业卡牌以及核心测试流等规范。
  - 请阅读：[game/core/battle/AGENTS.md](file:///c:/Users/pppop/Desktop/azuki/astrbot_plugin_text_roguelike/game/core/battle/AGENTS.md)
- **对决模式 (Duel Mode)**：包含双方对局、能量与动作成长、召唤失调、进化机制、局外牌组校验、局外主菜单、指令队列执行以及对局测试等规范。
  - 请阅读：[game/core/duel/AGENTS.md](file:///c:/Users/pppop/Desktop/azuki/astrbot_plugin_text_roguelike/game/core/duel/AGENTS.md)

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
    - `event_bus.py`: 事件总线订阅与广播机制。
    - `explore_engine.py`: 荒野探索、宝箱房、奇妙商店、篝火等节点逻辑。
    - `map_engine.py`: 关卡地图网络拓扑结构生成、节点移动和路由控制。
  - `data/`: 静态配置与文本模板数据字典。
    - `card_data.py`: 全体卡牌的基础映射字典与卡牌桥接属性配置。
    - `duel_card_data.py`: 全体对决卡牌静态映射属性、Quest与奖励卡配置。
    - `duel_template_data.py`: 全体对决系统广播、提示和错误反馈的静态文本模板配置文件。
    - `neutral_card_data.py`: 中立卡牌的属性、伤害/护盾/治疗参数与反馈模板数据。
    - `wizard_card_data.py`: 法师职业卡牌的属性、伤害/护盾/治疗参数与反馈模板数据。
    - `warrior_card_data.py`: 战士职业卡牌的属性、伤害/护盾/治疗参数与反馈模板数据.
    - `card_upgrade_data.py`: 全体卡牌升级后的属性与效果模板数据。
    - `minion_data.py`: 我方全体随从的属性、技能参数与反馈模板。
    - `enemy_data.py`: 敌方全体角色意图、召唤物属性与意图说明数据。
    - `amulet_data.py`: 全体护符的默认吟唱时间与结算效果参数。
    - `buff_data.py`: 全体战斗 Buff 的展示名称与效果描述配置。
    - `event_data.py`: 荒野事件的场景叙述、选项参数及选项触发反馈模板。
    - `relic_data.py`: 全体遗物的属性、稀有度、售价与效果描述配置.
  - `models/`: 数据模型及底层管理。
    - `state.py`: 玩家、敌人、随从、卡牌、护符等实体状态的 Dataclass 模型。
    - `events.py`: 包含 BattleStartEvent 等 14 个原子事件的定义。
    - `manager.py`: 本地存档序列化、载入及销毁管理。
  - `entities/`: 实体行为与逻辑多态实现。
    - `effects.py`: 原子游戏效果 definition。
    - `cards/`: 卡牌逻辑包，包含 registry.py，base.py，neutral.py，wizard.py，warrior.py，legendary.py，curse.py 以及 duel.py 等对决卡牌具体打出效果类实现。
    - `buffs/`: 战斗 Buff 逻辑包，包含 registry.py 提供装饰器注册机制，以及 buffs.py 继承自 BuffImpl 的各种 Buff 响应逻辑。
    - `relics/`: 遗物逻辑包，包含 registry.py 提供装饰器注册机制，以及 relics.py 包含各种遗物的被动监听逻辑实现。
    - `minions/`: 随从技能子类多态逻辑。
    - `amulets/`: 护符特有钩子回调实现。
    - `enemies/`: 各种怪物与 Boss 意图的具体执行逻辑。
      - `__init__.py`: 通过 `pkgutil` 动态遍历并加载子包及模块，自动装载实体模板类。
      - `base.py`: 敌人模板基类及注册器 `@register_enemy` 声明。
      - `boss.py`: 游戏各阶段 Boss 怪物逻辑实现。
      - `town_enemies.py`: 主城敌人逻辑实现。
      - `minions.py`: 已废弃并置空的文件。
      - `normal/`: 普通怪物行为包，包含各阶段普通怪物的独立行为模块。
      - `elite/`: 精英怪物行为包，包含各阶段精英怪物的独立行为模块。
      - `summon/`: 召唤物行为包，包含各类召唤物的独立行为模块。
    - `events/`: 随机事件选项逻辑子包。
      - `base.py`: 事件选项及模板基类定义。
      - `registry.py`: 事件选项注册器桥接。
      - `fountain.py`, `knight.py` 等 11 个具体事件选项的多态模块实现。
  - `renderer/`: 游戏状态文本渲染层。
    - `__init__.py`: 代理至各渲染子模块的 GameRenderer.
    - `menu.py`: 菜单、卡牌库及玩家牌组渲染。
    - `battle.py`: 战斗界面及简要战斗状态渲染.
    - `duel_renderer.py`: 对决模式公开战局脱敏与各自私密详情渲染。
    - `map.py`: 地图路线预览及可达节点渲染。
    - `explore.py`: 荒野事件、奇妙商店、古老宝箱、战利品等界面渲染.
    - `query.py`: 随从、遗物、Buff及卡牌模糊匹配查询效果渲染。
- `scratch/`: 本地临时测试与仿真目录。
  - `test_flow.py`: 自动化测试入口（肉鸽模式），采用自动扫描机制，加载运行 `rogue_tests/` 下的所有测试用例。
  - `test_duel.py`: 自动化测试入口（对决模式），采用自动扫描机制，加载运行 `duel_tests/` 下的所有测试用例。
  - `test_game.py`: 包含交互式与自动随机仿真的控制台测试程序。
  - `test_astrbot_load.py`: 用于在宿主机验证 Docker 容器内插件加载与依赖导入状况。
  - `run_tests_docker.bat`: 依次在容器中运行上述核心测试文件。
  - `rogue_tests/`: 肉鸽模式拆分后的高内聚单元与集成测试包。
    - `base.py`: 基础 Dummy 测试桩与环境配置。
    - `test_rogue_basic.py`: 基础游戏流程、选择主/子职业、中英文指令别名等基础用例。
    - `test_rogue_card_mech1.py`: 护盾与保留、回响形态及死亡律动交互、钢铁意志卡牌升级与护盾治疗叠加等机制测试。
    - `test_rogue_card_mech2.py`: 0 费消耗牌、多重重放、Arcane Torrent 伤害判定与法术黑名单限制、冲击波与回响形态交互等机制测试。
    - `test_rogue_minions.py`: 随从受击、攻击机制、佣兵在队伍中的索引重组等随从用例。
    - `test_rogue_enemy_stage.py`: 伤害结算及真实伤害判定、怪物行动与晕眩、状态压缩和关卡胜利结算等敌人与关卡用例。
    - `test_rogue_explore.py`: 荒野事件选项（如老兵房、古泉等）、遗物与护符结算、篝火 forge 卡牌强化与跳过等非战斗探索用例。
    - `test_rogue_system.py`: 局外持久化存档与恢复、牌组完备性、以及不同子命令间执行状态的强隔离用例。
  - `duel_tests/`: 对决模式拆分后的高内聚单元与集成测试包。
    - `base.py`: 对决模式基础 Dummy 测试桩与环境配置。
    - `test_duel_basic.py`: 局外牌组创建校验（25-50张、同名卡上限4张）、卡组导出导入分享码、对决菜单等用例。
    - `test_duel_flow.py`: 对局开始、使用卡牌能量扣除、指令队列执行、双人多轮交替回合流转的完整生命周期用例。
    - `test_duel_advanced.py`: 力量 Buff 数值伤害缩放、双击及回响多重打出检测、随从召唤与技能效果（如巡逻队长和旗手）触发用例。
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

### 2.3 核心数据与状态规范
- 数据结构须继承 models/state.py 中的 Dataclass，状态更新均须通过 models/manager.py 中的 SaveManager 完成序列化存盘。
- 引入 0 动作消耗牌机制，当卡牌的 cost_a 与 cost_ba 为 0 时打出不扣除动作资源.
- 改变卡牌效果与状态的机制不应更改卡牌名称：诸如重放（replay）、易碎（fragile）等修饰卡牌效果或状态的机制，不能在卡牌的 `name` 属性中拼接带有修饰状态（例如 `(重放 X)` 等）的后缀，卡牌的原有名称在发生此类修饰时必须保持不变，修饰状态仅以词条形式追加或修改在卡牌描述（desc）的末尾。
- 卡牌与护符描述称呼规范：静态数据中定义的卡牌与护符描述文本（desc / amulet_desc）中，禁止使用“玩家”来指代主角，必须统一称呼为“你”（例如：“你获得 3 点护盾”而不是“玩家获得 3 点护盾”）。
- 禁止大规模后处理“玩家”替换：严禁在后处理中采用任何形式的程序大规模匹配“玩家”并暴力替换为玩家名字的逻辑，以防导致遗物描述、Buff说明、怪物意图等被误替换。必须且仅在真正需要显示玩家昵称的界面（如战斗状态条、探索状态条等）中，显式通过 `player_name` / `run.player.name` 等变量或占位符进行精确格式化渲染。

### 2.4 指令调度与全局命令规范
- 指令分支由 main.py 的统一分发器 _execute_sub_action 路由。所有指令以元组 (res_text, should_terminate) 形式返回。
- 指令前缀配置项 `shortcut_prefix` 类型变更为 `list` 以支持多个前缀别名。匹配时对所有前缀按长度由长至短倒序排列，规避较短的前缀提前截断损坏指令单词。
- 提供“帮助”及“help”专用子命令，调用 GameRenderer.render_help() 列出全量指令的使用教程和中英文别名（包含免前缀模式提示），当输入未知指令时系统应当引导用户使用帮助指令。
- 新增命令设计规范：系统在添加任何新指令时，必须同步添加对应的纯英文命令变体，并且必须支持至少一个快捷命令（如英文缩写、别名或单字快捷指令）。同时，必须在 main.py 的免前缀拦截白名单（如 valid_cmds 或 town_cmds）中同步补全注册这些新增命令及其英文别名，强制确保新命令的免前缀快捷支持。

### 2.5 数据驱动与配置分离规范
- 静态配置数据化：所有卡牌、随从、怪物、护符、遗物、Buff、事件一律禁止硬编码，必须存放在 `game/data/` 的独立数据字典中。
- 反馈模板化：各实现类利用 `.format()` 动态渲染 `feedback` 模板并进行回填。

### 2.6 开闭原则 (OCP) 与事件驱动扩展规范
- 严格遵循开闭原则：对扩展开放，对修改封闭。
- 当引入新的遗物、Buff 或卡牌特性时，绝对禁止直接修改核心战斗引擎 (`battle_engine.py`) 或其它基础状态逻辑。
- 新增逻辑必须通过实现独立的监听器，并在加载时将其绑定 to `event_bus.py` 定义 of 原子事件（如 `BattleStartEvent`、`CardPlayedEvent`、`DamageCalculateEvent`）上来完成交互。确保任何特异性的判断和数值加成都内聚在具体实体类的回调中，不污染基础流转逻辑。

### 2.7 卡牌、遗物、Buff与指令注册规范
- 卡牌注册使用装饰器模式自动完成注册。全局统一在 `game/entities/cards/registry.py` 中导出 `@register_card(cid, **kwargs)`，在具体卡牌类声明处使用，并在 `base.py` 中自动装配实例化，禁止任何硬编码的卡牌注册分支。
- 遗物与 Buff 注册使用声明式装饰器注册与动态扫描反射机制实现。全局通过 `game/entities/relics/registry.py` 的 `@register_relic` 与 `game/entities/buffs/registry.py` 的 `@register_buff` 将具体类发布到全局注册表 `RELIC_CLASS_REGISTRY` 与 `BUFF_CLASS_REGISTRY` 中。特例（如 `GenericMinorVulnerableBuff` 等）在声明时使用 `@register_buff` 手动标注，其余普通实体在文件加载完毕后通过全局 globals() 按照类名驼峰自动转蛇形规则由系统自适应装载，彻底消灭 `RELIC_IMPLS` 与 `BUFF_MAP` 静态硬编码字典。
- 命令行路由使用命令模式（Command Pattern）。全局将具体子动作和指令分别拆分为继承自 `ActionHandler` 和 `CommandHandler` 的命令类，在 `CLIRouter` 内部由映射字典分发，解耦并消除庞大的 `if-else` 结构，完全符合开闭原则。

### 2.8 上帝类拆分与现代化 OOP 规范
- **禁止无限将逻辑堆叠进单个类**：核心引擎类（如 `BattleEngine`、`CLIRouter`、`ExploreEngine`）禁止无限膨胀。如果某个类的代码行数或职责过多，必须根据单一职责原则（SRP）进行重构，将相关业务逻辑组合委派给专门的子战略类（如 `CombatResolver`、`CardPlayer`、`EnemyTurnController`），由原上帝类作为 Facade 门面对外提供一致的 API 兼容。
- **被动监听与被动反应机制解耦**：遗物（Relic）、战斗 Buff、护符（Amulet）等具有监听游戏动作（如战斗开始、摸牌、受到伤害等）并产生被动副作用特性的系统，绝对禁止在战斗主循环中硬编码查询。必须将这些被动逻辑解耦为独立的事件观察者（Observer，如 `RelicTriggerHandler`），通过订阅 `event_bus` 实施原子交互。
- **避免编写大量重复逻辑**：严禁采用复制粘贴形式编写相似的游戏控制或效果逻辑。通用的判断、数值伤害缩放、文字排版等基础规则，必须抽象封装为基类核心流程（Template Method）或共享工具函数（Utility Functions）。
- **声明式自动注册**：对于新增加的事件分支、指令动作或卡牌种类，禁止手动硬编码关联的 if-else 或全局字典映射。统一使用 Python 的 `__init_subclass__` 或装饰器机制，在子类文件被加载时自动将类实例或类对象发布到全局注册表，确保完全的开闭原则（OCP）支持。

### 2.9 新机制与新事件开发规范
- **禁止在执行类中硬编码数值和文案**：
  - 新增随机事件的所有场景描述、选项文本、反馈文案，必须定义在 `game/data/event_data.py` 中，禁止在执行类（EventOption 子类）中硬编码文字串或奖励数值参数。
  - 新机制（如怪兽动作、新随从或护符状态）的所有文本与参数也必须统一放于 `game/data/` 目录的对应独立文件中，由运行时动态反射加载，实现数据与机制代码的彻底分离。
- **高复用性的通用生命周期接口**：
  - 新增事件的所有回调选项均应继承自 `EventOption` 并利用基类提供的模板方法执行。
  - 涉及通用且常见的业务逻辑（例如：展示三选一卡牌且支持跳过、移除牌组卡牌、给予/扣除金币或生命值上限变动），禁止在具体事件选项类中以复制粘贴等形式编写实现，必须直接调用核心引擎中已公开并测试的复用接口（如 `ExploreEngine` 的奖励生成接口、`CombatResolver` 的状态属性增减接口）。
- **可扩展的新机制设计**：
  - 添加新战斗或底层机制时，必须定义新的原子事件（继承自 `GameEvent` 并由 `event_bus` 调度），并对外提供可由 Relic 或 Buff 修改机制参数的标准化字段。
  - 核心处理引擎在进行机制计算时，应只依赖该事件的最终结算数据，以便后续的新卡牌、新被动能够通过订阅该事件完成逻辑扩展，禁止在核心流程中加入特定卡牌或状态的 `if` 逻辑。
  - 任何怪物或 Boss 特异性的生存被动、死亡拦截或形态觉醒逻辑（如“尤格-索托斯”濒死时进入觉醒形态），绝对禁止在核心结算机制 `CombatResolver` 中硬编码。必须完全通过在具体 `EnemyTemplate` 模板中订阅 `EnemyBeforeDeathEvent` 并执行 `event.cancel()` 拦截，进而自适应重组其属性状态，保证核心引擎纯净、高复用。

### 2.10 版本控制与命令规范
- 除非明确提及，否则绝对不能使用任何 git 相关命令。

### 2.11 中文编码与多端兼容规范
- 字符串与文件编码：项目中所有 Python 源代码文件、测试文件以及静态配置文件的读写操作，必须显式指定字符编码为 utf-8（例如使用 open() 时添加 encoding='utf-8' 参数）。
- 环境变量配置：在 Windows 本地运行测试脚本或插件交互验证时，需在终端显式指定 PYTHONPATH="." 以及 PYTHONIOENCODING="utf-8" 环境变量，确保中文字符集正常输出而不发生 UnicodeEncodeError 崩溃。
- 中文文案与语法纯正性：在编写或生成中文本地化文本（如卡牌/护符描述、系统播报、NPC对话和随机事件文案等）时，必须确保中文语法的纯正性，严禁出现非预期的中英混杂介词（如将中文助词“的”误写为英文介词“of”）。

### 2.12 文档与规范同步更新规范
- 如果在开发中更改了与本文档（AGENTS.md）内容有关的部分（例如目录结构调整、全局开发规范变更、新机制规范设计、新模式扩展或指令/动作规范调整等），则必须同步更新此文档，确保开发人员与 AI Agent 的参考指引时效一致。

### 2.13 文件删除规范
- 绝对禁止使用 PowerShell / CMD 等命令行（如 `Remove-Item`、`del`、`rm`）删除非二进制文件。如果行数 < 2000 行，必须优先使用编辑工具清空/删除，除非明确提及，否则绝对禁止运行命令行删除。


---

## 3. 代码编辑与扩展指引

在对项目进行代码编辑、新增卡牌、添加指令或修改系统播报时，应遵守以下编辑指引：

### 3.1 对决模式卡牌开发与扩展指引
- 数据配置分离：新增对决卡牌时，需在 game/data/duel_card_data.py 中的 DUEL_CARD_CONFIG 字典里添加其静态属性定义（包含 cost_a、cost_ba、rarity、type、desc等）。
- 卡牌效果注册：需在 game/entities/cards/duel.py 中实现具体的卡牌效果逻辑类，继承自 DuelCardImpl / CardImpl，并使用装饰器 @register_card(cid) 进行全局注册。
- 0 注释原则：在新增卡牌类时，严禁编写任何 # 井号注释和 docstring 说明文档。

### 3.2 播报及反馈文案修改指引
- 系统消息数据驱动：对决模式中所有的局内外系统广播、错误提示、操作反馈、胜负判决和帮助文本，均统一定义在 game/data/duel_template_data.py 中的 DUEL_BROADCAST_TEMPLATES 字典中。
- 禁止在逻辑代码中硬编码任何中文提示语。所有提示文案的修改必须只在 duel_template_data.py 中进行，并在调用处通过 DUEL_BROADCAST_TEMPLATES["key_name"].format(...) 动态注入。

### 3.3 指令与动作扩展指引
- 局外指令：若要为对决模式新增局外指令，必须在 game/core/duel/commands.py 中编写继承自 DuelCommandHandler 类的具体处理器类，并通过 names 参数传入其支持的指令名别名列表。
- 局内动作：若要新增局内打牌动作，必须在 game/core/duel/actions.py 中编写继承自 DuelActionHandler 类的具体动作处理器，并通过 names 参数传入支持的动作名别名列表。
- 装配机制：系统在运行初始化加载 commands.py 和 actions.py 时，会自动利用 __init_subclass__ 钩子将 these 指令类和动作类实例化并挂载到全局路由中，无需手动在路由器中编写额外的 switch 分支。

### 3.4 文字冒险（主城）模式本地化修改指引
- 主城所有系统提示、菜单交互、物品及房间渲染、切磋胜负结算文案等均已实现完全的 I18N 本地化分离，统一定义在 game/data/town/zh_cn_town.json 中。
- 逻辑代码（包括 town_engine.py, town.py 和 cli_router.py 等）严禁硬编码任何中文字符串，所有交互文本和渲染提示必须通过加载该 JSON 本地化配置文件并使用 zh_cn.get("global").get("key_name") 等方式进行动态回填或格式化渲染。

---

## 4. 测试与运行异常规范

### 4.1 Windows 本地命令行测试运行异常提示
在 Windows 环境下使用 PowerShell 或 CMD 直接运行测试脚本时，可能遇到以下两类环境问题：
1. 模块导入失败（ModuleNotFoundError）：若遇到无法导入 game 的错误，需在运行前显式指定 PYTHONPATH 环境变量（例如在 PowerShell 中执行：$env:PYTHONPATH="."）。
2. 控制台字符集编码错误（UnicodeEncodeError）：若在控制台打印带有各类圆形字符等 Unicode 符号时发生编码报错，需在执行前将 Python 的控制台编码指定为 utf-8（例如在 PowerShell 中执行：$env:PYTHONIOENCODING="utf-8"）。
3. 别名挂起与高 CPU 占用问题：在 Windows 环境下，严禁使用 `python` 命令运行脚本，必须统一使用 `py` 命令行启动器工具（例如 `py scratch/test_flow.py`），以规避触发 Windows 系统默认 of App Execution Aliases 机制，防止外壳包装进程静默死循环挂起并持续耗费 CPU 资源。

### 4.2 测试豁免规则
- 针对仅涉及纯数值微调或修正的改动（例如修改卡牌的伤害、护盾、治疗数值等静态数据配置，而不涉及控制流、游戏状态逻辑修改或新功能开发），无需运行自动化仿真及流验证测试。

### 4.3 单元测试编写规范
为确保项目自动化测试流程的正确性与可维护性，编写新的单元测试和集成测试时必须遵守以下规范：
- 源码零注释约束：所有的测试脚本（包括 scratch/test_flow.py 和 scratch/test_duel.py）同样被视为 Python 源码，其中绝对禁止包含任何以井号字符开头的注释和 docstring 文档字符串。
- 免前缀与用户输入模拟：新编写的单元和集成测试禁止直接调用底层 cli_router.handle_command，必须默认开启 stats.rogue_mode = True 以启用免前缀模式，并且全部通过调用 run_command(plugin, "command_string") 传入完整命令文本来直接模拟真实用户的输入行为。
- 目标血量保护设计：在测试高额伤害的卡牌、随从或特殊状态效果时，应当将承受伤害的敌方目标或随从目标的生命值上限（max_hp）及当前生命值（hp）设定为极高数值（如 9999），以防止目标由于伤害过高而意外死亡并被系统从活动实体字典中移除，导致后续测试指令执行因找不到目标而触发 KeyError 或断言失败。
- 对决牌组完整校验：在对决模式（Duel Mode）的单元测试中，为测试玩家模拟初始化的卡组必须包含 25 张到 50 张卡牌，且同名卡牌的放置数量上限为 4 张。必须通过此局外牌组合法性校验，否则对局引擎将无法开启并返回空实例（None），导致后续的打牌和回合测试发生 AttributeError。
