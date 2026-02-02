import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS siswa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        kelas TEXT,
        qr_code TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS presensi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT,
        mapel TEXT,
        kelas TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS detail_presensi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        presensi_id INTEGER,
        siswa_id INTEGER,
        status TEXT,
        metode TEXT,
        waktu TEXT
    )
    """)

    conn.commit()
    conn.close()
