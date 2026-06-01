import { useState } from 'react';
import styles from './Header.module.css';
import logoSrc from '/logo.png';
import { MenuIcon } from '../../icons';
import { MobileNavDrawer } from './MobileNavDrawer';
import { UserMenu } from './UserMenu';

interface HeaderProps {
  className?: string;
}

export function Header({ className }: HeaderProps) {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <>
      <header className={`${styles.header} ${className ?? ''}`}>
        <button
          type="button"
          className={styles.burger}
          aria-label="Открыть меню"
          aria-expanded={navOpen}
          onClick={() => setNavOpen(true)}
        >
          <MenuIcon size={24} />
        </button>

        <img src={logoSrc} alt="Благода" className={styles.logo} />
        <span className={styles.title}> Сиситема прогнозирования спроса </span>

        <div className={styles.spacer} />

        <div className={styles.user}>
          <UserMenu />
        </div>
      </header>

      <MobileNavDrawer open={navOpen} onClose={() => setNavOpen(false)} />
    </>
  );
}
