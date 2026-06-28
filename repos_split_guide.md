# 魔法肉鸽与独立对决插件仓库拆分部署指引 (Repository Split Guide)

本项目目前已经在逻辑依赖和物理文件上完成了彻底的解耦，形成了“无头后端核心”、“CLI前端”、“AstrBot肉鸽前端”和“AstrBot对决前端”的架构设计。

若需将它们分别推送到独立的 Repository，请按照以下规划进行拆包与发布。

---

## 1. 独立仓库划分规划

### 1.1 无头游戏后端核心 (Headless Core)
* **包含目录**：`game/` 目录下的核心逻辑（模型、配置、游戏规则、探索与战斗状态机、主城和咖啡馆逻辑，不包含对决组件）。
* **作用**：纯粹的游戏逻辑和无头驱动服务。对外仅暴露 `HeadlessGameServer` 网关接口，不依赖任何特定聊天平台或命令行输入。
* **发布建议**：可作为单独的私有包发布，或者在各前端中使用 `git submodule` 引入。

### 1.2 CLI 命令行前端 (CLI Frontend)
* **包含目录/文件**：`play_rogue.py` 控制台主程序。
* **作用**：提供免前缀的本地控制台交互游玩入口。
* **依赖关系**：仅通过 `from game.core.headless_server import HeadlessGameServer` 导入无头后端核心，彻底清除了对 AstrBot 平台和 `main.py` 的一切隐式依赖。

### 1.3 AstrBot 肉鸽主插件 (AstrBot Rogue Plugin)
* **包含目录/文件**：`main.py` (肉鸽版)、`metadata.yaml` (肉鸽版) 以及 `game/` 无头后端。
* **作用**：作为 AstrBot 的插件前端运行，只负责接收肉鸽指令、群聊拦截、进行 Matrix 排版优化及管理员鉴权，不含任何对决模式逻辑。
* **依赖关系**：委派全部肉鸽游戏流程至 `HeadlessGameServer`。

### 1.4 AstrBot 独立对决插件 (AstrBot Duel Plugin)
* **包含目录/文件**：位于 `astrbot_plugin_text_roguelike_duel`。包含其专用的 `main.py`、`metadata.yaml`、`game/`（包含对决专有的核心逻辑与独立的对战渲染）。
* **作用**：独立的双人 TCG 对决插件，支持单独匹配、邀请、牌组构筑导入导出、以及多人同时并发对战。
* **依赖关系**：仅加载对局与查询逻辑，使用独立的自动化对局测试套件。

---

## 2. 共享存档与积分 (GP) 机制

在本次重构中，对决插件和肉鸽主插件实现了完美的存档共享：
* **实现原理**：对决插件在初始化 `SaveManager` 时，强行指向肉鸽插件的专属数据存储目录：
  ```python
  data_dir = str(StarTools.get_data_dir("astrbot_plugin_text_roguelike"))
  ```
* **效果**：
  1. 两个独立插件在同一个 AstrBot 实例中运行时，会读写同一套玩家本地存档（`UserStats` 及牌组构筑）。
  2. 玩家在对决插件中进行联机对战赢得的 GP 积分，将实时写入共享存档，肉鸽主插件的主城商店与咖啡馆系统可以立刻消费该积分，实现跨仓库、跨插件的全局数据同步。

---

## 3. 测试与部署流程

### 3.1 运行肉鸽测试 (主项目目录下)
```powershell
python scratch/test_flow.py
```

### 3.2 运行对局测试 (对战项目目录下)
```powershell
python scratch/test_duel.py
```

### 3.3 本地命令行游玩 (主项目目录下)
```powershell
python play_rogue.py
```
