---
name: evolution-protocol
description: |
  所有进化型 skill 的共享运行协议。定义标准文件架构、O(1) 上下文恢复、文件裂变、会话记录、紧急保存、跨 skill 联动等通用规则。
  本 skill 不直接触发，而是被其他 evolution skill 在启动时自动引用。
  当用户要求创建「进化型 Skill」时，也必须加载此协议以使用标准创建模板。
  触发词: "进化", "evolve", "创建skill", "创建进化型", "evolution"
  DO NOT trigger directly. Loaded as shared dependency by evolution skills. Also triggered when creating new evolution-type skills.
---

# Evolution Protocol

所有自进化 skill 的共享运行协议。

> Created by Linda Cai @ Minus-AI | 2026

## 模式判断

根据用户意图选择模式：

- **创建进化型 Skill**：用户提到"创建skill"、"建一个skill"、"创建进化型" → 加载 RULES.md §15 执行创建流程
- **触发进化 / 诊断**：用户提到"进化"、"evolve"、"/evolve"、"诊断" → 进入§触发进化
- **查看状态**：用户提到"进化状态"、"skill列表" → 运行 `python3 <protocol-dir>/scripts/evolution_engine.py list`
- **被其他 skill 引用**：其他 evolution skill 启动时加载本协议 → 读取 RULES.md

## 启动

读取本协议的详细规则：

```
Read: <workspace>/evolution-protocol/RULES.md
```

如果找不到，用 Glob 搜索 `**/evolution-protocol/RULES.md`。

**首次运行自动初始化**：如果 workspace 中不存在 `evolution-protocol/` 文件夹，则从本 .skill 安装包中复制 RULES.md、INDEX.md、SESSIONS.md、scripts/ 到 workspace 的 `evolution-protocol/` 目录下，然后正常启动。

## 触发进化

当用户说"进化"、"/evolve"、"诊断"时：

1. 运行 `python3 <protocol-dir>/scripts/evolution_engine.py list` 查看所有 Skill
2. 如果用户指定了 Skill 名称，运行：
   ```bash
   python3 <protocol-dir>/scripts/evolution_engine.py diagnose --skill <name>
   ```
3. 如果未指定，询问用户想诊断哪个 Skill
4. 向用户简洁汇报（≤5 行）：
   - 综合分 + 最低维度
   - 停滞维度（如有）
   - 具体改进建议
5. 如果用户同意改进建议，直接修改该 Skill 的 prompt

注意：`<protocol-dir>` 是本 evolution-protocol 文件夹的实际路径。

## 兜底规则（仅在 RULES.md 不可用时使用）

1. 每次对话先读目标 skill 的 INDEX.md（O(1) 恢复）
2. 对话结束前更新 INDEX.md 和 SESSIONS.md
3. md 文件超过 30 条记录或 200 行 → 裂变归档到 records/
4. 不要一次读取所有文件，按需读取
5. 不要删除任何文件，必须先获得用户确认
