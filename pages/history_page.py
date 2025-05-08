import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.db.database import get_print_history, delete_print_history_entry
from tkinter import messagebox
import os


class HistoryPage:
    def __init__(self, main_window):
        self.main_window = main_window
        self.root = main_window.root
        self.history_frame = main_window.history_frame
        self.init_history_page()

    def init_history_page(self):
        """Инициализация страницы 'История'"""
        self.history_canvas = ttk.Canvas(self.history_frame)
        scrollbar = ttk.Scrollbar(
            self.history_frame, orient="vertical", command=self.history_canvas.yview
        )
        scrollable_frame = ttk.Frame(self.history_canvas, style="Custom.TFrame")

        self.history_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.history_canvas.configure(
                scrollregion=self.history_canvas.bbox("all")
            ),
        )
        self.history_canvas.configure(yscrollcommand=scrollbar.set)

        self.history_canvas.bind("<MouseWheel>", self.main_window.on_mousewheel)

        self.history_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        ttk.Label(
            scrollable_frame, text="История печати", font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=20, pady=10)

        headers = [
            "№ п/п",
            "Договор-Заявка №",
            "Дата",
            "Тип машины",
            "Заказчик",
            "Гос. номер",
            "Путь к файлу",
            "",  # Для кнопки "Открыть"
            "",  # Для кнопки "Удалить"
        ]
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=X, padx=20)

        for col, header in enumerate(headers):
            ttk.Label(
                header_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=0, column=col, sticky="nsew")

        self.history_body_frame = ttk.Frame(scrollable_frame)
        self.history_body_frame.pack(fill=X, padx=20)

        self.update_history()

    def update_history(self):
        """Обновление истории печати"""
        for widget in self.history_body_frame.winfo_children():
            widget.destroy()

        try:
            history = get_print_history()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить историю печати: {e}")
            return

        for row, entry in enumerate(history, 1):
            pdf_path = entry["pdf_path"]
            print_date = entry.get("date", "")
            customer = entry.get("customer", "")
            brand = entry.get("brand", "")
            number = entry.get("number", "")
            contract_number = entry.get("contract_number", "")
            vehicle_type = entry.get("type", "")

            ttk.Label(
                self.history_body_frame,
                text=str(row),
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=0, sticky="nsew")
            ttk.Label(
                self.history_body_frame,
                text=contract_number,
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=1, sticky="nsew")
            ttk.Label(
                self.history_body_frame,
                text=print_date,
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=2, sticky="nsew")
            ttk.Label(
                self.history_body_frame,
                text=vehicle_type,
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=3, sticky="nsew")
            ttk.Label(
                self.history_body_frame,
                text=customer,
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=4, sticky="nsew")
            ttk.Label(
                self.history_body_frame,
                text=number,
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=5, sticky="nsew")
            ttk.Label(
                self.history_body_frame,
                text=pdf_path,
                borderwidth=1,
                relief="solid",
                padding=5,
            ).grid(row=row, column=6, sticky="nsew")
            ttk.Button(
                self.history_body_frame,
                text="Открыть",
                style="Print.TButton",
                command=lambda path=pdf_path: self.open_pdf(path),
            ).grid(row=row, column=7, sticky="nsew", padx=1, pady=1)
            ttk.Button(
                self.history_body_frame,
                text="Удалить",
                style="Print.TButton",
                command=lambda entry_id=entry[
                    "id"
                ], path=pdf_path: self.delete_history_entry(entry_id, path),
            ).grid(row=row, column=8, sticky="nsew", padx=1, pady=1)

        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def open_pdf(self, pdf_path):
        """Открытие PDF-файла с обработкой ошибок"""
        try:
            if os.path.exists(pdf_path):
                os.startfile(pdf_path)  # Для Windows
            else:
                messagebox.showerror("Ошибка", f"Файл {pdf_path} не найден.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def delete_history_entry(self, entry_id, pdf_path):
        """Удаление записи из истории и PDF-файла"""
        # Удаляем PDF-файл, если он существует
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError as e:
                messagebox.showerror(
                    "Ошибка", f"Не удалось удалить файл {pdf_path}: {e}"
                )
                return
        # Удаляем запись из базы данных
        try:
            delete_print_history_entry(entry_id)
            messagebox.showinfo("Успех", "Запись успешно удалена из истории.")
        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось удалить запись из базы данных: {e}"
            )
            return
        # Обновляем таблицу
        self.update_history()
