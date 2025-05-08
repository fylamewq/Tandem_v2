from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

def resource_path(relative_path):
    """Получение абсолютного пути к ресурсу"""
    import sys
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', relative_path)

# Регистрация шрифта
font_path = resource_path("assets/DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

def generate_pdf(vehicle_data):
    """Генерация PDF-отчёта"""
    output_dir = os.path.join(os.getenv('APPDATA'), 'Tandem', 'reports')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(output_dir, f"report_{timestamp}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.setFont("DejaVuSans", 10)

    # Шапка
    c.drawString(50, 800, "ООО \"Аверс\"")
    c.drawString(50, 785, "654038, г. Новокузнецк, ул. Промстроевская, 60, корп. 2")
    c.drawString(50, 770, "тел/факс (3843) 52-76-59")
    c.drawString(50, 755, "e-mail: avers_2005@mail.ru")

    # Заголовок
    c.setFont("DejaVuSans", 12)
    c.drawCentredString(300, 720, "Договор наряд-заказ на работы")
    c.setFont("DejaVuSans", 10)
    c.drawCentredString(300, 705, "С действующими ценами ознакомлен")

    # Данные заказчика
    y = 675
    customer = vehicle_data.get('customer', '')
    c.drawString(50, y, f"Заказчик: {customer if customer else ''}")
    y -= 15
    address = vehicle_data.get('address', '')
    c.drawString(50, y, f"Адрес: {address if address else ''}")
    y -= 15
    vehicle_type = vehicle_data.get('type', '')
    c.drawString(50, y, f"Наименование оборудования: {vehicle_type if vehicle_type else ''}")

    # Данные оборудования
    y -= 30
    c.drawString(50, y, "Оборудование сдано:")
    y -= 15
    acceptance_date = vehicle_data.get('acceptance_date', '')
    c.drawString(50, y, f"Дата приёма: {acceptance_date if acceptance_date else ''}")
    y -= 15
    completion_date = vehicle_data.get('completion_date', '')
    c.drawString(50, y, f"Дата окончания работ: {completion_date if completion_date else ''}")

    # Таблица выполненных работ
    y -= 30
    c.drawString(50, y, "Выполненные работы")
    y -= 15
    headers = ["№ п/п", "Наименование выполненных работ", "Ед. изм.", "Кол-во", "Цена за ед.", "Сумма"]
    col_widths = [40, 200, 60, 60, 60, 60]
    x = 50
    for i, header in enumerate(headers):
        c.drawString(x, y, header)
        x += col_widths[i]
    y -= 5
    c.line(50, y, 550, y)
    y -= 15

    works = vehicle_data.get("works", [])
    for idx, work in enumerate(works, 1):
        if not any(work):
            continue
        x = 50
        c.drawString(x, y, str(idx))
        x += col_widths[0]
        c.drawString(x, y, str(work[0] if work[0] is not None else ""))
        x += col_widths[1]
        c.drawString(x, y, str(work[1] if work[1] is not None else ""))
        x += col_widths[2]
        c.drawString(x, y, str(work[2] if work[2] is not None else ""))
        x += col_widths[3]
        c.drawString(x, y, str(work[3] if work[3] is not None else ""))
        x += col_widths[4]
        c.drawString(x, y, str(work[4] if work[4] is not None else ""))
        y -= 15
        if y < 50:
            c.showPage()
            c.setFont("DejaVuSans", 10)
            y = 800

    # ИТОГО для работ
    y -= 15
    c.drawString(50, y, "ИТОГО")
    work_total = vehicle_data.get("work_total", "0.00")
    c.drawString(470, y, str(work_total if work_total else "0.00"))
    y -= 15
    c.drawString(50, y, "ИТОГО с коэф")
    work_total_with_coeff = vehicle_data.get("work_total_with_coeff", "0.00")
    c.drawString(470, y, str(work_total_with_coeff if work_total_with_coeff else "0.00"))

    # Таблица запасных частей
    y -= 30
    c.drawString(50, y, "Накладная на запасные части и расходные материалы")
    y -= 15
    x = 50
    for i, header in enumerate(headers):
        c.drawString(x, y, header)
        x += col_widths[i]
    y -= 5
    c.line(50, y, 550, y)
    y -= 15

    parts = vehicle_data.get("parts", [])
    for idx, part in enumerate(parts, 1):
        if not any(part):
            continue
        x = 50
        c.drawString(x, y, str(idx))
        x += col_widths[0]
        c.drawString(x, y, str(part[0] if part[0] is not None else ""))
        x += col_widths[1]
        c.drawString(x, y, str(part[1] if part[1] is not None else ""))
        x += col_widths[2]
        c.drawString(x, y, str(part[2] if part[2] is not None else ""))
        x += col_widths[3]
        c.drawString(x, y, str(part[3] if part[3] is not None else ""))
        x += col_widths[4]
        c.drawString(x, y, str(part[4] if part[4] is not None else ""))
        y -= 15
        if y < 50:
            c.showPage()
            c.setFont("DejaVuSans", 10)
            y = 800

    # ИТОГО для частей
    y -= 15
    c.drawString(50, y, "ИТОГО")
    parts_total = vehicle_data.get("parts_total", "0.00")
    c.drawString(470, y, str(parts_total if parts_total else "0.00"))

    # Подписи
    y -= 30
    c.drawString(50, y, "Заказчик: _________________________")
    c.drawString(350, y, "Исполнитель: _________________________")

    c.save()
    return pdf_path