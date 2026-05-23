import { useEffect } from 'react';
import { LogoutIcon } from '../../icons';
import styles from './LogoutConfirmModal.module.css';

interface LogoutConfirmModalProps {
  open: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export function LogoutConfirmModal({ open, onCancel, onConfirm }: LogoutConfirmModalProps) {
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onCancel();
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className={styles.overlay} onClick={onCancel} role="presentation">
      <div
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="logout-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.iconWrap} aria-hidden>
          <LogoutIcon size={57} />
        </div>
        <h2 id="logout-modal-title" className={styles.title}>
          Выход из системы
        </h2>
        <p className={styles.message}>Вы действительно хотите завершить работу?</p>
        <div className={styles.actions}>
          <button type="button" className={styles.cancel} onClick={onCancel}>
            Отмена
          </button>
          <button type="button" className={styles.confirm} onClick={onConfirm}>
            Выйти
          </button>
        </div>
      </div>
    </div>
  );
}
