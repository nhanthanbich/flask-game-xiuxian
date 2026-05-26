"""
time.py
Hệ thống thời gian: ngày - tháng - năm.
Mọi hành động trong game đều gọi advance() để tiêu thụ thời gian.

Lịch nội game:
  - 1 năm = 12 tháng
  - 1 tháng = 30 ngày
  - advance(days=N) là đơn vị cơ bản
  - advance_months(N) là tiện ích tắt
"""


class TimeSystem:
    MONTHS_PER_YEAR = 12
    DAYS_PER_MONTH  = 30

    # Tên tháng phong cách tu tiên
    MONTH_NAMES = [
        "Chính Nguyệt", "Nhị Nguyệt", "Tam Nguyệt", "Tứ Nguyệt",
        "Ngũ Nguyệt",   "Lục Nguyệt", "Thất Nguyệt","Bát Nguyệt",
        "Cửu Nguyệt",   "Thập Nguyệt","Thập Nhất",  "Thập Nhị",
    ]

    def __init__(self, year: int = 1, month: int = 1, day: int = 1):
        self.year        = year
        self.month       = month
        self.day         = day
        self.total_days  = 0

    # ── Tăng thời gian ──────────────────────────────────────────────────
    def advance(self, days: int = 1):
        """Đơn vị cơ bản: tăng N ngày."""
        self.total_days += days
        self.day        += days

        while self.day > self.DAYS_PER_MONTH:
            self.day   -= self.DAYS_PER_MONTH
            self.month += 1
            if self.month > self.MONTHS_PER_YEAR:
                self.month = 1
                self.year += 1

    def advance_months(self, months: int = 1):
        """Tiện ích: tăng N tháng (= N × 30 ngày)."""
        self.advance(months * self.DAYS_PER_MONTH)

    # ── Hiển thị ────────────────────────────────────────────────────────
    def display(self) -> str:
        """Dạng ngắn dùng trong header."""
        return f"Ngày {self.day:02d}/{self.month:02d} — Năm {self.year}"

    def display_full(self) -> str:
        """Dạng đầy đủ phong cách tu tiên."""
        month_name = self.MONTH_NAMES[self.month - 1]
        return f"Ngày {self.day}, {month_name}, Năm {self.year}"

    def display_short(self) -> str:
        """Dạng cực ngắn cho save slot."""
        return f"{self.day:02d}/{self.month:02d}/Năm {self.year}"

    # ── Serialize ───────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "year":       self.year,
            "month":      self.month,
            "day":        self.day,
            "total_days": self.total_days,
        }

    @staticmethod
    def from_dict(data: dict) -> "TimeSystem":
        t = TimeSystem(
            data.get("year",  1),
            data.get("month", 1),
            data.get("day",   1),
        )
        t.total_days = data.get("total_days", 0)
        # backward compat: save cũ dùng total_months
        if "total_months" in data and "total_days" not in data:
            t.total_days = data["total_months"] * TimeSystem.DAYS_PER_MONTH
        return t
