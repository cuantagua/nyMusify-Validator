import sqlite3
import random
import string
import csv
import os

DB_NAME = "bot_store.db"  # <- Usa una sola base para todo

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla de archivos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            telegram_file_id TEXT UNIQUE,
            tipo TEXT
        )
    """)

    # Tabla de cupones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla para asignar archivos a cupones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coupon_files (
            coupon_code TEXT,
            file_id INTEGER,
            FOREIGN KEY(coupon_code) REFERENCES coupons(code),
            FOREIGN KEY(file_id) REFERENCES files(id),
            UNIQUE(coupon_code, file_id)
        )
    """)

    # Redenciones (quién usó qué cupón)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redemptions (
            user_id INTEGER,
            coupon_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Archivos redimidos por usuario (más específica que redemptions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_files (
            user_id INTEGER,
            file_id INTEGER,
            redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
    """)

    conn.commit()
    conn.close()


# Otras funciones:

def add_file(name, telegram_file_id, tipo):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()

    # Verificar si ya existe ese telegram_file_id
    cursor.execute("SELECT id FROM files WHERE telegram_file_id = ?", (telegram_file_id,))
    exists = cursor.fetchone()

    if exists:
        conn.close()
        raise ValueError("El archivo ya existe en la base de datos.")

    cursor.execute("INSERT INTO files (name, telegram_file_id, type) VALUES (?, ?, ?)", (name, telegram_file_id, tipo))
    conn.commit()
    conn.close()

def add_coupon(code: str) -> bool:
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO coupons (code) VALUES (?)", (code,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def validate_coupon(code: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT file_id FROM coupon_files WHERE coupon_code = ?", (code,))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        return [row[0] for row in rows]
    else:
        return None

def coupon_used_by_user(user_id, code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM redemptions WHERE user_id = ? AND coupon_code = ?", (user_id, code))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def register_redemption(user_id, code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO redemptions (user_id, coupon_code) VALUES (?, ?)", (user_id, code))

    # Registrar archivos desbloqueados
    cursor.execute("SELECT file_id FROM coupon_files WHERE coupon_code = ?", (code,))
    file_ids = cursor.fetchall()
    for (file_id,) in file_ids:
        cursor.execute("INSERT INTO user_files (user_id, file_id) VALUES (?, ?)", (user_id, file_id))

    conn.commit()
    conn.close()

def get_file_by_id(file_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, telegram_file_id FROM files WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)

def associate_file_with_coupon(coupon_code, file_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO coupon_files (coupon_code, file_id) VALUES (?, ?)",
        (coupon_code, file_id)
    )
    conn.commit()
    conn.close()

def get_redeemed_files_by_user(user_id, order_by="recent", limit=5, offset=0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    order_clause = "uf.redeemed_at DESC"
    if order_by == "name":
        order_clause = "f.name ASC"

    cursor.execute(f"""
        SELECT f.name, f.telegram_file_id, f.tipo, uf.redeemed_at
        FROM user_files uf
        JOIN files f ON uf.file_id = f.id
        WHERE uf.user_id = ?
        GROUP BY f.id
        ORDER BY {order_clause}
        LIMIT ? OFFSET ?
    """, (user_id, limit, offset))

    files = cursor.fetchall()

    # Para contar total
    cursor.execute("""
        SELECT COUNT(DISTINCT f.id)
        FROM user_files uf
        JOIN files f ON uf.file_id = f.id
        WHERE uf.user_id = ?
    """, (user_id,))
    total = cursor.fetchone()[0]

    conn.close()
    return files, total

def generate_code():
    return f"{''.join(random.choices(string.ascii_uppercase + string.digits, k=3))}-" \
           f"{''.join(random.choices(string.ascii_uppercase + string.digits, k=3))}"

def generate_coupons_csv(file_name, cantidad):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Obtener ID del archivo
    cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
    file_id = cursor.fetchone()[0]

    codes = []
    for _ in range(cantidad):
        code = generate_code()
        cursor.execute("INSERT OR IGNORE INTO coupons (code) VALUES (?)", (code,))
        conn.commit()
        cursor.execute("INSERT INTO coupon_files (coupon_code, file_id) VALUES (?, ?)", (code, file_id))
        conn.commit()
        codes.append(code)

    # Crear CSV temporal
    csv_path = f"/tmp/coupons_{file_name.replace(' ', '_')}.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Código'])
        for c in codes:
            writer.writerow([c])

    conn.close()
    return csv_path

def migrate_add_type_to_files():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE files ADD COLUMN type TEXT DEFAULT 'musica'")
    conn.commit()
    conn.close()
