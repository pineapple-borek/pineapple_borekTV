from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory, flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os
import modules
from pineappleTV.modules import DatabaseInitializer
from pineappleTV.modules import db_initializer



app = Flask(__name__)
app.secret_key = "PineAppleTV"

# Veritabanı bağlantısı
def get_db_connection():
    conn = db_initializer.connect()
    return conn

# Veritabanı şemasını güncelle
def check_db():    
    db_initializer.initialize_database()
    
    conn = db_initializer.connect()
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



# "/" adresi login sayfasına yönlendirilsin
@app.route('/')
def redirect_to_main():
    return redirect(url_for('login'))

@app.route('/main_page')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

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
    # Eğer kullanıcı zaten giriş yaptıysa ana sayfaya yönlendir
    if 'user' in session:
        return redirect(url_for('index'))

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
@app.route('/video/<path:name>', methods=['GET', 'POST'])
def video(name):
    #video dosya isimleri 1.mp4, 2.mp4 gibi isimlendirilmelidir.
    if 'user' not in session:
        return redirect(url_for('login'))

    # Extract directory and filename
    video_dir_relative = os.path.dirname(name) # e.g., diziler/Flash
    video_filename = os.path.basename(name) # e.g., 1.mp4
    video_dir_absolute = os.path.join('pineappleTV', 'static', 'videos', video_dir_relative) # Absolute path to the directory

    prev_video = None
    next_video = None

    try:
        # List all mp4 files in the directory
        all_videos = sorted(
            [f for f in os.listdir(video_dir_absolute) if f.endswith('.mp4')],
            key=lambda x: int(os.path.splitext(x)[0]) # Sort numerically based on filename (e.g., 1, 2, 10)
        )

        # Find the index of the current video
        current_index = all_videos.index(video_filename)

        # Determine previous video
        if current_index > 0:
            prev_filename = all_videos[current_index - 1]
            prev_video = os.path.join(video_dir_relative, prev_filename).replace('\\', '/') # Use relative path for URL

        # Determine next video
        if current_index < len(all_videos) - 1:
            next_filename = all_videos[current_index + 1]
            next_video = os.path.join(video_dir_relative, next_filename).replace('\\', '/') # Use relative path for URL

    except (FileNotFoundError, ValueError, IndexError) as e:
        # Handle cases where directory doesn't exist, filename isn't numeric, or video not found
        print(f"Error finding next/prev video: {e}")
        pass # Keep prev_video and next_video as None

    conn = get_db_connection()
    cursor = conn.cursor()

    # Eğer POST isteği varsa, yeni bir yorum ekle
    if request.method == 'POST':
        username = session['user']
        comment_text = request.form['comment']
        cursor.execute('INSERT INTO comments (video_name, username, text) VALUES (?, ?, ?)', 
                       (name, username, comment_text))
        conn.commit()

    # Videoya ait yorumları getir
    cursor.execute('SELECT id, username, text FROM comments WHERE video_name = ? ORDER BY id DESC', (name,))
    comments = cursor.fetchall()

    # Yorum sayısını hesapla
    comment_count = len(comments)

    conn.close()

    return render_template('video.html', video_name=name, comments=comments, comment_count=comment_count, prev_video=prev_video, next_video=next_video)

# Videoları akışa sunma
@app.route('/videos/stream/<path:filename>')
def stream_video(filename):
    video_folder = os.path.join('static', 'videos')
    return send_from_directory(video_folder, filename)

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Yorumu sil
    cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()

    flash('Yorum başarıyla silindi.', 'success')
    return redirect(request.referrer)

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


@app.route('/favorite')
def favorite():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT video_name FROM favorites WHERE username = ?', (username,))
    favorite_videos = cursor.fetchall()
    conn.close()

    favorite_list = [row['video_name'] for row in favorite_videos]
    return render_template('favorite.html', favorite=favorite_list)


@app.route('/remove_favorite/<video_name>', methods=['POST'])
def remove_favorite(video_name):
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE username = ? AND video_name = ?', (username, video_name))
    conn.commit()
    conn.close()
    flash(f'"{video_name}" favorilerden kaldırıldı.', 'success')
    return redirect(url_for('favorite'))

@app.route('/search')
def search():
    if 'user' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').lower()
    search_path = os.path.join('pineappleTV', 'static', 'videos')

    results = []
    try:
        for filename in os.listdir(search_path):
            if query in filename.lower() and filename.endswith('.mp4'):
                base_filename = os.path.splitext(filename)[0]
                
                # mp4 ile jpg nin isminin aynı olıp olmadığına bakıyor
                thumbnail_filename = base_filename + '.jpg'
                thumbnail_path = os.path.join(search_path, thumbnail_filename)
                thumbnail = thumbnail_filename
                
                results.append({
                    'name': filename,
                    'thumbnail': thumbnail
                })
    except FileNotFoundError:
        pass

    return render_template('search_results.html', query=query, results=results)


if __name__ == '__main__':
    # Uygulama başlatılmadan önce veritabanı şemasını kontrol ediyoruz 
    check_db()
    app.run(debug=True)
