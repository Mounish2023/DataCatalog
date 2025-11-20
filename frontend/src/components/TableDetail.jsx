// src/components/TableDetail.jsx
import { useEffect, useState } from "react";
import { fetchTable } from "../api/api";
import ColumnEditor from "./ColumnEditor";
import styles from "./TableDetail.module.css";

export default function TableDetail({ tableId }) {
  const [table, setTable] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("columns");

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

  if (!tableId) return <div className={styles.emptyState}>Select a table to view details</div>;
  if (loading) return <div className={styles.loading}>Loading table details...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!table) return <div>No table data available.</div>;

  return (
    <div className={styles.tableDetail}>
      <div className={styles.header}>
        <h2 className={styles.tableTitle}>
          {table.display_name || table.technical_name}
          {table.status && (
            <span className={`${styles.badge} ${table.status === 'active' ? styles.active : styles.inactive}`}>
              {table.status}
            </span>
          )}
        </h2>
        
        <div className={styles.metadata}>
          {table.database?.name && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Database:</span>
              <span>{table.database.name}</span>
            </div>
          )}
          {table.table_type && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Type:</span>
              <span>{table.table_type}</span>
            </div>
          )}
          {table.owner && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Owner:</span>
              <span>{table.owner}</span>
            </div>
          )}
          {table.data_sensitivity && (
            <div className={styles.metadataItem}>
              <span className={styles.metadataLabel}>Sensitivity:</span>
              <span>{table.data_sensitivity}</span>
            </div>
          )}
        </div>
      </div>

      <div className={styles.tabs}>
        <button 
          className={`${styles.tab} ${activeTab === 'columns' ? styles.active : ''}`}
          onClick={() => setActiveTab('columns')}
        >
          Columns
        </button>
        <button 
          className={`${styles.tab} ${activeTab === 'details' ? styles.active : ''}`}
          onClick={() => setActiveTab('details')}
        >
          Details
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === 'columns' && (
          <>
            {table.description && (
              <div style={{ padding: '12px', background: '#252526', borderBottom: '1px solid #333' }}>
                <p style={{ margin: 0, color: '#d4d4d4' }}>{table.description}</p>
              </div>
            )}
            
            {table.columns && table.columns.length > 0 ? (
              <table className={styles.columnsTable}>
                <thead>
                  <tr className={styles.columnHeader}>
                    <th style={{ width: '25%' }}>Name</th>
                    <th style={{ width: '15%' }}>Type</th>
                    <th style={{ width: '10%' }}>Nullable</th>
                    <th>Description</th>
                    <th style={{ width: '60px' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {table.columns.map((col) => (
                    <ColumnEditor
                      key={col.id || col.column_name}
                      tableId={table.id}
                      column={col}
                      onUpdated={handleColumnUpdated}
                    />
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ padding: '16px', color: '#858585' }}>No columns found for this table.</div>
            )}
          </>
        )}

        {activeTab === 'details' && (
          <div style={{ padding: '16px' }}>
            {table.business_purpose && (
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ marginTop: 0 }}>Business Purpose</h4>
                <p>{table.business_purpose}</p>
              </div>
            )}
            
            <div className={styles.metadata}>
              {table.refresh_frequency && (
                <div className={styles.metadataItem}>
                  <span className={styles.metadataLabel}>Refresh Frequency:</span>
                  <span>{table.refresh_frequency}</span>
                </div>
              )}
              {table.created_at && (
                <div className={styles.metadataItem}>
                  <span className={styles.metadataLabel}>Created:</span>
                  <span>{new Date(table.created_at).toLocaleString()}</span>
                </div>
              )}
              {table.updated_at && (
                <div className={styles.metadataItem}>
                  <span className={styles.metadataLabel}>Updated:</span>
                  <span>{new Date(table.updated_at).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
