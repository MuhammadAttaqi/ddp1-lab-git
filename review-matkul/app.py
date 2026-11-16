from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "kunci-rahasia-lokal-bebas"

# Prodi sekarang berbentuk list []
matkul = {
    "matkul_wajib": {
        "semester_1": {
            "DDP1": {
                "kode": "CS101",
                "nama": "Dasar-Dasar Pemrograman 1",
                "prodi": ["Ilmu Komputer", "Sistem Informasi", "Kecerdasan Artifisial"],
                "sks": 4,
                "deskripsi": "Pengenalan logika pemrograman, algoritma dasar, dan struktur data menggunakan bahasa Python.",
                "topik_utama": ["Variabel & Tipe Data", "Percabangan & Perulangan", "Fungsi & Rekursi", "List & Dictionary"],
                "reviews": [
                    {
                        "rating": 5,
                        "dosen": "Pak Budi Santoso",
                        "penulis": "Anonim",
                        "komentar": "Materinya cukup padat untuk pemula, tapi praktikumnya sangat membantu."
                    }
                ]
            },
            "ALIN": {
                "kode": "AI102",
                "nama": "Aljabar Linear",
                "prodi": ["Ilmu Komputer", "Kecerdasan Artifisial"],
                "sks": 3,
                "deskripsi": "Konsep vektor, matriks, nilai eigen, dan penerapannya dalam komputasi serta machine learning.",
                "topik_utama": ["Operasi Matriks", "Ruang Vektor", "Eigenvalues & Eigenvectors", "Singular Value Decomposition (SVD)"],
                "reviews": [
                    {
                        "rating": 5,
                        "dosen": "Bu Siti Aminah",
                        "penulis": "Raka (Mahasiswa 2025)",
                        "komentar": "Teorinya lumayan menantang, wajib banyak latihan soal."
                    }
                ]
            }
        },
        "semester_3": {
            "ML": {
                "kode": "AI201",
                "nama": "Pembelajaran Mesin (Machine Learning)",
                "prodi": ["Kecerdasan Artifisial"],
                "sks": 4,
                "deskripsi": "Algoritma supervised dan unsupervised learning, evaluasi model, serta pengenalan neural networks.",
                "topik_utama": ["Regresi & Klasifikasi", "Decision Trees & Ensemble", "Clustering", "Evaluasi & Validasi Model"],
                "reviews": [
                    {
                        "rating": 5,
                        "dosen": "Pak Hendra Wijaya",
                        "penulis": "Anonim",
                        "komentar": "Banyak tugas coding pakai Scikit-Learn dan Pandas, seru tapi lumayan menyita waktu."
                    }
                ]
            }
        }
    },
    "matkul_pilihan": {
        "ROBOTIKA": {
            "kode": "EL201",
            "nama": "Pengantar Robotika & Otomasi",
            "prodi": "Semua prodi",
            "sks": 3,
            "upvotes": 12,
            "deskripsi": "Dasar kinematika robot, sensor, aktuator, dan pemrograman mikrokontroler dasar.",
            "topik_utama": ["Sensor & Aktuator", "Kinematika Maju", "Kontrol PID Dasar", "Simulasi Robot"],
            "reviews": [
                {
                    "rating": 5,
                    "dosen": "Pak Dimas Pratama",
                    "penulis": "Nadia (Mahasiswa 2024)",
                    "komentar": "Seru karena ada praktik merakit dan simulasi langsung."
                }
            ]
        },
        "KUANTUM": {
            "kode": "EL205",
            "nama": "Komputasi Kuantum Dasar",
            "prodi": "Semua prodi",
            "sks": 3,
            "upvotes": 7,
            "deskripsi": "Pengenalan qubit, gerbang logika kuantum, dan algoritma dasar seperti Grover dan Shor.",
            "topik_utama": ["Superposisi & Entanglement", "Quantum Gates", "Algoritma Deutsch-Jozsa", "Simulasi Qiskit"],
            "reviews": [
                {
                    "rating": 5,
                    "dosen": "Bu Larasati",
                    "penulis": "Anonim",
                    "komentar": "Konsepnya mind-blowing, butuh dasar aljabar linear yang kuat."
                }
            ]
        }
    }
}

def get_semua_matkul():
    hasil = []
    idx = 1

    for sem_key, daftar_mk in matkul.get("matkul_wajib", {}).items():
        nomor_sem = int(sem_key.split("_")[1]) if "_" in sem_key else sem_key
        for singkatan, info in daftar_mk.items():
            info["id"] = idx
            info["singkatan"] = singkatan
            info["jenis"] = "Wajib"
            info["semester"] = nomor_sem
            if isinstance(info["prodi"], str):
                info["prodi_list"] = [p.strip() for p in info["prodi"].split(",") if p.strip()]
            else:
                info["prodi_list"] = info["prodi"]    
            info["prodi_teks"] = ", ".join(info["prodi_list"])
            
            info.setdefault("upvotes", 0)
            hasil.append(info)
            idx += 1

    for singkatan, info in matkul.get("matkul_pilihan", {}).items():
        info["id"] = idx
        info["singkatan"] = singkatan
        info["jenis"] = "Pilihan"
        info["semester"] = None
        info.setdefault("upvotes", 0)
        hasil.append(info)
        idx += 1

    return hasil

def hitung_rata_rating(reviews):
    if not reviews:
        return 0
    total = sum(r["rating"] for r in reviews)
    return round(total / len(reviews), 1)

@app.route("/login", methods=["POST"])
def login():
    nama = request.form.get("nama", "").strip()
    role = request.form.get("role", "Mahasiswa")
    angkatan = request.form.get("angkatan", "").strip()

    if nama:
        session["user"] = {
            "nama": nama,
            "role": role,
            "angkatan": angkatan if role == "Mahasiswa" else ""
        }
    return redirect(request.referrer or url_for("index"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(request.referrer or url_for("index"))

@app.route("/upvote/<int:matkul_id>", methods=["POST"])
def upvote(matkul_id):
    semua_mk = get_semua_matkul()
    mk = next((m for m in semua_mk if m["id"] == matkul_id), None)
    if mk and mk["jenis"] == "Pilihan":
        mk["upvotes"] += 1
    return redirect(request.referrer or url_for("index"))

@app.route("/")
def index():
    semua_mk = get_semua_matkul()
    jenis_filter = request.args.get("jenis", "Semua")
    prodi_filter = request.args.get("prodi", "Semua")
    semester_filter = request.args.get("semester", "Semua")

    hasil_filter = []
    for m in semua_mk:
        cocok_jenis = (jenis_filter == "Semua") or (m["jenis"] == jenis_filter)
        
        if jenis_filter == "Wajib":
            # Cek apakah prodi_filter ada di dalam list m["prodi"]
            cocok_prodi = (prodi_filter == "Semua") or (prodi_filter in m["prodi"])
            cocok_semester = (semester_filter == "Semua") or (str(m["semester"]) == semester_filter)
        else:
            cocok_prodi = True
            cocok_semester = True

        if cocok_jenis and cocok_prodi and cocok_semester:
            data_matkul = m.copy()
            data_matkul["rata_rating"] = hitung_rata_rating(m["reviews"])
            hasil_filter.append(data_matkul)

    if jenis_filter == "Pilihan":
        hasil_filter.sort(key=lambda x: x["upvotes"], reverse=True)

    # Kumpulkan semua nama prodi unik dari tiap list prodi di matkul Wajib
    set_prodi = set()
    for m in semua_mk:
        if m["jenis"] == "Wajib":
            for p in m["prodi"]:
                set_prodi.add(p)
    daftar_prodi = sorted(list(set_prodi))

    daftar_semester = sorted(list(set(m["semester"] for m in semua_mk if m["jenis"] == "Wajib" and m["semester"] is not None)))

    return render_template(
        "index.html",
        matkul_list=hasil_filter,
        jenis_aktif=jenis_filter,
        prodi_aktif=prodi_filter,
        semester_aktif=semester_filter,
        daftar_prodi=daftar_prodi,
        daftar_semester=daftar_semester,
        user=session.get("user")
    )

@app.route("/matkul/<int:matkul_id>", methods=["GET", "POST"])
def detail(matkul_id):
    semua_mk = get_semua_matkul()
    mk = next((m for m in semua_mk if m["id"] == matkul_id), None)
    if not mk:
        return "Mata kuliah tidak ditemukan", 404

    if request.method == "POST":
        rating_baru = int(request.form.get("rating", 3))
        dosen_baru = request.form.get("dosen", "").strip() or "Tidak disebutkan"
        komentar_baru = request.form.get("komentar", "").strip()
        mode_identitas = request.form.get("identitas", "anonim")

        user = session.get("user")

        if mode_identitas == "publik" and user:
            if user["role"] == "Mahasiswa" and user["angkatan"]:
                penulis = f"{user['nama']} (Mahasiswa {user['angkatan']})"
            else:
                penulis = f"{user['nama']} ({user['role']})"
        else:
            penulis = "Anonim"

        if komentar_baru:
            mk["reviews"].append({
                "rating": rating_baru,
                "dosen": dosen_baru,
                "penulis": penulis,
                "komentar": komentar_baru
            })
        return redirect(url_for("detail", matkul_id=matkul_id))

    rata_rating = hitung_rata_rating(mk["reviews"])
    return render_template("detail.html", matkul=mk, rata_rating=rata_rating, user=session.get("user"))

if __name__ == "__main__":
    app.run(debug=True)