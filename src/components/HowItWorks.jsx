import React from 'react';
import { Link } from 'react-router-dom';

const HowItWorks = () => (
  <section style={{ padding: 'var(--space-12) var(--space-4)', textAlign: 'center' }}>
    <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 'var(--space-8)' }}>How CivicAssist Works</h2>
    <ol style={{ listStyle: 'none', counterReset: 'step', maxWidth: '800px', margin: '0 auto' }}>
      <li style={{ marginBottom: 'var(--space-6)', position: 'relative', paddingLeft: '3rem' }}>
        <span style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '2rem',
          height: '2rem',
          borderRadius: '50%',
          background: 'var(--color-primary-navy)',
          color: 'var(--color-white)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-display)',
        }}>01</span>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>Report</h3>
        <p>Tell us what happened and where.</p>
      </li>
      <li style={{ marginBottom: 'var(--space-6)', position: 'relative', paddingLeft: '3rem' }}>
        <span style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '2rem',
          height: '2rem',
          borderRadius: '50%',
          background: 'var(--color-primary-navy)',
          color: 'var(--color-white)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-display)',
        }}>02</span>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>Route</h3>
        <p>CivicAssist identifies the appropriate department.</p>
      </li>
      <li style={{ marginBottom: 'var(--space-6)', position: 'relative', paddingLeft: '3rem' }}>
        <span style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '2rem',
          height: '2rem',
          borderRadius: '50%',
          background: 'var(--color-primary-navy)',
          color: 'var(--color-white)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-display)',
        }}>03</span>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>Resolve</h3>
        <p>The responsible department investigates and works on the issue.</p>
      </li>
      <li style={{ position: 'relative', paddingLeft: '3rem' }}>
        <span style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: '2rem',
          height: '2rem',
          borderRadius: '50%',
          background: 'var(--color-primary-navy)',
          color: 'var(--color-white)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-display)',
        }}>04</span>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>Track</h3>
        <p>Follow the complaint until resolution.</p>
      </li>
    </ol>
    <p style={{ marginTop: 'var(--space-6)', fontFamily: 'var(--font-body)' }}>
      Intelligent classification helps route complaints, but you will always see which department is handling yours.
    </p>
  </section>
);

export default HowItWorks;
