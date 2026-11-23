import React from 'react';
import Navigation from '../components/Navigation';
import { Link } from 'react-router-dom';

const Hero = () => (
  <section style={{
    backgroundImage: "url('/src/assets/hero-placeholder.jpg')",
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    color: 'var(--color-white)',
    textAlign: 'center',
    padding: 'var(--space-16) var(--space-4)',
  }}>
    <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2.5rem', marginBottom: 'var(--space-4)' }}>
      Better cities begin with better reporting.
    </h1>
    <p style={{ fontFamily: 'var(--font-body)', fontSize: '1.2rem', marginBottom: 'var(--space-6)' }}>
      Report local issues, track their progress, and help your city respond faster.
    </p>
    <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-4)' }}>
      <Link to="/report" className="button" style={{
        background: 'var(--color-primary-navy)',
        color: 'var(--color-white)',
        padding: 'var(--space-3) var(--space-6)',
        textDecoration: 'none',
        borderRadius: '2px',
      }}>Report an Issue</Link>
      <Link to="/track" className="button" style={{
        background: 'var(--color-muted-blue)',
        color: 'var(--color-white)',
        padding: 'var(--space-3) var(--space-6)',
        textDecoration: 'none',
        borderRadius: '2px',
      }}>Track a Complaint</Link>
    </div>
  </section>
);

export default Hero;
