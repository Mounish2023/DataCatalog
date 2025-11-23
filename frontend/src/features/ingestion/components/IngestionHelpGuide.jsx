// frontend/src/components/IngestionHelpGuide.jsx
import React, { useState } from 'react';
import '../../../styles/IngestionHelp.css';

const IngestionHelpGuide = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');

  const sections = {
    overview: {
      title: '📖 Overview',
      content: (
        <>
          <h3>What is Metadata Ingestion?</h3>
          <p>
            Metadata ingestion extracts schema information from your database and enriches
            it with AI-powered semantic descriptions, making your data catalog more useful
            and searchable.
          </p>

          <h4>What Gets Extracted:</h4>
          <ul>
            <li><strong>Database Info:</strong> Name, table count, structure</li>
            <li><strong>Table Info:</strong> Names, row counts, relationships, foreign keys</li>
            <li><strong>Column Info:</strong> Data types, nullability, sample values, cardinality</li>
          </ul>

          <h4>What Gets Enriched (with GPT):</h4>
          <ul>
            <li><strong>Business Descriptions:</strong> Human-readable explanations</li>
            <li><strong>Table Types:</strong> Fact, dimension, reference, etc.</li>
            <li><strong>Data Sensitivity:</strong> PII, confidential, internal, public</li>
            <li><strong>Column Semantics:</strong> Purpose, usage patterns, valid values</li>
          </ul>
        </>
      )
    },

    connectionStrings: {
      title: '🔌 Connection Strings',
      content: (
        <>
          <h3>Database Connection Strings</h3>
          <p>Connection strings tell the system how to connect to your database.</p>

          <h4>Format:</h4>
          <pre><code>postgresql://username:password@host:port/database</code></pre>

          <h4>Examples:</h4>
          <div className="example-box">
            <strong>Local PostgreSQL:</strong>
            <pre><code>postgresql://postgres:mypassword@localhost:5432/sales_db</code></pre>
          </div>

          <div className="example-box">
            <strong>Remote Server:</strong>
            <pre><code>postgresql://user:pass@db.example.com:5432/analytics</code></pre>
          </div>

          <div className="example-box">
            <strong>Cloud Provider (AWS RDS):</strong>
            <pre><code>postgresql://admin:secret@mydb.abc123.us-east-1.rds.amazonaws.com:5432/prod</code></pre>
          </div>

          <div className="tip-box">
            <strong>💡 Tip:</strong> Make sure your database is accessible from this application's
            network. You may need to configure firewall rules or VPN access.
          </div>
        </>
      )
    },

    tablePatterns: {
      title: '🔍 Table Patterns',
      content: (
        <>
          <h3>Table Name Patterns</h3>
          <p>Use SQL LIKE patterns to filter which tables to ingest.</p>

          <h4>Pattern Syntax:</h4>
          <ul>
            <li><code>%</code> - Matches any sequence of characters</li>
            <li><code>_</code> - Matches any single character</li>
          </ul>

          <h4>Common Patterns:</h4>
          <div className="pattern-grid">
            <div className="pattern-card">
              <code>%</code>
              <p>All tables in schema</p>
            </div>
            <div className="pattern-card">
              <code>gold_%</code>
              <p>Tables starting with "gold_"</p>
            </div>
            <div className="pattern-card">
              <code>%_fact</code>
              <p>Tables ending with "_fact"</p>
            </div>
            <div className="pattern-card">
              <code>%sales%</code>
              <p>Tables containing "sales"</p>
            </div>
            <div className="pattern-card">
              <code>customers</code>
              <p>Exact table name</p>
            </div>
            <div className="pattern-card">
              <code>dim_%</code>
              <p>Dimension tables</p>
            </div>
          </div>

          <div className="warning-box">
            <strong>⚠️ Note:</strong> Pattern matching is case-sensitive on most systems.
            If your table is "Customers", use the exact case.
          </div>
        </>
      )
    },

    performance: {
      title: '⚡ Performance',
      content: (
        <>
          <h3>Performance & Best Practices</h3>

          <h4>Execution Modes:</h4>
          <div className="comparison-table">
            <div className="comparison-row header">
              <div>Mode</div>
              <div>Best For</div>
              <div>Duration</div>
            </div>
            <div className="comparison-row">
              <div><strong>Synchronous</strong></div>
              <div>&lt; 50 tables</div>
              <div>Wait for completion</div>
            </div>
            <div className="comparison-row">
              <div><strong>Asynchronous</strong></div>
              <div>50+ tables</div>
              <div>Run in background</div>
            </div>
          </div>

          <h4>Estimated Timings:</h4>
          <table className="timing-table">
            <thead>
              <tr>
                <th>Database Size</th>
                <th>Without GPT</th>
                <th>With GPT</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>10 tables / 80 columns</td>
                <td>~5 seconds</td>
                <td>~25 seconds</td>
              </tr>
              <tr>
                <td>50 tables / 400 columns</td>
                <td>~20 seconds</td>
                <td>~2 minutes</td>
              </tr>
              <tr>
                <td>200 tables / 1600 columns</td>
                <td>~1.5 minutes</td>
                <td>~8 minutes</td>
              </tr>
            </tbody>
          </table>

          <h4>Tips for Faster Ingestion:</h4>
          <ul>
            <li>Start with a specific table pattern to test</li>
            <li>Disable GPT enrichment for initial testing</li>
            <li>Use async mode for large databases</li>
            <li>Schedule ingestion during off-peak hours</li>
          </ul>
        </>
      )
    },

    troubleshooting: {
      title: '🔧 Troubleshooting',
      content: (
        <>
          <h3>Common Issues & Solutions</h3>

          <div className="issue-card">
            <h4>❌ Connection Failed</h4>
            <p><strong>Possible Causes:</strong></p>
            <ul>
              <li>Incorrect credentials or connection string</li>
              <li>Database is not accessible from network</li>
              <li>Firewall blocking connection</li>
            </ul>
            <p><strong>Solutions:</strong></p>
            <ul>
              <li>Verify credentials are correct</li>
              <li>Check firewall/security group settings</li>
              <li>Ensure database server is running</li>
              <li>Test connection from terminal: <code>psql "postgresql://..."</code></li>
            </ul>
          </div>

          <div className="issue-card">
            <h4>⚠️ GPT Enrichment Failures</h4>
            <p><strong>Possible Causes:</strong></p>
            <ul>
              <li>OpenAI API key not configured</li>
              <li>Rate limits exceeded</li>
              <li>API service down</li>
            </ul>
            <p><strong>Solutions:</strong></p>
            <ul>
              <li>Check OPENAI_API_KEY environment variable</li>
              <li>Disable GPT and re-run to get basic metadata</li>
              <li>Wait a few minutes and retry</li>
            </ul>
          </div>

          <div className="issue-card">
            <h4>🐌 Slow Performance</h4>
            <p><strong>Solutions:</strong></p>
            <ul>
              <li>Use more specific table patterns (e.g., <code>gold_%</code> instead of <code>%</code>)</li>
              <li>Disable GPT enrichment for faster extraction</li>
              <li>Use async mode for large databases</li>
              <li>Process tables in smaller batches</li>
            </ul>
          </div>

          <div className="issue-card">
            <h4>🔍 No Tables Found</h4>
            <p><strong>Possible Causes:</strong></p>
            <ul>
              <li>Wrong schema specified</li>
              <li>Table pattern doesn't match any tables</li>
              <li>Tables are views, not base tables</li>
            </ul>
            <p><strong>Solutions:</strong></p>
            <ul>
              <li>Verify schema name (default is "public")</li>
              <li>Use <code>%</code> pattern to see all tables</li>
              <li>Check table names are spelled correctly</li>
            </ul>
          </div>
        </>
      )
    },

    security: {
      title: '🔒 Security',
      content: (
        <>
          <h3>Security Considerations</h3>

          <div className="security-section">
            <h4>Connection String Security:</h4>
            <ul>
              <li>Connection strings with passwords are only stored temporarily during ingestion</li>
              <li>Use read-only database credentials when possible</li>
              <li>Consider using environment variables for sensitive connections</li>
              <li>Regularly rotate database passwords</li>
            </ul>
          </div>

          <div className="security-section">
            <h4>Data Privacy:</h4>
            <ul>
              <li>Sample data is collected (up to 10 values per column)</li>
              <li>PII detection helps identify sensitive columns</li>
              <li>Review metadata before sharing with other users</li>
              <li>Use sensitivity labels to control access</li>
            </ul>
          </div>

          <div className="security-section">
            <h4>GPT Enrichment:</h4>
            <ul>
              <li>Only schema metadata and samples are sent to OpenAI</li>
              <li>No full data dumps are transmitted</li>
              <li>Sample values are limited to prevent exposure</li>
              <li>You can disable GPT enrichment entirely if needed</li>
            </ul>
          </div>

          <div className="tip-box">
            <strong>🔐 Best Practice:</strong> Create a dedicated read-only database user
            specifically for metadata ingestion. This limits exposure if credentials are compromised.
          </div>
        </>
      )
    }
  };

  return (
    <>
      <button
        className="help-trigger-button"
        onClick={() => setIsOpen(true)}
        title="Open Help Guide"
      >
        <span>❓</span>
        Help
      </button>

      {isOpen && (
        <div className="help-modal-overlay" onClick={() => setIsOpen(false)}>
          <div className="help-modal" onClick={(e) => e.stopPropagation()}>
            <div className="help-header">
              <h2>Metadata Ingestion Guide</h2>
              <button
                className="help-close-button"
                onClick={() => setIsOpen(false)}
              >
                ✕
              </button>
            </div>

            <div className="help-content">
              <nav className="help-sidebar">
                {Object.entries(sections).map(([key, section]) => (
                  <button
                    key={key}
                    className={`help-nav-item ${activeSection === key ? 'active' : ''}`}
                    onClick={() => setActiveSection(key)}
                  >
                    {section.title}
                  </button>
                ))}
              </nav>

              <div className="help-main">
                {sections[activeSection].content}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default IngestionHelpGuide;