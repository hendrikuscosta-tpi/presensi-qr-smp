from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import qrcode
import os
from models.db import init_db

app = Flask(__name__)

# ======================
# DATABASE
# ======================
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ======================
# HOME
# ======================
@app.route('/')
def index():
    return render_template('index.html')

# ======================
# SISWA
# ======================
@app.route('/siswa', methods=['GET', 'POST'])
def siswa():
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute(
            "INSERT INTO siswa (nama, kelas) VALUES (?, ?)",
            (request.form['nama'], request.form['kelas'])
        )
        conn.commit()
        return redirect(url_for('siswa'))

    cur.execute("""
        SELECT siswa.id, siswa.nama, kelas.nama_kelas
        FROM siswa
        JOIN kelas_siswa ON siswa.id = kelas_siswa.siswa_id
        JOIN kelas ON kelas_siswa.kelas_id = kelas.id
        ORDER BY kelas.nama_kelas, siswa.nama
    """)
    data = cur.fetchall()
    conn.close()

    return render_template('siswa.html', siswa=data)

# ======================
# GENERATE QR
# ======================
@app.route('/generate_qr/<int:siswa_id>')
def generate_qr(siswa_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT nama FROM siswa WHERE id = ?", (siswa_id,))
    s = cur.fetchone()

    if not s:
        return "Siswa tidak ditemukan"

    kode_qr = str(siswa_id)
    cur.execute("UPDATE siswa SET qr_code = ? WHERE id = ?", (kode_qr, siswa_id))
    conn.commit()
    conn.close()

    folder = os.path.join('static', 'qrcode')
    os.makedirs(folder, exist_ok=True)

    img = qrcode.make(kode_qr)
    img.save(os.path.join(folder, f"{s['nama'].replace(' ','_')}_{siswa_id}.png"))

    return redirect(url_for('siswa'))

# ======================
# DAFTAR PRESENSI
# ======================
@app.route('/presensi')
def presensi():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT p.id, p.mapel, k.nama_kelas
        FROM presensi p
        JOIN kelas k ON p.kelas_id = k.id
    """)
    data = cur.fetchall()
    conn.close()

    return render_template('presensi.html', presensi=data)

# ======================
# ISI PRESENSI (QR + MANUAL)
# ======================
@app.route('/presensi/<int:presensi_id>', methods=['GET', 'POST'])
def isi_presensi(presensi_id):
    conn = get_db()
    cur = conn.cursor()

    # Ambil siswa + status presensi
    cur.execute("""
        SELECT s.id, s.nama,
               dp.status,
               dp.metode
        FROM siswa s
        JOIN kelas_siswa ks ON ks.siswa_id = s.id
        JOIN presensi p ON p.kelas_id = ks.kelas_id
        LEFT JOIN detail_presensi dp
            ON dp.siswa_id = s.id
           AND dp.presensi_id = ?
        WHERE p.id = ?
        ORDER BY s.nama
    """, (presensi_id, presensi_id))

    siswa = cur.fetchall()

    # SIMPAN PRESENSI MANUAL (HANYA YANG BELUM QR)
    if request.method == 'POST':
        for s in siswa:
            if s['metode'] == 'qr':
                continue

            status = request.form.get(f"status_{s['id']}")
            if status:
                cur.execute("""
                    INSERT INTO detail_presensi
                    (presensi_id, siswa_id, status, metode, waktu)
                    VALUES (?, ?, ?, 'manual', datetime('now'))
                """, (presensi_id, s['id'], status))

        conn.commit()
        return redirect(url_for('isi_presensi', presensi_id=presensi_id))

    conn.close()
    return render_template(
        'isi_presensi.html',
        siswa=siswa,
        presensi_id=presensi_id
    )

# ======================
# SCAN QR (API)
# ======================
@app.route('/scan_qr', methods=['POST'])
def scan_qr():
    data = request.get_json()
    qr_data = data.get('qr_data')
    presensi_id = data.get('presensi_id')

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO detail_presensi (presensi_id, siswa_id, status)
        VALUES (%s, %s, 'Hadir')
        ON CONFLICT DO NOTHING
    """, (presensi_id, qr_data))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'status': 'success',
        'message': 'Presensi berhasil'
    })

# ======================
# RUN
# ======================
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
 