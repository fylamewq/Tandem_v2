import sys
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
from src.db.database import (
    add_vehicle,
    update_vehicle,
    add_print_history,
    get_works,
    get_materials,
    add_material_and_work,
    get_materials_and_works,
    get_vehicle_by_id,
    get_all_vehicles,
    delete_materials_and_works,
)
from src.pdf.report_generator import generate_pdf
from tkinter import messagebox
import os
from src.utils.utils import (
    validate_date,
    validate_phone,
    select_all,
    copy_text,
    paste_text,
    cut_text,
)


class AddPage:
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.add_frame = main_window.add_frame
        self.vehicle_images = main_window.vehicle_images
        self.work_rows = 1
        self.parts_rows = 1
        self.init_add_page()

    def create_context_menu(self, entry):
        """Создание контекстного меню для поля ввода"""
        menu = ttk.Menu(entry, tearoff=0)
        menu.add_command(label="Вырезать", command=lambda: cut_text(entry))
        menu.add_command(label="Копировать", command=lambda: copy_text(entry))
        menu.add_command(label="Вставить", command=lambda: paste_text(entry))

        entry.bind(
            "<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root)
        )

    def bind_hotkeys(self, entry: ttk.Entry) -> None:
        # Английская раскладка
        entry.bind("<Control-x>", lambda event: cut_text(entry))
        entry.bind("<Control-c>", lambda event: copy_text(entry))
        entry.bind("<Control-v>", lambda event: paste_text(entry))
        # Поддержка Caps Lock (для английской раскладки)
        entry.bind("<Control-X>", lambda event: cut_text(entry))
        entry.bind("<Control-C>", lambda event: copy_text(entry))
        entry.bind("<Control-V>", lambda event: paste_text(entry))
        # Русская раскладка
        entry.bind("<Control-Cyrillic_CHE>", lambda event: cut_text(entry))  # Ctrl+Ч
        entry.bind("<Control-Cyrillic_ES>", lambda event: copy_text(entry))  # Ctrl+С
        entry.bind("<Control-Cyrillic_EM>", lambda event: paste_text(entry))  # Ctrl+М
        # Поддержка Caps Lock (для русской раскладки)
        entry.bind("<Control-Cyrillic_CHE>", lambda event: cut_text(entry))
        entry.bind("<Control-Cyrillic_ES>", lambda event: copy_text(entry))
        entry.bind("<Control-Cyrillic_EM>", lambda event: paste_text(entry))

    def init_add_page(self):
        # Левый блок: Характеристики ТС
        characteristics_frame = ttk.Frame(self.add_frame, style="Custom.TFrame")
        characteristics_frame.pack(side=LEFT, fill=Y, padx=(0, 20), expand=False)

        self.characteristics_canvas = ttk.Canvas(characteristics_frame)
        characteristics_scrollbar = ttk.Scrollbar(
            characteristics_frame,
            orient="vertical",
            command=self.characteristics_canvas.yview,
        )
        characteristics_scrollable_frame = ttk.Frame(
            self.characteristics_canvas, style="Custom.TFrame"
        )

        self.characteristics_canvas.create_window(
            (0, 0), window=characteristics_scrollable_frame, anchor="nw"
        )
        characteristics_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.characteristics_canvas.configure(
                scrollregion=self.characteristics_canvas.bbox("all")
            ),
        )
        self.characteristics_canvas.configure(
            yscrollcommand=characteristics_scrollbar.set
        )

        self.characteristics_canvas.bind("<Enter>", self.main_window._on_canvas_enter)
        self.characteristics_canvas.bind("<Leave>", self.main_window._on_canvas_leave)

        self.characteristics_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        characteristics_scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            characteristics_scrollable_frame,
            text="Характеристики ТС",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=10)

        self.add_entries = {}
        fields = [
            ("Договор-Заявка №", ""),
            ("Дата", datetime.now().strftime("%d.%m.%Y")),
            ("Дата приёма", ""),
            ("Дата наряда работ", ""),
            ("Дата окончания работ", ""),
            ("Тип машины", "Легковые"),
            ("Заказчик", ""),
            ("Адрес", ""),
            ("Государственный номер", ""),
            ("Марка", ""),
            ("Марка холодильной машины", ""),
            ("Год выпуска", ""),
            ("Пробег", ""),
            ("Сотовый телефон", ""),
            ("Предварительный осмотр (обнаруженная неисправность)", ""),
            ("Оборудование сдал:", ""),
            ("Рекомендации:", ""),
            ("Представитель Исполнителя (Должность):", ""),
            ("Представитель Исполнителя (Ф.И.О.):", ""),
            ("Представитель Заказчика (Должность):", ""),
            ("Представитель Заказчика (Ф.И.О.):", ""),
        ]

        vcmd_phone = (self.root.register(validate_phone), "%P", "%S")
        for field_name, default_value in fields:
            ttk.Label(characteristics_scrollable_frame, text=f"{field_name}:").pack(
                anchor="w", padx=20, pady=5
            )
            entry = ttk.Entry(characteristics_scrollable_frame, style="Custom.TEntry")
            entry.pack(fill=X, padx=20, pady=4)
            entry.insert(0, default_value)
            self.add_entries[field_name] = entry
            if "Дата" in field_name:
                vcmd_date = (
                    self.root.register(
                        lambda char, val, w=entry: validate_date(char, val, w)
                    ),
                    "%S",
                    "%P",
                )
                entry.configure(validate="key", validatecommand=vcmd_date)
            if field_name == "Сотовый телефон":
                entry.configure(validate="key", validatecommand=vcmd_phone)
            entry.bind("<Control-a>", lambda event: select_all(event))
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if field_name == "Тип машины":
                entry.bind("<KeyRelease>", self.show_type_suggestions)
                entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                entry.bind("<Return>", lambda e: self.select_type_suggestion())

        # Правый блок: Акт
        act_frame = ttk.Frame(self.add_frame, style="Custom.TFrame")
        act_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.act_canvas = ttk.Canvas(act_frame)
        act_scrollbar = ttk.Scrollbar(
            act_frame, orient="vertical", command=self.act_canvas.yview
        )
        act_scrollable_frame = ttk.Frame(self.act_canvas, style="Custom.TFrame")

        self.act_canvas.create_window((0, 0), window=act_scrollable_frame, anchor="nw")
        act_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.act_canvas.configure(
                scrollregion=self.act_canvas.bbox("all")
            ),
        )
        self.act_canvas.configure(yscrollcommand=act_scrollbar.set)

        self.act_canvas.bind("<Enter>", self.main_window._on_canvas_enter)
        self.act_canvas.bind("<Leave>", self.main_window._on_canvas_leave)

        self.act_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        act_scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            act_scrollable_frame, text="Выполненные работы", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=20, pady=10)

        ttk.Button(
            act_scrollable_frame,
            text="Добавить строку",
            style="Print.TButton",
            command=self.add_work_row,
        ).pack(anchor="w", padx=20, pady=5)

        work_headers = [
            "№ п/п",
            "Наименование выполненных работ",
            "Ед. изм.",
            "Кол-во",
            "Цена за ед.",
            "Сумма",
            "Параметры оборудования",
            "Параметры оборудования",
            "",
        ]
        self.work_frame = ttk.Frame(act_scrollable_frame)
        self.work_frame.pack(fill=X, padx=20)

        for col, header in enumerate(work_headers):
            ttk.Label(
                self.work_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=0, column=col, sticky="nsew")

        self.work_entries = []
        self.work_delete_buttons = []
        self.create_work_rows()

        total_frame = ttk.Frame(act_scrollable_frame)
        total_frame.pack(fill=X, padx=20)

        ttk.Label(
            total_frame,
            text="ИТОГО",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=0, column=1, sticky="nsew")
        self.work_total_sum = ttk.Entry(total_frame, width=10)
        self.work_total_sum.grid(row=0, column=5, sticky="nsew", padx=1, pady=1)
        self.bind_hotkeys(self.work_total_sum)
        self.create_context_menu(self.work_total_sum)

        ttk.Label(
            total_frame,
            text="ИТОГО с коэф",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=1, column=1, sticky="nsew")
        self.work_total_with_coeff = ttk.Entry(total_frame, width=10)
        self.work_total_with_coeff.grid(row=1, column=5, sticky="nsew", padx=1, pady=1)
        self.bind_hotkeys(self.work_total_with_coeff)
        self.create_context_menu(self.work_total_with_coeff)

        ttk.Label(
            total_frame,
            text="Коэффициент",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=2, column=1, sticky="nsew")
        self.coefficient_entry = ttk.Entry(total_frame, width=10)
        self.coefficient_entry.grid(row=2, column=5, sticky="nsew", padx=1, pady=1)
        self.coefficient_entry.insert(0, "1.2")
        self.bind_hotkeys(self.coefficient_entry)
        self.create_context_menu(self.coefficient_entry)
        vcmd_coeff = (self.root.register(self.validate_coefficient), "%P")
        self.coefficient_entry.configure(validate="key", validatecommand=vcmd_coeff)
        self.coefficient_entry.bind("<KeyRelease>", self.calculate_work_total)

        ttk.Label(
            act_scrollable_frame,
            text="Накладная на запасные части и расходные материалы",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=10)

        ttk.Button(
            act_scrollable_frame,
            text="Добавить строку",
            style="Print.TButton",
            command=self.add_parts_row,
        ).pack(anchor="w", padx=20, pady=5)

        parts_headers = [
            "№ п/п",
            "Наименование",
            "Ед. изм.",
            "Кол-во",
            "Цена за ед.",
            "Сумма",
            "",
        ]
        self.parts_frame = ttk.Frame(act_scrollable_frame)
        self.parts_frame.pack(fill=X, padx=20)

        for col, header in enumerate(parts_headers):
            ttk.Label(
                self.parts_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=0, column=col, sticky="nsew")

        self.parts_entries = []
        self.parts_delete_buttons = []
        self.create_parts_rows()

        ttk.Label(
            self.parts_frame,
            text="ИТОГО",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=self.parts_rows + 1, column=1, sticky="nsew")
        self.parts_total_sum = ttk.Entry(self.parts_frame, width=10)
        self.parts_total_sum.grid(
            row=self.parts_rows + 1, column=5, sticky="nsew", padx=1, pady=1
        )
        self.bind_hotkeys(self.parts_total_sum)
        self.create_context_menu(self.parts_total_sum)

        ttk.Label(
            self.parts_frame,
            text="ИТОГО по наряд-заказу:",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=self.parts_rows + 2, column=1, sticky="nsew")
        self.order_total_sum = ttk.Entry(self.parts_frame, width=10)
        self.order_total_sum.grid(
            row=self.parts_rows + 2, column=5, sticky="nsew", padx=1, pady=1
        )
        self.bind_hotkeys(self.order_total_sum)
        self.create_context_menu(self.order_total_sum)

        button_frame = ttk.Frame(act_scrollable_frame)
        button_frame.pack(anchor="e", padx=20, pady=20)

        ttk.Button(
            button_frame,
            text="Очистить",
            style="Print.TButton",
            command=self.clear_form,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Сохранить",
            style="Print.TButton",
            command=self.save_vehicle,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Печать",
            style="Print.TButton",
            command=self.save_and_print_vehicle,
        ).pack(side=LEFT, padx=5)

    def validate_number(self, value):
        """Валидация числовых полей: только цифры и одна точка"""
        if value == "":
            return True
        value = value.replace(",", ".")
        parts = value.split(".")
        if len(parts) > 2:
            return False
        for i, part in enumerate(parts):
            if i == 0 and part == "":
                continue
            if not part.isdigit():
                return False
        return True

    def create_work_rows(self):
        """Создание строк для таблицы 'Выполненные работы'"""
        vcmd_number = (self.root.register(self.validate_number), "%P")
        for row in range(self.work_rows):
            row_entries = []
            ttk.Label(
                self.work_frame,
                text=str(row + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row + 1, column=0, sticky="nsew")
            for col in range(1, 8):
                entry = ttk.Entry(self.work_frame, width=15 if col == 1 else 10)
                entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
                entry.insert(0, "")
                row_entries.append(entry)
                self.bind_hotkeys(entry)
                self.create_context_menu(entry)
                if col == 1:
                    self.bind_suggestion_events(entry, row, "work")
                    entry.focus_set()
                if col in [3, 4]:
                    entry.configure(validate="key", validatecommand=vcmd_number)
                    entry.bind(
                        "<KeyRelease>", lambda e, r=row: self.calculate_work_row(r)
                    )
            self.work_entries.append(row_entries)
            delete_button = ttk.Button(
                self.work_frame,
                text="X",
                style="Delete.TButton",
                width=2,
                command=lambda r=row: self.delete_work_row(r),
            )
            delete_button.grid(row=row + 1, column=8, sticky="nsew", padx=1, pady=1)
            self.work_delete_buttons.append(delete_button)

    def create_parts_rows(self):
        """Создание строк для таблицы 'Запасные части'"""
        vcmd_number = (self.root.register(self.validate_number), "%P")
        for row in range(self.parts_rows):
            row_entries = []
            ttk.Label(
                self.parts_frame,
                text=str(row + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row + 1, column=0, sticky="nsew")
            for col in range(1, 6):
                entry = ttk.Entry(self.parts_frame, width=15 if col == 1 else 10)
                entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
                entry.insert(0, "")
                row_entries.append(entry)
                self.bind_hotkeys(entry)
                self.create_context_menu(entry)
                if col == 1:
                    self.bind_suggestion_events(entry, row, "material")
                    entry.focus_set()
                if col in [3, 4]:
                    entry.configure(validate="key", validatecommand=vcmd_number)
                    entry.bind(
                        "<KeyRelease>", lambda e, r=row: self.calculate_parts_row(r)
                    )
            self.parts_entries.append(row_entries)
            delete_button = ttk.Button(
                self.parts_frame,
                text="X",
                style="Delete.TButton",
                width=2,
                command=lambda r=row: self.delete_parts_row(r),
            )
            delete_button.grid(row=row + 1, column=6, sticky="nsew", padx=1, pady=1)
            self.parts_delete_buttons.append(delete_button)

    def add_work_row(self):
        """Добавление новой строки в таблицу 'Выполненные работы'"""
        self.work_rows += 1
        row = self.work_rows - 1
        row_entries = []
        ttk.Label(
            self.work_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5
        ).grid(row=row + 1, column=0, sticky="nsew")

        vcmd_number = (self.root.register(self.validate_number), "%P")
        for col in range(1, 8):
            entry = ttk.Entry(self.work_frame, width=15 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if col == 1:
                self.bind_suggestion_events(entry, row, "work")
            if col in [3, 4]:
                entry.configure(validate="key", validatecommand=vcmd_number)
                entry.bind("<KeyRelease>", lambda e, r=row: self.calculate_work_row(r))
        self.work_entries.append(row_entries)
        delete_button = ttk.Button(
            self.work_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda r=row: self.delete_work_row(r),
        )
        delete_button.grid(row=row + 1, column=8, sticky="nsew", padx=1, pady=1)
        self.work_delete_buttons.append(delete_button)

        # Обновляем канвас и прокручиваем к новой строке
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))
        self.act_canvas.yview_moveto(1.0)
        self.root.update_idletasks()  # Принудительное обновление интерфейса
        self.work_entries[row][0].focus_set()  # Установка фокуса на поле "Наименование"

    def add_parts_row(self):
        """Добавление новой строки в таблицу 'Запасные части'"""
        self.parts_rows += 1
        row = self.parts_rows - 1
        row_entries = []
        ttk.Label(
            self.parts_frame,
            text=str(row + 1),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=row + 1, column=0, sticky="nsew")

        vcmd_number = (self.root.register(self.validate_number), "%P")
        for col in range(1, 6):
            entry = ttk.Entry(self.parts_frame, width=15 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if col == 1:
                self.bind_suggestion_events(entry, row, "material")
                entry.focus_set()
            if col in [3, 4]:
                entry.configure(validate="key", validatecommand=vcmd_number)
                entry.bind("<KeyRelease>", lambda e, r=row: self.calculate_parts_row(r))
        self.parts_entries.append(row_entries)
        delete_button = ttk.Button(
            self.parts_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda r=row: self.delete_parts_row(r),
        )
        delete_button.grid(row=row + 1, column=6, sticky="nsew", padx=1, pady=1)
        self.parts_delete_buttons.append(delete_button)

        self.parts_total_sum.grid_forget()
        self.order_total_sum.grid_forget()
        ttk.Label(
            self.parts_frame,
            text="ИТОГО",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=self.parts_rows + 1, column=1, sticky="nsew")
        self.parts_total_sum.grid(
            row=self.parts_rows + 1, column=5, sticky="nsew", padx=1, pady=1
        )
        ttk.Label(
            self.parts_frame,
            text="ИТОГО по наряд-заказу:",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=self.parts_rows + 2, column=1, sticky="nsew")
        self.order_total_sum.grid(
            row=self.parts_rows + 2, column=5, sticky="nsew", padx=1, pady=1
        )
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    def delete_work_row(self, row):
        """Удаление строки из таблицы 'Выполненные работы'"""
        if self.work_rows <= 1:
            return
        for entry in self.work_entries[row]:
            entry.grid_forget()
        self.work_delete_buttons[row].grid_forget()
        self.work_entries.pop(row)
        self.work_delete_buttons.pop(row)
        self.work_rows -= 1
        for i in range(row, self.work_rows):
            ttk.Label(
                self.work_frame,
                text=str(i + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=i + 1, column=0, sticky="nsew")
            for col, entry in enumerate(self.work_entries[i]):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
                if col == 0:
                    self.bind_suggestion_events(entry, i, "work")
                if col in [2, 3]:
                    entry.bind(
                        "<KeyRelease>", lambda e, r=i: self.calculate_work_row(r)
                    )
            self.work_delete_buttons[i].grid(
                row=i + 1, column=8, sticky="nsew", padx=1, pady=1
            )
            self.work_delete_buttons[i].configure(
                command=lambda r=i: self.delete_work_row(r)
            )
        self.calculate_work_total()
        self.calculate_order_total()
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    def delete_parts_row(self, row):
        """Удаление строки из таблицы 'Запасные части'"""
        if self.parts_rows <= 1:
            return
        for entry in self.parts_entries[row]:
            entry.grid_forget()
        self.parts_delete_buttons[row].grid_forget()
        self.parts_entries.pop(row)
        self.parts_delete_buttons.pop(row)
        self.parts_rows -= 1
        for i in range(row, self.parts_rows):
            ttk.Label(
                self.parts_frame,
                text=str(i + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=i + 1, column=0, sticky="nsew")
            for col, entry in enumerate(self.parts_entries[i]):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
                if col == 0:
                    self.bind_suggestion_events(entry, i, "material")
                if col in [2, 3]:
                    entry.bind(
                        "<KeyRelease>", lambda e, r=i: self.calculate_parts_row(r)
                    )
            self.parts_delete_buttons[i].grid(
                row=i + 1, column=6, sticky="nsew", padx=1, pady=1
            )
            self.parts_delete_buttons[i].configure(
                command=lambda r=i: self.delete_parts_row(r)
            )
        self.parts_total_sum.grid_forget()
        self.order_total_sum.grid_forget()
        ttk.Label(
            self.parts_frame,
            text="ИТОГО",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=self.parts_rows + 1, column=1, sticky="nsew")
        self.parts_total_sum.grid(
            row=self.parts_rows + 1, column=5, sticky="nsew", padx=1, pady=1
        )
        ttk.Label(
            self.parts_frame,
            text="ИТОГО по наряд-заказу:",
            font=("Arial", 10, "bold"),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=self.parts_rows + 2, column=1, sticky="nsew")
        self.order_total_sum.grid(
            row=self.parts_rows + 2, column=5, sticky="nsew", padx=1, pady=1
        )
        self.calculate_parts_total()
        self.calculate_order_total()
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    def validate_coefficient(self, value):
        """Валидация коэффициента: только числа (целые или десятичные)"""
        if value == "":
            return True
        try:
            float(value.replace(",", "."))
            return True
        except ValueError:
            return False

    def show_type_suggestions(self, event):
        """Показать подсказки для типа машины"""
        entry = event.widget
        text = entry.get().lower()
        suggestions = [t for t in self.vehicle_images.keys() if text in t.lower()]
        if not suggestions:
            self.hide_suggestions()
            return

        if hasattr(self, "suggestion_frame"):
            self.suggestion_frame.destroy()

        self.suggestion_frame = ttk.Frame(entry.master)
        self.suggestion_frame.place(
            x=entry.winfo_x(),
            y=entry.winfo_y() + entry.winfo_height(),
            width=entry.winfo_width(),
        )

        self.suggestion_labels = []
        for suggestion in suggestions:
            label = ttk.Label(
                self.suggestion_frame,
                text=suggestion,
                background="white",
                padding=5,
            )
            label.pack(fill=X)
            label.bind(
                "<Button-1>", lambda e, s=suggestion: self.select_type_suggestion(s)
            )
            self.suggestion_labels.append(label)

        self.selected_suggestion = -1

    def hide_suggestions(self):
        """Скрыть подсказки"""
        if hasattr(self, "suggestion_frame"):
            self.suggestion_frame.destroy()
            del self.suggestion_frame

    def bind_suggestion_events(self, entry, row, suggestion_type):
        """Привязка событий для автоподсказок"""
        if suggestion_type == "work":
            entry.bind(
                "<KeyRelease>", lambda e, r=row: self.show_work_suggestions(e, r)
            )
            entry.bind("<Return>", lambda e, r=row: self.select_work_suggestion(r))
        elif suggestion_type == "material":
            entry.bind(
                "<KeyRelease>", lambda e, r=row: self.show_material_suggestions(e, r)
            )
            entry.bind("<Return>", lambda e, r=row: self.select_material_suggestion(r))
        # Привязываем стрелки только к полю ввода
        entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
        entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
        # Предотвращаем потерю фокуса
        entry.bind(
            "<FocusOut>",
            lambda e: (
                self.hide_suggestions()
                if not self.suggestion_frame_contains(e.x_root, e.y_root)
                else None
            ),
        )

    def suggestion_frame_contains(self, x_root, y_root):
        """Проверяет, находится ли курсор внутри фрейма подсказок"""
        if hasattr(self, "suggestion_frame") and self.suggestion_frame.winfo_exists():
            frame_x = self.suggestion_frame.winfo_rootx()
            frame_y = self.suggestion_frame.winfo_rooty()
            frame_width = self.suggestion_frame.winfo_width()
            frame_height = self.suggestion_frame.winfo_height()
            return (
                frame_x <= x_root <= frame_x + frame_width
                and frame_y <= y_root <= frame_y + frame_height
            )
        return False

    def move_suggestion_selection(self, direction):
        """Перемещение по списку подсказок"""
        if not hasattr(self, "suggestion_labels") or not self.suggestion_labels:
            return
        # Снимаем выделение с текущей подсказки
        if self.selected_suggestion >= 0:
            self.suggestion_labels[self.selected_suggestion].configure(
                background="white"
            )
        # Обновляем индекс
        self.selected_suggestion = (self.selected_suggestion + direction) % len(
            self.suggestion_labels
        )
        # Выделяем новую подсказку
        self.suggestion_labels[self.selected_suggestion].configure(background="#D3D3D3")
        # Прокручиваем канвас, чтобы подсказка была видна
        suggestion_canvas = self.suggestion_frame.winfo_children()[0]
        suggestion_canvas.yview_moveto(
            self.selected_suggestion / len(self.suggestion_labels)
        )

    def select_type_suggestion(self, suggestion=None):
        """Выбор типа машины из подсказок"""
        if suggestion is None:
            if self.selected_suggestion >= 0:
                suggestion = self.suggestion_labels[self.selected_suggestion].cget(
                    "text"
                )
            else:
                return

        self.add_entries["Тип машины"].delete(0, END)
        self.add_entries["Тип машины"].insert(0, suggestion)
        self.hide_suggestions()

    def show_work_suggestions(self, event, row):
        """Показать подсказки для наименования работ"""
        entry = event.widget
        text = entry.get().lower().strip()
        works = get_works()  # Предполагается, что это получает список работ
        suggestions = [w["name"] for w in works if text in w["name"].lower().strip()]
        if not suggestions and text:
            suggestions = [w["name"] for w in works]
        suggestions = suggestions[:8]  # Ограничение до 8 подсказок
        if not suggestions:
            self.hide_suggestions()
            return
        print(f"Showing suggestions for row {row}")

        # Уничтожаем существующий фрейм с подсказками
        if hasattr(self, "suggestion_frame"):
            self.suggestion_frame.destroy()

        # Создаем фрейм с подсказками
        self.suggestion_frame = ttk.Frame(entry.master)
        self.suggestion_frame.place(
            x=entry.winfo_x(),
            y=entry.winfo_y() + entry.winfo_height(),
            width=entry.winfo_width(),
            height=min(len(suggestions) * 30, 160),  # Динамическая высота, макс. 160
        )

        # Создаем прокручиваемый канвас
        suggestion_canvas = tk.Canvas(self.suggestion_frame)
        scrollbar = ttk.Scrollbar(
            self.suggestion_frame, orient="vertical", command=suggestion_canvas.yview
        )
        scrollable_frame = ttk.Frame(suggestion_canvas)

        suggestion_canvas.configure(yscrollcommand=scrollbar.set)
        suggestion_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        suggestion_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: suggestion_canvas.configure(
                scrollregion=suggestion_canvas.bbox("all")
            ),
        )

        # Привязка колеса мыши
        suggestion_canvas.bind(
            "<MouseWheel>",
            lambda e: suggestion_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            ),
        )

        # Добавляем метки с подсказками
        self.suggestion_labels = []
        for suggestion in suggestions:
            label = ttk.Label(
                scrollable_frame, text=suggestion, background="white", padding=5
            )
            label.pack(fill=tk.X)
            label.bind(
                "<Button-1>",
                lambda e, s=suggestion, r=row: self.select_work_suggestion(r, s),
            )
            self.suggestion_labels.append(label)

        self.selected_suggestion = -1
        entry.focus_set()  # Устанавливаем фокус на поле ввода

    def select_work_suggestion(self, row, suggestion=None):
        """Выбор наименования работы из подсказок"""
        if row >= len(self.work_entries):
            return
        if suggestion is None:
            if self.selected_suggestion >= 0:
                suggestion = self.suggestion_labels[self.selected_suggestion].cget(
                    "text"
                )
            else:
                return

        works = get_works()
        selected_work = next((w for w in works if w["name"] == suggestion), None)
        if selected_work:
            self.work_entries[row][0].delete(0, END)
            self.work_entries[row][0].insert(0, selected_work["name"])
            self.work_entries[row][1].delete(0, END)
            self.work_entries[row][1].insert(0, selected_work["unit"])
            self.work_entries[row][2].delete(0, END)
            self.work_entries[row][2].insert(0, "1")
            self.work_entries[row][3].delete(0, END)
            self.work_entries[row][3].insert(0, selected_work["price"])
            self.calculate_work_row(row)
        self.hide_suggestions()

    def show_material_suggestions(self, event, row):
        """Показать подсказки для наименования материалов"""
        entry = event.widget
        text = entry.get().lower().strip()
        materials = get_materials()
        suggestions = [
            m["name"] for m in materials if text in m["name"].lower().strip()
        ]
        if not suggestions and text:
            suggestions = [m["name"] for m in materials]
        # Ограничение до 8 подсказок
        suggestions = suggestions[:8]
        if not suggestions:
            self.hide_suggestions()
            return

        if hasattr(self, "suggestion_frame"):
            self.suggestion_frame.destroy()

        self.suggestion_frame = ttk.Frame(entry.master)
        self.suggestion_frame.place(
            x=entry.winfo_x(),
            y=entry.winfo_y() + entry.winfo_height(),
            width=entry.winfo_width(),
        )

        self.suggestion_labels = []
        for suggestion in suggestions:
            label = ttk.Label(
                self.suggestion_frame,
                text=suggestion,
                background="white",
                padding=5,
            )
            label.pack(fill=X)
            label.bind(
                "<Button-1>",
                lambda e, s=suggestion, r=row: self.select_material_suggestion(r, s),
            )
            self.suggestion_labels.append(label)

        self.selected_suggestion = -1

    def select_material_suggestion(self, row, suggestion=None):
        """Выбор наименования материала из подсказок"""
        if row >= len(self.parts_entries):
            return
        if suggestion is None:
            if self.selected_suggestion >= 0:
                suggestion = self.suggestion_labels[self.selected_suggestion].cget(
                    "text"
                )
            else:
                return

        materials = get_materials()
        selected_material = next(
            (m for m in materials if m["name"] == suggestion), None
        )
        if selected_material:
            self.parts_entries[row][0].delete(0, END)
            self.parts_entries[row][0].insert(0, selected_material["name"])
            self.parts_entries[row][1].delete(0, END)
            self.parts_entries[row][1].insert(0, selected_material["unit"])
            self.parts_entries[row][2].delete(0, END)
            self.parts_entries[row][2].insert(0, "1")
            self.parts_entries[row][3].delete(0, END)
            self.parts_entries[row][3].insert(0, selected_material["price"])
            self.calculate_parts_row(row)
        self.hide_suggestions()

    def calculate_work_row(self, row):
        """Подсчёт суммы для строки в таблице 'Выполненные работы'"""
        quantity = self.work_entries[row][2].get().replace(",", ".")
        price = self.work_entries[row][3].get().replace(",", ".")
        try:
            quantity = float(quantity) if quantity else 0
            price = float(price) if price else 0
            total = quantity * price
            self.work_entries[row][4].delete(0, END)
            self.work_entries[row][4].insert(0, f"{total:.2f}")
        except ValueError:
            self.work_entries[row][4].delete(0, END)
            self.work_entries[row][4].insert(0, "0.00")
        self.calculate_work_total()

    def calculate_work_total(self, event=None):
        """Подсчёт ИТОГО и ИТОГО с коэффициентом для таблицы 'Выполненные работы'"""
        total = 0
        for row in self.work_entries:
            try:
                total += float(row[4].get().replace(",", "."))
            except ValueError:
                continue
        self.work_total_sum.delete(0, END)
        self.work_total_sum.insert(0, f"{total:.2f}")

        try:
            coeff = float(self.coefficient_entry.get().replace(",", "."))
        except ValueError:
            coeff = 1
        total_with_coeff = total * coeff
        self.work_total_with_coeff.delete(0, END)
        self.work_total_with_coeff.insert(0, f"{total_with_coeff:.2f}")
        self.calculate_order_total()

    def calculate_parts_row(self, row):
        """Подсчёт суммы для строки в таблице 'Запасные части'"""
        quantity = self.parts_entries[row][2].get().replace(",", ".")
        price = self.parts_entries[row][3].get().replace(",", ".")
        try:
            quantity = float(quantity) if quantity else 0
            price = float(price) if price else 0
            total = quantity * price
            self.parts_entries[row][4].delete(0, END)
            self.parts_entries[row][4].insert(0, f"{total:.2f}")
        except ValueError:
            self.parts_entries[row][4].delete(0, END)
            self.parts_entries[row][4].insert(0, "0.00")
        self.calculate_parts_total()

    def calculate_parts_total(self):
        """Подсчёт ИТОГО для таблицы 'Запасные части'"""
        total = 0
        for row in self.parts_entries:
            try:
                total += float(row[4].get().replace(",", "."))
            except ValueError:
                continue
        self.parts_total_sum.delete(0, END)
        self.parts_total_sum.insert(0, f"{total:.2f}")
        self.calculate_order_total()

    def calculate_order_total(self):
        """Подсчёт ИТОГО по наряд-заказу"""
        try:
            work_total = float(self.work_total_with_coeff.get().replace(",", "."))
        except ValueError:
            work_total = 0
        try:
            parts_total = float(self.parts_total_sum.get().replace(",", "."))
        except ValueError:
            parts_total = 0
        order_total = work_total + parts_total
        self.order_total_sum.delete(0, END)
        self.order_total_sum.insert(0, f"{order_total:.2f}")

    def save_vehicle(self):
        """Сохранение данных о ТС"""
        vehicle_data = self.collect_vehicle_data()
        if not vehicle_data:
            return

        for key in ["work_total", "work_total_with_coeff", "parts_total"]:
            value = vehicle_data.get(key, "")
            if value:
                try:
                    vehicle_data[key] = str(float(value.replace(",", ".")))
                except ValueError:
                    vehicle_data[key] = "0.00"

        try:
            if hasattr(self, "vehicle_id") and self.vehicle_id:
                vehicle_data["id"] = self.vehicle_id
                update_vehicle(vehicle_data)
                delete_materials_and_works(self.vehicle_id)
            else:
                self.vehicle_id = add_vehicle(vehicle_data)

            for row in self.work_entries:
                work = row[0].get()
                unit = row[1].get()
                quantity = row[2].get().replace(",", ".")
                price = row[3].get().replace(",", ".")
                equipment_param1 = row[5].get()
                equipment_param2 = row[6].get()
                if work:
                    add_material_and_work(
                        self.vehicle_id,
                        "",
                        work,
                        unit,
                        quantity,
                        price,
                        equipment_param1,
                        equipment_param2,
                    )

            for row in self.parts_entries:
                material = row[0].get()
                unit = row[1].get()
                quantity = row[2].get().replace(",", ".")
                price = row[3].get().replace(",", ".")
                if material:
                    add_material_and_work(
                        self.vehicle_id,
                        material,
                        "",
                        unit,
                        quantity,
                        price,
                        "",
                        "",
                    )

            messagebox.showinfo("Успех", "Данные успешно сохранены!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении данных: {str(e)}")

    def collect_vehicle_data(self):
        """Сбор данных о ТС из формы"""
        field_mapping = {
            "Договор-Заявка №": "contract_number",
            "Дата": "date",
            "Дата приёма": "acceptance_date",
            "Дата наряда работ": "work_order_date",
            "Дата окончания работ": "completion_date",
            "Тип машины": "type",
            "Заказчик": "customer",
            "Адрес": "address",
            "Государственный номер": "number",
            "Марка": "brand",
            "Марка холодильной машины": "refrigerator_brand",
            "Год выпуска": "year",
            "Пробег": "mileage",
            "Сотовый телефон": "phone",
            "Предварительный осмотр (обнаруженная неисправность)": "preliminary_inspection",
            "Оборудование сдал:": "equipment_delivered",
            "Рекомендации:": "recommendations",
            "Представитель Исполнителя (Должность):": "executor_position",
            "Представитель Исполнителя (Ф.И.О.):": "executor_name",
            "Представитель Заказчика (Должность):": "customer_position",
            "Представитель Заказчика (Ф.И.О.):": "customer_name",
        }

        vehicle_data = {}
        for field_name, db_field in field_mapping.items():
            vehicle_data[db_field] = self.add_entries[field_name].get()

        vehicle_data["work_total"] = self.work_total_sum.get()
        vehicle_data["work_total_with_coeff"] = self.work_total_with_coeff.get()
        vehicle_data["parts_total"] = self.parts_total_sum.get()

        required_fields = [
            "Договор-Заявка №",
            "Дата",
            "Заказчик",
            "Государственный номер",
            "Марка",
        ]
        for field in required_fields:
            if not self.add_entries[field].get():
                messagebox.showerror(
                    "Ошибка", f"Поле '{field}' обязательно для заполнения!"
                )
                return None

        return vehicle_data

    def save_and_print_vehicle(self):
        """Сохранение и печать данных о ТС"""
        self.save_vehicle()
        if not hasattr(self, "vehicle_id") or not self.vehicle_id:
            return

        vehicle_data = get_vehicle_by_id(self.vehicle_id)
        if not vehicle_data:
            messagebox.showerror("Ошибка", "Не удалось загрузить данные для печати!")
            return

        materials_and_works = get_materials_and_works(self.vehicle_id)
        pdf_path = generate_pdf(vehicle_data, materials_and_works)
        if pdf_path:
            add_print_history(vehicle_data, pdf_path)
            os.startfile(pdf_path, "open")

    def clear_form(self):
        """Очистка всех данных в форме с удалением строк таблиц до одной"""
        for entry in self.add_entries.values():
            entry.delete(0, END)

        while self.work_rows > 1:
            self.delete_work_row(self.work_rows - 1)

        for entry in self.work_entries[0]:
            entry.delete(0, END)

        while self.parts_rows > 1:
            self.delete_parts_row(self.parts_rows - 1)

        for entry in self.parts_entries[0]:
            entry.delete(0, END)

        self.work_total_sum.delete(0, END)
        self.work_total_sum.insert(0, "0.00")
        self.work_total_with_coeff.delete(0, END)
        self.work_total_with_coeff.insert(0, "0.00")
        self.parts_total_sum.delete(0, END)
        self.parts_total_sum.insert(0, "0.00")
        self.order_total_sum.delete(0, END)
        self.order_total_sum.insert(0, "0.00")

        self.coefficient_entry.delete(0, END)
        self.coefficient_entry.insert(0, "1.2")

        self.vehicle_id = None

    def load_vehicle(self, vehicle_id):
        """Загрузка данных о ТС для редактирования"""
        self.vehicle_id = vehicle_id
        vehicle_data = get_vehicle_by_id(vehicle_id)
        if not vehicle_data:
            messagebox.showerror("Ошибка", "Не удалось загрузить данные ТС!")
            return

        field_mapping = {
            "contract_number": "Договор-Заявка №",
            "date": "Дата",
            "acceptance_date": "Дата приёма",
            "work_order_date": "Дата наряда работ",
            "completion_date": "Дата окончания работ",
            "type": "Тип машины",
            "customer": "Заказчик",
            "address": "Адрес",
            "number": "Государственный номер",
            "brand": "Марка",
            "refrigerator_brand": "Марка холодильной машины",
            "year": "Год выпуска",
            "mileage": "Пробег",
            "phone": "Сотовый телефон",
            "preliminary_inspection": "Предварительный осмотр (обнаруженная неисправность)",
            "equipment_delivered": "Оборудование сдал:",
            "recommendations": "Рекомендации:",
            "executor_position": "Представитель Исполнителя (Должность):",
            "executor_name": "Представитель Исполнителя (Ф.И.О.):",
            "customer_position": "Представитель Заказчика (Должность):",
            "customer_name": "Представитель Заказчика (Ф.И.О.):",
        }

        for db_field, field_name in field_mapping.items():
            self.add_entries[field_name].delete(0, END)
            self.add_entries[field_name].insert(0, vehicle_data.get(db_field, ""))

        self.work_total_sum.delete(0, END)
        self.work_total_sum.insert(0, vehicle_data.get("work_total", "0.00"))
        self.work_total_with_coeff.delete(0, END)
        self.work_total_with_coeff.insert(
            0, vehicle_data.get("work_total_with_coeff", "0.00")
        )
        self.parts_total_sum.delete(0, END)
        self.parts_total_sum.insert(0, vehicle_data.get("parts_total", "0.00"))

        materials_and_works = get_materials_and_works(vehicle_id)

        while self.work_rows > 1:
            self.delete_work_row(self.work_rows - 1)
        while self.parts_rows > 1:
            self.delete_parts_row(self.parts_rows - 1)

        work_index = 0
        parts_index = 0
        for item in materials_and_works:
            if item["work"]:
                if work_index >= self.work_rows:
                    self.add_work_row()
                row = self.work_entries[work_index]
                row[0].delete(0, END)
                row[0].insert(0, item["work"])
                row[1].delete(0, END)
                row[1].insert(0, item["unit"])
                row[2].delete(0, END)
                row[2].insert(0, item["quantity"])
                row[3].delete(0, END)
                row[3].insert(0, item["price_per_unit"])
                row[5].delete(0, END)
                row[5].insert(0, item["equipment_param1"])
                row[6].delete(0, END)
                row[6].insert(0, item["equipment_param2"])
                self.calculate_work_row(work_index)
                work_index += 1
            elif item["material"]:
                if parts_index >= self.parts_rows:
                    self.add_parts_row()
                row = self.parts_entries[parts_index]
                row[0].delete(0, END)
                row[0].insert(0, item["material"])
                row[1].delete(0, END)
                row[1].insert(0, item["unit"])
                row[2].delete(0, END)
                row[2].insert(0, item["quantity"])
                row[3].delete(0, END)
                row[3].insert(0, item["price_per_unit"])
                self.calculate_parts_row(parts_index)
                parts_index += 1

        self.calculate_work_total()
        self.calculate_parts_total()
        self.calculate_order_total()
