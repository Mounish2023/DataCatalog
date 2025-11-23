"""
Test script to verify that tables with the same name can exist in different databases
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.models import DatabaseMetadata, TableMetadata, TableType
from sqlalchemy import select


async def test_duplicate_table_names():
    """
    Test that we can create tables with the same name in different databases
    """
    async with AsyncSessionLocal() as session:
        try:
            # Create or get two test databases
            db1_name = "test_database_1"
            db2_name = "test_database_2"
            
            # Check if databases exist
            result = await session.execute(
                select(DatabaseMetadata).where(DatabaseMetadata.database_name == db1_name)
            )
            db1 = result.scalars().first()
            
            if not db1:
                db1 = DatabaseMetadata(
                    database_name=db1_name,
                    description="Test database 1 for duplicate table name testing"
                )
                session.add(db1)
                await session.flush()
                print(f"✅ Created database: {db1_name}")
            else:
                print(f"ℹ️  Database {db1_name} already exists (ID: {db1.id})")
            
            result = await session.execute(
                select(DatabaseMetadata).where(DatabaseMetadata.database_name == db2_name)
            )
            db2 = result.scalars().first()
            
            if not db2:
                db2 = DatabaseMetadata(
                    database_name=db2_name,
                    description="Test database 2 for duplicate table name testing"
                )
                session.add(db2)
                await session.flush()
                print(f"✅ Created database: {db2_name}")
            else:
                print(f"ℹ️  Database {db2_name} already exists (ID: {db2.id})")
            
            # Try to create tables with the same name in both databases
            test_table_name = "common_table_test"
            
            # Check if table already exists in db1
            result = await session.execute(
                select(TableMetadata).where(
                    TableMetadata.database_id == db1.id,
                    TableMetadata.technical_name == test_table_name
                )
            )
            table1 = result.scalars().first()
            
            if not table1:
                table1 = TableMetadata(
                    database_id=db1.id,
                    technical_name=test_table_name,
                    display_name="Common Table in DB1",
                    description="Test table with common name in database 1",
                    table_type=TableType.raw
                )
                session.add(table1)
                await session.flush()
                print(f"✅ Created table '{test_table_name}' in {db1_name}")
            else:
                print(f"ℹ️  Table '{test_table_name}' already exists in {db1_name}")
            
            # Check if table already exists in db2
            result = await session.execute(
                select(TableMetadata).where(
                    TableMetadata.database_id == db2.id,
                    TableMetadata.technical_name == test_table_name
                )
            )
            table2 = result.scalars().first()
            
            if not table2:
                table2 = TableMetadata(
                    database_id=db2.id,
                    technical_name=test_table_name,
                    display_name="Common Table in DB2",
                    description="Test table with common name in database 2",
                    table_type=TableType.raw
                )
                session.add(table2)
                await session.flush()
                print(f"✅ Created table '{test_table_name}' in {db2_name}")
            else:
                print(f"ℹ️  Table '{test_table_name}' already exists in {db2_name}")
            
            await session.commit()
            
            print("\n" + "="*60)
            print("✅ TEST PASSED: Tables with the same name can exist in different databases!")
            print("="*60)
            print(f"\nBoth databases now have a table named '{test_table_name}':")
            print(f"  - Database: {db1_name} (ID: {db1.id})")
            print(f"    Table ID: {table1.id}")
            print(f"  - Database: {db2_name} (ID: {db2.id})")
            print(f"    Table ID: {table2.id}")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print("\n" + "="*60)
            print(f"❌ TEST FAILED: {e}")
            print("="*60)
            return False


if __name__ == "__main__":
    success = asyncio.run(test_duplicate_table_names())
    exit(0 if success else 1)
