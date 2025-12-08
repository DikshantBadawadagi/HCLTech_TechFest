from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None
    fs_bucket = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGO_URI)
        db.db = db.client[settings.DB_NAME]
        db.fs_bucket = AsyncIOMotorGridFSBucket(db.db)
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB: {settings.DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection")

def get_database():
    """Get database instance"""
    return db.db

def get_fs_bucket():
    """Get GridFS bucket for large file storage"""
    return db.fs_bucket