"""Topic A bonus: stress projection QA with dropout and coordinate noise."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.exp_yaw_sweep import CLASSES, points_in_box
from starter.datasets import load_frame
from starter.perturb import gaussian_noise, random_dropout
from starter.projection import project_velo_to_image, velo_to_cam


def score(points: np.ndarray, calib, image_shape, bbox) -> tuple[int, int, int]:
    if not len(points):
        return 0, 0, 0
    uv, _, mask = project_velo_to_image(points, calib, image_shape)
    x1, y1, x2, y2 = bbox
    hits = int(((uv[:, 0] >= x1) & (uv[:, 0] <= x2)
                & (uv[:, 1] >= y1) & (uv[:, 1] <= y2)).sum())
    return hits, len(points), int(mask.sum())


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress projection QA with point dropout and Gaussian noise")
    parser.add_argument("--data-root", default="data/kitti_mini", help="Dataset directory")
    parser.add_argument("--frame", default="000011", help="One fixed frame for every condition")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for repeatable corruptions")
    parser.add_argument("--out", default="results/degradation_stress.csv", help="Output CSV path")
    args = parser.parse_args()

    fr = load_frame(args.data_root, args.frame)
    points = fr["points"]
    valid = np.isfinite(points).all(axis=1)
    points = points[valid]
    cam_true = velo_to_cam(points[:, :3], fr["calib"])
    objects = []
    for obj in fr["labels"]:
        if obj.type in CLASSES:
            mask = points_in_box(cam_true, obj)
            if mask.any():
                objects.append((points[mask], obj.bbox))
    if not objects:
        raise SystemExit("No labelled object points found")

    conditions = [("baseline", 0.0, lambda p: p)]
    conditions += [("random_dropout", r, lambda p, r=r: random_dropout(p, r, seed=args.seed))
                   for r in (0.7, 0.5, 0.3)]
    conditions += [("gaussian_noise", sigma, lambda p, sigma=sigma: gaussian_noise(p, sigma_xyz_m=sigma, seed=args.seed))
                   for sigma in (0.02, 0.05, 0.1)]

    rows = []
    for corruption, level, transform in conditions:
        hits = remaining = in_image = 0
        for object_points, bbox in objects:
            degraded = transform(object_points)
            n_hits, n_points, n_inside = score(degraded, fr["calib"], fr["image"].shape, bbox)
            hits += n_hits
            remaining += n_points
            in_image += n_inside
        rows.append({
            "dataset": Path(args.data_root).name,
            "frame": args.frame,
            "corruption": corruption,
            "level": level,
            "seed": args.seed if corruption != "baseline" else "",
            "objects": len(objects),
            "remaining_points": remaining,
            "object_points_in_image": in_image,
            "hits_in_2d_box": hits,
            "hit_ratio": round(hits / in_image, 4) if in_image else "",
        })
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    labels = ["Baseline", "Keep 70%", "Keep 50%", "Keep 30%", "Noise 0.02m", "Noise 0.05m", "Noise 0.10m"]
    ratios = [float(row["hit_ratio"]) * 100 for row in rows]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#555555"] + ["#2878b5"] * 3 + ["#e07a2d"] * 3
    ax.bar(labels, ratios, color=colors)
    ax.set_ylabel("Object points inside 2D box (%)")
    ax.set_ylim(0, 105)
    ax.set_title(f"Projection QA stress test · {args.frame}")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    figure = Path("results/figures/degradation_stress.png")
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=150)
    print(f"-> {out}")
    print(f"-> {figure}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
