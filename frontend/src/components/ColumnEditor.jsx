// src/components/ColumnEditor.jsx
import { useState } from "react";
import { updateColumn } from "../api/api";

export default function ColumnEditor({ tableId, column, onUpdated }) {
  const [desc, setDesc] = useState(column.business_description || "");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = async () => {
    if (!desc.trim()) {
      setError("Description cannot be empty");
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      await updateColumn(tableId, column.id, {
        business_description: desc.trim(),
      });
      await onUpdated();
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating column:', err);
      setError(err.message || 'Failed to update column');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setDesc(column.business_description || "");
    setError(null);
    setIsEditing(false);
  };

  return (
    <div className="column-card">
      <div className="column-header">
        <h4>{column.name}</h4>
        <div className="column-meta">
          <span className="data-type">{column.data_type}</span>
          <span className={`nullable ${column.nullable ? 'yes' : 'no'}`}>
            {column.nullable ? 'Nullable' : 'Not Null'}
          </span>
        </div>
      </div>

      <div className="column-description">
        <label>Business Description:</label>
        {isEditing ? (
          <>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows="3"
              placeholder="Enter business description..."
              disabled={isSaving}
            />
            {error && <div className="error-message">{error}</div>}
          </>
        ) : (
          <div className="description-text" onClick={() => setIsEditing(true)}>
            {desc || <span className="placeholder">Click to add description</span>}
          </div>
        )}
      </div>

      <div className="column-actions">
        {isEditing ? (
          <>
            <button 
              onClick={handleSave} 
              disabled={isSaving}
              className="save-btn"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button 
              onClick={handleCancel} 
              disabled={isSaving}
              className="cancel-btn"
            >
              Cancel
            </button>
          </>
        ) : (
          <button 
            onClick={() => setIsEditing(true)}
            className="edit-btn"
          >
            Edit
          </button>
        )}
      </div>
    </div>
  );
}
