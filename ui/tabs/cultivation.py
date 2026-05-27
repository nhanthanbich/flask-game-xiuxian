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
            Renderer.title("Tu Luyện")
            Renderer.line(f"Linh căn  : {self.cult.root_display(player['root_id'])}")
            Renderer.line(f"Tiến độ   : {self.cult.exp_progress(player)}")
            Renderer.line(f"Thời gian : {time.display()}")
            Renderer.line()

            durations = [1, 3, 6, 12]
            options = [
                f"Ẩn cư {months:2} tháng (+{self.cult.calc_exp(months, player['root_id'])} exp)"
                for months in durations
            ] + ["Quay lại"]
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
            Renderer.line(f"Đã ẩn cư {months} tháng.")
            Renderer.line(f"Nhận được {exp_gain} exp.")
            Renderer.line(f"Thời gian : {time.display()}")

            if self.cult.can_breakthrough(player):
                info = self.cult.get_breakthrough_info(player)
                nxt = info.get("next")
                if nxt:
                    Renderer.line()
                    Renderer.line(f"Đủ điều kiện đột phá lên {nxt['name_vn']}!")
                    Renderer.line(f"Rủi ro thất bại: {int(info.get('risk',0.0)*100)}% | Nếu thất bại: bỏ qua {info.get('failure_skip_months',0)} tháng")
                    choice = Renderer.menu(["Thử đột phá", "Cho sau"])
                    if choice == 0:
                        result = self.cult.attempt_breakthrough(player)
                        if result.get("success"):
                            realm = result["realm"]
                            Renderer.line(f"Đột phá thành công: {realm['name_vn']}")
                            if self.flavor:
                                Renderer.line(self.flavor.get("breakthrough", realm["id"]))
                        else:
                            Renderer.line("Đột phá thất bại!")
                            skip = result.get("failure_skip_months", 0)
                            if skip:
                                time.advance_months(skip)
                                Renderer.line(f"Đã mất {skip} tháng do thất bại.")
                            if result.get("message"):
                                Renderer.line(result.get("message"))
            Renderer.pause()
