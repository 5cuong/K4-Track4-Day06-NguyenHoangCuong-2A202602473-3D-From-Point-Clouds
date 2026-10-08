"""Plot class-wise LiDAR point retention from the yaw sweep CSV."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    df = pd.read_csv("results/yaw_perturb_sweep.csv", dtype={"frame": str})
    summary = (
        df.dropna(subset=["hit_ratio"])
        .groupby(["yaw_deg", "class"], as_index=False)
        .apply(lambda group: pd.Series({
            "hits": group["hits"].sum(),
            "object_points": group["object_points"].sum(),
        }))
    )
    summary["hit_ratio"] = summary["hits"] / summary["object_points"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for object_class, group in summary.groupby("class"):
        group = group.sort_values("yaw_deg")
        ax.plot(group["yaw_deg"], 100 * group["hit_ratio"], marker="o", label=object_class)
    ax.set_xlabel("Yaw error (degrees)")
    ax.set_ylabel("Object LiDAR points inside 2D box (%)")
    ax.set_ylim(0, 105)
    ax.set_title("LiDAR-to-camera projection sensitivity by class")
    ax.grid(alpha=0.3)
    ax.legend(title="KITTI class")
    fig.tight_layout()

    out = Path("results/figures/yaw_sweep.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"-> {out}")


if __name__ == "__main__":
    main()
