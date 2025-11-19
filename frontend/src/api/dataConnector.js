import axios from 'axios';
import { getAuthHeaders } from './api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ingestData = async (targetDbUrl, schema = 'public', namePattern = '') => {
  try {
    const response = await axios.post(
      `${API_URL}/api/ingest`,
      {
        target_db_url: targetDbUrl,
        schema: schema,
        name_like: namePattern || '%'  // Default to all tables if no pattern provided
      },
      { headers: getAuthHeaders() }
    );
    return response.data;
  } catch (error) {
    console.error('Error ingesting data:', error);
    throw error;
  }
};

export const testConnection = async (connectionString) => {
  try {
    // This is a client-side test that only checks if the connection string is valid
    // The actual connection test should be done on the backend
    if (!connectionString) {
      throw new Error('Connection string is required');
    }
    
    // Basic validation for common database connection string formats
    const dbTypes = ['postgresql://', 'mysql://', 'sqlserver://', 'oracle://', 'sqlite://','postgresql+asyncpg://'];
    if (!dbTypes.some(type => connectionString.toLowerCase().startsWith(type))) {
      throw new Error('Invalid connection string format');
    }
    
    return { success: true, message: 'Connection string appears valid' };
  } catch (error) {
    return { success: false, message: error.message };
  }
};
