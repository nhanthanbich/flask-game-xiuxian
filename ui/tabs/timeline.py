"""
Timeline tab.
"""

from ui.renderer import Renderer


class TimelineTab:
    def __init__(self, world):
        self.world = world

    def run(self, player: dict, world_state: dict) -> bool:
        Renderer.clear()
        Renderer.title("Lịch Sử Thế Giới")
        fired = world_state.get("events_fired", [])
        if not fired:
            Renderer.line("Chưa có sự kiện nào được ghi lại.")
            Renderer.pause()
            return False
        for event_id in fired:
            event = self.world.events.get(event_id)
            if not event:
                continue
            Renderer.line(
                f"{event['name_vn']} | Năm {event['trigger_year']} tháng {event['trigger_month']} | "
                f"{event['effect_type']} {event['effect_value']}"
            )
            Renderer.line(f"  {event['description']}")
        Renderer.pause()
        return False
