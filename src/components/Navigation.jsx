import React from 'react';
import { useAuth } from '../lib/AuthProvider';
import { Navigate } from 'react-router-dom';

/** Simple navigation bar that reacts to auth state */
const Navigation = () => {
  const { user, profile, signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    // After logout, redirect to home (handled by router)
  };

  const role = profile?.role;
  const dashboardPath = role === 'citizen' ? '/citizen' : role === 'department' ? '/department' : role === 'admin' ? '/admin' : '/';

  return (
    <nav className="navigation" style={{ display: 'flex', justifyContent: 'space-between', padding: 'var(--space-4)', borderBottom: `1px solid var(--color-border)` }}>
      <div className="logo" style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem' }}>
        <a href="/" style={{ textDecoration: 'none', color: 'var(--color-primary-navy)' }}>CivicAssist</a>
      </div>
      <div className="links" style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center' }}>
        {user ? (
          <>
            <a href={dashboardPath} style={{ textDecoration: 'none', color: 'var(--color-dark-text)' }}>Dashboard</a>
            {/* Placeholder for notifications */}
            <button onClick={handleLogout} className="button" style={{ background: 'none', border: 'none', color: 'var(--color-primary-navy)', cursor: 'pointer' }}>Logout</button>
          </>
        ) : (
          <>
            <a href="/login" style={{ textDecoration: 'none', color: 'var(--color-dark-text)' }}>Login</a>
            <a href="/register" style={{ textDecoration: 'none', color: 'var(--color-primary-navy)' }}>Report an Issue</a>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
