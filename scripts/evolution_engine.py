#!/usr/bin/env python3
"""
evolution_engine.py — Evolution Protocol 进化引擎
===================================================

为所有进化型 Skill 提供自动化评分追踪、停滞检测、权重进化。
纯 Python 标准库，无第三方依赖。

用法:
    python3 scripts/evolution_engine.py create my-skill \
        --dimensions '{"accuracy":{"name":"准确度","weight":0.3},"insight":{"name":"洞察","weight":0.7}}'
    python3 scripts/evolution_engine.py list
    python3 scripts/evolution_engine.py state --skill my-skill
    python3 scripts/evolution_engine.py update --skill my-skill --scores "accuracy:3.5,insight:4.0"
    python3 scripts/evolution_engine.py diagnose --skill my-skill
    python3 scripts/evolution_engine.py bootstrap --skill my-skill

核心公式:
    composite = Σ(wᵢ × sᵢ)
    threshold(N) = round(20 × N^1.5)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# 常量
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / "data" / "skills"

# 奖励信号等级
REWARD_VALUES = {"S": 30, "A": 20, "B": 5, "C": 2, "D": -10}

# 进化参数
STAGNANT_THRESHOLD = 3
HIGH_SCORE_STREAK_THRESHOLD = 5
WEIGHT_TRANSFER_AMOUNT = 0.05
MINIMUM_WEIGHT = 0.05


# ============================================================
# Skill Context
# ============================================================

class SkillContext:
    """封装一个 Skill 的维度、权重、路径信息"""

    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        skill_dir = SKILLS_DIR / skill_name
        config_file = skill_dir / "config.json"

        if not config_file.exists():
            print(f"错误: Skill '{skill_name}' 不存在 → {config_file}", file=sys.stderr)
            print(f"提示: 先运行 create 命令创建", file=sys.stderr)
            sys.exit(1)

        with open(config_file, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.dim_keys = list(self.config["dimensions"].keys())
        self.default_weights = {
            k: v["weight"] for k, v in self.config["dimensions"].items()
        }
        self.dimensions = {
            k: {"name": v["name"], "symbol": v.get("symbol", k[:1].upper())}
            for k, v in self.config["dimensions"].items()
        }
        self.state_file = skill_dir / "state.json"
        self.scores_log = skill_dir / "scores.log"
        self.capability_map = self.config.get("capability_map", {})

    def load_state(self) -> dict:
        if not self.state_file.exists():
            print(f"错误: 状态文件不存在 → {self.state_file}", file=sys.stderr)
            print("提示: 请先运行 bootstrap 初始化", file=sys.stderr)
            sys.exit(1)
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_state(self, state: dict) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def append_score_log(self, snapshot: dict, note: str = "") -> None:
        self.scores_log.parent.mkdir(parents=True, exist_ok=True)
        is_new = not self.scores_log.exists()
        with open(self.scores_log, "a", encoding="utf-8") as f:
            if is_new:
                header = "date\t" + "\t".join(self.dim_keys) + "\tcomposite\tnote\n"
                f.write(header)
            scores = [f"{snapshot[k]:.1f}" for k in self.dim_keys]
            composite = sum(self.default_weights[k] * snapshot[k] for k in self.dim_keys)
            line = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\t"
            line += "\t".join(scores) + f"\t{composite:.2f}\t{note}\n"
            f.write(line)


# ============================================================
# 通用工具
# ============================================================

def threshold(level: int) -> int:
    if level <= 0:
        return 0
    return round(20 * (level ** 1.5))


def compute_composite(weights: dict, snapshot: dict, dim_keys: list) -> float:
    return sum(weights[k] * snapshot[k] for k in dim_keys)


def find_lowest_dim(snapshot: dict, dim_keys: list) -> str:
    return min(dim_keys, key=lambda k: snapshot[k])


def parse_scores(scores_str: str) -> dict:
    """解析 "accuracy:3.5,insight:4.0" 格式"""
    if not scores_str:
        return {}
    result = {}
    for token in scores_str.split(","):
        token = token.strip()
        if not token:
            continue
        parts = token.split(":")
        if len(parts) != 2:
            print(f"警告: 无法解析 '{token}'，跳过", file=sys.stderr)
            continue
        dim_key = parts[0].strip()
        try:
            score = float(parts[1].strip())
        except ValueError:
            print(f"警告: '{parts[1]}' 不是有效分数，跳过", file=sys.stderr)
            continue
        result[dim_key] = score
    return result


# ============================================================
# 命令: create
# ============================================================

SELF_EVAL_TEMPLATE = """
## 收尾自评（每次执行完自动运行）

完成任务后，自动执行以下评分流程：

1. 对本次产出按以下维度自评 1-5 分：
{dim_list}

   评分锚点：
   - 1.0 = 完全不可用，需要重做
   - 2.0 = 勉强可用，需大改
   - 3.0 = 基本合格，需中等修改
   - 4.0 = 良好，只需微调
   - 5.0 = 完美，直接可用

2. 运行评分记录：
   ```
   python3 {engine_path} update --skill {skill_name} \\
       --scores "{score_template}"
   ```

3. 如果任一维度比上次下降 >= 1 分，提醒用户。

4. 每 5 次使用后，运行诊断：
   ```
   python3 {engine_path} diagnose --skill {skill_name}
   ```
   向用户简洁汇报停滞维度和改进建议。
""".strip()


def cmd_create(args: argparse.Namespace) -> None:
    skill_name = args.name
    skill_dir = SKILLS_DIR / skill_name

    if skill_dir.exists():
        print(f"错误: Skill '{skill_name}' 已存在 → {skill_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        dimensions = json.loads(args.dimensions)
    except json.JSONDecodeError as e:
        print(f"错误: --dimensions JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    total_weight = sum(v["weight"] for v in dimensions.values())
    if abs(total_weight - 1.0) > 0.01:
        print(f"警告: 权重之和 = {total_weight:.2f}，建议调整为 1.0", file=sys.stderr)

    config = {
        "name": skill_name,
        "description": args.description or "",
        "dimensions": dimensions,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "capability_map": {},
    }

    skill_dir.mkdir(parents=True, exist_ok=True)
    config_file = skill_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")

    dim_keys = list(dimensions.keys())
    state = {
        "dimensions": {
            k: {"name": v["name"], "symbol": v.get("symbol", k[:1].upper())}
            for k, v in dimensions.items()
        },
        "weights": {k: v["weight"] for k, v in dimensions.items()},
        "snapshot": {k: 2.0 for k in dim_keys},
        "progress": {
            k: {"cumulative": 0, "max_cumulative": 0, "level": 0}
            for k in dim_keys
        },
        "stagnant_counts": {k: 0 for k in dim_keys},
        "high_score_streaks": {k: 0 for k in dim_keys},
        "session_count": 0,
    }
    state_file = skill_dir / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 生成收尾自评模板
    # 使用绝对路径，同时提供占位符说明，方便分享后修改
    engine_path = str(Path(__file__).resolve())
    engine_path_note = f"# 注意：如果文件夹被移动，请将下方路径替换为 evolution_engine.py 的实际位置\n   # 当前路径: {engine_path}"
    dim_list_lines = []
    for k, v in dimensions.items():
        dim_list_lines.append(f"   - **{v['name']}** ({k}): 权重 {v['weight']}")
    dim_list = "\n".join(dim_list_lines)
    score_template = ",".join(f"{k}:X.X" for k in dim_keys)

    self_eval = SELF_EVAL_TEMPLATE.format(
        dim_list=dim_list,
        skill_name=skill_name,
        score_template=score_template,
        engine_path=engine_path,
    )

    output = {
        "skill_name": skill_name,
        "directory": str(skill_dir),
        "dimensions": {k: f"{v['name']} (w={v['weight']})" for k, v in dimensions.items()},
        "files_created": [str(config_file), str(state_file)],
        "self_eval_template": self_eval,
        "message": f"Skill '{skill_name}' 创建成功。将上方 self_eval_template 粘贴到该 Skill 的 RULES.md 末尾即可启用自动进化。",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================
# 命令: list
# ============================================================

def cmd_list(args: argparse.Namespace) -> None:
    skills = []

    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            config_file = skill_dir / "config.json"
            if not config_file.exists():
                continue
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            dim_keys = list(config["dimensions"].keys())
            composite = 0.0
            sessions = 0
            state_file = skill_dir / "state.json"
            if state_file.exists():
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                weights = {k: v["weight"] for k, v in config["dimensions"].items()}
                composite = compute_composite(weights, state["snapshot"], dim_keys)
                sessions = state.get("session_count", 0)

            skills.append({
                "name": skill_dir.name,
                "description": config.get("description", ""),
                "dimensions": len(dim_keys),
                "dim_names": [v["name"] for v in config["dimensions"].values()],
                "composite": round(composite, 2),
                "sessions": sessions,
                "created_at": config.get("created_at", ""),
            })

    if not skills:
        print("暂无 Skill。运行 create 命令创建第一个。")
        return

    print(json.dumps({"skills": skills}, ensure_ascii=False, indent=2))


# ============================================================
# 命令: state
# ============================================================

def cmd_state(args: argparse.Namespace) -> None:
    ctx = SkillContext(args.skill)
    state = ctx.load_state()
    snapshot = state["snapshot"]
    weights = state["weights"]
    progress = state["progress"]
    stagnant_counts = state.get("stagnant_counts", {k: 0 for k in ctx.dim_keys})

    composite = compute_composite(weights, snapshot, ctx.dim_keys)
    lowest = find_lowest_dim(snapshot, ctx.dim_keys)
    stagnant_dims = [k for k in ctx.dim_keys if stagnant_counts.get(k, 0) >= STAGNANT_THRESHOLD]

    output = {
        "skill": ctx.skill_name,
        "snapshot": snapshot,
        "progress": progress,
        "weights": weights,
        "composite": round(composite, 4),
        "lowest_dim": lowest,
        "stagnant": stagnant_dims,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================
# 命令: update
# ============================================================

def cmd_update(args: argparse.Namespace) -> None:
    ctx = SkillContext(args.skill)
    state = ctx.load_state()

    old_snapshot = dict(state["snapshot"])
    old_composite = compute_composite(state["weights"], old_snapshot, ctx.dim_keys)

    # 1. 解析新分数
    new_scores = parse_scores(args.scores) if args.scores else {}
    if not new_scores:
        print("警告: 没有提供任何分数更新", file=sys.stderr)
        return

    # 2. 应用分数 + 计算变化量
    deltas = {}
    for key in ctx.dim_keys:
        if key in new_scores:
            deltas[key] = round(new_scores[key] - old_snapshot.get(key, 2.0), 4)
            state["snapshot"][key] = new_scores[key]

    # 3. 停滞计数
    stagnant_counts = state.get("stagnant_counts", {k: 0 for k in ctx.dim_keys})
    for key in ctx.dim_keys:
        if key in new_scores:
            if new_scores[key] == old_snapshot.get(key, 2.0):
                stagnant_counts[key] = stagnant_counts.get(key, 0) + 1
            else:
                stagnant_counts[key] = 0
    state["stagnant_counts"] = stagnant_counts

    # 4. 高分连续记录
    high_score_streaks = state.get("high_score_streaks", {k: 0 for k in ctx.dim_keys})
    for key in ctx.dim_keys:
        if state["snapshot"].get(key, 0) >= 4.0:
            high_score_streaks[key] = high_score_streaks.get(key, 0) + 1
        else:
            high_score_streaks[key] = 0
    state["high_score_streaks"] = high_score_streaks

    # 5. 快照分变化 → 累积分
    for key in ctx.dim_keys:
        if key in deltas and deltas[key] != 0:
            score_reward = round(deltas[key] * 20)
            state["progress"][key]["cumulative"] += score_reward
            if state["progress"][key]["cumulative"] < 0:
                state["progress"][key]["cumulative"] = 0
            if state["progress"][key]["cumulative"] > state["progress"][key]["max_cumulative"]:
                state["progress"][key]["max_cumulative"] = state["progress"][key]["cumulative"]

    # 6. 重算等级
    level_ups = {}
    for key in ctx.dim_keys:
        progress = state["progress"][key]
        old_level = progress["level"]
        while True:
            next_threshold = threshold(progress["level"] + 1)
            if progress["cumulative"] >= next_threshold:
                progress["level"] += 1
            else:
                break
        if progress["level"] > old_level:
            level_ups[key] = {"from": old_level, "to": progress["level"]}

    # 7. 权重进化
    for key in ctx.dim_keys:
        if high_score_streaks.get(key, 0) >= HIGH_SCORE_STREAK_THRESHOLD:
            current_weight = state["weights"][key]
            if current_weight > MINIMUM_WEIGHT + 0.001:
                lowest_dim = find_lowest_dim(state["snapshot"], ctx.dim_keys)
                if lowest_dim != key:
                    transfer = min(WEIGHT_TRANSFER_AMOUNT, current_weight - MINIMUM_WEIGHT)
                    state["weights"][key] = round(state["weights"][key] - transfer, 4)
                    state["weights"][lowest_dim] = round(state["weights"][lowest_dim] + transfer, 4)
                    high_score_streaks[key] = 0
                    state["high_score_streaks"] = high_score_streaks

    # 8. 会话计数
    state["session_count"] = state.get("session_count", 0) + 1

    # 9. 保存
    ctx.save_state(state)

    # 10. scores.log
    note = args.note or ""
    ctx.append_score_log(state["snapshot"], note)

    # 11. 退步检测
    regressions = []
    for key, delta in deltas.items():
        if delta <= -1.0:
            dim_name = state["dimensions"].get(key, {}).get("name", key)
            regressions.append(f"⚠️ {dim_name} 下降 {abs(delta):.1f} 分!")

    # 12. 停滞维度
    stagnant_dims = [k for k in ctx.dim_keys if stagnant_counts.get(k, 0) >= STAGNANT_THRESHOLD]

    # 13. 输出
    new_composite = compute_composite(state["weights"], state["snapshot"], ctx.dim_keys)
    output = {
        "skill": ctx.skill_name,
        "old_composite": round(old_composite, 4),
        "new_composite": round(new_composite, 4),
        "deltas": deltas,
        "level_ups": level_ups,
        "stagnant_dims": stagnant_dims,
        "regressions": regressions,
        "session_count": state["session_count"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================
# 命令: bootstrap
# ============================================================

def cmd_bootstrap(args: argparse.Namespace) -> None:
    ctx = SkillContext(args.skill)

    if not ctx.state_file.exists():
        print("状态文件不存在，创建默认初始状态...", file=sys.stderr)
        state = {
            "dimensions": dict(ctx.dimensions),
            "weights": dict(ctx.default_weights),
            "snapshot": {k: 2.0 for k in ctx.dim_keys},
            "progress": {
                k: {"cumulative": 0, "max_cumulative": 0, "level": 0}
                for k in ctx.dim_keys
            },
            "stagnant_counts": {k: 0 for k in ctx.dim_keys},
            "high_score_streaks": {k: 0 for k in ctx.dim_keys},
            "session_count": 0,
        }
        ctx.save_state(state)

    state = ctx.load_state()
    snapshot = state["snapshot"]

    for key in ctx.dim_keys:
        score = snapshot[key]
        boot_level = round(10 * (score - 1))
        if boot_level < 0:
            boot_level = 0
        boot_cumulative = threshold(boot_level)
        state["progress"][key] = {
            "cumulative": boot_cumulative,
            "max_cumulative": boot_cumulative,
            "level": boot_level,
        }

    state["stagnant_counts"] = {k: 0 for k in ctx.dim_keys}
    state["high_score_streaks"] = {k: 0 for k in ctx.dim_keys}
    ctx.save_state(state)

    result = {}
    for key in ctx.dim_keys:
        p = state["progress"][key]
        result[key] = {
            "snapshot": snapshot[key],
            "level": p["level"],
            "cumulative": p["cumulative"],
            "next_threshold": threshold(p["level"] + 1),
        }

    composite = compute_composite(state["weights"], snapshot, ctx.dim_keys)
    output = {
        "skill": ctx.skill_name,
        "bootstrapped": result,
        "composite": round(composite, 4),
        "message": "进度系统已从快照分初始化完成",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================
# 命令: diagnose
# ============================================================

def cmd_diagnose(args: argparse.Namespace) -> None:
    ctx = SkillContext(args.skill)
    state = ctx.load_state()
    snapshot = state["snapshot"]
    stagnant_counts = state.get("stagnant_counts", {k: 0 for k in ctx.dim_keys})

    stagnant_dims = [k for k in ctx.dim_keys if stagnant_counts.get(k, 0) >= STAGNANT_THRESHOLD]
    lowest_dim = find_lowest_dim(snapshot, ctx.dim_keys)
    composite = compute_composite(state["weights"], snapshot, ctx.dim_keys)
    focus_dims = list(set(stagnant_dims + [lowest_dim]))

    recommendations = []
    for dim in focus_dims:
        dim_info = state["dimensions"].get(dim, {"symbol": dim[:1].upper(), "name": dim})
        dim_name = f"{dim_info.get('symbol', '')} {dim_info['name']}"
        dim_score = snapshot[dim]
        is_stagnant = dim in stagnant_dims
        stagnant_count = stagnant_counts.get(dim, 0)

        # 查能力地图
        relevant_modules = []
        for module_path, module_info in ctx.capability_map.items():
            if dim in module_info.get("primary", []):
                relevant_modules.append({
                    "path": module_path, "name": module_info["name"],
                    "status": module_info.get("status", "not_built"),
                    "relation": "primary",
                })
            elif dim in module_info.get("secondary", []):
                relevant_modules.append({
                    "path": module_path, "name": module_info["name"],
                    "status": module_info.get("status", "not_built"),
                    "relation": "secondary",
                })

        suggestions = []
        if not relevant_modules:
            if is_stagnant:
                suggestions.append(
                    f"{dim_name} 已停滞 {stagnant_count} 次 — "
                    f"建议检查 prompt 中与该维度相关的指令，或添加更多参考样本"
                )
            else:
                suggestions.append(
                    f"{dim_name} 当前最低 ({dim_score:.1f}) — "
                    f"建议在 prompt 中加强该维度的具体指令"
                )
        else:
            for mod in relevant_modules:
                if mod["status"] == "not_built":
                    suggestions.append(f"构建 {mod['path']} ({mod['name']}) MVP — 这是提升 {dim_name} 的关键瓶颈")
                elif mod["status"] == "mvp":
                    suggestions.append(f"优化 {mod['path']} ({mod['name']}) — 模块已有 MVP，但 {dim_name} 仍未提升")
                elif mod["status"] == "ready" and is_stagnant:
                    suggestions.append(f"{mod['path']} ({mod['name']}) 已就绪但 {dim_name} 停滞 — 问题可能不在这个模块")

        recommendations.append({
            "dimension": dim, "display_name": dim_name, "score": dim_score,
            "is_stagnant": is_stagnant, "stagnant_sessions": stagnant_count,
            "relevant_modules": relevant_modules, "suggestions": suggestions,
        })

    recommendations.sort(key=lambda r: (not r["is_stagnant"], r["score"]))

    output = {
        "skill": ctx.skill_name,
        "composite": round(composite, 4),
        "focus_dimensions": focus_dims,
        "recommendations": recommendations,
        "next_action": (
            recommendations[0]["suggestions"][0]
            if recommendations and recommendations[0]["suggestions"]
            else "所有维度正常，继续当前路线"
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Evolution Protocol 进化引擎 — 多 Skill 评分追踪与停滞检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/evolution_engine.py create my-skill \\
      --dimensions '{"dim1":{"name":"维度1","weight":0.5},"dim2":{"name":"维度2","weight":0.5}}'

  python3 scripts/evolution_engine.py list
  python3 scripts/evolution_engine.py state --skill my-skill
  python3 scripts/evolution_engine.py update --skill my-skill --scores "dim1:3.5,dim2:4.0"
  python3 scripts/evolution_engine.py diagnose --skill my-skill
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # create
    create_parser = subparsers.add_parser("create", help="创建新 Skill Profile")
    create_parser.add_argument("name", help="Skill 名称（英文 kebab-case）")
    create_parser.add_argument("--dimensions", required=True, help='维度定义 JSON')
    create_parser.add_argument("--description", default="", help="Skill 描述")

    # list
    subparsers.add_parser("list", help="列出所有 Skill")

    # state
    state_parser = subparsers.add_parser("state", help="显示 Skill 状态")
    state_parser.add_argument("--skill", required=True, help="Skill 名称")

    # update
    update_parser = subparsers.add_parser("update", help="更新评分")
    update_parser.add_argument("--skill", required=True, help="Skill 名称")
    update_parser.add_argument("--scores", required=True, help='评分: "dim1:3.5,dim2:4.0"')
    update_parser.add_argument("--note", default="", help="备注")

    # bootstrap
    bootstrap_parser = subparsers.add_parser("bootstrap", help="初始化进度系统")
    bootstrap_parser.add_argument("--skill", required=True, help="Skill 名称")

    # diagnose
    diagnose_parser = subparsers.add_parser("diagnose", help="诊断停滞维度")
    diagnose_parser.add_argument("--skill", required=True, help="Skill 名称")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "create": cmd_create,
        "list": cmd_list,
        "state": cmd_state,
        "update": cmd_update,
        "bootstrap": cmd_bootstrap,
        "diagnose": cmd_diagnose,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
