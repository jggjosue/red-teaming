"""Command-line entry point.

Examples:
  python run.py plant   --attacker anthropic:claude-opus-5-5 --out results/run1
  python run.py review  --reviewer anthropic:claude-opus-5-5 --out results/run1
  python run.py review  --reviewer openai:gpt-5 --out results/run1
  python run.py analyze --out results/run1
"""

import argparse
from pathlib import Path

from pbw import experiment


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("plant", help="ask a model to plant subtle bugs")
    a.add_argument("--attacker", required=True)

    r = sub.add_parser("review", help="ask a model to review clean and buggy code")
    r.add_argument("--reviewer", required=True)
    r.add_argument("--conditions", default="code_only,with_tests")

    sub.add_parser("analyze", help="summarize results")

    for s in (a, r):
        s.add_argument("--workers", type=int, default=4)
    for s in sub.choices.values():
        s.add_argument("--out", type=Path, required=True)

    args = p.parse_args()
    if args.cmd == "plant":
        rows = experiment.plant(args.attacker, args.out, args.workers)
        print(f"valid bugs: {sum(r['valid'] for r in rows)}/{len(rows)}")
    elif args.cmd == "review":
        rows = experiment.review(args.reviewer, args.out, args.conditions.split(","), args.workers)
        print(f"reviews: {len(rows)}")
    print(experiment.analyze(args.out))


if __name__ == "__main__":
    main()
