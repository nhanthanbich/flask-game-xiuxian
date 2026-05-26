"""
Main game loop.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engine.core.event_bus import EventBus
from engine.core.flavor import FlavorSystem
from engine.core.loader import Loader
from engine.core.save_manager import SaveManager
from engine.systems.combat import CombatSystem
from engine.systems.cultivation import CultivationSystem
from engine.systems.item import ItemSystem
from engine.systems.npc import NPCSystem
from engine.systems.technique import TechniqueSystem
from engine.systems.time import TimeSystem
from engine.systems.world import WorldSystem
from ui.combat.screen import CombatScreen
from ui.renderer import Renderer
from ui.tabs.cultivation import CultivationTab
from ui.tabs.inventory import InventoryTab
from ui.tabs.relations import RelationTab
from ui.tabs.sect import SectTab
from ui.tabs.techniques import TechniqueTab
from ui.tabs.timeline import TimelineTab
from ui.tabs.world import WorldTab

ROOTS_PATH = "data/entities/spiritual_roots.csv"
ENEMIES_PATH = "data/entities/enemies.csv"


class Game:
    def __init__(self):
        self.settings = Loader.load_settings()
        self.event_bus = EventBus()
        self.flavor = FlavorSystem()

        self.cult = CultivationSystem(self.settings)
        self.tech = TechniqueSystem()
        self.items = ItemSystem()
        self.combat = CombatSystem(self.settings)
        self.world = WorldSystem(self.settings)
        self.npc = NPCSystem()

        self._wire_events()

        self.cult_tab = CultivationTab(self.cult, self.flavor)
        self.tech_tab = TechniqueTab(self.tech)
        self.world_tab = WorldTab(self.world, self.npc)
        self.sect_tab = SectTab(self.world, self.npc, self.tech)
        self.relation_tab = RelationTab(self.npc)
        self.inventory_tab = InventoryTab(self.items)
        self.timeline_tab = TimelineTab(self.world)
        self.combat_ui = CombatScreen(self.combat, self.tech, self.flavor)

        self.time = TimeSystem()
        self.player = {}
        self.world_state = self.world.default_state()
        self.active_slot = None

    def _wire_events(self):
        self.event_bus.subscribe("time_tick", self.world.on_time_tick)
        self.event_bus.subscribe("join_sect", self.npc.on_join_sect)
        self.event_bus.subscribe("breakthrough", self.npc.on_breakthrough)
        self.event_bus.subscribe("combat_win", self.npc.on_combat_win)
        self.event_bus.subscribe("gift", self.npc.on_gift)

    def run(self):
        Renderer.clear()
        Renderer.title("Tu Tien Ky - Khoi Nguyen")
        Renderer.line("Thien dia linh khi, van vat sinh truong...")
        Renderer.line()

        has_save = SaveManager.any_save()
        options = ["Tiep tuc", "Tao nhan vat moi", "Thoat"] if has_save else ["Tao nhan vat moi", "Thoat"]
        choice = Renderer.menu(options)

        if has_save:
            if choice == 0 and not self._load_menu():
                return
            if choice == 1:
                self._create_character()
            if choice == 2:
                return
        else:
            if choice == 0:
                self._create_character()
            else:
                return
        self._main_loop()

    def _create_character(self):
        Renderer.clear()
        Renderer.title("Tao Nhan Vat")
        while True:
            name = input("  Ten nhan vat: ").strip()
            if name:
                break
            Renderer.line("Hay nhap ten.")

        roots = Loader.load(ROOTS_PATH)
        options = [
            f"{r['name_vn']:14} | {r['element']:4} | x{r['exp_multiplier']} exp | {r['description'][:36]}"
            for r in roots
        ]
        chosen_root = roots[Renderer.menu(options)]

        if not Renderer.confirm(f"Bat dau voi {chosen_root['name_vn']}?"):
            self._create_character()
            return

        self.player = {
            "name": name,
            "realm_id": "mortal",
            "root_id": chosen_root["id"],
            "exp": 0,
            "technique_slots": [None, None, None, None],
            "inventory": {},
        }
        self.items.add_to_inventory(self.player, "minor_heal_pill", 2)
        self.items.add_to_inventory(self.player, "minor_mp_pill", 1)
        self.time = TimeSystem(year=1, month=1, day=1)
        self.world_state = self.world.default_state()
        self.active_slot = self._pick_save_slot()
        self._save_game()
        Renderer.line(f"Chao mung, {name}!")
        Renderer.pause()

    def _main_loop(self):
        while True:
            Renderer.clear()
            title = f"{self.player['name']} | {self.cult.realm_display(self.player['realm_id'])} | {self.time.display()}"
            if self.world_state.get("player_sect"):
                title += f" | {self.world.sects[self.world_state['player_sect']]['name_vn']}"
            Renderer.title(title)
            Renderer.line(self.cult.exp_progress(self.player))
            Renderer.line()

            options = [
                Renderer.t("menu_cultivate"),
                Renderer.t("menu_techniques"),
                Renderer.t("menu_world"),
                Renderer.t("menu_sect"),
                Renderer.t("menu_relations"),
                Renderer.t("menu_inventory"),
                Renderer.t("menu_timeline"),
                Renderer.t("menu_combat"),
                Renderer.t("menu_status"),
                Renderer.t("menu_save"),
                Renderer.t("menu_exit"),
            ]
            choice = Renderer.menu(options)

            if choice == 0:
                old_realm = self.player["realm_id"]
                changed = self.cult_tab.run(self.player, self.time)
                if changed:
                    self._publish_time_tick()
                    if self.player["realm_id"] != old_realm:
                        self.event_bus.publish("breakthrough", {
                            "player": self.player,
                            "realm": self.player["realm_id"],
                            "world_state": self.world_state,
                        })
                    self._save_game()
            elif choice == 1:
                self._save_if(self.tech_tab.run(self.player))
            elif choice == 2:
                changed = self.world_tab.run(self.player, self.world_state)
                if changed and self.world_state.get("player_sect"):
                    self.event_bus.publish("join_sect", {
                        "player": self.player,
                        "sect_id": self.world_state["player_sect"],
                        "world_state": self.world_state,
                    })
                self._save_if(changed)
            elif choice == 3:
                self._save_if(self.sect_tab.run(self.player, self.world_state))
            elif choice == 4:
                self.relation_tab.run(self.player, self.world_state)
            elif choice == 5:
                self._save_if(self.inventory_tab.run(self.player))
            elif choice == 6:
                self.timeline_tab.run(self.player, self.world_state)
            elif choice == 7:
                self._combat_menu()
            elif choice == 8:
                self._show_status()
                Renderer.pause()
            elif choice == 9:
                self._save_menu()
            elif choice == 10:
                if Renderer.confirm("Luu truoc khi thoat?"):
                    self._save_game()
                    Renderer.line("Da luu.")
                Renderer.line("Tam biet tu si...")
                break

    def _combat_menu(self):
        Renderer.clear()
        Renderer.title("Xuat Chinh - Chon Doi Thu")
        enemies = Loader.load(ENEMIES_PATH)
        realm_order = ["mortal", "qi_refining", "foundation", "core_formation", "nascent_soul", "deity_transform", "ascension"]
        cur_idx = realm_order.index(self.player["realm_id"])
        available = [e for e in enemies if realm_order.index(e["realm_id"]) <= cur_idx + 1]
        options = [
            f"{e['name_vn']:18} | {e['element']:5} | HP:{e['hp']:>4} | {e['description'][:30]}"
            for e in available
        ] + ["Quay lai"]
        choice = Renderer.menu(options)
        if choice == len(available):
            return
        if not self.tech.has_any(self.player):
            Renderer.line("Nguoi chua co ky nang nao trong slot.")
            Renderer.pause()
            return

        enemy_id = available[choice]["id"]
        result = self.combat_ui.run(self.player, enemy_id)
        self.time.advance(result.get("time_cost", int(self.settings["combat_time_cost"])))
        self._publish_time_tick()

        if result["result"] == "win":
            self.player["exp"] += result["exp"]
            self.event_bus.publish("combat_win", {
                "player": self.player,
                "enemy_id": enemy_id,
                "drop": result.get("drop"),
                "world_state": self.world_state,
            })
            Renderer.line(f"Tong exp: {self.player['exp']:,}")
            info = self.cult.get_breakthrough_info(self.player)
            if info.get("ready"):
                nxt = info.get("next")
                Renderer.line(f"Du dieu kien dot pha len {nxt['name_vn']}!")
                if Renderer.confirm("Dot pha ngay?"):
                    res = self.cult.attempt_breakthrough(self.player)
                    if res.get("success"):
                        realm = res["realm"]
                        self.event_bus.publish("breakthrough", {
                            "player": self.player,
                            "realm": realm,
                            "world_state": self.world_state,
                        })
                        Renderer.line(self.flavor.get("breakthrough", realm["id"]))
                    else:
                        skip = res.get("failure_skip_months", 0)
                        if skip:
                            self.time.advance_months(skip)
                            self._publish_time_tick()
                        Renderer.line(res.get("message", "Dot pha that bai"))
        elif result["result"] == "lose":
            self.event_bus.publish("combat_lose", {"player": self.player, "enemy_id": enemy_id})
        self._save_game()
        Renderer.pause()

    def _publish_time_tick(self):
        data = {"time": self.time, "world_state": self.world_state, "logs": []}
        self.event_bus.publish("time_tick", data)
        if data.get("logs"):
            Renderer.title("Bien Dong The Gioi")
            for log in data["logs"]:
                Renderer.line(log)
            Renderer.pause()

    def _show_status(self):
        Renderer.clear()
        Renderer.title("Thong Tin Tu Si")
        realm = self.cult.realms[self.player["realm_id"]]
        root = self.cult.roots[self.player["root_id"]]
        sect_id = self.world_state.get("player_sect")
        sect_name = self.world.sects[sect_id]["name_vn"] if sect_id else "Chua co"
        Renderer.line(f"Ten        : {self.player['name']}")
        Renderer.line(f"Canh gioi  : {realm['name_vn']} ({realm['name']})")
        Renderer.line(f"Linh can   : {root['name_vn']} - {root['element']} he")
        Renderer.line(f"Mon phai   : {sect_name}")
        Renderer.line(f"Tien do    : {self.cult.exp_progress(self.player)}")
        Renderer.line(f"Thoi gian  : {self.time.display_full()}")
        Renderer.line()
        Renderer.title("Ky Nang Hien Co")
        for line in self.tech.get_slot_display(self.player):
            Renderer.line(line)

    def _slot_line(self, s: dict) -> str:
        if s["empty"]:
            return f"Slot {s['slot']} - trong"
        realm_name = self.cult.realms.get(s["realm_id"], {}).get("name_vn", s["realm_id"])
        return f"Slot {s['slot']} {s['name']:14} | {realm_name:12} | {s['game_time']} (luu: {s['saved_at']})"

    def _load_menu(self) -> bool:
        Renderer.clear()
        Renderer.title("Chon Save De Tiep Tuc")
        slots = SaveManager.slot_list()
        filled = [s for s in slots if not s["empty"]]
        choice = Renderer.menu([self._slot_line(s) for s in filled] + ["Quay lai"])
        if choice == len(filled):
            return False
        chosen = filled[choice]
        data = SaveManager.load(chosen["slot"])
        self.player = data["player"]
        self.time = TimeSystem.from_dict(data["time"])
        self.world_state = self.world.ensure_state(data.get("world_state"))
        self.active_slot = chosen["slot"]
        self._ensure_player_defaults()
        Renderer.line(f"Da load slot {chosen['slot']}: {self.player['name']}")
        Renderer.pause()
        return True

    def _save_menu(self):
        Renderer.clear()
        Renderer.title("Luu Game")
        slots = SaveManager.slot_list()
        choice = Renderer.menu([self._slot_line(s) for s in slots] + ["Huy"])
        if choice == len(slots):
            return
        target = slots[choice]
        if not target["empty"] and not Renderer.confirm(f"Ghi de Slot {target['slot']}?"):
            return
        self.active_slot = target["slot"]
        self._save_game()
        Renderer.line(f"Da luu vao Slot {self.active_slot}.")
        Renderer.pause()

    def _pick_save_slot(self) -> int:
        slots = SaveManager.slot_list()
        choice = Renderer.menu([self._slot_line(s) for s in slots])
        return slots[choice]["slot"]

    def _save_game(self):
        if self.active_slot is None:
            self.active_slot = 1
        self._ensure_player_defaults()
        time_dict = self.time.to_dict()
        time_dict["display_short"] = self.time.display_short()
        SaveManager.save(self.active_slot, self.player, time_dict, self.world_state)

    def _save_if(self, changed: bool):
        if changed:
            self._save_game()

    def _ensure_player_defaults(self):
        self.tech.ensure_slots(self.player)
        self.items.ensure_inventory(self.player)
