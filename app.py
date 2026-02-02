from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import qrcode
import os
from models.db import init_db

app = Flask(__name__)

# ------------------------
# Database helper
# ------------------------
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------
# HOME
# ------------------------
@app.route('/')
def index():
    return render_template('index.html')


# ------------------------
# DATA SISWA
# ------------------------
@app.route('/siswa', methods=['GET', 'POST'])
def siswa():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        nama = request.form['nama']
        kelas = request.form['kelas']

        cur.execute(
            "INSERT INTO siswa (nama, kelas) VALUES (?, ?)",
            (nama, kelas)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('siswa'))

    cur.execute("SELECT * FROM siswa ORDER BY kelas, nama")
    data_siswa = cur.fetchall()
    conn.close()

    return render_template('siswa.html', siswa=data_siswa)


# ------------------------
# GENERATE QR SISWA
# ------------------------
@app.route('/generate_qr/<int:siswa_id>')
def generate_qr(siswa_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, nama, kelas FROM siswa WHERE id = ?",
        (siswa_id,)
    )
    siswa = cur.fetchone()

    if not siswa:
        conn.close()
        return "Siswa tidak ditemukan"

    kode_qr = f"SMP-{siswa[2]}-{siswa[0]}"

    cur.execute(
        "UPDATE siswa SET qr_code = ? WHERE id = ?",
        (kode_qr, siswa_id)
    )
    conn.commit()
    conn.close()

    qr_folder = os.path.join('static', 'qrcode')
    if not os.path.exists(qr_folder):
        os.makedirs(qr_folder)

    img = qrcode.make(kode_qr)
    nama_file = f"{safe_filename(siswa[1])}_{siswa_id}.png"
    img.save(os.path.join(qr_folder, nama_file))

    return redirect(url_for('siswa'))


def safe_filename(text):
    return text.lower().replace(" ", "_")


# ------------------------
# SESI PRESENSI (BUAT & DAFTAR)
# ------------------------
@app.route('/presensi', methods=['GET', 'POST'])
def presensi():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        tanggal = request.form['tanggal']
        mapel = request.form['mapel']
        kelas = request.form['kelas']

        cur.execute(
            "INSERT INTO presensi (tanggal, mapel, kelas) VALUES (?, ?, ?)",
            (tanggal, mapel, kelas)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('presensi'))

    cur.execute("""
        SELECT id, tanggal, mapel, kelas
        FROM presensi
        ORDER BY tanggal DESC
    """)
    data = cur.fetchall()
    conn.close()

    return render_template('presensi.html', presensi=data)


# ------------------------
# ISI PRESENSI MANUAL
# ------------------------
@app.route('/presensi/<int:presensi_id>', methods=['GET', 'POST'])
def isi_presensi_manual(presensi_id):
    conn = get_db()
    cur = conn.cursor()

    # Ambil data sesi presensi
    cur.execute("""
        SELECT kelas, tanggal, mapel
        FROM presensi
        WHERE id = ?
    """, (presensi_id,))
    presensi = cur.fetchone()

    if not presensi:
        conn.close()
        return "Presensi tidak ditemukan"

    kelas, tanggal, mapel = presensi

    # Ambil siswa sesuai kelas
    cur.execute("""
        SELECT id, nama
        FROM siswa
        WHERE kelas = ?
        ORDER BY nama
    """, (kelas,))
    siswa = cur.fetchall()

    # SIMPAN PRESENSI MANUAL
    if request.method == 'POST':
        for s in siswa:
            siswa_id = s[0]
            status = request.form.get(f'status_{siswa_id}')

            if status:
                cur.execute("""
                    INSERT INTO detail_presensi
                    (presensi_id, siswa_id, status, metode, waktu)
                    VALUES (?, ?, ?, 'manual', datetime('now'))
                """, (presensi_id, siswa_id, status))

        conn.commit()
        conn.close()
        return redirect(url_for('presensi'))

    conn.close()
    return render_template(
        'isi_presensi.html',
        siswa=siswa,
        presensi_id=presensi_id,
        tanggal=tanggal,
        mapel=mapel,
        kelas=kelas
    )



# ------------------------
# RUN APP (HARUS PALING BAWAH)
# ------------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
