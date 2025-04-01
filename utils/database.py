from pymongo import MongoClient
from dotenv import load_dotenv
import os
import redis

load_dotenv()

class MongoDBConnection:
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_CONN")
        self.database_name = os.getenv("MONGODB_DATABASE")
        
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
    
    
class RedisCache:
    def __init__(self):
        host = os.getenv("REDIS_HOST")
        port = os.getenv("REDIS_PORT")
        username = os.getenv("REDIS_USERNAME")
        password = os.getenv("REDIS_PASSWORD")
        
        self.redis = redis.Redis(host=host, port=port, decode_responses=True, username=username, password=password)
        
    def set(self, key, value, ex = None):
        return self.redis.set(key, value, ex=ex)

    def get(self, key):
        return self.redis.get(key)