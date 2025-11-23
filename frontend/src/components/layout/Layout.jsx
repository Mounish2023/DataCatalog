import { useState, useEffect, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthContext';
import { fetchDatabases, fetchTables, deleteDatabase, deleteTable } from '../../services/api';
import styles from './Layout.module.css';

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Database Tree State
  const [databases, setDatabases] = useState([]);
  const [expandedDbs, setExpandedDbs] = useState({}); // { dbId: true/false }
  const [dbTables, setDbTables] = useState({}); // { dbId: [tables] }
  const [loading, setLoading] = useState(true);

  // Expose refresh function globally for Settings component
  useEffect(() => {
    window.refreshDatabases = loadDatabases;
    return () => delete window.refreshDatabases;
  }, []);

  const loadDatabases = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchDatabases();
      setDatabases(data);
    } catch (err) {
      console.error("Failed to load databases:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDatabases();
  }, [loadDatabases]);

  const toggleDatabase = async (dbId) => {
    // Toggle expansion
    const isExpanded = !expandedDbs[dbId];
    setExpandedDbs(prev => ({ ...prev, [dbId]: isExpanded }));

    // If expanding and tables not loaded, fetch them
    if (isExpanded && !dbTables[dbId]) {
      try {
        const tables = await fetchTables(dbId);
        setDbTables(prev => ({ ...prev, [dbId]: tables }));
      } catch (err) {
        console.error(`Failed to load tables for db ${dbId}:`, err);
      }
    }
  };

  const handleDeleteDatabase = async (e, dbId, dbName) => {
    e.preventDefault();
    e.stopPropagation();

    if (!window.confirm(`Are you sure you want to delete the database "${dbName}"? This will also delete all its tables and columns.`)) {
      return;
    }

    try {
      await deleteDatabase(dbId);

      // If currently viewing this database, navigate away
      if (location.pathname.includes(dbId)) {
        navigate('/');
      }

      // Refresh database list
      await loadDatabases();

      // Clear the tables cache for this database
      setDbTables(prev => {
        const newTables = { ...prev };
        delete newTables[dbId];
        return newTables;
      });
    } catch (err) {
      alert(`Failed to delete database: ${err.message}`);
    }
  };

  const handleDeleteTable = async (e, tableId, tableName, databaseId) => {
    e.preventDefault();
    e.stopPropagation();

    if (!window.confirm(`Are you sure you want to delete the table "${tableName}"?`)) {
      return;
    }

    try {
      await deleteTable(tableId);

      // If currently viewing this table, navigate to database view
      if (location.pathname.includes(tableId)) {
        navigate(`/databases/${databaseId}`);
      }

      // Refresh the tables for this database
      const tables = await fetchTables(databaseId);
      setDbTables(prev => ({ ...prev, [databaseId]: tables }));
    } catch (err) {
      alert(`Failed to delete table: ${err.message}`);
    }
  };

  const navItems = [
    { path: '/connectors', label: 'Connectors', icon: '🔌' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={styles.layout}>
      <aside className={`${styles.sidebar} ${isSidebarOpen ? styles.open : styles.closed}`}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>💎</span>
          {isSidebarOpen && <span className={styles.logoText}>Gold Catalog</span>}
        </div>

        <nav className={styles.nav}>
          {/* Databases Section */}
          <div className={styles.navSection}>
            <div className={styles.sectionTitle}>{isSidebarOpen ? 'DATABASES' : 'DB'}</div>
            {loading ? (
              <div className={styles.navLoading}>Loading...</div>
            ) : (
              databases.map(db => (
                <div key={db.id} className={styles.dbItem}>
                  <div
                    className={`${styles.dbHeader} ${location.pathname.includes(db.id) ? styles.active : ''}`}
                  >
                    <button
                      className={styles.expandBtn}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleDatabase(db.id);
                      }}
                    >
                      {expandedDbs[db.id] ? '▼' : '▶'}
                    </button>
                    <Link
                      to={`/databases/${db.id}`}
                      className={styles.dbLink}
                      title={!isSidebarOpen ? db.name : ''}
                    >
                      <span className={styles.dbIcon}>🗄️</span>
                      {isSidebarOpen && <span className={styles.dbName}>{db.name}</span>}
                    </Link>
                    {isSidebarOpen && (
                      <button
                        className={styles.deleteBtn}
                        onClick={(e) => handleDeleteDatabase(e, db.id, db.name)}
                        title="Delete database"
                      >
                        🗑️
                      </button>
                    )}
                  </div>

                  {/* Nested Tables */}
                  {isSidebarOpen && expandedDbs[db.id] && (
                    <div className={styles.tableList}>
                      {dbTables[db.id] ? (
                        dbTables[db.id].length > 0 ? (
                          dbTables[db.id].map(table => (
                            <div key={table.id} className={styles.tableItemWrapper}>
                              <Link
                                to={`/tables/${table.id}`}
                                className={`${styles.tableItem} ${location.pathname === `/tables/${table.id}` ? styles.active : ''}`}
                              >
                                <span className={styles.tableIcon}>
                                  {table.type === 'view' ? '👁️' : '📅'}
                                </span>
                                <span className={styles.tableName}>
                                  {table.display_name || table.technical_name}
                                </span>
                              </Link>
                              <button
                                className={styles.deleteBtn}
                                onClick={(e) => handleDeleteTable(e, table.id, table.display_name || table.technical_name, db.id)}
                                title="Delete table"
                              >
                                🗑️
                              </button>
                            </div>
                          ))
                        ) : (
                          <div className={styles.emptyTables}>No tables</div>
                        )
                      ) : (
                        <div className={styles.loadingTables}>Loading...</div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Static Items */}
          <div className={styles.navDivider} />
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`${styles.navItem} ${location.pathname === item.path ? styles.active : ''}`}
              title={!isSidebarOpen ? item.label : ''}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              {isSidebarOpen && <span className={styles.navLabel}>{item.label}</span>}
            </Link>
          ))}
        </nav>

        <div className={styles.footer}>
          <button
            onClick={handleLogout}
            className={styles.logoutBtn}
            title={!isSidebarOpen ? 'Logout' : ''}
          >
            <span className={styles.navIcon}>🚪</span>
            {isSidebarOpen && <span className={styles.navLabel}>Logout</span>}
          </button>

          <button
            className={styles.toggleBtn}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            {isSidebarOpen ? '◀' : '▶'}
          </button>
        </div>
      </aside>

      <main className={styles.main}>
        <header className={styles.header}>
          <div className={styles.breadcrumbs}>
            <span className={styles.crumb}>Home</span>
            <span className={styles.separator}>/</span>
            <span className={styles.crumbActive}>Data Catalog</span>
          </div>
          <div className={styles.userProfile}>
            <div className={styles.avatar}>{user?.name ? user.name[0].toUpperCase() : 'U'}</div>
            <span className={styles.userName}>{user?.name || 'User'}</span>
          </div>
        </header>
        <div className={styles.content}>
          {children}
        </div>
      </main>
    </div>
  );
}
