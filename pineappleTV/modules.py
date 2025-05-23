import sqlite3
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import os
#builder design patterne göre bir sınıf
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

        #videoların beğenisi için gereken tablo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                video_name TEXT NOT NULL,
                state INTEGER DEFAULT 1, -- 1: Beğenildi, 0: Beğeni kaldırıldı
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, video_name) -- Aynı kullanıcı aynı videoyu birden fazla kez beğenemez
            )
        ''')

        # favoriler için gereken tablo
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                show_name TEXT,
                show_category TEXT,
                UNIQUE(username, show_name,show_category) -- Aynı kullanıcı aynı diziyi birden fazla kez favorilerine ekleyemez
            )
        ''')
    #adım adım ayrılmış fonksiyonların beraber bulunduğu fonksiyon. Bir nevi builder metodu
    def initialize_database(self):
        self.create_db_directory()
        self.connect()
        self.create_tables()
        self.conn.commit()
        self.close_connection()
db_initializer = DatabaseInitializer()

class UserManager:
    def __init__(self, db_connection):
        self.conn = db_connection

    def login(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            return True
        return False

    def register(self, username, email, password, card_info):
        cursor = self.conn.cursor()
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, email, password, card_info) VALUES (?, ?, ?, ?)', 
                       (username, email, hashed_password, card_info))
        self.conn.commit()

    def get_user_info(self, username):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()
    
class LikeManager:
    def __init__(self, db_connection):
        self.conn = db_connection

    def toggle_like(self, username, video_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT state FROM likes
            WHERE username = ? AND video_name = ?
        ''', (username, video_name))
        result = cursor.fetchone()

        if result and result['state'] == 1:
            # Beğeniyi kaldır
            cursor.execute('''
                UPDATE likes
                SET state = 0
                WHERE username = ? AND video_name = ?
            ''', (username, video_name))
        else:
            # Beğeniyi ekle veya güncelle
            cursor.execute('''
                INSERT INTO likes (username, video_name, state)
                VALUES (?, ?, 1)
                ON CONFLICT(username, video_name)
                DO UPDATE SET state = 1
            ''', (username, video_name))
        self.conn.commit()

    def toggle_dislike(self, username, video_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT state FROM likes
            WHERE username = ? AND video_name = ?
        ''', (username, video_name))
        result = cursor.fetchone()

        if result and result['state'] == -1:
            # Beğenmeyi kaldır
            cursor.execute('''
                UPDATE likes
                SET state = 0
                WHERE username = ? AND video_name = ?
            ''', (username, video_name))
        else:
            # Beğenmeyi ekle veya güncelle
            cursor.execute('''
                INSERT INTO likes (username, video_name, state)
                VALUES (?, ?, -1)
                ON CONFLICT(username, video_name)
                DO UPDATE SET state = -1
            ''', (username, video_name))
        self.conn.commit()

    def get_like_count(self, video_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as like_count FROM likes
            WHERE video_name = ? AND state = 1
        ''', (video_name,))
        result = cursor.fetchone()
        return result['like_count']

    def get_dislike_count(self, video_name):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as dislike_count FROM likes
            WHERE video_name = ? AND state = -1
        ''', (video_name,))
        result = cursor.fetchone()
        return result['dislike_count']