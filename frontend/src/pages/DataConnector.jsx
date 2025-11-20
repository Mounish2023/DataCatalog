// frontend/src/pages/DataConnector.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  testConnection, 
  runIngestionSync, 
  runIngestionAsync,
  getIngestionStatus,
  listIngestionJobs 
} from '../api/dataConnector';
import { useAuth } from '../contexts/AuthContext';
import IngestionHelpGuide from '../components/IngestionHelpGuide';
import '../styles/DataConnector.css';

const DataConnector = () => {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    connectionString: '',
    schema: 'public',
    tablePattern: '%',
    enrichWithGpt: true,
  });
  
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [ingestionResult, setIngestionResult] = useState(null);
  const [activeTab, setActiveTab] = useState('connection');
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [executionMode, setExecutionMode] = useState('sync'); // 'sync' or 'async'

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      loadRecentJobs();
    }
  }, [isAuthenticated, authLoading]);

  // Poll for job status when async job is running
  useEffect(() => {
    if (jobId && executionMode === 'async') {
      const interval = setInterval(async () => {
        try {
          const status = await getIngestionStatus(jobId);
          setJobStatus(status);
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(interval);
            setPollingInterval(null);
            await loadRecentJobs();
          }
        } catch (error) {
          console.error('Error polling job status:', error);
        }
      }, 3000); // Poll every 3 seconds
      
      setPollingInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [jobId, executionMode]);

  const loadRecentJobs = async () => {
    try {
      const response = await listIngestionJobs();
      setRecentJobs(response.jobs || []);
    } catch (error) {
      console.error('Error loading recent jobs:', error);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleTestConnection = async (e) => {
    e.preventDefault();
    setLoading(true);
    setTestResult(null);
    
    try {
      const result = await testConnection(formData.connectionString);
      setTestResult({
        success: true,
        message: `Connection successful! Found ${result.table_count} tables in database "${result.database}"`,
        details: result
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to test connection'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async (e) => {
    e.preventDefault();
    
    if (!testResult?.success) {
      setIngestionResult({
        success: false,
        message: 'Please test the connection first and ensure it is successful.'
      });
      return;
    }

    setLoading(true);
    setIngestionResult(null);
    setJobStatus(null);
    setJobId(null);

    try {
      if (executionMode === 'sync') {
        // Synchronous ingestion
        const result = await runIngestionSync(
          formData.connectionString,
          formData.schema,
          formData.tablePattern,
          formData.enrichWithGpt
        );
        
        setIngestionResult({
          success: true,
          message: result.message,
          stats: result.stats
        });
      } else {
        // Asynchronous ingestion
        const result = await runIngestionAsync(
          formData.connectionString,
          formData.schema,
          formData.tablePattern,
          formData.enrichWithGpt
        );
        
        setJobId(result.job_id);
        setIngestionResult({
          success: true,
          message: 'Ingestion job started. Monitoring progress...',
          job_id: result.job_id
        });
      }
    } catch (error) {
      console.error('Ingestion error:', error);
      setIngestionResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to start ingestion'
      });
    } finally {
      setLoading(false);
    }
  };

  const viewJobDetails = async (selectedJobId) => {
    try {
      const status = await getIngestionStatus(selectedJobId);
      setJobId(selectedJobId);
      setJobStatus(status);
      setActiveTab('results');
    } catch (error) {
      console.error('Error fetching job details:', error);
    }
  };

  if (authLoading) {
    return <div className="loading-container">Loading authentication...</div>;
  }

  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  return (
    <div className="data-connector-container">
      <div className="page-header">
        <h1>Metadata Ingestion Pipeline</h1>
        <p className="subtitle">
          Extract schema information from external databases and enrich with AI-powered semantic metadata
        </p>
      </div>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'connection' ? 'active' : ''}`}
          onClick={() => setActiveTab('connection')}
        >
          <span className="tab-icon">🔌</span>
          Connection
        </button>
        <button 
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
          disabled={!testResult?.success}
        >
          <span className="tab-icon">⚙️</span>
          Settings
        </button>
        <button 
          className={`tab ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          <span className="tab-icon">📊</span>
          Results
        </button>
        <button 
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <span className="tab-icon">🕐</span>
          History
        </button>
      </div>

      {/* Connection Tab */}
      {activeTab === 'connection' && (
        <div className="tab-content">
          <div className="info-banner">
            <span className="info-icon">ℹ️</span>
            <div>
              <strong>Step 1: Test Connection</strong>
              <p>Verify access to your target database before starting ingestion.</p>
            </div>
          </div>

          <form onSubmit={handleTestConnection} className="connection-form">
            <div className="form-group">
              <label htmlFor="connectionString">
                Database Connection String *
                <span className="label-hint">PostgreSQL connection URL</span>
              </label>
              <input
                type="password"
                id="connectionString"
                name="connectionString"
                value={formData.connectionString}
                onChange={handleChange}
                placeholder="postgresql://username:password@host:5432/database"
                required
                className="form-control"
                disabled={loading}
              />
              <small className="form-text">
                Example: postgresql://user:pass@localhost:5432/sales_db
              </small>
            </div>
            
            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !formData.connectionString}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Testing...
                  </>
                ) : (
                  <>
                    <span>🔍</span>
                    Test Connection
                  </>
                )}
              </button>
            </div>
          </form>

          {testResult && (
            <div className={`alert ${testResult.success ? 'alert-success' : 'alert-error'}`}>
              <div className="alert-icon">
                {testResult.success ? '✅' : '❌'}
              </div>
              <div className="alert-content">
                <strong>{testResult.success ? 'Success!' : 'Error'}</strong>
                <p>{testResult.message}</p>
                {testResult.details && (
                  <div className="connection-details">
                    <p><strong>Database:</strong> {testResult.details.database}</p>
                    <p><strong>Version:</strong> {testResult.details.version}</p>
                    <p><strong>Tables:</strong> {testResult.details.table_count}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {testResult?.success && (
            <div className="next-step-prompt">
              <p>✓ Connection verified! Ready to configure ingestion settings.</p>
              <button 
                onClick={() => setActiveTab('settings')}
                className="btn btn-secondary"
              >
                Continue to Settings →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="tab-content">
          <div className="info-banner">
            <span className="info-icon">⚙️</span>
            <div>
              <strong>Step 2: Configure Ingestion</strong>
              <p>Choose which tables to import and how to process them.</p>
            </div>
          </div>

          <form onSubmit={handleIngest} className="settings-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="schema">
                  Schema *
                  <span className="label-hint">Database schema to scan</span>
                </label>
                <input
                  type="text"
                  id="schema"
                  name="schema"
                  value={formData.schema}
                  onChange={handleChange}
                  placeholder="public"
                  className="form-control"
                  disabled={loading}
                />
                <small className="form-text">
                  The database schema containing your tables (default: public)
                </small>
              </div>

              <div className="form-group">
                <label htmlFor="tablePattern">
                  Table Pattern *
                  <span className="label-hint">SQL LIKE pattern</span>
                </label>
                <input
                  type="text"
                  id="tablePattern"
                  name="tablePattern"
                  value={formData.tablePattern}
                  onChange={handleChange}
                  placeholder="%"
                  className="form-control"
                  disabled={loading}
                />
                <small className="form-text">
                  Use % for all tables, or patterns like "gold_%" or "%_fact"
                </small>
              </div>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="enrichWithGpt"
                  checked={formData.enrichWithGpt}
                  onChange={handleChange}
                  disabled={loading}
                />
                <span className="checkbox-text">
                  <strong>Enable GPT-4o Enrichment</strong>
                  <small>Generate semantic descriptions and business context (recommended)</small>
                </span>
              </label>
            </div>

            <div className="form-group">
              <label>
                Execution Mode *
                <span className="label-hint">How to run the ingestion</span>
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    value="sync"
                    checked={executionMode === 'sync'}
                    onChange={(e) => setExecutionMode(e.target.value)}
                    disabled={loading}
                  />
                  <span className="radio-text">
                    <strong>Synchronous</strong>
                    <small>Wait for completion (recommended for &lt;50 tables)</small>
                  </span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    value="async"
                    checked={executionMode === 'async'}
                    onChange={(e) => setExecutionMode(e.target.value)}
                    disabled={loading}
                  />
                  <span className="radio-text">
                    <strong>Asynchronous</strong>
                    <small>Run in background (for large databases)</small>
                  </span>
                </label>
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="button"
                onClick={() => setActiveTab('connection')}
                className="btn btn-secondary"
                disabled={loading}
              >
                ← Back
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !testResult?.success}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    {executionMode === 'sync' ? 'Ingesting...' : 'Starting Job...'}
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    Start Ingestion
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="settings-info">
            <h4>💡 What happens during ingestion?</h4>
            <ul>
              <li><strong>Schema Extraction:</strong> Reads table structures, columns, and relationships</li>
              <li><strong>Sample Collection:</strong> Gathers sample data for context</li>
              <li><strong>AI Enrichment:</strong> Generates business descriptions (if enabled)</li>
              <li><strong>Metadata Storage:</strong> Saves to catalog database</li>
            </ul>
          </div>
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && (
        <div className="tab-content">
          {ingestionResult && (
            <div className={`alert ${ingestionResult.success ? 'alert-success' : 'alert-error'}`}>
              <div className="alert-icon">
                {ingestionResult.success ? '✅' : '❌'}
              </div>
              <div className="alert-content">
                <strong>{ingestionResult.success ? 'Success!' : 'Error'}</strong>
                <p>{ingestionResult.message}</p>
              </div>
            </div>
          )}

          {jobStatus && (
            <div className="job-status-card">
              <div className="job-status-header">
                <h3>Job Status</h3>
                <span className={`status-badge status-${jobStatus.status}`}>
                  {jobStatus.status === 'running' && '⏳ '}
                  {jobStatus.status === 'completed' && '✅ '}
                  {jobStatus.status === 'failed' && '❌ '}
                  {jobStatus.status.toUpperCase()}
                </span>
              </div>

              <div className="job-details">
                <p><strong>Job ID:</strong> <code>{jobStatus.job_id}</code></p>
                <p><strong>Started:</strong> {new Date(jobStatus.started_at).toLocaleString()}</p>
              </div>

              {jobStatus.stats && (
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-value">{jobStatus.stats.databases_processed}</div>
                    <div className="stat-label">Databases</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{jobStatus.stats.tables_processed}</div>
                    <div className="stat-label">Tables</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{jobStatus.stats.columns_processed}</div>
                    <div className="stat-label">Columns</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{jobStatus.stats.duration_seconds.toFixed(1)}s</div>
                    <div className="stat-label">Duration</div>
                  </div>
                </div>
              )}

              {jobStatus.error && (
                <div className="error-details">
                  <strong>Error:</strong>
                  <pre>{jobStatus.error}</pre>
                </div>
              )}

              {jobStatus.stats?.errors && jobStatus.stats.errors.length > 0 && (
                <div className="warnings-section">
                  <h4>⚠️ Warnings ({jobStatus.stats.errors.length})</h4>
                  <ul className="error-list">
                    {jobStatus.stats.errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {ingestionResult?.stats && !jobStatus && (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{ingestionResult.stats.databases_processed}</div>
                <div className="stat-label">Databases</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{ingestionResult.stats.tables_processed}</div>
                <div className="stat-label">Tables</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{ingestionResult.stats.columns_processed}</div>
                <div className="stat-label">Columns</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">
                  {ingestionResult.stats.duration_seconds?.toFixed(1) || 0}s
                </div>
                <div className="stat-label">Duration</div>
              </div>
            </div>
          )}

          {!ingestionResult && !jobStatus && (
            <div className="empty-state">
              <span className="empty-icon">📊</span>
              <h3>No Results Yet</h3>
              <p>Start an ingestion job to see results here.</p>
              <button 
                onClick={() => setActiveTab('settings')}
                className="btn btn-primary"
              >
                Configure Ingestion
              </button>
            </div>
          )}

          {(ingestionResult?.success || (jobStatus?.status === 'completed')) && (
            <div className="next-steps">
              <h4>🎉 What's Next?</h4>
              <ul>
                <li>View enriched metadata in the <a href="/">Home</a> page</li>
                <li>Search and explore your data catalog</li>
                <li>Export metadata for documentation</li>
                <li>Set up automated ingestion schedules</li>
              </ul>
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="tab-content">
          <div className="history-header">
            <h3>Ingestion History</h3>
            <button 
              onClick={loadRecentJobs}
              className="btn btn-secondary btn-sm"
              disabled={loading}
            >
              🔄 Refresh
            </button>
          </div>

          {recentJobs.length > 0 ? (
            <div className="jobs-list">
              {recentJobs.map((job) => (
                <div key={job.job_id} className="job-card">
                  <div className="job-card-header">
                    <span className={`status-badge status-${job.status}`}>
                      {job.status}
                    </span>
                    <span className="job-time">
                      {new Date(job.started_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="job-card-body">
                    <p><strong>Job ID:</strong> <code>{job.job_id}</code></p>
                  </div>
                  <div className="job-card-actions">
                    <button
                      onClick={() => viewJobDetails(job.job_id)}
                      className="btn btn-sm btn-secondary"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon">🕐</span>
              <h3>No History</h3>
              <p>Your ingestion jobs will appear here.</p>
            </div>
          )}
        </div>
      )}
      
      <IngestionHelpGuide />
    </div>
  );
};

export default DataConnector;