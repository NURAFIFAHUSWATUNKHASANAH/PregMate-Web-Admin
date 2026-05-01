from flask import Blueprint
from controller.controller_diskusi import (
    create_post,
    delete_comment,
    delete_post,
    edit_comment,
    get_posts,
    add_comment,
    like_post,
    set_db,
    update_post
)

diskusi_bp = Blueprint("diskusi_bp", __name__)

@diskusi_bp.route("/diskusi", methods=["GET"])
def posts():
    return get_posts()


@diskusi_bp.route("/diskusi", methods=["POST"])
def post():
    return create_post()


@diskusi_bp.route("/diskusi/comment/<string:post_id>", methods=["POST"])
def comment(post_id):
    return add_comment(post_id)


@diskusi_bp.route("/diskusi/like/<string:post_id>", methods=["POST"])
def like(post_id):
    return like_post(post_id)

@diskusi_bp.route("/diskusi/<string:post_id>", methods=["PUT"])
def edit(post_id):
    return update_post(post_id)


@diskusi_bp.route("/diskusi/<string:post_id>", methods=["DELETE"])
def delete(post_id):
    return delete_post(post_id)

@diskusi_bp.route("/diskusi/comment/<post_id>/<int:index>", methods=["PUT"])
def edit_comment_route(post_id, index):
    return edit_comment(post_id, index)


@diskusi_bp.route("/diskusi/comment/<post_id>/<int:index>", methods=["DELETE"])
def delete_comment_route(post_id, index):
    return delete_comment(post_id, index)