import React from 'react';
import Navigation from '../components/Navigation';
import { Link } from 'react-router-dom';

const QuickReport = () => (
  <section style={{
    backgroundColor: 'var(--color-warm-cream)',
    textAlign: 'center',
    padding: 'var(--space-12) var(--space-4)',
  }}>
    <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 'var(--space-4)' }}>
      Something needs attention?
    </h2>
    <p style={{ fontFamily: 'var(--font-body)', marginBottom: 'var(--space-6)' }}>
      Tell your municipality what happened.
    </p>
    <Link to="/report" className="button" style={{
      background: 'var(--color-primary-navy)',
      color: 'var(--color-white)',
      padding: 'var(--space-3) var(--space-6)',
      textDecoration: 'none',
      borderRadius: '2px',
    }}>
      Report an Issue
    </Link>
    <p style={{ marginTop: 'var(--space-4)', fontSize: '0.9rem' }}>
      Describe the problem, share its location, and attach a photo if needed. CivicAssist will route it.
    </p>
  </section>
);

export default QuickReport;
