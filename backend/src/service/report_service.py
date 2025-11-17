from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://root:example@localhost:27017")
db = client["testdb"]