import os
import sys

def resource_path(relative_path):
    """Получение абсолютного пути к ресурсу, работает как в разработке, так и в EXE."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Поднимаемся на два уровня вверх от src/pdf/ к Tandem/
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', relative_path)