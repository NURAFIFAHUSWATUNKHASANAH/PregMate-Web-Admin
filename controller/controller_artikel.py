from flask import request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import os
from bson import ObjectId
from datetime import datetime, timezone

db = None
artikel_collection = None

def set_db(database):
    global db, artikel_collection
    db = database
    artikel_collection = db['artikel']


def get_all_articles(search=''):
    query = {}
    if search:
        query = {
            "$or": [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}}
            ]
        }

    articles = list(artikel_collection.find(query))

    for article in articles:
        article['_id'] = str(article['_id'])

        # image URL fix
        if 'imageUrl' in article and article['imageUrl'] and not article['imageUrl'].startswith('http'):
            article['imageUrl'] = request.host_url.rstrip('/') + article['imageUrl']

        # ✅ SAFE createdAt handling (ANTI DATA KOTOR)
        created = article.get('createdAt')

        if isinstance(created, datetime):
            article['createdAt'] = created.isoformat()

        elif isinstance(created, str):
            try:
                # kalau sudah ISO valid → biarkan
                datetime.fromisoformat(created.replace("Z", "+00:00"))
            except:
                # kalau format aneh (Wed, 22 April 2026) → buang biar tidak crash Flutter
                article['createdAt'] = ""

        else:
            article['createdAt'] = ""

    return articles


def get_article_by_id(article_id):
    article = artikel_collection.find_one({'_id': ObjectId(article_id)})
    if article:
        article['_id'] = str(article['_id'])
        if 'imageUrl' in article and article['imageUrl'] and not article['imageUrl'].startswith('http'):
            article['imageUrl'] = request.host_url.rstrip('/') + article['imageUrl']
    return article


def create_article(title, content, image_file):
    filename = None
    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join('static/images/artikel', filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)

    artikel_collection.insert_one({
        'title': title,
        'content': content,
        'imageUrl': f'/static/images/artikel/{filename}' if filename else '',
        # ✅ ISO 8601 UTC (AMAN 100%)
        'createdAt': datetime.now(timezone.utc).isoformat()
    })

def update_article(article_id, title, content, image_file):
    update_data = {
        'title': title,
        'content': content,
    }
    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join('static/images/artikel', filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)
        update_data['imageUrl'] = f'/static/images/artikel/{filename}'
    artikel_collection.update_one({'_id': ObjectId(article_id)}, {'$set': update_data})

def delete_article(article_id):
    artikel_collection.delete_one({'_id': ObjectId(article_id)})
