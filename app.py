from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson import ObjectId
import os
import hashlib
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

app.secret_key = os.urandom(24)  # Kunci rahasia untuk sesi


# Konfigurasi folder upload
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Koneksi MongoDB
password = '123'
cxn_str = f'mongodb+srv://aryaisnaidi01:{password}@cluster0.bd5ho.mongodb.net/'
client = MongoClient(cxn_str)
db = client['school_db']  # Nama database
teachers_collection = db['teachers']  # Nama koleksi
about_collection = db['about']


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Anda harus login terlebih dahulu untuk mengakses halaman ini.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    # Ambil data galeri
    galleries = list(gallery_collection.find())

    # Web scraping berita
    url = "https://sdngub1sby.blogspot.com/search/label/PENGUMUMAN"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Ambil data berita
    articles = soup.select("article.hentry")
    news_items = []
    for article in articles:
        title = article.select_one("h2.entry-title").get_text(strip=True) if article.select_one("h2.entry-title") else "Judul tidak tersedia"
        link = article.select_one("a.post-filter-inner")["href"] if article.select_one("a.post-filter-inner") else "#"
        image = (
            article.select_one("img").get("data-src") or article.select_one("img").get("src")
            if article.select_one("img")
            else "/static/images/placeholder.jpg"
        )
        summary = article.select_one("p.post-snippet").get_text(strip=True) if article.select_one("p.post-snippet") else "Ringkasan tidak tersedia"

        news_items.append({
            "title": title,
            "link": link,
            "image": image,
            "summary": summary
        })

    # Ambil hanya 3 berita terbaru
    latest_news = news_items[:3]

    # Render ke template
    return render_template('index.html', title="Home", galleries=galleries, news_items=latest_news)


@app.route('/kelola/about', methods=['GET', 'POST'])
@login_required
def kelola_about():
    about_info = about_collection.find_one() or {}
    
    if request.method == 'POST':
        # Handle form submission for updating about page
        updated_about = {
            'sejarah_paragraf1': request.form.get('sejarah_paragraf1'),
            'sejarah_paragraf2': request.form.get('sejarah_paragraf2'),
            'nama_sekolah': request.form.get('nama_sekolah'),
            'nama_kepala_sekolah': request.form.get('nama_kepala_sekolah'),
            'alamat': request.form.get('alamat'),
            'website': request.form.get('website'),
            'email': request.form.get('email'),
            'telepon': request.form.get('telepon'),
            'no_pendirian': request.form.get('no_pendirian'),
            'no_sertifikat': request.form.get('no_sertifikat'),
            'akreditasi': request.form.get('akreditasi'),
            'tahun_pendirian': request.form.get('tahun_pendirian'),
            'tahun_operasional': request.form.get('tahun_operasional'),
            'no_statistik_sekolah': request.form.get('no_statistik_sekolah'),
            'nis': request.form.get('nis'),
            'status_tanah': request.form.get('status_tanah'),
            'luas_tanah': request.form.get('luas_tanah'),
            'status_bangunan': request.form.get('status_bangunan'),
            'luas_bangunan': request.form.get('luas_bangunan'),
            'fasilitas_lainnya': request.form.get('fasilitas_lainnya')
        }
        
        # Update or insert the about information
        about_collection.update_one({}, {'$set': updated_about}, upsert=True)
        
        flash('Informasi About berhasil diperbarui', 'success')
        return redirect(url_for('about'))
    
    return render_template('editabout.html', about=about_info, title="Kelola Informasi About")

@app.route('/about')
def about():
    # Retrieve about information from database
    about_info = about_collection.find_one() or {}
    return render_template('about.html', title="About", about=about_info)

@app.route('/guru')
def guru():
    page = int(request.args.get('page', 1))  # Halaman saat ini, default 1
    per_page = 8  # Jumlah kartu per halaman
    total_teachers = teachers_collection.count_documents({})  # Total data guru
    total_pages = (total_teachers + per_page - 1) // per_page  # Hitung total halaman

    # Data guru untuk halaman saat ini
    teachers = list(teachers_collection.find().skip((page - 1) * per_page).limit(per_page))
    
    return render_template(
        'dataGuru.html',
        teachers=teachers,
        total_pages=total_pages,
        current_page=page,
        title="Guru"
    )

@app.route('/visimisi')
def visimisi():
    return render_template('visimisi.html', title="Visi & Misi")

@app.route('/gallery')
def gallery():
    # Mengambil data dari koleksi gallery
    galleries = list(gallery_collection.find())
    return render_template('gallery.html', title="Gallery", galleries=galleries)

@app.route('/detail_gallery/<gallery_id>')
def detailGallery(gallery_id):
    # Mengambil data gambar berdasarkan ID dari database
    gallery = gallery_collection.find_one({"_id": ObjectId(gallery_id)})
    return render_template('detailGallery.html', title="Detail Gallery", gallery=gallery)

def scrape_news():
    url = "https://sdngub1sby.blogspot.com/search/label/PENGUMUMAN"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    news_items = []
    articles = soup.select("article.hentry")
    
    for article in articles:
        # Link Berita
        link_element = article.select_one("a.post-filter-inner")
        link = link_element["href"] if link_element else "#"
        
        # Judul Berita
        title_element = article.select_one("h2.entry-title")
        title = title_element.text.strip() if title_element else "Judul tidak tersedia"
        
        # Ringkasan Berita
        summary_element = article.select_one("p.post-snippet")
        summary = summary_element.text.strip() if summary_element else "Ringkasan tidak tersedia"
        
        # Gambar Berita (cek src atau data-src)
        image_element = article.select_one("img")
        if image_element:
            image = image_element.get("src") or image_element.get("data-src")
        else:
            image = "/static/images/placeholder.jpg"
        
        # Menambahkan ke daftar berita
        news_items.append({
            "title": title,
            "summary": summary,
            "link": link,
            "image": image
        })
    
    return news_items


@app.route('/informasi')
def informasi():
    news_items = scrape_news()
    return render_template('berita.html', title="Informasi", news_items=news_items)

kelas_collection = db['kelas']  # Koleksi kelas
@app.route('/jadwalpelajaran')
def jadwalPelajaran():
    kelas = request.args.get('kelas')
    schedules = []

    if kelas:
        # Mengambil jadwal sesuai kelas
        raw_schedules = list(schedules_collection.find({'kelas': kelas}).sort('start_time', 1))
        time_slots = {}

        # Mengelompokkan berdasarkan waktu mulai dan selesai
        for schedule in raw_schedules:
            time_key = f"{schedule['start_time']} - {schedule['end_time']}"
            if time_key not in time_slots:
                time_slots[time_key] = {day: None for day in ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']}
            time_slots[time_key][schedule['hari']] = {
                'mata_pelajaran': schedule['mata_pelajaran'],
                'pengajar': schedule['pengajar']
            }

        # Membentuk struktur jadwal
        schedules = [{'start_time': key.split(' - ')[0], 'end_time': key.split(' - ')[1], **days} for key, days in time_slots.items()]

    kelas_list = list(kelas_collection.distinct('nama'))
    return render_template(
        'jadwalpelajaran.html',
        title="Jadwal Pelajaran",
        schedules=schedules,
        selected_kelas=kelas,
        kelas_list=kelas_list
    )

contacts_collection = db['contacts']

@app.route('/kontak', methods=['GET', 'POST'])
def kontak():
    if request.method == 'POST':
        # Ambil data dari form
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        timestamp = datetime.now()

        # Simpan ke database
        new_contact = {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'timestamp': timestamp
        }
        contacts_collection.insert_one(new_contact)

        # Pesan konfirmasi
        flash('Pesan Anda telah dikirim. Terima kasih!', 'success')
        return redirect(url_for('kontak'))

    return render_template('kontak.html', title="Kontak Kami")

#### login dan register ####
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Ambil data dari form
        username = request.form['username']
        password = request.form['password']

        # Cari user di database
        user = users_collection.find_one({"$or": [{"username": username}, {"email": username}]})
        
        if user:
            # Verifikasi password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == user['password']:
                # Set session jika login berhasil
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                flash('Login successful', 'success')
                return redirect(url_for('dashboard'))  # Arahkan ke dashboard setelah login berhasil
            else:
                flash('Invalid password', 'danger')
        else:
            flash('User not found', 'danger')

    return render_template('login/login.html', title="Login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Ambil data dari form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        status = request.form['status']

        # Validasi password
        if password != confirm_password:
            return "Password dan Confirm Password tidak cocok!", 400

        # Hash password (opsional)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Buat data user baru
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "status": status
        }

        # Simpan ke database
        users_collection.insert_one(new_user)

        return redirect(url_for('login'))  # Redirect ke halaman utama setelah berhasil

    return render_template('login/register.html', title="Register")  # Tampilkan halaman register

#### Dashboard ####
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/dashboard.html', title="Dashboard Page")

# Kelola Guru
@app.route('/kelola/teacher')
@login_required
def teacher():
    teachers = list(teachers_collection.find())
    return render_template('dashboard/guru.html', title="Kelola Guru", teachers=teachers)

@app.route('/kelola/add-teacher', methods=['GET', 'POST'])
@login_required
def addTeacher():
    if request.method == 'POST':
        foto = request.files['foto']
        if foto:
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            foto_path = f'/static/uploads/{filename}'
        else:
            foto_path = ''

        new_teacher = {
            'nama': request.form['nama'],
            'umur': int(request.form['umur']),
            'pelajaran': request.form['pelajaran'],
            'foto': foto_path,
            'email': request.form['email']
        }
        teachers_collection.insert_one(new_teacher)
        return redirect(url_for('teacher'))
    return render_template('dashboard/addguru.html', title="Tambah Guru")

@app.route('/kelola/edit-teacher/<teacher_id>', methods=['GET', 'POST'])
@login_required
def editTeacher(teacher_id):
    teacher = teachers_collection.find_one({'_id': ObjectId(teacher_id)})
    if request.method == 'POST':
        foto = request.files['foto']
        if foto:
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            updated_foto = f'/static/uploads/{filename}'
        else:
            updated_foto = teacher['foto']

        updated_teacher = {
            'nama': request.form['nama'],
            'umur': int(request.form['umur']),
            'pelajaran': request.form['pelajaran'],
            'foto': updated_foto,
            'email': request.form['email']
        }
        teachers_collection.update_one({'_id': ObjectId(teacher_id)}, {'$set': updated_teacher})
        return redirect(url_for('teacher'))
    return render_template('dashboard/editguru.html', title="Edit Guru", teacher=teacher)

@app.route('/kelola/delete-teacher/<teacher_id>')
@login_required
def deleteTeacher(teacher_id):
    teachers_collection.delete_one({'_id': ObjectId(teacher_id)})
    return redirect(url_for('teacher'))

# kelola jadwal kelas
schedules_collection = db['schedules']  # Nama koleksi untuk jadwal kelas

@app.route('/kelola/mapel')
def kelolaJadwal():
    jadwal_list = list(schedules_collection.find())
    classes = list(kelas_collection.distinct('nama'))
    return render_template(
        'dashboard/jadwalkelas.html',
        title="Kelola Jadwal",
        jadwal_list=jadwal_list,
        classes=classes
    )

@app.route('/kelola/add-jadwal', methods=['GET', 'POST'])
def addJadwal():
    if request.method == 'POST':
        # Data dari form
        kelas = request.form['kelas']
        hari = request.form['hari']
        mata_pelajaran = request.form['mata_pelajaran']
        pengajar = request.form['nama']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        
        # Tambahkan jadwal baru ke database
        new_schedule = {
            'kelas': kelas,
            'hari': hari,
            'start_time': start_time,
            'end_time': end_time,
            'mata_pelajaran': mata_pelajaran,
            'pengajar': pengajar
        }
        schedules_collection.insert_one(new_schedule)
        return redirect(url_for('kelolaJadwal'))

    # GET request handling
    nama_guru_list = teachers_collection.distinct('nama')
    kelas_list = list(kelas_collection.find())
    return render_template(
        'dashboard/addjadwal.html',
        title="Tambah Jadwal",
        nama_guru_list=nama_guru_list,
        kelas_list=kelas_list
    )

@app.route('/kelola/edit-jadwal/<jadwal_id>', methods=['GET', 'POST'])
def editJadwal(jadwal_id):
    jadwal = schedules_collection.find_one({'_id': ObjectId(jadwal_id)})
    if request.method == 'POST':
        # Update jadwal dengan data dari form
        updated_schedule = {
            'kelas': request.form['kelas'],
            'hari': request.form['hari'],
            'start_time': request.form['start_time'],
            'end_time': request.form['end_time'],
            'mata_pelajaran': request.form['mata_pelajaran'],
            'pengajar': request.form['nama']
        }
        schedules_collection.update_one({'_id': ObjectId(jadwal_id)}, {'$set': updated_schedule})
        return redirect(url_for('kelolaJadwal'))

    # Ambil data guru dan kelas untuk form
    nama_guru_list = teachers_collection.distinct('nama')
    kelas_list = list(kelas_collection.find())
    return render_template(
        'dashboard/editjadwal.html',
        title="Edit Jadwal",
        jadwal=jadwal,
        nama_guru_list=nama_guru_list,
        kelas_list=kelas_list
    )

@app.route('/kelola/delete-jadwal/<jadwal_id>')
def deleteJadwal(jadwal_id):
    schedules_collection.delete_one({'_id': ObjectId(jadwal_id)})
    return redirect(url_for('kelolaJadwal'))

@app.route('/kelola/kelas')
def kelolaKelas():
    kelas_list = list(db['kelas'].find())
    return render_template('dashboard/kelas.html', title="Kelola Kelas", kelas_list=kelas_list)

@app.route('/kelola/add-kelas', methods=['GET', 'POST'])
def addKelas():
    if request.method == 'POST':
        new_kelas = {
            'nama': request.form['nama'],
        }
        db['kelas'].insert_one(new_kelas)
        return redirect(url_for('kelolaKelas'))
    return render_template('dashboard/addkelas.html', title="Tambah Kelas")

@app.route('/kelola/edit-kelas/<kelas_id>', methods=['GET', 'POST'])
def editKelas(kelas_id):
    kelas = db['kelas'].find_one({'_id': ObjectId(kelas_id)})
    if request.method == 'POST':
        updated_kelas = {
            'nama': request.form['nama'],
        }
        db['kelas'].update_one({'_id': ObjectId(kelas_id)}, {'$set': updated_kelas})
        return redirect(url_for('kelolaKelas'))
    return render_template('dashboard/editkelas.html', title="Edit Kelas", kelas=kelas)

@app.route('/kelola/delete-kelas/<kelas_id>')
def deleteKelas(kelas_id):
    db['kelas'].delete_one({'_id': ObjectId(kelas_id)})
    return redirect(url_for('kelolaKelas'))


# Kelola Gallery
gallery_collection = db['gallery']  # Koleksi galeri
@app.route('/kelola/galeri')
@login_required
def galeri():
    galleries = list(gallery_collection.find())
    return render_template('dashboard/galeri.html', title="Kelola galeri", galleries=galleries)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/kelola/add-galeri', methods=['GET', 'POST'])
@login_required
def addGaleri():
    if request.method == 'POST':
        files = request.files.getlist('foto')  # Mengambil semua file yang di-upload
        foto_paths = []  # Menyimpan path dari setiap foto yang diunggah

        for foto in files:
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_paths.append(f'uploads/{filename}')  # Menambahkan path foto ke list
        
        new_gallery = {
            'deskripsi': request.form['deskripsi'],
            'foto': foto_paths,  # Menyimpan list path foto
        }

        gallery_collection.insert_one(new_gallery)
        return redirect(url_for('galeri'))
    
    return render_template('dashboard/addgaleri.html', title="Tambah galeri")

@app.route('/kelola/edit-galeri/<gallery_id>', methods=['GET', 'POST'])
@login_required
def editGaleri(gallery_id):
    gallery = gallery_collection.find_one({'_id': ObjectId(gallery_id)})
    if request.method == 'POST':
        files = request.files.getlist('foto')
        foto_paths = []  # Menyimpan path foto yang baru

        for foto in files:
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_paths.append(f'uploads/{filename}')

        updated_gallery = {
            'deskripsi': request.form['deskripsi'],
            'foto': foto_paths,  # Memperbarui daftar foto
        }
        gallery_collection.update_one({'_id': ObjectId(gallery_id)}, {'$set': updated_gallery})
        return redirect(url_for('galeri'))
    
    return render_template('dashboard/editgaleri.html', title="Edit galeri", gallery=gallery)

@app.route('/kelola/delete-galeri/<gallery_id>')
@login_required
def deleteGaleri(gallery_id):
    gallery_collection.delete_one({'_id': ObjectId(gallery_id)})
    return redirect(url_for('galeri'))


# Kelola User
# Koleksi pengguna
users_collection = db['users']  # Nama koleksi untuk user

@app.route('/kelola/user')
@login_required
def user():
    users = list(users_collection.find())  # Ambil semua pengguna
    return render_template('dashboard/user.html', title="Kelola User", users=users)


@app.route('/kelola/add-user', methods=['GET', 'POST'])
@login_required
def addUser():
    if request.method == 'POST':
        # Handle form submission
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            return "Password and Confirm Password do not match!", 400

        # Hash password (opsional)
        hashed_password = password

        # Create new user data
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
            "status": "pending"
        }

        # Save to database
        db['users'].insert_one(new_user)
        return redirect(url_for('user'))

    # Handle GET request (display form)
    return render_template('dashboard/adduser.html')

@app.route('/kelola/approve-user/<user_id>', methods=['POST'])
@login_required
def approveUser(user_id):
    db['users'].update_one({"_id": ObjectId(user_id)}, {"$set": {"status": "active"}})
    return redirect(url_for('user'))  # Redirect ke halaman user setelah disetujui



@app.route('/kelola/edit-user/<user_id>', methods=['GET', 'POST'])
@login_required
def editUser(user_id):
    user = db['users'].find_one({"_id": ObjectId(user_id)})
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        # Validasi jika password akan diganti
        if password or confirm_password:
            if password != confirm_password:
                return "Password and Confirm Password do not match!", 400
            hashed_password = password
            updated_user = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "role": role
            }
        else:
            updated_user = {
                "username": username,
                "email": email,
                "role": role
            }

        db['users'].update_one({"_id": ObjectId(user_id)}, {"$set": updated_user})
        return redirect(url_for('user'))

    return render_template('dashboard/edituser.html', title="Edit User", user=user)


@app.route('/kelola/delete-user/<user_id>')
@login_required
def deleteUser(user_id):
    users_collection.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('user'))

@app.route('/kelola/activate-user/<user_id>')
@login_required
def activateUser(user_id):
    users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'status': 'Active'}})
    return redirect(url_for('user'))

@app.route('/kelola/kontak')
@login_required
def kontakMasuk():
    # Pesan belum dibaca di atas, pesan sudah dibaca di bawah
    contacts = list(contacts_collection.find().sort([
        ('read', 1),  # Belum dibaca (False) lebih tinggi prioritas
        ('timestamp', -1)  # Urutkan berdasarkan waktu terbaru
    ]))
    return render_template('dashboard/kontakmasuk.html', contacts=contacts, title="Kontak Masuk")

@app.route('/kelola/kontak/delete/<contact_id>')
@login_required
def deleteContact(contact_id):
    # Hapus pesan berdasarkan ID
    contacts_collection.delete_one({'_id': ObjectId(contact_id)})
    flash('Pesan berhasil dihapus!', 'success')
    return redirect(url_for('kontakMasuk'))

@app.route('/kelola/kontak/toggle-read/<contact_id>')
@login_required
def toggleRead(contact_id):
    # Temukan pesan berdasarkan ID dan ubah status "read"
    contact = contacts_collection.find_one({'_id': ObjectId(contact_id)})
    if contact:
        new_status = not contact.get('read', False)
        contacts_collection.update_one({'_id': ObjectId(contact_id)}, {'$set': {'read': new_status}})
        flash(f"Status pesan berhasil diubah menjadi {'Sudah Dibaca' if new_status else 'Belum Dibaca'}", 'success')
    return redirect(url_for('kontakMasuk'))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
