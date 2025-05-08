import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.db.database import (
    init_db,
    add_vehicle,
    get_all_vehicles,
    delete_vehicle,
    add_print_history,
    get_print_history,
    update_vehicle,
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

        # Новый атрибут для хранения текущего Canvas
        self.current_canvas = None

        # Установка иконки окна
        icon_path = resource_path(r"Tandem/assets/icon.png")
        try:
            icon_image = Image.open(icon_path)
            icon = ImageTk.PhotoImage(icon_image)
            self.root.iconphoto(True, icon)
            self.icon = icon  # Сохраняем ссылку
        except Exception as e:
            pass

        self.style = ttk.Style()
        self.configure_styles()

        # Создаем фрейм для логотипа
        self.logo_frame = tk.Frame(self.root, background="#FFFFFF")
        self.logo_frame.pack(fill="x", pady=10)
        # Добавляем диагностику размеров logo_frame после его отображения
        self.logo_frame.update()

        # Загружаем логотип для определения его размера
        logo_path = resource_path(r"Tandem/assets/logo.png")
        logo_active_path = resource_path(r"Tandem/assets/logo_active.png")
        try:
            logo_image = Image.open(logo_path)  # 190x32
            logo_active_image = Image.open(logo_active_path)  # 190x32
            logo_width, logo_height = 190, 32  # Размер изображений
            container_width, container_height = (
                200,
                40,
            )  # Увеличиваем контейнер для запаса
        except Exception as e:
            logo_width, logo_height = 190, 32
            container_width, container_height = 200, 40  # Запасной размер

        # Создаем фрейм для логотипа
        logo_container = ttk.Frame(
            self.logo_frame,
            style="NoBorder.TFrame",
            width=container_width,
            height=container_height,
        )
        logo_container.pack(anchor="center")
        logo_container.pack_propagate(False)  # Запрещаем изменение размера фрейма
        # Диагностика размеров logo_container
        logo_container.update()
  
        # Отображаем логотип как метку (Label вместо Button, чтобы избежать обрезки)
        try:
            self.logo_image = ImageTk.PhotoImage(logo_image)
            self.logo_active_image = ImageTk.PhotoImage(logo_active_image)

            self.logo_label = ttk.Label(
                logo_container,
                image=self.logo_image,
                style="Logo.TLabel",  # Новый стиль для метки
            )
            self.logo_label.pack(anchor="center")
            self.logo_label.image_default = self.logo_image
            self.logo_label.image_active = self.logo_active_image
            # Добавляем переключение при наведении
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
            # Добавляем обработку клика для перехода на страницу
            self.logo_label.bind("<Button-1>", lambda e: self.show_results())
            # Диагностика размеров logo_label
            self.logo_label.update()
        except Exception as e:
            tk.Label(
                logo_container,
                text="Логотип не загружен",
                background="#FFFFFF",
                foreground="black",
            ).pack(anchor="center")

        init_db()

        self.create_frames()
        self.show_results()

        # Привязка событий прокрутки глобально
        self.root.bind_all("<MouseWheel>", self.on_mousewheel)
        # Добавим поддержку Linux/macOS
        self.root.bind_all("<Button-4>", lambda event: self.on_mousewheel_manual(-1))
        self.root.bind_all("<Button-5>", lambda event: self.on_mousewheel_manual(1))

        self.root.update()
        self.root.state("normal")
        self.root.mainloop()

    def configure_styles(self):
        """Настройка стилей для фреймов, кнопок и меток без обводки"""
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

        # Стиль для метки логотипа
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

        # Добавляем стиль Custom.TLabel
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
        """Создание фреймов для страниц"""
        self.main_frame = ttk.Frame(self.root, style="NoBorder.TFrame")
        self.main_frame.pack(fill=BOTH, expand=True)

        self.results_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")
        self.add_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")
        self.history_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")
        self.processes_frame = ttk.Frame(self.main_frame, style="NoBorder.TFrame")

        self.results_page = ResultsPage(self)
        self.add_page = AddPage(self)
        self.history_page = HistoryPage(self)
        self.processes_page = ProcessesPage(self)

    def on_mousewheel(self, event):
        """Обработка прокрутки мышью"""
        if self.current_canvas and isinstance(self.current_canvas, tk.Canvas):
            self.current_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_manual(self, direction):
        """Обработка прокрутки для Linux/macOS (Button-4 и Button-5)"""
        if self.current_canvas and isinstance(self.current_canvas, tk.Canvas):
            self.current_canvas.yview_scroll(direction, "units")

    def _on_canvas_enter(self, event):
        """Событие: курсор вошел в область Canvas"""
        self.current_canvas = event.widget

    def _on_canvas_leave(self, event):
        """Событие: курсор покинул область Canvas"""
        self.current_canvas = None

    def show_results(self):
        """Показать страницу 'Список'"""
        self.hide_all_frames()
        self.results_frame.pack(fill=BOTH, expand=True)
        self.results_page.update_results()
        self.results_page.set_active_button(None)

    def show_add(self):
        """Показать страницу 'Добавить'"""
        self.hide_all_frames()
        self.add_frame.pack(fill=BOTH, expand=True)
        self.current_vehicle_id = None
        self.add_page.clear_form()
        self.results_page.set_active_button("add")

    def show_history(self):
        """Показать страницу 'История'"""
        self.hide_all_frames()
        self.history_frame.pack(fill=BOTH, expand=True)
        self.history_page.update_history()
        self.results_page.set_active_button("history")

    def show_processes(self):
        """Показать страницу 'Процессы'"""
        self.hide_all_frames()
        self.processes_frame.pack(fill=BOTH, expand=True)
        self.processes_page.update_processes()  # Добавляем обновление данных
        self.results_page.set_active_button("processes")

    def hide_all_frames(self):
        """Скрыть все фреймы"""
        for frame in [
            self.results_frame,
            self.add_frame,
            self.history_frame,
            self.processes_frame,
        ]:
            frame.pack_forget()

    def edit_vehicle(self, vehicle_id):
        """Редактирование ТС"""
        self.current_vehicle_id = vehicle_id
        try:
            vehicles = get_all_vehicles()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные ТС: {e}")
            return
        vehicle = next((v for v in vehicles if v["id"] == vehicle_id), None)
        if vehicle:
            self.hide_all_frames()
            self.add_frame.pack(fill=BOTH, expand=True)
            self.add_page.edit_vehicle(vehicle)
        else:
            messagebox.showerror("Ошибка", "Транспортное средство не найдено.")

    def print_vehicle(self, vehicle_id):
        """Печать ТС"""
        try:
            vehicles = get_all_vehicles()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные ТС: {e}")
            return
        vehicle = next((v for v in vehicles if v["id"] == vehicle_id), None)
        if vehicle:
            try:
                pdf_path = generate_pdf(vehicle)
                add_print_history(vehicle, pdf_path)
                try:
                    # Пробуем открыть PDF через приложение по умолчанию
                    subprocess.run(["start", "", pdf_path], shell=True)
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
        else:
            messagebox.showerror("Ошибка", "Транспортное средство не найдено.")