# Tu Tiên Ký - Hướng Dẫn Chạy Project

## Giới Thiệu

Dự án có **2 phiên bản**:

1. **Flask Web App** (`flask_app.py`) - Phiên bản web với UI xianxia đẹp mắt ✨ **(RECOMMENDED)**
2. **Terminal CLI** (`main.py`) - Phiên bản console text-based

---

## Cách 1: Chạy Flask Web App (Khuyên Dùng)

### Yêu Cầu:
- Python 3.9+
- pip

### Cài Đặt và Chạy:

#### Trên Linux/macOS:
```bash
cd claude
chmod +x run_web.sh
./run_web.sh
```

Hoặc thủ công:
```bash
cd claude
pip3 install -r requirements.txt
python3 flask_app.py
```

#### Trên Windows:
```cmd
cd claude
run_web.bat
```

Hoặc thủ công:
```cmd
cd claude
pip install -r requirements.txt
python flask_app.py
```

### Truy Cập Game:
Mở trình duyệt và truy cập: **http://localhost:5000**

---

## Cách 2: Chạy Terminal CLI Version

```bash
cd claude
python3 main.py
```

---

## Cấu Trúc Project

```
claude/
├── flask_app.py           # Flask web app (ĐÃ NÂNG CẤP UI) ⭐
├── main.py                # Terminal CLI version
├── requirements.txt       # Python dependencies
├── run_web.sh            # Script chạy web (Linux/macOS)
├── run_web.bat           # Script chạy web (Windows)
│
├── templates/            # HTML templates (ĐÃ NÂNG CẤP) ⭐
│   ├── base.html        # Base template
│   ├── start.html       # Start screen (mới)
│   ├── new_game.html    # Race selection (mới)
│   ├── confirm.html     # Character confirmation (mới)
│   ├── game.html        # Main game interface
│   └── combat.html      # Combat screen
│
├── static/
│   └── css/
│       ├── main.css          # Main styles (ĐÃ NÂNG CẤP) ⭐
│       └── components.css    # Component styles (mới)
│
├── engine/              # Backend game logic (KHÔNG THAY ĐỔI)
│   ├── core/
│   │   ├── game.py          # Terminal game engine
│   │   ├── loader.py        # Data loader
│   │   ├── save_manager.py  # Save system
│   │   └── ...
│   └── systems/              # Game systems
│       ├── combat.py
│       ├── cultivation.py
│       └── ...
│
├── ui/                  # Terminal UI (KHÔNG THAY ĐỔI)
│   ├── renderer.py
│   └── tabs/
│
└── data/                # Game data (KHÔNG THAY ĐỔI)
    └── entities/
```

---

## ✨ Đã Nâng Cấp Gì? (Flask Web Version)

### Frontend UI/UX - Đồ Họa Tu Tiên Xianxia Premium:

**1. Start Screen:**
- ☯ Tai Chi icon xoay với glow effect
- Title "修仙记" với animated gradient
- Heavenly realm background
- 15+ floating qi particles (jade, gold, silver)
- Ornamental dividers

**2. Race Selection:**
- Large animated race icons (👤/👿/🐉)
- Background glow pulses
- Stats mini bars
- Decorative animated borders
- Divine buttons với glow effects

**3. Character Confirmation:**
- Large rotating avatar frame
- Heavenly light effect
- Rarity system (Phàm Căn / Thiên Phẩm)
- Badge system với color coding
- Ornamental panels

**4. Main Game Interface:**
- Jade-gold spiritual palette
- Animated qi orbs
- Cultivation progress bars với shimmer
- Hover effects everywhere
- Ornamental dividers

**5. Combat Screen:**
- Battle arena 2-side layout
- Animated portrait frames
- HP/MP bars với fill animations
- Combat log panel
- Energy divider (VS)

**6. Additional Screens:**
- Inventory: Rare item colors, gradient cards
- World Map: Sect cards với power indicators
- Techniques: Stats grid, element badges
- NPC Relations: Avatar icons, relation stats
- Timeline: Event cards với timestamps

### 🔒 Được Bảo Toàn Hoàn Toàn:
- ✅ All backend game logic
- ✅ All gameplay systems (combat, cultivation, etc.)
- ✅ All CSV data structures
- ✅ Save/Load functionality
- ✅ Entity models
- ✅ Game balance

---

## Troubleshooting

### Lỗi: "ModuleNotFoundError: No module named 'flask'"
**Giải pháp:**
```bash
pip install Flask
```

### Lỗi: Encoding UTF-8
**Giải pháp:** Đảm bảo terminal hỗ trợ UTF-8:
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Port 5000 bị chiếm
**Giải pháp:** Thay đổi port trong `flask_app.py`:
```python
if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Thay port khác
```

---

## Development

### Để sửa đổi UI (Frontend):
- Templates: `templates/*.html`
- CSS: `static/css/`
- View functions: `flask_app.py` (phần render templates)

### Để sửa đổi Game Logic (Backend):
- Systems: `engine/systems/*.py`
- Data: `data/entities/*.csv`
- Core: `engine/core/*.py`

---

## Quick Start

```bash
# 1. Vào thư mục project
cd claude

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Chạy Flask app
python3 flask_app.py

# 4. Mở trình duyệt
# http://localhost:5000
```

---

## Credits

- Backend Engine: Original game systems
- Frontend UI/UX: Completely redesigned xianxia theme (2026)
- Design Style: Immortal cultivation, spiritual energy, heavenly realms
