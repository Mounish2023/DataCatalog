# backend/app/services/metadata_ingestion.py
"""
Async Metadata Ingestion Pipeline with GPT-4o Enrichment
Extracts schema from target Postgres DB and enriches with semantic metadata
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from datetime import datetime
import json
import os

from app.models.models import (
    DatabaseMetadata, 
    TableMetadata, 
    ColumnMetadata,
    TableType,
    Sensitivity
)
from app.utils.logger import logger

# OpenAI client setup
try:
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    logger.warning("OpenAI package not installed. GPT enrichment will be disabled.")
    openai_client = None


class SchemaExtractor:
    """Extracts raw schema information from target database"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # Create sync engine for inspection
        sync_url = connection_string.replace("postgresql+asyncpg://", "postgresql://")
        self.sync_engine = create_engine(sync_url)
        
    async def extract_database_info(self, schema: str = "public") -> Dict:
        """Extract high-level database information"""
        with self.sync_engine.connect() as conn:
            # Get database name
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            
            # Get total table count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = :schema AND table_type = 'BASE TABLE'
            """), {"schema": schema})
            table_count = result.scalar()
            
            return {
                "database_name": db_name,
                "schema": schema,
                "table_count": table_count
            }
    
    async def extract_tables(
        self, 
        schema: str = "public", 
        name_pattern: str = "%"
    ) -> List[Dict]:
        """Extract table-level metadata"""
        tables = []
        
        with self.sync_engine.connect() as conn:
            # Get all tables matching pattern
            query = text("""
                SELECT 
                    table_name,
                    table_schema,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = :schema 
                    AND table_name LIKE :pattern
                    AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            result = conn.execute(query, {"schema": schema, "pattern": name_pattern})
            
            for row in result:
                table_name = row[0]
                
                # Get row count estimate
                try:
                    count_query = text(f"""
                        SELECT reltuples::bigint AS estimate
                        FROM pg_class
                        WHERE relname = :table_name
                    """)
                    count_result = conn.execute(count_query, {"table_name": table_name})
                    row_count = count_result.scalar() or 0
                except Exception as e:
                    logger.warning(f"Could not get row count for {table_name}: {e}")
                    row_count = 0
                
                # Get table comment if exists
                try:
                    comment_query = text("""
                        SELECT obj_description(
                            (quote_ident(:schema) || '.' || quote_ident(:table_name))::regclass,
                            'pg_class'
                        )
                    """)
                    comment_result = conn.execute(
                        comment_query, 
                        {"schema": schema, "table_name": table_name}
                    )
                    table_comment = comment_result.scalar()
                except Exception:
                    table_comment = None
                
                tables.append({
                    "table_name": table_name,
                    "schema": schema,
                    "technical_name": f"{schema}.{table_name}",
                    "row_count": row_count,
                    "existing_comment": table_comment
                })
        
        return tables
    
    async def extract_columns(
        self, 
        schema: str, 
        table_name: str
    ) -> List[Dict]:
        """Extract column-level metadata including sample values"""
        columns = []
        
        with self.sync_engine.connect() as conn:
            # Get column information
            column_query = text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    udt_name
                FROM information_schema.columns
                WHERE table_schema = :schema 
                    AND table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            result = conn.execute(
                column_query, 
                {"schema": schema, "table_name": table_name}
            )
            
            for row in result:
                column_name = row[0]
                data_type = row[1]
                is_nullable = row[2] == 'YES'
                default_value = row[3]
                
                # Get sample values (up to 5 distinct, non-null)
                try:
                    sample_query = text(f"""
                        SELECT DISTINCT "{column_name}"::text
                        FROM "{schema}"."{table_name}"
                        WHERE "{column_name}" IS NOT NULL
                        LIMIT 5
                    """)
                    sample_result = conn.execute(sample_query)
                    sample_values = [r[0] for r in sample_result if r[0]]
                except Exception as e:
                    logger.warning(f"Could not get samples for {table_name}.{column_name}: {e}")
                    sample_values = []
                
                # Get cardinality estimate
                try:
                    cardinality_query = text(f"""
                        SELECT COUNT(DISTINCT "{column_name}") as distinct_count,
                               COUNT(*) as total_count
                        FROM "{schema}"."{table_name}"
                    """)
                    card_result = conn.execute(cardinality_query)
                    card_row = card_result.fetchone()
                    distinct_count = card_row[0] if card_row else 0
                    total_count = card_row[1] if card_row else 0
                    
                    # Classify cardinality
                    if total_count == 0:
                        cardinality = "empty"
                    elif distinct_count == total_count:
                        cardinality = "unique"
                    elif distinct_count < 10:
                        cardinality = "low"
                    elif distinct_count < 100:
                        cardinality = "medium"
                    else:
                        cardinality = "high"
                except Exception:
                    cardinality = "unknown"
                
                columns.append({
                    "column_name": column_name,
                    "data_type": data_type,
                    "is_nullable": is_nullable,
                    "default_value": str(default_value) if default_value else None,
                    "sample_values": sample_values,
                    "cardinality": cardinality,
                    "distinct_count": distinct_count if 'distinct_count' in locals() else None
                })
        
        return columns
    
    async def get_table_relationships(
        self, 
        schema: str, 
        table_name: str
    ) -> Dict[str, List[str]]:
        """Extract foreign key relationships"""
        relationships = {"foreign_keys": [], "referenced_by": []}
        
        with self.sync_engine.connect() as conn:
            # Get foreign keys FROM this table
            fk_query = text("""
                SELECT
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = :schema
                    AND tc.table_name = :table_name
            """)
            
            result = conn.execute(fk_query, {"schema": schema, "table_name": table_name})
            for row in result:
                relationships["foreign_keys"].append(
                    f"{row[0]} -> {row[1]}.{row[2]}.{row[3]}"
                )
            
            # Get foreign keys TO this table
            ref_query = text("""
                SELECT
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND ccu.table_schema = :schema
                    AND ccu.table_name = :table_name
            """)
            
            result = conn.execute(ref_query, {"schema": schema, "table_name": table_name})
            for row in result:
                relationships["referenced_by"].append(
                    f"{row[0]}.{row[1]}.{row[2]}"
                )
        
        return relationships


class GPTEnricher:
    """Enriches metadata using GPT-4o"""
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.client = openai_client
    
    async def enrich_database(self, db_info: Dict) -> Dict:
        """Enrich database-level metadata"""
        if not self.client:
            logger.warning("OpenAI client not available, skipping enrichment")
            return {
                "business_domain": "Unknown",
                "description": f"Database: {db_info['database_name']}",
                "sensitivity": Sensitivity.internal
            }
        
        prompt = f"""Analyze this database and provide semantic metadata:

Database Name: {db_info['database_name']}
Schema: {db_info['schema']}
Table Count: {db_info['table_count']}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
    "business_domain": "Primary business domain (e.g., Sales, Finance, Operations)",
    "description": "2-3 sentence description of database purpose",
    "sensitivity": "internal|confidential|pii|public"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data catalog expert. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Convert sensitivity string to enum
            sensitivity_map = {
                "internal": Sensitivity.internal,
                "confidential": Sensitivity.confidential,
                "pii": Sensitivity.pii,
                "public": Sensitivity.public
            }
            result["sensitivity"] = sensitivity_map.get(
                result.get("sensitivity", "internal").lower(),
                Sensitivity.internal
            )
            
            return result
            
        except Exception as e:
            logger.error(f"GPT enrichment failed for database: {e}")
            return {
                "business_domain": "Unknown",
                "description": f"Database: {db_info['database_name']}",
                "sensitivity": Sensitivity.internal
            }
    
    async def enrich_table(
        self, 
        table_info: Dict, 
        columns: List[Dict],
        relationships: Dict
    ) -> Dict:
        """Enrich table-level metadata"""
        if not self.client:
            return self._fallback_table_enrichment(table_info)
        
        # Prepare column summary
        column_summary = [
            f"{col['column_name']} ({col['data_type']})" 
            for col in columns[:15]  # Limit to avoid token limits
        ]
        
        prompt = f"""Analyze this database table and provide semantic metadata:

Table: {table_info['technical_name']}
Row Count: {table_info['row_count']:,}
Columns: {', '.join(column_summary)}
Foreign Keys: {', '.join(relationships.get('foreign_keys', [])[:5])}
Referenced By: {', '.join(relationships.get('referenced_by', [])[:5])}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
    "display_name": "User-friendly table name",
    "description": "2-3 sentence description of table purpose",
    "table_type": "fact|dimension|reference|staging|raw|view",
    "business_purpose": "How this table supports business operations",
    "sensitivity": "internal|confidential|pii|public"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data catalog expert. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Convert enums
            table_type_map = {
                "fact": TableType.fact,
                "dimension": TableType.dimension,
                "reference": TableType.reference,
                "staging": TableType.staging,
                "raw": TableType.raw,
                "view": TableType.view
            }
            result["table_type"] = table_type_map.get(
                result.get("table_type", "raw").lower(),
                TableType.raw
            )
            
            sensitivity_map = {
                "internal": Sensitivity.internal,
                "confidential": Sensitivity.confidential,
                "pii": Sensitivity.pii,
                "public": Sensitivity.public
            }
            result["sensitivity"] = sensitivity_map.get(
                result.get("sensitivity", "internal").lower(),
                Sensitivity.internal
            )
            
            return result
            
        except Exception as e:
            logger.error(f"GPT enrichment failed for table {table_info['table_name']}: {e}")
            return self._fallback_table_enrichment(table_info)
    
    def _fallback_table_enrichment(self, table_info: Dict) -> Dict:
        """Fallback enrichment when GPT is unavailable"""
        table_name = table_info['table_name']
        return {
            "display_name": table_name.replace("_", " ").title(),
            "description": f"Table: {table_name}",
            "table_type": TableType.raw,
            "business_purpose": f"Data storage for {table_name}",
            "sensitivity": Sensitivity.internal
        }
    
    async def enrich_column(
        self, 
        column_info: Dict,
        table_context: str
    ) -> Dict:
        """Enrich column-level metadata"""
        if not self.client:
            return self._fallback_column_enrichment(column_info)
        
        # Format sample values
        samples_str = ", ".join(str(v) for v in column_info['sample_values'][:5])
        
        prompt = f"""Analyze this database column and provide semantic metadata:

Table Context: {table_context}
Column: {column_info['column_name']}
Data Type: {column_info['data_type']}
Nullable: {column_info['is_nullable']}
Cardinality: {column_info['cardinality']}
Sample Values: {samples_str}

Respond with ONLY valid JSON (no markdown, no explanation):
{{
    "description": "Clear 1-2 sentence description of what this column represents",
    "is_pii": true|false,
    "valid_values": "Description of valid values or range (if applicable)",
    "downstream_usage": "How analytics/reports typically use this column"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data catalog expert. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"GPT enrichment failed for column {column_info['column_name']}: {e}")
            return self._fallback_column_enrichment(column_info)
    
    def _fallback_column_enrichment(self, column_info: Dict) -> Dict:
        """Fallback enrichment when GPT is unavailable"""
        return {
            "description": f"Column: {column_info['column_name']} ({column_info['data_type']})",
            "is_pii": False,
            "valid_values": None,
            "downstream_usage": "General purpose column"
        }


class MetadataIngestionPipeline:
    """Main orchestrator for metadata ingestion"""
    
    def __init__(
        self, 
        catalog_session: AsyncSession,
        target_connection_string: str
    ):
        self.catalog_session = catalog_session
        self.extractor = SchemaExtractor(target_connection_string)
        self.enricher = GPTEnricher()
    
    async def ingest_database(
        self,
        schema: str = "public",
        table_pattern: str = "%",
        enrich: bool = True
    ) -> Dict:
        """
        Main ingestion method - extracts and enriches metadata
        
        Args:
            schema: Target schema to ingest
            table_pattern: SQL LIKE pattern for table names
            enrich: Whether to use GPT enrichment
        
        Returns:
            Dict with ingestion summary
        """
        logger.info(f"Starting metadata ingestion for schema: {schema}, pattern: {table_pattern}")
        
        start_time = datetime.utcnow()
        stats = {
            "databases_processed": 0,
            "tables_processed": 0,
            "columns_processed": 0,
            "errors": []
        }
        
        try:
            # Step 1: Extract and upsert database metadata
            db_info = await self.extractor.extract_database_info(schema)
            database_id = await self._upsert_database(db_info, enrich)
            stats["databases_processed"] = 1
            
            # Step 2: Extract tables
            tables = await self.extractor.extract_tables(schema, table_pattern)
            logger.info(f"Found {len(tables)} tables matching pattern")
            
            # Step 3: Process each table
            for table_info in tables:
                try:
                    await self._process_table(
                        database_id, 
                        table_info, 
                        enrich
                    )
                    stats["tables_processed"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing table {table_info['table_name']}: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Commit all changes
            await self.catalog_session.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            stats["duration_seconds"] = duration
            
            logger.info(f"Ingestion complete: {stats}")
            return stats
            
        except Exception as e:
            await self.catalog_session.rollback()
            logger.error(f"Ingestion failed: {e}")
            raise
    
    async def _upsert_database(
        self, 
        db_info: Dict, 
        enrich: bool
    ) -> str:
        """Upsert database metadata"""
        db_name = db_info["database_name"]
        
        # Check if exists
        result = await self.catalog_session.execute(
            select(DatabaseMetadata).where(
                DatabaseMetadata.database_name == db_name
            )
        )
        db_record = result.scalars().first()
        
        # Enrich if enabled
        enriched = {}
        if enrich:
            enriched = await self.enricher.enrich_database(db_info)
        
        now = datetime.utcnow()
        
        if db_record:
            # Update existing
            db_record.description = enriched.get("description", db_record.description)
            db_record.business_domain = enriched.get("business_domain", db_record.business_domain)
            db_record.sensitivity = enriched.get("sensitivity", db_record.sensitivity)
            db_record.updated_at = now
            
            logger.info(f"Updated database: {db_name}")
        else:
            # Create new
            db_record = DatabaseMetadata(
                database_name=db_name,
                business_domain=enriched.get("business_domain", "Unknown"),
                description=enriched.get("description", f"Database: {db_name}"),
                sensitivity=enriched.get("sensitivity", Sensitivity.internal),
                created_at=now,
                updated_at=now
            )
            self.catalog_session.add(db_record)
            
            logger.info(f"Created database: {db_name}")
        
        await self.catalog_session.flush()
        return str(db_record.id)
    
    async def _process_table(
        self, 
        database_id: str,
        table_info: Dict, 
        enrich: bool
    ):
        """Process a single table with columns"""
        table_name = table_info["technical_name"]
        schema = table_info["schema"]
        base_name = table_info["table_name"]
        
        # Extract columns and relationships
        columns = await self.extractor.extract_columns(schema, base_name)
        relationships = await self.extractor.get_table_relationships(schema, base_name)
        
        # Enrich table metadata
        enriched_table = {}
        if enrich:
            enriched_table = await self.enricher.enrich_table(
                table_info, 
                columns, 
                relationships
            )
        
        # Upsert table
        table_id = await self._upsert_table(
            database_id,
            table_info,
            enriched_table,
            relationships
        )
        
        # Process columns
        for column_info in columns:
            try:
                await self._upsert_column(
                    table_id,
                    column_info,
                    table_name,
                    enrich
                )
                
            except Exception as e:
                logger.error(f"Error processing column {column_info['column_name']}: {e}")
        
        logger.info(f"Processed table: {table_name} ({len(columns)} columns)")
    
    async def _upsert_table(
        self,
        database_id: str,
        table_info: Dict,
        enriched: Dict,
        relationships: Dict
    ) -> str:
        """Upsert table metadata"""
        technical_name = table_info["technical_name"]
        
        # Check if exists
        result = await self.catalog_session.execute(
            select(TableMetadata).where(
                TableMetadata.technical_name == technical_name
            )
        )
        table_record = result.scalars().first()
        
        # Prepare foreign keys text
        fk_text = "\n".join(relationships.get("foreign_keys", []))
        
        now = datetime.utcnow()
        
        if table_record:
            # Update existing
            table_record.display_name = enriched.get("display_name", table_record.display_name)
            table_record.description = enriched.get("description", table_record.description)
            table_record.table_type = enriched.get("table_type", table_record.table_type)
            table_record.business_purpose = enriched.get("business_purpose", table_record.business_purpose)
            table_record.data_sensitivity = enriched.get("sensitivity", table_record.data_sensitivity)
            table_record.foreign_keys = fk_text
            table_record.updated_at = now
            
        else:
            # Create new
            table_record = TableMetadata(
                database_id=database_id,
                technical_name=technical_name,
                display_name=enriched.get("display_name", table_info["table_name"]),
                description=enriched.get("description", f"Table: {table_info['table_name']}"),
                table_type=enriched.get("table_type", TableType.raw),
                business_purpose=enriched.get("business_purpose"),
                data_sensitivity=enriched.get("sensitivity", Sensitivity.internal),
                foreign_keys=fk_text,
                created_at=now,
                updated_at=now
            )
            self.catalog_session.add(table_record)
        
        await self.catalog_session.flush()
        return str(table_record.id)
    
    async def _upsert_column(
        self,
        table_id: str,
        column_info: Dict,
        table_context: str,
        enrich: bool
    ) -> str:
        """Upsert column metadata"""
        column_name = column_info["column_name"]
        
        # Check if exists
        result = await self.catalog_session.execute(
            select(ColumnMetadata).where(
                ColumnMetadata.table_id == table_id,
                ColumnMetadata.column_name == column_name
            )
        )
        column_record = result.scalars().first()
        
        # Enrich column metadata
        enriched = {}
        if enrich:
            enriched = await self.enricher.enrich_column(column_info, table_context)
        
        # Format sample values
        example_value = column_info['sample_values'][0] if column_info['sample_values'] else None
        valid_values_text = ", ".join(str(v) for v in column_info['sample_values'][:10])
        
        now = datetime.utcnow()
        
        if column_record:
            # Update existing
            column_record.data_type = column_info["data_type"]
            column_record.description = enriched.get("description", column_record.description)
            column_record.is_nullable = column_info["is_nullable"]
            column_record.is_pii = enriched.get("is_pii", column_record.is_pii)
            column_record.cardinality = column_info["cardinality"]
            column_record.valid_values = enriched.get("valid_values") or valid_values_text
            column_record.example_value = str(example_value) if example_value else None
            column_record.downstream_usage = enriched.get("downstream_usage", column_record.downstream_usage)
            column_record.updated_at = now
            
        else:
            # Create new
            column_record = ColumnMetadata(
                table_id=table_id,
                column_name=column_name,
                data_type=column_info["data_type"],
                description=enriched.get("description", f"Column: {column_name}"),
                is_nullable=column_info["is_nullable"],
                is_pii=enriched.get("is_pii", False),
                cardinality=column_info["cardinality"],
                valid_values=enriched.get("valid_values") or valid_values_text,
                example_value=str(example_value) if example_value else None,
                downstream_usage=enriched.get("downstream_usage"),
                created_at=now,
                updated_at=now
            )
            self.catalog_session.add(column_record)
        
        await self.catalog_session.flush()
        return str(column_record.id)


# Convenience function for external use
async def run_metadata_ingestion(
    catalog_session: AsyncSession,
    target_connection_string: str,
    schema: str = "public",
    table_pattern: str = "%",
    enrich: bool = True
) -> Dict:
    """
    Run the metadata ingestion pipeline
    
    Usage:
        stats = await run_metadata_ingestion(
            catalog_session=session,
            target_connection_string="postgresql://...",
            schema="public",
            table_pattern="gold_%",
            enrich=True
        )
    """
    pipeline = MetadataIngestionPipeline(
        catalog_session=catalog_session,
        target_connection_string=target_connection_string
    )
    
    return await pipeline.ingest_database(
        schema=schema,
        table_pattern=table_pattern,
        enrich=enrich
    )
