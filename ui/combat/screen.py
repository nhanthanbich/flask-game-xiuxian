"""
Turn-based combat screen.
"""

from ui.renderer import Renderer


class CombatScreen:
    def __init__(self, combat, technique, flavor=None):
        self.combat = combat
        self.tech = technique
        self.flavor = flavor

    def run(self, player: dict, enemy_id: str) -> dict:
        self.tech.ensure_slots(player)
        p_state = self.combat.spawn_player_combat(player)
        e_state = self.combat.spawn_enemy(enemy_id)

        Renderer.clear()
        Renderer.title("Chien Dau Bat Dau")
        Renderer.line(f"{player['name']} VS {e_state['name']}")
        Renderer.pause()

        turn = 1
        while True:
            self._draw_status(player, p_state, e_state, turn)
            tid = self._pick_technique(player, p_state)
            if tid is None:
                Renderer.line("Nguoi roi khoi tran chien.")
                Renderer.pause()
                return {"result": "flee", "exp": 0, "time_cost": int(self.combat.settings["flee_time_cost"])}
            if tid == "__recover__":
                self.combat._regen_mp(p_state)
                Renderer.line("Nguoi dieu tuc mot luot de hoi phuc linh luc.")
            else:
                self._print_logs(self.combat.player_turn(tid, p_state, e_state))

            result = self.combat.is_over(p_state, e_state)
            if result:
                break

            self._print_logs(self.combat.enemy_skill_turn(e_state, p_state, self.tech.techniques))
            result = self.combat.is_over(p_state, e_state)
            if result:
                break

            turn += 1
            Renderer.pause()

        return self._outro(player, result, e_state)

    def _draw_status(self, player: dict, p: dict, e: dict, turn: int):
        Renderer.clear()
        Renderer.title(f"Luot {turn}")
        Renderer.line(f"{player['name']:16} HP {self._bar(p['hp'], p['hp_max'])} {p['hp']}/{p['hp_max']}")
        Renderer.line(f"{'':16} MP {self._bar(p['mp'], p['mp_max'], '=')} {p['mp']}/{p['mp_max']}")
        Renderer.line()
        Renderer.line(f"{e['name']:16} HP {self._bar(e['hp'], e['hp_max'])} {e['hp']}/{e['hp_max']}")
        Renderer.line(f"{'':16} MP {self._bar(e['mp'], e['mp_max'], '=')} {e['mp']}/{e['mp_max']}")
        Renderer.line()

    def _pick_technique(self, player: dict, p_state: dict) -> str | None:
        slots = player.get("technique_slots", [])
        options = []
        tids = []
        has_affordable = False
        for tid in slots:
            if tid and tid in self.tech.techniques:
                tech = self.tech.techniques[tid]
                mp_ok = p_state["mp"] >= int(tech.get("mp_cost", 10))
                has_affordable = has_affordable or mp_ok
                suffix = "" if mp_ok else " [thieu MP]"
                options.append(
                    f"{tech.get('name_vn', tid):18} | {tech.get('element', 'None'):5} | MP:{tech.get('mp_cost', 10):2}{suffix}"
                )
                tids.append(tid)
        if not options:
            Renderer.line("Khong co ky nang nao trong slot.")
            Renderer.pause()
            return None
        if not has_affordable:
            Renderer.line("Tat ca ky nang deu thieu MP.")
            Renderer.pause()
            return "__recover__"
        options.append("Bo chay")
        choice = Renderer.menu(options)
        if choice == len(tids):
            return None
        if p_state["mp"] < int(self.tech.techniques[tids[choice]].get("mp_cost", 10)):
            return "__recover__"
        return tids[choice]

    def _outro(self, player: dict, result: str, e_state: dict) -> dict:
        Renderer.line()
        drop = None
        if result == "win":
            Renderer.line(f"Chien thang! Nhan {e_state['exp']} exp.")
            if self.flavor:
                Renderer.line(self.flavor.get("combat_win", player["realm_id"]))
            drop = self.combat.calc_drop(e_state)
            if drop and drop in self.tech.techniques:
                tech = self.tech.techniques[drop]
                Renderer.line(f"Nhan duoc cong phap roi: {tech.get('name_vn', drop)}.")
                if Renderer.confirm("Hoc ngay?"):
                    self._learn_drop(player, drop)
        else:
            Renderer.line("That bai.")
            if self.flavor:
                Renderer.line(self.flavor.get("combat_lose", player["realm_id"]))
        Renderer.pause()
        return {
            "result": result,
            "exp": e_state["exp"] if result == "win" else 0,
            "time_cost": int(self.combat.settings["combat_time_cost"]),
            "drop": drop,
        }

    def _learn_drop(self, player: dict, technique_id: str):
        slot_options = self.tech.get_slot_display(player) + ["Huy"]
        choice = Renderer.menu(slot_options)
        if choice < len(player["technique_slots"]):
            self.tech.learn(player, technique_id, choice)
            Renderer.line("Da hoc cong phap moi.")

    @staticmethod
    def _print_logs(logs: list[str]):
        Renderer.line()
        for log in logs:
            Renderer.line(log)

    @staticmethod
    def _bar(current: int, maximum: int, char: str = "#", length: int = 15) -> str:
        if maximum <= 0:
            return "." * length
        filled = int(max(current, 0) / maximum * length)
        return char * filled + "." * (length - filled)
