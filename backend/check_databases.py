from sqlmodel import Session, create_engine, select
from app.models.models import DatabaseMetadata
from app.config import settings

# Create engine with psycopg2 for synchronous access
engine = create_engine(settings.DATABASE_URL.replace('asyncpg', 'psycopg2'))

with Session(engine) as session:
    dbs = session.exec(select(DatabaseMetadata)).all()
    print(f'Found {len(dbs)} databases:')
    for db in dbs:
        print(f'  - {db.database_name} (id: {db.id})')
