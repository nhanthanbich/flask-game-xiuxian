# Cải Thiện Hiển Thị - Báo Cáo

## Vấn Đề

Các giá trị trường thô như `qi_refining`, `linh_can_match` được hiển thị trực tiếp cho người dùng, gây khó hiểu.

## Các Thay Đổi

### 1. Sửa Hiển Thị Cảnh Giới (Realm ID)

**File: `flask_app.py`**

#### Save Slot Display
- **Trước:** `slot['realm_id']` → "qi_refining_1"
- **Sau:** `cult.realms.get(slot['realm_id'], {}).get('name_vn', slot['realm_id'])` → "Luyện Khí Sơ Kỳ"
- **Vị trí:** Line 106-110 (start_menu function)

#### Enemy Display
- **Trước:** `enemy['realm_id']` → "foundation_2"
- **Sau:** Hiển thị tên tiếng Việt "Trúc Cơ Trung Kỳ"
- **Vị trí:** Line 2041-2043 (view_combat function)

#### World Sect Display
- **Trước:** `entry_realm` có thể hiển thị ID thô
- **Sau:** Sử dụng `cult.realms.get()` với fallback tốt hơn
- **Vị trí:** Line 1710 (view_world function)

### 2. Dịch Điều Kiện Gia Nhập (Entry Condition)

**File: `flask_app.py`**

#### Hàm translate_entry_condition mới
- Thêm hàm helper để dịch các mã điều kiện thành tiếng Việt dễ đọc
- **Vị trí:** Line 43-74

**Ánh xạ:**
- `linh_can_match` → "Linh căn phù hợp nguyên tố môn phái"
- `quest_and_realm` → "Hoàn thành nhiệm vụ thử luyện"
- `always` → "Không có điều kiện đặc biệt"
- Các điều kiện tiếng Việt đã sẵn sàng được giữ nguyên

#### Áp dụng
- **Trước:** `entry_condition` hiển thị mã thô như "linh_can_match"
- **Sau:** Hiển thị văn bản tiếng Việt dễ hiểu
- **Vị trí:** Line 1711 (đã cập nhật để sử dụng hàm dịch)

### 3. Cải Thiện Hiển Thị Nhiệm Vụ (Quest)

**File: `flask_app.py`**

#### Quest Card
- **Trước:** Chỉ hiển thị số lượng vật phẩm "Vật phẩm: 0/1"
- **Sau:** Hiển thị cả tên vật phẩm "Vật phẩm (Nguyệt Linh Thảo): 0/1"
- Thêm hiển thị phần thưởng vật phẩm
- **Vị trí:** Line 1957-1978 (quest_card function)

### 4. Sửa Hiển Thị Menu Terminal

**File: `ui/tabs/world.py`**

- **Trước:** `s['min_realm']` hiển thị mã thô "qi_refining_1"
- **Sau:** Sử dụng `cult.realm_display()` để lấy tên tiếng Việt "Luyện Khí Sơ Kỳ"
- **Vị trí:** Line 74 (đã cập nhật)
- Thêm import `CultivationSystem` vào WorldTab

## Tóm Tắt Các Cải Thiện

| Thành Phần | Trước | Sau |
|-----------|-------|-----|
| Realm ID | `qi_refining_1` | Luyện Khí Sơ Kỳ |
| Entry Condition | `linh_can_match` | Linh căn phù hợp nguyên tố môn phái |
| Enemy Realm | `foundation_2` | Trúc Cơ Trung Kỳ |
| Quest Target | số lượng 0/1 | Nguyệt Linh Thảo: 0/1 |

## Các File Đã Sửa

1. `flask_app.py` - Thêm hàm dịch, sửa nhiều vị trí hiển thị
2. `ui/tabs/world.py` - Cải thiện hiển thị menu terminal

## Kết Quả

- ✅ Mọi mã cảnh giới được dịch thành tên tiếng Việt
- ✅ Điều kiện gia nhập môn phái hiển thị dễ hiểu
- ✅ Thông tin nhiệm vụ rõ ràng hơn
- ✅ Trải nghiệm người dùng được cải thiện đáng kể
