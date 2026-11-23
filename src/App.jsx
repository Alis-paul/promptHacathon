import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import { AuthProvider } from './lib/AuthProvider';
import ReportPage from './pages/ReportPage';
import TrackPage from './pages/TrackPage';
import ComplaintDetail from './pages/ComplaintDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import Unauthorized from './pages/Unauthorized';
import CitizenDashboard from './pages/CitizenDashboard';
import DepartmentDashboard from './pages/DepartmentDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route element={<ProtectedRoute allowedRoles={["citizen"]} />}>
            <Route path="/report" element={<ReportPage />} />
          </Route>
          <Route path="/track" element={<TrackPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute allowedRoles={["citizen"]} />}>
            <Route path="/citizen/*" element={<CitizenDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={["department"]} />}>
            <Route path="/department/*" element={<DepartmentDashboard />} />
          </Route>
          <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
            <Route path="/admin/*" element={<AdminDashboard />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
