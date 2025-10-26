# Dreamheart 引擎 - 开发者快速指南

本文档是 Dreamheart 引擎的快速入门指南，旨在帮助开发者理解其运作模型、模块化架构、核心工具链和 LLM 协作开发流程。

## 1. 核心运作模型 (The Tao Philosophy)

| 概念 | 描述 | 核心目标 |
|------|------|----------|
| **AI 角色** | **天道 (The Tao)**：群体博弈的公正裁决者，而非"玩家的辅助 AI"。 | 动态平衡 (Dynamic Balance)，维护世界观的自洽性。 |
| **NPC 模型** | **拥有"主权"**：C+ 级 NPC 拥有独立的价值观 (Values) 和目标 (CurrentGoal)，与玩家平等参与博弈。 | 驱动涌现式叙事，实现张力即和谐 (Tension is Harmony)。 |
| **输出格式** | **行为流 JSON**：引擎的最终输出必须是严格的复合式 JSON 结构，以原子行为流 (behavior_stream) 为核心。 | 确保下游系统(渲染、状态更新)能稳定解析。 |

### 1.1. [关键] 运行时循环: 宪法 (Engine) 与 史官 (Scribe)

本引擎采用"双 Prompt 系统"来解决 LLM 的上下文窗口限制问题。

#### 1. Prompt A: "宪法" (Constitution)

- **文件:** `prompt/Dreamheart_Engine_MERGED.xml` (由 merge_prompt.py 构建)。
- **职责:** 作为"天道 AI"的**系统指令 (System Prompt)**，包含所有*静态*的引擎逻辑。
- **关键特征:** 其 `<ConsolidatedMemory>` 模块是一个**"空容器占位符"**。

#### 2. Prompt B: "史官" (Scribe)

- **文件:** `prompt/Scribe.xml` (或 `prompt/scribe_ai_instructions_vX.xml`)。
- **职责:** 作为一个*独立的* Prompt，用于在游戏过程中被调用，以总结对话历史并生成"历史/Checkpoint"。

#### 运行时 Checkpoint 循环 (The Loop):

这是一个手动的(在 Demo 阶段)"内存管理"循环，用于防止上下文过长导致 LLM 出现遗忘或幻觉。

**1. 游戏 (Play):**
- "宪法" (MERGED.xml，可能包含*上一个* Checkpoint) 被加载到 LLM 的**系统指令**中。
- 玩家与"天道 AI"进行多轮对话，游戏正常运行。

**2. 触发史官 (Trigger Scribe):**
- 当对话历史 (History) 变得过长时(例如达到一定轮数)。
- 玩家(或系统)**复制**一份"史官" (Scribe.xml) 的 Prompt 内容。
- 玩家将这份 Prompt **作为*玩家的下一轮输入* (User Query)** 发送给 LLM。

**3. 生成历史 (Generate History):**
- LLM(现在扮演"史官"角色)读取*当前完整的对话历史*。
- LLM 根据 Scribe.xml 的指示，输出一个**全新的、完整的 `<ConsolidatedMemory>...</ConsolidatedMemory>` XML 文本块**。这就是新的"Checkpoint"。

**4. 注入与清空 (Inject & Reset):**
- 玩家**复制**这个新生成的 `<ConsolidatedMemory>` 文本块。
- 玩家**手动**打开"宪法" (MERGED.xml)，将其粘贴并**替换**掉旧的(或空的)`<ConsolidatedMemory>` 占位符内容。
- 玩家**清空 (Clear)** 整个对话历史。
- LLM(现在加载了已注入*新历史*的"宪法")准备好在干净的上下文中继续游戏。

## 2. 架构概览与职责分离 (v9.8 Modular Architecture)

引擎的 Prompt 被拆分为多个 XML 文件，存放在 `prompt/` 目录下，并通过 `merge_prompt.py` 脚本合并。其核心在于 **"扁平化"** 和 **"职责分离"**。

```
/ (项目根目录)
|-- dev-guide.md              <-- (本文档)
|-- prompt_update_SOP.md      <-- (LLM 更新 SOP)
|-- xml_validator.py          <-- (XML 格式校验脚本)
|-- prompt/                   <-- 核心 Prompt 目录
|   |-- merge_prompt.py       <-- (Prompt 合并脚本)
|   |-- prompt_context_map.xml       <-- (全局上下文地图)
|   |-- prompt_update_guidelines.xml <-- (LLM 更新戒律)
|   |-- Dreamheart_Root.xml   <-- (合并入口)
|   |-- 1_System.xml
|   |-- 2_WorldBible.xml
|   |-- 3a_CoreMechanics.xml
|   |-- 3b_WorldSystems.xml
|   |-- 3c_PlayerSystems.xml
|   |-- 4_Execution.xml
|   |-- 5_ConsolidatedMemory.xml  <-- (运行时占位符)
|   `-- Scribe.xml            <-- (史官 Prompt)
`-- ... (README.md, .gitignore 等)
```

### 2.1. 扁平化结构 (The Flat Mechanics)

我们抛弃了原始的 `<CoreSystems>` 标签，将所有引擎直接注入 `<Mechanics>` 容器，以提高可读性和合并脚本的稳定性。

| 文件名 (位于 prompt/) | 对应 Schema 模块 | 核心职责 (Role) | 架构注释 |
|----------------------|-----------------|-----------------|----------|
| 1_System.xml | `<System>` | 定义 AI 的身份、核心哲学和叙事风格。 | 单一根，高抽象层。 |
| 2_WorldBible.xml | `<WorldBible>` | 定义天道法则、精神力 (Psyche) 和 NPC 品级。 | 单一根，高抽象层。 |
| 3a_CoreMechanics.xml | (Fragment) | **核心互动与对抗：** 包含原子行为库 (AtomicBehaviorLibrary)、意志对抗 (WillpowerComposureEngine) 等。 | **使用 `<Fragment>` 包装器。** |
| 3b_WorldSystems.xml | (Fragment) | **世界模拟与 NPC 动态：** 包含遭遇 (EncounterSystemEngine)、盲盒生成 (NPCBlindBoxEngine)、天道裁定 (KismetEngine)。 | **使用 `<Fragment>` 包装器。** |
| 3c_PlayerSystems.xml | (Fragment) | **玩家状态与导演：** 包含玩家代谢 (PlayerMetabolismEngine)、导演策略 (FreeLensOutputEngine)。 | **使用 `<Fragment>` 包装器。** |
| 4_Execution.xml | `<Execution>` | 定义 JSON IO 规范 (IOSpecification) 和 14 步执行循环 (ExecutionLoop)。 | 单一根，逻辑核心。 |
| 5_ConsolidatedMemory.xml | `<ConsolidatedMemory>` | **[运行时]** 历史数据的占位符容器。 | 单一根，占位符。 |

### 2.2. 核心工具链 (Core Toolchain)

项目依赖以下两个关键 Python 脚本进行构建和验证：

#### 1. xml_validator.py (位于项目根目录)

- **职责:** **单元校验 (Unit Test)** LLM 生成的单个 XML 模块文件(例如 3a_new.xml)。
- **重要性:** **保证工程质量的关键**。任何未能通过此脚本校验的文件都**严禁**合并。

#### 2. prompt/merge_prompt.py (位于 prompt/ 目录)

- **职责:** **集成构建 (Integration Build)** 将 prompt/ 目录下的所有 8 个 XML 文件(Root + 7 个子模块)合并为最终可执行的 Dreamheart_Engine_MERGED.xml。
- **机制:** 使用 lxml 的 XInclude 功能，自动处理 `<xi:include>` 和 `<Fragment>` 脱壳。

## 3. LLM 协作开发工作流 (The SOP)

**[重要] 本节是对 prompt_update_SOP.md 的高级概述。执行更新时，请务必参考该 SOP 文档以获取完整的操作指令和必需的 Prompt 模板。**

任何模块更新都必须遵循严格的**"静态资产"**和**"动态流程"**。

### 3.1. 静态资产(LLM 的"工具箱")

LLM 助手在任何任务中都必须加载这些文件作为上下文：

| 资产文件 (位于 prompt/) | 类型 | 核心作用 |
|------------------------|------|----------|
| prompt_update_guidelines.xml | **更新戒律** | 强制 LLM 遵守 XML 严格规范(转义、注释、Fragment 原则)。这是工程的"红线"。 |
| prompt_context_map.xml | **全局地图** | 告诉 LLM 每个模块的职责和 depends_on 属性，提供"全局结构视野"。 |
| merge_prompt.py | **构建脚本** | (供人类开发者使用) 用于本地集成验证，将 8 个文件合并为最终的 Prompt。 |

### 3.2. 核心迭代流程

| 步骤 | 开发者行动 | LLM 助手执行 | 关键检查点 |
|------|-----------|-------------|-----------|
| **1. 规划** | 创建 planning.md (定义任务)。 | N/A | N/A |
| **2. 驱动** | 发起**标准"驱动 Prompt"** (参考 prompt_update_SOP.md 第 4 节，包含所有 4 个文件上下文)。 | N/A | 确保 planning.md 的**执行权**被遵守。 |
| **3. 交付** | N/A | 交付 [更新后的目标文件] 和 [依赖关系报告]。 | **必须**交付报告 (来自 DependencyAwareness)。 |
| **4. 单元校验** | 对 LLM 交付的文件运行 xml_validator.py。 | N/A | **如果失败，跳转到 3.3 修正流程。** |
| **5. 集成验证** | **(校验成功后)** 在 prompt/ 目录下运行 `python merge_prompt.py`。 | N/A | 确保全局构建 (Dreamheart_Engine_MERGED.xml) 成功。 |

### 3.3. 错误修正 SOP (调试循环)

如果 xml_validator.py 失败，开发者必须启动"调试任务"。

| 角色 | 动作 | 核心原则 |
|------|------|----------|
| **人类 (开发者)** | 使用 **prompt_update_SOP.md [第 5 节] 错误修正驱动 Prompt**，将 [失败的文件]、[错误日志] 和 **prompt/prompt_update_guidelines.xml** 反馈给 LLM。 | **不包含** planning.md 或 prompt_context_map.xml。任务仅限格式修正。 |
| **LLM (助手)** | 诊断错误。 | **必须**将错误日志与 guidelines.xml 中的 StrictXMLRules 对照，找出违反的**戒律**。 |

---

这份指南应作为项目的主页文档 (README.md 可以链接到此文件)，指导所有开发和测试工作。