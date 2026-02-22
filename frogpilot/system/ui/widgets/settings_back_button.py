import pyray as rl

from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.lib.text_measure import measure_text_cached

BUTTON_HEIGHT = 125
BUTTON_WIDTH = 300
BUTTON_TEXT_SIZE = 50
BUTTON_TOP_MARGIN = 60
BUTTON_RIGHT_MARGIN = 100
BUTTON_ROUNDNESS = 0.4
BUTTON_ROUND_SEGMENTS = 20

BUTTON_COLOR = rl.Color(41, 41, 41, 255)
BUTTON_PRESSED_COLOR = rl.Color(173, 173, 173, 255)


class SettingsBackButton:
  def __init__(self):
    self._font_medium = gui_app.font(FontWeight.MEDIUM)

  def draw(self, sidebar_rect: rl.Rectangle) -> rl.Rectangle:
    button_rect = rl.Rectangle(
      sidebar_rect.x + sidebar_rect.width - BUTTON_WIDTH - BUTTON_RIGHT_MARGIN,
      sidebar_rect.y + BUTTON_TOP_MARGIN,
      BUTTON_WIDTH,
      BUTTON_HEIGHT,
    )

    pressed = (
      rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_LEFT)
      and rl.check_collision_point_rec(rl.get_mouse_position(), button_rect)
    )
    button_color = BUTTON_PRESSED_COLOR if pressed else BUTTON_COLOR
    rl.draw_rectangle_rounded(button_rect, BUTTON_ROUNDNESS, BUTTON_ROUND_SEGMENTS, button_color)

    back_text = "\u2190 Back"
    text_size = measure_text_cached(self._font_medium, back_text, BUTTON_TEXT_SIZE)

    text_pos = rl.Vector2(
      button_rect.x + (button_rect.width - text_size.x) / 2,
      button_rect.y + (button_rect.height - text_size.y) / 2,
    )
    rl.draw_text_ex(self._font_medium, back_text, text_pos, BUTTON_TEXT_SIZE, 0, rl.WHITE)

    return button_rect
