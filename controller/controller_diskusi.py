from datetime import datetime

from bson import ObjectId
from flask import jsonify, request
from models.diskusi_model import DiskusiModel
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

diskusi_model = None
db_instance = None

def set_db(db):
    global diskusi_model, db_instance
    diskusi_model = DiskusiModel(db)
    db_instance = db


def create_post():

    user_id = request.form.get("user_id")
    content = request.form.get("content")

    image_url = None

    if "image" in request.files:

        file = request.files["image"]

        if file.filename != "":

            filename = secure_filename(file.filename)

            path = os.path.join(UPLOAD_FOLDER, filename)

            file.save(path)

            image_url = f"/static/uploads/{filename}"

    # =========================
    # AMBIL DATA USER DARI DB
    # =========================

    user = db_instance["users"].find_one({"_id": ObjectId(user_id)})

    if user:
        user_name = user.get("nama", "Pengguna")
        user_photo = user.get("foto", "")
    else:
        user_name = "Pengguna"
        user_photo = ""

    post = diskusi_model.create_post(
        user_id,
        user_name,
        user_photo,
        content,
        image_url
    )

    return jsonify(post), 201

def get_posts():

    posts = diskusi_model.get_posts()

    for post in posts:

        user = None
        user_id = post.get("user_id")

        if user_id and ObjectId.is_valid(user_id):

            user = db_instance["users"].find_one(
                {"_id": ObjectId(user_id)}
            )

        if user:
            post["user_name"] = user.get("nama", "Pengguna")
            post["user_photo"] = user.get("foto", "")
        else:
            post["user_name"] = "Pengguna"
            post["user_photo"] = ""

    return jsonify(posts)

def add_comment(post_id):

    data = request.get_json()

    user_id = data.get("user_id")
    content = data.get("content")

    result = diskusi_model.add_comment(post_id, user_id, content)

    return jsonify(result)

def like_post(post_id):

    data = request.get_json()
    user_id = data.get("user_id")

    result = diskusi_model.like_post(post_id, user_id)

    return jsonify(result)

def update_post(post_id):

    # 🔥 ambil dari JSON atau FORM
    content = request.form.get("content") or request.json.get("content")

    image_url = None

    if "image" in request.files:
        file = request.files["image"]

        if file.filename != "":
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            image_url = f"/static/uploads/{filename}"

    update_data = {}

    if content is not None:
        update_data["content"] = content

    if image_url:
        update_data["image"] = image_url

    db_instance["diskusi"].update_one(
        {"_id": ObjectId(post_id)},
        {"$set": update_data}
    )

    return jsonify({"message": "Post updated"})

def delete_post(post_id):

    post = db_instance["diskusi"].find_one(
        {"_id": ObjectId(post_id)}
    )

    if post:

        image = post.get("image")

        if image:

            image_path = image.replace("/static/", "static/")

            if os.path.exists(image_path):
                os.remove(image_path)

    db_instance["diskusi"].delete_one(
        {"_id": ObjectId(post_id)}
    )

    return jsonify({"message": "Post deleted"})