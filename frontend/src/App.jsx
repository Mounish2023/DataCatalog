import { Routes, Route, Navigate, Outlet, useParams } from 'react-router-dom';
import { AuthProvider, useAuth } from './features/auth/AuthContext';
import Layout from './components/layout/Layout';
import DatabaseDetail from './features/catalog/components/DatabaseDetail';
import TableDetail from './features/catalog/components/TableDetail';
import Connectors from './features/connectors/components/Connectors';
import Login from './features/auth/Login';
import Register from './features/auth/Register';
import './App.css';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <div>Loading...</div>;

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Routes */}
        <Route element={
          <ProtectedRoute>
            <Layout>
              <Outlet />
            </Layout>
          </ProtectedRoute>
        }>
          <Route path="/" element={
            <div className="welcome-screen">
              <h1>Welcome to Gold Catalog</h1>
              <p>Select a database from the sidebar to get started.</p>
            </div>
          } />
          <Route path="/databases/:databaseId" element={<DatabaseDetail />} />
          <Route path="/tables/:tableId" element={<TableDetailWrapper />} />
          <Route path="/connectors" element={<Connectors />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

// Wrapper to handle params
function TableDetailWrapper() {
  const { tableId } = useParams();
  return <TableDetail tableId={tableId} />;
}

export default App;