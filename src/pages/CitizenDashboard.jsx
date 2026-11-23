import React from 'react';
import Navigation from '../components/Navigation';

const CitizenDashboard = () => (
  <div>
    <Navigation />
    <section style={{ padding: 'var(--space-8)' }}>
      <h2 style={{ fontFamily: 'var(--font-display)' }}>Citizen Dashboard (placeholder)</h2>
      <p>Here citizens will see their complaints and status.</p>
    </section>
  </div>
);

export default CitizenDashboard;
