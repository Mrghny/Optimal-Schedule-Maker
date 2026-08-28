import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus


load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "db.json")
username = os.getenv('MONGO_USERNAME')
cluster = os.getenv('MONGO_CLUSTER')
password = os.getenv('MONGO_PASSWORD')

username = os.getenv('MONGO_USERNAME')
cluster = os.getenv('MONGO_CLUSTER')
password = os.getenv('MONGO_PASSWORD')

MONGO_URI = None
if username and cluster and password:
    MONGO_URI = f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{cluster}"

all_courses = {}   # department -> course -> { group: {sessions, _mask} }

mongo_client = None

if MONGO_URI:
    try:
        mongo_client = MongoClient(MONGO_URI)
        mongo_client.admin.command('ping')
    except Exception as e:
        print(f"MongoDB connection failed: {e}. Falling back to JSON.")
        mongo_client = None

def reload_courses():
    global all_courses
    # print(mongo_client)
    if mongo_client:
        try:
            db = mongo_client.get_database("app_db")
            collection = db["courses"]

            doc = collection.find_one({"_id": "all_courses_data"}, {"_id": 0})
            if doc:
                all_courses = doc
                return all_courses
        except Exception as e:
            print(f"Error fetching from MongoDB: {e}. Falling back to JSON.")

            

    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    all_courses = data
    return all_courses



def save_courses(data):
    global all_courses
    all_courses = data

    if mongo_client:
        try:
            db = mongo_client["app_db"]
            collection = db["courses"]
            mongo_safe_data = data
            collection.replace_one(
                {"_id": "all_courses_data"}, mongo_safe_data, upsert=True
            )
            return
        except Exception as e:
            print(f"Error saving to MongoDB: {e}. Falling back to JSON.")

    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)