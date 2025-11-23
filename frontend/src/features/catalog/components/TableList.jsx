import { useEffect, useState } from "react";
import { fetchTables } from "../../../services/api";
import styles from "./TableList.module.css";

export default function TableList({ onSelect, selectedTable }) {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState("all"); // all, gold, silver, bronze

  useEffect(() => {
    const loadTables = async () => {
      try {
        setLoading(true);
        const data = await fetchTables();
        setTables(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load tables:', err);
        setError('Failed to load tables.');
      } finally {
        setLoading(false);
      }
    };

    loadTables();
  }, []);

  const filteredTables = tables.filter(table => {
    const matchesSearch = (table.display_name || table.technical_name).toLowerCase().includes(searchTerm.toLowerCase());
    // Assuming we might have a 'tier' or similar property later, for now just search
    return matchesSearch;
  });

  if (loading) return (
    <div className={styles.loadingContainer}>
      <div className={styles.spinner}></div>
      <p>Loading tables...</p>
    </div>
  );

  if (error) return (
    <div className={styles.errorContainer}>
      <p>{error}</p>
      <button onClick={() => window.location.reload()} className={styles.retryBtn}>Retry</button>
    </div>
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Tables</h2>
        <div className={styles.searchBox}>
          <span className={styles.searchIcon}>🔍</span>
          <input
            type="text"
            placeholder="Search tables..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className={styles.searchInput}
          />
        </div>
      </div>

      <div className={styles.list}>
        {filteredTables.length === 0 ? (
          <div className={styles.emptyState}>No tables found</div>
        ) : (
          filteredTables.map((table) => (
            <button
              key={table.id}
              onClick={() => onSelect(table.id)}
              className={`${styles.item} ${selectedTable === table.id ? styles.active : ''}`}
            >
              <div className={styles.itemIcon}>
                {table.table_type === 'view' ? '👁️' : '📅'}
              </div>
              <div className={styles.itemContent}>
                <div className={styles.itemName}>
                  {table.display_name || table.technical_name}
                </div>
                <div className={styles.itemMeta}>
                  {table.schema || 'public'} • {table.row_count?.toLocaleString() || 0} rows
                </div>
              </div>
              {selectedTable === table.id && <div className={styles.activeIndicator} />}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
