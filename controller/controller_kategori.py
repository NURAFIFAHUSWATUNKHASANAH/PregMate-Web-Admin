from flask import redirect, render_template, request, url_for

from models.kategori_model import KategoriModel


def index():
    data= KategoriModel.get_all()
    return render_template("kategori/index.html", data=data)

def create():
    if request.method=="POST":
        KategoriModel.create({"name": request.form["nama"]})
        return redirect(url_for("kategori_bp.index"))
    return render_template("kategori/create.html")

def edit(id):
    kategori= KategoriModel.get_by_id(id)
    if request.method=="POST":
        KategoriModel.edit({"name": request.form["nama"]})
        return redirect(url_for("kategori_bp.index"))
    return render_template("kategori/edit.html")

def delete(id):
    KategoriModel.delete(id)
    return redirect(url_for("kategori_bp.index"))