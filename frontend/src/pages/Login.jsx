// frontend/src/pages/Login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';  // ← ADD THIS
import { useAuth } from '../contexts/AuthContext';
import { login as apiLogin } from '../api/api';
import './Auth.css';

export default function Login({ onSwitchToRegister }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();  // ← ADD THIS

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!email || !password) {
      setError('Please fill in all fields');
      setLoading(false);
      return;
    }

    try {
      const response = await apiLogin(email, password);
      
      // This saves token + user to context AND localStorage
      login(response.access_token, { email });

      // SUCCESS! Redirect to main app
      navigate('/data-connector', { replace: true });  // or '/' or '/dashboard'

    } catch (err) {
      console.error('Login error:', err);
      
      // Better error messages from backend
      const msg = err.response?.data?.detail 
        || err.message 
        || 'Login failed. Please check your credentials.';
      
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Login</h2>
        <p className="auth-subtitle">Welcome back to Gold Data Catalog</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={loading}
              required
            />
          </div>

          <button 
            type="submit" 
            disabled={loading} 
            className="auth-button"
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-switch">
          <p>
            Don't have an account?{' '}
            <button type="button" onClick={onSwitchToRegister} className="link-button">
              Register here
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}