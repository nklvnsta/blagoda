import type { InputHTMLAttributes } from 'react';
import styles from './Input.module.css';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export function Input({ label, error, icon, className, ...props }: InputProps) {
  return (
    <div className={styles.container}>
      {label && <label className={styles.label}>{label}</label>}
      <div className={styles.inputWrapper}>
        {icon && <div className={styles.icon}>{icon}</div>}
        <input className={`${styles.input} ${className || ''}`} {...props} />
      </div>
      {error && <span className={styles.error}>{error}</span>}
    </div>
  );
}
