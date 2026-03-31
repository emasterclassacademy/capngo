from ..effect import Effect
from pycaps.renderer import SubtitleRenderer

class ClipEffect(Effect):
    def set_renderer(self, renderer: SubtitleRenderer) -> None:
        self._renderer = renderer
