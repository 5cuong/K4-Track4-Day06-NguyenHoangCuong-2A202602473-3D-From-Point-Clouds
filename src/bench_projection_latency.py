"""Topic A bonus: measure projection latency after excluding warm-up run."""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np

from starter.datasets import load_frame
from starter.projection import project_velo_to_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark LiDAR-camera projection latency")
    parser.add_argument("--data-root", default="data/kitti_mini", help="Dataset directory")
    parser.add_argument("--frame", default="000011", help="Frame to time")
    parser.add_argument("--runs", type=int, default=21, help="Number of runs including one warm-up (minimum 21)")
    parser.add_argument("--out", default="results/latency_projection.csv", help="Per-run CSV path")
    args = parser.parse_args()
    if args.runs < 21:
        parser.error("--runs must be at least 21 so p50/p95 use at least 20 measured runs")

    fr = load_frame(args.data_root, args.frame)
    rows = []
    for run in range(1, args.runs + 1):
        start = time.perf_counter()
        _, _, mask = project_velo_to_image(fr["points"], fr["calib"], fr["image"].shape)
        elapsed_ms = (time.perf_counter() - start) * 1000
        rows.append({
            "dataset": Path(args.data_root).name,
            "frame": args.frame,
            "run": run,
            "warmup": run == 1,
            "elapsed_ms": round(elapsed_ms, 4),
            "n_points": len(mask),
            "inside_image": int(mask.sum()),
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    measured = np.array([row["elapsed_ms"] for row in rows[1:]])
    print(f"p50={np.percentile(measured, 50):.2f} ms p95={np.percentile(measured, 95):.2f} ms n={len(measured)}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
