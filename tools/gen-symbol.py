#!/usr/bin/env python3
"""Builds the yin-yang from my site as a small ASCII STL and writes it into the
README between the stl:start and stl:end markers. GitHub draws it as a model you
can rotate.

    pip install shapely trimesh mapbox-earcut numpy
    python3 tools/gen-symbol.py

The base is a flat disc. The dark half of the symbol is raised on top of it, with
the small dot cut out of the raised half and the other dot raised on the flat half.
"""
import re
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
SEG = 9             # segments per quarter circle: sets how smooth the edges are
BASE_H, RAISE_H = 6.0, 9.0


def disc(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=SEG)


def symbol():
    # y is up here, so the SVG's y-down symbol is mirrored top to bottom
    right = disc(0, 0, 100).intersection(box(0, -100, 100, 100))
    lower_lobe = disc(0, -50, 50)          # SVG lower lobe, dark
    upper_lobe = disc(0, 50, 50)           # SVG upper lobe, light
    dark = unary_union([right, lower_lobe]).difference(upper_lobe)
    dark = dark.union(disc(0, 50, 14)).difference(disc(0, -50, 14))
    return disc(0, 0, 100), dark


def extrude(poly, h, z):
    polys = poly.geoms if hasattr(poly, "geoms") else [poly]
    meshes = []
    for g in polys:
        m = trimesh.creation.extrude_polygon(g, h)
        m.apply_translation([0, 0, z])
        meshes.append(m)
    return trimesh.util.concatenate(meshes)


def ascii_stl(mesh, name="yinyang"):
    out = [f"solid {name}"]
    f = lambda v: f"{v:.1f}".rstrip("0").rstrip(".") if abs(v) > 1e-6 else "0"
    for tri, n in zip(mesh.triangles, mesh.face_normals):
        out.append(f"facet normal {f(n[0])} {f(n[1])} {f(n[2])}")
        out.append("outer loop")
        for v in tri:
            out.append(f"vertex {f(v[0])} {f(v[1])} {f(v[2])}")
        out.append("endloop")
        out.append("endfacet")
    out.append(f"endsolid {name}")
    return "\n".join(out)


def main():
    base_poly, dark_poly = symbol()
    mesh = trimesh.util.concatenate([extrude(base_poly, BASE_H, 0), extrude(dark_poly, RAISE_H, BASE_H)])
    text = ascii_stl(mesh)
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    block = f"<!-- stl:start -->\n```stl\n{text}\n```\n<!-- stl:end -->"
    new = re.sub(r"<!-- stl:start -->.*?<!-- stl:end -->", lambda _: block, readme, flags=re.S)
    assert new != readme or block in readme, "markers not found in README.md"
    readme_path.write_text(new)
    print(f"{len(mesh.faces)} triangles, {len(text) / 1024:.0f} KB of STL, watertight={mesh.is_watertight}")


if __name__ == "__main__":
    main()
