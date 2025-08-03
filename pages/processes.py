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
from src.ui.suggestion_mixin import SuggestionMixin
from src.utils.utils import bind_hotkeys, create_context_menu
from tkinter import messagebox
import src.utils.table_settings as tbl

class ProcessesPage(SuggestionMixin):
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.processes_frame = main_window.processes_frame
        self.work_rows = tbl.WORK_ROWS
        self.material_rows = tbl.MATERIAL_ROWS
        self.global_work_rows = tbl.WORK_ROWS
        self.global_material_rows = tbl.MATERIAL_ROWS
        self.vehicles = []
        self.active_canvas = None
        self.vehicle_id = None
        self.init_processes_page()

    def bind_suggestion_events(self, entry, field_type, row, table_type):
        super().bind_suggestion_events(entry, field_type, row, table_type)

    def init_processes_page(self):
        vehicle_selection_frame = ttk.Frame(self.processes_frame)
        vehicle_selection_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        ttk.Label(vehicle_selection_frame, text="Выберите ТС:", font=("Arial", 12)).pack(side=LEFT)
        self.vehicle_combobox = ttk.Combobox(vehicle_selection_frame, state="readonly", width=50)
        self.vehicle_combobox.pack(side=LEFT, padx=10)
        self.vehicle_combobox.bind("<<ComboboxSelected>>", self.update_vehicle_tables)

        self.processes_frame.grid_rowconfigure(1, weight=1)
        self.processes_frame.grid_rowconfigure(2, weight=1)
        self.processes_frame.grid_columnconfigure(0, weight=1)
        self.processes_frame.grid_columnconfigure(1, weight=1)

        # Работы для ТС
        works_frame = ttk.Frame(self.processes_frame)
        works_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.works_canvas = tk.Canvas(works_frame)
        works_scrollbar = ttk.Scrollbar(works_frame, orient="vertical", command=self.works_canvas.yview)
        works_scrollable_frame = ttk.Frame(self.works_canvas)
        self.works_canvas.create_window((0, 0), window=works_scrollable_frame, anchor="nw")
        works_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all")),
        )
        self.works_canvas.configure(yscrollcommand=works_scrollbar.set)
        self.works_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        works_scrollbar.pack(side=RIGHT, fill=Y)
        ttk.Label(works_scrollable_frame, text="Работы (для ТС)", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        ttk.Button(works_scrollable_frame, text="Добавить строку", command=self.add_work_row).pack(anchor="w", padx=20, pady=5)
        work_headers = ["№ п/п", "Наименование", "Ед. изм.", "Кол-во", "Цена за ед.", ""]
        self.work_frame = ttk.Frame(works_scrollable_frame)
        self.work_frame.pack(fill=X, padx=20)
        for col, header in enumerate(work_headers):
            ttk.Label(self.work_frame, text=header, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=0, column=col, sticky="nsew")
        self.work_entries = []
        self.work_delete_buttons = []
        self.work_ids = []

        # Общий список работ
        global_works_frame = ttk.Frame(self.processes_frame)
        global_works_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.global_works_canvas = tk.Canvas(global_works_frame)
        global_works_scrollbar = ttk.Scrollbar(global_works_frame, orient="vertical", command=self.global_works_canvas.yview)
        global_works_scrollable_frame = ttk.Frame(self.global_works_canvas)
        self.global_works_canvas.create_window((0, 0), window=global_works_scrollable_frame, anchor="nw")
        global_works_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.global_works_canvas.configure(scrollregion=self.global_works_canvas.bbox("all")),
        )
        self.global_works_canvas.configure(yscrollcommand=global_works_scrollbar.set)
        self.global_works_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        global_works_scrollbar.pack(side=RIGHT, fill=Y)
        ttk.Label(global_works_scrollable_frame, text="Общий список работ", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        ttk.Button(global_works_scrollable_frame, text="Добавить строку", command=self.add_global_work_row).pack(anchor="w", padx=20, pady=5)
        global_work_headers = ["№ п/п", "Наименование", "Ед. изм.", "Цена за ед.", ""]
        self.global_work_frame = ttk.Frame(global_works_scrollable_frame)
        self.global_work_frame.pack(fill=X, padx=20)
        for col, header in enumerate(global_work_headers):
            ttk.Label(self.global_work_frame, text=header, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=0, column=col, sticky="nsew")
        self.global_work_entries = []
        self.global_work_delete_buttons = []
        self.global_work_ids = []

        # Материалы для ТС
        materials_frame = ttk.Frame(self.processes_frame)
        materials_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.materials_canvas = tk.Canvas(materials_frame)
        materials_scrollbar = ttk.Scrollbar(materials_frame, orient="vertical", command=self.materials_canvas.yview)
        materials_scrollable_frame = ttk.Frame(self.materials_canvas)
        self.materials_canvas.create_window((0, 0), window=materials_scrollable_frame, anchor="nw")
        materials_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all")),
        )
        self.materials_canvas.configure(yscrollcommand=materials_scrollbar.set)
        self.materials_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        materials_scrollbar.pack(side=RIGHT, fill=Y)
        ttk.Label(materials_scrollable_frame, text="Материалы (для ТС)", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        ttk.Button(materials_scrollable_frame, text="Добавить строку", command=self.add_material_row).pack(anchor="w", padx=20, pady=5)
        material_headers = ["№ п/п", "Наименование", "Ед. изм.", "Кол-во", "Цена за ед.", ""]
        self.material_frame = ttk.Frame(materials_scrollable_frame)
        self.material_frame.pack(fill=X, padx=20)
        for col, header in enumerate(material_headers):
            ttk.Label(self.material_frame, text=header, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=0, column=col, sticky="nsew")
        self.material_entries = []
        self.material_delete_buttons = []
        self.material_ids = []

        # Общий список материалов
        global_materials_frame = ttk.Frame(self.processes_frame)
        global_materials_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        self.global_materials_canvas = tk.Canvas(global_materials_frame)
        global_materials_scrollbar = ttk.Scrollbar(global_materials_frame, orient="vertical", command=self.global_materials_canvas.yview)
        global_materials_scrollable_frame = ttk.Frame(self.global_materials_canvas)
        self.global_materials_canvas.create_window((0, 0), window=global_materials_scrollable_frame, anchor="nw")
        global_materials_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.global_materials_canvas.configure(scrollregion=self.global_materials_canvas.bbox("all")),
        )
        self.global_materials_canvas.configure(yscrollcommand=global_materials_scrollbar.set)
        self.global_materials_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        global_materials_scrollbar.pack(side=RIGHT, fill=Y)
        ttk.Label(global_materials_scrollable_frame, text="Общий список материалов", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=10)
        ttk.Button(global_materials_scrollable_frame, text="Добавить строку", command=self.add_global_material_row).pack(anchor="w", padx=20, pady=5)
        global_material_headers = ["№ п/п", "Наименование", "Ед. изм.", "Цена за ед.", ""]
        self.global_material_frame = ttk.Frame(global_materials_scrollable_frame)
        self.global_material_frame.pack(fill=X, padx=20)
        for col, header in enumerate(global_material_headers):
            ttk.Label(self.global_material_frame, text=header, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", padding=5).grid(row=0, column=col, sticky="nsew")
        self.global_material_entries = []
        self.global_material_delete_buttons = []
        self.global_material_ids = []

        save_frame = ttk.Frame(self.processes_frame)
        save_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        ttk.Button(save_frame, text="Сохранить", command=self.save_processes).pack(anchor="e")

        self.update_vehicle_combobox()
        self.update_global_tables()

    def add_work_row(self, add_to_global=True):
        if add_to_global:
            tbl.WORK_ROWS += 1
            self.work_rows = tbl.WORK_ROWS
        else:
            self.work_rows += 1
        row = self.work_rows - 1
        row_entries = []
        ttk.Label(self.work_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 5):
            entry = ttk.Entry(self.work_frame, width=30 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            bind_hotkeys(entry)
            create_context_menu(entry)
            if col == 1:
                self.bind_suggestion_events(entry, "work_name", row, "vehicle_works")
            elif col == 2:
                self.bind_suggestion_events(entry, "unit", row, "vehicle_works")
            elif col == 3:
                self.bind_suggestion_events(entry, "quantity", row, "vehicle_works")
            elif col == 4:
                self.bind_suggestion_events(entry, "price", row, "vehicle_works")
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
        self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all"))
        self.works_canvas.yview_moveto(1.0)

    def add_material_row(self, add_to_global=True):
        if add_to_global:
            tbl.MATERIAL_ROWS += 1
            self.material_rows = tbl.MATERIAL_ROWS
        else:
            self.material_rows += 1
        row = self.material_rows - 1
        row_entries = []
        ttk.Label(self.material_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 5):
            entry = ttk.Entry(self.material_frame, width=30 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            bind_hotkeys(entry)
            create_context_menu(entry)
            if col == 1:
                self.bind_suggestion_events(entry, "material_name", row, "vehicle_materials")
            elif col == 2:
                self.bind_suggestion_events(entry, "unit", row, "vehicle_materials")
            elif col == 3:
                self.bind_suggestion_events(entry, "quantity", row, "vehicle_materials")
            elif col == 4:
                self.bind_suggestion_events(entry, "price", row, "vehicle_materials")
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
        self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all"))
        self.materials_canvas.yview_moveto(1.0)

    def add_global_work_row(self, add_to_global=True):
        if add_to_global:
            tbl.WORK_ROWS += 1
            self.global_work_rows = tbl.WORK_ROWS
        else:
            self.global_work_rows += 1
        row = self.global_work_rows - 1
        row_entries = []
        ttk.Label(self.global_work_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 4):
            entry = ttk.Entry(self.global_work_frame, width=30 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            bind_hotkeys(entry)
            create_context_menu(entry)
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
        self.global_work_ids.append(None)
        self.global_works_canvas.configure(scrollregion=self.global_works_canvas.bbox("all"))

    def add_global_material_row(self, add_to_global=True):
        if add_to_global:
            tbl.MATERIAL_ROWS += 1
            self.global_material_rows = tbl.MATERIAL_ROWS
        else:
            self.global_material_rows += 1
        row = self.global_material_rows - 1
        row_entries = []
        ttk.Label(self.global_material_frame, text=str(row + 1), borderwidth=1, relief="solid", padding=5).grid(row=row + 1, column=0, sticky="nsew")
        for col in range(1, 4):
            entry = ttk.Entry(self.global_material_frame, width=30 if col == 1 else 10)
            entry.grid(row=row + 1, column=col, sticky="nsew", padx=1, pady=1)
            entry.insert(0, "")
            row_entries.append(entry)
            bind_hotkeys(entry)
            create_context_menu(entry)
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
        self.global_material_ids.append(None)
        self.global_materials_canvas.configure(scrollregion=self.global_materials_canvas.bbox("all"))

    def update_vehicle_combobox(self):
        try:
            self.vehicles = get_all_vehicles()
            if not self.vehicles:
                messagebox.showinfo("Информация", "Список транспортных средств пуст.")
                self.vehicle_combobox["values"] = []
                self.vehicle_combobox.set("")
                self.vehicle_id = None
                self.update_vehicle_tables()
                return
            vehicle_options = [
                f"{v['type']} — {v['customer']}, Заявка № {v['contract_number']}, Гос. номер {v['number']}"
                for v in self.vehicles
            ]
            self.vehicle_combobox["values"] = vehicle_options
            self.vehicle_combobox.set(vehicle_options[0])
            self.vehicle_id = self.vehicles[0]['id']
            self.update_vehicle_tables()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список ТС: {e}")

    def update_vehicle_tables(self, event=None, vehicle_id=None):
        if event:
            idx = self.vehicle_combobox.current()
            if idx >= 0 and idx < len(self.vehicles):
                self.vehicle_id = self.vehicles[idx]['id']
            else:
                self.vehicle_id = None
        elif vehicle_id is not None:
            self.vehicle_id = vehicle_id

        if not self.vehicle_id:
            self.clear_vehicle_tables()
            return

        materials_and_works = get_materials_and_works(self.vehicle_id)
        works = [entry for entry in materials_and_works if entry["work"]]
        materials = [entry for entry in materials_and_works if entry["material"]]

        self.work_rows = max(len(works), tbl.WORK_ROWS)
        for entries in getattr(self, "work_entries", []):
            for entry in entries:
                entry.grid_forget()
        for button in getattr(self, "work_delete_buttons", []):
            button.grid_forget()
        self.work_entries = []
        self.work_delete_buttons = []
        self.work_ids = []

        for row in range(len(works)):
            self.add_work_row(add_to_global=False)
            entries = self.work_entries[-1]
            entries[0].insert(0, works[row]["work"])
            entries[1].insert(0, works[row]["unit"])
            entries[2].insert(0, works[row]["quantity"])
            entries[3].insert(0, works[row]["price_per_unit"])
            self.work_ids.append(works[row]["id"])

        for _ in range(len(works), self.work_rows):
            self.add_work_row(add_to_global=False)
            self.work_ids.append(None)
        self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all"))

        self.material_rows = max(len(materials), tbl.MATERIAL_ROWS)
        for entries in getattr(self, "material_entries", []):
            for entry in entries:
                entry.grid_forget()
        for button in getattr(self, "material_delete_buttons", []):
            button.grid_forget()
        self.material_entries = []
        self.material_delete_buttons = []
        self.material_ids = []

        for row in range(len(materials)):
            self.add_material_row(add_to_global=False)
            entries = self.material_entries[-1]
            entries[0].insert(0, materials[row]["material"])
            entries[1].insert(0, materials[row]["unit"])
            entries[2].insert(0, materials[row]["quantity"])
            entries[3].insert(0, materials[row]["price_per_unit"])
            self.material_ids.append(materials[row]["id"])

        for _ in range(len(materials), self.material_rows):
            self.add_material_row(add_to_global=False)
            self.material_ids.append(None)
        self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all"))

    def clear_vehicle_tables(self):
        for entries in getattr(self, "work_entries", []):
            for entry in entries:
                entry.delete(0, tk.END)
        for entries in getattr(self, "material_entries", []):
            for entry in entries:
                entry.delete(0, tk.END)

    def update_global_tables(self):
        works = get_works()
        materials = get_materials()
        self.global_work_rows = max(len(works), tbl.WORK_ROWS)
        for entries in self.global_work_entries:
            for entry in entries:
                entry.grid_forget()
        for button in self.global_work_delete_buttons:
            button.grid_forget()
        self.global_work_entries = []
        self.global_work_delete_buttons = []
        self.global_work_ids = []
        for row in range(len(works)):
            self.add_global_work_row(add_to_global=False)
            entries = self.global_work_entries[-1]
            entries[0].insert(0, works[row]["name"])
            entries[1].insert(0, works[row]["unit"])
            entries[2].insert(0, works[row]["price"])
            self.global_work_ids.append(works[row]["id"])
        for _ in range(len(works), self.global_work_rows):
            self.add_global_work_row(add_to_global=False)
            self.global_work_ids.append(None)
        self.global_works_canvas.configure(scrollregion=self.global_works_canvas.bbox("all"))
        self.global_material_rows = max(len(materials), tbl.MATERIAL_ROWS)
        for entries in self.global_material_entries:
            for entry in entries:
                entry.grid_forget()
        for button in self.global_material_delete_buttons:
            button.grid_forget()
        self.global_material_entries = []
        self.global_material_delete_buttons = []
        self.global_material_ids = []
        for row in range(len(materials)):
            self.add_global_material_row(add_to_global=False)
            entries = self.global_material_entries[-1]
            entries[0].insert(0, materials[row]["name"])
            entries[1].insert(0, materials[row]["unit"])
            entries[2].insert(0, materials[row]["price"])
            self.global_material_ids.append(materials[row]["id"])
        for _ in range(len(materials), self.global_material_rows):
            self.add_global_material_row(add_to_global=False)
            self.global_material_ids.append(None)
        self.global_materials_canvas.configure(scrollregion=self.global_materials_canvas.bbox("all"))

    def delete_work_row(self, row):
        if self.work_rows <= 1:
            return
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
                    self.bind_suggestion_events(entry, "work_name", i, "vehicle_works")
            self.work_delete_buttons[i].grid(
                row=i + 1, column=5, sticky="nsew", padx=1, pady=1
            )
        self.rebind_work_delete_buttons()
        self.works_canvas.configure(scrollregion=self.works_canvas.bbox("all"))
        tbl.WORK_ROWS -= 1

    def delete_material_row(self, row):
        if self.material_rows <= 1:
            return
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
                    self.bind_suggestion_events(entry, "material_name", i, "vehicle_materials")
            self.material_delete_buttons[i].grid(
                row=i + 1, column=5, sticky="nsew", padx=1, pady=1
            )
        self.rebind_material_delete_buttons()
        self.materials_canvas.configure(scrollregion=self.materials_canvas.bbox("all"))
        tbl.MATERIAL_ROWS -= 1

    def delete_global_work_row(self, row):
        if self.global_work_rows <= 1:
            return
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
            self.global_work_delete_buttons[i].grid(
                row=i + 1, column=4, sticky="nsew", padx=1, pady=1
            )
        self.rebind_global_work_delete_buttons()
        self.global_works_canvas.configure(
            scrollregion=self.global_works_canvas.bbox("all")
        )
        tbl.WORK_ROWS -= 1

    def delete_global_material_row(self, row):
        if self.global_material_rows <= 1:
            return
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
            self.global_material_delete_buttons[i].grid(
                row=i + 1, column=4, sticky="nsew", padx=1, pady=1
            )
        self.rebind_global_material_delete_buttons()
        self.global_materials_canvas.configure(
            scrollregion=self.global_materials_canvas.bbox("all")
        )
        tbl.MATERIAL_ROWS -= 1

    def rebind_work_delete_buttons(self):
        for i, btn in enumerate(self.work_delete_buttons):
            btn.configure(command=lambda r=i: self.delete_work_row(r))

    def rebind_material_delete_buttons(self):
        for i, btn in enumerate(self.material_delete_buttons):
            btn.configure(command=lambda r=i: self.delete_material_row(r))

    def rebind_global_work_delete_buttons(self):
        for i, btn in enumerate(self.global_work_delete_buttons):
            btn.configure(command=lambda r=i: self.delete_global_work_row(r))

    def rebind_global_material_delete_buttons(self):
        for i, btn in enumerate(self.global_material_delete_buttons):
            btn.configure(command=lambda r=i: self.delete_global_material_row(r))

    def save_processes(self):
        try:
            existing_works = get_works()
            for work in existing_works:
                delete_work(work["id"])
            for entries in self.global_work_entries:
                name = entries[0].get().strip()
                unit = entries[1].get().strip()
                price = entries[2].get().strip()
                if name:
                    add_work(name, unit, price)

            existing_materials = get_materials()
            for material in existing_materials:
                delete_material(material["id"])
            for entries in self.global_material_entries:
                name = entries[0].get().strip()
                unit = entries[1].get().strip()
                price = entries[2].get().strip()
                if name:
                    add_material(name, unit, price)

            if hasattr(self.main_window, "add_page"):
                self.main_window.add_page.update_suggestions()
            self.update_global_tables()
            messagebox.showinfo("Успех", "Общие списки успешно сохранены!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные в общих таблицах: {e}")

    def refresh_from_add_page(self, vehicle_id):
        self.update_vehicle_combobox()
        self.update_vehicle_tables(vehicle_id=vehicle_id)