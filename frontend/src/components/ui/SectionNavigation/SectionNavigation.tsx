import { NavLink } from 'react-router-dom';
import styles from './SectionNavigation.module.css';

interface NavigationItem {
  id: string;
  label: string;
  to?: string;
}

const NAVIGATION_ITEMS: NavigationItem[] = [
  { id: 'home', label: 'Главная', to: '/' },
  { id: 'sales', label: 'Продажи', to: '/sales' },
  { id: 'forecast', label: 'Прогноз спроса', to: '/forecast' },
  { id: 'inventory', label: 'Запасы' },
  { id: 'supplies', label: 'Поставки', to: '/supplies' },
  { id: 'order-picking', label: 'Сбор заказа', to: '/picking' },
  { id: 'reports', label: 'Отчеты', to: '/reports' },
];

interface SectionNavigationProps {
  className?: string;
}

export function SectionNavigation({ className }: SectionNavigationProps) {
  return (
    <nav
      aria-label="Основная навигация"
      className={`${styles.navigation} ${className ?? ''}`}
    >
        <ul className={styles.list}>
          {NAVIGATION_ITEMS.map((item) => {
            return (
              <li key={item.id} className={styles.listItem}>
                {item.to ? (
                  <NavLink
                    to={item.to}
                    end
                    className={({ isActive }) =>
                      `${styles.item} ${isActive ? styles.itemActive : ''}`
                    }
                  >
                    {item.label}
                  </NavLink>
                ) : (
                  <span className={styles.item}>{item.label}</span>
                )}
              </li>
            );
          })}
        </ul>
    </nav>
  );
}
