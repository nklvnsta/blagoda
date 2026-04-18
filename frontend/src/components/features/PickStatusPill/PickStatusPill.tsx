import type { GroupPickStatus, RowPickStatus } from '../../../api/types';
import styles from './PickStatusPill.module.css';

export type PickStatus = GroupPickStatus | RowPickStatus;

interface PickStatusPillProps {
  status: PickStatus;
  className?: string;
}

const LABELS: Record<PickStatus, string> = {
  not_started: 'Не начато',
  in_progress: 'В сборке',
  partial: 'Частично',
  picked: 'Собрано',
};

const CLASS_BY_STATUS: Record<PickStatus, string> = {
  not_started: styles.pillNotStarted,
  in_progress: styles.pillInProgress,
  partial: styles.pillPartial,
  picked: styles.pillPicked,
};

export function PickStatusPill({ status, className }: PickStatusPillProps) {
  const cls = [styles.pill, CLASS_BY_STATUS[status], className]
    .filter(Boolean)
    .join(' ');
  return <span className={cls}>{LABELS[status]}</span>;
}
