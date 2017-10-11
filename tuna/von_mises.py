"""
Fast two-peak von Mises fit
"""
__author__ = "Dimitri Yatsenko"

"""
Fast two-peak von Mises fit
"""
__author__ = "Dimitri Yatsenko"

import numpy as np

# by "width", we really mean "sharpness" with higher values corresponding to narrower peaks.
nwidths = 64  # make a power of two
max_width = 30.0
widths = np.logspace(0, 1, nwidths, base=max_width)


def g(c, w):
    """ von Mises peak """
    return np.exp(-w * (1 - c))


def von_mises2(phi, a0, a1, a2, theta, w, **kwargs):
    """ two-peak von Mises """
    c = np.cos(phi - theta)
    return a0 + a1 * g(c, w) + a2 * g(-c, w)


def fit_von_mises2(phi, x):
    """
    :input phi: 1D vector of equidistally distributed angles between 0 and 2*pi
    :input x:  1D vector of response magnitudes at those angles
    :output: v, r2 - where v is the list of the fitted coefficients and r2 is squared error
    """
    assert x.ndim == 1 and phi.ndim == 1, 'data must be in 1D vectors'
    angles, idx, counts = np.unique(phi, return_counts=True, return_inverse=True)
    assert all(abs(np.diff(angles) - 2 * np.pi / angles.shape[0]) < 1e-6), 'non-uniform angles'

    # estimate theta with two-cosine fit
    s = x / counts[idx] @ np.exp(2j * phi)
    theta = 0.5 * np.angle(s)
    xm = x.mean()
    x = x - xm
    c = np.cos(phi - theta)

    def amps(width):
        # fit amplitudes
        G = np.stack((g(c, width), g(-c, width)))
        gm = G.mean(axis=1, keepdims=True)
        a = np.maximum(x @ np.linalg.pinv(G - gm), 0)
        d = x - a @ (G - gm)
        return d @ d, a, gm, width, np.sign(d @ (a @ (G * np.stack((1 - c, 1 + c)))))

    # binary search for optimal width
    best = None
    bounds = [0, nwidths]
    while bounds[1] - bounds[0] > 1:
        mid = (bounds[0] + bounds[1]) // 2
        candidate = amps(widths[mid])
        if best is None or best[0] > candidate[0]:
            best = candidate
        bounds[1 if candidate[4] > 0 else 0] = mid

    r2, a, gm, w, _ = best

    if a[0] < a[1]:
        a = a[[1, 0]]
        theta = theta + np.pi

    return (xm - a @ gm, a[0], a[1], theta % (2 * np.pi), w), r2


def bootstrap_von_mises2(phi, x, shuffles=5000):
    v, r2 = fit_von_mises2(phi, x)
    return v, r2, sum((fit_von_mises2(phi, x[np.random.permutation(x.shape[0])])[1] < r2
                       for shuffle in range(shuffles)), 0.5) / shuffles


def fast_tuning_bootstrap(phi, y, balanced=True, shuffles=5000, sequential=False):
    if balanced:
        factor = np.ones_like(phi)
    else:
        _, inv_ix, counts = np.unique(phi, return_inverse=True, return_counts=True)
        factor = 1 / counts[inv_ix]
    base = np.exp(2j * phi) * factor
    s = np.abs(y @ base)

    if not sequential:
        y_shuffle = np.tile(y, (shuffles, 1))
        list(map(np.random.shuffle, y_shuffle))
        s_shuffle = np.abs(y_shuffle @ base)
    else:
        y = np.array(y)  # copy input
        s_shuffle = []
        for _ in range(shuffles):
            np.random.shuffle(y)
            s_shuffle.append(np.abs(y @ base))
        s_shuffle = np.array(s_shuffle)

    p = (s_shuffle > s).mean() + 0.5 / shuffles
    return p, s, s_shuffle
