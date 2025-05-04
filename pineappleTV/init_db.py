import sqlite3
from werkzeug.security import generate_password_hash
import os

class DatabaseInitializer:
    #database dizininin adresini alıyor ve yoksa .db dosyası açıyor. (yapıcı)
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_dir = os.path.join(self.base_dir, 'db')
        self.db_path = os.path.join(self.db_dir, 'user.db')
        self.conn = None

    def create_db_directory(self):
        os.makedirs(self.db_dir, exist_ok=True)
    #db ye bağlanma
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    #bağlantıyı kapama
    def close_connection(self):
        if self.conn:
            self.conn.close()
    #yoksa tabloları kuruyor
    def create_tables(self):
        cursor = self.conn.cursor()

        # Kullanıcı kayıt olurken alının bütün bilgiler buraya kayıt ediliyor
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                email TEXT DEFAULT 'example@example.com',
                card_info TEXT,
                subscription_end_date TEXT
            )
        ''')

        #yorumlar için gereken tablo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_name TEXT,
                username TEXT,
                text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # favoriler için gereken tablo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                video_name TEXT
            )
        ''')
    
    
        #favori tablosu oluşturma
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                video_name TEXT
            )
        ''')
    #adım adım ayrılmış fonksiyonların beraber bulunduğu fonksiyon. factory patterne benziyor metoduna biraz benziyor
    def initialize_database(self):
        self.create_db_directory()
        self.connect()
        self.create_tables()
        self.conn.commit()
        self.close_connection()
db_initializer = DatabaseInitializer()