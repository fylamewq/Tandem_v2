from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import mm
import os
from datetime import datetime

def resource_path(relative_path):
    import sys
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', relative_path)

# Регистрация шрифта
font_path = resource_path("assets/DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

def generate_pdf(vehicle_data):
    output_dir = os.path.join(os.getenv('APPDATA'), 'Tandem', 'reports')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(output_dir, f"report_{timestamp}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("DejaVuSans", 10)

    WIDTH, HEIGHT = A4
    left = 20 * mm
    right = WIDTH - 20 * mm

    # --- Шапка ---
    c.setFont("DejaVuSans", 11)
    c.drawString(left, HEIGHT - 30, 'ООО "Аверс"')
    c.setFont("DejaVuSans", 9)
    c.drawString(left, HEIGHT - 42, '654038, г. Новокузнецк, ул. Промстроевская, 60 корп.7')
    c.drawString(left, HEIGHT - 54, 'тел./факс (3843)52-76-59; e-mail : avers_2005@mail.ru')

    # --- Квадраты с датами и номерами ---
    def draw_rect_text(x, y, w, h, txt, fontsize=9):
        c.setFont("DejaVuSans", fontsize)
        c.rect(x, y, w, h)
        c.drawCentredString(x + w/2, y + h/2 - 4, txt)

    table_top = HEIGHT - 65
    cell_h = 18
    x0 = right - 120
    y0 = table_top - cell_h * 3
    col_w = 60

    draw_rect_text(x0, table_top - cell_h, col_w, cell_h, "Дата приёма")
    draw_rect_text(x0 + col_w, table_top - cell_h, col_w, cell_h, vehicle_data.get("acceptance_date", ""))
    draw_rect_text(x0, table_top - 2*cell_h, col_w, cell_h, "Дата наряда работ")
    draw_rect_text(x0 + col_w, table_top - 2*cell_h, col_w, cell_h, vehicle_data.get("work_order_date", ""))
    draw_rect_text(x0, table_top - 3*cell_h, col_w, cell_h, "Дата окончания работ")
    draw_rect_text(x0 + col_w, table_top - 3*cell_h, col_w, cell_h, vehicle_data.get("completion_date", ""))

    # --- Заголовок и номер ---
    c.setFont("DejaVuSans", 12)
    c.drawCentredString(WIDTH/2, table_top - 30, "Договор наряд-заказ на работы")
    c.setFont("DejaVuSans", 9)
    c.drawCentredString(WIDTH/2, table_top - 44, "С прейскурантом цен ознакомлен.")

    c.setFont("DejaVuSans", 10)
    c.drawString(left, table_top - 70, f"Договор наряд-заказ на работы    № {vehicle_data.get('contract_number', '')}")

    # --- Поля слева/справа ---
    y_base = table_top - 92
    c.setFont("DejaVuSans", 10)
    c.drawString(left, y_base, f"Заказчик: {vehicle_data.get('customer', '')}")
    c.drawString(left, y_base - 14, f"Адрес: {vehicle_data.get('address', '')}")
    c.drawString(left, y_base - 28, f"Наименование оборудования: {vehicle_data.get('type', '')}")
    c.drawString(left, y_base - 42, f"Оборудование сдал: {vehicle_data.get('equipment_delivered', '') if vehicle_data.get('equipment_delivered','') else '_____________________' }")
    c.drawString(left, y_base - 56, f"Государственный номер: {vehicle_data.get('number', '')}")
    c.drawString(left, y_base - 70, f"Марка: {vehicle_data.get('brand', '')}")

    c.drawString(right - 180, y_base, f"Холодильная машина: {vehicle_data.get('refrigerator_brand', '')}")
    c.drawString(right - 180, y_base - 14, f"Автомобиль: {vehicle_data.get('type', '')}")
    c.drawString(right - 180, y_base - 28, f"Гос. номер: {vehicle_data.get('number', '')}")
    c.drawString(right - 180, y_base - 42, f"Год выпуска: {vehicle_data.get('year', '')}")
    c.drawString(right - 180, y_base - 56, f"Расписка:")

    # --- Предварительный осмотр ---
    y_pre = y_base - 90
    c.setFont("DejaVuSans", 10)
    c.drawString(left, y_pre, "Предварительный осмотр (обнаружены неисправности):")
    c.setFont("DejaVuSans", 9)
    recommendations = vehicle_data.get("preliminary_inspection", "")
    c.drawString(left, y_pre - 14, recommendations)

    # --- Таблица выполненных работ ---
    y_table = y_pre - 30
    col_widths = [20, 150, 35, 35, 40, 40, 60, 60]
    headers = [
        "№", "Выполненные работы", "ед. изм.", "кол-во", "цена за ед.", "сумма", "Параметры оборудования", ""
    ]

    # Draw table header
    x = left
    y = y_table
    c.setFont("DejaVuSans", 9)
    for i, header in enumerate(headers):
        w = col_widths[i]
        c.rect(x, y, w, 18, fill=0)
        c.drawCentredString(x + w/2, y + 5, header)
        x += w

    # Draw rows
    works = vehicle_data.get("works", [])
    y_row = y - 18
    for idx, work in enumerate(works, 1):
        # work: [name, unit, quantity, price, sum, param1, param2]
        x = left
        values = [
            str(idx),
            str(work.get("work", "")),
            str(work.get("unit", "")),
            str(work.get("quantity", "")),
            str(work.get("price_per_unit", "")),
            str(round(float(work.get("quantity", 0)) * float(work.get("price_per_unit", 0)), 2) if work.get("quantity") and work.get("price_per_unit") else ""),
            str(work.get("equipment_param1", "")),
            str(work.get("equipment_param2", "")),
        ]
        for i, val in enumerate(values):
            w = col_widths[i]
            c.rect(x, y_row, w, 16, fill=0)
            c.setFont("DejaVuSans", 9)
            c.drawCentredString(x + w/2, y_row + 4, val)
            x += w
        y_row -= 16

    # Итоги по работам
    c.setFont("DejaVuSans", 9)
    c.rect(left, y_row, sum(col_widths[:6]), 16, fill=0)
    c.drawRightString(left + sum(col_widths[:6]) - 5, y_row + 4, "ИТОГО:")
    c.drawString(left + sum(col_widths[:6]) + 2, y_row + 4, str(vehicle_data.get("work_total", "")))
    y_row -= 16
    c.rect(left, y_row, sum(col_widths[:6]), 16, fill=0)
    c.drawRightString(left + sum(col_widths[:6]) - 5, y_row + 4, "ИТОГО с коэффициентом:")
    c.drawString(left + sum(col_widths[:6]) + 2, y_row + 4, str(vehicle_data.get("work_total_with_coeff", "")))
    y_row -= 24

    # --- Таблица материалов (накладная) ---
    c.setFont("DejaVuSans", 10)
    c.drawString(left, y_row, "Накладная на запасные части и расходные материалы")
    y_row -= 18

    mat_headers = ["№", "Наименование", "ед. изм.", "кол-во", "цена за ед.", "сумма"]
    mat_col_widths = [20, 250, 35, 35, 50, 50]
    x = left
    for i, header in enumerate(mat_headers):
        w = mat_col_widths[i]
        c.rect(x, y_row, w, 16, fill=0)
        c.setFont("DejaVuSans", 9)
        c.drawCentredString(x + w/2, y_row + 4, header)
        x += w
    y_row -= 16

    parts = vehicle_data.get("parts", [])
    for idx, part in enumerate(parts, 1):
        x = left
        # part: [name, unit, quantity, price, sum]
        values = [
            str(idx),
            str(part.get("material", "")),
            str(part.get("unit", "")),
            str(part.get("quantity", "")),
            str(part.get("price_per_unit", "")),
            str(round(float(part.get("quantity", 0)) * float(part.get("price_per_unit", 0)), 2) if part.get("quantity") and part.get("price_per_unit") else ""),
        ]
        for i, val in enumerate(values):
            w = mat_col_widths[i]
            c.rect(x, y_row, w, 16, fill=0)
            c.setFont("DejaVuSans", 9)
            c.drawCentredString(x + w/2, y_row + 4, val)
            x += w
        y_row -= 16

    # Итог по материалам
    c.rect(left, y_row, sum(mat_col_widths[:5]), 16, fill=0)
    c.setFont("DejaVuSans", 9)
    c.drawRightString(left + sum(mat_col_widths[:5]) - 5, y_row + 4, "ИТОГО:")
    c.drawString(left + sum(mat_col_widths[:5]) + 2, y_row + 4, str(vehicle_data.get("parts_total", "")))
    y_row -= 30

    # --- Итог по наряду ---
    c.setFont("DejaVuSans", 10)
    c.drawString(left, y_row, f"ИТОГО по наряд-заказу: {vehicle_data.get('work_total_with_coeff', '') or ''}")
    y_row -= 18

    # --- Рекомендации ---
    c.setFont("DejaVuSans", 10)
    c.drawString(left, y_row, "Рекомендации:")
    c.setFont("DejaVuSans", 9)
    c.drawString(left + 80, y_row, vehicle_data.get("recommendations", ""))
    y_row -= 20

    # --- Подписи ---
    c.setFont("DejaVuSans", 9)
    c.drawString(left, y_row, "Представитель Исполнителя (Должность):")
    c.drawString(left + 180, y_row, vehicle_data.get("executor_position", ""))
    c.drawString(left + 300, y_row, "Ф.И.О.:")
    c.drawString(left + 340, y_row, vehicle_data.get("executor_name", ""))
    c.drawString(left + 470, y_row, "Подпись: ______________")
    y_row -= 14

    c.drawString(left, y_row, "Оборудование принято в исправном / неисправном состоянии (нужное подчеркнуть).")
    y_row -= 14

    c.drawString(left, y_row, "Представитель Заказчика (Должность):")
    c.drawString(left + 180, y_row, vehicle_data.get("customer_position", ""))
    c.drawString(left + 300, y_row, "Ф.И.О.:")
    c.drawString(left + 340, y_row, vehicle_data.get("customer_name", ""))
    c.drawString(left + 470, y_row, "Подпись: ______________")

    c.save()
    return pdf_path