"""Small planar geometry helpers for district polygons (GeoJSON order: [lng, lat])."""

from __future__ import annotations

import random

Ring = list[list[float]]


def point_in_ring(lng: float, lat: float, ring: Ring) -> bool:
    """Ray-casting point-in-polygon test for a single (closed or open) ring."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def ring_centroid(ring: Ring) -> tuple[float, float]:
    """Vertex mean of the ring (the closing vertex is not counted twice). Returns (lng, lat)."""
    pts = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def random_point_in_ring(rng: random.Random, ring: Ring, max_tries: int = 1000) -> tuple[float, float]:
    """Uniform point inside the ring by rejection sampling on its bounding box. Returns (lng, lat)."""
    lngs = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    lo_x, hi_x, lo_y, hi_y = min(lngs), max(lngs), min(lats), max(lats)
    for _ in range(max_tries):
        x = rng.uniform(lo_x, hi_x)
        y = rng.uniform(lo_y, hi_y)
        if point_in_ring(x, y, ring):
            return x, y
    raise RuntimeError("could not sample a point inside the polygon; is it degenerate?")
