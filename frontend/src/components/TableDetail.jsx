// src/components/TableDetail.jsx
import { useEffect, useState } from "react";
import { fetchTable } from "../api/api";
import ColumnEditor from "./ColumnEditor";

export default function TableDetail({ tableId }) {
  const [table, setTable] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadTable = async () => {
      if (!tableId) return;
      
      try {
        setLoading(true);
        setError(null);
        const data = await fetchTable(tableId);
        setTable(data);
      } catch (err) {
        console.error(`Error loading table with ID ${tableId}:`, err);
        setError(`Failed to load table details. ${err.message}`);
        setTable(null);
      } finally {
        setLoading(false);
      }
    };

    loadTable();
  }, [tableId]);

  const handleColumnUpdated = async () => {
    try {
      const data = await fetchTable(tableId);
      setTable(data);
    } catch (err) {
      console.error('Error refreshing table:', err);
      setError('Failed to refresh table data.');
    }
  };

  if (!tableId) return <div className="empty-state">Select a table to view details</div>;
  if (loading) return <div>Loading table details...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!table) return <div>No table data available.</div>;

  return (
    <div className="table-detail">
      <div className="table-header">
        <h2>{table.display_name || table.name}</h2>
        {table.description && <p className="table-description">{table.description}</p>}
      </div>

      <div className="columns-section">
        <h3>Columns ({table.columns?.length || 0})</h3>
        {table.columns && table.columns.length > 0 ? (
          <div className="columns-grid">
            {table.columns.map((col) => (
              <ColumnEditor
                key={col.name}
                tableName={table.technical_name}
                column={col}
                onUpdated={handleColumnUpdated}
              />
            ))}
          </div>
        ) : (
          <p>No columns found for this table.</p>
        )}
      </div>
    </div>
  );
}
