// frontend/src/api/dataConnector.js
import axios from 'axios';
import { getAuthHeaders } from './api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Test database connection
 */
export const testConnection = async (connectionString) => {
  try {
    const response = await axios.post(
      `${API_URL}/api/ingestion/test-connection`,
      { connection_string: connectionString },
      { 
        headers: getAuthHeaders(),
        params: { connection_string: connectionString }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error testing connection:', error);
    throw error;
  }
};

/**
 * Run synchronous metadata ingestion
 * Use for smaller databases (< 50 tables)
 */
export const runIngestionSync = async (
  connectionString,
  schema = 'public',
  tablePattern = '%',
  enrichWithGpt = true
) => {
  try {
    const response = await axios.post(
      `${API_URL}/api/ingestion/run-sync`,
      {
        target_connection_string: connectionString,
        schema: schema,
        table_pattern: tablePattern,
        enrich_with_gpt: enrichWithGpt
      },
      { headers: getAuthHeaders() }
    );
    return response.data;
  } catch (error) {
    console.error('Error running sync ingestion:', error);
    throw error;
  }
};

/**
 * Run asynchronous metadata ingestion
 * Use for larger databases (50+ tables)
 * Returns a job_id to track progress
 */
export const runIngestionAsync = async (
  connectionString,
  schema = 'public',
  tablePattern = '%',
  enrichWithGpt = true
) => {
  try {
    const response = await axios.post(
      `${API_URL}/api/ingestion/run`,
      {
        target_connection_string: connectionString,
        schema: schema,
        table_pattern: tablePattern,
        enrich_with_gpt: enrichWithGpt
      },
      { headers: getAuthHeaders() }
    );
    return response.data;
  } catch (error) {
    console.error('Error running async ingestion:', error);
    throw error;
  }
};

/**
 * Get status of an ingestion job
 */
export const getIngestionStatus = async (jobId) => {
  try {
    const response = await axios.get(
      `${API_URL}/api/ingestion/status/${jobId}`,
      { headers: getAuthHeaders() }
    );
    return response.data;
  } catch (error) {
    console.error('Error getting job status:', error);
    throw error;
  }
};

/**
 * List all ingestion jobs for current user
 */
export const listIngestionJobs = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/api/ingestion/jobs`,
      { headers: getAuthHeaders() }
    );
    return response.data;
  } catch (error) {
    console.error('Error listing jobs:', error);
    throw error;
  }
};

/**
 * Legacy function for backward compatibility
 * @deprecated Use runIngestionSync or runIngestionAsync instead
 */
export const ingestData = async (targetDbUrl, schema = 'public', namePattern = '') => {
  console.warn('ingestData is deprecated. Use runIngestionSync or runIngestionAsync instead.');
  return runIngestionSync(targetDbUrl, schema, namePattern || '%', true);
};