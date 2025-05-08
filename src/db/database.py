import sqlite3
import os
import sys
from datetime import datetime


def get_persistent_db_path():
    """Получение пути для сохранения базы данных в постоянной папке."""
    user_data_dir = os.path.join(os.getenv("APPDATA"), "Tandem")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    return os.path.join(user_data_dir, "database.db")


def resource_path(relative_path):
    """Получение абсолютного пути к ресурсу, работает как в разработке, так и в EXE."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", relative_path
        )


# Путь к базе данных
DB_PATH = get_persistent_db_path()

# Проверяем, существует ли база данных, если нет — копируем из ресурсов
if not os.path.exists(DB_PATH):
    default_db_path = resource_path("data/database.db")
    if os.path.exists(default_db_path):
        with open(default_db_path, "rb") as src, open(DB_PATH, "wb") as dst:
            dst.write(src.read())


def init_db():
    """Инициализация базы данных и создание таблиц с устойчивой миграцией"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаём таблицу для хранения версии схемы
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
    except sqlite3.Error as e:
        conn.rollback()
        raise

    # Проверяем текущую версию схемы
    cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    current_version = row[0] if row else 0
    latest_version = 2  # Обновляем версию схемы из-за новых полей

    # Если версия схемы уже актуальна, пропускаем миграцию
    if current_version >= latest_version:
        conn.close()
        return

    # --- Миграция таблицы vehicles ---
    cursor.execute("PRAGMA table_info(vehicles)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = [
        "id",
        "contract_number",
        "date",
        "acceptance_date",
        "work_order_date",
        "completion_date",
        "type",
        "customer",
        "number",
        "brand",
        "refrigerator_brand",
        "year",
        "mileage",
        "phone",
        "address",
        "preliminary_inspection",
        "work_total",
        "work_total_with_coeff",
        "parts_total",
        "equipment_delivered",
        "recommendations",
        "executor_position",
        "executor_name",
        "customer_position",
        "customer_name",
    ]

    if columns and columns != expected_columns:
        try:
            cursor.execute("DROP TABLE IF EXISTS vehicles_temp")

            cursor.execute(
                """
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
                """
            )

            # Копируем данные (только для существующих столбцов)
            existing_columns = [col for col in columns if col in expected_columns]
            columns_str = ", ".join(existing_columns)
            cursor.execute(
                f"""
                INSERT INTO vehicles_temp ({columns_str})
                SELECT {columns_str}
                FROM vehicles
                """
            )

            cursor.execute("DROP TABLE vehicles")

            cursor.execute("ALTER TABLE vehicles_temp RENAME TO vehicles")
        except sqlite3.Error as e:
            conn.rollback()
            raise

    # Создаём таблицу vehicles, если она ещё не существует
    cursor.execute(
        """
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
        """
    )

    cursor.execute("PRAGMA table_info(print_history)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = [
        "id",
        "vehicle_id",
        "print_date",
        "customer",
        "brand",
        "number",
        "pdf_path",
    ]

    if columns and columns != expected_columns:
        try:
            cursor.execute("DROP TABLE IF EXISTS print_history_temp")

            cursor.execute(
                """
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
                """
            )

            cursor.execute(
                """
                INSERT INTO print_history_temp (
                    id, vehicle_id, print_date, customer, brand, number, pdf_path
                )
                SELECT id, vehicle_id, print_date, customer, brand, number, pdf_path
                FROM print_history
                """
            )

            cursor.execute("DROP TABLE print_history")

            cursor.execute("ALTER TABLE print_history_temp RENAME TO print_history")
        except sqlite3.Error as e:
            conn.rollback()
            raise
    else:
        cursor.execute(
            """
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
            """
        )

    cursor.execute("PRAGMA table_info(print_history)")
    columns = [column[1] for column in cursor.fetchall()]
    if "print_date" not in columns:
        try:
            cursor.execute("ALTER TABLE print_history ADD COLUMN print_date TEXT")
        except sqlite3.Error as e:
            conn.rollback()
            raise

    # --- Миграция таблицы materials_and_works ---
    cursor.execute("PRAGMA table_info(materials_and_works)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = [
        "id",
        "vehicle_id",
        "material",
        "work",
        "unit",
        "quantity",
        "price_per_unit",
        "equipment_param1",
        "equipment_param2",
    ]

    if columns and columns != expected_columns:
        try:
            cursor.execute("DROP TABLE IF EXISTS materials_and_works_temp")

            cursor.execute(
                """
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
                """
            )

            # Копируем данные (только для существующих столбцов)
            existing_columns = [col for col in columns if col in expected_columns]
            columns_str = ", ".join(existing_columns)
            cursor.execute(
                f"""
                INSERT INTO materials_and_works_temp ({columns_str})
                SELECT {columns_str}
                FROM materials_and_works
                """
            )

            cursor.execute("DROP TABLE materials_and_works")

            cursor.execute(
                "ALTER TABLE materials_and_works_temp RENAME TO materials_and_works"
            )
        except sqlite3.Error as e:
            conn.rollback()
            raise
    else:
        cursor.execute(
            """
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
            """
        )

    # --- Миграция таблицы works ---
    cursor.execute("PRAGMA table_info(works)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = ["id", "name", "unit", "price"]

    if columns and columns != expected_columns:
        try:
            cursor.execute("DROP TABLE IF EXISTS works_temp")

            cursor.execute(
                """
                CREATE TABLE works_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    unit TEXT,
                    price TEXT
                )
                """
            )

            cursor.execute(
                """
                INSERT INTO works_temp (id, name, unit, price)
                SELECT id, name, unit, price
                FROM works
                """
            )

            cursor.execute("DROP TABLE works")

            cursor.execute("ALTER TABLE works_temp RENAME TO works")
        except sqlite3.Error as e:
            conn.rollback()
            raise
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unit TEXT,
                price TEXT
            )
            """
        )

    # --- Миграция таблицы materials ---
    cursor.execute("PRAGMA table_info(materials)")
    columns = [column[1] for column in cursor.fetchall()]
    expected_columns = ["id", "name", "unit", "price"]

    if columns and columns != expected_columns:
        try:
            cursor.execute("DROP TABLE IF EXISTS materials_temp")

            cursor.execute(
                """
                CREATE TABLE materials_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    unit TEXT,
                    price TEXT
                )
                """
            )

            cursor.execute(
                """
                INSERT INTO materials_temp (id, name, unit, price)
                SELECT id, name, unit, price
                FROM materials
                """
            )

            cursor.execute("DROP TABLE materials")

            cursor.execute("ALTER TABLE materials_temp RENAME TO materials")
        except sqlite3.Error as e:
            conn.rollback()
            raise
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                unit TEXT,
                price TEXT
            )
            """
        )

    # Добавляем тестовые данные, если таблицы пустые
    try:
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
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
                (
                    "20250407",
                    "01.04.2025",
                    "02.04.2025",
                    "03.04.2025",
                    "04.04.2025",
                    "Легковые",
                    "ООО Тест",
                    "А123БВ",
                    "Toyota",
                    "Thermo King",
                    "2020",
                    "150000",
                    "+7 (123) 456-78-90",
                    "г. Новокузнецк, ул. Тестовая, 1",
                    "Неисправность двигателя",
                    "5000.00",
                    "5500.00",
                    "2000.00",
                    "Иванов И.И.",
                    "Проверить систему охлаждения",
                    "Мастер",
                    "Петров П.П.",
                    "Клиент",
                    "Сидоров С.С.",
                ),
            )
            vehicle_id = cursor.lastrowid

            test_materials_and_works = [
                (
                    vehicle_id,
                    "Масло моторное",
                    "",
                    "л",
                    "5",
                    "1000",
                    "Проверка 1",
                    "Проверка 2",
                ),
                (
                    vehicle_id,
                    "Фильтр масляный",
                    "",
                    "шт.",
                    "1",
                    "500",
                    "Проверка 3",
                    "Проверка 4",
                ),
                (
                    vehicle_id,
                    "",
                    "Замена масла",
                    "усл.",
                    "1",
                    "1500",
                    "Проверка 5",
                    "Проверка 6",
                ),
                (
                    vehicle_id,
                    "",
                    "Диагностика двигателя",
                    "усл.",
                    "1",
                    "2000",
                    "Проверка 7",
                    "Проверка 8",
                ),
            ]
            cursor.executemany(
                "INSERT INTO materials_and_works (vehicle_id, material, work, unit, quantity, price_per_unit, equipment_param1, equipment_param2) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                test_materials_and_works,
            )
    except sqlite3.Error as e:
        conn.rollback()
        raise

    try:
        cursor.execute("SELECT COUNT(*) FROM print_history")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO print_history (vehicle_id, print_date, customer, brand, number, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                    "ООО Тест",
                    "Toyota",
                    "А123БВ",
                    "C:/path/to/test_report.pdf",
                ),
            )
    except sqlite3.Error as e:
        conn.rollback()
        raise

    try:
        cursor.execute("SELECT COUNT(*) FROM works")
        if cursor.fetchone()[0] == 0:
            test_works = [
                (
                    "Проверка азотом системы кондиционирования на герметичность (1 контур)",
                    "шт.",
                    "500",
                ),
                (
                    "Проверка азотом системы кондиционирования на герметичность (2 контура)",
                    "шт.",
                    "1000",
                ),
                ("Поиск микроутечки", "шт.", "250"),
                ("Вакуумирование системы", "шт.", "500"),
                ("Замена подшипника шкива (на снятом компрессоре)", "шт.", "500"),
                ("Замена подшипника натяжного ролика", "шт.", "500"),
                ("Замена сальника компрессора", "шт.", "2000"),
                (
                    "Замена электромагнитного клапана на снятом компрессоре)",
                    "шт.",
                    "1500",
                ),
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
    except sqlite3.Error as e:
        conn.rollback()
        raise

    try:
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
                "INSERT INTO materials (name, unit, price) VALUES (?, ?, ?)",
                test_materials,
            )
    except sqlite3.Error as e:
        conn.rollback()
        raise

    # Обновляем версию схемы
    if current_version < latest_version:
        try:
            cursor.execute(
                """
                INSERT INTO schema_version (version, applied_at)
                VALUES (?, ?)
                """,
                (latest_version, datetime.now().strftime("%d.%m.%Y %H:%M:%S")),
            )
        except sqlite3.Error as e:
            conn.rollback()
            raise

    conn.commit()
    conn.close()


def add_vehicle(vehicle_data):
    """Добавление нового ТС в базу данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
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

        vehicle_id = cursor.lastrowid
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))

        conn.commit()
        return vehicle_id
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_vehicles():
    """Получение всех ТС из базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM vehicles")
        rows = cursor.fetchall()

        vehicles = []
        for row in rows:
            vehicle = {
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
            vehicles.append(vehicle)
        return vehicles
    except sqlite3.Error as e:
        raise
    finally:
        conn.close()


def get_vehicle_by_id(vehicle_id):
    """Получение данных ТС по ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        vehicle = {
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
        return vehicle
    except sqlite3.Error as e:
        raise
    finally:
        conn.close()


def delete_vehicle(vehicle_id):
    """Удаление ТС из базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        cursor.execute("DELETE FROM print_history WHERE vehicle_id = ?", (vehicle_id,))
        cursor.execute(
            "DELETE FROM materials_and_works WHERE vehicle_id = ?", (vehicle_id,)
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_vehicle(vehicle_data):
    """Обновление данных о ТС"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
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

        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_data["id"],))

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_print_history(vehicle_data, pdf_path):
    """Добавление записи в историю печати"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
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
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_print_history():
    """Получение истории печати с данными о ТС"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT ph.id, ph.vehicle_id, ph.print_date, ph.customer, ph.brand, ph.number, ph.pdf_path,
                   v.contract_number, v.type
            FROM print_history ph
            LEFT JOIN vehicles v ON ph.vehicle_id = v.id
            """
        )
        rows = cursor.fetchall()

        history = []
        for row in rows:
            record = {
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
            history.append(record)
        return history
    except sqlite3.Error as e:
        raise
    finally:
        conn.close()


def delete_materials_and_works(vehicle_id):
    """Удаление всех работ и материалов для указанного vehicle_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM materials_and_works WHERE vehicle_id = ?", (vehicle_id,)
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_print_history_entry(entry_id):
    """Удаление записи из истории печати"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM print_history WHERE id = ?", (entry_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_material_and_work(
    vehicle_id,
    material,
    work,
    unit="шт.",
    quantity="1",
    price_per_unit="0",
    equipment_param1="",
    equipment_param2="",
):
    """Добавление материала или работы, связанных с ТС"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO materials_and_works (vehicle_id, material, work, unit, quantity, price_per_unit, equipment_param1, equipment_param2) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
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
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_materials_and_works(vehicle_id):
    """Получение материалов и работ для ТС"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
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
    except sqlite3.Error as e:
        raise
    finally:
        conn.close()


def delete_material_and_work(entry_id):
    """Удаление материала или работы, связанных с ТС"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM materials_and_works WHERE id = ?", (entry_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_work(name, unit="шт.", price="0"):
    """Добавление новой работы в общий список с ID, начиная с 30000"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Получаем максимальный ID в таблице works
        cursor.execute("SELECT MAX(id) FROM works")
        max_id = cursor.fetchone()[0]
        if max_id is None or max_id < 30000:
            new_id = 30000
        else:
            new_id = max_id + 1

        cursor.execute(
            "INSERT INTO works (id, name, unit, price) VALUES (?, ?, ?, ?)",
            (new_id, name, unit, price),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_works():
    """Получение всех работ из общего списка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, unit, price FROM works")
        rows = cursor.fetchall()
        return [
            {"id": row[0], "name": row[1], "unit": row[2], "price": row[3]}
            for row in rows
        ]
    except sqlite3.Error as e:
        raise
    finally:
        conn.close()


def delete_work(work_id):
    """Удаление работы из общего списка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_material(name, unit="шт.", price="0"):
    """Добавление нового материала в общий список с ID, начиная с 20000"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Получаем максимальный ID в таблице materials
        cursor.execute("SELECT MAX(id) FROM materials")
        max_id = cursor.fetchone()[0]
        if max_id is None or max_id < 20000:
            new_id = 20000
        else:
            new_id = max_id + 1

        cursor.execute(
            "INSERT INTO materials (id, name, unit, price) VALUES (?, ?, ?, ?)",
            (new_id, name, unit, price),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_materials():
    """Получение всех материалов из общего списка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, unit, price FROM materials")
        rows = cursor.fetchall()
        return [
            {"id": row[0], "name": row[1], "unit": row[2], "price": row[3]}
            for row in rows
        ]
    except sqlite3.Error as e:
        raise
    finally:
        conn.close()


def delete_material(material_id):
    """Удаление материала из общего списка"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
