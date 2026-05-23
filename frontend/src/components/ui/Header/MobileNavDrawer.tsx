import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../../auth/AuthContext';
import { CloseIcon } from '../../icons';
import { getNavigationItems } from '../../../navigation/items';
import styles from './MobileNavDrawer.module.css';

interface MobileNavDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function MobileNavDrawer({ open, onClose }: MobileNavDrawerProps) {
  const { user } = useAuth();
  const items = user ? getNavigationItems(user.role) : [];

  useEffect(() => {
    if (!open) return;

    document.body.style.overflow = 'hidden';

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  return (
    <>
      <div
        className={`${styles.overlay} ${open ? styles.overlayOpen : ''}`}
        onClick={onClose}
        role="presentation"
        aria-hidden={!open}
      />
      <aside
        className={`${styles.panel} ${open ? styles.panelOpen : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="Меню навигации"
        aria-hidden={!open}
      >
        <div className={styles.header}>
          <h2 className={styles.title}>Меню</h2>
          <button
            type="button"
            className={styles.closeButton}
            aria-label="Закрыть меню"
            onClick={onClose}
          >
            <CloseIcon size={24} />
          </button>
        </div>
        <ul className={styles.list}>
          {items.map((item) => (
            <li key={item.id} className={styles.listItem}>
              {item.to ? (
                <NavLink
                  to={item.to}
                  end
                  className={({ isActive }) =>
                    `${styles.link} ${isActive ? styles.linkActive : ''}`
                  }
                  onClick={onClose}
                >
                  {item.label}
                </NavLink>
              ) : (
                <span className={styles.disabled}>{item.label}</span>
              )}
            </li>
          ))}
        </ul>
      </aside>
    </>
  );
}
