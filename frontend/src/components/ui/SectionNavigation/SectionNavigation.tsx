import { NavLink } from 'react-router-dom';
import { NAVIGATION_ITEMS } from '../../../navigation/items';
import styles from './SectionNavigation.module.css';

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
        {NAVIGATION_ITEMS.map((item) => (
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
        ))}
      </ul>
    </nav>
  );
}
