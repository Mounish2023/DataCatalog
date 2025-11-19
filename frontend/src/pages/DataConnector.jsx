import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ingestData, testConnection } from '../api/dataConnector';
import { useAuth } from '../contexts/AuthContext';
import '../styles/DataConnector.css';

const DataConnector = () => {
  const { user: currentUser, isAuthenticated, loading } = useAuth();
  
  const [formData, setFormData] = useState({
    connectionString: '',
    schema: 'public',
    tablePattern: '',
  });
  
  const [localLoading, setLoading] = useState(false); // rename to avoid conflict
  const [testResult, setTestResult] = useState(null);
  const [ingestResult, setIngestResult] = useState(null);
  const [activeTab, setActiveTab] = useState('connection');
  const navigate = useNavigate();

  console.log('DataConnector - isAuthenticated:', isAuthenticated, 'user:', currentUser);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTestConnection = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTestResult(null);
    
    try {
      const result = await testConnection(formData.connectionString);
      setTestResult({
        success: result.success,
        message: result.message
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to test connection'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    if (!testResult?.success) {
      setIngestResult({
        success: false,
        message: 'Please test the connection first and ensure it is successful.'
      });
      return;
    }

    setLoading(true);
    setIngestResult(null);

    try {
      const result = await ingestData(
        formData.connectionString,
        formData.schema,
        formData.tablePattern
      );
      
      setIngestResult({
        success: true,
        message: `Successfully imported ${result.imported?.length || 0} tables`,
        data: result.imported
      });
    } catch (error) {
      console.error('Ingest error:', error);
      setIngestResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to import data'
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
  return <div>Loading authentication...</div>;
}

if (!isAuthenticated) {
  navigate('/login');
  return null;
}

  return (
    <div className="data-connector-container">
      <h1>Data Connector</h1>
      <p className="subtitle">Connect to external databases and import table metadata</p>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'connection' ? 'active' : ''}`}
          onClick={() => setActiveTab('connection')}
        >
          Connection
        </button>
        <button 
          className={`tab ${activeTab === 'import' ? 'active' : ''}`}
          onClick={() => setActiveTab('import')}
          disabled={!testResult?.success}
        >
          Import Settings
        </button>
      </div>

      {activeTab === 'connection' ? (
        <div className="tab-content">
          <form onSubmit={handleTestConnection} className="connection-form">
            <div className="form-group">
              <label htmlFor="connectionString">Database Connection String</label>
              <input
                type="password"
                id="connectionString"
                name="connectionString"
                value={formData.connectionString}
                onChange={handleChange}
                placeholder="postgresql://username:password@host:port/database"
                required
                className="form-control"
              />
              <small className="form-text text-muted">
                Example: postgresql://username:password@localhost:5432/your_database
              </small>
            </div>
            
            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !formData.connectionString}
              >
                {loading ? 'Testing...' : 'Test Connection'}
              </button>
            </div>
          </form>

          {testResult && (
            <div className={`alert ${testResult.success ? 'alert-success' : 'alert-error'}`}>
              {testResult.message}
            </div>
          )}
        </div>
      ) : (
        <div className="tab-content">
          <form onSubmit={handleIngest} className="import-form">
            <div className="form-group">
              <label htmlFor="schema">Schema</label>
              <input
                type="text"
                id="schema"
                name="schema"
                value={formData.schema}
                onChange={handleChange}
                placeholder="public"
                className="form-control"
              />
              <small className="form-text text-muted">
                The database schema to import tables from (default: public)
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="tablePattern">Table Name Pattern (optional)</label>
              <input
                type="text"
                id="tablePattern"
                name="tablePattern"
                value={formData.tablePattern}
                onChange={handleChange}
                placeholder="%"
                className="form-control"
              />
              <small className="form-text text-muted">
                Use SQL LIKE pattern (e.g., 'sales_%' for tables starting with 'sales_')
              </small>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !testResult?.success}
              >
                {loading ? 'Importing...' : 'Import Tables'}
              </button>
            </div>
          </form>

          {ingestResult && (
            <div className={`alert ${ingestResult.success ? 'alert-success' : 'alert-error'}`}>
              {ingestResult.message}
              {ingestResult.data && ingestResult.data.length > 0 && (
                <div className="imported-tables">
                  <h4>Imported Tables:</h4>
                  <ul>
                    {ingestResult.data.map((table, index) => (
                      <li key={index}>{table}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataConnector;
