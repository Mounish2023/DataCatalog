"""
Migration script to fix table name uniqueness constraint
Changes technical_name from globally unique to unique per database
"""
import asyncio
from sqlalchemy import text
from app.database import engine
from app.utils.logger import logger


async def run_migration():
    """
    Drop the old unique constraint on technical_name and 
    add a composite unique constraint on (database_id, technical_name)
    """
    logger.info("Starting migration: fix_table_name_uniqueness")
    
    async with engine.begin() as conn:
        try:
            # Step 1: Drop the existing unique index/constraint on technical_name
            logger.info("Dropping old unique constraint on technical_name...")
            await conn.execute(text("""
                ALTER TABLE table_metadata 
                DROP CONSTRAINT IF EXISTS table_metadata_technical_name_key;
            """))
            
            # Also drop the index if it exists separately
            await conn.execute(text("""
                DROP INDEX IF EXISTS ix_table_metadata_technical_name;
            """))
            
            # Step 2: Recreate the index without unique constraint
            logger.info("Creating new index on technical_name...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_table_metadata_technical_name 
                ON table_metadata(technical_name);
            """))
            
            # Step 3: Add composite unique constraint
            logger.info("Adding composite unique constraint on (database_id, technical_name)...")
            await conn.execute(text("""
                ALTER TABLE table_metadata
                ADD CONSTRAINT uix_database_table 
                UNIQUE (database_id, technical_name);
            """))
            
            logger.info("Migration completed successfully!")
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            print(f"❌ Migration failed: {e}")
            raise


async def rollback_migration():
    """
    Rollback the migration - restore original constraints
    """
    logger.info("Rolling back migration: fix_table_name_uniqueness")
    
    async with engine.begin() as conn:
        try:
            # Drop composite constraint
            await conn.execute(text("""
                ALTER TABLE table_metadata
                DROP CONSTRAINT IF EXISTS uix_database_table;
            """))
            
            # Recreate unique constraint on technical_name
            await conn.execute(text("""
                ALTER TABLE table_metadata
                ADD CONSTRAINT table_metadata_technical_name_key 
                UNIQUE (technical_name);
            """))
            
            logger.info("Rollback completed successfully!")
            print("✅ Rollback completed successfully!")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            print(f"❌ Rollback failed: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Running migration rollback...")
        asyncio.run(rollback_migration())
    else:
        print("Running migration...")
        asyncio.run(run_migration())
