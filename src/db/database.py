import sqlite3
import os
import sys
from datetime import datetime
from functools import wraps

# --- Константы для диапазонов ID ---
VEHICLE_ID_MIN = 1
VEHICLE_ID_MAX = 9999
MATERIALS_AND_WORKS_ID_MIN = 10000
MATERIALS_AND_WORKS_ID_MAX = 19999
MATERIAL_ID_MIN = 20000
MATERIAL_ID_MAX = 29999
WORK_ID_MIN = 30000
WORK_ID_MAX = 39999

# --- Вспомогательные функции для путей ---
def get_persistent_db_path():
    user_data_dir = os.path.join(os.getenv("APPDATA"), "Tandem")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    return os.path.join(user_data_dir, "database.db")

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", relative_path
        )

# --- Глобальный путь к БД ---
DB_PATH = get_persistent_db_path()

if not os.path.exists(DB_PATH):
    default_db_path = resource_path("data/database.db")
    if os.path.exists(default_db_path):
        with open(default_db_path, "rb") as src, open(DB_PATH, "wb") as dst:
            dst.write(src.read())

# --- Декоратор для автоматического открытия/закрытия соединения ---
def with_connection(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(DB_PATH)
        try:
            result = fn(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    return wrapper

# --- Полная функция инициализации и миграции таблиц ---
@with_connection
def init_db(conn):
    cursor = conn.cursor()

    # Таблица версии схемы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL
        )
    """)

    # Проверяем текущую версию схемы
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    current_version = row[0] if row else 0
    latest_version = 2  # Обновляйте при изменениях

    # Если версия актуальна — ничего не делаем
    if current_version >= latest_version:
        return

    # --- vehicles ---
    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = [
        "id", "contract_number", "date", "acceptance_date", "work_order_date",
        "completion_date", "type", "customer", "number", "brand", "refrigerator_brand",
        "year", "mileage", "phone", "address", "preliminary_inspection", "work_total",
        "work_total_with_coeff", "parts_total", "equipment_delivered", "recommendations",
        "executor_position", "executor_name", "customer_position", "customer_name"
    ]

    if columns and columns != expected_columns:
        cursor.execute("DROP TABLE IF EXISTS vehicles_temp")
        cursor.execute("""
            CREATE TABLE vehicles_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_number TEXT,
                date TEXT,
                acceptance_date TEXT,
                work_order_date TEXT,
                completion_date TEXT,
                type TEXT,
                customer TEXT,
                number TEXT,
                brand TEXT,
                refrigerator_brand TEXT,
                year TEXT,
                mileage TEXT,
                phone TEXT,
                address TEXT,
                preliminary_inspection TEXT,
                work_total TEXT,
                work_total_with_coeff TEXT,
                parts_total TEXT,
                equipment_delivered TEXT,
                recommendations TEXT,
                executor_position TEXT,
                executor_name TEXT,
                customer_position TEXT,
                customer_name TEXT
            )
        """)
        existing_columns = [col for col in columns if col in expected_columns]
        columns_str = ", ".join(existing_columns)
        cursor.execute(f"""
            INSERT INTO vehicles_temp ({columns_str})
            SELECT {columns_str}
            FROM vehicles
        """)
        cursor.execute("DROP TABLE vehicles")
        cursor.execute("ALTER TABLE vehicles_temp RENAME TO vehicles")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_number TEXT,
            date TEXT,
            acceptance_date TEXT,
            work_order_date TEXT,
            completion_date TEXT,
            type TEXT,
            customer TEXT,
            number TEXT,
            brand TEXT,
            refrigerator_brand TEXT,
            year TEXT,
            mileage TEXT,
            phone TEXT,
            address TEXT,
            preliminary_inspection TEXT,
            work_total TEXT,
            work_total_with_coeff TEXT,
            parts_total TEXT,
            equipment_delivered TEXT,
            recommendations TEXT,
            executor_position TEXT,
            executor_name TEXT,
            customer_position TEXT,
            customer_name TEXT
        )
    """)

    # --- print_history ---
    cursor.execute("PRAGMA table_info(print_history)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = [
        "id", "vehicle_id", "print_date", "customer", "brand", "number", "pdf_path"
    ]

    if columns and columns != expected_columns:
        cursor.execute("DROP TABLE IF EXISTS print_history_temp")
        cursor.execute("""
            CREATE TABLE print_history_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                print_date TEXT,
                customer TEXT,
                brand TEXT,
                number TEXT,
                pdf_path TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            )
        """)
        cursor.execute("""
            INSERT INTO print_history_temp (
                id, vehicle_id, print_date, customer, brand, number, pdf_path
            )
            SELECT id, vehicle_id, print_date, customer, brand, number, pdf_path
            FROM print_history
        """)
        cursor.execute("DROP TABLE print_history")
        cursor.execute("ALTER TABLE print_history_temp RENAME TO print_history")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS print_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                print_date TEXT,
                customer TEXT,
                brand TEXT,
                number TEXT,
                pdf_path TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            )
        """)

    # --- materials_and_works ---
    cursor.execute("PRAGMA table_info(materials_and_works)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = [
        "id", "vehicle_id", "material", "work", "unit", "quantity",
        "price_per_unit", "equipment_param1", "equipment_param2"
    ]

    if columns and columns != expected_columns:
        cursor.execute("DROP TABLE IF EXISTS materials_and_works_temp")
        cursor.execute("""
            CREATE TABLE materials_and_works_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                material TEXT,
                work TEXT,
                unit TEXT,
                quantity TEXT,
                price_per_unit TEXT,
                equipment_param1 TEXT,
                equipment_param2 TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            )
        """)
        existing_columns = [col for col in columns if col in expected_columns]
        columns_str = ", ".join(existing_columns)
        cursor.execute(f"""
            INSERT INTO materials_and_works_temp ({columns_str})
            SELECT {columns_str}
            FROM materials_and_works
        """)
        cursor.execute("DROP TABLE materials_and_works")
        cursor.execute("ALTER TABLE materials_and_works_temp RENAME TO materials_and_works")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials_and_works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                material TEXT,
                work TEXT,
                unit TEXT,
                quantity TEXT,
                price_per_unit TEXT,
                equipment_param1 TEXT,
                equipment_param2 TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            )
        """)

    # --- works ---
    cursor.execute("PRAGMA table_info(works)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = ["id", "name", "unit", "price"]

    if columns and columns != expected_columns:
        cursor.execute("DROP TABLE IF EXISTS works_temp")
        cursor.execute("""
            CREATE TABLE works_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unit TEXT,
                price TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO works_temp (id, name, unit, price)
            SELECT id, name, unit, price
            FROM works
        """)
        cursor.execute("DROP TABLE works")
        cursor.execute("ALTER TABLE works_temp RENAME TO works")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unit TEXT,
                price TEXT
            )
        """)

    # --- materials ---
    cursor.execute("PRAGMA table_info(materials)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = ["id", "name", "unit", "price"]

    if columns and columns != expected_columns:
        cursor.execute("DROP TABLE IF EXISTS materials_temp")
        cursor.execute("""
            CREATE TABLE materials_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unit TEXT,
                price TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO materials_temp (id, name, unit, price)
            SELECT id, name, unit, price
            FROM materials
        """)
        cursor.execute("DROP TABLE materials")
        cursor.execute("ALTER TABLE materials_temp RENAME TO materials")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unit TEXT,
                price TEXT
            )
        """)

    # --- Тестовые данные (только если таблицы пустые) ---
    # vehicles
    cursor.execute("SELECT COUNT(*) FROM vehicles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO vehicles (
                contract_number, date, acceptance_date, work_order_date, completion_date,
                type, customer, number, brand, refrigerator_brand, year, mileage, phone,
                address, preliminary_inspection, work_total, work_total_with_coeff, parts_total,
                equipment_delivered, recommendations, executor_position, executor_name,
                customer_position, customer_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "20250407", "01.04.2025", "02.04.2025", "03.04.2025", "04.04.2025",
            "Легковые", "ООО Тест", "А123БВ", "Toyota", "Thermo King", "2020",
            "150000", "+7 (123) 456-78-90", "г. Новокузнецк, ул. Тестовая, 1",
            "Неисправность двигателя", "5000.00", "5500.00", "2000.00",
            "Иванов И.И.", "Проверить систему охлаждения",
            "Мастер", "Петров П.П.", "Клиент", "Сидоров С.С."
        ))
        vehicle_id = cursor.lastrowid

        test_materials_and_works = [
            (vehicle_id, "Масло моторное", "", "л", "5", "1000", "Проверка 1", "Проверка 2"),
            (vehicle_id, "Фильтр масляный", "", "шт.", "1", "500", "Проверка 3", "Проверка 4"),
            (vehicle_id, "", "Замена масла", "усл.", "1", "1500", "Проверка 5", "Проверка 6"),
            (vehicle_id, "", "Диагностика двигателя", "усл.", "1", "2000", "Проверка 7", "Проверка 8"),
        ]
        cursor.executemany("""
            INSERT INTO materials_and_works (vehicle_id, material, work, unit, quantity, price_per_unit, equipment_param1, equipment_param2)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, test_materials_and_works)

    # print_history
    cursor.execute("SELECT COUNT(*) FROM print_history")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO print_history (vehicle_id, print_date, customer, brand, number, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            1, datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "ООО Тест", "Toyota", "А123БВ", "C:/path/to/test_report.pdf"
        ))

    # works
    cursor.execute("SELECT COUNT(*) FROM works")
    if cursor.fetchone()[0] == 0:
        test_works = [
            ("Проверка азотом системы кондиционирования на герметичность (1 контур)", "шт.", "500"),
            ("Проверка азотом системы кондиционирования на герметичность (2 контура)", "шт.", "1000"),
            ("Поиск микроутечки", "шт.", "250"),
            ("Вакуумирование системы", "шт.", "500"),
            ("Замена подшипника шкива (на снятом компрессоре)", "шт.", "500"),
            ("Замена подшипника натяжного ролика", "шт.", "500"),
            ("Замена сальника компрессора", "шт.", "2000"),
            ("Замена электромагнитного клапана на снятом компрессоре)", "шт.", "1500"),
            ("Замена электромагнитного клапана по месту", "шт.", "2000"),
            ("Комплексный ремонт компрессора", "шт.", "5600"),
            ("Заправка системы маслом", "шт.", "500"),
            ("Замена прокладки (2 шт)", "шт.", "300"),
            ("Замена проводов, клемм, реле", "шт.", "300"),
            ("Замена предохранителя", "шт.", "300"),
            ("Замена датчика давления", "шт.", "1100"),
            ("Замена вентилятора конденсатора", "шт.", "1100"),
            ("Реле 4-х (5) контактное Denso, Toyota (12V)", "шт.", "400"),
            ("Поиск неисправности", "шт.", "1000"),
            ("Диагностика", "шт.", "500"),
        ]
        cursor.executemany(
            "INSERT INTO works (name, unit, price) VALUES (?, ?, ?)", test_works
        )

    # materials
    cursor.execute("SELECT COUNT(*) FROM materials")
    if cursor.fetchone()[0] == 0:
        test_materials = [
            ("Катушка электромагнитной муфты TM", "шт.", "0"),
            ("Катушка электромагнитной муфты Denso", "шт.", "0"),
            ("Шкив с прижимной пластиной SD", "шт.", "0"),
            ("Шкив с прижимной пластиной Denso", "шт.", "0"),
            ("Осушитель кондиционера (в конденсатор)", "шт.", "0"),
            ("Фильтр-картридж для промывки", "шт.", "0"),
        ]
        cursor.executemany(
            "INSERT INTO materials (name, unit, price) VALUES (?, ?, ?)", test_materials
        )

    # --- В конце обновляем версию схемы ---
    if current_version < latest_version:
        cursor.execute("""
            INSERT INTO schema_version (version, applied_at)
            VALUES (?, ?)
        """, (latest_version, datetime.now().strftime("%d.%m.%Y %H:%M:%S")))

# =========================
# --- VEHICLES CRUD ---
# =========================
@with_connection
def save_vehicle(conn, vehicle_data, works, materials):
    """
    Сохраняет или обновляет ТС и связанные работы/материалы по id.
    - vehicle_data: dict с полями ТС (как в add_vehicle/update_vehicle)
    - works: список словарей работ (каждая — поля: work, unit, quantity, price_per_unit, equipment_param1, equipment_param2)
    - materials: список словарей материалов (каждая — поля: material, unit, quantity, price_per_unit)
    Возвращает id ТС.
    """
    cursor = conn.cursor()

    # 1. Проверка уникальности contract_number (договора-заявки)
    contract_number = vehicle_data.get("contract_number")
    vehicle_id = vehicle_data.get("id")
    cursor.execute("SELECT id FROM vehicles WHERE contract_number = ?", (contract_number,))
    row = cursor.fetchone()
    if row:
        existing_id = row[0]
        # Если редактируем — допускаем совпадение только с самим собой
        if not vehicle_id or (vehicle_id and existing_id != vehicle_id):
            raise Exception(f"Транспорт с номером договора-заявки {contract_number} уже существует!")

    # 2. Добавление или обновление ТС
    if vehicle_id:  # обновление
        update_vehicle(vehicle_data)
        saved_id = vehicle_id
    else:           # добавление
        saved_id = add_vehicle(vehicle_data)
        vehicle_data["id"] = saved_id

    # 3. Удалить старые работы/материалы для этого ТС
    delete_materials_and_works(saved_id)

    # 4. Сохранить новые работы
    for w in works:
        add_material_and_work(
            saved_id,
            "",
            w.get("work", ""),
            w.get("unit", ""),
            w.get("quantity", ""),
            w.get("price_per_unit", ""),
            w.get("equipment_param1", ""),
            w.get("equipment_param2", "")
        )

    # 5. Сохранить новые материалы
    for m in materials:
        add_material_and_work(
            saved_id,
            m.get("material", ""),
            "",
            m.get("unit", ""),
            m.get("quantity", ""),
            m.get("price_per_unit", ""),
            "", ""
        )
    return saved_id

@with_connection
def add_vehicle(conn, vehicle_data):
    """Добавление нового ТС в базу данных"""
    cursor = conn.cursor()
    data_to_insert = (
        vehicle_data.get("contract_number", ""),
        vehicle_data.get("date", ""),
        vehicle_data.get("acceptance_date", ""),
        vehicle_data.get("work_order_date", ""),
        vehicle_data.get("completion_date", ""),
        vehicle_data.get("type", ""),
        vehicle_data.get("customer", ""),
        vehicle_data.get("number", ""),
        vehicle_data.get("brand", ""),
        vehicle_data.get("refrigerator_brand", ""),
        vehicle_data.get("year", ""),
        vehicle_data.get("mileage", ""),
        vehicle_data.get("phone", ""),
        vehicle_data.get("address", ""),
        vehicle_data.get("preliminary_inspection", ""),
        vehicle_data.get("work_total", ""),
        vehicle_data.get("work_total_with_coeff", ""),
        vehicle_data.get("parts_total", ""),
        vehicle_data.get("equipment_delivered", ""),
        vehicle_data.get("recommendations", ""),
        vehicle_data.get("executor_position", ""),
        vehicle_data.get("executor_name", ""),
        vehicle_data.get("customer_position", ""),
        vehicle_data.get("customer_name", ""),
    )
    cursor.execute(
        """
        INSERT INTO vehicles (
            contract_number, date, acceptance_date, work_order_date, completion_date,
            type, customer, number, brand, refrigerator_brand, year, mileage, phone,
            address, preliminary_inspection, work_total, work_total_with_coeff, parts_total,
            equipment_delivered, recommendations, executor_position, executor_name,
            customer_position, customer_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data_to_insert,
    )
    return cursor.lastrowid

@with_connection
def get_all_vehicles(conn):
    """Получение всех ТС"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles")
    rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "contract_number": row[1],
            "date": row[2],
            "acceptance_date": row[3],
            "work_order_date": row[4],
            "completion_date": row[5],
            "type": row[6],
            "customer": row[7],
            "number": row[8],
            "brand": row[9],
            "refrigerator_brand": row[10],
            "year": row[11],
            "mileage": row[12],
            "phone": row[13],
            "address": row[14],
            "preliminary_inspection": row[15],
            "work_total": row[16],
            "work_total_with_coeff": row[17],
            "parts_total": row[18],
            "equipment_delivered": row[19],
            "recommendations": row[20],
            "executor_position": row[21],
            "executor_name": row[22],
            "customer_position": row[23],
            "customer_name": row[24],
        }
        for row in rows
    ]

@with_connection
def get_vehicle_by_id(conn, vehicle_id):
    """Получение данных ТС по ID"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "contract_number": row[1],
        "date": row[2],
        "acceptance_date": row[3],
        "work_order_date": row[4],
        "completion_date": row[5],
        "type": row[6],
        "customer": row[7],
        "number": row[8],
        "brand": row[9],
        "refrigerator_brand": row[10],
        "year": row[11],
        "mileage": row[12],
        "phone": row[13],
        "address": row[14],
        "preliminary_inspection": row[15],
        "work_total": row[16],
        "work_total_with_coeff": row[17],
        "parts_total": row[18],
        "equipment_delivered": row[19],
        "recommendations": row[20],
        "executor_position": row[21],
        "executor_name": row[22],
        "customer_position": row[23],
        "customer_name": row[24],
    }

@with_connection
def update_vehicle(conn, vehicle_data):
    """Обновление данных о ТС"""
    cursor = conn.cursor()
    data_to_update = (
        vehicle_data.get("contract_number", ""),
        vehicle_data.get("date", ""),
        vehicle_data.get("acceptance_date", ""),
        vehicle_data.get("work_order_date", ""),
        vehicle_data.get("completion_date", ""),
        vehicle_data.get("type", ""),
        vehicle_data.get("customer", ""),
        vehicle_data.get("number", ""),
        vehicle_data.get("brand", ""),
        vehicle_data.get("refrigerator_brand", ""),
        vehicle_data.get("year", ""),
        vehicle_data.get("mileage", ""),
        vehicle_data.get("phone", ""),
        vehicle_data.get("address", ""),
        vehicle_data.get("preliminary_inspection", ""),
        vehicle_data.get("work_total", ""),
        vehicle_data.get("work_total_with_coeff", ""),
        vehicle_data.get("parts_total", ""),
        vehicle_data.get("equipment_delivered", ""),
        vehicle_data.get("recommendations", ""),
        vehicle_data.get("executor_position", ""),
        vehicle_data.get("executor_name", ""),
        vehicle_data.get("customer_position", ""),
        vehicle_data.get("customer_name", ""),
        vehicle_data["id"],
    )
    cursor.execute(
        """
        UPDATE vehicles SET
            contract_number = ?, date = ?, acceptance_date = ?, work_order_date = ?,
            completion_date = ?, type = ?, customer = ?, number = ?, brand = ?,
            refrigerator_brand = ?, year = ?, mileage = ?, phone = ?,
            address = ?, preliminary_inspection = ?, work_total = ?, work_total_with_coeff = ?,
            parts_total = ?, equipment_delivered = ?, recommendations = ?,
            executor_position = ?, executor_name = ?, customer_position = ?, customer_name = ?
        WHERE id = ?
        """,
        data_to_update,
    )

@with_connection
def delete_vehicle(conn, vehicle_id):
    """Удаление ТС из базы данных (удаляет также связанные записи)"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    cursor.execute("DELETE FROM print_history WHERE vehicle_id = ?", (vehicle_id,))
    cursor.execute("DELETE FROM materials_and_works WHERE vehicle_id = ?", (vehicle_id,))

# =========================
# --- WORKS CRUD ---
# =========================
@with_connection
def add_work(conn, name, unit="шт.", price="0"):
    """Добавление новой работы в общий список с ID, начиная с 30000"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM works")
    max_id = cursor.fetchone()[0]
    if max_id is None or max_id < WORK_ID_MIN:
        new_id = WORK_ID_MIN
    else:
        new_id = max_id + 1
    cursor.execute(
        "INSERT INTO works (id, name, unit, price) VALUES (?, ?, ?, ?)",
        (new_id, name, unit, price),
    )

@with_connection
def get_works(conn):
    """Получение всех работ из общего списка"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, unit, price FROM works")
    rows = cursor.fetchall()
    return [
        {"id": row[0], "name": row[1], "unit": row[2], "price": row[3]}
        for row in rows
    ]

@with_connection
def delete_work(conn, work_id):
    """Удаление работы из общего списка"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))

# =========================
# --- MATERIALS CRUD ---
# =========================
@with_connection
def add_material(conn, name, unit="шт.", price="0"):
    """Добавление нового материала в общий список с ID, начиная с 20000"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM materials")
    max_id = cursor.fetchone()[0]
    if max_id is None or max_id < MATERIAL_ID_MIN:
        new_id = MATERIAL_ID_MIN
    else:
        new_id = max_id + 1
    cursor.execute(
        "INSERT INTO materials (id, name, unit, price) VALUES (?, ?, ?, ?)",
        (new_id, name, unit, price),
    )

@with_connection
def get_materials(conn):
    """Получение всех материалов из общего списка"""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, unit, price FROM materials")
    rows = cursor.fetchall()
    return [
        {"id": row[0], "name": row[1], "unit": row[2], "price": row[3]}
        for row in rows
    ]

@with_connection
def delete_material(conn, material_id):
    """Удаление материала из общего списка"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))

# =========================
# --- MATERIALS_AND_WORKS CRUD ---
# =========================
@with_connection
def add_material_and_work(
    conn,
    vehicle_id,
    material,
    work,
    unit="шт.",
    quantity="1",
    price_per_unit="0",
    equipment_param1="",
    equipment_param2="",
):
    """Добавление материала или работы, связанных с ТС (ID в диапазоне 10000-19999)"""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM materials_and_works")
    max_id = cursor.fetchone()[0]
    if max_id is None or max_id < MATERIALS_AND_WORKS_ID_MIN:
        new_id = MATERIALS_AND_WORKS_ID_MIN
    elif max_id >= MATERIALS_AND_WORKS_ID_MAX:
        raise Exception("Превышен лимит ID для materials_and_works!")
    else:
        new_id = max_id + 1
    cursor.execute(
        "INSERT INTO materials_and_works (id, vehicle_id, material, work, unit, quantity, price_per_unit, equipment_param1, equipment_param2) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            new_id,
            vehicle_id,
            material,
            work,
            unit,
            quantity,
            price_per_unit,
            equipment_param1,
            equipment_param2,
        ),
    )

@with_connection
def get_materials_and_works(conn, vehicle_id):
    """Получение материалов и работ для ТС"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, material, work, unit, quantity, price_per_unit, equipment_param1, equipment_param2 FROM materials_and_works WHERE vehicle_id = ?",
        (vehicle_id,),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "material": row[1],
            "work": row[2],
            "unit": row[3],
            "quantity": row[4],
            "price_per_unit": row[5],
            "equipment_param1": row[6],
            "equipment_param2": row[7],
        }
        for row in rows
    ]

@with_connection
def delete_materials_and_works(conn, vehicle_id):
    """Удаление всех работ и материалов для указанного vehicle_id"""
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM materials_and_works WHERE vehicle_id = ?", (vehicle_id,)
    )

@with_connection
def delete_material_and_work(conn, entry_id):
    """Удаление материала или работы, связанных с ТС"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials_and_works WHERE id = ?", (entry_id,))

# =========================
# --- PRINT_HISTORY CRUD ---
# =========================
@with_connection
def add_print_history(conn, vehicle_data, pdf_path):
    """Добавление записи в историю печати"""
    cursor = conn.cursor()
    current_date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO print_history (vehicle_id, print_date, customer, brand, number, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            vehicle_data["id"],
            current_date,
            vehicle_data.get("customer", ""),
            vehicle_data.get("brand", ""),
            vehicle_data.get("number", ""),
            pdf_path,
        ),
    )

@with_connection
def get_print_history(conn):
    """Получение истории печати с данными о ТС"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ph.id, ph.vehicle_id, ph.print_date, ph.customer, ph.brand, ph.number, ph.pdf_path,
               v.contract_number, v.type
        FROM print_history ph
        LEFT JOIN vehicles v ON ph.vehicle_id = v.id
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "id": row[0],
            "vehicle_id": row[1],
            "date": row[2],
            "customer": row[3],
            "brand": row[4],
            "number": row[5],
            "pdf_path": row[6],
            "contract_number": row[7],
            "type": row[8],
        }
        for row in rows
    ]

@with_connection
def delete_print_history_entry(conn, entry_id):
    """Удаление записи из истории печати"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM print_history WHERE id = ?", (entry_id,))

# --- Для ручного запуска инициализации ---
if __name__ == "__main__":
    init_db()