from flask import request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models.tas_bersalin_model import TasBersalinModel


# ===================== TOGGLE =====================
@jwt_required()
def toggle_tas_bersalin():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"msg": "Body request kosong"}), 422

    kehamilan_id = data.get("kehamilan_id")
    category = data.get("category")
    name = data.get("name")

    if not all([kehamilan_id, category, name]):
        return jsonify({"msg": "Data tidak lengkap"}), 422

    result = TasBersalinModel.toggle_item(
        user_id=user_id,
        kehamilan_id=kehamilan_id,
        category=category,
        name=name,
        detail=data.get("detail", ""),
        is_checked=data.get("isChecked", False)
    )

    if result:
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 500


# ===================== DELETE ITEM (USER & ADMIN) =====================
@jwt_required()
def delete_tas_bersalin(id): # 'id' didapat dari variabel URL parameter 
    data = request.get_json() or {}
    kehamilan_id = data.get("kehamilan_id")

    if not kehamilan_id:
        return jsonify({"msg": "kehamilan_id diperlukan untuk menghapus item"}), 422

    try:
        k_id = ObjectId(kehamilan_id) if ObjectId.is_valid(kehamilan_id) else kehamilan_id
        item_id = ObjectId(id) if ObjectId.is_valid(id) else id

        # 1. Cek dulu apakah item ini ada di user_progress_tas dan berstatus 'is_custom'
        user_item = TasBersalinModel.collection.find_one({"_id": item_id})

        if user_item and user_item.get("is_custom") == True:
            # Skenario A: Jika item buatan kustom user sendiri -> HAPUS PERMANEN
            TasBersalinModel.delete_custom_item(id)
            return jsonify({"status": "success", "msg": "Item custom berhasil dihapus"}), 200
        else:
            # Skenario B: Jika item bawaan ADMIN (tidak ada di koleksi progres atau tidak custom)
            # Ambil detail nama & kategori dari data master terlebih dahulu
            master_item = TasBersalinModel.master_collection.find_one({"_id": item_id})
            
            # Jika item_id ternyata adalah id progress bawaan yang di-upsert, cari cadangannya lewat nama
            if not master_item and user_item:
                name_item = user_item.get("name")
                category_item = user_item.get("category")
            elif master_item:
                name_item = master_item.get("name")
                category_item = master_item.get("category")
            else:
                return jsonify({"msg": "Item tidak ditemukan"}), 404

            # Daftarkan flag 'is_hidden': True khusus kehamilan_id ini
            TasBersalinModel.hide_item_for_user(k_id, name_item, category_item)
            return jsonify({"status": "success", "msg": "Item rekomendasi disembunyikan"}), 200

    except Exception as e:
        print(f"❌ Error delete_tas_bersalin: {e}")
        return jsonify({"status": "error", "msg": "Terjadi kesalahan internal"}), 500


# ===================== GET USER (SINKRON DENGAN FITUR SEMBUNYI) =====================
@jwt_required()
def get_tas_bersalin():
    user_id = get_jwt_identity()
    kehamilan_id = request.args.get("kehamilan_id")

    if not kehamilan_id or kehamilan_id == "null":
        return jsonify({"msg": "kehamilan_id tidak valid"}), 422

    try:
        k_id = ObjectId(kehamilan_id) if ObjectId.is_valid(kehamilan_id) else kehamilan_id

        # 1. Ambil seluruh data master bawaan admin yang bersifat global (tidak disembunyikan admin)
        master_items = list(TasBersalinModel.master_collection.find({"is_hidden": {"$ne": True}}))
        
        # 2. Ambil progres & konfigurasi spesifik dari user ini
        user_progress_data = list(TasBersalinModel.collection.find({"kehamilan_id": k_id}))

        # Buat daftar item bawaan admin yang sengaja disembunyikan oleh pengguna ini
        hidden_by_user = [
            u["name"] for u in user_progress_data if u.get("is_hidden") == True
        ]

        result = []

        # 3. Gabungkan Master (yang tidak di-hide user) + Custom User
        for m in master_items:
            if m["name"] in hidden_by_user:
                continue # Skip jika disembunyikan oleh pengguna ini

            match = next((u for u in user_progress_data if u["name"] == m["name"]), None)
            result.append({
                "id": str(m["_id"]),
                "name": m["name"],
                "detail": m.get("detail", ""),
                "category": m["category"],
                "type": m.get("type", "Disarankan"),
                "isChecked": match["isChecked"] if match else False,
                "isCustom": False
            })

        for u in user_progress_data:
            if u.get("is_custom") == True and u.get("is_hidden") != True:
                result.append({
                    "id": str(u["_id"]),
                    "name": u["name"],
                    "detail": u.get("detail", ""),
                    "category": u["category"],
                    "type": u.get("type", "Pribadi"),
                    "isChecked": u.get("isChecked", False),
                    "isCustom": True
                })

        return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        print(f"❌ Error get_items: {e}")
        return jsonify({"status": "error", "msg": "Terjadi kesalahan internal"}), 500

# ===================== ADD CUSTOM ITEM =====================
@jwt_required()
def add_custom_item():
    user_id = get_jwt_identity()
    data = request.get_json()

    kehamilan_id = data.get("kehamilan_id")
    name = data.get("name")
    category = data.get("category")
    priority_type = data.get("priority")  # Di Flutter kamu kirim key 'priority'
    detail = data.get("detail", "")       # Ambil deskripsi opsional

    if not all([kehamilan_id, name, category, priority_type]):
        return jsonify({"msg": "Data tidak lengkap"}), 422

    result = TasBersalinModel.add_custom_item(
        user_id=user_id,
        kehamilan_id=kehamilan_id,
        name=name,
        category=category,
        type=priority_type,
        detail=detail
    )

    if result:
        return jsonify({"msg": "Item kustom berhasil ditambahkan"}), 201
    return jsonify({"msg": "Gagal menambahkan item"}), 500


# ===================== UPDATE CUSTOM ITEM (FITUR BARU) =====================
@jwt_required()
def update_custom_item(item_id):
    data = request.get_json()

    name = data.get("name")
    category = data.get("category")
    priority_type = data.get("priority")
    detail = data.get("detail", "")

    if not all([name, category, priority_type]):
        return jsonify({"msg": "Data perubahan tidak lengkap"}), 422

    result = TasBersalinModel.update_custom_item(
        item_id=item_id,
        name=name,
        category=category,
        type=priority_type,
        detail=detail
    )

    if result and result.modified_count > 0:
        return jsonify({"msg": "Item kustom berhasil diperbarui"}), 200
        
    return jsonify({"msg": "Gagal memperbarui item atau tidak ada perubahan data"}), 400

# ===================== ADMIN INDEX (WITH PAGINATION & SEARCH) =====================
def admin_index_tas():
    try:
        # 1. Ambil query pencarian dan nomor halaman aktif dari URL
        search_query = request.args.get('search', '').strip()
        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            page = 1
            
        per_page = 10  # Jumlah data per halaman

        # 2. Bangun filter pencarian menggunakan Regex (Case-Insensitive)
        query_filter = {}
        if search_query:
            query_filter = {
                "$or": [
                    {"name": {"$regex": search_query, "$options": "i"}},
                    {"detail": {"$regex": search_query, "$options": "i"}},
                    {"category": {"$regex": search_query, "$options": "i"}},
                    {"type": {"$regex": search_query, "$options": "i"}}
                ]
            }
        
        # 3. Hitung total records ter-filter dan total halaman keseluruhan
        total_items = TasBersalinModel.master_collection.count_documents(query_filter)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        
        # Pastikan page tidak out-of-bounds
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        # 4. Ambil potongan data berdasarkan halaman aktif
        skip_amount = (page - 1) * per_page
        items = list(TasBersalinModel.master_collection.find(query_filter).skip(skip_amount).limit(per_page))
        
        # 5. Kirimkan variabel penunjang pagination dan search ke template
        return render_template(
            "tas_bersalin/index.html", 
            items=items, 
            current_page=page, 
            total_pages=total_pages,
            total_items=total_items,
            search_query=search_query
        )
    except Exception as e:
        print(f"❌ Error admin_index_tas: {e}")
        items = list(TasBersalinModel.master_collection.find().limit(10))
        return render_template("tas_bersalin/index.html", items=items, current_page=1, total_pages=1, total_items=len(items), search_query="")

# ===================== ADMIN CREATE =====================
def admin_create_tas():
    if request.method == "POST":
        TasBersalinModel.master_collection.insert_one({
            "name": request.form["name"],
            "detail": request.form["detail"],
            "category": request.form["category"],
            "type": request.form.get("type", "Disarankan")  # 🔥 WAJIB / OPTIONAL
        })
        return redirect(url_for("tasbersalin_bp.admin_index_tas"))

    return render_template("tas_bersalin/create.html")


# ===================== ADMIN EDIT =====================
def admin_edit_tas(id):
    item = TasBersalinModel.master_collection.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        TasBersalinModel.master_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "name": request.form["name"],
                "detail": request.form["detail"],
                "category": request.form["category"],
                "type": request.form.get("type", "Disarankan")  # 🔥
            }}
        )
        return redirect(url_for("tasbersalin_bp.admin_index_tas"))

    return render_template("tas_bersalin/edit.html", item=item)


# ===================== ADMIN DELETE =====================
def admin_delete_tas(id):
    TasBersalinModel.master_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("tasbersalin_bp.admin_index_tas"))