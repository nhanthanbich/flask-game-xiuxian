import os
import random
import secrets

from flask import Flask, redirect, render_template, request, session, url_for

from engine.core.event_bus import EventBus
from engine.core.flavor import FlavorSystem
from engine.core.loader import Loader
from engine.core.save_manager import SaveManager
from engine.systems.combat import CombatSystem
from engine.systems.cultivation import CultivationSystem
from engine.systems.item import ItemSystem
from engine.systems.npc import NPCSystem
from engine.systems.race import RaceSystem
from engine.systems.technique import REALM_ORDER, TechniqueSystem
from engine.systems.time import TimeSystem
from engine.systems.world import WorldSystem

ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-" + secrets.token_hex(16))

settings = Loader.load_settings()
flavor = FlavorSystem()
cult = CultivationSystem(settings)
tech = TechniqueSystem()
items = ItemSystem()
combat = CombatSystem(settings)
world = WorldSystem(settings)
npc = NPCSystem()
races = RaceSystem()
event_bus = EventBus()
event_bus.subscribe("time_tick", world.on_time_tick)
event_bus.subscribe("join_sect", npc.on_join_sect)
event_bus.subscribe("breakthrough", npc.on_breakthrough)
event_bus.subscribe("combat_win", npc.on_combat_win)

ROOTS_PATH = "data/entities/spiritual_roots.csv"
ENEMIES_PATH = "data/entities/enemies.csv"


def translate_entry_condition(conditions_str):
    """Translate entry condition codes into readable Vietnamese text."""
    if not conditions_str:
        return "Không có điều kiện đặc biệt."

    conditions = [c.strip() for c in conditions_str.split(',') if c.strip()]
    translations = []

    for cond in conditions:
        if cond == "linh_can_match":
            translations.append("Linh căn phù hợp nguyên tố môn phái")
        elif cond == "quest_and_realm":
            translations.append("Hoàn thành nhiệm vụ thử luyện")
        elif cond == "always":
            translations.append("Không có điều kiện đặc biệt")
        elif "Tiêu diệt" in cond or "Thắng" in cond or "Đánh bại" in cond:
            # Already Vietnamese
            translations.append(cond)
        elif "advance_months" in cond:
            translations.append("Tĩnh tâm tu luyện không间断")
        elif "quan hệ" in cond.lower() or "Đạt quan hệ" in cond:
            translations.append(cond)
        elif "Có ít nhất" in cond:
            translations.append(cond)
        elif "HP xuống dưới" in cond:
            translations.append(cond)
        else:
            # Keep as-is if it's already Vietnamese or unknown
            translations.append(cond)

    return "; ".join(translations) if translations else "Không có điều kiện đặc biệt."


def default_player(root_id="metal", race_id="human", name="Tan Tu"):
    return {
        "name": name,
        "realm_id": "mortal",
        "root_id": root_id,
        "race_id": race_id,
        "age": 15,
        "gender": "Nam",
        "exp": 0,
        "technique_slots": [None, None, None, None],
        "inventory": {"red_restoration": 1, "qi_pill_minor": 2},
    }


def start_menu():
    slots = SaveManager.slot_list()
    save_rows = []
    for slot in slots:
        if slot["empty"]:
            save_rows.append(
                f"<div class='slot-card'>"
                f"<span class='slot-number'>{slot['slot']}</span>"
                f"<div class='slot-header'><h3 class='slot-title'>Tu Tiên Sơ Trưởng</h3>"
                f"<p class='slot-status'>Trống Rỗng</p></div>"
                f"<div class='slot-actions'>"
                f"<button class='btn' disabled>Tiếp Tục</button>"
                f"</div></div>"
            )
        else:
            realm_name = cult.realms.get(slot['realm_id'], {}).get('name_vn', slot['realm_id'])
            save_rows.append(
                f"<div class='slot-card' id='slot-{slot['slot']}'>"
                f"<span class='slot-number'>{slot['slot']}</span>"
                f"<div class='slot-header'><h3 class='slot-title'>{slot['name']}</h3>"
                f"<p class='slot-status active'>{realm_name}</p></div>"
                f"<p class='slot-meta'>{slot['game_time']} - Lưu lúc {slot['saved_at']}</p>"
                f"<div class='slot-actions'>"
                f"<form method='post' action='{url_for('load_save', slot=slot['slot'])}'>"
                f"<button class='btn btn-load'>Tiếp Tục</button>"
                f"</form>"
                f"<button class='btn btn-delete' onclick=\"confirmDelete({slot['slot']}, '{slot['name']}')\">Xóa</button>"
                f"</div></div>"
            )
    new_game_button = (
        f"<div class='slot-card'>"
        f"<span class='slot-number'>+</span>"
        f"<div class='slot-header'><h3 class='slot-title'>Khởi Đạo Trường</h3>"
        f"<p class='slot-status'>Bắt đầu hành trình mới</p></div>"
        f"<div class='slot-actions'>"
        f"<form method='get' action='{url_for('new_game')}' style='width: 100%;'>"
        f"<button class='btn btn-new'>Nhập Thế</button>"
        f"</form></div></div>"
    )

    # Add confirm script
    confirm_script = """
    <script>
    function confirmDelete(slot, name) {
        if (confirm('Bạn có chắc muốn xóa save slot ' + slot + ' (' + name + ')?\\nHành động này không thể hoàn tác!')) {
            // Create form and submit
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/delete/' + slot;
            document.body.appendChild(form);
            form.submit();
        }
    }
    </script>
    """

    return render_template("start.html", content=new_game_button + ''.join(save_rows) + confirm_script)


def _random_root() -> str:
    five_elements_id = next(
        (root_id for root_id, root in cult.roots.items() if root.get("element") == "Ngũ Hành"),
        None,
    )
    normal_roots = [root_id for root_id, root in cult.roots.items() if root.get("element") != "Ngũ Hành"]
    if five_elements_id is None or not normal_roots:
        return random.choice(list(cult.roots.keys()))
    if random.random() < 0.05:
        return five_elements_id
    return random.choice(normal_roots)


def new_player_state(root_id: str, race_id: str = "human"):
    return {
        "player": default_player(root_id=root_id, race_id=race_id),
        "time": TimeSystem().to_dict(),
        "world_state": world.default_state(),
        "logs": ["Bắt đầu hành trình tu tiên."],
        "combat_state": None,
        "secret_state": None,
    }


@app.get("/new")
def new_game():
    race_order = ["human", "mo", "yao"]
    races_data = {}

    for rid in race_order:
        if rid in races.races:
            race = races.races[rid]

            # Calculate stat percentages based on CSV multipliers
            if rid == "human":
                talent_percent = 80
                power_percent = 40
                vitality_percent = 45
            elif rid == "mo":
                talent_percent = 35
                power_percent = 90
                vitality_percent = 40
            elif rid == "yao":
                talent_percent = 40
                power_percent = 50
                vitality_percent = 85
            else:
                talent_percent = 50
                power_percent = 50
                vitality_percent = 50

            races_data[rid] = {
                "name_vn": race["name_vn"],
                "element": race.get("element", "Trung lập"),
                "description": race["description"],
                "talent_percent": talent_percent,
                "power_percent": power_percent,
                "vitality_percent": vitality_percent,
            }

    return render_template("new_game.html", races_data=races_data)


@app.post("/new/<race_id>")
def create_game(race_id):
    if race_id not in races.races:
        return redirect(url_for("new_game"))
    root_id = _random_root()
    session["pending_game"] = new_player_state(root_id, race_id=race_id)
    session.modified = True
    return redirect(url_for("confirm_game"))


@app.get("/confirm")
def confirm_game():
    pending = session.get("pending_game")
    if not pending:
        return redirect(url_for("index"))
    player = pending["player"]
    root = cult.roots[player["root_id"]]
    race = races.races[player["race_id"]]

    # Determine rarity
    rarity_color = "#4fd1a5"
    rarity_text = "Phàm Căn"
    if root.get("element") == "Ngũ Hành":
        rarity_color = "#ffc847"
        rarity_text = "Thiên Phẩm Linh Căn"

    context = {
        "player": player,
        "root": root,
        "race": race,
        "rarity_color": rarity_color,
        "rarity_text": rarity_text,
    }
    return render_template("confirm.html", **context)


@app.post("/confirm")
def confirm_game_submit():
    pending = session.pop("pending_game", None)
    if not pending:
        return redirect(url_for("index"))

    player_name = request.form.get("player_name", "").strip()
    if not player_name:
        player_name = "Tan Tu"

    player_gender = request.form.get("player_gender", "Nam").strip() or "Nam"

    pending["player"]["name"] = player_name
    pending["player"]["gender"] = player_gender
    pending["player"]["age"] = 15
    pending["player"]["race_confirmed"] = True

    session["game"] = pending
    session.modified = True
    return redirect(url_for("game"))


@app.post("/cancel_new")
def cancel_new_game():
    session.pop("pending_game", None)
    session.modified = True
    return redirect(url_for("index"))

def load_save_state(slot: int):
    data = SaveManager.load(slot)
    if not data:
        return None
    session["game"] = {
        "player": data.get("player", default_player()),
        "time": data.get("time", TimeSystem().to_dict()),
        "world_state": data.get("world_state", world.default_state()),
        "logs": [f"Đã load save slot {slot}."],
        "combat_state": None,
        "secret_state": None,
    }
    ensure_defaults(session["game"])
    return session["game"]


def default_state():
    return {
        "player": default_player(),
        "time": TimeSystem().to_dict(),
        "world_state": world.default_state(),
        "logs": ["Bắt đầu hành trình tu tiên."],
        "combat_state": None,
        "secret_state": None,
    }


def get_state():
    if "game" not in session:
        return None
    state = session["game"]
    ensure_defaults(state)
    return state


def save_state(state):
    session["game"] = state
    session.modified = True


def ensure_defaults(state):
    state.setdefault("player", default_player())
    state.setdefault("time", TimeSystem().to_dict())
    state["world_state"] = world.ensure_state(state.get("world_state"))
    state.setdefault("logs", [])
    state.setdefault("combat_state", None)
    state.setdefault("secret_state", None)
    tech.ensure_slots(state["player"])
    items.ensure_inventory(state["player"])
    state["player"].setdefault("race_id", "human")
    state["player"].setdefault("race_confirmed", True)
    state["player"].setdefault("age", 15)
    state["player"].setdefault("gender", "Nam")
    state["player"].setdefault("realm_id", "mortal")
    state["player"].setdefault("cultivation_pressure", 0)
    state["player"].setdefault("breakthrough_ready", False)
    state["player"].setdefault("breakthrough_risk", 0)
    state["world_state"].setdefault("npc_events_fired", [])
    state["world_state"].setdefault("world_history", [])


def get_breakthrough_block_reason(state):
    if state.get("combat_state"):
        return "Không thể đột phá khi đang trong chiến đấu."
    if state.get("secret_state"):
        return "Không thể đột phá trong lúc thám hiểm bí cảnh."
    if world.has_ready_sect_task(state["player"], state["world_state"]):
        return "Hoàn thành nhiệm vụ môn phái đã sẵn sàng trước khi đột phá."
    return ""


def current_time(state):
    return TimeSystem.from_dict(state["time"])


def set_time(state, time):
    state["time"] = time.to_dict()
    state["time"]["display_short"] = time.display_short()


def log(state, text):
    state["logs"].append(text)
    if len(state["logs"]) > 80:
        del state["logs"][:-80]


def tick_time(state, time):
    data = {"time": time, "world_state": state["world_state"], "logs": []}
    event_bus.publish("time_tick", data)
    for line in data.get("logs", []):
        log(state, "Sự kiện: " + line)

    # Process NPC timelines
    npc_events = npc.process_npc_timelines(time.year, state)
    for event in npc_events:
        log(state, "— Tin tức từ giang hồ — " + event)


def render_page(tab, body):
    state = get_state()
    player = state["player"]
    realm = cult.realms[player["realm_id"]]
    root = cult.roots[player["root_id"]]
    race = races.get(player.get("race_id", "human"))
    nxt = cult.next_realm(player["realm_id"])
    progress = 100 if not nxt else min(100, int(player["exp"] / int(nxt["exp_required"]) * 100))
    sect_id = state["world_state"].get("player_sect")
    sect_name = world.sects[sect_id]["name_vn"] if sect_id else "Tán tu"
    tabs = [
        ("cultivate", "Tu luyện"),
        ("techniques", "Công pháp"),
        ("world", "Tông môn"),
        ("secret", "Bí cảnh"),
        ("combat", "Chiến đấu"),
        ("inventory", "Túi đồ"),
        ("relations", "NPC"),
        ("timeline", "Lịch sử"),
    ]
    context = {
        "body": body,
        "player": player,
        "realm": realm,
        "root": root,
        "race": race,
        "time": current_time(state),
        "progress": progress,
        "progress_max": 100,
        "sect_name": sect_name,
        "tabs": tabs,
        "tab": tab,
        "logs": state["logs"][-40:],
        "combat_state": state.get("combat_state"),
        "secret_state": state.get("secret_state"),
        "world_state": state["world_state"],
    }
    return render_template("game.html", **context)


@app.get("/")
def index():
    if "pending_game" in session:
        return confirm_game()
    return start_menu()


@app.get("/back_to_menu")
def back_to_menu():
    session.pop("game", None)
    session.pop("pending_game", None)
    session.modified = True
    return redirect(url_for("index"))


@app.get("/combat")
def combat_alias():
    return redirect(url_for("game", tab="combat"))


@app.get("/game")
def game():
    if "game" not in session:
        if "pending_game" in session:
            return redirect(url_for("confirm_game"))
        return redirect(url_for("index"))
    if "game" not in session:
        return redirect(url_for("index"))
    tab = request.args.get("tab", "cultivate")
    body = {
        "cultivate": view_cultivate,
        "techniques": view_techniques,
        "world": view_world,
        "sect": view_world,
        "secret": view_secret,
        "combat": view_combat,
        "inventory": view_inventory,
        "relations": view_relations,
        "timeline": view_timeline,
        "save": view_save_menu,
    }.get(tab, view_cultivate)()
    return render_page(tab, body)


@app.post("/load/<int:slot>")
def load_save(slot):
    game = load_save_state(slot)
    if not game:
        return "Không tìm thấy save slot.", 404
    return redirect(url_for("game"))


@app.post("/save/<int:slot>")
def save_slot(slot):
    state = get_state()
    if not state:
        return redirect(url_for("game"))
    SaveManager.save(slot, state["player"], state["time"], state["world_state"])
    log(state, f"Lưu game vào slot {slot}.")
    save_state(state)
    return redirect(url_for("game", tab="save"))


@app.post("/delete/<int:slot>")
def delete_save(slot):
    SaveManager.delete(slot)
    state = get_state()
    if state:
        log(state, f"Xóa save slot {slot}.")
        save_state(state)
    return redirect(url_for("game", tab="save"))


@app.get("/save")
def view_save_menu():
    state = get_state()
    if not state:
        return start_menu()
    slots = SaveManager.slot_list()
    rows = []
    for slot in slots:
        if slot["empty"]:
            rows.append(
                f"<div class='card'><h3>Slot {slot['slot']} - TRỐNG</h3>"
                f"<form method='post' action='{url_for('save_slot', slot=slot['slot'])}'><button>Lưu vào slot</button></form>"
                f"<form><button disabled>Xóa</button></form>"
                f"</div>"
            )
        else:
            realm_name = cult.realms.get(slot['realm_id'], {}).get('name_vn', slot['realm_id'])
            rows.append(
                f"<div class='card'><h3>Slot {slot['slot']} - {slot['name']}</h3>"
                f"<p>{realm_name} | {slot['game_time']} | Lưu lúc {slot['saved_at']}</p>"
                f"<form method='post' action='{url_for('load_save', slot=slot['slot'])}'><button>Load</button></form>"
                f"<form method='post' action='{url_for('save_slot', slot=slot['slot'])}'><button>Lưu vào slot</button></form>"
                f"<form method='post' action='{url_for('delete_save', slot=slot['slot'])}'><button>Xóa</button></form>"
                f"</div>"
            )
    return f"<h2>Quản lý Save</h2><div class='grid'>{''.join(rows)}</div>"


@app.post("/cultivate/<int:months>")
def cultivate(months):
    state = get_state()
    player = state["player"]
    time = current_time(state)
    gain = cult.calc_player_exp(months, player, races)
    adjusted_gain, efficiency_message = cult.apply_pressure_to_exp(player, gain)
    player["exp"] += adjusted_gain

    if efficiency_message:
        log(state, efficiency_message)
    if adjusted_gain != gain:
        log(state, f"Hiệu quả tu luyện giảm: {adjusted_gain}/{gain} exp thực nhận.")

    # Add cultivation pressure
    pressure_result = cult.add_cultivation_pressure(player, adjusted_gain)
    if pressure_result.get("flavor"):
        log(state, pressure_result["flavor"])
    if pressure_result.get("event") == "táu_hoả_nhập_ma":
        log(state, "CẢNH BÁO: " + pressure_result["message"])
        # Apply HP loss
        hp_loss = pressure_result["hp_loss_percent"]
        time.advance_months(months)
        tick_time(state, time)
        set_time(state, time)
        save_state(state)
        return redirect(url_for("game", tab="cultivate"))
    elif pressure_result.get("message"):
        log(state, pressure_result["message"])
    else:
        log(state, f"Bế quan {months} tháng, nhận {adjusted_gain} exp.")

    time.advance_months(months)
    tick_time(state, time)
    set_time(state, time)
    save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/breakthrough")
def breakthrough():
    state = get_state()
    player = state["player"]
    time = current_time(state)

    block_reason = get_breakthrough_block_reason(state)
    if block_reason:
        log(state, block_reason)
        save_state(state)
        return redirect(url_for("game", tab="cultivate"))

    # Check pressure requirement
    pressure = player.get("cultivation_pressure", 0)
    if pressure < 80:
        log(state, "Linh lực chưa đủ, cần tu luyện thêm.")
        save_state(state)
        return redirect(url_for("game", tab="cultivate"))

    result = cult.attempt_breakthrough(player, mode="normal")
    if result.get("success"):
        realm = result["realm"]
        event_bus.publish("breakthrough", {"player": player, "realm": realm, "world_state": state["world_state"]})
        if result.get("item_used") and result.get("breakthrough_item"):
            item_name = items.items.get(result["breakthrough_item"], {}).get("name_vn", result["breakthrough_item"])
            log(state, f"Đã sử dụng {item_name} để trợ đột phá.")
        log(state, f"Đột phá thành công lên {realm['name_vn']}!")
        if result.get("lore"):
            log(state, result["lore"])

        # World reaction
        log(state, "— Thiên hạ rúng động —")
        log(state, f"Năm {time.year}, {player['name']} đạt {realm['name_vn']} tại nơi tu hành.")

        if state["world_state"].get("player_sect"):
            sect_id = state["world_state"]["player_sect"]
            sect_boost = random.randint(3, 7)
            state["world_state"]["sect_power"][sect_id] = world._clamp_power(
                state["world_state"]["sect_power"].get(sect_id, 50) + sect_boost
            )
            log(state, f"{world.sects[sect_id]['name_vn']} tự hào, thế lực tăng thêm {sect_boost} điểm.")
        else:
            log(state, "Danh tiếng ngươi vang vọng giang hồ, mọi nơi đều biết đến tên tuổi này.")

        # Add to world history
        if "world_history" not in state["world_state"]:
            state["world_state"]["world_history"] = []
        history_entry = {
            "year": time.year,
            "event": f"{player['name']} đột phá {realm['name_vn']}",
            "detail": f"Cảnh giới mới: {realm['name_vn']}"
        }
        if history_entry not in state["world_state"]["world_history"]:
            state["world_state"]["world_history"].append(history_entry)

        # NPC reactions
        npc_knowledge = npc.process_npc_timelines(time.year, state)
        for event in npc_knowledge:
            log(state, event)

        text = flavor.get("breakthrough", realm["id"])
        if text:
            log(state, text)
    else:
        skip = result.get("failure_skip_months", 0)
        if skip:
            time.advance_months(skip)
            tick_time(state, time)
            set_time(state, time)
        if result.get("hp_loss_percent"):
            log(state, f"{result['message']} Mất {result['hp_loss_percent']}% sinh lực.")
        else:
            log(state, result.get("message", "Đột phá thất bại."))
    save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/breakthrough_seclusion")
def breakthrough_seclusion():
    """Bế quan đột phá - tỷ lệ thành công cao hơn."""
    state = get_state()
    player = state["player"]
    time = current_time(state)

    block_reason = get_breakthrough_block_reason(state)
    if block_reason:
        log(state, block_reason)
        save_state(state)
        return redirect(url_for("game", tab="cultivate"))

    pressure = player.get("cultivation_pressure", 0)
    if pressure < 80:
        log(state, "Linh lực chưa đủ để bế quan đột phá.")
        save_state(state)
        return redirect(url_for("game", tab="cultivate"))

    result = cult.attempt_breakthrough(player, mode="seclusion")
    if result.get("success"):
        realm = result["realm"]
        seclusion_time = result.get("seclusion_time", random.randint(1, 3))

        time.advance_months(seclusion_time)
        tick_time(state, time)
        set_time(state, time)

        if result.get("item_used") and result.get("breakthrough_item"):
            item_name = items.items.get(result["breakthrough_item"], {}).get("name_vn", result["breakthrough_item"])
            log(state, f"Đã sử dụng {item_name} để trợ đột phá.")

        event_bus.publish("breakthrough", {"player": player, "realm": realm, "world_state": state["world_state"]})
        log(state, f"Sau {seclusion_time} tháng bế quan, đột phá thành công lên {realm['name_vn']}!")
        if result.get("lore"):
            log(state, result["lore"])

        if state["world_state"].get("player_sect"):
            sect_id = state["world_state"]["player_sect"]
            sect_boost = random.randint(3, 7)
            state["world_state"]["sect_power"][sect_id] = world._clamp_power(
                state["world_state"]["sect_power"].get(sect_id, 50) + sect_boost
            )
            log(state, f"{world.sects[sect_id]['name_vn']} tự hào, thế lực tăng thêm {sect_boost} điểm.")
        else:
            log(state, "Danh tiếng ngươi vang vọng giang hồ, mọi nơi đều biết đến tên tuổi này.")

        text = flavor.get("breakthrough", realm["id"])
        if text:
            log(state, text)
    else:
        skip = result.get("failure_skip_months", 0)
        if skip:
            time.advance_months(skip)
        tick_time(state, time)
        set_time(state, time)
        if result.get("hp_loss_percent"):
            log(state, f"Bế quan thất bại: {result['message']}")
        else:
            log(state, result.get("message", "Bế quan đột phá thất bại."))
    save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/breakthrough_wait")
def breakthrough_wait():
    """Trì hoãn đột phá - tăng áp lực và rủi ro."""
    state = get_state()
    player = state["player"]
    time = current_time(state)

    block_reason = get_breakthrough_block_reason(state)
    if block_reason:
        log(state, block_reason)
        save_state(state)
        return redirect(url_for("game", tab="cultivate"))

    result = cult.attempt_breakthrough(player, mode="wait")
    danger_risk = result.get("risk", 0)
    delay_months = result.get("advance_months", 1)

    time.advance_months(delay_months)
    tick_time(state, time)
    set_time(state, time)

    if danger_risk > 70:
        log(state, f"CẢNH BÁO ĐỎ: Rủi ro trì hoãn đã đạt {danger_risk}%! Nên đột phá ngay.")
    else:
        log(state, f"Trì hoãn đột phá {delay_months} tháng. {result['message']}")

    save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/learn/<technique_id>")
def learn(technique_id):
    state = get_state()
    player = state["player"]
    slots = player["technique_slots"]
    slot = next((i for i, value in enumerate(slots) if not value), 0)
    tech.learn(player, technique_id, slot)
    log(state, f"Học công pháp {tech.techniques[technique_id]['name_vn']} vào slot {slot + 1}.")
    save_state(state)
    return redirect(request.referrer or url_for("game", tab="techniques"))


@app.post("/join/<sect_id>")
def join(sect_id):
    state = get_state()
    if world.join_sect(state["player"], state["world_state"], sect_id):
        event_bus.publish("join_sect", {"player": state["player"], "sect_id": sect_id, "world_state": state["world_state"]})
        log(state, f"Gia nhập {world.sects[sect_id]['name_vn']}.")
    else:
        log(state, "Không thể gia nhập môn phái này.")
    save_state(state)
    return redirect(url_for("game", tab="world"))


@app.post("/leave")
def leave_sect():
    state = get_state()
    if not state:
        return redirect(url_for("game"))
    if world.leave_sect(state["player"], state["world_state"]):
        log(state, "Đã rời tông môn.")
    else:
        log(state, "Ngươi chưa có tông môn để rời.")
    save_state(state)
    return redirect(url_for("game", tab="world"))


@app.post("/gift/<npc_id>")
def gift_npc(npc_id):
    state = get_state()
    if not state:
        return redirect(url_for("game"))
    n = npc.npcs.get(npc_id)
    if n:
        npc.remember(state["player"], npc_id, "gift", state["world_state"])
        log(state, f"Đã tặng quà cho {n['name_vn']}.")
    else:
        log(state, "Không tìm thấy NPC để tặng quà.")
    save_state(state)
    return redirect(url_for("game", tab="relations"))


@app.post("/race/<race_id>")
def choose_race(race_id):
    state = get_state()
    if state:
        log(state, "Không thể đổi tộc hệ sau khi bắt đầu.")
        save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/promote")
def promote():
    state = get_state()
    if world.promote_player(state["world_state"]):
        log(state, "Hoan thanh nhiem vu mon phai, cap bac tang len.")
    save_state(state)
    return redirect(url_for("game", tab="world"))


@app.post("/quest/<quest_id>")
def complete_quest(quest_id):
    state = get_state()
    ok, message = world.complete_quest(state["player"], state["world_state"], quest_id)
    log(state, message)
    save_state(state)
    return redirect(url_for("game", tab="world"))


@app.post("/secret/<realm_id>")
def explore_secret(realm_id):
    state = get_state()
    player = state["player"]
    secret = world.secret_realms.get(realm_id)
    if not secret or secret not in world.get_available_secret_realms(player):
        log(state, "Bí cảnh chưa phù hợp với cảnh giới hiện tại.")
        return redirect(url_for("game", tab="secret"))
    state["secret_state"] = {
        "id": realm_id,
        "progress": 0,
        "danger": float(secret["risk"]),
        "logs": [f"Ngươi bước vào {secret['name_vn']}."],
    }
    save_state(state)
    return redirect(url_for("game", tab="secret"))


@app.post("/secret_action/<action>")
def secret_action(action):
    state = get_state()
    sstate = state.get("secret_state")
    if not sstate:
        return redirect(url_for("game", tab="secret"))
    secret = world.secret_realms[sstate["id"]]
    if action == "observe":
        sstate["danger"] = max(0.02, sstate["danger"] - 0.04)
        sstate["logs"].append("Ngươi quan sát địa thế, rủi ro giảm xuống.")
    elif action == "retreat":
        log(state, f"NgÆ°Æ¡i rá»i {secret['name_vn']} trÆ°á»›c khi lÃºn sÃ¢u.")
        state["secret_state"] = None
    elif action == "advance":
        import random
        sstate["progress"] += 1
        if random.random() < sstate["danger"]:
            time = current_time(state)
            time.advance_months(max(1, int(secret["time_months"]) // 2))
            tick_time(state, time)
            set_time(state, time)
            log(state, f"Gặp biến cố trong {secret['name_vn']}, thám hiểm thất bại.")
            state["secret_state"] = None
        elif sstate["progress"] >= 3:
            time = current_time(state)
            time.advance_months(int(secret["time_months"]))
            tick_time(state, time)
            set_time(state, time)
            state["player"]["exp"] += int(secret["exp_reward"])
            reward = secret.get("item_reward", "")
            if reward:
                inv = state["player"].setdefault("inventory", {})
                inv[reward] = inv.get(reward, 0) + 1
            log(state, f"Khám phá trọn vẹn {secret['name_vn']}, nhận {secret['exp_reward']} exp.")
            state["secret_state"] = None
        else:
            sstate["logs"].append("Ngươi tiến sâu hơn, linh khí quanh thân dày thêm.")
    save_state(state)
    return redirect(url_for("game", tab="secret"))


@app.post("/use_item/<item_id>")
def use_item(item_id):
    state = get_state()
    log(state, items.use_item(state["player"], item_id))
    save_state(state)
    return redirect(url_for("game", tab="inventory"))


@app.post("/fight/<enemy_id>")
def fight(enemy_id):
    state = get_state()
    player = state["player"]
    if not tech.has_any(player):
        log(state, "Chưa có công pháp trong slot.")
        return redirect(url_for("game", tab="combat"))
    state["combat_state"] = {
        "enemy_id": enemy_id,
        "p_state": combat.spawn_player_combat(player),
        "e_state": combat.spawn_enemy(enemy_id),
        "turn": 1,
        "logs": [f"Bắt đầu giao chiến với {combat.enemies[enemy_id]['name_vn']}."],
    }
    save_state(state)
    return redirect(url_for("game", tab="combat"))


def finish_combat(state, result):
    cstate = state["combat_state"]
    player = state["player"]
    e_state = cstate["e_state"]
    time = current_time(state)
    time.advance(int(settings["combat_time_cost"]))
    tick_time(state, time)
    set_time(state, time)
    if result == "win":
        player["exp"] += e_state["exp"]
        drop = combat.calc_drop(e_state)
        if drop:
            slot = next((i for i, value in enumerate(player["technique_slots"]) if not value), 0)
            tech.learn(player, drop, slot)
        event_bus.publish("combat_win", {
            "player": player,
            "enemy_id": cstate["enemy_id"],
            "drop": drop,
            "world_state": state["world_state"],
        })
        state["world_state"]["combat_wins"] = state["world_state"].get("combat_wins", 0) + 1
        log(state, f"Tháº¯ng {e_state['name']}, nháº­n {e_state['exp']} exp." + (f" Rơi công pháp {drop}." if drop else ""))
    else:
        log(state, f"Thất bại trước {e_state['name']}.")
    state["combat_state"] = None


@app.post("/combat/use/<technique_id>")
def combat_use(technique_id):
    state = get_state()
    cstate = state.get("combat_state")
    if not cstate:
        return redirect(url_for("game", tab="combat"))
    p_state = cstate["p_state"]
    e_state = cstate["e_state"]
    if technique_id not in tech.techniques:
        cstate["logs"].append("Công pháp không tồn tại.")
    elif p_state["mp"] < int(tech.techniques[technique_id]["mp_cost"]):
        combat._regen_mp(p_state)
        cstate["logs"].append("KhÃ´ng Ä‘á»§ MP, ngÆ°Æ¡i Ä‘iá»u tá»©c Ä‘á»ƒ há»“i linh lá»±c.")
    else:
        cstate["logs"].extend(combat.player_turn(technique_id, p_state, e_state))
    result = combat.is_over(p_state, e_state)
    if not result:
        cstate["logs"].extend(combat.enemy_skill_turn(e_state, p_state, tech.techniques))
        result = combat.is_over(p_state, e_state)
    if result:
        finish_combat(state, result)
    else:
        cstate["turn"] += 1
    save_state(state)
    return redirect(url_for("game", tab="combat"))


@app.post("/combat/recover")
def combat_recover():
    state = get_state()
    cstate = state.get("combat_state")
    if cstate:
        combat._regen_mp(cstate["p_state"])
        cstate["logs"].append("NgÆ°Æ¡i lui ná»­a bÆ°á»›c, Ä‘iá»u tá»©c há»“i MP.")
        cstate["logs"].extend(combat.enemy_skill_turn(cstate["e_state"], cstate["p_state"], tech.techniques))
        result = combat.is_over(cstate["p_state"], cstate["e_state"])
        if result:
            finish_combat(state, result)
        else:
            cstate["turn"] += 1
    save_state(state)
    return redirect(url_for("game", tab="combat"))


@app.post("/combat/flee")
def combat_flee():
    state = get_state()
    cstate = state.get("combat_state")
    if cstate:
        time = current_time(state)
        time.advance(int(settings.get("flee_time_cost", 1)))
        tick_time(state, time)
        set_time(state, time)
        log(state, f"NgÆ°Æ¡i rÃºt khá»i tráº­n vá»›i {cstate['e_state']['name']}.")
        state["combat_state"] = None
    save_state(state)
    return redirect(url_for("game", tab="combat"))


def view_cultivate():
    state = get_state()
    player = state["player"]
    current_year = current_time(state).year
    world_events_count = len(state["world_state"].get("events_fired", []))

    # Get pressure status
    pressure_status = cult.get_pressure_status(player)
    pressure = pressure_status["pressure"]
    pressure_status_text = pressure_status["status"]
    breakthrough_risk = pressure_status["breakthrough_risk"]

    info = cult.get_breakthrough_info(player)
    buttons = "".join(
        f'<div class="cultivate-option">'
        f'<div class="option-header">'
        f'<span class="option-icon">🧘</span>'
        f'<span class="option-time">{m} tháng</span>'
        f'</div>'
        f'<div class="option-gain">+{cult.calc_player_exp(m, player, races)} exp</div>'
        f'<form method="post" action="{url_for("cultivate", months=m)}">'
        f'<button class="btn btn-cultivate">Bế Quan</button>'
        f'</form></div>'
        for m in (1, 3, 6, 12)
    )

    # Pressure display
    pressure_color = "var(--jade-essence)" if pressure < 60 else "var(--celestial-gold)" if pressure < 80 else "var(--blood-crystal)"
    pressure_level = "Ổn định" if pressure < 60 else "Cao" if pressure < 80 else "Nguy hiểm" if pressure < 95 else "Cực hạn"

    pressure_requirement = info.get("pressure_required", 0)
    pressure_requirement_text = (
        f'<span>Ngưỡng đột phá hiện tại: {pressure_requirement}%</span>'
        if info.get("next") is not None else
        '<span>Chưa có cảnh giới tiếp theo.</span>'
    )
    pressure_section = f"""
        <div class="pressure-section">
            <h3>Áp Lực Tu Luyện</h3>
            <div class="pressure-bar-container">
                <div class="pressure-bar">
                    <div class="pressure-fill" style="width: {pressure}%; background: {pressure_color};"></div>
                </div>
                <div class="pressure-info">
                    <span class="pressure-value" style="color: {pressure_color};">{pressure}%</span>
                    <span class="pressure-level">{pressure_level}</span>
                </div>
            </div>
            <div class="pressure-meta">
                <span>Năm: {current_year}</span>
                <span>Rủi ro trì hoãn: {breakthrough_risk}%</span>
                <span>Sự kiện thế giới: {world_events_count}</span>
                {pressure_requirement_text}
            </div>
            {f'<p class="pressure-warning" style="color: var(--blood-crystal);">⚠ Rủi ro trì hoãn: {breakthrough_risk}%</p>' if breakthrough_risk > 0 else ''}
        </div>
    """

    breakthrough_button = ""
    breakthrough_block_reason = get_breakthrough_block_reason(state)
    breakthrough_blocked = bool(breakthrough_block_reason)
    assist_item = info.get("breakthrough_item")
    assist_hint = ""
    if assist_item:
        item_name = items.items.get(assist_item, {}).get("name_vn", assist_item)
        item_qty = player.get("inventory", {}).get(assist_item, 0)
        assist_hint = (
            f'<p class="breakthrough-tip">Ngươi có {item_qty} x {item_name}, sẽ được dùng tự động nếu đột phá.</p>'
            if item_qty
            else f'<p class="breakthrough-tip">Thu thập {item_name} để tăng tỷ lệ đột phá.</p>'
        )

    if info.get("ready") and info.get("next"):
        nxt = info["next"]
        risk_percent = int(info["risk"] * 100)
        risk_color = "var(--jade-essence)" if risk_percent < 30 else "var(--celestial-gold)" if risk_percent < 60 else "var(--blood-crystal)"

        pressure_required = info.get("pressure_required", 0)
        can_breakthrough = info.get("ready") and info.get("pressure_ready")
        button_disabled = "disabled" if breakthrough_blocked or not can_breakthrough else ""
        requirement_text = ""
        if pressure_required > 0 and not info.get("pressure_ready"):
            requirement_text = f'<p class="pressure-requirement">Cần áp lực ≥ {pressure_required}% (hiện tại {pressure}%)</p>'

        breakthrough_button = (
            f'<div class="breakthrough-section">'
            f'<div class="breakthrough-header">'
            f'<span class="breakthrough-icon">⚡</span>'
            f'<h3>Đột Phá Đề Trảnh</h3>'
            f'</div>'
            f'<div class="breakthrough-info">'
            f'<p class="breakthrough-target">Thăng cấp: <strong>{nxt["name_vn"]}</strong></p>'
            f'<div class="risk-display">'
            f'<span class="risk-label">Rủi ro cơ bản</span>'
            f'<span class="risk-value" style="color: {risk_color};">{risk_percent}%</span>'
            f'</div>'
            f'{assist_hint}'
            f'</div>'
            f'{requirement_text}'
            f'{f"<p class=\"breakthrough-block\">{breakthrough_block_reason}</p>" if breakthrough_blocked else ""}'
            f'<div class="breakthrough-options">'
            f'<form method="post" action="{url_for("breakthrough")}">'
            f'<button class="btn btn-breakthrough" {button_disabled}>Đột Phá Ngay (60% cơ bản)</button>'
            f'</form>'
            f'<form method="post" action="{url_for("breakthrough_seclusion")}">'
            f'<button class="btn btn-seclusion" {button_disabled}>Bế Quan Đột Phá (85%, tốn thời gian)</button>'
            f'</form>'
            f'<form method="post" action="{url_for("breakthrough_wait")}">'
            f'<button class="btn btn-wait" {"disabled" if breakthrough_blocked else ""}>Chờ Thêm (+5% áp lực, +10% rủi ro)</button>'
            f'</form>'
            f'</div></div>'
        )
    else:
        disabled_message = breakthrough_block_reason or "Chưa đủ tu vi để đột phá"
        breakthrough_button = (
            f'<div class="breakthrough-section disabled">'
            f'<div class="breakthrough-header">'
            f'<span class="breakthrough-icon">🔒</span>'
            f'<h3>Đột Phá Đề Trảnh</h3>'
            f'</div>'
            f'<p class="muted">{disabled_message}</p>'
            f'</div>'
        )
    race = races.get(player.get("race_id", "human"))
    flavor_text = flavor.get('cultivation', player['realm_id']) or "Linh khí thiên địa tụ hội..."

    return f"""
        <div class="cultivation-panel">
            <div class="panel-ornament">
                <span class="ornament-left">❖</span>
                <span class="ornament-title">Tu Luyện Đạo Trưởng</span>
                <span class="ornament-right">❖</span>
            </div>

            <div class="cultivation-env">
                <div class="qi-visualization">
                    <div class="qi-orb"></div>
                    <p class="qi-text">{flavor_text}</p>
                </div>

                <div class="race-info">
                    <span class="race-icon">{'👤' if race['id'] == 'human' else '👿' if race['id'] == 'mo' else '🐉'}</span>
                    <div class="race-desc">
                        <h4 class="race-name">{race['name_vn']}</h4>
                        <p class="race-text">{race['description']}</p>
                    </div>
                </div>
            </div>

            {pressure_section}

            <div class="cultivation-options">
                <h3>Chọn Thời Gian Bế Quan</h3>
                <div class="options-grid">
                    {buttons}
                </div>
            </div>

            {breakthrough_button}
        </div>

        <style>
            .cultivation-panel {{
                background: linear-gradient(135deg, rgba(15, 15, 25, 0.95) 0%, rgba(20, 20, 30, 0.95) 100%);
            }}

            .cultivation-env {{
                margin: var(--space-xl) 0;
                padding: var(--space-xl);
                background: radial-gradient(ellipse at center, rgba(79, 209, 165, 0.1) 0%, transparent 70%);
                border-radius: 8px;
            }}

            .qi-visualization {{
                text-align: center;
                margin-bottom: var(--space-xl);
            }}

            .qi-orb {{
                width: 100px;
                height: 100px;
                margin: 0 auto var(--space-lg);
                border-radius: 50%;
                background: radial-gradient(circle, rgba(79, 209, 165, 0.4) 0%, rgba(255, 200, 71, 0.2) 50%, transparent 70%);
                box-shadow: 0 0 50px rgba(79, 209, 165, 0.5);
                animation: qiFloat 3s ease-in-out infinite;
            }}

            @keyframes qiFloat {{
                0%, 100% {{ transform: translateY(0) scale(1); }}
                50% {{ transform: translateY(-10px) scale(1.05); }}
            }}

            .qi-text {{
                color: var(--jade-essence);
                font-style: italic;
                font-size: 0.95em;
            }}

            .race-info {{
                display: flex;
                align-items: center;
                gap: var(--space-lg);
                padding: var(--space-lg);
                background: rgba(20, 20, 30, 0.5);
                border-left: 3px solid var(--jade-essence);
                border-radius: 4px;
            }}

            .race-icon {{
                font-size: 2.5em;
            }}

            .race-name {{
                font-family: var(--font-script);
                color: var(--celestial-gold);
                margin: 0 0 var(--space-xs) 0;
                font-size: 1.2em;
            }}

            .race-text {{
                color: var(--moonlight-silver);
                font-size: 0.9em;
                line-height: 1.6;
            }}

            .pressure-section {{
                margin: var(--space-xl) 0;
                padding: var(--space-lg);
                background: rgba(20, 20, 30, 0.4);
                border-radius: 6px;
            }}

            .pressure-section h3 {{
                color: var(--jade-essence);
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: var(--space-md);
            }}

            .pressure-bar-container {{
                display: flex;
                align-items: center;
                gap: var(--space-md);
            }}

            .pressure-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: var(--space-sm);
                margin-top: var(--space-sm);
                color: var(--spirit-silver);
                font-size: 0.85rem;
            }}

            .pressure-bar {{
                flex: 1;
                height: 20px;
                background: rgba(15, 15, 20, 0.9);
                border: 1px solid rgba(79, 209, 165, 0.3);
                border-radius: 10px;
                overflow: hidden;
            }}

            .pressure-fill {{
                height: 100%;
                transition: width 0.5s ease;
                box-shadow: 0 0 10px currentColor;
            }}

            .pressure-info {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: var(--space-xs);
            }}

            .pressure-value {{
                font-size: 1.5em;
                font-weight: 700;
                font-family: var(--font-spirit);
            }}

            .pressure-level {{
                font-size: 0.75em;
                color: var(--spirit-silver);
                text-transform: uppercase;
            }}

            .pressure-warning {{
                margin-top: var(--space-md);
                text-align: center;
                font-weight: 600;
                animation: warningPulse 1s ease-in-out infinite;
            }}

            @keyframes warningPulse {{
                0%, 100% {{ opacity: 0.7; }}
                50% {{ opacity: 1; }}
            }}

            .cultivation-options {{
                margin: var(--space-xl) 0;
            }}

            .cultivation-options h3 {{
                color: var(--jade-essence);
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-bottom: var(--space-lg);
                text-align: center;
            }}

            .options-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: var(--space-md);
            }}

            .cultivate-option {{
                padding: var(--space-lg);
                background: rgba(18, 18, 26, 0.9);
                border: 1px solid rgba(79, 209, 165, 0.2);
                border-radius: 4px;
                text-align: center;
                transition: all 0.3s ease;
            }}

            .cultivate-option:hover {{
                transform: translateY(-5px);
                border-color: var(--jade-essence);
                box-shadow: 0 10px 30px rgba(79, 209, 165, 0.2);
            }}

            .option-header {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: var(--space-sm);
                margin-bottom: var(--space-sm);
            }}

            .option-icon {{
                font-size: 1.5em;
                opacity: 0.8;
            }}

            .option-time {{
                font-family: var(--font-script);
                font-size: 1.2em;
                color: var(--celestial-gold);
                font-weight: 600;
            }}

            .option-gain {{
                font-family: var(--font-spirit);
                font-size: 0.85em;
                color: var(--jade-essence);
                margin-bottom: var(--space-md);
            }}

            .btn-cultivate {{
                width: 100%;
                border-color: var(--jade-essence);
            }}

            .breakthrough-section {{
                margin-top: var(--space-xl);
                padding: var(--space-xl);
                background: linear-gradient(135deg, rgba(40, 25, 20, 0.4) 0%, rgba(30, 20, 15, 0.6) 100%);
                border: 2px solid rgba(220, 38, 38, 0.3);
                border-radius: 6px;
                transition: all 0.3s ease;
            }}

            .breakthrough-section:not(.disabled):hover {{
                border-color: var(--blood-crystal);
                box-shadow: 0 0 40px rgba(220, 38, 38, 0.3);
                transform: translateY(-2px);
            }}

            .breakthrough-section.disabled {{
                opacity: 0.5;
                border-color: var(--spirit-silver);
            }}

            .breakthrough-header {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: var(--space-md);
                margin-bottom: var(--space-lg);
            }}

            .breakthrough-icon {{
                font-size: 2em;
            }}

            .breakthrough-header h3 {{
                color: var(--blood-crystal);
                text-shadow: 0 0 20px rgba(220, 38, 38, 0.5);
                margin: 0;
            }}

            .breakthrough-info {{
                margin-bottom: var(--space-lg);
                text-align: center;
            }}

            .breakthrough-target {{
                font-size: 1.1em;
                color: var(--moonlight-silver);
                margin-bottom: var(--space-sm);
            }}

            .breakthrough-target strong {{
                color: var(--celestial-gold);
            }}

            .pressure-requirement {{
                color: var(--celestial-gold);
                font-size: 0.9em;
                margin-bottom: var(--space-md);
            }}

            .risk-display {{
                display: inline-flex;
                flex-direction: column;
                align-items: center;
                gap: var(--space-xs);
                padding: var(--space-sm) var(--space-md);
                background: rgba(20, 20, 30, 0.8);
                border-radius: 4px;
                margin-bottom: var(--space-md);
            }}

            .risk-label {{
                font-family: var(--font-spirit);
                font-size: 0.7em;
                color: var(--spirit-silver);
                text-transform: uppercase;
            }}

            .risk-value {{
                font-size: 1.5em;
                font-weight: 700;
            }}

            .breakthrough-options {{
                display: flex;
                flex-direction: column;
                gap: var(--space-md);
            }}

            .btn-breakthrough, .btn-seclusion, .btn-wait {{
                width: 100%;
            }}

            .btn-breakthrough {{
                border-color: var(--blood-crystal);
                background: linear-gradient(135deg, rgba(60, 20, 20, 0.9) 0%, rgba(50, 15, 15, 0.9) 100%);
                font-size: 1.05em;
            }}

            .btn-breakthrough:hover:not(:disabled) {{
                background: linear-gradient(135deg, rgba(80, 25, 25, 0.95) 0%, rgba(70, 20, 20, 0.95) 100%);
                box-shadow: 0 0 30px rgba(220, 38, 38, 0.5);
            }}

            .btn-seclusion {{
                border-color: var(--celestial-gold);
                background: linear-gradient(135deg, rgba(40, 30, 20, 0.9) 0%, rgba(50, 35, 20, 0.9) 100%);
            }}

            .btn-seclusion:hover:not(:disabled) {{
                background: linear-gradient(135deg, rgba(50, 35, 20, 0.95) 0%, rgba(60, 40, 25, 0.95) 100%);
                box-shadow: 0 0 25px rgba(255, 200, 71, 0.4);
            }}

            .btn-wait {{
                border-color: var(--spirit-silver);
                background: linear-gradient(135deg, rgba(25, 25, 35, 0.9) 0%, rgba(30, 30, 40, 0.9) 100%);
            }}

            .btn-wait:hover {{
                border-color: var(--jade-essence);
                box-shadow: 0 0 20px rgba(79, 209, 165, 0.3);
            }}

            .btn-breakthrough:disabled, .btn-seclusion:disabled {{
                opacity: 0.4;
                cursor: not-allowed;
            }}
        </style>
        """


def view_techniques():
    state = get_state()
    player = state["player"]
    cards = []
    for technique in tech.get_learnable(player["realm_id"]):
        cards.append(
            f"<div class='card technique-card'>"
            f"<div class='technique-header'>"
            f"<h3 class='technique-name'>{technique['name_vn']}</h3>"
            f"<span class='technique-element'>{technique.get('element', 'None')}</span>"
            f"</div>"
            f"<div class='technique-stats'>"
            f"<div class='tech-stat'><span class='tech-stat-label'>Linh lực</span><span class='tech-stat-value'>{technique.get('mp_cost', 10)}</span></div>"
            f"<div class='tech-stat'><span class='tech-stat-label'>Sức mạnh</span><span class='tech-stat-value'>{technique.get('power', 10)}</span></div>"
            f"<div class='tech-stat'><span class='tech-stat-label'>Loại</span><span class='tech-stat-value'>{technique.get('type', 'Pháp thuật')}</span></div>"
            f"</div>"
            f"<p class='technique-desc'>{technique.get('description', '')}</p>"
            f"<form method='post' action='{url_for('learn', technique_id=technique['id'])}'>"
            f"<button class='btn'>Học Công Pháp</button>"
            f"</form></div>"
        )
    slots = "<br>".join(tech.get_slot_display(player))
    return f"""
        <div class="techniques-panel">
            <div class="panel-ornament">
                <span class="ornament-left">❖</span>
                <span class="ornament-title">Công Pháp Mật Tịch</span>
                <span class="ornament-right">❖</span>
            </div>
            <div class="slots-display">
                <h3>Công Pháp Đã Học</h3>
                <div class="slots-content">{slots}</div>
            </div>
            <div class="techniques-grid">
                {''.join(cards)}
            </div>
        </div>
        <style>
            .slots-display {{
                margin-bottom: var(--space-xl);
                padding: var(--space-lg);
                background: rgba(20, 20, 30, 0.5);
                border-left: 3px solid var(--jade-essence);
            }}
            .slots-display h3 {{
                color: var(--jade-essence);
                margin: 0 0 var(--space-md) 0;
            }}
            .slots-content {{
                color: var(--moonlight-silver);
                font-family: var(--font-spirit);
                line-height: 1.8;
            }}
            .techniques-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: var(--space-lg);
                margin-top: var(--space-xl);
            }}
        </style>
        """


def view_world():
    state = get_state()
    player = state["player"]
    joined_sect_id = state["world_state"].get("player_sect")

    if joined_sect_id:
        sect = world.sects[joined_sect_id]
        rank = state["world_state"].get("player_rank", 0)
        power = state["world_state"]["sect_power"].get(joined_sect_id, 50)
        techniques = [tech.techniques[tid] for tid in world.get_sect_techniques(joined_sect_id, rank) if tid in tech.techniques]
        technique_buttons = "".join(
            f"<form method='post' action='{url_for('learn', technique_id=t['id'])}'><button class='btn btn-action'>{t['name_vn']}</button></form>"
            for t in techniques
        )

        sect_npcs = [n for n in npc.get_npcs_in_sect(joined_sect_id) if n["sect_id"] == joined_sect_id or n["sect_id"] == "none"]
        npc_cards = "".join(
            f"<div class='npc-card'>"
            f"<div class='npc-avatar'>👤</div>"
            f"<div class='npc-card-body'>"
            f"<div class='npc-card-title'><strong>{n['name_vn']}</strong> <span class='npc-role'>{n.get('role', 'Tu sĩ')}</span></div>"
            f"<div class='npc-meta'>Tuổi { _npc_age(n) } · { _npc_gender(n) } · { _npc_realm_name(n) }</div>"
            f"<p class='npc-desc'>{n['description']}</p>"
            f"<div class='npc-actions'>"
            f"<form method='post' action='{url_for('gift', npc_id=n['id'])}'><button class='btn btn-gift'>Tặng quà</button></form>"
            f"</div></div></div>"
            for n in sect_npcs
        )

        return f"""
            <div class='section-panel'>
                <div class='panel-ornament'>
                    <span class='ornament-left'>❖</span>
                    <span class='ornament-title'>Nội Môn - {sect['name_vn']}</span>
                    <span class='ornament-right'>❖</span>
                </div>
                <div class='sect-summary'>
                    <div>
                        <p><strong>Cấp bậc:</strong> {rank}</p>
                        <p><strong>Thế lực:</strong> {power}/100</p>
                    </div>
                    <form method='post' action='{url_for('leave_sect')}' class='leave-form'>
                        <button class='btn btn-leave'>Rời tông môn</button>
                    </form>
                </div>
                <div class='sect-inner-grid'>
                    <div class='card sect-inner-card'>
                        <h3>Công pháp tông môn</h3>
                        <p class='muted'>Những công pháp hiện tại phù hợp cấp bậc nội môn của ngươi.</p>
                        {technique_buttons or '<p class="muted">Chưa có công pháp nào mở cho cấp bậc này.</p>'}
                    </div>
                    <div class='card sect-inner-card'>
                        <h3>Ngày thường trong tông môn</h3>
                        <p class='muted'>Các đồng môn và tình huống trong đại môn.</p>
                        <div class='npc-grid'>{npc_cards}</div>
                    </div>
                </div>
                <div class='card sect-quest-card'>
                    <h3>Nhiệm vụ môn phái</h3>
                    <div class='grid'>{''.join(quest_card(state, q) for q in world.get_available_quests(state['world_state']))}</div>
                </div>
            </div>
            <style>
                .sect-summary {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: var(--space-lg);
                    padding: var(--space-lg);
                    background: rgba(20, 20, 30, 0.7);
                    border: 1px solid rgba(79, 209, 165, 0.15);
                    border-radius: 8px;
                    margin-bottom: var(--space-xl);
                }

                .sect-inner-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: var(--space-lg);
                    margin-bottom: var(--space-xl);
                }

                .sect-inner-card {
                    padding: var(--space-lg);
                    background: rgba(15, 15, 25, 0.95);
                    border: 1px solid rgba(79, 209, 165, 0.12);
                }

                .npc-grid {
                    display: grid;
                    gap: var(--space-lg);
                }

                .npc-card {
                    display: grid;
                    grid-template-columns: 56px 1fr;
                    gap: var(--space-md);
                    padding: var(--space-lg);
                    background: rgba(20, 20, 30, 0.7);
                    border-radius: 8px;
                    border: 1px solid rgba(79, 209, 165, 0.1);
                }

                .npc-avatar {
                    display: grid;
                    align-items: center;
                    justify-items: center;
                    font-size: 2rem;
                    border-radius: 50%;
                    background: rgba(79, 209, 165, 0.1);
                    width: 56px;
                    height: 56px;
                }

                .npc-card-body {
                    display: flex;
                    flex-direction: column;
                    gap: var(--space-sm);
                }

                .npc-card-title {
                    display: flex;
                    justify-content: space-between;
                    gap: var(--space-sm);
                    align-items: center;
                    flex-wrap: wrap;
                    color: var(--celestial-gold);
                }

                .npc-meta {
                    color: var(--spirit-silver);
                    font-size: 0.85rem;
                }

                .npc-desc {
                    color: var(--moonlight-silver);
                    margin: 0;
                }

                .npc-actions {
                    margin-top: var(--space-sm);
                }

                .btn-gift, .btn-action, .btn-leave {
                    border-color: var(--jade-essence);
                    background: linear-gradient(135deg, rgba(15, 20, 25, 0.9) 0%, rgba(22, 26, 30, 0.9) 100%);
                }

                .btn-gift:hover, .btn-action:hover, .btn-leave:hover {
                    box-shadow: 0 0 25px rgba(79, 209, 165, 0.25);
                }

                .sect-quest-card {
                    padding: var(--space-lg);
                    background: rgba(18, 18, 26, 0.95);
                    border: 1px solid rgba(79, 209, 165, 0.12);
                    border-radius: 8px;
                }

                .sect-quest-card .grid {
                    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                }

                .leave-form {
                    margin: 0;
                }
            </style>
        """

    available_ids = {s["id"] for s in world.get_available_sects(player)}
    cards = []
    for sect in world.sects.values():
        element = sect.get("elements") or sect.get("element", "?")
        power = state['world_state']['sect_power'].get(sect['id'], 50)
        power_level = "Yếu" if power < 40 else "Trung bình" if power < 70 else "Mạnh" if power < 90 else "Vô địch"
        power_color = "var(--blood-crystal)" if power < 40 else "var(--celestial-gold)" if power < 90 else "var(--jade-essence)"
        faction_icon = "🏔" if "Chính" in sect.get('faction', '') else "🔥" if "Ma" in sect.get('faction', '') else "☯"
        entry_realm = cult.realms.get(sect.get('min_realm', ''), {}).get('name_vn', cult.realms.get('mortal', {}).get('name_vn', 'Không rõ'))
        entry_condition = translate_entry_condition(sect.get('entry_condition', ''))
        sect_npcs = [n for n in npc.get_npcs_in_sect(sect['id']) if n['sect_id'] == sect['id']]
        top_npcs = [n['name_vn'] for n in sect_npcs if n.get('role') == 'elder'][:3] or [n['name_vn'] for n in sect_npcs[:2]]
        hover_npcs = ', '.join(top_npcs) or 'Chưa rõ'
        technique_names = [tech.techniques[tid]['name_vn'] for tid in world.get_sect_techniques(sect['id'], 100) if tid in tech.techniques][:4]
        tech_preview = ', '.join(technique_names) or 'Công pháp chưa lưu hành.'
        can_join = sect['id'] in available_ids
        action_html = (
            f"<form method='post' action='{url_for('join', sect_id=sect['id'])}'><button class='btn btn-join'>Gia nhập môn phái</button></form>"
            if can_join else
            f"<button class='btn btn-disabled' disabled>Chưa đủ điều kiện</button>"
        )

        cards.append(
            f"<div class='card sect-card'>"
            f"<div class='sect-header'>"
            f"<span class='sect-icon'>{faction_icon}</span>"
            f"<div class='sect-info'>"
            f"<h3 class='sect-name'>{sect['name_vn']}</h3>"
            f"<span class='sect-faction'>{sect.get('faction', 'Trung lập')}</span>"
            f"</div></div>"
            f"<div class='sect-stats'>"
            f"<div class='stat-item'>"
            f"<span class='stat-label'>Nguyên tố</span>"
            f"<span class='stat-value'>{element}</span>"
            f"</div>"
            f"<div class='stat-item'>"
            f"<span class='stat-label'>Thế lực</span>"
            f"<span class='stat-value' style='color: {power_color};'>{power} ({power_level})</span>"
            f"</div></div>"
            f"<p class='sect-desc'>{sect['description']}</p>"
            f"<div class='sect-detail'>"
            f"<p><strong>Yêu cầu gia nhập:</strong> {entry_realm}</p>"
            f"<p><em>{entry_condition}</em></p>"
            f"<div class='sect-hover-panel'>"
            f"<h4>Cao tầng</h4><p>{hover_npcs}</p>"
            f"<h4>Công pháp</h4><p>{tech_preview}</p>"
            f"</div>"
            f"</div>"
            f"{action_html}"
            f"</div>"
        )

    return f"""
        <div class='world-panel'>
            <div class='panel-ornament'>
                <span class='ornament-left'>❖</span>
                <span class='ornament-title'>Tông môn</span>
                <span class='ornament-right'>❖</span>
            </div>
            <p class='world-intro'>Giới tu tiên rộng lớn, các tông môn tranh đấu không ngừng. Hãy chọn con đường tu hành của ngươi.</p>
            <div class='world-grid'>
                {''.join(cards)}
            </div>
        </div>
        <style>
            .world-panel {{
                background: linear-gradient(135deg, rgba(15, 15, 25, 0.95) 0%, rgba(20, 20, 30, 0.95) 100%);
            }}

            .world-intro {{
                color: var(--moonlight-silver);
                text-align: center;
                margin-bottom: var(--space-xl);
                font-style: italic;
            }}

            .world-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: var(--space-lg);
                margin-top: var(--space-xl);
            }}

            .sect-card {{
                background: linear-gradient(135deg, rgba(18, 18, 26, 0.95) 0%, rgba(25, 25, 37, 0.95) 100%);
                border: 1px solid rgba(79, 209, 165, 0.2);
                padding: var(--space-xl);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}

            .sect-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, transparent 0%, var(--jade-essence) 50%, transparent 100%);
            }}

            .sect-card:hover {{
                transform: translateY(-8px);
                border-color: var(--celestial-gold);
                box-shadow: 0 20px 60px rgba(255, 200, 71, 0.2);
            }}

            .sect-header {{
                display: flex;
                align-items: center;
                gap: var(--space-lg);
                margin-bottom: var(--space-lg);
            }}

            .sect-icon {{
                font-size: 3em;
                opacity: 0.9;
            }}

            .sect-info {{
                flex: 1;
            }}

            .sect-name {{
                margin: 0 0 var(--space-xs) 0;
                font-family: var(--font-script);
                color: var(--celestial-gold);
                font-size: 1.3em;
                text-shadow: 0 0 15px rgba(255, 200, 71, 0.3);
            }}

            .sect-faction {{
                color: var(--spirit-silver);
                font-family: var(--font-spirit);
                font-size: 0.8em;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }}

            .sect-stats {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: var(--space-md);
                margin-bottom: var(--space-lg);
            }}

            .stat-item {{
                padding: var(--space-sm);
                background: rgba(20, 20, 30, 0.6);
                border-radius: 3px;
            }}

            .stat-label {{
                display: block;
                font-size: 0.7em;
                color: var(--spirit-silver);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: var(--space-xs);
            }}

            .stat-value {{
                display: block;
                font-family: var(--font-spirit);
                font-weight: 600;
                color: var(--moonlight-silver);
            }}

            .sect-desc {{
                color: var(--moonlight-silver);
                font-size: 0.9em;
                line-height: 1.6;
                margin-bottom: var(--space-lg);
            }}

            .sect-detail {{
                padding: var(--space-md);
                margin-bottom: var(--space-lg);
                background: rgba(20, 20, 30, 0.65);
                border-radius: 6px;
            }}

            .sect-detail h4 {{
                margin: 0 0 var(--space-xs) 0;
                color: var(--celestial-gold);
            }}

            .sect-detail p {{
                margin: 0.2rem 0;
                color: var(--moonlight-silver);
                font-size: 0.9rem;
            }}

            .sect-hover-panel {{
                margin-top: var(--space-sm);
                padding: var(--space-sm);
                border-radius: 6px;
                background: rgba(15, 15, 20, 0.9);
                opacity: 0.85;
                transition: opacity 0.3s ease;
            }}

            .sect-card:hover .sect-hover-panel {{
                opacity: 1;
            }}

            .sect-hover-panel h4 {{
                margin-bottom: var(--space-xs);
                color: var(--jade-essence);
                font-size: 0.9rem;
            }}

            .btn-join, .btn-disabled {{
                width: 100%;
                border-color: var(--jade-essence);
                background: linear-gradient(135deg, rgba(20, 30, 25, 0.9) 0%, rgba(25, 35, 30, 0.9) 100%);
                padding: var(--space-md) var(--space-lg);
                color: var(--moonlight-silver);
                margin-top: var(--space-lg);
            }}

            .btn-disabled {{
                opacity: 0.55;
                cursor: not-allowed;
            }}

            .btn-join:hover {{
                background: linear-gradient(135deg, rgba(25, 35, 30, 0.95) 0%, rgba(30, 40, 35, 0.95) 100%);
                box-shadow: 0 0 25px rgba(79, 209, 165, 0.4);
            }}
        </style>
        """


def view_sect():
    state = get_state()
    sect_id = state["world_state"].get("player_sect")
    if not sect_id:
        return "<h2>Nội môn</h2><p>Chưa gia nhập môn phái.</p>"
    sect = world.sects[sect_id]
    ids = world.get_sect_techniques(sect_id, state["world_state"].get("player_rank", 0))
    buttons = "".join(
        f"<form method='post' action='{url_for('learn', technique_id=tid)}'><button>{tech.techniques[tid]['name_vn']}</button></form>"
        for tid in ids if tid in tech.techniques
    )
    quest_cards = "".join(quest_card(state, q) for q in world.get_available_quests(state["world_state"]))
    npcs = "".join(f"<li>{n['name_vn']} - {n['role']}</li>" for n in npc.get_npcs_in_sect(sect_id))
    return f"<h2>{sect['name_vn']}</h2><p>Cáº¥p báº­c {state['world_state'].get('player_rank', 0)} | Tráº­n tháº¯ng chá» ná»™p: {state['world_state'].get('combat_wins', 0)}</p>{buttons}<h3>Nhiá»‡m vá»¥ mÃ´n phÃ¡i</h3><div class='grid'>{quest_cards}</div><h3>NPC</h3><ul>{npcs}</ul>"


def quest_card(state, q):
    player = state["player"]
    ws = state["world_state"]
    if q["type"] == "item":
        have = player.get("inventory", {}).get(q["target_id"], 0)
        need = int(q["required_qty"])
        target_name = items.items.get(q["target_id"], {}).get("name_vn", q["target_id"])
        progress = f"Vật phẩm ({target_name}): {have}/{need}"
    else:
        have = ws.get("combat_wins", 0)
        need = int(q["required_qty"])
        progress = f"Trận thắng: {have}/{need}"
    reward_item_name = ""
    if q.get("reward_item"):
        reward_item_name = items.items.get(q["reward_item"], {}).get("name_vn", q["reward_item"])
    reward_text = f"rank +{q['reward_rank']}, thế lực +{q['reward_power']}"
    if reward_item_name:
        reward_text += f", {reward_item_name}"
    return (
        f"<div class='card'><h3>{q['name_vn']}</h3>"
        f"<p>{progress} | thưởng: {reward_text}</p>"
        f"<p class='muted'>{q['description']}</p>"
        f"<form method='post' action='{url_for('complete_quest', quest_id=q['id'])}'><button>Hoàn thành</button></form></div>"
    )


def view_secret():
    state = get_state()
    sstate = state.get("secret_state")
    if sstate:
        secret = world.secret_realms[sstate["id"]]
        logs = "".join(f"<div>{line}</div>" for line in sstate.get("logs", []))
        return (
            f"<h2>{secret['name_vn']}</h2>"
            f"<p>Tiến độ {sstate['progress']}/3 | Rủi ro hiện tại {int(sstate['danger'] * 100)}%</p>"
            f"<p class='muted'>{secret['description']}</p>"
            f"<form method='post' action='{url_for('secret_action', action='observe')}'><button>Quan sát địa thế</button></form>"
            f"<form method='post' action='{url_for('secret_action', action='advance')}'><button>Tiến sâu</button></form>"
            f"<form method='post' action='{url_for('secret_action', action='retreat')}'><button>RÃºt lui</button></form>"
            f"<h3>Diá»…n biáº¿n</h3><div class='log'>{logs}</div>"
        )
    cards = []
    for secret in world.get_available_secret_realms(state["player"]):
        cards.append(
            f"<div class='card'><h3>{secret['name_vn']}</h3><p>Thời gian {secret['time_months']} tháng | Rủi ro {int(float(secret['risk']) * 100)}%</p>"
            f"<p class='muted'>{secret['description']}</p><form method='post' action='{url_for('explore_secret', realm_id=secret['id'])}'><button>Thám hiểm</button></form></div>"
        )
    return f"<h2>Bí cảnh</h2><div class='grid'>{''.join(cards) or '<p>Chưa có bí cảnh phù hợp.</p>'}</div>"


def view_combat():
    state = get_state()
    cstate = state.get("combat_state")
    if cstate:
        p = cstate["p_state"]
        e = cstate["e_state"]
        technique_buttons = []
        for tid in state["player"]["technique_slots"]:
            if not tid or tid not in tech.techniques:
                continue
            t = tech.techniques[tid]
            mp_cost = int(t.get("mp_cost", 10))
            disabled_note = " (thiếu MP)" if p["mp"] < mp_cost else ""
            technique_buttons.append(
                f"<form method='post' action='{url_for('combat_use', technique_id=tid)}'><button>{t.get('name_vn', tid)} - MP {mp_cost}{disabled_note}</button></form>"
            )
        logs = "".join(f"<div>{line}</div>" for line in cstate.get("logs", [])[-12:])
        return (
            f"<h2>Chiến đấu - lượt {cstate['turn']}</h2>"
            f"<div class='grid'>"
            f"<div class='card'><h3>{state['player']['name']}</h3><p>HP {p['hp']}/{p['hp_max']} | MP {p['mp']}/{p['mp_max']}</p></div>"
            f"<div class='card'><h3>{e['name']}</h3><p>HP {e['hp']}/{e['hp_max']} | MP {e['mp']}/{e['mp_max']}</p></div>"
            f"</div><h3>Hành động</h3>{''.join(technique_buttons)}"
            f"<form method='post' action='{url_for('combat_recover')}'><button>Äiá»u tá»©c há»“i MP</button></form>"
            f"<form method='post' action='{url_for('combat_flee')}'><button>Bỏ chạy</button></form>"
            f"<h3>Diá»…n biáº¿n</h3><div class='log'>{logs}</div>"
        )
    # Safe realm index lookup with fallback
    player_level = tech.get_realm_index(state["player"]["realm_id"])

    cards = []
    for enemy in Loader.load(ENEMIES_PATH):
        enemy_level = tech.get_realm_index(enemy["realm_id"])
        if enemy_level > player_level + 1:
            continue
        enemy_realm_name = cult.realms.get(enemy['realm_id'], {}).get('name_vn', enemy['realm_id'])
        cards.append(
            f"<div class='card'><h3>{enemy['name_vn']}</h3><p>{enemy_realm_name} | {enemy['element']} | HP {enemy['hp']}</p>"
            f"<p class='muted'>{enemy['description']}</p><form method='post' action='{url_for('fight', enemy_id=enemy['id'])}'><button>Chiến đấu</button></form></div>"
        )
    return f"<h2>Chiến đấu</h2><div class='grid'>{''.join(cards)}</div>"


def view_inventory():
    state = get_state()
    player = state["player"]
    if not player["inventory"]:
        return """
            <div class="inventory-empty">
                <div class="empty-icon">🎒</div>
                <h2>Túi Trù Vủ</h2>
                <p class="muted">Chưa có vật phẩm nào trong túi trữ vật</p>
                <p class="empty-hint">Hãy thám hiểm bí cảnh hoặc đả bại kẻ thù để thu thập linh dược và bảo vật</p>
            </div>
            <style>
                .inventory-empty {
                    text-align: center;
                    padding: var(--space-2xl);
                    background: radial-gradient(ellipse at center, rgba(79, 209, 165, 0.1) 0%, transparent 70%);
                }
                .empty-icon {
                    font-size: 5em;
                    opacity: 0.3;
                    margin-bottom: var(--space-lg);
                }
                .empty-hint {
                    color: var(--spirit-silver);
                    font-size: 0.9em;
                    font-style: italic;
                    margin-top: var(--space-md);
                }
            </style>
        """
    cards = []
    for item_id, qty in player["inventory"].items():
        item = items.items.get(item_id)
        if not item:
            cards.append(
                f"<div class='card item-card unknown-item'>"
                f"<div class='item-icon'>❓</div>"
                f"<h3 class='item-name'>{item_id} x{qty}</h3>"
                f"<p class='muted'>Vật phẩm không xác định</p>"
                f"</div>"
            )
            continue

        # Determine item rarity color
        effect_value = int(item.get('effect_value', 0))
        rarity_color = "var(--spirit-silver)"
        if effect_value >= 50:
            rarity_color = "var(--celestial-gold)"
        elif effect_value >= 30:
            rarity_color = "var(--jade-essence)"

        effect_icon = "💚" if "hp" in item.get('effect_type', '').lower() else "💙" if "mp" in item.get('effect_type', '').lower() else "✨"

        cards.append(
            f"<div class='card item-card'>"
            f"<div class='item-header'>"
            f"<span class='item-icon' style='background: {rarity_color}20; border-color: {rarity_color};'>{effect_icon}</span>"
            f"<div class='item-info'>"
            f"<h3 class='item-name' style='color: {rarity_color};'>{item['name_vn']}</h3>"
            f"<span class='item-quantity'>x{qty}</span>"
            f"</div></div>"
            f"<div class='item-effect'>"
            f"<span class='effect-type'>{item['effect_type']}</span>"
            f"<span class='effect-value'>+{item['effect_value']}</span>"
            f"</div>"
            f"<p class='item-desc'>{item['description']}</p>"
            f"<form method='post' action='{url_for('use_item', item_id=item_id)}'>"
            f"<button class='btn btn-use'>Sử Dụng</button>"
            f"</form></div>"
        )
    return f"""
        <div class="inventory-panel">
            <div class="panel-ornament">
                <span class="ornament-left">❖</span>
                <span class="ornament-title">Túi Trù Vật</span>
                <span class="ornament-right">❖</span>
            </div>
            <div class="inventory-grid">
                {''.join(cards)}
            </div>
        </div>
        <style>
            .inventory-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: var(--space-lg);
                margin-top: var(--space-xl);
            }}

            .item-card {{
                background: linear-gradient(135deg, rgba(18, 18, 26, 0.95) 0%, rgba(25, 25, 37, 0.95) 100%);
                border: 1px solid rgba(79, 209, 165, 0.2);
                padding: var(--space-lg);
                transition: all 0.3s ease;
            }}

            .item-card:hover {{
                transform: translateY(-5px);
                border-color: var(--jade-essence);
                box-shadow: 0 15px 40px rgba(79, 209, 165, 0.2);
            }}

            .item-header {{
                display: flex;
                align-items: center;
                gap: var(--space-md);
                margin-bottom: var(--space-md);
            }}

            .item-icon {{
                width: 50px;
                height: 50px;
                border-radius: 50%;
                border: 2px solid;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.8em;
                flex-shrink: 0;
            }}

            .item-info {{
                flex: 1;
            }}

            .item-name {{
                margin: 0 0 var(--space-xs) 0;
                font-family: var(--font-script);
                font-size: 1.2em;
            }}

            .item-quantity {{
                color: var(--spirit-silver);
                font-family: var(--font-spirit);
                font-size: 0.85em;
            }}

            .item-effect {{
                display: flex;
                justify-content: space-between;
                padding: var(--space-sm);
                background: rgba(20, 20, 30, 0.6);
                border-radius: 3px;
                margin-bottom: var(--space-md);
            }}

            .effect-type {{
                color: var(--spirit-silver);
                font-size: 0.85em;
                text-transform: uppercase;
            }}

            .effect-value {{
                color: var(--jade-essence);
                font-weight: 700;
                font-family: var(--font-spirit);
            }}

            .item-desc {{
                color: var(--moonlight-silver);
                font-size: 0.9em;
                line-height: 1.6;
                margin-bottom: var(--space-md);
            }}

            .btn-use {{
                width: 100%;
                border-color: var(--jade-essence);
            }}

            .unknown-item {{
                opacity: 0.6;
                border-color: var(--spirit-silver);
            }}
        </style>
        """


def _npc_gender(npc_data: dict) -> str:
    explicit = npc_data.get("gender", "").strip()
    if explicit:
        return explicit
    name = npc_data.get("name_vn", "").lower()
    if "sư muội" in name or "sư tỷ" in name or "cô" in name or "bà" in name or "sa" in name:
        return "Nữ"
    if "sư huynh" in name or "sư đệ" in name or "trưởng lão" in name or "đạo nhân" in name or "tiên" in name:
        return "Nam"
    return "Không xác định"


def _npc_age(npc_data: dict) -> str:
    explicit = npc_data.get("age", "").strip()
    if explicit:
        return explicit
    role = npc_data.get("role", "").lower()
    if role == "elder":
        return "70+"
    if role == "disciple":
        return "24"
    if role == "merchant":
        return "38"
    if role == "rogue":
        return "30"
    return "?"


def _npc_realm_name(npc_data: dict) -> str:
    realm_id = npc_data.get("realm_id", "")
    realm_data = cult.realms.get(realm_id, {})
    return realm_data.get("name_vn", realm_id or "Chưa rõ")


def view_relations():
    state = get_state()
    rels = state["world_state"].get("npc_relations", {})
    rows = []
    for npc_id, relation in rels.items():
        n = npc.npcs.get(npc_id)
        if n:
            rows.append(
                f"<div class='npc-card'>"
                f"<div class='npc-header'>"
                f"<div class='npc-avatar' title='Tuổi: {_npc_age(n)}\nGiới tính: {_npc_gender(n)}\nCảnh giới: {_npc_realm_name(n)}'>👤</div>"
                f"<div class='npc-info'>"
                f"<h3 class='npc-name'>{n['name_vn']}</h3>"
                f"<span class='npc-role'>{n.get('role', 'Tu sĩ')}</span>"
                f"</div></div>"
                f"<div class='npc-relations'>"
                f"<div class='relation-stat'>"
                f"<span class='relation-label'>Kính</span>"
                f"<span class='relation-value' style='color: var(--jade-essence);'>{relation['respect']}</span>"
                f"</div>"
                f"<div class='relation-stat'>"
                f"<span class='relation-label'>Tín</span>"
                f"<span class='relation-value' style='color: var(--celestial-gold);'>{relation['trust']}</span>"
                f"</div>"
                f"<div class='relation-stat'>"
                f"<span class='relation-label'>Sợ</span>"
                f"<span class='relation-value' style='color: var(--blood-crystal);'>{relation['fear']}</span>"
                f"</div>"
                f"</div>"
                f"<p class='npc-greeting'>{npc.get_greeting(npc_id, relation)}</p>"
                f"<div class='npc-actions'>"
                f"<form method='post' action='{url_for('gift', npc_id=npc_id)}'><button class='btn btn-gift'>Tặng quà</button></form>"
                f"</div>"
                f"</div>"
            )
    return f"""
        <div class="relations-panel">
            <div class="panel-ornament">
                <span class="ornament-left">❖</span>
                <span class="ornament-title">Nhân Duyên Quan Hệ</span>
                <span class="ornament-right">❖</span>
            </div>
            <div class="relations-content">
                {''.join(rows) if rows else '<p class="no-relations">Chưa gặp NPC nào trong giới tu tiên.</p>'}
            </div>
        </div>
        <style>
            .relations-content {{
                margin-top: var(--space-xl);
            }}
            .npc-card {{
                padding: var(--space-lg);
                background: rgba(18, 18, 26, 0.95);
                border: 1px solid rgba(79, 209, 165, 0.12);
                border-radius: 10px;
                margin-bottom: var(--space-lg);
            }}
            .npc-header {{
                display: flex;
                align-items: center;
                gap: var(--space-md);
                margin-bottom: var(--space-md);
            }}
            .npc-avatar {{
                width: 56px;
                height: 56px;
                display: grid;
                place-items: center;
                border-radius: 50%;
                background: rgba(79, 209, 165, 0.12);
                font-size: 1.8rem;
                cursor: help;
            }}
            .npc-info {{
                display: flex;
                flex-direction: column;
                gap: 0.25rem;
            }}
            .npc-name {{
                margin: 0;
                color: var(--celestial-gold);
            }}
            .npc-role {{
                color: var(--spirit-silver);
                font-size: 0.9rem;
            }}
            .npc-relations {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: var(--space-sm);
                margin-bottom: var(--space-md);
            }}
            .relation-stat {{
                padding: var(--space-sm);
                background: rgba(20, 20, 30, 0.6);
                border-radius: 6px;
                text-align: center;
            }}
            .relation-label {{
                display: block;
                font-size: 0.75rem;
                color: var(--spirit-silver);
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}
            .relation-value {{
                display: block;
                margin-top: 0.25rem;
                font-size: 1.1rem;
                font-weight: 600;
            }}
            .npc-greeting {{
                color: var(--moonlight-silver);
                font-style: italic;
                margin-top: var(--space-md);
                padding: var(--space-sm);
                background: rgba(20, 20, 30, 0.4);
                border-left: 2px solid var(--jade-essence);
                border-radius: 6px;
            }}
            .npc-actions {{
                margin-top: var(--space-md);
            }}
            .btn-gift {{
                border-color: var(--jade-essence);
                background: linear-gradient(135deg, rgba(20, 30, 25, 0.9) 0%, rgba(25, 35, 30, 0.9) 100%);
                padding: var(--space-md) var(--space-lg);
            }}
            .btn-gift:hover {{
                box-shadow: 0 0 25px rgba(79, 209, 165, 0.25);
            }}
            .no-relations {{
                text-align: center;
                color: var(--spirit-silver);
                font-style: italic;
                padding: var(--space-2xl);
                background: rgba(20, 20, 30, 0.3);
            }}
        </style>
        """


def view_timeline():
    state = get_state()
    rows = []
    for history in state["world_state"].get("world_history", []):
        rows.append(
            f"<div class='event-card'>"
            f"<h3 class='event-title'>{history['event']}</h3>"
            f"<p class='event-time'>Năm {history['year']}</p>"
            f"<p class='muted'>{history.get('detail', '')}</p>"
            f"</div>"
        )
    for event_id in state["world_state"].get("events_fired", []):
        event = world.events.get(event_id)
        if event:
            rows.append(
                f"<div class='event-card'>"
                f"<h3 class='event-title'>{event['name_vn']}</h3>"
                f"<p class='event-time'>Năm {event['trigger_year']} - Tháng {event['trigger_month']}</p>"
                f"<p class='muted'>{event['description']}</p>"
                f"<div class='event-effect'>Tác động: {event['effect_type']} +{event['effect_value']}</div>"
                f"</div>"
            )
    return f"""
        <div class="timeline-panel">
            <div class="panel-ornament">
                <span class="ornament-left">❖</span>
                <span class="ornament-title">Thời Quang Hành Trình</span>
                <span class="ornament-right">❖</span>
            </div>
            <div class="timeline-content">
                {''.join(rows) if rows else '<p class="no-events">Chưa có sự kiện nào xảy ra.</p>'}
            </div>
        </div>
        <style>
            .timeline-content {{
                margin-top: var(--space-xl);
                padding-left: var(--space-lg);
                border-left: 2px solid rgba(79, 209, 165, 0.2);
            }}
            .no-events {{
                text-align: center;
                color: var(--spirit-silver);
                font-style: italic;
                padding: var(--space-2xl);
                background: rgba(20, 20, 30, 0.3);
            }}
        </style>
        """


if __name__ == "__main__":
    app.run(debug=True)

