from collections.abc import Callable

import pyray as rl

from openpilot.common.params import Params
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller

from openpilot.frogpilot.system.ui.widgets.list_view import frogpilot_multiple_button_item
from openpilot.frogpilot.ui.layouts.settings.alerts_and_sounds import AlertsAndSoundsLayout

PANEL_LAYOUT_FACTORIES: dict[str, Callable[[Callable[[], None]], Widget]] = {
  "alerts_and_sounds": lambda back_callback: AlertsAndSoundsLayout(back_callback=back_callback),
}

PANEL_LAYOUT = (
  {
    "title": tr_noop("Alerts and Sounds"),
    "description": tr_noop("<b>Adjust alert volumes and enable custom notifications.</b>"),
    "buttons": (tr_noop("MANAGE"),),
    "panel_targets": ("alerts_and_sounds",),
  },
  {
    "title": tr_noop("Driving Controls"),
    "description": tr_noop("<b>Fine-tune custom FrogPilot acceleration, braking, and steering controls.</b>"),
    "buttons": (tr_noop("DRIVING MODEL"), tr_noop("GAS / BRAKE"), tr_noop("STEERING")),
  },
  {
    "title": tr_noop("Navigation"),
    "description": tr_noop("<b>Download map data for the \"Speed Limit Controller\".</b>"),
    "buttons": (tr_noop("MAP DATA"), tr_noop("NAVIGATION")),
  },
  {
    "title": tr_noop("System Settings"),
    "description": tr_noop("<b>Manage backups, device settings, screen options, storage, and tools to keep FrogPilot running smoothly.</b>"),
    "buttons": (tr_noop("DATA"), tr_noop("DEVICE CONTROLS"), tr_noop("UTILITIES")),
  },
  {
    "title": tr_noop("Theme and Appearance"),
    "description": tr_noop("<b>Customize the look of the driving screen and interface, including themes!</b>"),
    "buttons": (tr_noop("APPEARANCE"), tr_noop("THEME")),
  },
  {
    "title": tr_noop("Vehicle Settings"),
    "description": tr_noop("<b>Configure car-specific options and steering wheel button mappings.</b>"),
    "buttons": (tr_noop("VEHICLE SETTINGS"), tr_noop("WHEEL CONTROLS")),
  },
)

TUNING_LEVEL_DESCRIPTION = tr_noop(
  "Choose your tuning level. Lower levels keep it simple; higher levels unlock more toggles for finer control.\n\n"
  "Minimal - Ideal for those who prefer simplicity or ease of use\n"
  "Standard - Recommended for most users for a balanced experience\n"
  "Advanced - Fine-tuning for experienced users\n"
  "Developer - Highly customizable settings for seasoned enthusiasts"
)

TUNING_LEVEL_LABELS = (
  tr_noop("Minimal"),
  tr_noop("Standard"),
  tr_noop("Advanced"),
  tr_noop("Developer"),
)

DEFAULT_TUNING_LEVEL = 2
MAX_TUNING_LEVEL = len(TUNING_LEVEL_LABELS) - 1


class FrogPilotLayout(Widget):
  def __init__(self):
    super().__init__()

    self._params = Params()
    self._tuning_level = self._get_tuning_level()

    self._active_panel: str | None = None
    self._panel_layouts: dict[str, Widget] = {
      panel_id: layout_factory(self._show_main_panel)
      for panel_id, layout_factory in PANEL_LAYOUT_FACTORIES.items()
    }

    items = [
      frogpilot_multiple_button_item(
        lambda: tr("Tuning Level"),
        description=lambda: tr(TUNING_LEVEL_DESCRIPTION),
        buttons=[lambda label=label: tr(label) for label in TUNING_LEVEL_LABELS],
        selected_index=self._tuning_level,
        callback=self._set_tuning_level,
      ),
    ]

    for group in PANEL_LAYOUT:
      panel_targets = group.get("panel_targets", ())
      if panel_targets and len(panel_targets) != len(group["buttons"]):
        raise ValueError(f"panel_targets length must match buttons for panel '{group['title']}'")
      if any(panel_id is not None and panel_id not in self._panel_layouts for panel_id in panel_targets):
        raise ValueError(f"panel_targets contains unknown panel ID for panel '{group['title']}'")

      callback = None
      if panel_targets:
        callback = lambda button_index, panel_targets=panel_targets: self._open_group_panel(panel_targets, button_index)

      items.append(
        frogpilot_multiple_button_item(
          lambda title=group["title"]: tr(title),
          description=lambda description=group["description"]: tr(description),
          buttons=[lambda label=label: tr(label) for label in group["buttons"]],
          selected_index=-1,
          callback=callback,
        )
      )

    self._main_scroller = Scroller(items, line_separator=True, spacing=0)

  def show_event(self):
    active_panel = self._get_active_panel_layout()
    if active_panel is not None:
      active_panel.show_event()
    else:
      self._main_scroller.show_event()

  def hide_event(self):
    active_panel = self._get_active_panel_layout()
    if active_panel is not None:
      active_panel.hide_event()
    self._active_panel = None

  def _get_active_panel_layout(self) -> Widget | None:
    if self._active_panel is None:
      return None
    return self._panel_layouts.get(self._active_panel)

  def _open_group_panel(self, panel_targets: tuple[str | None, ...], button_index: int):
    if button_index < 0 or button_index >= len(panel_targets):
      return

    panel_id = panel_targets[button_index]
    if panel_id is None:
      return
    self._open_panel(panel_id)

  def _open_panel(self, panel_id: str):
    panel_layout = self._panel_layouts.get(panel_id)
    if panel_layout is None:
      return
    self._active_panel = panel_id
    panel_layout.show_event()

  def _render(self, rect: rl.Rectangle):
    active_panel = self._get_active_panel_layout()
    if active_panel is not None:
      active_panel.render(rect)
    else:
      self._main_scroller.render(rect)

  def _set_tuning_level(self, tuning_level: int):
    clamped_tuning_level = max(0, min(MAX_TUNING_LEVEL, int(tuning_level)))
    self._tuning_level = clamped_tuning_level
    self._params.put("TuningLevel", clamped_tuning_level)
    self._params.put_bool("TuningLevelConfirmed", True)

  def _get_tuning_level(self) -> int:
    if not self._params.get_bool("TuningLevelConfirmed"):
      return DEFAULT_TUNING_LEVEL

    value = self._params.get("TuningLevel", return_default=True)
    try:
      return max(0, min(MAX_TUNING_LEVEL, int(value)))
    except (TypeError, ValueError):
      return DEFAULT_TUNING_LEVEL

  def _show_main_panel(self):
    self._active_panel = None
    self._main_scroller.show_event()

  def can_navigate_back(self) -> bool:
    active_panel = self._get_active_panel_layout()
    if active_panel is not None:
      panel_can_navigate_back = getattr(active_panel, "can_navigate_back", None)
      if callable(panel_can_navigate_back) and panel_can_navigate_back():
        return True

    return self._active_panel is not None

  def navigate_back(self) -> bool:
    if not self.can_navigate_back():
      return False

    active_panel = self._get_active_panel_layout()
    if active_panel is not None:
      panel_navigate_back = getattr(active_panel, "navigate_back", None)
      if callable(panel_navigate_back) and panel_navigate_back():
        return True

    self._show_main_panel()
    return True
