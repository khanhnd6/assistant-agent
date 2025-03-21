from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class MongoDBConnection:
    def __init__(self, connection_string=None, database_name=None):
        self.connection_string = connection_string or os.getenv("MONGODB_CONN")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE")
        
        if not self.connection_string or not self.database_name:
            raise ValueError("MongoDB connection string or database name not provided and not found in environment variables")
        
        self.client = None
        self.db = None
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.client.server_info()
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def close_connection(self):
        try:
            if self.client:
                self.client.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
    
    def get_database(self):
        return self.db

# Sử dụng
# mongo_conn = MongoDBConnection(uri=os.getenv("MONGODB_CONN"), db_name=os.getenv("MONGODB_DATABASE"))
# db = mongo_conn.get_database()
