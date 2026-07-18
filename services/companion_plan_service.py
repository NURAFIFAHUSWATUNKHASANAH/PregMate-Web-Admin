from datetime import datetime

from bson import ObjectId

from app import mongo

from services.companion_rules import get_rule


class CompanionPlanService:

    @staticmethod
    def generate_plan(
            user_id,
            partner_id,
            minggu,
            trimester
    ):

        rule = get_rule(trimester)

        daily_tasks = []

        for item in rule["ibu"]:

            daily_tasks.append({

                "title": item,
                "status": False

            })

        partner_tasks = []

        for item in rule["pendamping"]:

            partner_tasks.append({

                "title": item,
                "status": False

            })

        document = {

            "user_id": ObjectId(user_id),

            "partner_id": ObjectId(partner_id) if partner_id else None,

            "week": minggu,

            "trimester": trimester,

            "daily_tasks": daily_tasks,

            "partner_tasks": partner_tasks,

            "education": rule["education"],

            "created_at": datetime.utcnow(),

            "updated_at": datetime.utcnow()

        }

        mongo.db.companion_plans.update_one(

            {

                "user_id": ObjectId(user_id)

            },

            {

                "$set": document

            },

            upsert=True

        )

        return document