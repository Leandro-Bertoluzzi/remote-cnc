"""Port: file renderer."""

from typing import Protocol


class IRenderer(Protocol):
    """Renders a G-code file."""

    def run(self, path_src: str, path_out: str, moves: bool) -> None:
        """Render *path_src* and save the output image to *path_out*.

        Args:
            path_src: Absolute path to the G-code source file.
            path_out: Absolute path where the rendered output will be written.
            moves: Whether to render rapid-move segments in addition to controlled-move segments.
        """
        ...
