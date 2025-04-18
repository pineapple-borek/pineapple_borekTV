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

# Ana sayfa (video listesini gösterir)
@app.route('/')
def index():
    if 'user' in session:
        # Diziler ve Filmler başlıkları
        return render_template('index.html')
    return redirect('/login')


# Kullanıcı girişi
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Veritabanına bağlan
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kullanıcıyı sorgula
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):  # user[2] şifreyi tutuyor
            flash('Giriş başarılı!', 'success')
            session['user'] = username  # Oturumu başlat
            return redirect(url_for('index'))  # Ana sayfaya yönlendir
        else:
            flash('Hatalı kullanıcı adı veya şifre.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# Kullanıcı kaydı
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Şifreyi hash'le
        hashed_password = generate_password_hash(password)

        # Veritabanına bağlan
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kullanıcı adının zaten mevcut olup olmadığını kontrol et
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user:  # Eğer kullanıcı varsa
            flash('Bu kullanıcı adı zaten alınmış.', 'error')
            return redirect(url_for('register'))

        # Kullanıcıyı ekle
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
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
    return redirect('/login')

# Videoları kategoriye göre listeleme
@app.route('/videos/<category>')
def videos(category):
    if 'user' not in session:
        return redirect(url_for('login'))

    # Kategorilere göre videoları listeleme
    if category == 'diziler':
        videos = os.listdir('pineappleTV/static/videos/diziler')  # Diziler klasörü
    elif category == 'filmler':
        videos = os.listdir('pineappleTV/static/videos/filmler')  # Filmler klasörü
    else:
        flash('Geçersiz kategori.', 'error')
        return redirect(url_for('index'))

    if '.gitignore' in videos:
        videos.remove('.gitignore')

    return render_template('videos.html', videos=videos, category=category)

# Video izleme sayfası
@app.route('/video/<category>/<name>')
def video(category, name):
    if 'user' not in session:
        return redirect(url_for('login'))
    print(f"Category: {category}, Name: {name}")  # Debugging için terminale yazdır
    return render_template('video.html', video_name=name, category=category)


# Videoları akışa sunma
@app.route('/videos/<path:filename>')
def stream_video(filename):
    return send_from_directory('static/videos', filename)

if __name__ == '__main__':
    app.run(debug=True)