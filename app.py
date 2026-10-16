
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DATABASE = "mahasiswa.db"


# Membuka koneksi database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Membuat tabel jika belum tersedia
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mahasiswa (
            nim INTEGER PRIMARY KEY,
            nama TEXT NOT NULL,
            program_studi TEXT NOT NULL,
            angkatan INTEGER NOT NULL,
            ipk REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# Memvalidasi data dari form
def validasi_form(form):
    nim = form.get("nim", "").strip()
    nama = form.get("nama", "").strip()
    program_studi = form.get("program_studi", "").strip()
    angkatan = form.get("angkatan", "").strip()
    ipk = form.get("ipk", "").strip()

    if not all([nim, nama, program_studi, angkatan, ipk]):
        return None, "Semua kolom wajib diisi."

    try:
        nim = int(nim)
        angkatan = int(angkatan)
        ipk = float(ipk)
    except ValueError:
        return None, "NIM dan angkatan harus bilangan bulat, IPK harus berupa angka."

    if nim <= 0:
        return None, "NIM harus berupa bilangan bulat positif."

    if not 1900 <= angkatan <= datetime.now().year:
        return None, "Angkatan tidak valid."

    if not 0 <= ipk <= 4:
        return None, "IPK harus berada antara 0,00 dan 4,00."

    return {
        "nim": nim,
        "nama": nama,
        "program_studi": program_studi,
        "angkatan": angkatan,
        "ipk": ipk
    }, None


# READ: menampilkan daftar mahasiswa
@app.route("/")
def home():
    kata_kunci = request.args.get("cari", "").strip()

    conn = get_db()

    if kata_kunci:
        mahasiswa = conn.execute(
            """
            SELECT * FROM mahasiswa
            WHERE CAST(nim AS TEXT) LIKE ?
               OR nama LIKE ?
            ORDER BY nim
            """,
            (f"%{kata_kunci}%", f"%{kata_kunci}%")
        ).fetchall()
    else:
        mahasiswa = conn.execute(
            "SELECT * FROM mahasiswa ORDER BY nim"
        ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        mahasiswa=mahasiswa,
        tahun_sekarang=datetime.now().year,
        error=request.args.get("error"),
        success=request.args.get("success"),
        kata_kunci=kata_kunci
    )



# CREATE: menambah mahasiswa
@app.route("/tambah", methods=["POST"])
def tambah():
    data, error = validasi_form(request.form)

    if error:
        return redirect(url_for("home", error=error))

    conn = get_db()

    try:
        conn.execute("""
            INSERT INTO mahasiswa
            (nim, nama, program_studi, angkatan, ipk)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["nim"],
            data["nama"],
            data["program_studi"],
            data["angkatan"],
            data["ipk"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return redirect(url_for(
            "home", error="NIM sudah terdaftar!"
        ))

    conn.close()
    return redirect(url_for(
        "home", success="Mahasiswa berhasil ditambahkan."
    ))


# UPDATE: menampilkan form edit dan menyimpan perubahan
@app.route("/edit/<int:nim>", methods=["GET", "POST"])
def edit(nim):
    conn = get_db()
    mahasiswa = conn.execute(
        "SELECT * FROM mahasiswa WHERE nim = ?", (nim,)
    ).fetchone()

    if mahasiswa is None:
        conn.close()
        return redirect(url_for(
            "home", error="Data mahasiswa tidak ditemukan."
        ))

    if request.method == "POST":
        data, error = validasi_form(request.form)

        if error:
            conn.close()
            return redirect(url_for("edit", nim=nim, error=error))

        try:
            conn.execute("""
                UPDATE mahasiswa
                SET nim = ?, nama = ?, program_studi = ?,
                    angkatan = ?, ipk = ?
                WHERE nim = ?
            """, (
                data["nim"],
                data["nama"],
                data["program_studi"],
                data["angkatan"],
                data["ipk"],
                nim
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return redirect(url_for(
                "edit", nim=nim, error="NIM sudah digunakan mahasiswa lain."
            ))

        conn.close()
        return redirect(url_for(
            "home", success="Data mahasiswa berhasil diperbarui."
        ))

    conn.close()
    return render_template(
        "edit.html",
        m=mahasiswa,
        error=request.args.get("error")
    )


# DELETE: menghapus mahasiswa
@app.route("/hapus/<int:nim>", methods=["POST"])
def hapus(nim):
    conn = get_db()
    conn.execute("DELETE FROM mahasiswa WHERE nim = ?", (nim,))
    conn.commit()
    conn.close()

    return redirect(url_for(
        "home", success="Data mahasiswa berhasil dihapus."
    ))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
