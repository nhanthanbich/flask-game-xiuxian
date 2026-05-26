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

def default_player(root_id="metal", race_id="human", name="Tan Tu"):
    return {
        "name": name,
        "realm_id": "mortal",
        "root_id": root_id,
        "race_id": race_id,
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
            save_rows.append(
                f"<div class='slot-card' id='slot-{slot['slot']}'>"
                f"<span class='slot-number'>{slot['slot']}</span>"
                f"<div class='slot-header'><h3 class='slot-title'>{slot['name']}</h3>"
                f"<p class='slot-status active'>{slot['realm_id']}</p></div>"
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

    # Get player name from form
    player_name = request.form.get("player_name", "").strip()
    # Use fallback if empty
    if not player_name:
        player_name = "Tan Tu"

    # Update player name
    pending["player"]["name"] = player_name
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
        log(state, "Su kien: " + line)


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
        ("world", "Thế giới"),
        ("sect", "Nội môn"),
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
        "sect": view_sect,
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
            rows.append(
                f"<div class='card'><h3>Slot {slot['slot']} - {slot['name']}</h3>"
                f"<p>{slot['realm_id']} | {slot['game_time']} | Lưu lúc {slot['saved_at']}</p>"
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
    player["exp"] += gain
    time.advance_months(months)
    tick_time(state, time)
    set_time(state, time)
    log(state, f"Be quan {months} thang, nhan {gain} exp.")
    save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/breakthrough")
def breakthrough():
    state = get_state()
    player = state["player"]
    time = current_time(state)
    result = cult.attempt_breakthrough(player)
    if result.get("success"):
        realm = result["realm"]
        event_bus.publish("breakthrough", {"player": player, "realm": realm, "world_state": state["world_state"]})
        log(state, f"Dot pha thanh cong len {realm['name_vn']}.")
        text = flavor.get("breakthrough", realm["id"])
        if text:
            log(state, text)
    else:
        skip = result.get("failure_skip_months", 0)
        if skip:
            time.advance_months(skip)
            tick_time(state, time)
            set_time(state, time)
        log(state, result.get("message", "Dot pha that bai."))
    save_state(state)
    return redirect(url_for("game", tab="cultivate"))


@app.post("/learn/<technique_id>")
def learn(technique_id):
    state = get_state()
    player = state["player"]
    slots = player["technique_slots"]
    slot = next((i for i, value in enumerate(slots) if not value), 0)
    tech.learn(player, technique_id, slot)
    log(state, f"Hoc cong phap {tech.techniques[technique_id]['name_vn']} vao slot {slot + 1}.")
    save_state(state)
    return redirect(request.referrer or url_for("game", tab="techniques"))


@app.post("/join/<sect_id>")
def join(sect_id):
    state = get_state()
    if world.join_sect(state["player"], state["world_state"], sect_id):
        event_bus.publish("join_sect", {"player": state["player"], "sect_id": sect_id, "world_state": state["world_state"]})
        log(state, f"Gia nhap {world.sects[sect_id]['name_vn']}.")
    else:
        log(state, "Khong the gia nhap mon phai nay.")
    save_state(state)
    return redirect(url_for("game", tab="world"))


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
    return redirect(url_for("game", tab="sect"))


@app.post("/quest/<quest_id>")
def complete_quest(quest_id):
    state = get_state()
    ok, message = world.complete_quest(state["player"], state["world_state"], quest_id)
    log(state, message)
    save_state(state)
    return redirect(url_for("game", tab="sect"))


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
    breakthrough_button = ""
    if info.get("ready") and info.get("next"):
        nxt = info["next"]
        risk_percent = int(info["risk"] * 100)
        risk_color = "var(--jade-essence)" if risk_percent < 30 else "var(--celestial-gold)" if risk_percent < 60 else "var(--blood-crystal)"
        breakthrough_button = (
            f'<div class="breakthrough-section">'
            f'<div class="breakthrough-header">'
            f'<span class="breakthrough-icon">⚡</span>'
            f'<h3>Đột Phá Đề Trảnh</h3>'
            f'</div>'
            f'<div class="breakthrough-info">'
            f'<p class="breakthrough-target">Thăng cấp: <strong>{nxt["name_vn"]}</strong></p>'
            f'<div class="risk-display">'
            f'<span class="risk-label">Rủi ro</span>'
            f'<span class="risk-value" style="color: {risk_color};">{risk_percent}%</span>'
            f'</div></div>'
            f'<form method="post" action="{url_for("breakthrough")}">'
            f'<button class="btn btn-breakthrough">Thực Hiện Đột Phá</button>'
            f'</form></div>'
        )
    else:
        breakthrough_button = (
            f'<div class="breakthrough-section disabled">'
            f'<div class="breakthrough-header">'
            f'<span class="breakthrough-icon">🔒</span>'
            f'<h3>Đột Phá Đề Trảnh</h3>'
            f'</div>'
            f'<p class="muted">Chưa đủ tu vi để đột phá</p>'
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

            .risk-display {{
                display: inline-flex;
                flex-direction: column;
                align-items: center;
                gap: var(--space-xs);
                padding: var(--space-sm) var(--space-md);
                background: rgba(20, 20, 30, 0.8);
                border-radius: 4px;
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

            .btn-breakthrough {{
                width: 100%;
                border-color: var(--blood-crystal);
                background: linear-gradient(135deg, rgba(60, 20, 20, 0.9) 0%, rgba(50, 15, 15, 0.9) 100%);
                font-size: 1.1em;
            }}

            .btn-breakthrough:hover {{
                background: linear-gradient(135deg, rgba(80, 25, 25, 0.95) 0%, rgba(70, 20, 20, 0.95) 100%);
                box-shadow: 0 0 30px rgba(220, 38, 38, 0.5);
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
            f"<span class='technique-element'>{technique['element']}</span>"
            f"</div>"
            f"<div class='technique-stats'>"
            f"<div class='tech-stat'><span class='tech-stat-label'>Linh lực</span><span class='tech-stat-value'>{technique['mp_cost']}</span></div>"
            f"<div class='tech-stat'><span class='tech-stat-label'>Hiệu quả</span><span class='tech-stat-value'>{technique['effect']}</span></div>"
            f"<div class='tech-stat'><span class='tech-stat-label'>Loại</span><span class='tech-stat-value'>{technique.get('type', 'Pháp thuật')}</span></div>"
            f"</div>"
            f"<p class='technique-desc'>{technique['description']}</p>"
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
    cards = []
    for sect in world.sects.values():
        element = sect.get("elements") or sect.get("element", "?")
        power = state['world_state']['sect_power'].get(sect['id'], 50)

        # Determine power level indicator
        power_level = "Yếu" if power < 40 else "Trung bình" if power < 70 else "Mạnh" if power < 90 else "Vô địch"
        power_color = "var(--blood-crystal)" if power < 40 else "var(--celestial-gold)" if power < 90 else "var(--jade-essence)"

        # Get faction icon
        faction_icon = "🏔" if "Chính" in sect.get('faction', '') else "🔥" if "Ma" in sect.get('faction', '') else "☯"

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
            f"<form method='post' action='{url_for('join', sect_id=sect['id'])}'>"
            f"<button class='btn btn-join'>Gia Nhập Môn Phái</button>"
            f"</form></div>"
        )
    return f"""
        <div class="world-panel">
            <div class="panel-ornament">
                <span class="ornament-left">❖</span>
                <span class="ornament-title">Tu Tiên Giới Vịnh</span>
                <span class="ornament-right">❖</span>
            </div>
            <p class="world-intro">Giới tu tiên rộng lớn, các môn phái tranh đấu không ngừng. Hãy chọn con đường tu hành của ngươi.</p>
            <div class="world-grid">
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

            .btn-join {{
                width: 100%;
                border-color: var(--jade-essence);
                background: linear-gradient(135deg, rgba(20, 30, 25, 0.9) 0%, rgba(25, 35, 30, 0.9) 100%);
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
        return "<h2>Noi mon</h2><p>Chua gia nhap mon phai.</p>"
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
        progress = f"Váº­t pháº©m: {have}/{need}"
    else:
        have = ws.get("combat_wins", 0)
        need = int(q["required_qty"])
        progress = f"Tráº­n tháº¯ng: {have}/{need}"
    return (
        f"<div class='card'><h3>{q['name_vn']}</h3>"
        f"<p>{progress} | thưởng: rank +{q['reward_rank']}, thế lực +{q['reward_power']}</p>"
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
            disabled_note = " (thiáº¿u MP)" if p["mp"] < int(t["mp_cost"]) else ""
            technique_buttons.append(
                f"<form method='post' action='{url_for('combat_use', technique_id=tid)}'><button>{t['name_vn']} - MP {t['mp_cost']}{disabled_note}</button></form>"
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
        cards.append(
            f"<div class='card'><h3>{enemy['name_vn']}</h3><p>{enemy['realm_id']} | {enemy['element']} | HP {enemy['hp']}</p>"
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
                f"<div class='npc-avatar'>👤</div>"
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
            .npc-greeting {{
                color: var(--moonlight-silver);
                font-style: italic;
                margin-top: var(--space-md);
                padding: var(--space-sm);
                background: rgba(20, 20, 30, 0.4);
                border-left: 2px solid var(--jade-essence);
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

