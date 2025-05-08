import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.db.database import get_all_vehicles, delete_vehicle
from tkinter import messagebox
import os
from PIL import Image, ImageTk
from src.utils.utils import resource_path


class ResultsPage:
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.results_frame = main_window.results_frame
        self.vehicle_images = main_window.vehicle_images
        self.current_active_button = None

        self.init_results_page()

    def init_results_page(self):
        """Инициализация страницы 'Список'"""
        # Верхняя панель: Поиск, Фильтр, Кнопки
        top_frame = ttk.Frame(self.results_frame, style="NoBorder.TFrame")
        top_frame.pack(fill=X, padx=20, pady=10)

        # Поиск
        search_frame = ttk.Frame(top_frame, style="NoBorder.TFrame")
        search_frame.pack(side=LEFT)

        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.insert(0, "Поиск")
        self.search_entry.pack(side=LEFT, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_vehicles)
        self.search_entry.bind("<FocusIn>", self.clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self.restore_search_placeholder)

        try:
            search_icon_path = resource_path(r"Tandem/assets/search_icon.png")
            search_image = Image.open(search_icon_path)
            search_icon = ImageTk.PhotoImage(search_image)
            search_button = ttk.Button(
                search_frame,
                image=search_icon,
                style="NoBorder.TButton",
                command=self.filter_vehicles,
                takefocus=0,
            )
            search_button.pack(side=LEFT)
            search_button.image = search_icon  # Сохраняем ссылку
        except Exception as e:
            print(f"Ошибка загрузки search_icon: {e}")  # Диагностика
            search_button = ttk.Button(
                search_frame,
                text="Поиск",
                style="NoBorder.TButton",
                command=self.filter_vehicles,
                takefocus=0,
            )
            search_button.pack(side=LEFT)

        # Фильтр по типу ТС
        filter_frame = ttk.Frame(top_frame, style="NoBorder.TFrame")
        filter_frame.pack(side=LEFT, padx=10)

        self.filter_combobox = ttk.Combobox(
            filter_frame,
            values=["Все типы", "Легковые", "Автобусы", "Рефрижераторы", "Разное"],
            state="readonly",
            width=15,
        )
        self.filter_combobox.set("Все типы")
        self.filter_combobox.pack()
        self.filter_combobox.bind("<<ComboboxSelected>>", self.filter_vehicles)

        # Кнопки управления
        button_frame = ttk.Frame(top_frame, style="NoBorder.TFrame")
        button_frame.pack(side=RIGHT)

        # Кнопка "История"
        try:
            history_icon_path = resource_path(r"Tandem/assets/history.png")
            history_icon_active_path = resource_path(
                r"Tandem/assets/history_active.png"
            )
            history_image = Image.open(history_icon_path)
            history_icon = ImageTk.PhotoImage(history_image)
            history_active_image = Image.open(history_icon_active_path)
            history_icon_active = ImageTk.PhotoImage(history_active_image)
            self.history_button = ttk.Button(
                button_frame,
                image=history_icon,
                style="NoBorder.TButton",
                command=lambda: [
                    self.main_window.show_history(),
                    self.set_active_button("history"),
                ],
                takefocus=0,
            )
            self.history_button.pack(side=LEFT, padx=5)
            self.history_button.image_default = history_icon
            self.history_button.image_active = history_icon_active
            self.history_button.bind(
                "<Enter>",
                lambda e, b=self.history_button: b.configure(image=b.image_active),
            )
            self.history_button.bind(
                "<Leave>",
                lambda e, b=self.history_button: b.configure(
                    image=(
                        b.image_default
                        if self.current_active_button != "history"
                        else b.image_active
                    )
                ),
            )
            button_frame.image_history = history_icon
        except Exception as e:
            self.history_button = ttk.Button(
                button_frame,
                text="История",
                style="NoBorder.TButton",
                command=lambda: [
                    self.main_window.show_history(),
                    self.set_active_button("history"),
                ],
                takefocus=0,
            )
            self.history_button.pack(side=LEFT, padx=5)

        # Кнопка "Процессы"
        try:
            processes_icon_path = resource_path(r"Tandem/assets/list.png")
            processes_icon_active_path = resource_path(r"Tandem/assets/list_active.png")
            processes_image = Image.open(processes_icon_path)
            processes_icon = ImageTk.PhotoImage(processes_image)
            processes_active_image = Image.open(processes_icon_active_path)
            processes_icon_active = ImageTk.PhotoImage(processes_active_image)
            self.processes_button = ttk.Button(
                button_frame,
                image=processes_icon,
                style="NoBorder.TButton",
                command=lambda: [
                    self.main_window.show_processes(),
                    self.set_active_button("processes"),
                ],
                takefocus=0,
            )
            self.processes_button.pack(side=LEFT, padx=5)
            self.processes_button.image_default = processes_icon
            self.processes_button.image_active = processes_icon_active
            self.processes_button.bind(
                "<Enter>",
                lambda e, b=self.processes_button: b.configure(image=b.image_active),
            )
            self.processes_button.bind(
                "<Leave>",
                lambda e, b=self.processes_button: b.configure(
                    image=(
                        b.image_default
                        if self.current_active_button != "processes"
                        else b.image_active
                    )
                ),
            )
            button_frame.image_processes = processes_icon
        except Exception as e:
            self.processes_button = ttk.Button(
                button_frame,
                text="Процессы",
                style="NoBorder.TButton",
                command=lambda: [
                    self.main_window.show_processes(),
                    self.set_active_button("processes"),
                ],
                takefocus=0,
            )
            self.processes_button.pack(side=LEFT, padx=5)

        # Кнопка "Добавить"
        try:
            add_icon_path = resource_path(r"Tandem/assets/add.png")
            add_icon_active_path = resource_path(r"Tandem/assets/add_active.png")
            add_image = Image.open(add_icon_path)
            add_icon = ImageTk.PhotoImage(add_image)
            add_active_image = Image.open(add_icon_active_path)
            add_icon_active = ImageTk.PhotoImage(add_active_image)
            self.add_button = ttk.Button(
                button_frame,
                image=add_icon,
                style="NoBorder.TButton",
                command=lambda: [
                    self.main_window.show_add(),
                    self.set_active_button("add"),
                ],
                takefocus=0,
            )
            self.add_button.pack(side=LEFT, padx=5)
            self.add_button.image_default = add_icon
            self.add_button.image_active = add_icon_active
            self.add_button.bind(
                "<Enter>",
                lambda e, b=self.add_button: b.configure(image=b.image_active),
            )
            self.add_button.bind(
                "<Leave>",
                lambda e, b=self.add_button: b.configure(
                    image=(
                        b.image_default
                        if self.current_active_button != "add"
                        else b.image_active
                    )
                ),
            )
            button_frame.image_add = add_icon
        except Exception as e:
            self.add_button = ttk.Button(
                button_frame,
                text="Добавить",
                style="NoBorder.TButton",
                command=lambda: [
                    self.main_window.show_add(),
                    self.set_active_button("add"),
                ],
                takefocus=0,
            )
            self.add_button.pack(side=LEFT, padx=5)

        # Список ТС с прокруткой
        self.results_canvas = ttk.Canvas(self.results_frame)
        scrollbar = ttk.Scrollbar(
            self.results_frame, orient="vertical", command=self.results_canvas.yview
        )
        scrollable_frame = ttk.Frame(self.results_canvas, style="NoBorder.TFrame")

        self.results_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.results_canvas.configure(
                scrollregion=self.results_canvas.bbox("all")
            ),
        )
        self.results_canvas.configure(yscrollcommand=scrollbar.set)

        self.results_canvas.bind("<Enter>", self.main_window._on_canvas_enter)
        self.results_canvas.bind("<Leave>", self.main_window._on_canvas_leave)

        self.results_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.results_body_frame = ttk.Frame(scrollable_frame)
        self.results_body_frame.pack(fill=X, padx=20, pady=10)

        # Загрузка иконок ТС
        self.vehicle_images_tk = {}
        for vehicle_type, path in self.vehicle_images.items():
            full_path = resource_path(path)
            if os.path.exists(full_path):
                try:
                    image = Image.open(full_path)
                    image = image.resize((100, 100), Image.Resampling.LANCZOS)
                    image_tk = ImageTk.PhotoImage(image)
                    self.vehicle_images_tk[vehicle_type] = image_tk
                except Exception as e:
                    pass

    def set_active_button(self, button_name):
        """Устанавливает активное состояние для указанной кнопки"""
        self.current_active_button = button_name
        buttons = {
            "add": self.add_button,
            "processes": self.processes_button,
            "history": self.history_button,
        }
        for name, btn in buttons.items():
            if name == button_name and hasattr(btn, "image_active"):
                btn.configure(image=btn.image_active)
            elif hasattr(btn, "image_default"):
                btn.configure(image=btn.image_default)
            else:
                pass

    def clear_search_placeholder(self, event):
        """Очистка текста 'Поиск' при фокусе"""
        if self.search_entry.get() == "Поиск":
            self.search_entry.delete(0, END)

    def restore_search_placeholder(self, event):
        """Восстановление текста 'Поиск', если поле пустое"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Поиск")

    def update_results(self):
        """Обновление списка ТС"""
        for widget in self.results_body_frame.winfo_children():
            widget.destroy()

        try:
            vehicles = get_all_vehicles()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список ТС: {e}")
            return

        if not vehicles:
            ttk.Label(
                self.results_body_frame,
                text="Список транспортных средств пуст.",
                style="Custom.TLabel",
            ).pack(pady=20)
            return

        search_text = self.search_entry.get().lower().strip()
        if search_text == "поиск":
            search_text = ""
        filter_type = self.filter_combobox.get()

        filtered_vehicles = vehicles
        if search_text:
            filtered_vehicles = [
                v
                for v in filtered_vehicles
                if search_text in v.get("contract_number", "").lower().strip()
                or search_text in v.get("customer", "").lower().strip()
                or search_text in v.get("number", "").lower().strip()
                or search_text in v.get("brand", "").lower().strip()
            ]
        if filter_type != "Все типы":
            filtered_vehicles = [
                v
                for v in filtered_vehicles
                if v.get("type", "").lower().strip() == filter_type.lower().strip()
            ]

        if not filtered_vehicles:
            ttk.Label(
                self.results_body_frame,
                text="Нет транспортных средств, соответствующих фильтру.",
                style="Custom.TLabel",
            ).pack(pady=20)
            return

        for idx, vehicle in enumerate(filtered_vehicles):
            vehicle_frame = ttk.Frame(self.results_body_frame, style="NoBorder.TFrame")
            vehicle_frame.pack(fill=X, pady=5)

            # Иконка ТС
            vehicle_type = vehicle.get("type", "Разное")
            vehicle_icon = self.vehicle_images_tk.get(
                vehicle_type, self.vehicle_images_tk.get("Разное")
            )
            if vehicle_icon:
                ttk.Label(
                    vehicle_frame, image=vehicle_icon, style="Custom.TLabel"
                ).pack(side=LEFT, padx=10)
            else:
                ttk.Label(
                    vehicle_frame, text="[Иконка не загружена]", style="Custom.TLabel"
                ).pack(side=LEFT, padx=10)

            # Текст с данными ТС
            vehicle_text = (
                f"{vehicle.get('type', 'Не указан')} — {vehicle.get('customer', 'Не указан')}, "
                f"Заявка № {vehicle.get('contract_number', 'Не указан')}, "
                f"Гос. номер {vehicle.get('number', 'Не указан')}, "
                f"Марка — {vehicle.get('brand', 'Не указан')}"
            )
            vehicle_label = ttk.Label(
                vehicle_frame, text=vehicle_text, style="Custom.TLabel", wraplength=0
            )
            vehicle_label.pack(side=LEFT, padx=10, fill=X, expand=True)

            # Кнопки
            button_frame = ttk.Frame(vehicle_frame, style="NoBorder.TFrame")
            button_frame.pack(side=RIGHT, padx=10)

            # Кнопка "Редактировать"
            try:
                edit_icon_path = resource_path(r"Tandem/assets/edit.png")
                edit_icon_active_path = resource_path(r"Tandem/assets/edit_active.png")
                edit_image = Image.open(edit_icon_path)
                edit_icon = ImageTk.PhotoImage(edit_image)
                edit_active_image = Image.open(edit_icon_active_path)
                edit_icon_active = ImageTk.PhotoImage(edit_active_image)
                edit_button = ttk.Button(
                    button_frame,
                    image=edit_icon,
                    style="NoBorder.TButton",
                    command=lambda vid=vehicle["id"]: self.main_window.edit_vehicle(
                        vid
                    ),
                    takefocus=0,
                )
                edit_button.pack(side=LEFT, padx=5)
                edit_button.image_default = edit_icon
                edit_button.image_active = edit_icon_active
                edit_button.bind(
                    "<Enter>",
                    lambda e, b=edit_button: b.configure(image=b.image_active),
                )
                edit_button.bind(
                    "<Leave>",
                    lambda e, b=edit_button: b.configure(image=b.image_default),
                )
                button_frame.image_edit = edit_icon
            except Exception as e:
                edit_button = ttk.Button(
                    button_frame,
                    text="Ред.",
                    style="NoBorder.TButton",
                    command=lambda vid=vehicle["id"]: self.main_window.edit_vehicle(
                        vid
                    ),
                    takefocus=0,
                )
                edit_button.pack(side=LEFT, padx=5)

            # Кнопка "Печать"
            try:
                print_icon_default_path = resource_path(
                    r"Tandem/assets/print_icon_default.png"
                )
                print_icon_hover_path = resource_path(
                    r"Tandem/assets/print_icon_while_hovering.png"
                )
                print_image = Image.open(print_icon_default_path)
                print_icon_default = ImageTk.PhotoImage(print_image)
                print_hover_image = Image.open(print_icon_hover_path)
                print_icon_hover = ImageTk.PhotoImage(print_hover_image)
                print_button = ttk.Button(
                    button_frame,
                    image=print_icon_default,
                    style="NoBorder.TButton",
                    command=lambda vid=vehicle["id"]: self.main_window.print_vehicle(
                        vid
                    ),
                    takefocus=0,
                )
                print_button.pack(side=LEFT, padx=5)
                print_button.image_default = print_icon_default
                print_button.image_active = print_icon_hover
                print_button.bind(
                    "<Enter>",
                    lambda e, b=print_button: b.configure(image=b.image_active),
                )
                print_button.bind(
                    "<Leave>",
                    lambda e, b=print_button: b.configure(image=b.image_default),
                )
                button_frame.image_print = print_icon_default
            except Exception as e:
                print_button = ttk.Button(
                    button_frame,
                    text="Печ.",
                    style="NoBorder.TButton",
                    command=lambda vid=vehicle["id"]: self.main_window.print_vehicle(
                        vid
                    ),
                    takefocus=0,
                )
                print_button.pack(side=LEFT, padx=5)

            # Кнопка "Удалить"
            try:
                delete_icon_default_path = resource_path(
                    r"Tandem/assets/delete_icon_default.png"
                )
                delete_icon_hover_path = resource_path(
                    r"Tandem/assets/delete_icon_while_hovering.png"
                )
                delete_image = Image.open(delete_icon_default_path)
                delete_icon_default = ImageTk.PhotoImage(delete_image)
                delete_hover_image = Image.open(delete_icon_hover_path)
                delete_icon_hover = ImageTk.PhotoImage(delete_hover_image)
                delete_button = ttk.Button(
                    button_frame,
                    image=delete_icon_default,
                    style="NoBorder.TButton",
                    command=lambda vid=vehicle["id"]: self.delete_vehicle(vid),
                    takefocus=0,
                )
                delete_button.pack(side=LEFT, padx=5)
                delete_button.image_default = delete_icon_default
                delete_button.image_active = delete_icon_hover
                delete_button.bind(
                    "<Enter>",
                    lambda e, b=delete_button: b.configure(image=b.image_active),
                )
                delete_button.bind(
                    "<Leave>",
                    lambda e, b=delete_button: b.configure(image=b.image_default),
                )
                button_frame.image_delete = delete_icon_default
            except Exception as e:
                delete_button = ttk.Button(
                    button_frame,
                    text="Удал.",
                    style="NoBorder.TButton",
                    command=lambda vid=vehicle["id"]: self.delete_vehicle(vid),
                    takefocus=0,
                )
                delete_button.pack(side=LEFT, padx=5)

    def filter_vehicles(self, event=None):
        """Фильтрация списка ТС"""
        self.update_results()

    def delete_vehicle(self, vehicle_id):
        """Удаление ТС"""
        try:
            delete_vehicle(vehicle_id)
            messagebox.showinfo("Успех", "Транспортное средство успешно удалено.")
            self.update_results()
        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось удалить транспортное средство: {e}"
            )
