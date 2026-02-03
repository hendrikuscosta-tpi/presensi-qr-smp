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
        kelas_id = request.form['kelas_id']

        cur.execute(
            "INSERT INTO presensi (tanggal, mapel, kelas_id) VALUES (?, ?, ?)",
            (tanggal, mapel, kelas_id)
        )
        conn.commit()
        return redirect(url_for('presensi'))

    cur.execute("""
        SELECT presensi.id, presensi.tanggal, presensi.mapel,
               kelas.nama_kelas, kelas.tahun_ajaran
        FROM presensi
        JOIN kelas ON presensi.kelas_id = kelas.id
        ORDER BY presensi.tanggal DESC
    """)
    data = cur.fetchall()

    cur.execute("SELECT * FROM kelas")
    daftar_kelas = cur.fetchall()

    conn.close()
    return render_template(
        'presensi.html',
        presensi=data,
        daftar_kelas=daftar_kelas
    )


# ------------------------
# ISI PRESENSI MANUAL
# ------------------------
@app.route('/presensi/<int:presensi_id>', methods=['GET', 'POST'])
def isi_presensi_manual(presensi_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT presensi.tanggal, presensi.mapel, kelas.nama_kelas, kelas.id
        FROM presensi
        JOIN kelas ON presensi.kelas_id = kelas.id
        WHERE presensi.id = ?
    """, (presensi_id,))
    presensi = cur.fetchone()

    if not presensi:
        return "Presensi tidak ditemukan"

    cur.execute("""
        SELECT siswa.id, siswa.nama
        FROM siswa
        JOIN kelas_siswa ON siswa.id = kelas_siswa.siswa_id
        WHERE kelas_siswa.kelas_id = ?
        ORDER BY siswa.nama
    """, (presensi['id'],))
    siswa = cur.fetchall()

    if request.method == 'POST':
        for s in siswa:
            status = request.form.get(f"status_{s['id']}")
            if status:
                cur.execute("""
                    INSERT INTO detail_presensi
                    (presensi_id, siswa_id, status, metode, waktu)
                    VALUES (?, ?, ?, 'manual', datetime('now'))
                """, (presensi_id, s['id'], status))

        conn.commit()
        return redirect(url_for('presensi'))

    conn.close()
    return render_template(
        'isi_presensi.html',
        siswa=siswa,
        presensi=presensi
    )

    # =====================
    # TAMPILKAN FORM (GET)
    # =====================
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
