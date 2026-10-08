"""Topic A experiment: yaw error versus LiDAR points retained by 2D boxes.

Run from the repository root, for example:
    python -m src.exp_yaw_sweep --data-root data/kitti_mini \
        --frames 000008 000011 000049

The Codelab sweep is extended with class and distance buckets.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from starter.datasets import load_frame
from starter.projection import perturb_extrinsic, project_velo_to_image, velo_to_cam

CLASSES = ("Car", "Van", "Pedestrian", "Cyclist")


def points_in_box(points_cam: np.ndarray, obj) -> np.ndarray:
    """Return a mask for points inside a KITTI 3D box in camera coordinates."""
    h, w, l = obj.dimensions
    c, s = np.cos(obj.rotation_y), np.sin(obj.rotation_y)
    rotation = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    local = (points_cam - obj.location) @ rotation
    return (
        (np.abs(local[:, 0]) <= l / 2)
        & (local[:, 1] <= 0)
        & (local[:, 1] >= -h)
        & (np.abs(local[:, 2]) <= w / 2)
    )


def distance_bucket(distance_m: float) -> str:
    if distance_m < 15:
        return "0-15m"
    if distance_m < 30:
        return "15-30m"
    return ">30m"


def run_one(frame: str, data_root: str, yaw_deg: float) -> list[dict]:
    fr = load_frame(data_root, frame)
    points = fr["points"]
    valid = np.isfinite(points).all(axis=1)
    points = points[valid]
    cam_true = velo_to_cam(points[:, :3], fr["calib"])

    perturbed = perturb_extrinsic(fr["calib"], yaw_deg=yaw_deg)
    uv, _, mask = project_velo_to_image(points, perturbed, fr["image"].shape)
    uv_all = np.full((len(points), 2), np.nan)
    uv_all[mask] = uv

    groups: dict[tuple[str, str], dict[str, int]] = {}
    for obj in fr["labels"]:
        if obj.type not in CLASSES:
            continue
        distance_m = float(np.hypot(obj.location[0], obj.location[2]))
        bucket = distance_bucket(distance_m)
        key = (obj.type, bucket)
        group = groups.setdefault(key, {"object_points": 0, "hits": 0})

        # Match the lab metric: assess points that project into the image, then
        # count which of those land inside the object's annotated 2D rectangle.
        selected = points_in_box(cam_true, obj) & mask
        x1, y1, x2, y2 = obj.bbox
        u, v = uv_all[selected, 0], uv_all[selected, 1]
        group["hits"] += int(((u >= x1) & (u <= x2) & (v >= y1) & (v <= y2)).sum())
        group["object_points"] += int(selected.sum())

    rows = []
    for (object_class, bucket), group in sorted(groups.items()):
        n_obj = group["object_points"]
        rows.append({
            "dataset": Path(data_root).name,
            "frame": frame,
            "yaw_deg": yaw_deg,
            "class": object_class,
            "distance_bucket": bucket,
            "n_points": len(points),
            "inside_image": int(mask.sum()),
            "object_points": n_obj,
            "hits": group["hits"],
            "hit_ratio": round(group["hits"] / n_obj, 4) if n_obj else "",
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure KITTI LiDAR-to-2D-box hit ratio under yaw error")
    parser.add_argument("--data-root", default="data/kitti_mini", help="KITTI dataset directory")
    parser.add_argument("--frames", nargs="+", default=["000008", "000011", "000049"], help="Frame IDs")
    parser.add_argument("--yaw-levels", nargs="+", type=float, default=[0, 0.5, 1, 2, 3], help="Yaw errors in degrees")
    parser.add_argument("--out", default="results/yaw_perturb_sweep.csv", help="Output CSV path")
    args = parser.parse_args()

    rows = []
    for frame in args.frames:
        for yaw in args.yaw_levels:
            frame_rows = run_one(frame, args.data_root, yaw)
            rows.extend(frame_rows)
            for row in frame_rows:
                print(row)

    if not rows:
        raise SystemExit("No labelled object points found for the selected frames")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"-> {out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
