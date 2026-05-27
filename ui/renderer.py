"""
Console renderer.
"""

from engine.core.loader import Loader


class Renderer:
    _lang = "vi"
    _i18n = None

    @staticmethod
    def t(key: str) -> str:
        if Renderer._i18n is None:
            try:
                Renderer._i18n = Loader.load_json("config/i18n.json")
            except FileNotFoundError:
                Renderer._i18n = {}
        return Renderer._i18n.get(Renderer._lang, {}).get(key, key)

    @staticmethod
    def clear():
        print("\n" + "=" * 50)

    @staticmethod
    def title(text: str):
        print(f"\n  * {text}")
        print("  " + "-" * 40)

    @staticmethod
    def line(text: str = ""):
        print(f"  {text}")

    @staticmethod
    def menu(options: list[str]) -> int:
        for i, opt in enumerate(options, 1):
            print(f"  [{i}] {opt}")
        print()
        while True:
            try:
                choice = input("  -> Chọn: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return idx
                print("  Số không hợp lệ, thử lại.")
            except ValueError:
                print("  Nhập số thôi nhé.")

    @staticmethod
    def confirm(question: str) -> bool:
        ans = input(f"  {question} (y/n): ").strip().lower()
        return ans in ("y", "yes", "co", "có")

    @staticmethod
    def pause():
        input("\n  [Nhấn Enter để tiếp tục...]")
