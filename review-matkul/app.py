import csv
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "kunci-rahasia-lokal-bebas"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_MATKUL = os.path.join(BASE_DIR, "matkul.csv")
FILE_REVIEWS = os.path.join(BASE_DIR, "reviews.csv")

DAFTAR_PRODI = ["IK", "SI", "IK KKI", "KA"]

def pastikan_file_ada():
    if not os.path.exists(FILE_MATKUL):
        with open(FILE_MATKUL, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "kode", "nama", "prodi_wajib", "prodi_pilihan", "sks", "deskripsi", "topik_utama"])

    if not os.path.exists(FILE_REVIEWS):
        with open(FILE_REVIEWS, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["matkul_id", "rating", "dosen", "penulis", "komentar"])

pastikan_file_ada()

def deteksi_delimiter(filepath):
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        baris_pertama = f.readline()
        return ";" if baris_pertama.count(";") > baris_pertama.count(",") else ","

def baca_semua_reviews():
    reviews = []
    delim = deteksi_delimiter(FILE_REVIEWS)
    with open(FILE_REVIEWS, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delim)
        for raw_row in reader:
            row = {k.strip(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            if row.get("matkul_id") and row["matkul_id"].isdigit():
                reviews.append({
                    "matkul_id": int(row["matkul_id"]),
                    "rating": int(row["rating"]) if row.get("rating", "").isdigit() else 3,
                    "dosen": row.get("dosen") or "Tidak disebutkan",
                    "penulis": row.get("penulis") or "Anonim",
                    "komentar": row.get("komentar", "")
                })
    return reviews

def baca_semua_matkul():
    semua_reviews = baca_semua_reviews()
    hasil = []
    delim = deteksi_delimiter(FILE_MATKUL)
    
    with open(FILE_MATKUL, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delim)
        for raw_row in reader:
            row = {k.strip(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            if not row.get("id") or not row["id"].isdigit():
                continue

            mk_id = int(row["id"])
            
            # Fallback jika masih ada kolom 'semester' terpisah di CSV lama
            sem_kolom_str = row.get("semester", "")
            default_sem = int(sem_kolom_str) if sem_kolom_str.isdigit() else None
            
            # Parsing format Prodi:Semester (contoh: "IK:3;KA:1") atau "IK;KA"
            wajib_map = {}
            wajib_labels = []
            for item in row.get("prodi_wajib", "").split(";"):
                item = item.strip()
                if not item:
                    continue
                if ":" in item:
                    p_name, sem_part = item.split(":", 1)
                    p_name = p_name.strip()
                    sem_val = int(sem_part.strip()) if sem_part.strip().isdigit() else default_sem
                else:
                    p_name = item
                    sem_val = default_sem

                wajib_map[p_name] = sem_val
                wajib_labels.append(f"{p_name} (Sem {sem_val})" if sem_val else p_name)

            prodi_pilihan = [p.strip() for p in row.get("prodi_pilihan", "").split(";") if p.strip()]
            topik_list = [t.strip() for t in row.get("topik_utama", "").split(";") if t.strip()]
            
            mk_reviews = [r for r in semua_reviews if r["matkul_id"] == mk_id]
            sks_str = row.get("sks", "")
            
            hasil.append({
                "id": mk_id,
                "kode": row.get("kode", ""),
                "nama": row.get("nama", "Tanpa Nama"),
                "wajib_map": wajib_map,
                "prodi_wajib": list(wajib_map.keys()),
                "prodi_pilihan": prodi_pilihan,
                "wajib_teks": ", ".join(wajib_labels),
                "pilihan_teks": ", ".join(prodi_pilihan),
                "semester": default_sem,
                "sks": int(sks_str) if sks_str.isdigit() else 0,
                "deskripsi": row.get("deskripsi", ""),
                "topik_utama": topik_list,
                "reviews": mk_reviews
            })
    return hasil

def tambah_review_csv(matkul_id, rating, dosen, penulis, komentar):
    delim = deteksi_delimiter(FILE_REVIEWS)
    needs_newline = False
    if os.path.exists(FILE_REVIEWS) and os.path.getsize(FILE_REVIEWS) > 0:
        with open(FILE_REVIEWS, "rb") as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b"\n":
                needs_newline = True

    with open(FILE_REVIEWS, mode="a", newline="", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        writer = csv.writer(f, delimiter=delim)
        writer.writerow([matkul_id, rating, dosen, penulis, komentar])

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

@app.route("/")
def index():
    semua_mk = baca_semua_matkul()
    kategori = request.args.get("kategori", "home")
    prodi_filter = request.args.get("prodi", "Semua")
    semester_filter = request.args.get("semester", "Semua")
    search_query = request.args.get("q", "").strip()

    hasil_filter = []
    daftar_semester = []
    tampilkan_semester = (kategori == "wajib" and prodi_filter != "Semua")

    if kategori == "home":
        for m in semua_mk:
            if search_query:
                q_lower = search_query.lower()
                cocok_nama = q_lower in m["nama"].lower()
                cocok_kode = q_lower in m["kode"].lower()
                cocok_desk = q_lower in m["deskripsi"].lower()
                cocok_topik = any(q_lower in t.lower() for t in m["topik_utama"])
                if not (cocok_nama or cocok_kode or cocok_desk or cocok_topik):
                    continue

            data_matkul = m.copy()
            data_matkul["rata_rating"] = hitung_rata_rating(m["reviews"])
            hasil_filter.append(data_matkul)

    elif kategori == "wajib":
        kandidat_wajib = []
        for m in semua_mk:
            if m["wajib_map"]:
                if prodi_filter == "Semua":
                    data_matkul = m.copy()
                    kandidat_wajib.append(data_matkul)
                elif prodi_filter in m["wajib_map"]:
                    data_matkul = m.copy()
                    data_matkul["semester"] = m["wajib_map"][prodi_filter]
                    kandidat_wajib.append(data_matkul)

        if tampilkan_semester:
            daftar_semester = sorted(list(set(
                m["semester"] for m in kandidat_wajib if m["semester"] is not None
            )))

        for m in kandidat_wajib:
            if not tampilkan_semester or semester_filter == "Semua" or str(m["semester"]) == semester_filter:
                m["rata_rating"] = hitung_rata_rating(m["reviews"])
                hasil_filter.append(m)

    elif kategori == "pilihan":
        for m in semua_mk:
            if m["prodi_pilihan"]:
                data_matkul = m.copy()
                data_matkul["rata_rating"] = hitung_rata_rating(m["reviews"])
                hasil_filter.append(data_matkul)

    return render_template(
        "index.html",
        matkul_list=hasil_filter,
        kategori_aktif=kategori,
        prodi_aktif=prodi_filter,
        semester_aktif=semester_filter,
        search_query=search_query,
        daftar_prodi=DAFTAR_PRODI,
        daftar_semester=daftar_semester,
        tampilkan_semester=tampilkan_semester,
        user=session.get("user")
    )

@app.route("/matkul/<int:matkul_id>", methods=["GET", "POST"])
def detail(matkul_id):
    semua_mk = baca_semua_matkul()
    mk = next((m for m in semua_mk if m["id"] == matkul_id), None)
    if not mk:
        return "Mata kuliah tidak ditemukan", 404

    asal_kategori = request.args.get("kategori", "home")
    asal_prodi = request.args.get("prodi", "Semua")
    asal_semester = request.args.get("semester", "Semua")
    tampilkan_semester = (asal_kategori == "wajib" and asal_prodi != "Semua")

    if tampilkan_semester and asal_prodi in mk["wajib_map"]:
        mk["semester"] = mk["wajib_map"][asal_prodi]

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
            tambah_review_csv(matkul_id, rating_baru, dosen_baru, penulis, komentar_baru)
        return redirect(url_for(
            "detail",
            matkul_id=matkul_id,
            kategori=asal_kategori,
            prodi=asal_prodi,
            semester=asal_semester
        ))

    rata_rating = hitung_rata_rating(mk["reviews"])
    return render_template(
        "detail.html",
        matkul=mk,
        rata_rating=rata_rating,
        asal_kategori=asal_kategori,
        asal_prodi=asal_prodi,
        asal_semester=asal_semester,
        tampilkan_semester=tampilkan_semester,
        user=session.get("user")
    )

if __name__ == "__main__":
    app.run(debug=True)