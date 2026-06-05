"""
main.py
Chạy: python main.py
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Đảm bảo chạy từ thư mục gốc CultivationRPG/
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core.game import Game

if __name__ == "__main__":
    game = Game()
    game.run()
