"""Infrastructure adapter: renders G-code files as PNG thumbnails."""

from __future__ import annotations

from typing import TypedDict

import plotly.graph_objects as go
from PIL import Image

import worker.domain.gcode.parser as gcode

# ---------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------


class Points(TypedDict):
    x: list[float]
    y: list[float]
    z: list[float]


class Coordinates(TypedDict):
    object: Points
    moves: Points


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

    # -----------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------

    def _reset(self):
        self.path = ""
        self.moves = False
        self.model = None

        self.coords: Coordinates = {
            "object": {"x": [], "y": [], "z": []},
            "moves": {"x": [], "y": [], "z": []},
        }

    def _load_model(
        self,
        path: str,
    ) -> None:
        parser = gcode.GcodeParser()
        self.model = parser.parseFile(path)

        for segment in self.model.segments:
            if segment.type == "G1":
                self.coords["object"]["x"].append(segment.coords["x"])
                self.coords["object"]["y"].append(segment.coords["y"])
                self.coords["object"]["z"].append(segment.coords["z"])
                continue

            if self.moves:
                self.coords["moves"]["x"].append(segment.coords["x"])
                self.coords["moves"]["y"].append(segment.coords["y"])
                self.coords["moves"]["z"].append(segment.coords["z"])

    def _build_figure(
        self,
    ) -> go.Figure:
        fig = go.Figure()

        self._add_object_trace(fig)

        if self.moves:
            self._add_moves_trace(fig)

        self._configure_scene(fig)

        return fig

    def _add_object_trace(
        self,
        fig: go.Figure,
    ) -> None:
        fig.add_trace(
            go.Scatter3d(
                x=self.coords["object"]["x"],
                y=self.coords["object"]["y"],
                z=self.coords["object"]["z"],
                mode="lines",
                line={
                    "color": self.extrudecolor,
                    "width": 5,
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )

    def _add_moves_trace(
        self,
        fig: go.Figure,
    ) -> None:
        if not self.coords["moves"]["x"]:
            return

        fig.add_trace(
            go.Scatter3d(
                x=self.coords["moves"]["x"],
                y=self.coords["moves"]["y"],
                z=self.coords["moves"]["z"],
                mode="lines",
                line={
                    "color": self.movecolor,
                    "width": 2,
                    "dash": "dot",
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )

    def _configure_scene(
        self,
        fig: go.Figure,
    ) -> None:
        fig.update_layout(
            width=self.imgwidth,
            height=self.imgheight,
            paper_bgcolor=self.background,
            plot_bgcolor=self.background,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            scene={
                "aspectmode": "data",
                "camera": self._compute_camera(),
                "xaxis": {
                    "visible": False,
                    "showgrid": False,
                    "zeroline": False,
                },
                "yaxis": {
                    "visible": False,
                    "showgrid": False,
                    "zeroline": False,
                },
                "zaxis": {
                    "visible": False,
                    "showgrid": False,
                    "zeroline": False,
                },
            },
        )

    def _compute_camera(
        self,
    ) -> dict:
        if self.model is None or self.model.bbox is None:
            return {
                "eye": {"x": -1.6, "y": -1.6, "z": 1.3},
                "center": {"x": 0, "y": 0, "z": 0},
            }

        bbox = self.model.bbox

        dx = max(bbox.dx(), 1.0)
        dy = max(bbox.dy(), 1.0)
        dz = max(bbox.dz(), 1.0)

        size = max(dx, dy, dz)
        distance = 1.6 + size / 150.0

        return {
            "eye": {
                "x": -distance,
                "y": -distance,
                "z": distance * 0.85,
            },
            "center": {"x": 0, "y": 0, "z": 0},
            "up": {"x": 0, "y": 0, "z": 1},
        }

    def _save(
        self,
        figure: go.Figure,
        path_out: str,
    ) -> None:
        figure.write_image(
            path_out,
            width=self.imgwidth,
            height=self.imgheight,
        )

        img = Image.open(path_out)
        basewidth = self.imgwidth
        wpercent = basewidth / float(img.size[0])
        hsize = int(img.size[1] * wpercent)

        img = img.resize((basewidth, hsize), Image.Resampling.LANCZOS)
        img.save(path_out)
