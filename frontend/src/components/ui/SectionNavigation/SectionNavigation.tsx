import { NavLink } from 'react-router-dom';
import { useAuth } from '../../../auth/AuthContext';
import { getNavigationItems } from '../../../navigation/items';
import styles from './SectionNavigation.module.css';

interface SectionNavigationProps {
  className?: string;
}

export function SectionNavigation({ className }: SectionNavigationProps) {
  const { user } = useAuth();
  const items = user ? getNavigationItems(user.role) : [];

  return (
    <nav
      aria-label="Основная навигация"
      className={`${styles.navigation} ${className ?? ''}`}
    >
      <ul className={styles.list}>
        {items.map((item) => (
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
