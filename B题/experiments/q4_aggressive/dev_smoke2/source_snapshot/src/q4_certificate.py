"""Sufficient continuous certificate for omnidirectional AND 180-degree RF discovery.

An outer regular polygon contains Omega. Its vertices lie strictly inside the
point-set hull. For each Delaunay triangle intersecting that polygon, all three
sites must be < R_MIN from every point of the intersection. The maximum of the
convex distance function occurs at a polygon vertex, so finitely many checks
certify the whole disk, not just sampled locations/headings.

For a source on a triangulation edge/vertex, take all incident triangles. Since
Omega is strictly inside the hull, their sites surround the source; every open
half-plane contains a nonzero vector to a receiving site. Thus a directional
source also has a strict witness. This is sufficient, not a minimal-cover proof.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import ConvexHull, Delaunay, QhullError

from params import OMEGA_RADIUS, R_MIN
from q4_localize import _clip_convex


def discovery_certificate(points, *, radius=OMEGA_RADIUS, receive_radius=R_MIN, sides=128):
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    result = dict(valid=False, n_points=len(pts), polygon_sides=sides,
                  max_distance_m=None, hull_margin_m=None, triangles_checked=0)
    if len(pts) < 3 or not np.all(np.isfinite(pts)) or sides < 8:
        return result
    angles = np.arange(sides) * (2 * np.pi / sides)
    outer = radius / np.cos(np.pi / sides) * np.column_stack((np.cos(angles), np.sin(angles)))
    try:
        hull = ConvexHull(pts)
        mesh = Delaunay(pts)
    except QhullError:
        return result
    margin = -float(np.max(outer @ hull.equations[:, :2].T + hull.equations[:, 2]))
    result["hull_margin_m"] = margin
    if margin <= 1e-6:
        return result
    bound = 0.0
    for indices in mesh.simplices:
        tri = pts[indices]
        cell = outer.copy()
        for equation in ConvexHull(tri).equations:
            cell = _clip_convex(cell, equation[:2], -equation[2])
        if len(cell):
            result["triangles_checked"] += 1
            bound = max(bound, float(np.max(np.linalg.norm(cell[:, None] - tri[None, :], axis=2))))
    result["max_distance_m"] = bound
    result["valid"] = bool(bound < receive_radius - 1e-6)
    return result
