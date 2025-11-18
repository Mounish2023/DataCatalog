# backend/app/ingest.py
"""
Simple ingestion: connects to a target DB URL, scans information_schema for tables matching name pattern,
and upserts them into the catalog tables/columns. Samples use LIMIT 5.
"""
from sqlalchemy import create_engine, text
from sqlmodel import Session, select
from app.models.models import Table as CatalogTable, ColumnMetadata as CatalogColumn
from datetime import datetime

def ingest_from_target(session: Session, target_db_url: str, schema: str = "public", name_like: str = "gold%"):
    engine = create_engine(target_db_url)
    with engine.connect() as conn:
        # get tables
        q = text("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = :schema AND table_name LIKE :like AND table_type='BASE TABLE'
        """)
        rows = conn.execute(q, {"schema": schema, "like": name_like}).fetchall()
        imported = []
        for r in rows:
            tschema, tname = r
            technical = f"{tschema}.{tname}"
            # upsert table
            existing = session.exec(select(CatalogTable).where(CatalogTable.technical_name == technical)).first()
            now = datetime.utcnow()
            if not existing:
                existing = CatalogTable(technical_name=technical, display_name=tname, description=None, created_at=now, updated_at=now)
                session.add(existing)
                session.commit()
            else:
                existing.updated_at = now
                session.add(existing)
                session.commit()

            # get columns
            cq = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :tname
                ORDER BY ordinal_position
            """)
            cols = conn.execute(cq, {"schema": schema, "tname": tname}).fetchall()
            for c in cols:
                cname, dtype, is_nullable = c
                existing_col = session.exec(select(CatalogColumn).where(CatalogColumn.table_id == existing.id).where(CatalogColumn.name == cname)).first()
                if not existing_col:
                    # collect sample values - basic
                    sample_q = text(f"SELECT {cname} FROM {tschema}.{tname} WHERE {cname} IS NOT NULL LIMIT 5")
                    try:
                        samples = [str(x[0]) for x in conn.execute(sample_q).fetchall()]
                    except Exception:
                        samples = []
                    col = CatalogColumn(table_id=existing.id, name=cname, data_type=dtype, is_nullable=(is_nullable == 'YES'), sample_values="|".join(samples))
                    session.add(col)
                    session.commit()
                else:
                    existing_col.data_type = dtype
                    existing_col.is_nullable = (is_nullable == 'YES')
                    existing_col.updated_at = now
                    session.add(existing_col)
                    session.commit()
            imported.append(technical)
    return imported
