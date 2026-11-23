import React from 'react';
import Navigation from '../components/Navigation';

const AdminDashboard = () => (
  <div>
    <Navigation />
    <section style={{ padding: 'var(--space-8)' }}>
      <h2 style={{ fontFamily: 'var(--font-display)' }}>Admin Dashboard (placeholder)</h2>
      <p>Admins can manage the system here.</p>
    </section>
  </div>
);

export default AdminDashboard;
