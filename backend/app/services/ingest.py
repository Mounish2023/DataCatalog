# backend/app/ingest.py
"""
Simple ingestion: connects to a target DB URL, scans information_schema for tables matching name pattern,
and upserts them into the catalog tables/columns. Samples use LIMIT 5.
"""
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Table as CatalogTable, ColumnMetadata as CatalogColumn
from datetime import datetime

async def ingest_from_target(session: AsyncSession, target_db_url: str, schema: str = "public", name_like: str = "gold%"):
    # For the target database, we'll use a synchronous connection since we're just querying
    # information_schema and don't need async for this part
    from sqlalchemy import create_engine
    engine = create_engine(target_db_url.replace("postgresql+asyncpg://", "postgresql://"))
    
    with engine.connect() as conn:
        # get tables
        q = text("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = :schema AND table_name LIKE :like AND table_type='BASE TABLE'
        """)
        result = conn.execute(q, {"schema": schema, "like": name_like})
        rows = result.fetchall()
        imported = []
        
        for r in rows:
            tschema, tname = r
            technical = f"{tschema}.{tname}"
            # upsert table - using async session
            result = await session.execute(select(CatalogTable).where(CatalogTable.technical_name == technical))
            existing = result.scalars().first()
            now = datetime.utcnow()
            if not existing:
                existing = CatalogTable(technical_name=technical, display_name=tname, description=None, created_at=now, updated_at=now)
                session.add(existing)
                await session.commit()
            else:
                existing.updated_at = now
                session.add(existing)
                await session.commit()

            # get columns
            q = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
            """)
            result = conn.execute(q, {"schema": tschema, "table": tname})
            cols = result.fetchall()

            # Sample data
            sample_q = text(f'SELECT * FROM \"{tschema}\".\"{tname}\" LIMIT 5')
            try:
                sample_result = conn.execute(sample_q)
                sample_rows = sample_result.fetchall()
                sample_values = {}
                if sample_rows:
                    for i, col in enumerate(cols):
                        col_name = col[0]
                        sample_values[col_name] = [str(row[i]) if row[i] is not None else None for row in sample_rows]
            except Exception as e:
                print(f"Error sampling data from {tschema}.{tname}: {e}")
                sample_values = {}

            # upsert columns
            for col in cols:
                col_name, data_type, is_nullable, col_default = col
                col_result = await session.execute(
                    select(CatalogColumn)
                    .where(CatalogColumn.table_id == existing.id)
                    .where(CatalogColumn.name == col_name)
                )
                existing_col = col_result.scalars().first()

                sample_vals = "|".join(str(v) for v in sample_values.get(col_name, []) if v is not None) if col_name in sample_values and sample_values[col_name] else None

                if not existing_col:
                    col_obj = CatalogColumn(
                        table_id=existing.id,
                        name=col_name,
                        data_type=data_type,
                        is_nullable=is_nullable == 'YES',
                        default_value=str(col_default) if col_default else None,
                        sample_values=sample_vals,
                        created_at=now,
                        updated_at=now
                    )
                    session.add(col_obj)
                else:
                    existing_col.data_type = data_type
                    existing_col.is_nullable = is_nullable == 'YES'
                    existing_col.default_value = str(col_default) if col_default else None
                    existing_col.sample_values = sample_vals
                    existing_col.updated_at = now
                    session.add(existing_col)
                
                await session.commit()

            imported.append(technical)

    await session.commit()
    return imported
