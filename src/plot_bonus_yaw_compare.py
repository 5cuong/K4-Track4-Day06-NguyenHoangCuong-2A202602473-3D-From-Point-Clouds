"""Compare the same yaw sweep across KITTI and nuScenes."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    kitti = pd.read_csv("results/bonus_kitti_yaw.csv")
    nusc = pd.read_csv("results/bonus_nusc_yaw.csv")
    kitti["dataset"] = "KITTI (64-beam)"
    nusc["dataset"] = "nuScenes (32-beam)"
    df = pd.concat([kitti, nusc], ignore_index=True).dropna(subset=["hit_ratio"])
    summary = df.groupby(["dataset", "yaw_deg"], as_index=False)[["hits", "object_points"]].sum()
    summary["hit_ratio"] = summary["hits"] / summary["object_points"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for dataset, group in summary.groupby("dataset"):
        group = group.sort_values("yaw_deg")
        ax.plot(group["yaw_deg"], 100 * group["hit_ratio"], marker="o", label=dataset)
    ax.set_xlabel("Yaw error (degrees)")
    ax.set_ylabel("Object LiDAR points inside 2D box (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Same yaw sweep across two real datasets")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out = Path("results/figures/bonus_yaw_dataset_compare.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
