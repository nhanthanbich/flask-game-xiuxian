"""
Cultivation tab.
"""

from ui.renderer import Renderer


class CultivationTab:
    def __init__(self, cultivation, flavor=None):
        self.cult = cultivation
        self.flavor = flavor

    def run(self, player: dict, time) -> bool:
        changed = False
        while True:
            Renderer.clear()
            Renderer.title("Tu Luyen")
            Renderer.line(f"Linh can  : {self.cult.root_display(player['root_id'])}")
            Renderer.line(f"Tien do   : {self.cult.exp_progress(player)}")
            Renderer.line(f"Thoi gian : {time.display()}")
            Renderer.line()

            durations = [1, 3, 6, 12]
            options = [
                f"An cu {months:2} thang (+{self.cult.calc_exp(months, player['root_id'])} exp)"
                for months in durations
            ] + ["Quay lai"]
            choice = Renderer.menu(options)
            if choice == len(durations):
                return changed

            months = durations[choice]
            exp_gain = self.cult.calc_exp(months, player["root_id"])
            time.advance_months(months)
            player["exp"] += exp_gain
            changed = True

            Renderer.clear()
            if self.flavor:
                Renderer.line(self.flavor.get("cultivation", player["realm_id"]))
            Renderer.line(f"Da an cu {months} thang.")
            Renderer.line(f"Nhan duoc {exp_gain} exp.")
            Renderer.line(f"Thoi gian : {time.display()}")

            if self.cult.can_breakthrough(player):
                info = self.cult.get_breakthrough_info(player)
                nxt = info.get("next")
                if nxt:
                    Renderer.line()
                    Renderer.line(f"Du dieu kien dot pha len {nxt['name_vn']}!")
                    Renderer.line(f"Rui ro that bai: {int(info.get('risk',0.0)*100)}% | Neu that bai: bo qua {info.get('failure_skip_months',0)} thang")
                    choice = Renderer.menu(["Thu dot pha", "Cho sau"])
                    if choice == 0:
                        result = self.cult.attempt_breakthrough(player)
                        if result.get("success"):
                            realm = result["realm"]
                            Renderer.line(f"Dot pha thanh cong: {realm['name_vn']}")
                            if self.flavor:
                                Renderer.line(self.flavor.get("breakthrough", realm["id"]))
                        else:
                            Renderer.line("Dot pha that bai!")
                            skip = result.get("failure_skip_months", 0)
                            if skip:
                                time.advance_months(skip)
                                Renderer.line(f"Da mat {skip} thang do that bai.")
                            if result.get("message"):
                                Renderer.line(result.get("message"))
            Renderer.pause()
