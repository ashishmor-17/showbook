from showbook_common.database import db_manager
from app.core.config import settings

db_manager.init(
    database_url=settings.DATABASE_URL.get_secret_value(),
    testing=settings.TESTING
)

async def get_db():
    async with db_manager.get_db_context() as session:
        yield session
