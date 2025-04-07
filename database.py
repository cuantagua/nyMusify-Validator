def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()

    # Tabla de archivos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        telegram_file_id TEXT NOT NULL UNIQUE
    )
    """)

    # Tabla de cupones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        code TEXT PRIMARY KEY
    )
    """)

    # Asociación entre cupones y archivos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupon_files (
        coupon_code TEXT,
        file_id INTEGER,
        FOREIGN KEY (coupon_code) REFERENCES coupons(code),
        FOREIGN KEY (file_id) REFERENCES files(id)
    )
    """)

    # Redenciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS redemptions (
        user_id INTEGER,
        coupon_code TEXT,
        FOREIGN KEY (coupon_code) REFERENCES coupons(code)
    )
    """)

    conn.commit()
    conn.close()
