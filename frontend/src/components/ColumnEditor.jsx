// src/components/ColumnEditor.jsx
import { useState } from "react";
import { updateColumn } from "../api/api";

export default function ColumnEditor({ tableId, column, onUpdated }) {
  const [desc, setDesc] = useState(column.description || "");
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
        description: desc.trim(),
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
    setDesc(column.description || "");
    setError(null);
    setIsEditing(false);
  };

  return (
    <div className="column-row">
      <div className="column-name">
        {column.name}
        {column.is_primary_key && <span className="column-badge primary">PK</span>}
        {column.is_foreign_key && <span className="column-badge foreign">FK</span>}
        {column.is_pii && <span className="column-badge pii">PII</span>}
      </div>
      <div className="column-type">
        {column.data_type}
        {column.nullable ? ' NULL' : ' NOT NULL'}
      </div>
      <div className="column-nullable">
        {column.nullable ? '✓' : '✗'}
      </div>
      
      <div className="column-description">
        {isEditing ? (
          <>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows="2"
              placeholder="Enter column description..."
            />
            <div className="form-actions">
              <button 
                className="btn-save" 
                onClick={handleSave} 
                disabled={isSaving || !desc.trim()}
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
              <button 
                className="btn-cancel" 
                onClick={handleCancel} 
                disabled={isSaving}
              >
                Cancel
              </button>
            </div>
            {error && <div className="error-message">{error}</div>}
          </>
        ) : (
          <div className="description-text" onClick={() => setIsEditing(true)}>
            {desc || <span className="no-description">Click to add description</span>}
            {column.example_value && (
              <div className="example-value">
                <span className="example-label">Example: </span>
                <code>{column.example_value}</code>
              </div>
            )}
          </div>
        )}
        
        <div className="column-actions">
          <button 
            className="icon-button" 
            onClick={() => setIsEditing(!isEditing)}
            title={isEditing ? 'Cancel' : 'Edit description'}
          >
            {isEditing ? '✕' : '✏️'}
          </button>
        </div>
      </div>
    </div>
  );
}
