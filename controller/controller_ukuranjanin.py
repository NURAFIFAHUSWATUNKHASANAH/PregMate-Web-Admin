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
    search_query = request.args.get('search', '')
    data = UkuranJaninModel.get_all(search_query)
    
    # Ambil header accept dengan default string kosong jika None
    accept_header = request.headers.get('Accept', '')
    
    # --- PERBAIKAN CEK DARI FLUTTER ---
    # Memeriksa secara fleksibel apakah client meminta atau mengirim JSON
    if 'application/json' in accept_header or request.is_json:
        list_data = []
        for item in data:
            # Pastikan object kloningan aman dimodifikasi agar tidak merusak data cache asli
            item_copy = dict(item)
            # Mengubah ObjectId MongoDB menjadi string agar serializable ke JSON
            item_copy['_id'] = str(item_copy['_id'])
            list_data.append(item_copy)
        return jsonify(list_data), 200
    # ----------------------------------

    # Tetap kembalikan template web untuk kebutuhan Admin Panel/Web Browser
    return render_template('ukuran_janin/index.html', data=data, search_query=search_query)

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