import sys
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import datetime
from tkinter import messagebox
import os
from src.db.database import (
    add_print_history, get_works, get_materials,
    get_materials_and_works, get_vehicle_by_id, save_vehicle
)
from src.ui.suggestion_mixin import SuggestionMixin
from src.pdf.report_generator import generate_pdf
from src.utils.utils import (
    validate_date, validate_phone, bind_hotkeys, create_context_menu
)
import src.utils.table_settings as tbl

def extract_unique_field_from_work(field):
    items = get_works()
    return sorted(set(str(item.get(field, '')).strip() for item in items if item.get(field, '')).union({''}))

def extract_unique_field_from_material(field):
    items = get_materials()
    return sorted(set(str(item.get(field, '')).strip() for item in items if item.get(field, '')).union({''}))

def get_suggestions_for_field(field_type, text):
    text = text.lower()
    if field_type == "work_name":
        return [w["name"] for w in get_works() if not text or text in w["name"].lower()]
    elif field_type == "material_name":
        return [m["name"] for m in get_materials() if not text or text in m["name"].lower()]
    elif field_type in ("unit", "quantity", "price"):
        extractor = {
            "unit": "unit",
            "quantity": "quantity",
            "price": "price",
        }[field_type]
        works = extract_unique_field_from_work(extractor)
        materials = extract_unique_field_from_material(extractor)
        values = set(works + materials)
        return [v for v in values if not text or text in str(v).lower()]
    return []

class AddPage(SuggestionMixin):
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.add_frame = main_window.add_frame
        self.vehicle_images = main_window.vehicle_images
        self.vehicle_id = None
        self.suggestion_toplevel = None
        self.suggestion_listbox = None
        self._suppress_suggestions = False
        self.init_add_page()

    def bind_suggestion_events(self, entry, field_type, row, table_type):
        super().bind_suggestion_events(entry, field_type, row, table_type)

    def validate_number(self, value):
        if value == "": return True
        value = value.replace(",", ".")
        parts = value.split(".")
        if len(parts) > 2: return False
        for i, part in enumerate(parts):
            if i == 0 and part == "": continue
            if not part.isdigit(): return False
        return True

    def validate_coefficient(self, value):
        if value == "":
            return True
        try:
            float(value.replace(",", "."))
            return True
        except ValueError:
            return False

    # ----------- Инициализация формы -----------
    def init_add_page(self):
        self.add_entries = {}
        self.work_entries = []
        self.parts_entries = []
        self.work_delete_buttons = []
        self.parts_delete_buttons = []

        # Frame для характеристик ТС
        characteristics_frame = ttk.Frame(self.add_frame, style="Custom.TFrame")
        characteristics_frame.pack(side=LEFT, fill=Y, padx=(0, 20), expand=False)
        characteristics_canvas = ttk.Canvas(characteristics_frame)
        characteristics_scrollbar = ttk.Scrollbar(characteristics_frame, orient="vertical", command=characteristics_canvas.yview)
        characteristics_scrollable_frame = ttk.Frame(characteristics_canvas, style="Custom.TFrame")
        characteristics_canvas.create_window((0, 0), window=characteristics_scrollable_frame, anchor="nw")
        characteristics_scrollable_frame.bind(
            "<Configure>",
            lambda e: characteristics_canvas.configure(scrollregion=characteristics_canvas.bbox("all")),
        )
        characteristics_canvas.configure(yscrollcommand=characteristics_scrollbar.set)
        characteristics_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        characteristics_scrollbar.pack(side=RIGHT, fill=Y)
        ttk.Label(characteristics_scrollable_frame, text="Характеристики ТС", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)

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
            ("Оборудование сдал", ""),
            ("Рекомендации", ""),
            ("Представитель Исполнителя (Должность)", ""),
            ("Представитель Исполнителя (Ф.И.О.)", ""),
            ("Представитель Заказчика (Должность)", ""),
            ("Представитель Заказчика (Ф.И.О.)", ""),
        ]

        vcmd_phone = (self.root.register(validate_phone), "%P", "%S")
        for field_name, default_value in fields:
            ttk.Label(characteristics_scrollable_frame, text=f"{field_name}:").pack(anchor="w", padx=20, pady=5)
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
            bind_hotkeys(entry)
            create_context_menu(entry)
            if field_name == "Тип машины":
                self.bind_suggestion_events(entry, "type", 0, "vehicle_fields")

        # --- Frame для работ и материалов ---
        act_frame = ttk.Frame(self.add_frame, style="Custom.TFrame")
        act_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.act_canvas = ttk.Canvas(act_frame)
        act_scrollbar = ttk.Scrollbar(act_frame, orient="vertical", command=self.act_canvas.yview)
        act_scrollable_frame = ttk.Frame(self.act_canvas, style="Custom.TFrame")
        self.act_canvas.create_window((0, 0), window=act_scrollable_frame, anchor="nw")
        act_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all")),
        )
        self.act_canvas.configure(yscrollcommand=act_scrollbar.set)
        self.act_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        act_scrollbar.pack(side=RIGHT, fill=Y)

        # --- Таблица работ ---
        ttk.Label(act_scrollable_frame, text="Выполненные работы", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        ttk.Button(act_scrollable_frame, text="Добавить строку", style="Print.TButton", command=self.add_work_row).pack(anchor="w", padx=20, pady=5)
        work_headers = [
            "№ п/п", "Наименование выполненных работ", "Ед. изм.", "Кол-во",
            "Цена за ед.", "Сумма", "Параметры оборудования", "Параметры оборудования", ""
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
        self.create_work_rows()

        # --- Суммы по работам ---
        total_frame = ttk.Frame(act_scrollable_frame)
        total_frame.pack(fill=X, padx=20)
        ttk.Label(total_frame, text="ИТОГО", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=0, column=1, sticky="nsew")
        self.work_total_sum = ttk.Entry(total_frame, width=10)
        self.work_total_sum.grid(row=0, column=5, sticky="nsew", padx=1, pady=1)
        bind_hotkeys(self.work_total_sum)
        create_context_menu(self.work_total_sum)
        ttk.Label(total_frame, text="ИТОГО с коэф", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=1, column=1, sticky="nsew")
        self.work_total_with_coeff = ttk.Entry(total_frame, width=10)
        self.work_total_with_coeff.grid(row=1, column=5, sticky="nsew", padx=1, pady=1)
        bind_hotkeys(self.work_total_with_coeff)
        create_context_menu(self.work_total_with_coeff)
        ttk.Label(total_frame, text="Коэффициент", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=2, column=1, sticky="nsew")
        self.coefficient_entry = ttk.Entry(total_frame, width=10)
        self.coefficient_entry.grid(row=2, column=5, sticky="nsew", padx=1, pady=1)
        self.coefficient_entry.insert(0, "1.2")
        bind_hotkeys(self.coefficient_entry)
        create_context_menu(self.coefficient_entry)
        vcmd_coeff = (self.root.register(self.validate_coefficient), "%P")
        self.coefficient_entry.configure(validate="key", validatecommand=vcmd_coeff)
        self.coefficient_entry.bind("<KeyRelease>", self.calculate_work_total)

        # --- Таблица материалов ---
        ttk.Label(act_scrollable_frame, text="Накладная на запасные части и расходные материалы", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        ttk.Button(act_scrollable_frame, text="Добавить строку", style="Print.TButton", command=self.add_parts_row).pack(anchor="w", padx=20, pady=5)
        parts_headers = [
            "№ п/п", "Наименование", "Ед. изм.", "Кол-во", "Цена за ед.", "Сумма", ""
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
        self.create_parts_rows()

        # --- Суммы по материалам ---
        parts_total_frame = ttk.Frame(act_scrollable_frame)
        parts_total_frame.pack(fill=X, padx=20)
        ttk.Label(parts_total_frame, text="ИТОГО", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=0, column=1, sticky="nsew")
        self.parts_total_sum = ttk.Entry(parts_total_frame, width=10)
        self.parts_total_sum.grid(row=0, column=5, sticky="nsew", padx=1, pady=1)
        bind_hotkeys(self.parts_total_sum)
        create_context_menu(self.parts_total_sum)
        ttk.Label(parts_total_frame, text="ИТОГО по наряд-заказу:", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=1, column=1, sticky="nsew")
        self.order_total_sum = ttk.Entry(parts_total_frame, width=10)
        self.order_total_sum.grid(row=1, column=5, sticky="nsew", padx=1, pady=1)
        bind_hotkeys(self.order_total_sum)
        create_context_menu(self.order_total_sum)

        # --- Кнопки управления ---
        button_frame = ttk.Frame(act_scrollable_frame)
        button_frame.pack(anchor="e", padx=20, pady=20)
        ttk.Button(button_frame, text="Очистить", style="Print.TButton", command=self.clear_form).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Сохранить", style="Print.TButton", command=self.save_vehicle).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Печать", style="Print.TButton", command=self.save_and_print_vehicle).pack(side=LEFT, padx=5)
        self.clear_form()

    # === Динамическое создание строк ===
    def create_work_rows(self):
        self.work_entries = []
        self.work_delete_buttons = []
        for _ in range(tbl.WORK_ROWS):
            self.add_work_row(add_to_global=False)

    def create_parts_rows(self):
        self.parts_entries = []
        self.parts_delete_buttons = []
        for _ in range(tbl.MATERIAL_ROWS):
            self.add_parts_row(add_to_global=False)

    def add_work_row(self, add_to_global=True):
        if add_to_global:
            tbl.WORK_ROWS += 1
        row = len(self.work_entries)
        vcmd_number = (self.root.register(self.validate_number), "%P")
        row_entries = []
        ttk.Label(self.work_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 8):
            entry = ttk.Entry(self.work_frame, width=15 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            bind_hotkeys(entry)
            create_context_menu(entry)
            # ВАЖНО: всегда захватываем row по умолчанию!
            if col == 1:
                self.bind_suggestion_events(entry, "work_name", row=row, table_type="vehicle_works")
            elif col == 2:
                self.bind_suggestion_events(entry, "unit", row=row, table_type="vehicle_works")
            elif col == 3:
                self.bind_suggestion_events(entry, "quantity", row=row, table_type="vehicle_works")
                entry.configure(validate="key", validatecommand=vcmd_number)
                entry.bind("<KeyRelease>", lambda e, ent=entry: self._calculate_work_row_by_entry(ent))
            elif col == 4:
                self.bind_suggestion_events(entry, "price", row=row, table_type="vehicle_works")
                entry.configure(validate="key", validatecommand=vcmd_number)
                entry.bind("<KeyRelease>", lambda e, ent=entry: self._calculate_work_row_by_entry(ent))
            elif col == 5:
                self.bind_suggestion_events(entry, "amount", row=row, table_type="vehicle_works")
        self.work_entries.append(row_entries)
        delete_button = ttk.Button(
            self.work_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda row_entries=row_entries: self._delete_work_row_by_button(row_entries),
        )
        delete_button.grid(row=row + 1, column=8, sticky="nsew", padx=1, pady=1)
        self.work_delete_buttons.append(delete_button)
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    def add_parts_row(self, add_to_global=True):
        if add_to_global:
            tbl.MATERIAL_ROWS += 1
        row = len(self.parts_entries)
        vcmd_number = (self.root.register(self.validate_number), "%P")
        row_entries = []
        ttk.Label(self.parts_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 6):
            entry = ttk.Entry(self.parts_frame, width=40 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            bind_hotkeys(entry)
            create_context_menu(entry)
            # ВАЖНО: всегда захватываем row по умолчанию!
            if col == 1:
                self.bind_suggestion_events(entry, "material_name", row=row, table_type="vehicle_materials")
            elif col == 2:
                self.bind_suggestion_events(entry, "unit", row=row, table_type="vehicle_materials")
            elif col == 3:
                self.bind_suggestion_events(entry, "quantity", row=row, table_type="vehicle_materials")
                entry.configure(validate="key", validatecommand=vcmd_number)
                entry.bind("<KeyRelease>", lambda e, ent=entry: self._calculate_parts_row_by_entry(ent))
            elif col == 4:
                self.bind_suggestion_events(entry, "price", row=row, table_type="vehicle_materials")
                entry.configure(validate="key", validatecommand=vcmd_number)
                entry.bind("<KeyRelease>", lambda e, ent=entry: self._calculate_parts_row_by_entry(ent))
            elif col == 5:
                self.bind_suggestion_events(entry, "amount", row=row, table_type="vehicle_materials")
        self.parts_entries.append(row_entries)
        delete_button = ttk.Button(
            self.parts_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda row_entries=row_entries: self._delete_parts_row_by_button(row_entries),
        )
        delete_button.grid(row=row + 1, column=6, sticky="nsew", padx=1, pady=1)
        self.parts_delete_buttons.append(delete_button)
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    # ----------- Расчёты -----------
    def calculate_work_row(self, row):
        quantity = self.work_entries[row][2].get().replace(",", ".")
        price = self.work_entries[row][3].get().replace(",", ".")
        try:
            quantity = float(quantity) if quantity else 0
            price = float(price) if price else 0
            total = quantity * price
            self.work_entries[row][4].delete(0, tk.END)
            self.work_entries[row][4].insert(0, f"{total:.2f}")
        except ValueError:
            self.work_entries[row][4].delete(0, tk.END)
            self.work_entries[row][4].insert(0, "0.00")
        self.calculate_work_total()

    def _calculate_work_row_by_entry(self, entry):
        for i, row in enumerate(self.work_entries):
            if entry in row:
                self.calculate_work_row(i)
                break

    def calculate_work_total(self, event=None):
        total = 0
        for row in self.work_entries:
            try:
                total += float(row[4].get().replace(",", "."))
            except Exception:
                continue
        self.work_total_sum.delete(0, tk.END)
        self.work_total_sum.insert(0, f"{total:.2f}")
        try:
            coeff = float(self.coefficient_entry.get().replace(",", "."))
        except Exception:
            coeff = 1
        total_with_coeff = total * coeff
        self.work_total_with_coeff.delete(0, tk.END)
        self.work_total_with_coeff.insert(0, f"{total_with_coeff:.2f}")
        self.calculate_order_total()

    def calculate_parts_row(self, row):
        quantity = self.parts_entries[row][2].get().replace(",", ".")
        price = self.parts_entries[row][3].get().replace(",", ".")
        try:
            quantity = float(quantity) if quantity else 0
            price = float(price) if price else 0
            total = quantity * price
            self.parts_entries[row][4].delete(0, tk.END)
            self.parts_entries[row][4].insert(0, f"{total:.2f}")
        except ValueError:
            self.parts_entries[row][4].delete(0, tk.END)
            self.parts_entries[row][4].insert(0, "0.00")
        self.calculate_parts_total()

    def _calculate_parts_row_by_entry(self, entry):
        for i, row in enumerate(self.parts_entries):
            if entry in row:
                self.calculate_parts_row(i)
                break

    def calculate_parts_total(self):
        total = 0
        for row in self.parts_entries:
            try:
                total += float(row[4].get().replace(",", "."))
            except Exception:
                continue
        self.parts_total_sum.delete(0, tk.END)
        self.parts_total_sum.insert(0, f"{total:.2f}")
        self.calculate_order_total()

    def calculate_order_total(self):
        try:
            work_total = float(self.work_total_with_coeff.get().replace(",", "."))
        except Exception:
            work_total = 0
        try:
            parts_total = float(self.parts_total_sum.get().replace(",", "."))
        except Exception:
            parts_total = 0
        order_total = work_total + parts_total
        self.order_total_sum.delete(0, tk.END)
        self.order_total_sum.insert(0, f"{order_total:.2f}")

    # --- удаление строк ---
    def _delete_work_row_by_button(self, row_entries):
        for i, row in enumerate(self.work_entries):
            if row is row_entries:
                self.delete_work_row(i)
                break

    def delete_work_row(self, row):
        if len(self.work_entries) <= 1:
            return
        tbl.WORK_ROWS -= 1
        if not (0 <= row < len(self.work_entries)):
            return
        
        for widget in self.work_frame.grid_slaves(row=row + 1):
            widget.grid_forget()
            widget.destroy()
        
        self.work_delete_buttons[row].destroy()
        
        del self.work_entries[row]
        del self.work_delete_buttons[row]
        
        for widget in self.work_frame.grid_slaves(column=0):
            if int(widget.grid_info()["row"]) == 0: continue
            widget.grid_forget()
            widget.destroy()
            
        for i, (entries, btn) in enumerate(zip(self.work_entries, self.work_delete_buttons)):
            for col, entry in enumerate(entries):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
            btn.grid(row=i + 1, column=8, sticky="nsew", padx=1, pady=1)
            ttk.Label(
                self.work_frame, text=str(i + 1), borderwidth=1, relief="solid", padding=5
            ).grid(row=i + 1, column=0, sticky="nsew")
            
        self.calculate_work_total()
        self.calculate_order_total()
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    def _delete_parts_row_by_button(self, row_entries):
        for i, row in enumerate(self.parts_entries):
            if row is row_entries:
                self.delete_parts_row(i)
                break

    def delete_parts_row(self, row):
        if len(self.parts_entries) <= 1:
            return
        tbl.MATERIAL_ROWS -= 1
        if not (0 <= row < len(self.parts_entries)):
            return
        
        # Удаляем строку
        for widget in self.parts_frame.grid_slaves(row=row + 1):
            widget.grid_forget()
            widget.destroy()
            
        self.parts_delete_buttons[row].destroy()
        
        del self.parts_entries[row]
        del self.parts_delete_buttons[row]

        # Очищаем всю колонку нумерации (чтобы не было дублей)
        for widget in self.parts_frame.grid_slaves(column=0):
            if int(widget.grid_info()["row"]) == 0: continue
            widget.grid_forget()
            widget.destroy()
        
        # Перерисовываем все строки
        for i, (entries, btn) in enumerate(zip(self.parts_entries, self.parts_delete_buttons)):
            for col, entry in enumerate(entries):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
            btn.grid(row=i + 1, column=6, sticky="nsew", padx=1, pady=1)
            # Создаём новый номер строки
            ttk.Label(
                self.parts_frame, text=str(i + 1), borderwidth=1, relief="solid", padding=5
            ).grid(row=i + 1, column=0, sticky="nsew")
        
        self.calculate_parts_total()
        self.calculate_order_total()
        self.act_canvas.configure(scrollregion=self.act_canvas.bbox("all"))

    # --- очистка и заполнение ---
    def clear_form(self):
        for entry in self.add_entries.values():
            entry.delete(0, tk.END)
        while len(self.work_entries) > 1:
            self.delete_work_row(len(self.work_entries) - 1)
        if self.work_entries:
            for entry in self.work_entries[0]:
                entry.delete(0, tk.END)
        while len(self.parts_entries) > 1:
            self.delete_parts_row(len(self.parts_entries) - 1)
        if self.parts_entries:
            for entry in self.parts_entries[0]:
                entry.delete(0, tk.END)
        self.work_total_sum.delete(0, tk.END)
        self.work_total_sum.insert(0, "0.00")
        self.work_total_with_coeff.delete(0, tk.END)
        self.work_total_with_coeff.insert(0, "0.00")
        self.parts_total_sum.delete(0, tk.END)
        self.parts_total_sum.insert(0, "0.00")
        self.order_total_sum.delete(0, tk.END)
        self.order_total_sum.insert(0, "0.00")
        self.coefficient_entry.delete(0, tk.END)
        self.coefficient_entry.insert(0, "1.2")
        self.vehicle_id = None

    # ----------- Сбор данных -----------
    def collect_vehicle_data(self):
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
            "Оборудование сдал": "equipment_delivered",
            "Рекомендации": "recommendations",
            "Представитель Исполнителя (Должность)": "executor_position",
            "Представитель Исполнителя (Ф.И.О.)": "executor_name",
            "Представитель Заказчика (Должность)": "customer_position",
            "Представитель Заказчика (Ф.И.О.)": "customer_name",
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

    # ----------- Загрузка данных -----------
    def load_vehicle(self, vehicle_id):
        self.clear_form()
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
            "equipment_delivered": "Оборудование сдал",
            "recommendations": "Рекомендации",
            "executor_position": "Представитель Исполнителя (Должность)",
            "executor_name": "Представитель Исполнителя (Ф.И.О.)",
            "customer_position": "Представитель Заказчика (Должность)",
            "customer_name": "Представитель Заказчика (Ф.И.О.)",
        }
        for db_field, field_name in field_mapping.items():
            self.add_entries[field_name].delete(0, tk.END)
            self.add_entries[field_name].insert(0, vehicle_data.get(db_field, ""))
        self.work_total_sum.delete(0, tk.END)
        self.work_total_sum.insert(0, vehicle_data.get("work_total", "0.00"))
        self.work_total_with_coeff.delete(0, tk.END)
        self.work_total_with_coeff.insert(
            0, vehicle_data.get("work_total_with_coeff", "0.00")
        )
        self.parts_total_sum.delete(0, tk.END)
        self.parts_total_sum.insert(0, vehicle_data.get("parts_total", "0.00"))
        materials_and_works = get_materials_and_works(vehicle_id)
        while len(self.work_entries) > 1:
            self.delete_work_row(len(self.work_entries) - 1)
        while len(self.parts_entries) > 1:
            self.delete_parts_row(len(self.parts_entries) - 1)
        work_index = 0
        parts_index = 0
        for item in materials_and_works:
            if item["work"]:
                if work_index >= len(self.work_entries):
                    self.add_work_row()
                row = self.work_entries[work_index]
                row[0].delete(0, tk.END)
                row[0].insert(0, item["work"])
                row[1].delete(0, tk.END)
                row[1].insert(0, item["unit"])
                row[2].delete(0, tk.END)
                row[2].insert(0, item["quantity"])
                row[3].delete(0, tk.END)
                row[3].insert(0, item["price_per_unit"])
                row[5].delete(0, tk.END)
                row[5].insert(0, item.get("equipment_param1", ""))
                row[6].delete(0, tk.END)
                row[6].insert(0, item.get("equipment_param2", ""))
                self.calculate_work_row(work_index)
                work_index += 1
            elif item["material"]:
                if parts_index >= len(self.parts_entries):
                    self.add_parts_row()
                row = self.parts_entries[parts_index]
                row[0].delete(0, tk.END)
                row[0].insert(0, item["material"])
                row[1].delete(0, tk.END)
                row[1].insert(0, item["unit"])
                row[2].delete(0, tk.END)
                row[2].insert(0, item["quantity"])
                row[3].delete(0, tk.END)
                row[3].insert(0, item["price_per_unit"])
                self.calculate_parts_row(parts_index)
                parts_index += 1
        self.calculate_work_total()
        self.calculate_parts_total()
        self.calculate_order_total()

    # ----------- Сохранение данных -----------
    def save_vehicle(self):
        vehicle_data = self.collect_vehicle_data()
        if vehicle_data is None:
            return

        if self.vehicle_id:
            vehicle_data["id"] = self.vehicle_id

        # Сбор работ
        works = []
        for row in self.work_entries:
            work_name = row[0].get().strip()
            if work_name:
                works.append({
                    "work": work_name,
                    "unit": row[1].get().strip(),
                    "quantity": row[2].get().strip(),
                    "price_per_unit": row[3].get().strip(),
                    "equipment_param1": row[5].get().strip() if len(row) > 5 else "",
                    "equipment_param2": row[6].get().strip() if len(row) > 6 else "",
                })

        # Сбор материалов
        materials = []
        for row in self.parts_entries:
            material_name = row[0].get().strip()
            if material_name:
                materials.append({
                    "material": material_name,
                    "unit": row[1].get().strip(),
                    "quantity": row[2].get().strip(),
                    "price_per_unit": row[3].get().strip(),
                })

        try:
            self.vehicle_id = save_vehicle(vehicle_data, works, materials)
            messagebox.showinfo("Успех", "Данные успешно сохранены.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

    # ----------- Печать -----------
    def save_and_print_vehicle(self):
        self.save_vehicle()
        if not self.vehicle_id:
            return
        vehicle_data = get_vehicle_by_id(self.vehicle_id)
        if not vehicle_data:
            messagebox.showerror("Ошибка", "Не удалось загрузить данные для печати!")
            return
        materials_and_works = get_materials_and_works(self.vehicle_id)
        pdf_path = generate_pdf(vehicle_data, materials_and_works)
        if pdf_path:
            add_print_history(vehicle_data, pdf_path)
            try:
                os.startfile(pdf_path, "open")
            except Exception:
                os.system(f'xdg-open "{pdf_path}"')
                
    # ----- Получение данных -----
    def get_works(self):
        from src.db.database import get_works
        return get_works()

    def get_materials(self):
        from src.db.database import get_materials
        return get_materials()

    def get_suggestions_for_field(self, field_type, text):
        from pages.add_page import get_suggestions_for_field
        return get_suggestions_for_field(field_type, text)