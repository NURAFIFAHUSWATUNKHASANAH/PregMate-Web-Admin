from bson import ObjectId
from werkzeug.security import generate_password_hash

db = None
users_collection = None

def set_db(database):
    global db, users_collection
    db = database
    users_collection = db['users']


def get_all_users():
    users = list(users_collection.find())
    for u in users:
        u['_id'] = str(u['_id'])
    return users


def get_user(id):
    user = users_collection.find_one({'_id': ObjectId(id)})
    if user:
        user['_id'] = str(user['_id'])
    return user


def create_user(data):
    users_collection.insert_one({
        "nama": data['nama'],
        "email": data['email'],
        "password": generate_password_hash(data['password']),
        "role": data['role'],
        "is_active": True
    })


def update_user(id, data):
    users_collection.update_one(
        {'_id': ObjectId(id)},
        {'$set': {
            "nama": data['nama'],
            "email": data['email'],
            "role": data['role']
        }}
    )


def delete_user(id):
    users_collection.delete_one({'_id': ObjectId(id)})