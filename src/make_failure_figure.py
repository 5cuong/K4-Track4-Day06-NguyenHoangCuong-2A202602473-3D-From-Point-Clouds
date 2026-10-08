"""Create a reproducible side-by-side yaw calibration failure figure."""
from pathlib import Path

import cv2
import numpy as np

from src.exp_yaw_sweep import points_in_box
from starter.datasets import load_frame
from starter.projection import (
    draw_box2d,
    overlay_points,
    perturb_extrinsic,
    project_velo_to_image,
    velo_to_cam,
)


def _box_hit_ratio(uv: np.ndarray, selected: np.ndarray, bbox) -> tuple[int, int, float]:
    x1, y1, x2, y2 = bbox
    u, v = uv[selected, 0], uv[selected, 1]
    hits = int(((u >= x1) & (u <= x2) & (v >= y1) & (v <= y2)).sum())
    count = int(selected.sum())
    return hits, count, hits / count if count else float("nan")


def main() -> None:
    data_root, frame, yaw_deg = "data/kitti_mini", "000011", 2.0
    fr = load_frame(data_root, frame)
    points = fr["points"]
    finite = np.isfinite(points).all(axis=1)
    points = points[finite]
    cam_true = velo_to_cam(points[:, :3], fr["calib"])

    uv_base, depth_base, mask_base = project_velo_to_image(points, fr["calib"], fr["image"].shape)
    bad_calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw_deg)
    uv_bad, depth_bad, mask_bad = project_velo_to_image(points, bad_calib, fr["image"].shape)
    uv_base_all, uv_bad_all = np.full((len(points), 2), np.nan), np.full((len(points), 2), np.nan)
    uv_base_all[mask_base], uv_bad_all[mask_bad] = uv_base, uv_bad

    candidates = []
    for index, obj in enumerate(fr["labels"]):
        if obj.type != "Pedestrian":
            continue
        true_object_points = points_in_box(cam_true, obj)
        base_hits, base_count, base_ratio = _box_hit_ratio(
            uv_base_all, true_object_points & mask_base, obj.bbox
        )
        bad_hits, bad_count, bad_ratio = _box_hit_ratio(
            uv_bad_all, true_object_points & mask_bad, obj.bbox
        )
        if base_count:
            candidates.append((bad_ratio, index, obj, base_hits, base_count, base_ratio, bad_hits, bad_count))

    if not candidates:
        raise SystemExit(f"No visible pedestrian points in {frame}")
    _, object_index, target, base_hits, base_count, base_ratio, bad_hits, bad_count = min(candidates)

    baseline = overlay_points(fr["image"], uv_base, depth_base)
    failure = overlay_points(fr["image"], uv_bad, depth_bad)
    for obj in fr["labels"]:
        baseline = draw_box2d(baseline, obj.bbox, label=obj.type)
        failure = draw_box2d(failure, obj.bbox, label=obj.type)
    baseline = draw_box2d(baseline, target.bbox, color=(255, 0, 255), label=f"target {object_index}")
    failure = draw_box2d(failure, target.bbox, color=(0, 0, 255), label=f"target {object_index}")

    cv2.putText(baseline, "yaw error = 0 deg", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(failure, f"yaw error = {yaw_deg:g} deg", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    distance = float(np.hypot(target.location[0], target.location[2]))
    detail = (
        f"Pedestrian #{object_index}, {distance:.1f} m: "
        f"{base_hits}/{base_count} ({base_ratio:.1%}) -> {bad_hits}/{bad_count} ({bad_ratio:.1%})"
    )
    cv2.putText(baseline, detail, (20, baseline.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(failure, detail, (20, failure.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    combined = np.hstack([baseline, failure])
    out = Path("results/figures/fail_01_yaw_2deg_pedestrian.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out), combined):
        raise SystemExit(f"Could not write {out}")
    print(f"target={object_index} distance={distance:.1f}m {detail}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
