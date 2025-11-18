// src/components/TableList.jsx
import { useEffect, useState } from "react";
import { fetchTables } from "../api/api";

export default function TableList({ onSelect, selectedTable }) {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadTables = async () => {
      try {
        setLoading(true);
        const data = await fetchTables();
        setTables(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load tables:', err);
        setError('Failed to load tables. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadTables();
  }, []);

  if (loading) return <div>Loading tables...</div>;
  if (error) return <div className="error">{error}</div>;
  if (tables.length === 0) return <div>No tables found.</div>;

  return (
    <div className="table-list">
      <h2>Gold Tables</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {tables.map((table) => (
          <li key={table.name} style={{ marginBottom: '8px' }}>
            <button
              onClick={() => onSelect(table.name)}
              className={`table-button ${selectedTable === table.name ? 'active' : ''}`}
            >
              {table.display_name || table.name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
