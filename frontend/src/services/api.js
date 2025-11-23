// frontend/src/api/api.js
const API_URL = "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.message || 'Something went wrong');
  }
  return response.json();
}

export function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
}

// Auth endpoints
export async function register(email, name, password) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name, password }),
  });
  return await handleResponse(res);
}

export async function login(email, password) {
  const formData = new FormData();
  formData.append('username', email); // API expects 'username' field
  formData.append('password', password);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    body: formData,
  });
  return await handleResponse(res);
}

// Database endpoints
export async function fetchDatabases() {
  const res = await fetch(`${API_URL}/api/databases`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchDatabase(dbId) {
  const res = await fetch(`${API_URL}/api/databases/${dbId}`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

export async function updateDatabase(dbId, payload) {
  const res = await fetch(`${API_URL}/api/databases/${dbId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

// Table endpoints
export async function fetchTables(databaseId = null) {
  const url = databaseId
    ? `${API_URL}/api/databases/${databaseId}/tables`
    : `${API_URL}/api/tables`;

  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchTable(tableId) {
  const res = await fetch(`${API_URL}/api/tables/${tableId}`, {
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

export async function updateTable(tableId, payload) {
  const res = await fetch(`${API_URL}/api/tables/${tableId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

export async function updateColumn(tableId, columnId, payload) {
  const res = await fetch(`${API_URL}/api/tables/${tableId}/columns/${columnId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

// Ingestion endpoints
export async function triggerIngestion(payload) {
  const res = await fetch(`${API_URL}/api/ingestion/run`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

export async function testConnection(connectionString) {
  const res = await fetch(`${API_URL}/api/ingestion/test-connection?connection_string=${encodeURIComponent(connectionString)}`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

// Delete endpoints
export async function deleteDatabase(dbId) {
  const res = await fetch(`${API_URL}/api/databases/${dbId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}

export async function deleteTable(tableId) {
  const res = await fetch(`${API_URL}/api/tables/${tableId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  return await handleResponse(res);
}