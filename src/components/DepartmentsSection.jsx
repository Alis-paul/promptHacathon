import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import Navigation from '../components/Navigation';

const DepartmentsSection = () => {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const { data, error } = await supabase.from('departments').select('name, helpline, email');
        if (error) throw error;
        setDepartments(data);
      } catch (e) {
        console.error('Error loading departments', e);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchDepartments();
  }, []);

  if (loading) return <p>Loading departments...</p>;
  if (error) return <p>We couldn't load department information right now. Please try again.</p>;
  if (departments.length === 0) return <p>Department information is currently unavailable.</p>;

  return (
    <section style={{ padding: 'var(--space-12) var(--space-4)' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', textAlign: 'center', marginBottom: 'var(--space-8)' }}>Municipal Departments</h2>
      <ul style={{ listStyle: 'none', padding: 0, maxWidth: '800px', margin: '0 auto' }}>
        {departments.map((dept) => (
          <li key={dept.name} style={{ marginBottom: 'var(--space-6)', borderBottom: `1px solid var(--color-border)`, paddingBottom: 'var(--space-4)' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', margin: 0 }}>{dept.name}</h3>
            {dept.helpline && <p>Helpline: {dept.helpline}</p>}
            {dept.email && <p>Email: {dept.email}</p>}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default DepartmentsSection;
