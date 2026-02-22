from collections.abc import Callable

import pyray as rl

from openpilot.common.params import Params
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller

from openpilot.frogpilot.system.ui.widgets.list_view import frogpilot_manage_control_item, frogpilot_numeric_control_item, frogpilot_toggle_item

ALERT_VOLUME_CONTROL = "AlertVolumeControl"
CUSTOM_ALERTS = "CustomAlerts"
ALERT_VOLUME_PANEL = "alert_volume"
CUSTOM_ALERTS_PANEL = "custom_alerts"
VOLUME_STEP = 5
VOLUME_MIN = 0
VOLUME_MAX = 101
WARNING_IMMEDIATE_MIN = 25
DEFAULT_TUNING_LEVEL = 2
MAX_TUNING_LEVEL = 3

CUSTOM_ALERT_SETTING_KEYS = (
  "GoatScream",
  "GreenLightAlert",
  "LeadDepartingAlert",
  "LoudBlindspotAlert",
  "SpeedLimitChangedAlert",
)

SOUND_BOOL_KEYS = (
  ALERT_VOLUME_CONTROL,
  CUSTOM_ALERTS,
  *CUSTOM_ALERT_SETTING_KEYS,
)

SOUND_VOLUME_KEYS = (
  "DisengageVolume",
  "EngageVolume",
  "PromptVolume",
  "PromptDistractedVolume",
  "RefuseVolume",
  "WarningSoftVolume",
  "WarningImmediateVolume",
)

SOUNDS_TOGGLES = (
  ("AlertVolumeControl", "Alert Volume Controller",
   "<b>Set how loud each type of openpilot alert is</b> to keep routine prompts from becoming distracting.",
   "../../../frogpilot/assets/toggle_icons/icon_mute.png"),
  ("DisengageVolume", "Disengage Volume",
   "<b>Set the volume for alerts when openpilot disengages.</b><br><br>Examples include: \"Cruise Fault: Restart the Car\", \"Parking Brake Engaged\", \"Pedal Pressed\".",
   ""),
  ("EngageVolume", "Engage Volume",
   "<b>Set the volume for the chime when openpilot engages</b>, such as after pressing the \"RESUME\" or \"SET\" steering wheel buttons.",
   ""),
  ("PromptVolume", "Prompt Volume",
   "<b>Set the volume for prompts that need attention.</b><br><br>Examples include: \"Car Detected in Blindspot\", \"Steering Temporarily Unavailable\", \"Turn Exceeds Steering Limit\".",
   ""),
  ("PromptDistractedVolume", "Prompt Distracted Volume",
   "<b>Set the volume for prompts when openpilot detects driver distraction or unresponsiveness.</b><br><br>Examples include: \"Pay Attention\", \"Touch Steering Wheel\".",
   ""),
  ("RefuseVolume", "Refuse Volume",
   "<b>Set the volume for alerts when openpilot refuses to engage.</b><br><br>Examples include: \"Brake Hold Active\", \"Door Open\", \"Seatbelt Unlatched\".",
   ""),
  ("WarningSoftVolume", "Warning Soft Volume",
   "<b>Set the volume for softer warnings about potential risks.</b><br><br>Examples include: \"BRAKE! Risk of Collision\", \"Steering Temporarily Unavailable\".",
   ""),
  ("WarningImmediateVolume", "Warning Immediate Volume",
   "<b>Set the volume for the loudest warnings that require urgent attention.</b><br><br>Examples include: \"DISENGAGE IMMEDIATELY - Driver Distracted\", \"DISENGAGE IMMEDIATELY - Driver Unresponsive\".",
   ""),
  ("CustomAlerts", "FrogPilot Alerts",
   "<b>Optional FrogPilot alerts</b> that highlight driving events in a more noticeable way.",
   "../../../frogpilot/assets/toggle_icons/icon_green_light.png"),
  ("GoatScream", "Goat Scream",
   "<b>Play the infamous \"Goat Scream\" when the steering controller reaches its limit.</b> Based on the \"Turn Exceeds Steering Limit\" event.",
   ""),
  ("GreenLightAlert", "Green Light Alert",
   "<b>Play an alert when the model predicts a red light has turned green.</b><br><br><i><b>Disclaimer</b>: openpilot does not explicitly detect traffic lights. This alert is based on end-to-end model predictions from camera input and may trigger even when the light has not changed.</i>",
   ""),
  ("LeadDepartingAlert", "Lead Departing Alert",
   "<b>Play an alert when the lead vehicle departs from a stop.</b>",
   ""),
  ("LoudBlindspotAlert", "Loud \"Car Detected in Blindspot\" Alert",
   "<b>Play a louder alert if a vehicle is in the blind spot when attempting to change lanes.</b> Based on the \"Car Detected in Blindspot\" event.",
   ""),
  ("SpeedLimitChangedAlert", "Speed Limit Changed Alert",
   "<b>Play an alert when the posted speed limit changes.</b>",
   ""),
)


class AlertsAndSoundsLayout(Widget):
  def __init__(self, back_callback: Callable):
    super().__init__()

    self._params = Params()
    self._required_tuning_levels = {
      key: self._params.get_tuning_level(key)
      for key, _, _, _ in SOUNDS_TOGGLES
    }
    self._active_panel: str | None = None
    self._back_callback = back_callback
    self._bool_items = {}

    main_items = []
    alert_volume_items = []
    custom_alert_items = []

    for key, title, description, icon in SOUNDS_TOGGLES:
      if key == ALERT_VOLUME_CONTROL:
        item = frogpilot_manage_control_item(
          title=lambda title=title: tr(title),
          description=lambda description=description: tr(description),
          initial_state=self._params.get_bool(key),
          toggle_callback=lambda state, key=key: self._set_bool_param(key, state),
          button_text=lambda: tr("MANAGE"),
          button_callback=self._open_alert_volume_panel,
        )
        self._bool_items[key] = item
      elif key in SOUND_VOLUME_KEYS:
        min_value = WARNING_IMMEDIATE_MIN if key == "WarningImmediateVolume" else VOLUME_MIN
        item = frogpilot_numeric_control_item(
          title=lambda title=title: tr(title),
          description=lambda description=description: tr(description),
          value_getter=lambda key=key: self._get_int_param(key),
          value_setter=lambda value, key=key: self._set_int_param(key, value),
          value_formatter=self._format_volume_value,
          min_value=min_value,
          max_value=VOLUME_MAX,
          step=VOLUME_STEP,
          enabled=lambda: self._params.get_bool(ALERT_VOLUME_CONTROL),
        )
        item.set_visible(lambda key=key: self._is_toggle_visible(key))
        alert_volume_items.append(item)
        continue
      elif key == CUSTOM_ALERTS:
        item = frogpilot_manage_control_item(
          title=lambda title=title: tr(title),
          description=lambda description=description: tr(description),
          initial_state=self._params.get_bool(key),
          toggle_callback=lambda state, key=key: self._set_bool_param(key, state),
          button_text=lambda: tr("MANAGE"),
          button_callback=self._open_custom_alerts_panel,
        )
        self._bool_items[key] = item
      elif key in CUSTOM_ALERT_SETTING_KEYS:
        item = frogpilot_toggle_item(
          title=lambda title=title: tr(title),
          description=lambda description=description: tr(description),
          initial_state=self._params.get_bool(key),
          callback=lambda state, key=key: self._set_bool_param(key, state),
        )
        item.action_item.set_enabled(lambda: self._params.get_bool(CUSTOM_ALERTS))
        self._bool_items[key] = item
      elif key in SOUND_BOOL_KEYS:
        item = frogpilot_toggle_item(
          title=lambda title=title: tr(title),
          description=lambda description=description: tr(description),
          initial_state=self._params.get_bool(key),
          callback=lambda state, key=key: self._set_bool_param(key, state),
        )
        self._bool_items[key] = item
      else:
        continue

      if icon:
        item.set_icon(icon)

      item.set_visible(lambda key=key: self._is_toggle_visible(key))

      if key in CUSTOM_ALERT_SETTING_KEYS:
        custom_alert_items.append(item)
      else:
        main_items.append(item)

    self._main_scroller = Scroller(main_items, line_separator=True, spacing=0)
    self._alert_volume_scroller = Scroller(alert_volume_items, line_separator=True, spacing=0)
    self._custom_alerts_scroller = Scroller(custom_alert_items, line_separator=True, spacing=0)

  def show_event(self):
    self._active_scroller().show_event()

  def hide_event(self):
    self._active_panel = None

  def _format_volume_value(self, value: int) -> str:
    if value >= VOLUME_MAX:
      return "Auto"
    return f"{value}%"

  def _render(self, rect: rl.Rectangle):
    self._active_scroller().render(rect)

  def _set_bool_param(self, key: str, state: bool):
    self._params.put_bool(key, state)

  def _get_int_param(self, key: str) -> int:
    value = self._params.get(key, return_default=True)
    try:
      return int(value)
    except (TypeError, ValueError):
      default_value = self._params.get_default_value(key)
      return int(default_value) if default_value is not None else VOLUME_MIN

  def _set_int_param(self, key: str, value: int):
    min_value = WARNING_IMMEDIATE_MIN if key == "WarningImmediateVolume" else VOLUME_MIN
    clamped_value = max(min_value, min(VOLUME_MAX, int(value)))
    self._params.put(key, clamped_value)

  def _current_tuning_level(self) -> int:
    if not self._params.get_bool("TuningLevelConfirmed"):
      return DEFAULT_TUNING_LEVEL

    value = self._params.get("TuningLevel", return_default=True)
    try:
      return max(0, min(MAX_TUNING_LEVEL, int(value)))
    except (TypeError, ValueError):
      return DEFAULT_TUNING_LEVEL

  def _is_toggle_visible(self, key: str) -> bool:
    required_level = self._required_tuning_levels.get(key, 0)
    return self._current_tuning_level() >= required_level

  def _active_scroller(self) -> Scroller:
    if self._active_panel == ALERT_VOLUME_PANEL:
      return self._alert_volume_scroller
    if self._active_panel == CUSTOM_ALERTS_PANEL:
      return self._custom_alerts_scroller
    return self._main_scroller

  def _open_alert_volume_panel(self):
    self._active_panel = ALERT_VOLUME_PANEL
    self._alert_volume_scroller.show_event()

  def _open_custom_alerts_panel(self):
    self._active_panel = CUSTOM_ALERTS_PANEL
    self._custom_alerts_scroller.show_event()

  def _show_main_panel(self):
    self._active_panel = None
    self._main_scroller.show_event()

  def can_navigate_back(self) -> bool:
    return self._active_panel is not None

  def navigate_back(self) -> bool:
    if not self.can_navigate_back():
      return False
    self._show_main_panel()
    return True
