import styles from './Footer.module.css';
import { useAuth } from '../../../auth/AuthContext';

interface FooterProps {
  className?: string;
  version?: string;
}

export function Footer({
  className,
  version = '1.0',
}: FooterProps) {
  const { user } = useAuth();
  const userName = user?.display_name ?? '—';
  const roleLabel = user?.role_label ?? '—';
  const now = new Date();
  const time = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

  return (
    <footer className={`${styles.footer} ${className ?? ''}`}>
      <div className={styles.info}>
        <div>&copy; ООО Динисалл, {now.getFullYear()} | Прогнозирование спроса в розничной сети | v{version}</div>
        <div>Пользователь: {userName} | Роль: {roleLabel}</div>
        <div>Обновление данных: {time} | Статус: актуально</div>
      </div>
    </footer>
  );
}
