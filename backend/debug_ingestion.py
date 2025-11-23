import asyncio
import os
import sys
import traceback
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.getcwd())

from app.config import settings
from app.services.metadata_ingestion import run_metadata_ingestion

async def main():
    print("Starting debug ingestion...")
    
    # Create engine and session
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        print("Session created. Running ingestion...")
        try:
            stats = await run_metadata_ingestion(
                catalog_session=session,
                target_connection_string=settings.DATABASE_URL,
                schema="public",
                table_pattern="%",
                enrich=True
            )
            print("Ingestion finished.")
            print("Stats:", stats)
        except Exception as e:
            with open("error.log", "w") as f:
                f.write(f"Error: {e}\n")
                traceback.print_exc(file=f)
            print("Error written to error.log")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
