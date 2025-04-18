import sqlite3
from werkzeug.security import generate_password_hash
import os

def create_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'db', 'user.db')

    # Veritabanı bağlantısını aç
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Kullanıcılar tablosunu oluştur
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    # Örnek kullanıcı ekleyebilirsiniz (isteğe bağlı)
    hashed_password = generate_password_hash("yourpassword")
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('example_user', hashed_password))

    # Değişiklikleri kaydet ve bağlantıyı kapat
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db()
