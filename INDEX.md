# Evolution Protocol — 状态追踪

> Claude: 每次新对话必须先读这个文件。
> 上次更新: YYYY-MM-DD | 版本: v3.1

---

## 当前状态

协议已就绪，等待被其他进化型 skill 引用。

## 依赖此协议的 Skill

| Skill | 状态 | 已改造为 v2.0 架构 |
|---|---|---|
| （安装进化型 skill 后自动出现） |

## 最近记录（最近 5 条）

| ID | 日期 | 类型 | 摘要 |
|---|---|---|---|
| （暂无记录） |

## 文件导航

```
evolution-protocol/
├── SKILL.md              ← bootloader（上传到 Claude Desktop / OpenClaw）
├── RULES.md              ← 详细规则（v3.1，可进化）
├── INDEX.md              ← 你在这里
├── SESSIONS.md           ← 会话记录
├── records/
│   ├── DECISIONS.md      ← 决策记录
│   ├── CHALLENGE_LOG.md  ← 高频失败清单（Challenger 免疫系统）
│   ├── MILESTONES.md     ← 里程碑记录
│   ├── OBSERVATIONS.md   ← 观察记录
│   ├── SYNTHESIS.md      ← 综合分析
│   ├── INSIGHTS.md       ← 洞察记录
│   └── QUESTIONS.md      ← 开放问题追踪
├── scripts/
│   └── evolution_engine.py  ← 进化引擎工具（评分追踪、停滞检测）
├── data/
│   └── skills/           ← 各 Skill 的评分数据（自动创建）
├── outputs/              ← 产出物（可重建，分享时删除）
└── README_操作指南.md    ← 完整使用指南
```
