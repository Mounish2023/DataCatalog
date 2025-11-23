import { useState } from 'react';
import { triggerIngestion, testConnection } from '../../../services/api';
import IngestionHelpGuide from '../../ingestion/components/IngestionHelpGuide';
import styles from './Connectors.module.css';

export default function Connectors() {
    const [selectedConnector, setSelectedConnector] = useState(null);
    const [config, setConfig] = useState({
        connectionString: '',
        schema: 'public',
        tablePattern: '%',
        enrichWithGpt: true
    });
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null);
    const [testResult, setTestResult] = useState(null);

    const connectors = [
        {
            id: 'postgresql',
            name: 'PostgreSQL',
            icon: '🐘',
            status: 'active',
            description: 'Connect to PostgreSQL databases'
        },
        {
            id: 'mysql',
            name: 'MySQL',
            icon: '🐬',
            status: 'coming-soon',
            description: 'Connect to MySQL databases'
        },
        {
            id: 'mongodb',
            name: 'MongoDB',
            icon: '🍃',
            status: 'coming-soon',
            description: 'Connect to MongoDB databases'
        },
        {
            id: 'sqlserver',
            name: 'SQL Server',
            icon: '🔷',
            status: 'coming-soon',
            description: 'Connect to Microsoft SQL Server'
        }
    ];

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setConfig(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleTestConnection = async () => {
        if (!config.connectionString) {
            setStatus({ type: 'error', message: 'Connection string is required' });
            return;
        }

        try {
            setLoading(true);
            setStatus(null);
            setTestResult(null);
            const result = await testConnection(config.connectionString);
            setTestResult(result);
            setStatus({ type: 'success', message: 'Connection successful!' });
        } catch (err) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setLoading(false);
        }
    };

    const handleIngest = async () => {
        if (!config.connectionString) {
            setStatus({ type: 'error', message: 'Connection string is required' });
            return;
        }

        try {
            setLoading(true);
            setStatus(null);
            const result = await triggerIngestion({
                target_connection_string: config.connectionString,
                schema: config.schema,
                table_pattern: config.tablePattern,
                enrich_with_gpt: config.enrichWithGpt
            });
            setStatus({
                type: 'success',
                message: `Ingestion started! Job ID: ${result.job_id}`
            });

            // Auto-refresh the database list in the sidebar
            if (window.refreshDatabases) {
                window.refreshDatabases();
            }
        } catch (err) {
            setStatus({ type: 'error', message: err.message });
        } finally {
            setLoading(false);
        }
    };

    const handleConnectorClick = (connectorId) => {
        if (connectorId === 'postgresql') {
            setSelectedConnector(selectedConnector === connectorId ? null : connectorId);
            setStatus(null);
            setTestResult(null);
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Data Connectors</h1>
            <p className={styles.subtitle}>Connect to your data sources and start cataloging</p>

            <div className={styles.connectorsGrid}>
                {connectors.map(connector => (
                    <div
                        key={connector.id}
                        className={`${styles.connectorCard} ${connector.status === 'active' ? styles.active : styles.disabled
                            } ${selectedConnector === connector.id ? styles.selected : ''}`}
                        onClick={() => handleConnectorClick(connector.id)}
                    >
                        <div className={styles.cardHeader}>
                            <span className={styles.connectorIcon}>{connector.icon}</span>
                            <div className={styles.connectorInfo}>
                                <h3 className={styles.connectorName}>{connector.name}</h3>
                                <p className={styles.connectorDesc}>{connector.description}</p>
                            </div>
                            {connector.status === 'coming-soon' && (
                                <span className={styles.badge}>Coming Soon</span>
                            )}
                            {connector.status === 'active' && (
                                <span className={styles.badgeActive}>Available</span>
                            )}
                        </div>

                        {/* PostgreSQL Configuration Form */}
                        {connector.id === 'postgresql' && selectedConnector === 'postgresql' && (
                            <div className={styles.configForm} onClick={(e) => e.stopPropagation()}>
                                <div className={styles.formDivider}></div>

                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Connection String</label>
                                    <input
                                        type="text"
                                        name="connectionString"
                                        value={config.connectionString}
                                        onChange={handleChange}
                                        placeholder="postgresql://user:password@localhost:5432/dbname"
                                        className={styles.input}
                                    />
                                </div>

                                <div className={styles.row}>
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Schema</label>
                                        <input
                                            type="text"
                                            name="schema"
                                            value={config.schema}
                                            onChange={handleChange}
                                            className={styles.input}
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Table Pattern (SQL LIKE)</label>
                                        <input
                                            type="text"
                                            name="tablePattern"
                                            value={config.tablePattern}
                                            onChange={handleChange}
                                            className={styles.input}
                                        />
                                    </div>
                                </div>

                                <div className={styles.formGroup}>
                                    <label className={styles.checkboxLabel}>
                                        <input
                                            type="checkbox"
                                            name="enrichWithGpt"
                                            checked={config.enrichWithGpt}
                                            onChange={handleChange}
                                        />
                                        <span className={styles.checkboxText}>Enrich metadata with GPT-4o</span>
                                    </label>
                                    <p className={styles.helpText} style={{ marginLeft: '24px' }}>
                                        Automatically generates descriptions and tags for tables and columns.
                                    </p>
                                </div>

                                <div className={styles.actions}>
                                    <button
                                        onClick={handleTestConnection}
                                        disabled={loading}
                                        className={styles.secondaryBtn}
                                    >
                                        Test Connection
                                    </button>
                                    <button
                                        onClick={handleIngest}
                                        disabled={loading}
                                        className={styles.primaryBtn}
                                    >
                                        {loading ? 'Processing...' : 'Start Ingestion'}
                                    </button>
                                </div>

                                {status && (
                                    <div className={`${styles.status} ${styles[status.type]}`}>
                                        {status.message}
                                    </div>
                                )}

                                {testResult && (
                                    <div className={styles.testResult}>
                                        <h4>Connection Details</h4>
                                        <div className={styles.resultGrid}>
                                            <div className={styles.resultItem}>
                                                <span className={styles.resultLabel}>Database:</span>
                                                <span>{testResult.database}</span>
                                            </div>
                                            <div className={styles.resultItem}>
                                                <span className={styles.resultLabel}>Version:</span>
                                                <span>{testResult.version}</span>
                                            </div>
                                            <div className={styles.resultItem}>
                                                <span className={styles.resultLabel}>Table Count:</span>
                                                <span>{testResult.table_count}</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <IngestionHelpGuide />
        </div>
    );
}
