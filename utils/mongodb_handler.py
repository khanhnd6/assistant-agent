from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

class MongoDBHandler:
    def __init__(self, connection_string, database_name):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            self.client.server_info()
            logging.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logging.error(f"Could not connect to MongoDB: {e}")
            raise

    def insert_document(self, collection_name, document):
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error inserting document: {e}")
            return None

    def find_documents(self, collection_name, query=None, limit=0):
        try:
            if query is None:
                query = {}
            collection = self.db[collection_name]
            cursor = collection.find(query).limit(limit)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error finding documents: {e}")
            return []

    def update_document(self, collection_name, query, update_data):
        try:
            collection = self.db[collection_name]
            result = collection.update_many(query, {"$set": update_data})
            return result.modified_count
        except Exception as e:
            logging.error(f"Error updating document: {e}")
            return 0

    def delete_document(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            result = collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logging.error(f"Error deleting document: {e}")
            return 0

    def close_connection(self):
        try:
            self.client.close()
            logging.info("MongoDB connection closed")
        except Exception as e:
            logging.error(f"Error closing connection: {e}")

