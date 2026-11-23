import React from 'react';
import { Link } from 'react-router-dom';

const IssueCategories = () => (
  <section style={{ padding: 'var(--space-12) var(--space-4)', textAlign: 'center' }}>
    <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: 'var(--space-8)' }}>What can you report?</h2>
    <ul style={{ listStyle: 'none', margin: 0, padding: 0, maxWidth: '800px', marginLeft: 'auto', marginRight: 'auto' }}>
      <li style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>01&nbsp;Garbage Collection</h3>
        <p>Missed pickups, overflowing bins and waste accumulation.</p>
      </li>
      <li style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>02&nbsp;Roads &amp; Infrastructure</h3>
        <p>Potholes, damaged signage, street surface issues.</p>
      </li>
      <li style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>03&nbsp;Water Supply</h3>
        <p>Leaks, pressure problems, water quality concerns.</p>
      </li>
      <li style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>04&nbsp;Drainage</h3>
        <p>Clogged drains, flooding, stormwater issues.</p>
      </li>
      <li style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>05&nbsp;Streetlights</h3>
        <p>Outages, flickering, damaged fixtures.</p>
      </li>
    </ul>
    <Link to="/report" className="button" style={{
      background: 'var(--color-primary-navy)',
      color: 'var(--color-white)',
      padding: 'var(--space-3) var(--space-6)',
      textDecoration: 'none',
      borderRadius: '2px',
      marginTop: 'var(--space-6)'
    }}>Report an Issue</Link>
  </section>
);

export default IssueCategories;
