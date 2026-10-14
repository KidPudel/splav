import numpy as np


def offset(c, d):
    """Move a contour's points d units outward from the ink."""
    if not d:
        return c
    t = np.roll(c, -1, 0) - np.roll(c, 1, 0)
    t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    return c + np.stack([t[:, 1], -t[:, 0]], 1) * d
