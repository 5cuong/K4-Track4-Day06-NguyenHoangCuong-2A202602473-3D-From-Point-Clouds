"""Build a compact PDF deck for the three-minute lab demo."""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages


ROOT = Path(".")
OUT = ROOT / "report/DAY06_DEMO.pdf"


def _page(title: str):
    fig = plt.figure(figsize=(13.33, 7.5), facecolor="white")
    fig.text(0.06, 0.91, title, fontsize=26, weight="bold", color="#132238")
    fig.text(0.06, 0.86, "K4 · Track 4 · Day 6 | 3D from Point Clouds", fontsize=12, color="#526579")
    return fig


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(OUT) as pdf:
        fig = _page("Calibration yaw shifts narrow objects out of their image boxes")
        fig.text(0.08, 0.70, "CLAIM", fontsize=13, weight="bold", color="#2463a5")
        fig.text(0.08, 0.61,
                 "On KITTI frame 000011, a 1° yaw error lowers the all-class hit ratio\n"
                 "from 99.45% to 77.44% (−22.01 percentage points).",
                 fontsize=20, color="#132238", linespacing=1.5)
        fig.text(0.08, 0.39, "DATA", fontsize=13, weight="bold", color="#2463a5")
        fig.text(0.08, 0.31,
                 "KITTI mini · frames 000008 (cars), 000011 (pedestrians), 000049 (occlusion)\n"
                 "Controlled variable: yaw error 0°, 0.5°, 1°, 2°, 3°.",
                 fontsize=16, color="#132238", linespacing=1.5)
        fig.text(0.08, 0.12, "Nguyen Hoang Cuong · 2A202602473", fontsize=12, color="#526579")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = _page("Evidence: pedestrians lose alignment faster than cars")
        ax = fig.add_axes([0.08, 0.10, 0.84, 0.72])
        ax.imshow(mpimg.imread(ROOT / "results/figures/yaw_sweep.png"))
        ax.axis("off")
        fig.text(0.08, 0.08,
                 "At 1°: frame 000011 overall = 77.44%; frame 000008 Car = 98.62%.",
                 fontsize=14, color="#132238")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = _page("Failure case: a 34.2 m pedestrian loses every in-box point")
        ax = fig.add_axes([0.04, 0.20, 0.92, 0.58])
        ax.imshow(mpimg.imread(ROOT / "results/figures/fail_01_yaw_2deg_pedestrian.png"))
        ax.axis("off")
        fig.text(0.08, 0.12,
                 "Frame 000011 · yaw 2° · target #3: 40/40 points (0°) → 0/40 points (2°).\n"
                 "Debug layer: Geometry — LiDAR-camera extrinsic is misaligned.",
                 fontsize=14, color="#132238", linespacing=1.5)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = _page("Deployment recommendation")
        fig.text(0.08, 0.72, "Use case", fontsize=13, weight="bold", color="#2463a5")
        fig.text(0.08, 0.65, "Urban delivery vehicle; validate alignment at startup and after impact or strong vibration.", fontsize=16)
        fig.text(0.08, 0.50, "Log", fontsize=13, weight="bold", color="#2463a5")
        fig.text(0.08, 0.43, "Camera/LiDAR hit ratio by class and distance, estimated yaw, and sensor-mount temperature.", fontsize=16)
        fig.text(0.08, 0.28, "Alert", fontsize=13, weight="bold", color="#2463a5")
        fig.text(0.08, 0.21, "Below 90% for three consecutive checks. Run while stopped to limit runtime cost; require visible objects.", fontsize=16)
        fig.text(0.08, 0.08, "Study limit: three selected KITTI frames; the threshold needs validation on the target vehicle and camera detector.", fontsize=11, color="#526579")
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
