import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../lib/AuthProvider';

/**
 * ProtectedRoute renders children only if the user is authenticated and
 * their role is included in `allowedRoles`. Otherwise it redirects:
 *   - not authenticated → /login
 *   - authenticated but wrong role → /unauthorized
 */
const ProtectedRoute = ({ allowedRoles }) => {
  const { user, profile, sessionLoading } = useAuth();

  if (sessionLoading) {
    return <div className="loading">Checking your session...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const role = profile?.role;
  if (!allowedRoles.includes(role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
