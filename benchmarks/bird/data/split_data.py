#!/usr/bin/env python3
"""BIRD 数据分割 —— 每个数据库内部 50/50 分层分割。

原则：
- 每个 db_id 独立分割
- 按 difficulty 分层（simple / moderate / challenging）
- seed=42 保证可复现
- train 问题的 SQL 和 evidence 字段剥离（Builder 不可见）
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_dataset_config


def split_data(input_file: str, output_dir: str, seed: int = 42,
               train_ratio: float = 0.5):
    """执行分层分割（按 difficulty 在每个 DB 内部独立 50/50）。"""
    random.seed(seed)

    with open(input_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # 按 db_id 分组
    by_db = defaultdict(list)
    for q in questions:
        by_db[q["db_id"]].append(q)

    output_path = Path(output_dir)
    train_dir = output_path / "train"
    test_dir = output_path / "test"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "seed": seed,
        "train_ratio": train_ratio,
        "total_questions": len(questions),
        "total_databases": len(by_db),
        "databases": {},
    }

    train_total = 0
    test_total = 0

    for db_id in sorted(by_db.keys()):
        db_questions = by_db[db_id]

        # 按 difficulty 分组
        by_diff = defaultdict(list)
        for q in db_questions:
            by_diff[q["difficulty"]].append(q)

        train_qs = []
        test_qs = []
        diff_report = {}

        for difficulty in ["simple", "moderate", "challenging"]:
            qs = by_diff.get(difficulty, [])
            if not qs:
                continue

            random.shuffle(qs)
            n_train = max(1, round(len(qs) * train_ratio))
            # 当只有 1 题时，随机分配到 train 或 test
            if len(qs) == 1:
                if random.random() < train_ratio:
                    n_train = 1
                else:
                    n_train = 0

            train_split = qs[:n_train]
            test_split = qs[n_train:]

            train_qs.extend(train_split)
            test_qs.extend(test_split)

            diff_report[f"train_{difficulty}"] = len(train_split)
            diff_report[f"test_{difficulty}"] = len(test_split)

        # 剥离 train 问题的 SQL 和 evidence
        train_clean = []
        for q in train_qs:
            train_clean.append({
                "question_id": q["question_id"],
                "db_id": q["db_id"],
                "question": q["question"],
                "difficulty": q["difficulty"],
            })
        # test 保留所有字段（评估需要 gold SQL）
        test_clean = [{k: v for k, v in q.items()} for q in test_qs]

        # 写入文件
        train_file = train_dir / f"{db_id}.json"
        test_file = test_dir / f"{db_id}.json"

        with open(train_file, "w", encoding="utf-8") as f:
            json.dump({
                "db_id": db_id,
                "count": len(train_clean),
                "questions": train_clean,
            }, f, ensure_ascii=False, indent=2)

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({
                "db_id": db_id,
                "count": len(test_clean),
                "questions": test_clean,
            }, f, ensure_ascii=False, indent=2)

        report["databases"][db_id] = {
            "total": len(db_questions),
            "train": len(train_clean),
            "test": len(test_clean),
            **diff_report,
        }
        train_total += len(train_clean)
        test_total += len(test_clean)

        print(f"  {db_id}: {len(train_clean)} train / {len(test_clean)} test "
              f"(total: {len(db_questions)})")

    report["train_total"] = train_total
    report["test_total"] = test_total

    # 写分割报告
    report_file = output_path / "split_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n分割完成: {train_total} train / {test_total} test")
    print(f"报告: {report_file}")

    # 验证
    print(f"\n验证:")
    print(f"  - 总数据库数: {len(report['databases'])}")
    print(f"  - train+test == total: "
          f"{train_total + test_total == len(questions)}")
    for db_id, info in report["databases"].items():
        if info["total"] < 10:
            print(f"  ⚠ {db_id}: 仅 {info['total']} 题（小样本）")


def main():
    parser = argparse.ArgumentParser(description="BIRD 数据分层分割")
    parser.add_argument("--dataset", default="minidev",
                        choices=["minidev", "dev"],
                        help="数据集选择 (minidev=500题, dev=1534题)")
    parser.add_argument("--input", default="",
                        help="覆盖默认的 questions JSON 路径")
    parser.add_argument("--output", default="",
                        help="覆盖默认的输出目录")
    parser.add_argument("--seed", type=int, default=42,
                        help="随机种子（默认 42）")
    parser.add_argument("--train-ratio", type=float, default=0.5,
                        help="训练集比例（默认 0.5）")
    args = parser.parse_args()

    ds = get_dataset_config(args.dataset)
    input_file = args.input or str(ds["questions"])
    output_dir = args.output or str(ds["train_dir"].parent)

    print(f"数据集: {args.dataset}")
    print(f"输入: {input_file}")
    print(f"输出: {output_dir}")
    print(f"Seed: {args.seed}\n")

    split_data(input_file, output_dir, args.seed, args.train_ratio)


if __name__ == "__main__":
    main()
