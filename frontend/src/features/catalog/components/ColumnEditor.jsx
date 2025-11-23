import { useState } from "react";
import { updateColumn } from "../../../services/api";
import styles from "./ColumnEditor.module.css";

export default function ColumnEditor({ tableId, column, onUpdated }) {
  const [desc, setDesc] = useState(column.description || "");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = async () => {
    if (!desc.trim()) return;

    try {
      setIsSaving(true);
      setError(null);
      await updateColumn(tableId, column.id, {
        description: desc.trim(),
      });
      await onUpdated();
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating column:', err);
      setError(err.message || 'Failed to update');
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      setDesc(column.description || "");
      setIsEditing(false);
    }
  };

  return (
    <tr className={styles.row}>
      <td className={styles.nameCell}>
        <div className={styles.nameWrapper}>
          <span className={styles.columnName}>{column.column_name}</span>
          <div className={styles.badges}>
            {column.is_primary_key && <span className={`${styles.badge} ${styles.pk}`}>PK</span>}
            {column.is_foreign_key && <span className={`${styles.badge} ${styles.fk}`}>FK</span>}
            {column.is_pii && <span className={`${styles.badge} ${styles.pii}`}>PII</span>}
          </div>
        </div>
      </td>
      <td className={styles.typeCell}>
        <code className={styles.dataType}>{column.data_type}</code>
      </td>
      <td className={styles.nullableCell}>
        {column.nullable ? (
          <span className={styles.nullBadge}>NULL</span>
        ) : (
          <span className={styles.notNullBadge}>REQ</span>
        )}
      </td>
      <td className={styles.descCell}>
        {isEditing ? (
          <div className={styles.editContainer}>
            <textarea
              className={styles.textarea}
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              placeholder="Add a description..."
              autoFocus
            />
            <div className={styles.actions}>
              <button
                className={styles.saveBtn}
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? '...' : 'Save'}
              </button>
              <button
                className={styles.cancelBtn}
                onClick={() => {
                  setDesc(column.description || "");
                  setIsEditing(false);
                }}
              >
                Cancel
              </button>
            </div>
            {error && <div className={styles.error}>{error}</div>}
          </div>
        ) : (
          <div
            className={styles.descDisplay}
            onClick={() => setIsEditing(true)}
            title="Click to edit"
          >
            {desc ? (
              <span className={styles.descText}>{desc}</span>
            ) : (
              <span className={styles.placeholder}>Add description...</span>
            )}
            <span className={styles.editIcon}>✏️</span>
          </div>
        )}
      </td>
    </tr>
  );
}
