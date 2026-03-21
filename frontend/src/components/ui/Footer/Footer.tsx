import styles from './Footer.module.css';

interface FooterProps {
  className?: string;
  userName?: string;
  role?: string;
  version?: string;
}

export function Footer({
  className,
  userName = 'Николаева А.И.',
  role = 'Администратор',
  version = '1.0',
}: FooterProps) {
  const now = new Date();
  const time = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

  return (
    <footer className={`${styles.footer} ${className ?? ''}`}>
      <div className={styles.info}>
        <div>&copy; ООО Динисалл, {now.getFullYear()} | Оптимизация товарных потоков | v{version}</div>
        <div>Пользователь: {userName} | Роль: {role}</div>
        <div>Обновление данных: {time} | Статус: актуально</div>
      </div>
    </footer>
  );
}
