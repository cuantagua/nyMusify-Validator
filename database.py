import sqlite3

def init_db():
    conn = sqlite3.connect('bot_store.db')
    c = conn.cursor()

    # Tabla de archivos
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL
        )
    ''')

    # Tabla de cupones
    c.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            file_ids TEXT NOT NULL
        )
    ''')

    # Tabla de redenciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS redemptions (
            user_id INTEGER,
            coupon_code TEXT,
            PRIMARY KEY (user_id, coupon_code)
        )
    ''')

    conn.commit()
    conn.close()
