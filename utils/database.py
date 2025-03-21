from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class MongoDBConnection:
    _instance = None

    def __new__(cls, uri, db_name):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance.client = MongoClient(uri)
            cls._instance.db = cls._instance.client[db_name]
        return cls._instance

    def get_database(self):
        return self.db
    
    def is_connected(self):
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            return False

# Sử dụng
mongo_conn = MongoDBConnection(uri=os.getenv("MONGODB_CONN"), db_name=os.getenv("MONGODB_DATABASE"))
db = mongo_conn.get_database()

# Kiểm tra kết nối
if mongo_conn.is_connected():
    print("Kết nối MongoDB thành công!")
else:
    print("Không thể kết nối MongoDB.")