from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "PineAppleTV"

# Veritabanı bağlantısı
def get_db_connection():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'db', 'user.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı şemasını güncelle
def update_db_schema():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Eğer subscription_end_date, email ve card_info sütunları yoksa, yeni sütun ekliyoruz
    cursor.execute('PRAGMA table_info(users)')
    columns = [column[1] for column in cursor.fetchall()]

    if 'subscription_end_date' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN subscription_end_date TEXT')
        conn.commit()
        print("subscription_end_date sütunu eklendi.")
    
    if 'email' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
        conn.commit()
        print("email sütunu eklendi.")
    
    if 'card_info' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN card_info TEXT')
        conn.commit()
        print("card_info sütunu eklendi.")
    
    conn.close()

# Uygulama başlatılmadan önce veritabanı şemasını güncelliyoruz
update_db_schema()

# "/" adresi login sayfasına yönlendirilsin
@app.route('/')
def redirect_to_main():
    return redirect(url_for('login'))

@app.route('/main_page')
def index():
    if 'user' not in session:
        return redireset(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Kullanıcı bilgilerini çekelim
    cursor.execute('SELECT username, subscription_end_date FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    # Kullanıcının favori videolarını alalım
    cursor.execute('SELECT video_name FROM favorites WHERE username = ?', (username,))
    favorites = [row['video_name'] for row in cursor.fetchall()]

    conn.close()

    # Kullanıcı adı ve abonelik bitiş tarihini HTML'e gönderiyoruz
    return render_template('index.html', username=user['username'], subscription_end_date=user['subscription_end_date'], favorites=favorites)



# Kullanıcı girişi
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            flash('Giriş başarılı!', 'success')
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash('Hatalı kullanıcı adı veya şifre.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Kullanıcı kaydı
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        card_info = request.form['card_info']  # Kart bilgileri (göstermelik)

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:
            flash('Bu kullanıcı adı zaten alınmış.', 'error')
            return redirect(url_for('register'))

        # Kullanıcıyı veritabanına ekliyoruz
        cursor.execute('INSERT INTO users (username, email, password, card_info) VALUES (?, ?, ?, ?)', 
                       (username, email, hashed_password, card_info))
        conn.commit()
        conn.close()

        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Çıkış işlemi
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Çıkış başarılı.', 'info')
    return redirect(url_for('login'))
@app.route('/shows/<category>')
def shows(category):
    # Kullanıcı giriş yapmadıysa login sayfasına yönlendiriyoruz
    if 'user' not in session:
        return redirect(url_for('login'))
    #secilen kategoriye göre şovların pathini degistiriyoruz
    if category == 'diziler':
        shows_path = 'pineappleTV/static/videos/diziler'
    elif category == 'filmler':
        shows_path = 'pineappleTV/static/videos/filmler'
    else:
        # Geçersiz kategori durumunda hata mesajı gösteriyoruz
        flash('Geçersiz kategori.', 'error')
        return redirect(url_for('index'))
    try:
        # Seçilen kategoriye ait şovların listesini alıyoruz
        #sectigimiz kategoriye göre shows_pathi degistiriyoruz
        #shows_path in içindeki şovların dosyalarının isimleriyle bir liste oluşturuyoruz
        shows = [f for f in os.listdir(shows_path)]
        #şov isimlerini ve thumbnail isimlerini anahtarlara atayoruz
        show_list = [{'name': f, 'thumbnail':'thumbnail.jpg'} for f in shows]
        
    except FileNotFoundError:
        show_list = []
    return render_template('shows.html', category=category, shows=show_list)

@app.route('/videos/<path:category>')
def videos(category):
    if 'user' not in session:
        return redirect(url_for('login'))

    video_path = 'pineappleTV/static/videos/'+'/'+category
    
    
    try:
        videos = [f for f in os.listdir(video_path) if f.endswith('.mp4')]
        video_list = [{'name': f, 'thumbnail':'thumbnail.jpg'} for f in videos]
    except FileNotFoundError:
        video_list = []

    return render_template('videos.html', category=category,videos=video_list)

# Video izleme sayfası
@app.route('/video/<path:name>')
def video(name):
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('video.html', video_name=name)

# Videoları akışa sunma
@app.route('/videos/stream/<path:filename>')
def stream_video(filename):
    video_folder = os.path.join('static', 'videos')
    return send_from_directory(video_folder, filename)

@app.route('/add_to_favorites', methods=['POST'])
def add_to_favorites():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    video_name = request.form['video_name']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Kullanıcı favorilerine video ekliyoruz
    cursor.execute('SELECT * FROM favorites WHERE username = ? AND video_name = ?', (username, video_name))
    existing_favorite = cursor.fetchone()

    if not existing_favorite:
        cursor.execute('INSERT INTO favorites (username, video_name) VALUES (?, ?)', (username, video_name))
        conn.commit()
        flash(f'{video_name} favorilere eklendi!', 'success')
    else:
        flash(f'{video_name} zaten favorilerinizde.', 'warning')

    conn.close()

    return redirect(request.referrer)

def create_favorites_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            video_name TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Uygulama başlatılmadan önce tabloyu oluşturuyoruz
create_favorites_table()

if __name__ == '__main__':
    app.run(debug=True)
