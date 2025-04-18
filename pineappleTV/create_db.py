import sqlite3
import os

try:
    # Klasör yoksa oluştur
    os.makedirs('db', exist_ok=True)

    # Bağlantı oluştur
    conn = sqlite3.connect('db/users.db')

    # SQL sorgusu: Kullanıcı tablosu
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

    print("✅ Veritabanı ve tablo başarıyla oluşturuldu.")

except sqlite3.Error as e:
    print(f"Veritabanı hatası: {e}")
except Exception as e:
    print(f"Beklenmeyen bir hata oluştu: {e}")
