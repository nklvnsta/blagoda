import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../auth/AuthContext';
import { ChevronDown } from '../../icons';
import { LogoutConfirmModal } from '../LogoutConfirmModal';
import styles from './UserMenu.module.css';

const PLACEHOLDER_ROLE = '—';

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);

  const userName = user?.display_name ?? '—';

  useEffect(() => {
    if (!open) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const handleLogoutConfirm = () => {
    setLogoutOpen(false);
    setOpen(false);
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <>
      <div className={styles.root} ref={menuRef}>
        <button
          type="button"
          className={styles.trigger}
          aria-expanded={open}
          aria-haspopup="menu"
          onClick={() => setOpen((v) => !v)}
        >
          <span className={styles.userName}>Пользователь: {userName}</span>
          <ChevronDown size={20} className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`} />
        </button>

        {open && (
          <div className={styles.dropdown} role="menu">
            <div className={styles.userInfo}>
              <span className={styles.infoName}>{userName}</span>
              <span className={styles.infoRole}>Роль: {PLACEHOLDER_ROLE}</span>
            </div>
            <button
              type="button"
              className={styles.logoutItem}
              role="menuitem"
              onClick={() => {
                setOpen(false);
                setLogoutOpen(true);
              }}
            >
              Выйти
            </button>
          </div>
        )}
      </div>

      <LogoutConfirmModal
        open={logoutOpen}
        onCancel={() => setLogoutOpen(false)}
        onConfirm={handleLogoutConfirm}
      />
    </>
  );
}
