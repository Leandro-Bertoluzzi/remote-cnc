"""Infrastructure adapter: renders G-code files as PNG thumbnails."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from worker.domain.gcode.parser import GcodeParser, MovementType, Polyline

# ---------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------


class GcodeRenderer:
    def __init__(self):
        self.imgwidth = 800
        self.imgheight = 600

        self.bedsize = (210.0, 210.0)

        self.extrudecolor = "#007FFE"
        self.movecolor = "#E53935"
        self.background = "white"

        self._reset()

    # -----------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------

    def run(self, path_src: str, path_out: str, moves: bool):
        self._reset()

        self.path = path_src
        self.moves = moves

        self._load_model(path_src)

        figure = self._build_figure()

        self._save(
            figure,
            path_out,
        )

        plt.close(figure)

    # -----------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------

    def _reset(self):
        self.path = ""
        self.moves = False
        self.model = None

    def _load_model(
        self,
        path: str,
    ) -> None:
        parser = GcodeParser()
        self.model = parser.parse_file(path)

    def _build_figure(
        self,
    ) -> plt.Figure:
        fig = plt.figure(figsize=(self.imgwidth / 100, self.imgheight / 100), dpi=100)

        axes = fig.add_subplot(111, projection="3d")

        self._plot_model(axes)

        self._configure_axes(axes)

        return fig

    def _plot_model(self, axes: Axes3D):
        for polyline in self.model.polylines:
            if polyline.type == MovementType.MACHINING:
                self._plot_polyline(
                    axes,
                    polyline,
                    color=self.extrudecolor,
                    linewidth=1.0,
                    solid_capstyle="round",
                    solid_joinstyle="round",
                )

            elif polyline.type == MovementType.TRAVEL and self.moves:
                self._plot_polyline(
                    axes,
                    polyline,
                    color=self.movecolor,
                    linewidth=1.0,
                    linestyle="dotted",
                )

    def _plot_polyline(self, axes: Axes3D, polyline: Polyline, **kwargs) -> None:
        x = [vertex.x for vertex in polyline.vertices]
        y = [vertex.y for vertex in polyline.vertices]
        z = [vertex.z for vertex in polyline.vertices]

        axes.plot(
            x,
            y,
            z,
            **kwargs,
        )

    def _configure_axes(
        self,
        axes: Axes3D,
    ) -> None:
        axes.set_axis_off()
        axes.set_box_aspect(
            (self.bedsize[0], self.bedsize[1], self._z_size()),
        )

        elev, azim, focal_length = self._compute_camera()
        axes.view_init(elev=elev, azim=azim)
        # axes.set_proj_type("persp", focal_length=focal_length)

        if self.model and self.model.bbox:
            bbox = self.model.bbox
            eps = 0.5
            xmin = bbox.xmin - eps if bbox.dx() == 0 else bbox.xmin
            xmax = bbox.xmax + eps if bbox.dx() == 0 else bbox.xmax
            ymin = bbox.ymin - eps if bbox.dy() == 0 else bbox.ymin
            ymax = bbox.ymax + eps if bbox.dy() == 0 else bbox.ymax
            zmin = bbox.zmin - eps if bbox.dz() == 0 else bbox.zmin
            zmax = bbox.zmax + eps if bbox.dz() == 0 else bbox.zmax
            axes.set_xlim(xmin, xmax)
            axes.set_ylim(ymin, ymax)
            axes.set_zlim(zmin, zmax)

    def _z_size(self) -> float:
        if self.model is None or self.model.bbox is None:
            return 1.0

        return max(self.model.bbox.dz(), 1.0)

    def _compute_camera(
        self,
    ) -> tuple[float, float, float]:
        """Return (elev, azim, focal_length) derived from the eye vector (-d, -d, d*0.85)."""
        _base_distance = 1.6

        if self.model is None or self.model.bbox is None:
            distance = _base_distance
        else:
            # Use the calculated bounding box to compute a suitable camera position
            bbox = self.model.bbox
            dx = max(bbox.dx(), 1.0)
            dy = max(bbox.dy(), 1.0)
            dz = max(bbox.dz(), 1.0)
            size = max(dx, dy, dz)
            distance = _base_distance + size / 150.0

        # Convert eye vector (-d, -d, d*0.85) to spherical angles
        ex, ey, ez = -distance, -distance, distance * 0.85
        r_xy = math.sqrt(ex**2 + ey**2)
        elev = math.degrees(math.atan2(ez, r_xy))  # 35°
        azim = math.degrees(math.atan2(ey, ex))  # -135°

        # Wider FOV for larger models (simulates stepping back)
        focal_length = _base_distance / distance

        return elev, azim, focal_length

    def _save(
        self,
        figure: plt.Figure,
        path_out: str,
    ) -> None:
        figure.savefig(
            path_out,
            format="png",
            dpi=100,
            facecolor=self.background,
            edgecolor="none",
            bbox_inches=None,
            pad_inches=0,
        )
