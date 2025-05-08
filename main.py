import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ttkbootstrap as ttk
from ui import (
    UI,
)

if __name__ == "__main__":
    app = UI()