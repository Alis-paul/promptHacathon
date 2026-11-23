import React from 'react';
import Navigation from '../components/Navigation';

const Transparency = () => (
  <section style={{
    backgroundColor: 'var(--color-warm-cream)',
    padding: 'var(--space-12) var(--space-4)',
    textAlign: 'center',
  }}>
    <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 'var(--space-8)' }}>
      See how your city is responding.
    </h2>
    <p style={{ fontFamily: 'var(--font-body)', marginBottom: 'var(--space-8)' }}>
      CivicAssist makes municipal performance easier to understand through public, aggregated information about complaints and resolution.
    </p>
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
      gap: 'var(--space-6)',
      maxWidth: '800px',
      margin: '0 auto',
    }}>
      <div>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>12,480</h3>
        <p>Complaints received</p>
      </div>
      <div>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>9,842</h3>
        <p>Complaints resolved</p>
      </div>
      <div>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>78.9%</h3>
        <p>Resolution rate</p>
      </div>
      <div>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>18</h3>
        <p>Active incidents</p>
      </div>
    </div>
  </section>
);

export default Transparency;
