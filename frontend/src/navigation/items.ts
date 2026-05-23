export interface NavigationItem {
  id: string;
  label: string;
  to?: string;
}

export const NAVIGATION_ITEMS: NavigationItem[] = [
  { id: 'home', label: 'Главная', to: '/' },
  { id: 'sales', label: 'Продажи', to: '/sales' },
  { id: 'forecast', label: 'Прогноз спроса', to: '/forecast' },
  { id: 'inventory', label: 'Запасы' },
  { id: 'supplies', label: 'Поставки', to: '/supplies' },
  { id: 'order-picking', label: 'Сбор заказа', to: '/picking' },
  { id: 'reports', label: 'Отчеты', to: '/reports' },
];
