from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
DATABASE = 'palabra_y_menoscabo.db'
DATABASE_URL = f"sqlite+aiosqlite:///./{DATABASE}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
