import type { UserRole } from '../auth/AuthContext';

export interface NavigationItem {
  id: string;
  label: string;
  to?: string;
  roles: UserRole[];
}

export const NAVIGATION_ITEMS: NavigationItem[] = [
  { id: 'home', label: 'Главная', to: '/', roles: ['admin', 'logist'] },
  { id: 'sales', label: 'Продажи', to: '/sales', roles: ['admin', 'logist'] },
  { id: 'forecast', label: 'Прогноз спроса', to: '/forecast', roles: ['admin', 'logist'] },
  { id: 'supplies', label: 'Поставки', to: '/supplies', roles: ['admin', 'logist'] },
  { id: 'order-picking', label: 'Сбор заказа', to: '/picking', roles: ['admin', 'picker'] },
  { id: 'reports', label: 'Отчеты', to: '/reports', roles: ['admin'] },
];

export function getNavigationItems(role: UserRole): NavigationItem[] {
  return NAVIGATION_ITEMS.filter((item) => item.roles.includes(role));
}
