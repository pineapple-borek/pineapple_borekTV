import sqlite3
import os

# Veritabanı dosyasının yolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'db', 'user.db')  # Veritabanınızın yolu

# Veritabanına bağlanıyoruz
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 'favorites' tablosunun var olup olmadığını kontrol edip oluşturuyoruz
cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        video_name TEXT
    )
''')

conn.commit()
conn.close()

print("Favorites tablosu başarıyla oluşturuldu veya zaten var.")

# Veritabanı dosyasının yolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'db', 'user.db')  # Veritabanınızın yolu

# Veritabanına bağlanıyoruz
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# subscription_end_date sütununun var olup olmadığını kontrol ediyoruz
cursor.execute('PRAGMA table_info(users)')
columns = [column[1] for column in cursor.fetchall()]

if 'subscription_end_date' not in columns:
    cursor.execute('''
        ALTER TABLE users ADD COLUMN subscription_end_date TEXT;
    ''')
    conn.commit()
    print("subscription_end_date sütunu başarıyla eklendi.")
else:
    print("subscription_end_date sütunu zaten mevcut.")

conn.close()
