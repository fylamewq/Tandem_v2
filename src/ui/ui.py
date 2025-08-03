import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.db.database import (
    init_db,
    get_all_vehicles,
    add_print_history,
    get_materials_and_works,
    get_vehicle_by_id,
)
from src.pdf.report_generator import generate_pdf
from pages.add_page import AddPage
from pages.results_page import ResultsPage
from pages.history_page import HistoryPage
from pages.processes import ProcessesPage
from tkinter import messagebox
from PIL import Image, ImageTk
import tkinter as tk
from src.utils.utils import resource_path
import subprocess

class UI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tandem")
        self.root.geometry("1280x720+100+100")

        self.current_canvas = None

        # Установка иконки окна
        icon_path = resource_path(r"Tandem/assets/icon.png")
        try:
            icon_image = Image.open(icon_path)
            icon = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, icon)
            self.icon = icon
        except Exception:
            pass

        self.style = ttk.Style()
        self.configure_styles()

        # Логотип
        self.logo_frame = tk.Frame(self.root, background="#FFFFFF")
        self.logo_frame.pack(fill="x", pady=10)
        self.logo_frame.update()

        logo_path = resource_path(r"Tandem/assets/logo.png")
        logo_active_path = resource_path(r"Tandem/assets/logo_active.png")
        try:
            logo_image = Image.open(logo_path)
            logo_active_image = Image.open(logo_active_path)
            logo_width, logo_height = 190, 32
            container_width, container_height = 200, 40
        except Exception:
            logo_width, logo_height = 190, 32
            container_width, container_height = 200, 40

        logo_container = ttk.Frame(
            self.logo_frame,
            style="NoBorder.TFrame",
            width=container_width,
            height=container_height,
        )
        logo_container.pack(anchor="center")
        logo_container.pack_propagate(False)
        logo_container.update()

        try:
            self.logo_image = ImageTk.PhotoImage(logo_image)
            self.logo_active_image = ImageTk.PhotoImage(logo_active_image)

            self.logo_label = ttk.Label(
                logo_container,
                image=self.logo_image,
                style="Logo.TLabel",
            )
            self.logo_label.pack(anchor="center")
            self.logo_label.image_default = self.logo_image
            self.logo_label.image_active = self.logo_active_image
            self.logo_label.bind(
                "<Enter>",
                lambda e: self.logo_label.configure(image=self.logo_label.image_active),
            )
            self.logo_label.bind(
                "<Leave>",
                lambda e: self.logo_label.configure(
                    image=self.logo_label.image_default
                ),
            )
            self.logo_label.bind("<Button-1>", lambda e: self.show_results())
            self.logo_label.update()
        except Exception:
            tk.Label(
                logo_container,
                text="Логотип не загружен",
                background="#FFFFFF",
                foreground="black",
            ).pack(anchor="center")

        init_db()

        self.create_frames()
        self.show_results()

        # Прокрутка для Canvas
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)
        self.root.bind_all("<Button-4>", lambda event: self.on_mousewheel_manual(-1))
        self.root.bind_all("<Button-5>", lambda event: self.on_mousewheel_manual(1))

        self.root.update()
        self.root.state("normal")
        self.root.mainloop()

    def configure_styles(self):
        self.style.configure(
            "NoBorder.TFrame", borderwidth=0, relief=FLAT, highlightthickness=0
        )
        self.style.configure(
            "NoBorder.TButton",
            borderwidth=0,
            relief=FLAT,
            highlightthickness=0,
            highlightcolor="",
            highlightbackground="",
            focuscolor="",
            background="#FFFFFF",
            bordercolor="",
            foreground="black",
        )
        self.style.map(
            "NoBorder.TButton",
            highlightthickness=[("active", 0), ("focus", 0)],
            borderwidth=[("active", 0), ("focus", 0)],
            relief=[("active", FLAT), ("focus", FLAT)],
            highlightcolor=[("active", ""), ("focus", "")],
            highlightbackground=[("active", ""), ("focus", "")],
            bordercolor=[("active", ""), ("focus", "")],
            background=[("active", "#FFFFFF")],
            foreground=[("active", "black")],
        )
        self.style.configure(
            "Logo.TLabel",
            borderwidth=0,
            relief=FLAT,
            highlightthickness=0,
            highlightcolor="",
            highlightbackground="",
            background="#FFFFFF",
            bordercolor="",
        )
        self.style.configure(
            "Custom.TLabel",
            background="#FFFFFF",
            foreground="black",
            font=("Arial", 12),
        )

        self.vehicle_images = {
            "Легковые": r"Tandem/assets/passenger_car.png",
            "Рефрижераторы": r"Tandem/assets/refrigerator.png",
            "Автобусы": r"Tandem/assets/bus.png",
            "Разное": r"Tandem/assets/different.png",
        }

        self.current_vehicle_id = None

    def create_frames(self):
        self.main_frame = ttk.Frame(self.root, style="NoBorder.TFrame")
        self.main_frame.pack(fill="both", expand=True)

        self.results_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")
        self.add_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")
        self.history_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")
        self.processes_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")

        self.results_page = ResultsPage(self)
        self.add_page = AddPage(self)
        self.history_page = HistoryPage(self)
        self.processes_page = ProcessesPage(self)

    def on_mousewheel(self, event):
        if self.current_canvas and isinstance(self.current_canvas, tk.Canvas):
            self.current_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_manual(self, direction):
        if self.current_canvas and isinstance(self.current_canvas, tk.Canvas):
            self.current_canvas.yview_scroll(direction, "units")

    def _on_canvas_enter(self, event):
        self.current_canvas = event.widget

    def _on_canvas_leave(self, event):
        self.current_canvas = None

    def show_results(self):
        self.hide_all_frames()
        self.results_frame.pack(fill="both", expand=True)
        self.results_page.update_results()
        self.results_page.set_active_button(None)

    def show_add(self, clear=True):
        self.hide_all_frames()
        self.add_frame.pack(fill="both", expand=True)
        self.current_vehicle_id = None
        if clear and hasattr(self.add_page, "clear_form"):
            self.add_page.clear_form()
        self.results_page.set_active_button("add")

    def show_history(self):
        self.hide_all_frames()
        self.history_frame.pack(fill="both", expand=True)
        self.history_page.update_history()
        self.results_page.set_active_button("history")

    def show_processes(self):
        self.hide_all_frames()
        self.processes_frame.pack(fill="both", expand=True)
        # Синхронизация процессов (обновление данных и подсказок)
        if hasattr(self.processes_page, "update_vehicle_combobox"):
            self.processes_page.update_vehicle_combobox()
        if hasattr(self.processes_page, "update_global_tables"):
            self.processes_page.update_global_tables()
        self.results_page.set_active_button("processes")

    def hide_all_frames(self):
        for frame in [
            self.results_frame,
            self.add_frame,
            self.history_frame,
            self.processes_frame,
        ]:
            frame.pack_forget()

    def edit_vehicle(self, vehicle_id):
        self.current_vehicle_id = vehicle_id
        self.show_add(clear=True)
        if hasattr(self.add_page, "load_vehicle"):
            self.add_page.load_vehicle(vehicle_id)

    def print_vehicle(self, vehicle_id):
        try:
            vehicle = get_vehicle_by_id(vehicle_id)
            if not vehicle:
                messagebox.showerror("Ошибка", "Транспортное средство не найдено.")
                return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные ТС: {e}")
            return
        try:
            materials_and_works = get_materials_and_works(vehicle_id)
            pdf_path = generate_pdf(vehicle, materials_and_works)
            add_print_history(vehicle, pdf_path)
            try:
                if sys.platform.startswith("win"):
                    os.startfile(pdf_path)
                elif sys.platform.startswith("darwin"):
                    subprocess.run(["open", pdf_path])
                else:
                    subprocess.run(["xdg-open", pdf_path])
            except Exception as e:
                messagebox.showwarning(
                    "Предупреждение",
                    f"Не удалось открыть PDF: {e}\n"
                    f"Файл сохранен по пути: {pdf_path}\n"
                    "Пожалуйста, откройте его вручную.",
                )
            self.history_page.update_history()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать PDF: {e}")