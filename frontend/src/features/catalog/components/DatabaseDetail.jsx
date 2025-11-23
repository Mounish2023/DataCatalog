import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchDatabase, updateDatabase } from "../../../services/api";
import styles from "./DatabaseDetail.module.css";

export default function DatabaseDetail() {
    const { databaseId } = useParams();
    const navigate = useNavigate();
    const [database, setDatabase] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Editing state
    const [isEditingDescription, setIsEditingDescription] = useState(false);
    const [editedDescription, setEditedDescription] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const loadDatabase = async () => {
            if (!databaseId) return;

            try {
                setLoading(true);
                setError(null);
                const data = await fetchDatabase(databaseId);
                setDatabase(data);
                setEditedDescription(data.description || "");
            } catch (err) {
                console.error(`Error loading database ${databaseId}:`, err);
                setError("Failed to load database details.");
            } finally {
                setLoading(false);
            }
        };

        loadDatabase();
    }, [databaseId]);

    const handleSaveDescription = async () => {
        try {
            setSaving(true);
            await updateDatabase(databaseId, { description: editedDescription });

            // Update local state
            setDatabase(prev => ({ ...prev, description: editedDescription }));
            setIsEditingDescription(false);
        } catch (err) {
            console.error("Failed to update description:", err);
            alert("Failed to save description");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className={styles.loading}>Loading database details...</div>;
    if (error) return <div className={styles.error}>{error}</div>;
    if (!database) return <div className={styles.empty}>Database not found</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.titleRow}>
                    <h1 className={styles.title}>{database.name}</h1>
                    <span className={styles.badge}>Database</span>
                </div>

                <div className={styles.metaGrid}>
                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Business Domain</span>
                        <span className={styles.metaValue}>{database.business_domain || "Unknown"}</span>
                    </div>
                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Owner</span>
                        <span className={styles.metaValue}>{database.owner || "Unassigned"}</span>
                    </div>
                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Sensitivity</span>
                        <span className={styles.metaValue}>{database.sensitivity || "Internal"}</span>
                    </div>
                    <div className={styles.metaItem}>
                        <span className={styles.metaLabel}>Tables</span>
                        <span className={styles.metaValue}>{database.tables?.length || 0}</span>
                    </div>
                </div>

                <div className={styles.descriptionSection}>
                    <div className={styles.sectionHeader}>
                        <h3>Description</h3>
                        {!isEditingDescription && (
                            <button
                                onClick={() => setIsEditingDescription(true)}
                                className={styles.editBtn}
                            >
                                Edit
                            </button>
                        )}
                    </div>

                    {isEditingDescription ? (
                        <div className={styles.editContainer}>
                            <textarea
                                value={editedDescription}
                                onChange={(e) => setEditedDescription(e.target.value)}
                                className={styles.descriptionInput}
                                rows={4}
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
                                        setEditedDescription(database.description || "");
                                    }}
                                    disabled={saving}
                                    className={styles.cancelBtn}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <p className={styles.descriptionText}>
                            {database.description || "No description provided."}
                        </p>
                    )}
                </div>
            </div>

            <div className={styles.tablesSection}>
                <h3>Tables</h3>
                <div className={styles.tableGrid}>
                    {database.tables?.map(table => (
                        <div
                            key={table.id}
                            className={styles.tableCard}
                            onClick={() => navigate(`/tables/${table.id}`)}
                        >
                            <div className={styles.tableIcon}>📅</div>
                            <div className={styles.tableInfo}>
                                <div className={styles.tableName}>{table.display_name || table.technical_name}</div>
                                <div className={styles.tableType}>{table.type}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
