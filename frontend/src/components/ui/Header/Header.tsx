import styles from './Header.module.css';
import logoSrc from '/logo.png';
import { BellIcon, CalendarIcon, SettingsIcon } from '../../icons';
import { UserMenu } from './UserMenu';

interface HeaderProps {
  className?: string;
}

export function Header({ className }: HeaderProps) {
  return (
    <header className={`${styles.header} ${className ?? ''}`}>
      <img src={logoSrc} alt="Благода" className={styles.logo} />
      <span className={styles.title}>Оптимизация товарных потоков</span>

      <div className={styles.spacer} />

      <div className={styles.actions}>
        <button className={styles.iconButton} aria-label="Уведомления">
          <BellIcon />
        </button>
        <button className={styles.iconButton} aria-label="Календарь">
          <CalendarIcon />
        </button>
        <button className={styles.iconButton} aria-label="Настройки">
          <SettingsIcon />
        </button>
      </div>

      <div className={styles.user}>
        <UserMenu />
      </div>
    </header>
  );
}
