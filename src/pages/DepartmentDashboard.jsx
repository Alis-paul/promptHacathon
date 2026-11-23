import React from 'react';
import Navigation from '../components/Navigation';

const DepartmentDashboard = () => (
  <div>
    <Navigation />
    <section style={{ padding: 'var(--space-8)' }}>
      <h2 style={{ fontFamily: 'var(--font-display)' }}>Department Dashboard (placeholder)</h2>
      <p>Department users will manage assigned complaints here.</p>
    </section>
  </div>
);

export default DepartmentDashboard;
