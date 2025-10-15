# rendering.py
"""
Matplotlib-based 2D rendering (headless-friendly).
Drop-in replacement for the pyglet/OpenGL version used by MultiAgentEnv.
"""

from __future__ import annotations

# Force a non-interactive backend for servers/headless use.
import matplotlib
matplotlib.use("Agg")

import math
import numpy as np

from matplotlib.figure import Figure
from matplotlib.patches import Circle as MplCircle, Polygon as MplPolygon
from matplotlib.lines import Line2D
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import transforms as mtransforms


RAD2DEG = 57.29577951308232


def _clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


class Attr:
    def enable(self, *args, **kwargs):
        raise NotImplementedError

    def disable(self, *args, **kwargs):
        pass


class Color(Attr):
    def __init__(self, vec4):
        # (r, g, b, a), each in [0,1]
        r, g, b, a = vec4
        self.vec4 = (_clamp01(r), _clamp01(g), _clamp01(b), _clamp01(a))

    def enable(self, *args, **kwargs):
        # handled in Geom draw path
        pass


class LineWidth(Attr):
    def __init__(self, stroke: float):
        self.stroke = float(stroke)

    def enable(self, *args, **kwargs):
        # handled in Geom draw path
        pass


class Transform(Attr):
    def __init__(self, translation=(0.0, 0.0), rotation=0.0, scale=(1.0, 1.0)):
        self.set_translation(*translation)
        self.set_rotation(rotation)
        self.set_scale(*scale)

    def set_translation(self, newx, newy):
        self.translation = (float(newx), float(newy))

    def set_rotation(self, new):
        self.rotation = float(new)  # radians

    def set_scale(self, newx, newy):
        self.scale = (float(newx), float(newy))

    def as_affine(self) -> mtransforms.Affine2D:
        t = mtransforms.Affine2D()
        # Match the original GL order by composing in the same sequence used on enable().
        # In the original code transforms were enabled in reversed(self.attrs).
        # We'll compose the per-Transform operation here; Geom will decide ordering.
        tx, ty = self.translation
        sx, sy = self.scale
        if sx != 1.0 or sy != 1.0:
            t = t.scale(sx, sy)
        if self.rotation != 0.0:
            t = t.rotate(self.rotation)
        if tx != 0.0 or ty != 0.0:
            t = t.translate(tx, ty)
        return t


class Geom:
    def __init__(self):
        self._color = Color((0.0, 0.0, 0.0, 1.0))
        self.attrs = [self._color]
        self._linewidth = LineWidth(1.0)

    # API compatibility with original
    def add_attr(self, attr: Attr):
        self.attrs.append(attr)

    def set_color(self, r, g, b, alpha=1.0):
        self._color = Color((r, g, b, alpha))
        # keep it present/last-set in attrs
        # remove previous Color if exists then append fresh one
        self.attrs = [a for a in self.attrs if not isinstance(a, Color)]
        self.attrs.append(self._color)

    def set_linewidth(self, x):
        self._linewidth = LineWidth(x)

    # Helpers for subclasses
    def _collect_transform(self) -> mtransforms.Affine2D:
        # Emulate original GL order: enable() was called in reversed(self.attrs)
        # so we’ll multiply transforms in reversed attr order.
        affine = mtransforms.Affine2D()
        for attr in reversed(self.attrs):
            if isinstance(attr, Transform):
                affine = affine + attr.as_affine()
        return affine

    def _get_colors(self):
        r, g, b, a = self._color.vec4
        face = (r, g, b, a)
        edge = (0.5 * r, 0.5 * g, 0.5 * b, 0.5 * a)
        return face, edge

    def _get_linewidth(self):
        return self._linewidth.stroke

    # Subclasses must implement this: add matplotlib artists to ax
    def draw(self, ax):
        raise NotImplementedError


class FilledPolygon(Geom):
    def __init__(self, v):
        super().__init__()
        # v: list of (x, y)
        self.v = np.asarray(v, dtype=float)

    def draw(self, ax):
        face, edge = self._get_colors()
        patch = MplPolygon(self.v, closed=True, facecolor=face, edgecolor=edge, linewidth=self._get_linewidth())
        patch.set_transform(self._collect_transform() + ax.transData)
        ax.add_patch(patch)


class PolyLine(Geom):
    def __init__(self, v, close: bool):
        super().__init__()
        self.v = np.asarray(v, dtype=float)
        self.close = bool(close)

    def draw(self, ax):
        face, edge = self._get_colors()
        if self.close:
            # close loop by repeating first point
            pts = np.vstack([self.v, self.v[0]])
        else:
            pts = self.v
        line = Line2D(pts[:, 0], pts[:, 1], linewidth=self._get_linewidth(), color=edge)
        # Apply transform to data coordinates by transforming the points beforehand
        aff = self._collect_transform()
        pts_t = aff.transform(pts)
        line.set_data(pts_t[:, 0], pts_t[:, 1])
        ax.add_line(line)


class Circle(Geom):
    def __init__(self, radius=10.0):
        super().__init__()
        self.radius = float(radius)

    def draw(self, ax):
        face, edge = self._get_colors()
        patch = MplCircle((0.0, 0.0), self.radius, facecolor=face, edgecolor=edge, linewidth=self._get_linewidth())
        patch.set_transform(self._collect_transform() + ax.transData)
        ax.add_patch(patch)


class Compound(Geom):
    def __init__(self, geoms):
        super().__init__()
        self.gs = geoms

    def draw(self, ax):
        for g in self.gs:
            g.draw(ax)


def make_circle(radius=10, res=30, filled=True):
    # res is unused here; matplotlib draws circle analytically.
    return Circle(radius=radius)


def make_polygon(v, filled=True):
    if filled:
        return FilledPolygon(v)
    else:
        return PolyLine(v, True)


def make_polyline(v):
    return PolyLine(v, False)


def make_capsule(length, width):
    # Optional helper for parity with original; not used by your env code.
    # Build as a rectangle + two semicircles using Compound.
    half_w = width / 2.0
    body = make_polygon([(0, -half_w), (0, half_w), (length, half_w), (length, -half_w)], filled=True)
    cap0 = make_circle(half_w)
    cap1 = make_circle(half_w)
    t1 = Transform(translation=(length, 0.0))
    cap1.add_attr(t1)
    return Compound([body, cap0, cap1])


class Viewer:
    def __init__(self, width, height, display=None, dpi=100):
        # width, height are pixels (to match old API expectations)
        self.width = int(width)
        self.height = int(height)
        self.dpi = int(dpi)

        self.figure = Figure(figsize=(self.width / self.dpi, self.height / self.dpi), dpi=self.dpi)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor((1, 1, 1))
        self.ax.axis("off")
        self.geoms = []
        self.onetime_geoms = []

        # default bounds
        self._bounds = (-1.0, 1.0, -1.0, 1.0)

    def close(self):
        # Nothing to close in headless mode.
        pass

    # API compatibility
    def set_bounds(self, left, right, bottom, top):
        assert right > left and top > bottom
        self._bounds = (left, right, bottom, top)

    def add_geom(self, geom: Geom):
        self.geoms.append(geom)

    def add_onetime(self, geom: Geom):
        self.onetime_geoms.append(geom)

    def _prepare_axes(self):
        left, right, bottom, top = self._bounds
        self.ax.clear()
        self.ax.set_facecolor((1, 1, 1))
        self.ax.set_xlim(left, right)
        self.ax.set_ylim(bottom, top)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.axis("off")

    def render(self, return_rgb_array=False):
        self._prepare_axes()

        # Draw persistent geoms
        for g in self.geoms:
            g.draw(self.ax)
        # Draw one-time geoms
        for g in self.onetime_geoms:
            g.draw(self.ax)

        # Clear one-time geoms after draw (API parity)
        self.onetime_geoms = []

        self.canvas.draw()

        if return_rgb_array:
            w, h = self.canvas.get_width_height()
            buf = np.frombuffer(self.canvas.tostring_argb(), dtype=np.uint8)
            arr = buf.reshape((h, w, 4))[:, :, :3]  # drop alpha
            # The original pyglet path returned an array with origin at the *top*.
            # Agg already returns top-origin buffers; if you need bottom-origin, flip here:
            # arr = arr[::-1, :, :]
            return arr

        # In "human" mode we don’t open a window server-side. No-op.
        return None

    # Convenience drawing helpers (kept for API parity, rarely used)
    def draw_circle(self, radius=10, res=30, filled=True, **attrs):
        geom = make_circle(radius=radius, res=res, filled=filled)
        _add_attrs(geom, attrs)
        self.add_onetime(geom)
        return geom

    def draw_polygon(self, v, filled=True, **attrs):
        geom = make_polygon(v=v, filled=filled)
        _add_attrs(geom, attrs)
        self.add_onetime(geom)
        return geom

    def draw_polyline(self, v, **attrs):
        geom = make_polyline(v=v)
        _add_attrs(geom, attrs)
        self.add_onetime(geom)
        return geom

    def draw_line(self, start, end, **attrs):
        geom = PolyLine([start, end], close=False)
        _add_attrs(geom, attrs)
        self.add_onetime(geom)
        return geom

    def get_array(self):
        # Kept for parity with original API
        return self.render(return_rgb_array=True)


def _add_attrs(geom: Geom, attrs: dict):
    if "color" in attrs:
        geom.set_color(*attrs["color"])
    if "linewidth" in attrs:
        geom.set_linewidth(attrs["linewidth"])


# Simple image viewer implemented with matplotlib (API compatibility if you use it elsewhere)
class SimpleImageViewer(object):
    def __init__(self, display=None):
        self.figure = None
        self.canvas = None
        self.ax = None
        self.isopen = False

    def imshow(self, arr: np.ndarray):
        h, w, c = arr.shape
        if c != 3:
            raise AssertionError("Expected an RGB image (H, W, 3).")
        if self.figure is None:
            self.figure = Figure(figsize=(w / 100.0, h / 100.0), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.ax = self.figure.add_subplot(111)
            self.ax.axis("off")
            self.isopen = True
        else:
            self.ax.clear()
            self.ax.axis("off")

        # Matplotlib expects origin at lower-left by default; show as-is.
        self.ax.imshow(arr)
        self.canvas.draw()

    def close(self):
        self.isopen = False

    def __del__(self):
        self.close()
