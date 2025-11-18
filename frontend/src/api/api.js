// src/api/api.js
const API_URL = "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Something went wrong');
  }
  return response.json();
}

export async function fetchTables() {
  try {
    const res = await fetch(`${API_URL}/tables`);
    return await handleResponse(res);
  } catch (error) {
    console.error('Error fetching tables:', error);
    throw error;
  }
}

export async function fetchTable(tableName) {
  try {
    const res = await fetch(`${API_URL}/tables/${tableName}`);
    return await handleResponse(res);
  } catch (error) {
    console.error(`Error fetching table ${tableName}:`, error);
    throw error;
  }
}

export async function updateColumn(tableName, columnName, payload) {
  try {
    const res = await fetch(`${API_URL}/tables/${tableName}/columns/${columnName}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await handleResponse(res);
  } catch (error) {
    console.error(`Error updating column ${columnName}:`, error);
    throw error;
  }
}
