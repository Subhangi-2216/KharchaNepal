import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

// Basic check: Does the token exist?
// In a real app, you might want to validate the token's expiry or signature
const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('accessToken');
  return !!token; // Return true if token exists, false otherwise
};

interface ProtectedRouteProps {
    redirectPath?: string;
    children?: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ redirectPath = '/login', children }) => {
  if (!isAuthenticated()) {
    // User not authenticated, redirect to login page
    return <Navigate to={redirectPath} replace />;
  }

  // User is authenticated, render the child route component
  // If children are provided directly, render them. Otherwise, render the Outlet for nested routes.
  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute; 