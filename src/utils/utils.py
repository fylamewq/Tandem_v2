import os
import sys


def validate_date(char, current_value, widget):
    """Валидация ввода даты в формате дд.мм.гггг с автоматическим добавлением точек."""
    # Разрешаем ввод только цифр
    if char and not char.isdigit():
        return False

    # Если удаляем символ (Backspace), разрешаем
    if char == "":
        return True

    # Удаляем все нецифровые символы из текущего значения для анализа
    digits = ''.join(filter(str.isdigit, current_value))

    # Если длина введенных цифр больше 8 (ддммгггг), запрещаем дальнейший ввод
    if len(digits) > 8:
        return False

    # Форматируем строку
    formatted = ""
    if len(digits) >= 1:
        formatted += digits[:2]  # День
    if len(digits) >= 3:
        formatted = formatted[:2] + "." + digits[2:4]  # Добавляем точку и месяц
    if len(digits) >= 5:
        formatted = formatted[:5] + "." + digits[4:8]  # Добавляем точку и год

    # Обновляем содержимое поля ввода
    widget.delete(0, "end")
    widget.insert(0, formatted)

    return True


def validate_phone(value, char):
    """Валидация ввода телефона"""
    if char == "":
        return True
    if len(value) == 0 and char != "+":
        return False
    if len(value) > 0 and not char.isdigit():
        return False
    if len(value) >= 12:
        return False
    return True


def select_all(event):
    """Выделение всего текста в поле ввода"""
    widget = event.widget
    widget.select_range(0, "end")
    widget.icursor("end")
    return "break"


def copy_text(widget):
    """Копирование текста из поля ввода"""
    try:
        selected_text = widget.selection_get()
        widget.clipboard_clear()
        widget.clipboard_append(selected_text)
    except:
        pass


def paste_text(widget):
    """Вставка текста в поля ввода"""
    try:
        clipboard_text = widget.clipboard_get()
        if widget.tag_ranges("sel"):
            widget.delete("sel.first", "sel.last")
        widget.insert("insert", clipboard_text)
    except:
        pass


def cut_text(widget):
    """Вырезание текста из поля ввода"""
    try:
        selected_text = widget.selection_get()
        widget.clipboard_clear()
        widget.clipboard_append(selected_text)
        widget.delete("sel.first", "sel.last")
    except:
        pass


def resource_path(relative_path):
    """Получение абсолютного пути к ресурсу, работает как в разработке, так и в .exe"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
    full_path = os.path.normpath(os.path.join(base_path, relative_path))
    return full_path