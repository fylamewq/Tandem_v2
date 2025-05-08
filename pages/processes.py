import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.constants import *
from src.db.database import (
    get_all_vehicles,
    get_materials_and_works,
    add_material_and_work,
    delete_material_and_work,
    get_works,
    get_materials,
    add_work,
    add_material,
    delete_work,
    delete_material,
)
from src.utils.utils import select_all, copy_text, paste_text, cut_text
from tkinter import messagebox, ttk
import sys


class ProcessesPage:
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.processes_frame = main_window.processes_frame
        self.work_rows = 10  # Начальное количество строк для работ
        self.material_rows = 10  # Начальное количество строк для материалов
        self.global_work_rows = 10  # Начальное количество строк для общего списка работ
        self.global_material_rows = (
            10  # Начальное количество строк для общего списка материалов
        )
        self.vehicles = []  # Список ТС для выпадающего списка
        self.active_canvas = None  # Для отслеживания активного Canvas для прокрутки
        self.init_processes_page()

    def init_processes_page(self):
        # Инициализация страницы 'Процессы'
        # Выбор ТС (остаётся сверху)
        vehicle_selection_frame = ttk.Frame(self.processes_frame, style="Custom.TFrame")
        vehicle_selection_frame.grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10
        )

        ttk.Label(
            vehicle_selection_frame, text="Выберите ТС:", font=("Arial", 12)
        ).pack(side=LEFT)
        self.vehicle_combobox = ttk.Combobox(
            vehicle_selection_frame, state="readonly", width=50
        )
        self.vehicle_combobox.pack(side=LEFT, padx=10)
        self.vehicle_combobox.bind("<<ComboboxSelected>>", self.update_vehicle_tables)

        # Настройка сетки 2x2 в processes_frame
        self.processes_frame.grid_rowconfigure(1, weight=1)
        self.processes_frame.grid_rowconfigure(2, weight=1)
        self.processes_frame.grid_columnconfigure(0, weight=1)
        self.processes_frame.grid_columnconfigure(1, weight=1)

        # 1. Работы для ТС (левый верхний угол)
        works_frame = ttk.Frame(self.processes_frame, style="Custom.TFrame")
        works_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.works_canvas = tk.Canvas(works_frame)
        works_scrollbar = ttk.Scrollbar(
            works_frame, orient="vertical", command=self.works_canvas.yview
        )
        works_scrollable_frame = ttk.Frame(self.works_canvas, style="Custom.TFrame")

        self.works_canvas.create_window(
            (0, 0), window=works_scrollable_frame, anchor="nw"
        )
        works_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.works_canvas.configure(
                scrollregion=self.works_canvas.bbox("all")
            ),
        )
        self.works_canvas.configure(yscrollcommand=works_scrollbar.set)
        # Привязка прокрутки при наведении
        self.works_canvas.bind(
            "<Enter>", lambda e: self.set_active_canvas(self.works_canvas)
        )
        self.works_canvas.bind("<Leave>", lambda e: self.set_active_canvas(None))
        # Привязка MouseWheel ко всем дочерним виджетам
        self.bind_mousewheel_recursive(works_scrollable_frame)

        self.works_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        works_scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            works_scrollable_frame, text="Работы (для ТС)", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=20, pady=10)

        ttk.Button(
            works_scrollable_frame,
            text="Добавить строку",
            style="Print.TButton",
            command=self.add_work_row,
        ).pack(anchor="w", padx=20, pady=5)

        work_headers = [
            "№ п/п",
            "Наименование",
            "Ед. изм.",
            "Кол-во",
            "Цена за ед.",
            "",
        ]
        self.work_frame = ttk.Frame(works_scrollable_frame)
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
        self.work_ids = []

        # 2. Общий список работ (правый верхний угол)
        global_works_frame = ttk.Frame(self.processes_frame, style="Custom.TFrame")
        global_works_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.global_works_canvas = tk.Canvas(global_works_frame)
        global_works_scrollbar = ttk.Scrollbar(
            global_works_frame,
            orient="vertical",
            command=self.global_works_canvas.yview,
        )
        global_works_scrollable_frame = ttk.Frame(
            self.global_works_canvas, style="Custom.TFrame"
        )

        self.global_works_canvas.create_window(
            (0, 0), window=global_works_scrollable_frame, anchor="nw"
        )
        global_works_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.global_works_canvas.configure(
                scrollregion=self.global_works_canvas.bbox("all")
            ),
        )
        self.global_works_canvas.configure(yscrollcommand=global_works_scrollbar.set)
        self.global_works_canvas.bind(
            "<Enter>", lambda e: self.set_active_canvas(self.global_works_canvas)
        )
        self.global_works_canvas.bind("<Leave>", lambda e: self.set_active_canvas(None))
        self.bind_mousewheel_recursive(global_works_scrollable_frame)

        self.global_works_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        global_works_scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            global_works_scrollable_frame,
            text="Общий список работ",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=10)

        ttk.Button(
            global_works_scrollable_frame,
            text="Добавить строку",
            style="Print.TButton",
            command=self.add_global_work_row,
        ).pack(anchor="w", padx=20, pady=5)

        global_work_headers = ["№ п/п", "Наименование", "Ед. изм.", "Цена за ед.", ""]
        self.global_work_frame = ttk.Frame(global_works_scrollable_frame)
        self.global_work_frame.pack(fill=X, padx=20)

        for col, header in enumerate(global_work_headers):
            ttk.Label(
                self.global_work_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=0, column=col, sticky="nsew")

        self.global_work_entries = []
        self.global_work_delete_buttons = []
        self.global_work_ids = []

        # 3. Материалы для ТС (левый нижний угол)
        materials_frame = ttk.Frame(self.processes_frame, style="Custom.TFrame")
        materials_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        self.materials_canvas = tk.Canvas(materials_frame)
        materials_scrollbar = ttk.Scrollbar(
            materials_frame, orient="vertical", command=self.materials_canvas.yview
        )
        materials_scrollable_frame = ttk.Frame(
            self.materials_canvas, style="Custom.TFrame"
        )

        self.materials_canvas.create_window(
            (0, 0), window=materials_scrollable_frame, anchor="nw"
        )
        materials_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.materials_canvas.configure(
                scrollregion=self.materials_canvas.bbox("all")
            ),
        )
        self.materials_canvas.configure(yscrollcommand=materials_scrollbar.set)
        self.materials_canvas.bind(
            "<Enter>", lambda e: self.set_active_canvas(self.materials_canvas)
        )
        self.materials_canvas.bind("<Leave>", lambda e: self.set_active_canvas(None))
        self.bind_mousewheel_recursive(materials_scrollable_frame)

        self.materials_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        materials_scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            materials_scrollable_frame,
            text="Материалы (для ТС)",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=10)

        ttk.Button(
            materials_scrollable_frame,
            text="Добавить строку",
            style="Print.TButton",
            command=self.add_material_row,
        ).pack(anchor="w", padx=20, pady=5)

        material_headers = [
            "№ п/п",
            "Наименование",
            "Ед. изм.",
            "Кол-во",
            "Цена за ед.",
            "",
        ]
        self.material_frame = ttk.Frame(materials_scrollable_frame)
        self.material_frame.pack(fill=X, padx=20)

        for col, header in enumerate(material_headers):
            ttk.Label(
                self.material_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=0, column=col, sticky="nsew")

        self.material_entries = []
        self.material_delete_buttons = []
        self.material_ids = []

        # 4. Общий список материалов (правый нижний угол)
        global_materials_frame = ttk.Frame(self.processes_frame, style="Custom.TFrame")
        global_materials_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)

        self.global_materials_canvas = tk.Canvas(global_materials_frame)
        global_materials_scrollbar = ttk.Scrollbar(
            global_materials_frame,
            orient="vertical",
            command=self.global_materials_canvas.yview,
        )
        global_materials_scrollable_frame = ttk.Frame(
            self.global_materials_canvas, style="Custom.TFrame"
        )

        self.global_materials_canvas.create_window(
            (0, 0), window=global_materials_scrollable_frame, anchor="nw"
        )
        global_materials_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.global_materials_canvas.configure(
                scrollregion=self.global_materials_canvas.bbox("all")
            ),
        )
        self.global_materials_canvas.configure(
            yscrollcommand=global_materials_scrollbar.set
        )
        self.global_materials_canvas.bind(
            "<Enter>", lambda e: self.set_active_canvas(self.global_materials_canvas)
        )
        self.global_materials_canvas.bind(
            "<Leave>", lambda e: self.set_active_canvas(None)
        )
        self.bind_mousewheel_recursive(global_materials_scrollable_frame)

        self.global_materials_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        global_materials_scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            global_materials_scrollable_frame,
            text="Общий список материалов",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=10)

        ttk.Button(
            global_materials_scrollable_frame,
            text="Добавить строку",
            style="Print.TButton",
            command=self.add_global_material_row,
        ).pack(anchor="w", padx=20, pady=5)

        global_material_headers = [
            "№ п/п",
            "Наименование",
            "Ед. изм.",
            "Цена за ед.",
            "",
        ]
        self.global_material_frame = ttk.Frame(global_materials_scrollable_frame)
        self.global_material_frame.pack(fill=X, padx=20)

        for col, header in enumerate(global_material_headers):
            ttk.Label(
                self.global_material_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=0, column=col, sticky="nsew")

        self.global_material_entries = []
        self.global_material_delete_buttons = []
        self.global_material_ids = []

        # Кнопка "Сохранить" (переносим под сетку)
        save_frame = ttk.Frame(self.processes_frame, style="Custom.TFrame")
        save_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        ttk.Button(
            save_frame,
            text="Сохранить",
            style="Print.TButton",
            command=self.save_processes,
        ).pack(anchor="e")

        # Инициализация данных
        self.update_vehicle_combobox()
        self.update_global_tables()

    # Метод для установки активного Canvas для прокрутки
    def set_active_canvas(self, canvas):
        self.active_canvas = canvas
        # Перенаправляем прокрутку на активный Canvas
        if canvas:
            self.root.bind("<MouseWheel>", self.on_mousewheel)
        else:
            self.root.unbind("<MouseWheel>")

    # Метод для обработки прокрутки
    def on_mousewheel(self, event):
        if self.active_canvas:
            if event.delta > 0:
                self.active_canvas.yview_scroll(-1, "units")  # Прокрутка вверх
            else:
                self.active_canvas.yview_scroll(1, "units")  # Прокрутка вниз

    # Рекурсивная привязка MouseWheel ко всем дочерним виджетам
    def bind_mousewheel_recursive(self, widget):
        widget.bind("<MouseWheel>", self.on_mousewheel)
        for child in widget.winfo_children():
            self.bind_mousewheel_recursive(child)

    def create_context_menu(self, entry):
        """Создание контекстного меню для поля ввода"""
        menu = tk.Menu(entry, tearoff=0)
        menu.add_command(label="Вырезать", command=lambda: cut_text(entry))
        menu.add_command(label="Копировать", command=lambda: copy_text(entry))
        menu.add_command(label="Вставить", command=lambda: paste_text(entry))
        entry.bind(
            "<Button-3>", lambda event: menu.tk_popup(event.x_root, event.y_root)
        )

    def bind_hotkeys(self, entry):
        """Привязка горячих клавиш для вырезания, копирования и вставки"""
        # Английская раскладка
        entry.bind("<Control-x>", lambda event: cut_text(entry))  # Ctrl+X (вырезать)
        entry.bind("<Control-c>", lambda event: copy_text(entry))  # Ctrl+C (копировать)
        entry.bind("<Control-v>", lambda event: paste_text(entry))  # Ctrl+V (вставить)
        # Поддержка Caps Lock (для английской раскладки)
        entry.bind("<Control-X>", lambda event: cut_text(entry))
        entry.bind("<Control-C>", lambda event: copy_text(entry))
        entry.bind("<Control-V>", lambda event: paste_text(entry))
        # Русская раскладка
        entry.bind(
            "<Control-Cyrillic_CHE>", lambda event: cut_text(entry)
        )  # Ctrl+Ч (вырезать)
        entry.bind(
            "<Control-Cyrillic_ES>", lambda event: copy_text(entry)
        )  # Ctrl+С (копировать)
        entry.bind(
            "<Control-Cyrillic_EM>", lambda event: paste_text(entry)
        )  # Ctrl+М (вставить)
        # Поддержка Caps Lock (для русской раскладки)
        entry.bind("<Control-Cyrillic_CHE>", lambda event: cut_text(entry))
        entry.bind("<Control-Cyrillic_ES>", lambda event: copy_text(entry))
        entry.bind("<Control-Cyrillic_EM>", lambda event: paste_text(entry))

    def update_vehicle_combobox(self):
        """Обновление списка ТС в выпадающем списке"""
        try:
            self.vehicles = get_all_vehicles()
            if not self.vehicles:
                messagebox.showinfo("Информация", "Список транспортных средств пуст.")
                self.vehicle_combobox["values"] = []
                self.vehicle_combobox.set("")
                return
            vehicle_options = [
                f"{v['type']} — {v['customer']}, Заявка № {v['contract_number']}, Гос. номер {v['number']}"
                for v in self.vehicles
            ]
            self.vehicle_combobox["values"] = vehicle_options
            self.vehicle_combobox.set(vehicle_options[0])
            self.update_vehicle_tables()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список ТС: {e}")

    def show_work_suggestions(self, event, row, table_type):
        """Показать подсказки для наименования работ"""
        entry = event.widget
        text = entry.get().lower()
        works = get_works()
        suggestions = [w["name"] for w in works if text in w["name"].lower()]
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
            height=160,
        )

        suggestion_canvas = tk.Canvas(self.suggestion_frame)
        scrollbar = ttk.Scrollbar(
            self.suggestion_frame, orient="vertical", command=suggestion_canvas.yview
        )
        scrollable_frame = ttk.Frame(suggestion_canvas)

        suggestion_canvas.configure(yscrollcommand=scrollbar.set)
        suggestion_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        suggestion_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: suggestion_canvas.configure(
                scrollregion=suggestion_canvas.bbox("all")
            ),
        )

        # Привязка прокрутки мышью
        suggestion_canvas.bind(
            "<MouseWheel>",
            lambda e: suggestion_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            ),
        )

        self.suggestion_labels = []
        for suggestion in suggestions[:8]:
            label = ttk.Label(
                scrollable_frame,
                text=suggestion,
                background="white",
                padding=5,
            )
            label.pack(fill=X)
            label.bind(
                "<Button-1>",
                lambda e, s=suggestion, r=row, t=table_type: self.select_work_suggestion(
                    r, t, s
                ),
            )
            self.suggestion_labels.append(label)

        self.selected_suggestion = -1

    def show_material_suggestions(self, event, row, table_type):
        """Показать подсказки для наименования материалов"""
        entry = event.widget
        text = entry.get().lower()
        materials = get_materials()
        suggestions = [m["name"] for m in materials if text in m["name"].lower()]
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
            height=160,
        )

        suggestion_canvas = tk.Canvas(self.suggestion_frame)
        scrollbar = ttk.Scrollbar(
            self.suggestion_frame, orient="vertical", command=suggestion_canvas.yview
        )
        scrollable_frame = ttk.Frame(suggestion_canvas)

        suggestion_canvas.configure(yscrollcommand=scrollbar.set)
        suggestion_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        suggestion_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: suggestion_canvas.configure(
                scrollregion=suggestion_canvas.bbox("all")
            ),
        )

        # Привязка прокрутки мышью
        suggestion_canvas.bind(
            "<MouseWheel>",
            lambda e: suggestion_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"
            ),
        )

        self.suggestion_labels = []
        for suggestion in suggestions[:8]:
            label = ttk.Label(
                scrollable_frame,
                text=suggestion,
                background="white",
                padding=5,
            )
            label.pack(fill=X)
            label.bind(
                "<Button-1>",
                lambda e, s=suggestion, r=row, t=table_type: self.select_material_suggestion(
                    r, t, s
                ),
            )
            self.suggestion_labels.append(label)

        self.selected_suggestion = -1

    def hide_suggestions(self):
        """Скрыть подсказки"""
        if hasattr(self, "suggestion_frame"):
            self.suggestion_frame.destroy()
            del self.suggestion_frame

    def move_suggestion_selection(self, direction):
        """Перемещение выбора в списке подсказок"""
        if not hasattr(self, "suggestion_labels") or not self.suggestion_labels:
            return

        if self.selected_suggestion >= 0:
            self.suggestion_labels[self.selected_suggestion].configure(
                background="white"
            )

        self.selected_suggestion = (self.selected_suggestion + direction) % len(
            self.suggestion_labels
        )
        self.suggestion_labels[self.selected_suggestion].configure(background="#D3D3D3")

    def select_work_suggestion(self, row, table_type, suggestion=None):
        """Выбор наименования работы из подсказок"""
        if suggestion is None:
            if self.selected_suggestion >= 0:
                suggestion = self.suggestion_labels[self.selected_suggestion].cget(
                    "text"
                )
            else:
                return

        entries = (
            self.work_entries
            if table_type == "vehicle_works"
            else self.global_work_entries
        )
        entries[row][0].delete(0, END)
        entries[row][0].insert(0, suggestion)
        works = get_works()
        for work in works:
            if work["name"] == suggestion:
                entries[row][1].delete(0, END)
                entries[row][1].insert(0, work["unit"])
                if table_type == "vehicle_works":
                    entries[row][3].delete(0, END)
                    entries[row][3].insert(0, work["price"])
                else:
                    entries[row][2].delete(0, END)
                    entries[row][2].insert(0, work["price"])
        self.hide_suggestions()

    def select_material_suggestion(self, row, table_type, suggestion=None):
        """Выбор наименования материала из подсказок"""
        if suggestion is None:
            if self.selected_suggestion >= 0:
                suggestion = self.suggestion_labels[self.selected_suggestion].cget(
                    "text"
                )
            else:
                return

        entries = (
            self.material_entries
            if table_type == "vehicle_materials"
            else self.global_material_entries
        )
        entries[row][0].delete(0, END)
        entries[row][0].insert(0, suggestion)
        materials = get_materials()
        for material in materials:
            if material["name"] == suggestion:
                entries[row][1].delete(0, END)
                entries[row][1].insert(0, material["unit"])
                if table_type == "vehicle_materials":
                    entries[row][3].delete(0, END)
                    entries[row][3].insert(0, material["price"])
                else:
                    entries[row][2].delete(0, END)
                    entries[row][2].insert(0, material["price"])
        self.hide_suggestions()

    def update_vehicle_tables(self, event=None):
        """Обновление таблиц 'Работы' и 'Материалы' для выбранного ТС"""
        # Очищаем таблицы
        for entries in self.work_entries:
            for entry in entries:
                entry.grid_forget()
        for button in self.work_delete_buttons:
            button.grid_forget()
        for entries in self.material_entries:
            for entry in entries:
                entry.grid_forget()
        for button in self.material_delete_buttons:
            button.grid_forget()

        self.work_entries = []
        self.work_delete_buttons = []
        self.work_ids = []
        self.material_entries = []
        self.material_delete_buttons = []
        self.material_ids = []
        self.work_rows = 0
        self.material_rows = 0

        # Находим vehicle_id
        selected_vehicle = self.vehicle_combobox.get()
        vehicle_id = None
        for vehicle in self.vehicles:
            vehicle_str = f"{vehicle['type']} — {vehicle['customer']}, Заявка № {vehicle['contract_number']}, Гос. номер {vehicle['number']}"
            if vehicle_str == selected_vehicle:
                vehicle_id = vehicle["id"]
                break

        if vehicle_id is None:
            return

        # Загружаем данные из базы
        materials_and_works = get_materials_and_works(vehicle_id)
        works = [entry for entry in materials_and_works if entry["work"]]
        materials = [entry for entry in materials_and_works if entry["material"]]

        # Заполняем таблицу "Работы"
        self.work_rows = max(len(works), 10)  # Минимум 10 строк
        for row in range(self.work_rows):
            row_entries = []
            ttk.Label(
                self.work_frame,
                text=str(row + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row + 1, column=0, sticky="nsew")
            for col in range(1, 5):
                entry = ttk.Entry(
                    self.work_frame, width=30 if col == 1 else 10
                )  # Увеличена ширина для "Наименование"
                entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
                if row < len(works):
                    # Заполняем поля: Наименование, Ед. изм., Кол-во, Цена за ед.
                    if col == 1:
                        entry.insert(0, works[row]["work"])
                    elif col == 2:
                        entry.insert(0, works[row]["unit"])
                    elif col == 3:
                        entry.insert(0, works[row]["quantity"])
                    elif col == 4:
                        entry.insert(0, works[row]["price_per_unit"])
                else:
                    entry.insert(0, "")
                row_entries.append(entry)
                entry.bind("<Control-a>", lambda event: select_all(event))
                self.bind_hotkeys(entry)
                self.create_context_menu(entry)
                if col == 1:  # Поле "Наименование"
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=row: self.show_work_suggestions(
                            e, r, "vehicle_works"
                        ),
                    )
                    entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                    entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                    entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                    entry.bind(
                        "<Return>",
                        lambda e, r=row: self.select_work_suggestion(
                            r, "vehicle_works"
                        ),
                    )
            self.work_entries.append(row_entries)
            delete_button = ttk.Button(
                self.work_frame,
                text="X",
                style="Delete.TButton",
                width=2,
                command=lambda r=row: self.delete_work_row(r),
            )
            delete_button.grid(row=row + 1, column=5, sticky="nsew", padx=1, pady=1)
            self.work_delete_buttons.append(delete_button)
            self.work_ids.append(works[row]["id"] if row < len(works) else None)

        # Заполняем таблицу "Материалы"
        self.material_rows = max(len(materials), 10)  # Минимум 10 строк
        for row in range(self.material_rows):
            row_entries = []
            ttk.Label(
                self.material_frame,
                text=str(row + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row + 1, column=0, sticky="nsew")
            for col in range(1, 5):
                entry = ttk.Entry(
                    self.material_frame, width=30 if col == 1 else 10
                )  # Увеличена ширина для "Наименование"
                entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
                if row < len(materials):
                    # Заполняем поля: Наименование, Ед. изм., Кол-во, Цена за ед.
                    if col == 1:
                        entry.insert(0, materials[row]["material"])
                    elif col == 2:
                        entry.insert(0, materials[row]["unit"])
                    elif col == 3:
                        entry.insert(0, materials[row]["quantity"])
                    elif col == 4:
                        entry.insert(0, materials[row]["price_per_unit"])
                else:
                    entry.insert(0, "")
                row_entries.append(entry)
                entry.bind("<Control-a>", lambda event: select_all(event))
                self.bind_hotkeys(entry)
                self.create_context_menu(entry)
                if col == 1:  # Поле "Наименование"
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=row: self.show_material_suggestions(
                            e, r, "vehicle_materials"
                        ),
                    )
                    entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                    entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                    entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                    entry.bind(
                        "<Return>",
                        lambda e, r=row: self.select_material_suggestion(
                            r, "vehicle_materials"
                        ),
                    )
            self.material_entries.append(row_entries)
            delete_button = ttk.Button(
                self.material_frame,
                text="X",
                style="Delete.TButton",
                width=2,
                command=lambda r=row: self.delete_material_row(r),
            )
            delete_button.grid(row=row + 1, column=5, sticky="nsew", padx=1, pady=1)
            self.material_delete_buttons.append(delete_button)
            self.material_ids.append(
                materials[row]["id"] if row < len(materials) else None
            )

        self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all"))
        self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all"))

    def update_global_tables(self):
        """Обновление таблиц 'Общий список работ' и 'Общий список материалов'"""
        # Очищаем таблицы
        for entries in self.global_work_entries:
            for entry in entries:
                entry.grid_forget()
        for button in self.global_work_delete_buttons:
            button.grid_forget()
        for entries in self.global_material_entries:
            for entry in entries:
                entry.grid_forget()
        for button in self.global_material_delete_buttons:
            button.grid_forget()

        self.global_work_entries = []
        self.global_work_delete_buttons = []
        self.global_work_ids = []
        self.global_material_entries = []
        self.global_material_delete_buttons = []
        self.global_material_ids = []
        self.global_work_rows = 0
        self.global_material_rows = 0

        # Загружаем данные из базы
        works = get_works()
        materials = get_materials()

        # Заполняем таблицу "Общий список работ"
        self.global_work_rows = max(len(works), 10)  # Минимум 10 строк
        for row in range(self.global_work_rows):
            row_entries = []
            ttk.Label(
                self.global_work_frame,
                text=str(row + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row + 1, column=0, sticky="nsew")
            for col in range(1, 4):
                entry = ttk.Entry(
                    self.global_work_frame, width=30 if col == 1 else 10
                )  # Увеличена ширина для "Наименование"
                entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
                if row < len(works):
                    # Заполняем поля: Наименование, Ед. изм., Цена за ед.
                    if col == 1:
                        entry.insert(0, works[row]["name"])
                    elif col == 2:
                        entry.insert(0, works[row]["unit"])
                    elif col == 3:
                        entry.insert(0, works[row]["price"])
                else:
                    entry.insert(0, "")
                row_entries.append(entry)
                entry.bind("<Control-a>", lambda event: select_all(event))
                self.bind_hotkeys(entry)
                self.create_context_menu(entry)
                if col == 1:  # Поле "Наименование"
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=row: self.show_work_suggestions(
                            e, r, "global_works"
                        ),
                    )
                    entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                    entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                    entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                    entry.bind(
                        "<Return>",
                        lambda e, r=row: self.select_work_suggestion(r, "global_works"),
                    )
            self.global_work_entries.append(row_entries)
            delete_button = ttk.Button(
                self.global_work_frame,
                text="X",
                style="Delete.TButton",
                width=2,
                command=lambda r=row: self.delete_global_work_row(r),
            )
            delete_button.grid(row=row + 1, column=4, sticky="nsew", padx=1, pady=1)
            self.global_work_delete_buttons.append(delete_button)
            self.global_work_ids.append(works[row]["id"] if row < len(works) else None)

        # Заполняем таблицу "Общий список материалов"
        self.global_material_rows = max(len(materials), 10)  # Минимум 10 строк
        for row in range(self.global_material_rows):
            row_entries = []
            ttk.Label(
                self.global_material_frame,
                text=str(row + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row + 1, column=0, sticky="nsew")
            for col in range(1, 4):
                entry = ttk.Entry(
                    self.global_material_frame, width=30 if col == 1 else 10
                )  # Увеличена ширина для "Наименование"
                entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
                if row < len(materials):
                    # Заполняем поля: Наименование, Ед. изм., Цена за ед.
                    if col == 1:
                        entry.insert(0, materials[row]["name"])
                    elif col == 2:
                        entry.insert(0, materials[row]["unit"])
                    elif col == 3:
                        entry.insert(0, materials[row]["price"])
                else:
                    entry.insert(0, "")
                row_entries.append(entry)
                entry.bind("<Control-a>", lambda event: select_all(event))
                self.bind_hotkeys(entry)
                self.create_context_menu(entry)
                if col == 1:  # Поле "Наименование"
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=row: self.show_material_suggestions(
                            e, r, "global_materials"
                        ),
                    )
                    entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                    entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                    entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                    entry.bind(
                        "<Return>",
                        lambda e, r=row: self.select_material_suggestion(
                            r, "global_materials"
                        ),
                    )
            self.global_material_entries.append(row_entries)
            delete_button = ttk.Button(
                self.global_material_frame,
                text="X",
                style="Delete.TButton",
                width=2,
                command=lambda r=row: self.delete_global_material_row(r),
            )
            delete_button.grid(row=row + 1, column=4, sticky="nsew", padx=1, pady=1)
            self.global_material_delete_buttons.append(delete_button)
            self.global_material_ids.append(
                materials[row]["id"] if row < len(materials) else None
            )

        self.global_works_canvas.configure(
            scrollregion=self.global_works_canvas.bbox("all")
        )
        self.global_materials_canvas.configure(
            scrollregion=self.global_materials_canvas.bbox("all")
        )

    def add_work_row(self):
        """Добавление новой строки в таблицу 'Работы' для ТС"""
        self.work_rows += 1
        row = self.work_rows - 1
        row_entries = []
        ttk.Label(
            self.work_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5
        ).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 5):
            entry = ttk.Entry(self.work_frame, width=30 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            entry.bind("<Control-a>", lambda event: select_all(event))
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if col == 1:  # Поле "Наименование"
                entry.bind(
                    "<KeyRelease>",
                    lambda e, r=row: self.show_work_suggestions(e, r, "vehicle_works"),
                )
                entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                entry.bind(
                    "<Return>",
                    lambda e, r=row: self.select_work_suggestion(r, "vehicle_works"),
                )
                # Устанавливаем фокус на поле "Наименование"
                entry.focus_set()
        self.work_entries.append(row_entries)
        delete_button = ttk.Button(
            self.work_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda r=row: self.delete_work_row(r),
        )
        delete_button.grid(row=row + 1, column=5, sticky="nsew", padx=1, pady=1)
        self.work_delete_buttons.append(delete_button)
        self.work_ids.append(None)
        # Обновляем регион прокрутки и прокручиваем к новой строке
        self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all"))
        self.works_canvas.yview_moveto(1.0)  # Прокрутка вниз к последней строке

    def add_material_row(self):
        """Добавление новой строки в таблицу 'Материалы' для ТС"""
        self.material_rows += 1
        row = self.material_rows - 1
        row_entries = []
        ttk.Label(
            self.material_frame,
            text=str(row + 1),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 5):
            entry = ttk.Entry(self.material_frame, width=30 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            entry.bind("<Control-a>", lambda event: select_all(event))
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if col == 1:  # Поле "Наименование"
                entry.bind(
                    "<KeyRelease>",
                    lambda e, r=row: self.show_material_suggestions(
                        e, r, "vehicle_materials"
                    ),
                )
                entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                entry.bind(
                    "<Return>",
                    lambda e, r=row: self.select_material_suggestion(
                        r, "vehicle_materials"
                    ),
                )
                # Устанавливаем фокус на поле "Наименование"
                entry.focus_set()
        self.material_entries.append(row_entries)
        delete_button = ttk.Button(
            self.material_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda r=row: self.delete_material_row(r),
        )
        delete_button.grid(row=row + 1, column=5, sticky="nsew", padx=1, pady=1)
        self.material_delete_buttons.append(delete_button)
        self.material_ids.append(None)
        # Обновляем регион прокрутки и прокручиваем к новой строке
        self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all"))
        self.materials_canvas.yview_moveto(1.0)  # Прокрутка вниз к последней строке

    def add_global_work_row(self):
        """Добавление новой строки в таблицу 'Общий список работ'"""
        self.global_work_rows += 1
        row = self.global_work_rows - 1
        row_entries = []
        ttk.Label(
            self.global_work_frame,
            text=str(row + 1),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 4):
            entry = ttk.Entry(
                self.global_work_frame, width=30 if col == 1 else 10
            )  # Увеличена ширина для "Наименование"
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            entry.bind("<Control-a>", lambda event: select_all(event))
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if col == 1:  # Поле "Наименование"
                entry.bind(
                    "<KeyRelease>",
                    lambda e, r=row: self.show_work_suggestions(e, r, "global_works"),
                )
                entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                entry.bind(
                    "<Return>",
                    lambda e, r=row: self.select_work_suggestion(r, "global_works"),
                )
        self.global_work_entries.append(row_entries)
        delete_button = ttk.Button(
            self.global_work_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda r=row: self.delete_global_work_row(r),
        )
        delete_button.grid(row=row + 1, column=4, sticky="nsew", padx=1, pady=1)
        self.global_work_delete_buttons.append(delete_button)
        self.global_work_ids.append(None)  # Новая строка пока не сохранена в базе
        self.global_works_canvas.configure(
            scrollregion=self.global_works_canvas.bbox("all")
        )

    def add_global_material_row(self):
        """Добавление новой строки в таблицу 'Общий список материалов'"""
        self.global_material_rows += 1
        row = self.global_material_rows - 1
        row_entries = []
        ttk.Label(
            self.global_material_frame,
            text=str(row + 1),
            borderwidth=1,
            relief="solid",
            padding=5,
        ).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 4):
            entry = ttk.Entry(
                self.global_material_frame, width=30 if col == 1 else 10
            )  # Увеличена ширина для "Наименование"
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            entry.bind("<Control-a>", lambda event: select_all(event))
            self.bind_hotkeys(entry)
            self.create_context_menu(entry)
            if col == 1:  # Поле "Наименование"
                entry.bind(
                    "<KeyRelease>",
                    lambda e, r=row: self.show_material_suggestions(
                        e, r, "global_materials"
                    ),
                )
                entry.bind("<FocusOut>", lambda e: self.hide_suggestions())
                entry.bind("<Down>", lambda e: self.move_suggestion_selection(1))
                entry.bind("<Up>", lambda e: self.move_suggestion_selection(-1))
                entry.bind(
                    "<Return>",
                    lambda e, r=row: self.select_material_suggestion(
                        r, "global_materials"
                    ),
                )
        self.global_material_entries.append(row_entries)
        delete_button = ttk.Button(
            self.global_material_frame,
            text="X",
            style="Delete.TButton",
            width=2,
            command=lambda r=row: self.delete_global_material_row(r),
        )
        delete_button.grid(row=row + 1, column=4, sticky="nsew", padx=1, pady=1)
        self.global_material_delete_buttons.append(delete_button)
        self.global_material_ids.append(None)  # Новая строка пока не сохранена в базе
        self.global_materials_canvas.configure(
            scrollregion=self.global_materials_canvas.bbox("all")
        )

    def delete_work_row(self, row):
        """Удаление строки из таблицы 'Работы' для ТС"""
        if self.work_rows <= 1:
            return
        # Удаляем запись из базы, если она существует
        if self.work_ids[row] is not None:
            try:
                delete_material_and_work(self.work_ids[row])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить работу: {e}")
                return
        for entry in self.work_entries[row]:
            entry.grid_forget()
        self.work_delete_buttons[row].grid_forget()
        self.work_entries.pop(row)
        self.work_delete_buttons.pop(row)
        self.work_ids.pop(row)
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
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=i: self.show_work_suggestions(
                            e, r, "vehicle_works"
                        ),
                    )
                    entry.bind(
                        "<Return>",
                        lambda e, r=i: self.select_work_suggestion(r, "vehicle_works"),
                    )
            self.work_delete_buttons[i].grid(
                row=i + 1, column=5, sticky="nsew", padx=1, pady=1
            )
            self.work_delete_buttons[i].configure(
                command=lambda r=i: self.delete_work_row(r)
            )
        self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all"))

    def delete_material_row(self, row):
        """Удаление строки из таблицы 'Материалы' для ТС"""
        if self.material_rows <= 1:
            return
        # Удаляем запись из базы, если она существует
        if self.material_ids[row] is not None:
            try:
                delete_material_and_work(self.material_ids[row])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить материал: {e}")
                return
        for entry in self.material_entries[row]:
            entry.grid_forget()
        self.material_delete_buttons[row].grid_forget()
        self.material_entries.pop(row)
        self.material_delete_buttons.pop(row)
        self.material_ids.pop(row)
        self.material_rows -= 1
        for i in range(row, self.material_rows):
            ttk.Label(
                self.material_frame,
                text=str(i + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=i + 1, column=0, sticky="nsew")
            for col, entry in enumerate(self.material_entries[i]):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
                if col == 0:
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=i: self.show_material_suggestions(
                            e, r, "vehicle_materials"
                        ),
                    )
                    entry.bind(
                        "<Return>",
                        lambda e, r=i: self.select_material_suggestion(
                            r, "vehicle_materials"
                        ),
                    )
            self.material_delete_buttons[i].grid(
                row=i + 1, column=5, sticky="nsew", padx=1, pady=1
            )
            self.material_delete_buttons[i].configure(
                command=lambda r=i: self.delete_material_row(r)
            )
        self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all"))

    def delete_global_work_row(self, row):
        """Удаление строки из таблицы 'Общий список работ'"""
        if self.global_work_rows <= 1:
            return
        # Удаляем запись из базы, если она существует
        if self.global_work_ids[row] is not None:
            try:
                delete_work(self.global_work_ids[row])
            except Exception as e:
                messagebox.showerror(
                    "Ошибка", f"Не удалось удалить работу из общего списка: {e}"
                )
                return
        for entry in self.global_work_entries[row]:
            entry.grid_forget()
        self.global_work_delete_buttons[row].grid_forget()
        self.global_work_entries.pop(row)
        self.global_work_delete_buttons.pop(row)
        self.global_work_ids.pop(row)
        self.global_work_rows -= 1
        for i in range(row, self.global_work_rows):
            ttk.Label(
                self.global_work_frame,
                text=str(i + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=i + 1, column=0, sticky="nsew")
            for col, entry in enumerate(self.global_work_entries[i]):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
                if col == 0:
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=i: self.show_work_suggestions(e, r, "global_works"),
                    )
                    entry.bind(
                        "<Return>",
                        lambda e, r=i: self.select_work_suggestion(r, "global_works"),
                    )
            self.global_work_delete_buttons[i].grid(
                row=i + 1, column=4, sticky="nsew", padx=1, pady=1
            )
            self.global_work_delete_buttons[i].configure(
                command=lambda r=i: self.delete_global_work_row(r)
            )
        self.global_works_canvas.configure(
            scrollregion=self.global_works_canvas.bbox("all")
        )

    def delete_global_material_row(self, row):
        """Удаление строки из таблицы 'Общий список материалов'"""
        if self.global_material_rows <= 1:
            return
        # Удаляем запись из базы, если она существует
        if self.global_material_ids[row] is not None:
            try:
                delete_material(self.global_material_ids[row])
            except Exception as e:
                messagebox.showerror(
                    "Ошибка", f"Не удалось удалить материал из общего списка: {e}"
                )
                return
        for entry in self.global_material_entries[row]:
            entry.grid_forget()
        self.global_material_delete_buttons[row].grid_forget()
        self.global_material_entries.pop(row)
        self.global_material_delete_buttons.pop(row)
        self.global_material_ids.pop(row)
        self.global_material_rows -= 1
        for i in range(row, self.global_material_rows):
            ttk.Label(
                self.global_material_frame,
                text=str(i + 1),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=i + 1, column=0, sticky="nsew")
            for col, entry in enumerate(self.global_material_entries[i]):
                entry.grid(row=i + 1, column=col + 1, sticky="nsew", padx=1, pady=1)
                if col == 0:
                    entry.bind(
                        "<KeyRelease>",
                        lambda e, r=i: self.show_material_suggestions(
                            e, r, "global_materials"
                        ),
                    )
                    entry.bind(
                        "<Return>",
                        lambda e, r=i: self.select_material_suggestion(
                            r, "global_materials"
                        ),
                    )
            self.global_material_delete_buttons[i].grid(
                row=i + 1, column=4, sticky="nsew", padx=1, pady=1
            )
            self.global_material_delete_buttons[i].configure(
                command=lambda r=i: self.delete_global_material_row(r)
            )
        self.global_materials_canvas.configure(
            scrollregion=self.global_materials_canvas.bbox("all")
        )

    def save_processes(self):
        """Сохранение процессов в базу данных"""
        try:
            # Сохранение работ и материалов для выбранного ТС
            selected_vehicle = self.vehicle_combobox.get()
            vehicle_id = None
            for vehicle in self.vehicles:
                vehicle_str = f"{vehicle['type']} — {vehicle['customer']}, Заявка № {vehicle['contract_number']}, Гос. номер {vehicle['number']}"
                if vehicle_str == selected_vehicle:
                    vehicle_id = vehicle["id"]
                    break

            if vehicle_id is None:
                messagebox.showerror("Ошибка", "Выберите ТС")
                return

            # Удаляем все существующие записи для этого ТС
            materials_and_works = get_materials_and_works(vehicle_id)
            for entry in materials_and_works:
                delete_material_and_work(entry["id"])

            # Сохраняем работы для ТС
            for row, entries in enumerate(self.work_entries):
                work = entries[0].get().strip()  # Наименование
                unit = entries[1].get().strip()  # Ед. изм.
                quantity = entries[2].get().strip()  # Кол-во
                price_per_unit = entries[3].get().strip()  # Цена за ед.
                if work:  # Сохраняем только непустые строки
                    add_material_and_work(
                        vehicle_id, "", work, unit, quantity, price_per_unit
                    )

            # Сохраняем материалы для ТС
            for row, entries in enumerate(self.material_entries):
                material = entries[0].get().strip()  # Наименование
                unit = entries[1].get().strip()  # Ед. изм.
                quantity = entries[2].get().strip()  # Кол-во
                price_per_unit = entries[3].get().strip()  # Цена за ед.
                if material:  # Сохраняем только непустые строки
                    add_material_and_work(
                        vehicle_id, material, "", unit, quantity, price_per_unit
                    )

            # Сохранение общего списка работ
            existing_works = get_works()
            for work in existing_works:
                delete_work(work["id"])
            for row, entries in enumerate(self.global_work_entries):
                name = entries[0].get().strip()  # Наименование
                unit = entries[1].get().strip()  # Ед. изм.
                price = entries[2].get().strip()  # Цена за ед.
                if name:  # Сохраняем только непустые строки
                    add_work(name, unit, price)

            # Сохранение общего списка материалов
            existing_materials = get_materials()
            for material in existing_materials:
                delete_material(material["id"])
            for row, entries in enumerate(self.global_material_entries):
                name = entries[0].get().strip()  # Наименование
                unit = entries[1].get().strip()  # Ед. изм.
                price = entries[2].get().strip()  # Цена за ед.
                if name:  # Сохраняем только непустые строки
                    add_material(name, unit, price)

            # Обновляем таблицы
            self.update_vehicle_tables()
            self.update_global_tables()
            messagebox.showinfo("Успех", "Данные успешно сохранены!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {e}")
