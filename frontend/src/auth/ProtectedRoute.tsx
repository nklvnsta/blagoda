import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { canAccessRoute, defaultRouteForRole, firstAllowedRoute } from '../navigation/access';
import { useAuth } from './AuthContext';

export function ProtectedRoute() {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return null;
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!canAccessRoute(user.role, location.pathname)) {
    return <Navigate to={firstAllowedRoute(user.role)} replace />;
  }

  return <Outlet />;
}

export function GuestRoute() {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) {
    return null;
  }

  if (isAuthenticated && user) {
    return <Navigate to={defaultRouteForRole(user.role)} replace />;
  }

  return <Outlet />;
}
