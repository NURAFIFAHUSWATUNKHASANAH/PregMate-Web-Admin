import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from models.ukuranjanin_model import UkuranJaninModel
from bson import ObjectId

UPLOAD_FOLDER = os.path.join('static', 'images', 'ukuran_janin')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def index():
    # 1. Ambil parameter query pencarian dan nomor halaman aktif
    search_query = request.args.get('search', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
        
    per_page = 10  # Jumlah data per halaman untuk web admin

    # --- JIKA REKUEST DARI FLUTTER / API MOBILE ---
    # Memastikan Flutter tetap mendapatkan data hasil pencarian penuh (tanpa terpotong pagination web)
    accept_header = request.headers.get('Accept', '')
    if 'application/json' in accept_header or request.is_json:
        all_data = UkuranJaninModel.get_all(search_query)
        list_data = []
        for item in all_data:
            item_copy = dict(item)
            item_copy['_id'] = str(item_copy['_id'])
            list_data.append(item_copy)
        return jsonify(list_data), 200
    # -----------------------------------------------

    # 2. LOGIKA PAGINATION & SEARCH UNTUK WEB ADMIN PANEL
    query_filter = {}
    if search_query:
        # Ciptakan kriteria pencarian text dasar (case-insensitive)
        or_conditions = [
            {"buah": {"$regex": search_query, "$options": "i"}},
            {"deskripsi": {"$regex": search_query, "$options": "i"}}
        ]
        
        # KUNCI: Jika input pencarian adalah angka murni (cth: "12"), masukkan filter angka untuk field 'minggu'
        if search_query.isdigit():
            or_conditions.append({"minggu": int(search_query)})
        else:
            # Jika user mengetik "Mg-12" atau "Minggu 12", ekstrak angkanya saja agar bisa dicocokkan dengan integer DB
            numeric_extract = ''.join(filter(str.isdigit, search_query))
            if numeric_extract:
                or_conditions.append({"minggu": int(numeric_extract)})
                
        query_filter = {"$or": or_conditions}

    # Ambil instance koneksi collection MongoDB langsung dari model Anda
    collection = UkuranJaninModel.collection 
    
    # Hitung total items hasil filter pencarian
    total_items = collection.count_documents(query_filter)
    total_pages = max(1, (total_items + per_page - 1) // per_page)

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    skip_amount = (page - 1) * per_page
    
    # Mengambil data dengan sorting berdasarkan 'minggu' terurut maju (1 = ascending)
    data_paginated = list(collection.find(query_filter).sort("minggu", 1).skip(skip_amount).limit(per_page))

    # Kembalikan ke template Web Admin beserta data pagination
    return render_template(
        'ukuran_janin/index.html', 
        data=data_paginated, 
        search_query=search_query,
        current_page=page,
        total_pages=total_pages,
        total_items=total_items
    )

def create():
    if request.method == 'POST':
        minggu = request.form.get('minggu')
        buah = request.form.get('buah')
        panjang = request.form.get('panjang')
        berat = request.form.get('berat')
        deskripsi = request.form.get('deskripsi')
        
        file = request.files.get('image')
        image_url = None

        if file and allowed_file(file.filename):
            filename = secure_filename(f"janin_minggu_{minggu}_{file.filename}")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            # Pastikan path image_url bisa diakses lengkap secara absolut jika diperlukan oleh mobile
            image_url = f"/static/images/ukuran_janin/{filename}"

        data_baru = {
            "minggu": int(minggu) if minggu.isdigit() else minggu, # Disarankan diubah ke int agar sorting presisi
            "buah": buah,
            "panjang": panjang,
            "berat": berat,
            "deskripsi": deskripsi,
            "imageUrl": image_url
        }

        UkuranJaninModel.insert(data_baru)
        flash('Data ukuran janin berhasil ditambahkan!', 'success')
        return redirect(url_for('ukuranjanin_bp.index'))

    return render_template('ukuran_janin/create.html')

def edit(id):
    item = UkuranJaninModel.get_by_id(id)
    if not item:
        flash('Data tidak ditemukan!', 'danger')
        return redirect(url_for('ukuranjanin_bp.index'))

    if request.method == 'POST':
        minggu = request.form.get('minggu')
        buah = request.form.get('buah')
        panjang = request.form.get('panjang')
        berat = request.form.get('berat')
        deskripsi = request.form.get('deskripsi')
        
        file = request.files.get('image')
        image_url = item.get('imageUrl')

        if file and allowed_file(file.filename):
            filename = secure_filename(f"janin_minggu_{minggu}_{file.filename}")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            image_url = f"/static/images/ukuran_janin/{filename}"

        data_update = {
            "minggu": int(minggu) if minggu.isdigit() else minggu,
            "buah": buah,
            "panjang": panjang,
            "berat": berat,
            "deskripsi": deskripsi,
            "imageUrl": image_url
        }

        UkuranJaninModel.update(id, data_update)
        flash('Data ukuran janin berhasil diperbarui!', 'success')
        return redirect(url_for('ukuranjanin_bp.index'))

    return render_template('ukuran_janin/edit.html', item=item)

def delete(id):
    UkuranJaninModel.delete(id)
    flash('Data ukuran janin berhasil dihapus!', 'success')
    return redirect(url_for('ukuranjanin_bp.index'))