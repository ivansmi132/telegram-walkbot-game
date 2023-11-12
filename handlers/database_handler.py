import logging
from pymongo import MongoClient
import pymongo

# Import the logger from the main module
logger = logging.getLogger(__name__)

"""
Schema
{
    'chat_id',
    'first_name',
    'score',
}
"""


class MongoDBHandler:
    def __init__(self, connection_string, database_name, collection_name):
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

    def create_user(self, chat_id, user_name):
        # check if the thing exists
        existing_document = self.collection.find_one({"chat_id": chat_id})
        if existing_document is None:
            item = {'chat_id': chat_id, 'user_name': user_name, 'score': 0}
            result = self.collection.insert_one(item)
            # Logging the action
            logger.info(f"database> Item inserted with ID: {result.inserted_id}")
        else:
            logger.info(f"database> User already existed")

    def find_by_id(self, chat_id):
        query = {'chat_id': chat_id}
        result = self.collection.find_one(query)
        logger.info(f"database> fetched item={result}")
        return result

    def find_score(self, chat_id):
        query = {'chat_id': chat_id}
        result = self.collection.find_one(query)
        logger.info(f"database> user: {result['user_name']!r} fetched score: {result['score']}")
        return result['score']

    def score_increment(self, chat_id, increment_value):
        query = {"chat_id": chat_id}
        update = {"$inc": {"score": increment_value}}
        result = self.collection.update_one(query, update, upsert=True)
        logger.info(f"Matched {result.matched_count} document(s) and modified {result.modified_count} document(s)")

    def find_top_three(self):
        temp = self.collection.find()
        temp.sort("score", pymongo.DESCENDING).limit(3)
        return [(person['user_name'], person['score']) for person in list(temp)]
