import React, { useState } from 'react';
import { useAuth } from '../lib/AuthProvider';
import { Navigate } from 'react-router-dom';
import Navigation from '../components/Navigation';

const Register = () => {
  const { user, signUp, authError, sessionLoading } = useAuth();
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formError, setFormError] = useState(null);

  if (sessionLoading) return <div className="loading">Checking your session...</div>;
  if (user) {
    // redirect to citizen dashboard after registration/login
    return <Navigate to="/citizen" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    if (password !== confirmPassword) {
      setFormError('Passwords do not match.');
      return;
    }
    await signUp(email, password, fullName, phone);
  };

  return (
    <div>
      <Navigation />
      <section style={{ padding: 'var(--space-8)', maxWidth: '500px', margin: '0 auto' }}>
        <h2 style={{ fontFamily: 'var(--font-display)' }}>Create an Account</h2>
        {authError && <div style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-4)' }}>{authError}</div>}
        {formError && <div style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-4)' }}>{formError}</div>}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="fullName" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Full Name</label>
            <input id="fullName" type="text" required value={fullName} onChange={e => setFullName(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }} />
          </div>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="phone" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Phone Number</label>
            <input id="phone" type="tel" required value={phone} onChange={e => setPhone(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }} />
          </div>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="email" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Email</label>
            <input id="email" type="email" required value={email} onChange={e => setEmail(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }} />
          </div>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="password" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Password</label>
            <input id="password" type="password" required value={password} onChange={e => setPassword(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }} />
          </div>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <label htmlFor="confirmPassword" style={{ display: 'block', marginBottom: 'var(--space-2)' }}>Confirm Password</label>
            <input id="confirmPassword" type="password" required value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
              style={{ width: '100%', padding: 'var(--space-2)', border: '1px solid var(--color-border)' }} />
          </div>
          <button type="submit" className="button" style={{ background: 'var(--color-primary-navy)', color: 'var(--color-white)', padding: 'var(--space-3) var(--space-5)', border: 'none' }}>
            Register
          </button>
        </form>
        <div style={{ marginTop: 'var(--space-4)' }}>
          <a href="/login">Already have an account? Login</a>
        </div>
      </section>
    </div>
  );
};

export default Register;
