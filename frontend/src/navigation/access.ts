import type { UserRole } from '../auth/AuthContext';

export const ROUTE_ACCESS: Record<string, UserRole[]> = {
  '/': ['admin', 'logist'],
  '/sales': ['admin', 'logist'],
  '/forecast': ['admin', 'logist'],
  '/supplies': ['admin', 'logist'],
  '/picking': ['admin', 'picker'],
  '/reports': ['admin'],
};

const ROUTE_PRIORITY = ['/', '/sales', '/forecast', '/supplies', '/picking', '/reports'] as const;

export function canAccessRoute(role: UserRole, path: string): boolean {
  if (path.startsWith('/picking/')) {
    return role === 'admin' || role === 'picker';
  }

  const allowed = ROUTE_ACCESS[path];
  if (!allowed) {
    return false;
  }

  return allowed.includes(role);
}

export function defaultRouteForRole(role: UserRole): string {
  if (role === 'picker') {
    return '/picking';
  }
  return '/';
}

export function firstAllowedRoute(role: UserRole): string {
  for (const route of ROUTE_PRIORITY) {
    if (canAccessRoute(role, route)) {
      return route;
    }
  }
  return '/login';
}
