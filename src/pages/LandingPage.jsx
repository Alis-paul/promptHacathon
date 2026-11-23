import React from 'react';
import Navigation from '../components/Navigation';
import Hero from '../components/Hero';
import QuickReport from '../components/QuickReport';
import IssueCategories from '../components/IssueCategories';
import HowItWorks from '../components/HowItWorks';
import Transparency from '../components/Transparency';
import DepartmentsSection from '../components/DepartmentsSection';
import TrustMessage from '../components/TrustMessage';
import Footer from '../components/Footer';

const LandingPage = () => (
  <div>
    <Navigation />
    <main>
      <Hero />
      <QuickReport />
      <IssueCategories />
      <HowItWorks />
      <Transparency />
      <DepartmentsSection />
      <TrustMessage />
    </main>
    <Footer />
  </div>
);

export default LandingPage;
