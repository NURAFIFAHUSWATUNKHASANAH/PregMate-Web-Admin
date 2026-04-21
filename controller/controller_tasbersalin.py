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


# ===================== GET USER (UPDATED + SAFE + CLEAN) =====================
@jwt_required()
def get_tas_bersalin():
    user_id = get_jwt_identity()
    kehamilan_id = request.args.get("kehamilan_id")

    if not kehamilan_id or kehamilan_id == "null":
        return jsonify({"msg": "kehamilan_id tidak valid"}), 422

    try:
        k_id = ObjectId(kehamilan_id) if ObjectId.is_valid(kehamilan_id) else kehamilan_id

        master_items = list(TasBersalinModel.master_collection.find({}))
        user_items = list(TasBersalinModel.collection.find({"kehamilan_id": k_id}))

        result = []

        for m in master_items:
            match = next(
                (u for u in user_items if u["name"] == m["name"] and u["category"] == m["category"]),
                None
            )

            result.append({
                "name": m.get("name"),
                "detail": m.get("detail", ""),
                "category": m.get("category"),
                "type": m.get("type", "optional"),  # 🔥 TAMBAHAN WAJIB / OPTIONAL
                "isChecked": match["isChecked"] if match else False
            })

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except Exception as e:
        print(f"❌ Error get_items: {e}")
        return jsonify({"status": "error", "msg": "internal error"}), 500


# ===================== ADMIN INDEX =====================
def admin_index_tas():
    items = list(TasBersalinModel.master_collection.find())
    return render_template("tas_bersalin/index.html", items=items)


# ===================== ADMIN CREATE =====================
def admin_create_tas():
    if request.method == "POST":
        TasBersalinModel.master_collection.insert_one({
            "name": request.form["name"],
            "detail": request.form["detail"],
            "category": request.form["category"],
            "type": request.form.get("type", "optional")  # 🔥 WAJIB / OPTIONAL
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
                "type": request.form.get("type", "optional")  # 🔥
            }}
        )
        return redirect(url_for("tasbersalin_bp.admin_index_tas"))

    return render_template("tas_bersalin/edit.html", item=item)


# ===================== ADMIN DELETE =====================
def admin_delete_tas(id):
    TasBersalinModel.master_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("tasbersalin_bp.admin_index_tas"))