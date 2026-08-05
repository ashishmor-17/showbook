from showbook_common.database import db_manager

async def get_db():
    async with db_manager.get_db_context() as session:
        yield session
