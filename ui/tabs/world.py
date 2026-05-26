"""
World map and sect browser tab.
"""

from ui.renderer import Renderer


class WorldTab:
    def __init__(self, world, npc):
        self.world = world
        self.npc = npc

    def run(self, player: dict, world_state: dict) -> bool:
        changed = False
        while True:
            Renderer.clear()
            Renderer.title("The Gioi")
            current = world_state.get("player_sect")
            if current:
                sect = self.world.sects[current]
                Renderer.line(f"Mon phai hien tai: {sect['name_vn']} (cap {world_state.get('player_rank', 0)})")
            else:
                Renderer.line("Mon phai hien tai: chua gia nhap")
            Renderer.line()

            options = [
                "Xem danh sach mon phai",
                "Gia nhap mon phai",
                "Roi mon phai",
                "Su kien lich su",
                "Quay lai",
            ]
            choice = Renderer.menu(options)

            if choice == 0:
                self._show_sects(world_state)
            elif choice == 1:
                changed = self._join(player, world_state) or changed
            elif choice == 2:
                changed = self._leave(player, world_state) or changed
            elif choice == 3:
                self._show_events(world_state)
            else:
                return changed

    def _show_sects(self, world_state: dict):
        Renderer.clear()
        Renderer.title("Ban Do Mon Phai")
        for sect in self.world.sects.values():
            power = world_state["sect_power"].get(sect["id"], 50)
            npc_count = len([n for n in self.npc.npcs.values() if n["sect_id"] == sect["id"]])
            Renderer.line(
                f"{sect['name_vn']:16} | {sect['element']:4} | {sect['faction']:5} | "
                f"The luc {power:3}/100 | NPC {npc_count} | {sect['location']}"
            )
            Renderer.line(f"  {sect['description']}")
        Renderer.pause()

    def _join(self, player: dict, world_state: dict) -> bool:
        if world_state.get("player_sect"):
            Renderer.line("Nguoi da co mon phai.")
            Renderer.pause()
            return False

        available = self.world.get_available_sects(player)
        if not available:
            Renderer.line("Chua co mon phai phu hop canh gioi.")
            Renderer.pause()
            return False

        Renderer.clear()
        Renderer.title("Gia Nhap Mon Phai")
        options = [
            f"{s['name_vn']:16} | {s['element']:4} | yeu cau {s['min_realm']}"
            for s in available
        ] + ["Huy"]
        choice = Renderer.menu(options)
        if choice == len(available):
            return False

        sect = available[choice]
        if not Renderer.confirm(f"Gia nhap {sect['name_vn']}?"):
            return False

        if not self.world.join_sect(player, world_state, sect["id"]):
            Renderer.line("Khong the gia nhap mon phai nay.")
            Renderer.pause()
            return False

        for npc in self.npc.get_npcs_in_sect(sect["id"]):
            self.npc.remember(player, npc["id"], "join_sect", world_state)
        Renderer.line(f"Da gia nhap {sect['name_vn']}.")
        Renderer.pause()
        return True

    def _leave(self, player: dict, world_state: dict) -> bool:
        sect_id = world_state.get("player_sect")
        if not sect_id:
            Renderer.line("Nguoi chua co mon phai.")
            Renderer.pause()
            return False
        sect = self.world.sects[sect_id]
        if not Renderer.confirm(f"Roi {sect['name_vn']}?"):
            return False
        self.world.leave_sect(player, world_state)
        Renderer.line("Da roi mon phai.")
        Renderer.pause()
        return True

    def _show_events(self, world_state: dict):
        Renderer.clear()
        Renderer.title("Su Kien Lich Su")
        fired = world_state.get("events_fired", [])
        if not fired:
            Renderer.line("Chua co su kien lon nao xay ra.")
        for event_id in fired:
            event = self.world.events.get(event_id)
            if event:
                Renderer.line(f"{event['name_vn']} - nam {event['trigger_year']}/{event['trigger_month']}")
                Renderer.line(f"  {event['description']}")
        Renderer.pause()
