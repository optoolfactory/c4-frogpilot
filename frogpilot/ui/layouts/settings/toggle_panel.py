from collections.abc import Callable

import pyray as rl

from openpilot.common.params import Params
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.scroller_tici import Scroller

from openpilot.frogpilot.system.ui.widgets.list_view import frogpilot_manage_control_item, frogpilot_numeric_control_item, frogpilot_toggle_item
from openpilot.frogpilot.ui.layouts.settings.toggle_metadata import ToggleDefinition, ToggleType


class TogglePanel(Widget):
  def __init__(self, toggle_definitions: tuple[ToggleDefinition, ...], back_callback: Callable):
    super().__init__()

    self._params = Params(return_defaults=True)

    self._back_callback = back_callback

    self._active_panel: Widget | None = None

    self._tuning_level: int = self._params.get("TuningLevel")

    parent_params = {toggle_definition.parent_param for toggle_definition in toggle_definitions if toggle_definition.parent_param}

    tuning_levels: dict[str, int] = {
      toggle_definition.param: self._params.get_tuning_level(toggle_definition.param)
      for toggle_definition in toggle_definitions
    }

    child_params: dict[str, list[str]] = {}
    for parent_param in parent_params:
      child_params[parent_param] = [
        toggle_definition.param for toggle_definition in toggle_definitions
        if toggle_definition.parent_param == parent_param
      ]

    self._sub_panels: dict[str, Scroller] = {}
    for parent_param in parent_params:
      child_items = []
      for toggle_definition in toggle_definitions:
        if toggle_definition.parent_param != parent_param:
          continue

        item = self._create_child_item(toggle_definition)
        item.set_visible(lambda p=toggle_definition.param: self._tuning_level >= tuning_levels[p])
        child_items.append(item)
      self._sub_panels[parent_param] = Scroller(child_items, line_separator=True, spacing=0)

    main_items = []
    for toggle_definition in toggle_definitions:
      if toggle_definition.parent_param is not None:
        continue

      if toggle_definition.param in parent_params:
        item = self._create_parent_item(toggle_definition)
        item.set_visible(lambda p=toggle_definition.param: any(
          self._tuning_level >= tuning_levels[child_param] for child_param in child_params[p]
        ))
      else:
        item = self._create_child_item(toggle_definition)
        item.set_visible(lambda p=toggle_definition.param: self._tuning_level >= tuning_levels[p])
      main_items.append(item)

    self._main_scroller = Scroller(main_items, line_separator=True, spacing=0)

  def show_event(self):
    self._main_scroller.show_event()

    self._tuning_level = self._params.get("TuningLevel")

  def hide_event(self):
    if self._active_panel is not None:
      self._active_panel = None

  def can_navigate_back(self) -> bool:
    return self._active_panel is not None

  def navigate_back(self) -> bool:
    if not self.can_navigate_back():
      return False

    self._show_main_panel()
    return True

  def _create_child_item(self, toggle_definition):
    if toggle_definition.toggle_type == ToggleType.NUMERIC:
      return frogpilot_numeric_control_item(
        title=lambda t=toggle_definition.title: tr(t),
        description=lambda d=toggle_definition.description: tr(d),
        value_getter=lambda p=toggle_definition.param: self._params.get(p),
        value_setter=lambda v, p=toggle_definition.param: self._params.put(p, v),
        value_formatter=lambda v, u=toggle_definition.unit, vm=toggle_definition.value_map: vm[v] if vm and v in vm else f"{v}{u}",
        min_value=int(toggle_definition.min_value),
        max_value=int(toggle_definition.max_value),
        step=int(toggle_definition.step),
        icon=toggle_definition.icon,
      )

    return frogpilot_toggle_item(
      title=lambda t=toggle_definition.title: tr(t),
      description=lambda d=toggle_definition.description: tr(d),
      initial_state=self._params.get_bool(toggle_definition.param),
      callback=lambda state, p=toggle_definition.param: self._params.put_bool(p, state),
      icon=toggle_definition.icon,
    )

  def _create_parent_item(self, toggle_definition):
    return frogpilot_manage_control_item(
      title=lambda t=toggle_definition.title: tr(t),
      description=lambda d=toggle_definition.description: tr(d),
      initial_state=self._params.get_bool(toggle_definition.param),
      toggle_callback=lambda state, p=toggle_definition.param: self._params.put_bool(p, state),
      button_callback=lambda p=toggle_definition.param: self._open_panel(p),
      icon=toggle_definition.icon,
    )

  def _open_panel(self, parent_param: str):
    self._active_panel = self._sub_panels[parent_param]
    self._active_panel.show_event()

  def _render(self, rect: rl.Rectangle):
    if self._active_panel is not None:
      self._active_panel.render(rect)
    else:
      self._main_scroller.render(rect)

  def _show_main_panel(self):
    self._main_scroller.show_event()

    self._active_panel = None
