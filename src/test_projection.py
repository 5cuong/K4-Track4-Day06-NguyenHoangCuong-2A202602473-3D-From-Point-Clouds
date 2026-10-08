"""Self-check for the two CP2 projection functions.

Run from the repository root with: python -m src.test_projection
"""
import numpy as np

from starter.datasets import load_frame
from starter.projection import cam_to_image, velo_to_cam


def main() -> None:
    np.set_printoptions(suppress=True, precision=2)
    fr = load_frame("data/synthetic", "000000")
    calib, shape = fr["calib"], fr["image"].shape
    pts = np.array([
        [10.0, 0.0, 0.0],
        [np.nan, 0.0, 0.0],
        [-10.0, 0.0, 0.0],
        [10.0, 50.0, 0.0],
    ])

    cam = velo_to_cam(pts, calib)
    uv, depth, mask = cam_to_image(cam, calib.P2, shape)
    print("camera frame:\n", np.round(cam, 2))
    print("uv:", np.round(uv, 1), " depth:", np.round(depth, 2), " mask:", mask)

    assert cam.shape == (4, 3), f"velo_to_cam must return (N, 3), got {cam.shape}"
    assert abs(cam[0, 2] - 9.73) < 0.01, f"expected z_cam ~= 9.73, got {cam[0, 2]}"
    assert mask.tolist() == [True, False, False, False], f"wrong mask: {mask}"
    assert uv.shape == (1, 2) and depth.shape == (1,), "wrong uv/depth shape"
    assert np.allclose(uv[0], [614, 175], atol=1), f"wrong pixel: {uv[0]}"
    print("CP2 self-test passed")


if __name__ == "__main__":
    main()
