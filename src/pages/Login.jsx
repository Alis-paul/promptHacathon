import React, { useState } from 'react';
import { useAuth } from '../lib/AuthProvider';
import { Navigate } from 'react-router-dom';
import Navigation from '../components/Navigation';

const Login = () => {
  const { user, signIn, authError, sessionLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (sessionLoading) return <div className="loading">Checking your session...</div>;
  if (user) {
    // Redirect based on role after login
    const role = user?.role || 'citizen';
    const path = role === 'admin' ? '/admin' : role === 'department' ? '/department' : '/citizen';
    return <Navigate to={path} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    await signIn(email, password);
  };

  return (
    <div>
      <Navigation />
      <section style={{ padding: 'var(--space-8)', maxWidth: '400px', margin: '0 auto' }}>
        <h2 style={{ fontFamily: 'var(--font-display)' }}>Login</h2>
        {authError && <div style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-4)' }}>{authError}</div>}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="email" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }}
            />
          </div>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Password</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }}
            />
          </div>
          <button type="submit" className="button" style={{ background: 'var(--color-primary-navy)', color: 'var(--color-white)', padding: 'var(--space-3) var(--space-5)', border: 'none' }}>
            Login
          </button>
        </form>
        <div style={{ marginTop: 'var(--space-4)' }}>
          <a href="/register" style={{ marginRight: 'var(--space-4)' }}>Create an account</a>
          <a href="#">Forgot password?</a>
        </div>
      </section>
    </div>
  );
};

export default Login;
