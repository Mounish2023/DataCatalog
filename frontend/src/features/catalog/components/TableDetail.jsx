import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchTable, updateTable, deleteTable } from "../../../services/api";
import ColumnEditor from "./ColumnEditor";
import styles from "./TableDetail.module.css";

export default function TableDetail({ tableId }) {
  const navigate = useNavigate();
  const [table, setTable] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("columns");
  const [deleting, setDeleting] = useState(false);

  // Editing state
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [editedDescription, setEditedDescription] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadTable = async () => {
      if (!tableId) return;

      try {
        setLoading(true);
        setError(null);
        const data = await fetchTable(tableId);
        setTable(data);
        setEditedDescription(data.description || "");
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
    }
  };

  const handleSaveDescription = async () => {
    try {
      setSaving(true);
      await updateTable(tableId, { description: editedDescription });

      // Update local state
      setTable(prev => ({ ...prev, description: editedDescription }));
      setIsEditingDescription(false);
    } catch (err) {
      console.error("Failed to update description:", err);
      alert("Failed to save description");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete the table "${table.display_name || table.technical_name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setDeleting(true);
      await deleteTable(tableId);

      // Navigate back to database view
      if (table.database?.id) {
        navigate(`/databases/${table.database.id}`);
      } else {
        navigate('/');
      }

      // Refresh the database list in sidebar
      if (window.refreshDatabases) {
        window.refreshDatabases();
      }
    } catch (err) {
      alert(`Failed to delete table: ${err.message}`);
      setDeleting(false);
    }
  };

  if (!tableId) return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>👆</div>
      <h3>Select a table to view details</h3>
      <p>Choose a table from the sidebar to view its schema and metadata.</p>
    </div>
  );

  if (loading) return <div className={styles.loading}>Loading table details...</div>;
  if (error) return <div className={styles.error}>{error}</div>;
  if (!table) return <div>No table data available.</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <h1 className={styles.title}>
            {table.display_name || table.technical_name}
          </h1>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <span className={`${styles.badge} ${table.status === 'active' ? styles.badgeActive : styles.badgeInactive}`}>
              {table.status || 'Active'}
            </span>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className={styles.deleteButton}
              title="Delete table"
            >
              {deleting ? '🗑️ Deleting...' : '🗑️ Delete'}
            </button>
          </div>
        </div>

        <div className={styles.metaGrid}>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Database</span>
            <span className={styles.metaValue}>{table.database?.name || 'Unknown'}</span>
          </div>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Type</span>
            <span className={styles.metaValue}>{table.table_type || 'Table'}</span>
          </div>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Owner</span>
            <span className={styles.metaValue}>{table.owner || 'Data Team'}</span>
          </div>
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Sensitivity</span>
            <span className={styles.metaValue}>{table.data_sensitivity || 'Internal'}</span>
          </div>
        </div>

        {/* Editable Description Section */}
        <div className={styles.descriptionSection}>
          <div className={styles.sectionHeader}>
            {!isEditingDescription && (
              <button
                onClick={() => setIsEditingDescription(true)}
                className={styles.editBtn}
              >
                Edit Description
              </button>
            )}
          </div>

          {isEditingDescription ? (
            <div className={styles.editContainer}>
              <textarea
                value={editedDescription}
                onChange={(e) => setEditedDescription(e.target.value)}
                className={styles.descriptionInput}
                rows={3}
              />
              <div className={styles.editActions}>
                <button
                  onClick={handleSaveDescription}
                  disabled={saving}
                  className={styles.saveBtn}
                >
                  {saving ? "Saving..." : "Save"}
                </button>
                <button
                  onClick={() => {
                    setIsEditingDescription(false);
                    setEditedDescription(table.description || "");
                  }}
                  disabled={saving}
                  className={styles.cancelBtn}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className={styles.description}>
              {table.description || "No description provided."}
            </div>
          )}
        </div>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'columns' ? styles.active : ''}`}
          onClick={() => setActiveTab('columns')}
        >
          Columns ({table.columns?.length || 0})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'details' ? styles.active : ''}`}
          onClick={() => setActiveTab('details')}
        >
          Business Context
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'lineage' ? styles.active : ''}`}
          onClick={() => setActiveTab('lineage')}
        >
          Lineage
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === 'columns' && (
          <div className={styles.tableWrapper}>
            <table className={styles.columnsTable}>
              <thead>
                <tr>
                  <th style={{ width: '25%' }}>Column</th>
                  <th style={{ width: '15%' }}>Type</th>
                  <th style={{ width: '10%' }}>Nullable</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {table.columns?.map((col) => (
                  <ColumnEditor
                    key={col.id || col.column_name}
                    tableId={table.id}
                    column={col}
                    onUpdated={handleColumnUpdated}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'details' && (
          <div className={styles.detailsTab}>
            <div className={styles.detailSection}>
              <h3>Business Purpose</h3>
              <p>{table.business_purpose || "No business purpose defined."}</p>
            </div>

            <div className={styles.detailSection}>
              <h3>Refresh Schedule</h3>
              <p>{table.refresh_frequency || "Daily"}</p>
            </div>

            <div className={styles.detailSection}>
              <h3>Timestamps</h3>
              <div className={styles.timestampGrid}>
                <div>Created: {new Date(table.created_at).toLocaleString()}</div>
                <div>Updated: {new Date(table.updated_at).toLocaleString()}</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'lineage' && (
          <div className={styles.lineagePlaceholder}>
            <p>Lineage visualization coming soon.</p>
          </div>
        )}
      </div>
    </div>
  );
}
