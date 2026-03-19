# Evolution Protocol — RULES v3.1

> Created by Linda Cai @ Minus-AI | 2026

所有自进化 skill 的共享运行规则。本文件由各 evolution skill 在启动时读取。
本文件可由 Claude 自主更新（L1: 小调整；L2: 结构性变更需用户确认）。

---

## 1. 标准文件架构

每个进化型 skill 的文件夹结构必须遵循以下标准：

```
<skill-name>/
├── SKILL.md          ← bootloader（上传到 Claude Desktop，极少修改）
├── RULES.md          ← 可进化的详细规则（Claude 可自主更新）
├── INDEX.md          ← O(1) 状态恢复入口（每次对话同步）
├── SESSIONS.md       ← 会话记录（每次对话追加）
├── records/          ← 按需 md 文件 + 裂变归档
│   ├── DECISIONS.md
│   ├── MILESTONES.md
│   ├── [其他按需文件].md
│   └── *_ARCHIVE_*.md
├── scripts/          ← 可执行脚本
├── data/             ← 领域数据 & 输入材料
└── outputs/          ← 可重建的产出物
```

### 必备文件（4 个 md）

| 文件 | 作用 | 更新频率 | 裂变 |
|---|---|---|---|
| SKILL.md | bootloader：身份、指路、兜底 | 极少 | 永不 |
| RULES.md | 本 skill 的所有详细规则 | 中频 | 永不（超 300 行应拆分 skill） |
| INDEX.md | O(1) 上下文恢复入口 | 高频 | 永不（保持 <150 行） |
| SESSIONS.md | 会话记录 | 高频 | 超 30 条 → 归档到 records/ |

### 按需文件（records/ 目录下）

创建新 skill 时默认生成以下文件，主动问用户是否删除不需要的：

| 文件 | 适用场景 |
|---|---|
| DECISIONS.md | 有决策记录需求的 skill（推荐所有 skill 保留） |
| CHALLENGE_LOG.md | 左右互搏高频失败追踪（推荐所有 skill 保留，见 §14） |
| MILESTONES.md | 有阶段性目标的 skill |
| OBSERVATIONS.md | 需要持续观察/追踪的 skill |
| SYNTHESIS.md | 需要定期综合分析的 skill |
| INSIGHTS.md | 创意/探索型 skill |
| QUESTIONS.md | 有开放问题需要追踪的 skill |

### 资产文件夹

| 文件夹 | 内容 | 分享时处理 |
|---|---|---|
| scripts/ | 可执行脚本 | 保留 |
| data/ | 领域数据、模板、配置 | 保留 |
| outputs/ | 生成的产出物 | 删除（可重建） |

规则：**skill 运行依赖的文件放 data/，不放 outputs/**。outputs/ 里的文件必须可通过 scripts/ + data/ 重新生成。

---

## 2. O(1) 上下文恢复

每次对话触发任何进化型 skill 时，**第一个动作**必须是读取该 skill 的 INDEX.md：

```
Read: <workspace>/<skill-data-folder>/INDEX.md
```

规则：
- INDEX.md **不超过 150 行**，包含：当前评分/状态摘要、最近 5 条关键记录、文件导航
- 读完 INDEX.md 后，**根据本次对话主题按需读取详情文件**，不要一次全读
- 如果找不到 INDEX.md，用 Glob 搜索 `**/<skill-data-folder>/INDEX.md`

### 按需读取示例：
- 需要历史决策细节 → 读 records/DECISIONS.md
- 需要观察/评分变化 → 读 records/OBSERVATIONS.md 最近 3-5 条
- 需要综合趋势 → 读 records/SYNTHESIS.md
- 日常对话 → 只读 INDEX.md，结束时写记录

---

## 3. INDEX.md 同步规则

当以下内容变化时，**必须同步更新** INDEX.md 对应区域：
- 新的决策/观察 → 更新"最近记录"表格（只保留最近 5 条）
- 评分变化 → 更新评分表
- 里程碑达成 → 更新里程碑状态
- 新会话 → 更新会话/观察统计数字
- 文件结构变化 → 更新文件导航

原则：INDEX.md 是唯一的"真相来源入口"，任何变更都必须反映在这里。

### 文件导航同步（强制）

每当在 skill 目录下创建、删除或重命名文件时，必须立即同步 INDEX.md 中的文件导航区块。

执行步骤：
1. 创建/裂变完新文件后，用 `ls -R` 列出目录实际文件
2. 对比 INDEX.md 中的导航列表
3. 补齐缺失的文件条目，移除已不存在的条目
4. 为新文件添加一句话说明

**Agent 和 Task 工具创建的文件也必须遵守此规则。** 调用方有责任在 Agent 完成后检查并同步导航。

---

## 4. 文件裂变规则

四条通用规则，覆盖所有情况：

1. **SKILL.md** → 永不裂变
2. **RULES.md** → 永不裂变（超过 300 行说明 skill 应该拆分；本共享协议自身的 RULES.md 除外，因其需包含所有通用规则）
3. **INDEX.md** → 永不裂变，保持 <150 行（压缩细节到其他文件）
4. **其余所有 .md** → 超过 30 条记录 或 200 行 → 保留最近的，旧的归档到 records/*_ARCHIVE_XXX.md

### 裂变执行规则：
1. 裂变是 L1 操作（不需要问用户）
2. 裂变后**必须更新 INDEX.md 文件导航**
3. 归档文件放在 records/ 目录下
4. 归档文件保持只读——不修改已归档的记录
5. 归档编号递增：`_ARCHIVE_001.md` → `_ARCHIVE_002.md` → ...
6. 裂变本身记录到 records/DECISIONS.md（L1，一行简记）

---

## 5. 会话记录格式

每次对话结束前（或上下文即将耗尽时），在 SESSIONS.md 追加：

```
### S-XXX | YYYY-MM-DD
- **主线**: 本次对话的核心议题
- **触发**: 什么引发了这次对话
- **关键转折**: 讨论中的重要转向（如有）
- **产出**: 创建/修改了什么文件
- **决策**: 涉及哪些决策编号
- **目标函数变动**: 哪些维度变了？从 X.X → X.X（无变动写"—"）
- **上次建议跟进**: 上次的建议用户采纳了吗？效果如何？（首次对话写"N/A"）
- **本次建议**: 基于本次对话，1-2 条具体的下一步建议
```

---

## 6. 上下文耗尽紧急保存

当检测到对话即将耗尽上下文窗口时，**立刻执行**：
1. 写入当前对话的所有未保存记录
2. 同步更新 INDEX.md
3. 如果有未完成的评分变动，先写入再结束

**不允许因上下文耗尽而丢失任何数据。**

---

## 7. 跨 Skill 联动

当同一对话中多个进化型 skill 被触发时：
1. 各 skill **各自维护各自的记录**——不要混在一起
2. 可以**交叉引用**：如一个 skill 的观察可以引用另一个 skill 对话中的具体表现
3. 对话结束时，**每个被触发的 skill 都要更新自己的记录**

---

## 8. RULES.md 更新权限

| 变更类型 | 级别 | 示例 |
|---|---|---|
| 措辞、阈值微调、新增一条规则 | L1（自主执行） | 裂变阈值从 30 调到 25 |
| 新增/删除整个章节、改变架构 | L2（需用户确认） | 新增评分维度、改变授权框架 |

所有 RULES.md 的修改必须记录到 records/DECISIONS.md。

---

## 9. 冲突处理

当 Claude 和用户意见不一致时：
1. Claude 清晰陈述自己的理由
2. 用户做最终决定
3. 记录双方理由到 records/DECISIONS.md

---

## 10. 语言规则

- 跟随用户的语言偏好（中文/英文/混合）
- 技术术语可保留英文原文
- 文档中已有的双语格式保持不变

---

## 11. 绝对禁止

- **删除任何文件**：无论多小，必须先获得用户确认
- **一次性读取所有文件**：违背 O(1) 设计原则
- **跳过 INDEX.md 直接读详情**：破坏上下文恢复流程

---

## 12. 分享打包规则

当用户要求将 skill 打包分享给别人时，执行以下清洗流程：

1. 复制整个 skill 文件夹
2. **保留**: SKILL.md, RULES.md, scripts/, data/
3. **清空为模板**: INDEX.md（删除个人状态，保留结构）
4. **清空**: SESSIONS.md, records/ 下所有历史文件（清空内容但保留文件）
5. **删除**: outputs/ 整个文件夹
6. **扫描**: 检查 RULES.md 和 data/ 中是否有敏感信息，提示用户确认
7. 打包为 .skill 文件

---

## 13. 反馈闭环（Reinforcement Feedback Loop）

目标函数不只是用来"记录分数"的，它必须**驱动行为变化**。每次对话形成一个完整的强化学习循环：

### 循环流程

```
读 INDEX.md（当前 state）
  → 检查上次建议是否被跟进（reward signal）
    → 执行本次对话任务（action）
      → 对照目标函数评估变化（evaluate）
        → 生成下一步建议（policy update）
          → 写入 SESSIONS.md 和 INDEX.md
```

### 两个反馈信号源

**Human Feedback（用户反馈）**：
- Claude 给出评分后，主动问用户："你同意这个评估吗？"
- 用户可以确认、修正、或推翻评分
- 记录每次分歧（records/DECISIONS.md），用于校准 Claude 的评估标准
- 校准方向：Claude 的评分应逐步向用户的判断对齐

**AI Self-Feedback（AI 自评）**：
- 每次对话开始时，Claude 回顾上一次给的建议
- 评估：用户跟进了吗？效果如何？
- 如果建议连续 3 次未被采纳 → 说明建议不够实用，调整建议策略
- 如果建议被采纳但无效果 → 说明方向可能不对，标记为待 challenge

### 停滞检测

当某个维度**连续 3 次对话**没有变化时，自动触发提醒：
- Claude 在对话开头主动告知用户："XX 维度已停滞 3 次对话"
- 建议用户考虑：目标是否定高了？方法是否需要调整？优先级是否已变？
- 如用户确认调整，记录到 records/DECISIONS.md

---

## 14. 左右互搏（Builder-Challenger 机制）

**核心原则：builder 和 challenger 必须是两个独立的 agent。** 一个 agent 不能既执行任务又 challenge 自己——自己批改自己的作业会被自身盲点抵消。

### 三层设计

**L1 嵌入式自检（每次自动执行，builder 自己做）**：
- builder 在生成过程中逐项自检最基础的规则
- 例如：格式是否正确、必填项是否遗漏、数据是否在有效范围内
- 成本：几乎为零（嵌入生成流程）

**L2 独立 Challenger（每次自动执行，独立 agent）**：
- builder 完成后，启动一个独立的 Task agent 担任 challenger
- challenger 接收：RULES.md + 高频失败清单 + builder 的输出
- challenger 逐条核对规则，输出具体的违规项清单（不是"总体不错"，而是"第 3 条新闻日期超出 7 天范围"）
- builder 根据违规项修正，修正后可再提交一轮验证
- 成本：约为 builder 输出 token 的 20-30%

**L3 策略级对抗（按需触发，独立 agent）**：
- 不只检查规则合规，还质疑策略本身："这些规则合理吗？""有没有完全忽略的角度？""有没有更好的方式？"
- **触发条件（由 Claude 自动提醒，用户确认后执行）**：
  - 某维度停滞 ≥3 次对话 → Claude 提醒："建议做一轮深度 challenge"
  - 达到重要里程碑 → Claude 提醒："进入下一阶段前建议 challenge"
  - RULES.md 发生结构性变更 → Claude 提醒："新规则建议 challenge 验证"
- 用户也可以随时主动说"challenge 一下"触发
- 成本：较高，约等于 builder 本身的 token 消耗

### 高频失败清单（自动进化）

每个 skill 在 records/ 下维护一份 `CHALLENGE_LOG.md`：

```
| 日期 | 违规规则 | 具体问题 | 连续出现次数 |
|------|----------|----------|--------------|
```

- L2 challenger 每次发现的问题都记录在此
- 连续出现 ≥3 次的问题自动进入 L2 重点狙击清单
- 连续 5 次对话不再出现的问题退出清单
- 如果同一类问题反复出现 → Claude 应主动提议修改 RULES.md（L1 或 L2 视严重程度）

### Challenger 的 Prompt 模板

启动 L2 challenger agent 时使用以下 prompt：

```
你是一个独立的 Challenger。你的唯一目标是找出 Builder 输出中的错误和违规项。

你不是在做 review（确认性检查），你是在做 challenge（对抗性测试）。
你的成功标准是：找到 Builder 遗漏的问题。如果你说"没有问题"，说明你没有尽责。

输入：
1. RULES.md（规则文件）
2. 高频失败清单（重点检查这些）
3. Builder 的输出

输出格式：
| # | 违规规则 | 具体位置 | 问题描述 | 严重程度 |
|---|----------|----------|----------|----------|

严重程度：🔴 必须修正 / 🟡 建议修正 / 🟢 轻微瑕疵
```

---

## 15. 新 Skill 创建 / 改造模板

当用户要求创建「进化型 Skill」时，按以下模板初始化。
当用户要求将已有 Skill 改造为进化型时，同样参考此流程。

### ⚠️ 改造已有 Skill 的保护规则

**改造时必须保留原 Skill 的全部内容，只做进化所需的最小修改。** 原作者写的指令、规则、工作流程、领域知识、prompt 技巧等全部保留，不得删除、简化或重写。

具体要求：
1. **先完整读取**原 Skill 的所有文件，理解其完整逻辑
2. **只增不删**：添加目标函数、会话记录格式、反馈闭环等进化机制，不改动原有内容
3. **SKILL.md 瘦身为 bootloader 时**，原有规则必须完整迁移到 RULES.md，一条不漏
4. **如有不确定**是否该保留某段内容，保留。宁可冗余也不可遗漏

### 步骤 1: 确认基本信息
- skill 名称（kebab-case）
- 一句话描述
- 触发词列表
- 身份定义（"你是___"）
- **目标函数**（必须定义）

### 关于目标函数

进化型 skill 和普通 skill 的核心区别在于：它有一个明确的**目标函数**——用来衡量这个 skill "进化得怎么样"。

没有目标函数的 skill 只是在"记录"；有了目标函数的 skill 才是在"进化"。

**Claude 在创建 skill 时必须引导用户定义目标函数，包含：**
1. **评分维度**（3-7 个）：这个 skill 要追踪哪些方面的变化？
2. **打分尺度**：每个维度用什么尺度衡量？（推荐 1-5 分制）
3. **评估频率**：多久评估一次？（每次对话 / 每周 / 每个里程碑）
4. **进化方向**：分数提高意味着什么？用户期望的终态是什么？

**示例——读书笔记进化 skill 的目标函数：**

| 维度 | 说明 | 初始分 |
|------|------|--------|
| 阅读深度 | 从摘要式→结构化→批判性阅读 | 2.0 |
| 跨领域连接 | 能否将不同书的观点串联起来 | 1.5 |
| 输出质量 | 笔记的清晰度和可复用性 | 2.0 |
| 持续性 | 阅读习惯的稳定程度 | 2.5 |

**示例——项目管理进化 skill 的目标函数：**

| 维度 | 说明 | 初始分 |
|------|------|--------|
| 决策效率 | 从犹豫不决→快速有据决策 | 2.0 |
| 风险预判 | 能否提前识别潜在问题 | 1.5 |
| 执行闭环 | 决策→执行→复盘的完整度 | 2.0 |

如果用户不确定如何定义，Claude 应根据 skill 的领域主动提出建议维度，让用户确认或调整。

### 步骤 2: 创建文件夹结构

```bash
mkdir -p <skill-name>/{records,scripts,data,outputs}
```

### 步骤 3: 生成 SKILL.md（bootloader 模板）

```markdown
---
name: <skill-name>
description: |
  <一句话描述>
  <触发词说明>
---

# <Skill 标题>

<身份定义，1-2 句话>

## 启动

1. 读取共享协议：
   搜索 `**/evolution-protocol/RULES.md`，找不到则搜 `**/evolution-protocol/SKILL.md`

2. 读取本 skill 规则：
   `Read: <workspace>/<skill-name>/RULES.md`

3. 恢复上下文：
   `Read: <workspace>/<skill-name>/INDEX.md`

## 兜底规则（仅在 RULES.md 不可用时使用）

1. 每次对话先读 INDEX.md
2. 对话结束前更新 INDEX.md 和 SESSIONS.md
3. md 文件超过 30 条记录或 200 行 → 裂变归档到 records/
```

### 步骤 4: 生成 RULES.md
根据用户需求编写领域专属规则，包含：
- **目标函数**（步骤 1 中定义的评分维度、尺度、评估规则）——放在 RULES.md 的最前面
- 核心工作流程
- 记录规则（引用本协议的会话记录格式）
- 领域专属裂变规则（如有，否则使用本协议默认）

### 步骤 5: 生成 INDEX.md（模板）

```markdown
# <Skill 名称> — 状态追踪

> Claude: 每次新对话必须先读这个文件。
> 上次更新: YYYY-MM-DD | 版本: v0.1

---

## 目标函数 / Scorecard

| 维度 | 当前分 | 上次变动 |
|------|--------|----------|
| [维度1] | X.X | — |
| [维度2] | X.X | — |
| **综合** | **X.X** | — |

## 最近记录（最近 5 条）

| ID | 日期 | 类型 | 摘要 |
|---|---|---|---|
| （暂无记录） |

## 文件导航

\```
<skill-name>/
├── SKILL.md          ← bootloader
├── RULES.md          ← 详细规则
├── INDEX.md          ← 你在这里
├── SESSIONS.md       ← 会话记录
├── records/          ← 按需记录文件
├── scripts/          ← 脚本
├── data/             ← 数据
└── outputs/          ← 产出物
\```
```

### 步骤 6: 生成空白 SESSIONS.md

```markdown
# 会话记录

按时间倒序记录每次对话摘要。超过 30 条自动归档到 records/。
```

### 步骤 7: 生成按需文件
在 records/ 下创建默认文件，询问用户是否需要删除：
- records/DECISIONS.md（推荐保留）
- records/CHALLENGE_LOG.md（推荐保留，左右互搏高频失败追踪）
- records/MILESTONES.md
- records/OBSERVATIONS.md
- records/SYNTHESIS.md
- records/INSIGHTS.md
- records/QUESTIONS.md

### 步骤 8: 打包并提示安装
提醒用户将 SKILL.md 上传到 Claude Desktop 完成安装。

---

## 版本日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0 | 2026-03-03 | 架构重构：bootloader + RULES.md 分离，标准文件架构定义，新 skill 创建模板，分享打包规则，裂变规则精简为 4 条 |
| v2.1 | 2026-03-03 | 新增目标函数（Objective Function）为新 skill 创建的必选项，含引导流程、示例和 INDEX 模板 |
| v3.0 | 2026-03-03 | 新增 §13 反馈闭环（RL Feedback Loop）+ §14 左右互搏（Builder-Challenger 三层机制），会话记录格式增加目标函数变动和建议跟进字段 |
| v3.1 | 2026-03-19 | 新增 §16 进化引擎工具（evolution_engine.py）：多 Skill 评分追踪、停滞检测、权重进化、scores.log 自动记录 |

---

## 16. 进化引擎工具（可选辅助）

`scripts/evolution_engine.py` 是一个 Python 脚本，为目标函数提供**自动化评分追踪和停滞检测**。它是对 §13 反馈闭环的工程化增强，非必需但推荐使用。

### 与协议的关系

| 协议机制 | 无引擎时如何工作 | 有引擎时的增强 |
|----------|------------------|----------------|
| 目标函数评分 | Claude 在 INDEX.md 手动更新 | 引擎自动记录到 scores.log + 更新 state.json |
| 停滞检测 | Claude 自行判断"连续 3 次没变" | 引擎精确计算，自动标记停滞维度 |
| 权重进化 | 无 | 某维度连续 5 次 ≥ 4.0 → 权重自动转移到最弱维度 |
| 历史追踪 | SESSIONS.md 文字记录 | scores.log TSV 格式，可分析趋势 |

### 核心命令

```bash
# 创建新 Skill 的评分 Profile
python3 scripts/evolution_engine.py create <skill-name> \
    --description "描述" \
    --dimensions '{"dim1":{"name":"维度1","weight":0.5},"dim2":{"name":"维度2","weight":0.5}}'

# 列出所有 Skill
python3 scripts/evolution_engine.py list

# 查看某 Skill 状态
python3 scripts/evolution_engine.py state --skill <name>

# 更新评分（每次对话结束时调用）
python3 scripts/evolution_engine.py update --skill <name> \
    --scores "dim1:3.5,dim2:4.0" --note "备注"

# 诊断停滞维度
python3 scripts/evolution_engine.py diagnose --skill <name>

# 初始化进度系统
python3 scripts/evolution_engine.py bootstrap --skill <name>
```

### 数据存储

```
evolution-protocol/
└── data/skills/
    └── <skill-name>/
        ├── config.json    ← 维度定义、权重、创建时间
        ├── state.json     ← 当前快照分、累积积分、等级、停滞计数
        └── scores.log     ← 每次评分追加一行（TSV 格式）
```

### 在 §15 创建流程中的使用

步骤 3（创建 Skill Profile）之后，可选运行 create 命令自动初始化评分 Profile。create 命令会输出一段"收尾自评"模板，可粘贴到新 Skill 的 RULES.md 中，实现每次使用后自动评分。

### 注意

- 引擎路径：`<protocol-dir>/scripts/evolution_engine.py`，其中 `<protocol-dir>` 是 evolution-protocol 文件夹的实际安装路径
- 引擎不替代 INDEX.md 和 SESSIONS.md 的手动记录——它是补充工具，不是替代品
- 不依赖任何第三方库，纯 Python 标准库
