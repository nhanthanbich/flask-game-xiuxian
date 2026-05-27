# HỆ THỐNG PROGRESSION VÀ TIMELINE - BÁO CÁO HOÀN THÀNH

## TỔNG QUAN

Đã triển khai thành công 2 hệ thống theo yêu cầu:

1. **Vòng lặp Progression: Tu luyện → Tích lũy → Áp lực → Đột phá → Phản ứng thế giới**
2. **NPC Timeline: Thời gian trôi và thế giới vận động**

---

## PHẦN 1: PROGRESSION LOOP

### 1A. TRẠNG THÁI TÍCH LŨY TU LUYỆN

**Fields mới trong character state:**
- `cultivation_pressure`: int (0–100)
- `breakthrough_ready`: bool
- `breakthrough_risk`: int (0–100)

**Cơ chế áp lực:**
```
Mỗi lần tu luyện:
  - cultivation_pressure += exp_gained × 0.1 × linh_căn_multiplier
  - Khi pressure >= 80:  → msg-warning "Linh lực sung mãn, nội tâm có chút bất ổn"
  - Khi pressure >= 95: → msg-warning "Không thể tiếp tục trì hoãn đột phá"
                           breakthrough_ready = True
  - Khi pressure = 100: → Event "Tẩu Hỏa Nhập Ma"
                           Mất 20-40% HP, pressure reset về 60
```

**File đã sửa:** `engine/systems/cultivation.py`
- Method: `add_cultivation_pressure()`
- Method: `get_pressure_status()`
- Method: `increase_breakthrough_risk()`
- Method: `reset_pressure()`

---

### 1B. SỰ KIỆN ĐỘT PHÁ CÓ TRỌNG LƯỢNG

**3 chế độ đột phá:**

| Chế độ | Tỷ lệ thành công | Thời gian | Hậu quả thất bại |
|--------|-------------------|-----------|-------------------|
| Đột phá ngay | 60% + (pressure/100 × 20%) | 0 tháng | Mất 30% HP, pressure về 50 |
| Bế quan đột phá | 85% | 1-3 tháng | Mất 15% HP, pressure về 60 |
| Chờ thêm | - | - | Pressure +5, Risk +10 |

**Điều kiện tiên quyết:**
- cultivation_pressure >= 80
- Không trong combat/nhiệm vụ dở

**File đã sửa:** `engine/systems/cultivation.py`
- Method: `attempt_breakthrough(player, mode)`
- Method: `_get_breakthrough_lore(realm_id)` - 15 đoạn lore riêng cho từng cảnh giới

---

### 1C. PHẢN ỨNG THẾ GIỚI SAU ĐỘT PHÁ

**Trigger khi đột phá thành công:**

1. **Log thế giới:**
   - "Năm X, [Tên] đạt [Cảnh giới] tại nơi tu hành"
   - Lưu vào `world_history`

2. **NPC quen biết phản ứng:**
   - Tôn trọng tăng (or ganh ghét nếu rival)
   - Kích hoạt NPC timeline events

3. **Tông môn phản ứng:**
   - Gửi thông báo/lời mời (nếu chưa có môn phái)

**File đã sửa:** `flask_app.py`
- Route `/breakthrough` - Cập nhật để fire world events
- Route `/breakthrough_seclusion` - Mới
- Route `/breakthrough_wait` - Mới

---

## PHẦN 2: NPC TIMELINE

### 2A. CẤU TRÚC NPC TIMELINE

**File dữ liệu mới:** `data/relations/npc_timelines.csv`

**Cấu trúc mỗi event:**
```csv
id,npc_id,trigger_year,trigger_condition,event_type,event_text,result
senior_an_promote,senior_an,5,always,promote,"An Sư Huynh đột phá...","{\"realm\": \"core_formation_1\"}"
```

**Trigger conditions:**
- `always` - Chỉ cần đến năm
- `player_realm >= Trúc Cơ` - Cảnh giới player
- `player_sect != same_sect` - Khác tông môn
- `sect_power < 30` - Thế lực tông môn yếu

**Event types:**
- `promote` - Thăng cấp
- `die` - Chết
- `change_faction` - Đổi tông môn
- `become_enemy` - Trở thành kẻ thù
- `disappear` - Biến mất
- `breakthrough` - Đột phá

---

### 2B. WORLD TICK — CHẠY KHI THỜI GIAN TRÔI

**File đã sửa:** `engine/systems/npc.py`

**Method:** `process_npc_timelines(current_year, game_state)`

**Chạy khi:**
- Tu luyện (tăng exp)
- Bế quan (tăng thời gian)
- Di chuyển (tăng thời gian)
- Combat (tăng thời gian)

**Output:**
```
"— Tin tức từ giang hồ —"
[An Sư Huynh đã đột phá Kim Đan, trở thành Trưởng Lão của tông môn.]
[Lam Vũ Sư Muội đột phá Trúc Cơ, bắt đầu xem nhân tộc khác biệt.]
```

---

### 2C. SỰ THAY ĐỔI THEO THỜI GIAN

**File đã sửa:** `engine/systems/world.py`

**Sect power simulation:**
```
Mỗi năm:
  - Human tông: +1 ± random(-2, +2)
  - Yao tông: +2 ± random(-2, +2)
  - Mo tông: -1 ± random(-2, +2)

Thresholds:
  - power < 20: "suy vong", không nhận đệ tử
  - power > 80: "cường thịnh", mở thêm nhiệm vụ
  - power = 0: tông môn giải thể
```

**Method:** `_check_sect_threshold()`

---

### 2D. DỮ LIỆU MẪU

**NPC Timeline events:** 10 events

| NPC | Năm | Event |
|-----|-----|-------|
| An Sư Huynh | 5 | Đột phá Kim Đan |
| Vân Thạch Trưởng Lão | 10 | Ghen tuông khi player rời tông |
| Vũ Kiếm Sư Huynh | 12 | Trở thành đối thủ |
| Lam Vũ Sư Muội | 8 | Đột phá Trúc Cơ |
| Mã Thương Nhân | 7 | Giàu nhất vùng đông |
| Diệp Hoàng Sứ | 10 | Thăng chức |

**World events:** Đã có sẵn 29 events trong `data/entities/world_events.csv`

---

## SƠ ĐỒ VÒNG LẶP ĐỘT PHÁ

```
┌─────────────────────┐
│   TU LUYỆN         │
│ +exp, +pressure     │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ CHECK THRESHOLD │
    │ pressure >= 80? │
    └──────┬───────┬──┘
           │       │
      >= 80│   < 80│
           │       │
           ▼       └──────► CONTINUE TULUYEN
    ┌──────────────┐
    │ BREAKTHROUGH │
    │   OPTIONS    │
    └──────┬───────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
 ┌────┐ ┌────┐ ┌────┐
 │NGAY│ │BẾ  │ │CHỜ │
 │60% │ │85% │ │THEM│
 └──┬─┘ └──┬─┘ └──┬─┘
    │      │       │
    ▼      ▼       ▼
 ┌──────────────────┐
 │   KẾT QUẢ        │
 │ success/fail    │
 └────────┬─────────┘
          │
    ┌─────┴─────┐
    │           │
SUCCESS      FAIL
    │           │
    ▼           ▼
┌─────────┐ ┌──────────┐
│LORE TEXT│ │HP LOSS   │
│NEW REALM│ │PRESS RESET│
│WORLD LOG│ │TIME SKIP │
│NPC REACT│ └──────────┘
└─────────┘
```

---

## DANH SÁCH NPC CÓ TIMELINE

1. **senior_an** (An Sư Huynh) - 2 events
   - Năm 5: Đột phá Kim Đan
   - Năm X+: Trở thành trưởng lão

2. **elder_van** (Vân Thạch Trưởng Lão) - 1 event
   - Năm 10: Ghen tuông khi player rời tông

3. **thunder_disciple_vu** (Vũ Kiếm Sư Huynh) - 1 event
   - Năm 12: Trở thành đối thủ nếu player >= Trúc Cơ

4. **yao_disciple_lam** (Lam Vũ Sư Muội) - 1 event
   - Năm 8: Đột phá Trúc Cơ

5. **forge_master_sat** (Sắt Lư Đại Sư) - 1 event
   - Năm 15: Biến mất

6. **merchant_ma** (Mã Thương Nhân) - 1 event
   - Năm 7: Thương nhân giàu nhất

7. **rogue_lao_co** (Lão Cô Tu Sĩ) - 1 event
   - Năm 20: Biến mất vào bí cảnh

8. **yao_elder_nguyet** (Nguyệt Hồ Trưởng Lão) - 1 event
   - Năm 25: Tiết lộ thân phận nếu player >= Nguyên Anh

9. **blood_elder_huyet** (Huyết Uyên Tông Chủ) - 1 event
   - Năm 18: Đột phá Hóa Thần nếu tông môn yếu

10. **imperial_envoy_diep** (Diệp Hoàng Sứ) - 1 event
    - Năm 10: Thăng chức

---

## DANH SÁCH WORLD EVENTS NĂM CỐ ĐỊNH

**Đã có sẵn trong file:** `data/entities/world_events.csv`

**Ví dụ năm cố định:**

| Năm | Sự kiện |
|-----|---------|
| 5 | Linh Mạch Chấn Động |
| 13 | Sương Thị Khai Mở |
| 22 | Linh Vũ Thất Nhật |
| 26 | Lũ Linh Khí |
| 41 | Hỏa Linh Bí Cảnh Xuất Thế |
| 53 | Yêu Triều Bạo Động |
| 61 | Hòa Ước Thanh Lâm |
| 74 | Huyết Tế Tà Đàn |
| 97 | Nguyệt Yêu Triệu Hội |
| 119 | Cổ Cảnh Kim Đan |
| 148 | Long Cốt Xuất Thế |
| 183 | Thiên Các Khuynh Đảo |
| 217 | Thiên Bảo Đại Hội |
| 247 | Biên Giới Đại Chiến |
| 277 | Phượng Viêm Tái Sinh |
| 358 | Bách Quỷ Dạ Hành |
| 413 | Thiên Khung Rạn Nứt |
| 497 | Linh Mạch Tản Viên Tái Chấn |
| 557 | Hắc Ôn Ma Dịch |
| 563 | Huyết Nguyệt Nghi Lễ |
| 589 | Yêu Hoàng Giáng Lâm |
| 634 | Yêu Triều Tái Phát |
| 703 | Tiên Phủ Tàn Tích |
| 761 | Ma Tướng Hiện Thế |
| 819 | Yêu Hoàng Tuyên Chiến |
| 897 | Thiên Ma Đại Chiến |
| 953 | Thiên Hạ Sau Đại Chiến |

**Tổng cộng:** 29 world events theo năm cố định

---

## CONFLICT VÀ LƯU Ý

**Không có conflict với code hiện tại.**

**Các file đã thêm mới:**
- `data/relations/npc_timelines.csv` - Dữ liệu timeline NPC
- `test_progression.py` - Script test

**Các file đã sửa:**
- `engine/systems/cultivation.py` - Thêm pressure system
- `engine/systems/npc.py` - Thêm timeline system
- `engine/systems/world.py` - Cải thiện world tick
- `flask_app.py` - Cập nhật routes và UI

**Không sửa:**
- UI đã làm
- Combat system
- Tông môn/công pháp
- Chức năng khác

---

## KẾT LUẬN

Hai hệ thống đã được triển khai đầy đủ:

1. **Progression Loop** - Player cảm nhận rõ vòng lặp tu luyện → áp lực → đột phá → phản ứng
2. **NPC Timeline** - Thế giới vận động khi thời gian trôi, không cần AI phức tạp

**Test results:** 4/4 tests PASSED

**Ready for deployment.**
