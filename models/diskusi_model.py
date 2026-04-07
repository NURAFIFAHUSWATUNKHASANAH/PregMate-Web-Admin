from datetime import datetime, timezone
from bson import ObjectId

class DiskusiModel:

    def __init__(self, db):
        self.collection = db["diskusi"]
        self.users = db["users"]

    def create_post(self, user_id, user_name, user_photo, content, image_url=None):

        data = {
            "user_id": user_id,
            "user_name": user_name,
            "user_photo": user_photo,
            "content": content,
            "image": image_url,
            "likes": 0,
            "liked_by": [],
            "comments": [],
            "tanggal": datetime.utcnow(),
            "tanggal": datetime.now(timezone.utc).isoformat()
        }

        result = self.collection.insert_one(data)

        data["_id"] = str(result.inserted_id)

        return data

    def get_posts(self):

        posts = list(self.collection.find().sort("tanggal", -1))

        for post in posts:
            post["_id"] = str(post["_id"])

        return posts

    def add_comment(self, post_id, user_id, content):

        user = self.users.find_one({"_id": ObjectId(user_id)})

        if user:
            user_name = user.get("nama", "Pengguna")
            user_photo = user.get("foto", "")
        else:
            user_name = "Pengguna"
            user_photo = ""

        comment = {
            "user_id": user_id,
            "user_name": user_name,
            "user_photo": user_photo,
            "content": content,
            "tanggal": datetime.utcnow()
        }

        self.collection.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"comments": comment}}
        )

        return {"message": "Comment added"}


    def like_post(self, post_id, user_id):

        post = self.collection.find_one({"_id": ObjectId(post_id)})

        if not post:
            return {"message": "Post not found"}

        liked_by = post.get("liked_by", [])

        if user_id in liked_by:
            # ❌ UNLIKE
            self.collection.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$pull": {"liked_by": user_id},
                    "$inc": {"likes": -1}
                }
            )
            return {"message": "Unliked"}
        else:
            # ❤️ LIKE
            self.collection.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$addToSet": {"liked_by": user_id},
                    "$inc": {"likes": 1}
                }
            )
            return {"message": "Liked"}