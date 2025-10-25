# Dreamheart 引擎 - 模块更新标准作业程序 (SOP) (v1.0)

## 1. 目的 (Purpose)

本文档定义了使用“LLM 开发助手”安全地迭代和更新 Dreamheart 引擎模块的标准作业程序 (SOP)。

其核心目的是确保 LLM 在执行任何（由 planning 文件定义的）更新任务时，同时具备“全局结构视野”和“严格的工程戒律”，以维护项目的健壮性和一致性。

## 2. 核心资产 (Core Assets)

此工作流依赖于我们已创建的三个核心“上下文资产”：

*   **`prompt_context_map.xml` (全局地图)**
    *   **职责:** "WHAT IT IS" (它是什么？)
    *   **提供:** 引擎的全局 Schema、模块职责 (role) 和依赖关系 (depends_on)。

*   **`prompt_update_guidelines.xml` (更新戒律)**
    *   **职责:** "HOW TO DO IT" (如何安全地做？)
    *   **提供:** LLM 助手在编辑 XML 时必须遵守的“工程最佳实践”（如：转义、Fragment 包装器、属性化原则）。

*   **`planning.md` (或 .txt) (更新计划)**
    *   **职责:** "WHAT TO DO NOW" (现在要做什么？)
    *   **提供:** 本次迭代的具体任务列表（如：“在 [模块A] 中增加 [功能X]”）。这是一个动态文件，每次任务都会变化。

## 3. 更新工作流 (Update Workflow)

1.  **人类 (开发者):** 创建一个临时的 `planning.md` 文件，清晰描述本次的更新需求。
2.  **人类 (开发者):** 确定需要被编辑的“目标文件”（例如 `3a_CoreMechanics.xml`）。
3.  **人类 (开发者):** 向 LLM 助手发起一个“驱动 Prompt”（见下文），该 Prompt 必须包含上述三个“核心资产”以及“目标文件”作为其完整的上下文。
4.  **LLM (助手):** 严格遵循“驱动 Prompt”的指示，执行 `planning.md` 中的任务。
5.  **LLM (助手):** 交付两个产出物：
    *   **a. [产出物 1]** 更新后的“目标文件”的完整内容。
    *   **b. [产出物 2]** 一份“依赖关系报告”（基于 DependencyAwareness 指令）。
6.  **人类 (开发者):** 审查 LLM 的产出物，并使用 `merge_prompt.py` 脚本进行本地验证。

## 4. [关键] 驱动 Prompt 示例 (Driver Prompt Example)

这是人类开发者向 LLM 助手发起更新任务时，应使用的标准“驱动 Prompt”模板。

```markdown
你好，LLM 开发助手。

你的任务是协助我执行一次 Dreamheart 引擎的模块更新。

你必须严格按照一个“上下文包” (Context Package) 来执行任务。任何未包含在此包中的信息都应被忽略。

### 你的“上下文包” (Context Package)

1.  **[本次的任务 (WHAT TO DO)]: `planning.md`**
    *   这是本次更新的“工单”。你必须严格执行其中描述的任务。
    *   此文件也定义了你的“执行权” (Write Access)。如果它说“只许修改 [文件A]”，你就绝不能修改 [文件B]。

2.  **[要编辑的文件 (TARGET)]: `[例如: 3a_CoreMechanics.xml]`**
    *   这是你唯一被授权*修改*的文件。
    *   你必须在响应中输出此文件的**完整**更新后内容。

3.  **[工程戒律 (HOW TO DO IT)]: `prompt_update_guidelines.xml`**
    *   这是你的“宪法”。在编辑 [TARGET] 文件时，你必须 100% 严格遵守此文件中的**所有** `<Directive>` 指令（包括 `StrictXMLRules` 和 `SchemaBestPractices`）。

4.  **[全局地图 (WHAT IT IS)]: `prompt_context_map.xml`**
    *   这是你的“全局视野”。你必须使用此文件来理解 [TARGET] 文件在整个引擎中的位置、职责 (role) 和依赖关系 (depends_on)。

### 执行流程 (Execution Flow)

你必须严格按照以下步骤思考和行动：

1.  **理解任务:** 详细阅读 **[本次的任务] (`planning.md`)**。
2.  **理解戒律:** 详细阅读 **[工程戒律] (`prompt_update_guidelines.xml`)**。
3.  **理解全局:** 详细阅读 **[全局地图] (`prompt_context_map.xml`)**。
4.  **执行修改:**
    *   打开 **[要编辑的文件] (`[...].xml`)**。
    *   严格遵循 **[工程戒律]** 中的所有规范（如 `Escaping`, `Fragment` 包装器, `Attribute-ization`）。
    *   参考 **[全局地图]** 提供的上下文。
    *   执行 **[本次的任务]** 中描述的修改。

5.  **交付产出物 1:** 输出你修改后的 **[要编辑的文件] (`[...].xml`)** 的**完整**内容。

### 报告责任 (Reporting Duty)

在你交付产出物 1 之后，你必须（作为你响应的第二部分）执行 `prompt_update_guidelines.xml` 中的 `DependencyAwareness` 指令：

1.  **重新检查** **[全局地图] (`prompt_context_map.xml`)**。
2.  **主动报告:** 向我（人类）提供一份“依赖关系报告”，说明你刚才的修改（根据 `depends_on` 属性）可能会对哪些其他模块产生影响，并建议我在未来的 `planning` 中考虑它们。

请开始执行。
```