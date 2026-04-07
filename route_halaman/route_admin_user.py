from flask import Blueprint, render_template, request, redirect, url_for
import controller.controller_admin_user as controller

admin_user = Blueprint('admin_user', __name__, template_folder='../templates/user')

@admin_user.route('/admin/user')
def index():
    users = controller.get_all_users()
    return render_template('user/index.html', users=users)


@admin_user.route('/admin/user/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        controller.create_user(request.form)
        return redirect(url_for('admin_user.index'))
    return render_template('user/create.html')


@admin_user.route('/admin/user/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        controller.update_user(id, request.form)
        return redirect(url_for('admin_user.index'))

    user = controller.get_user(id)
    return render_template('user/edit.html', user=user)


@admin_user.route('/admin/user/delete/<id>')
def delete(id):
    controller.delete_user(id)
    return redirect(url_for('admin_user.index'))