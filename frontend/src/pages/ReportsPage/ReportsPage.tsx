import { API_BASE } from '../../api';
import styles from './ReportsPage.module.css';

type ReportKind = 'sales' | 'stock' | 'forecast' | 'xyz';
type OutputFormat = 'xlsx' | 'pdf';

interface ReportCardData {
  kind: ReportKind;
  title: string;
  description: string;
}

const REPORTS: ReportCardData[] = [
  {
    kind: 'sales',
    title: 'Отчет по продажам',
    description: 'Анализ выручки, количества продаж и средних показателей',
  },
  {
    kind: 'stock',
    title: 'Отчет по остаткам',
    description: 'Текущие остатки, дефицитные и избыточные позиции',
  },
  {
    kind: 'forecast',
    title: 'Отчет по прогнозу спроса',
    description: 'Прогноз продаж по товарам на выбранный период',
  },
  {
    kind: 'xyz',
    title: 'XYZ - анализ',
    description: 'Оценка стабильности спроса по товарам',
  },
];

function reportUrl(kind: ReportKind, output: OutputFormat): string {
  return `${API_BASE}/reports/${kind}/?output=${output}`;
}

function ReportCard({ kind, title, description }: ReportCardData) {
  return (
    <div className={styles.card}>
      <div className={styles.info}>
        <div className={styles.titles}>
          <h3 className={styles.title}>{title}</h3>
          <span className={styles.format}>Формат: Excel / PDF</span>
        </div>
        <p className={styles.description}>{description}</p>
      </div>
      <div className={styles.actions}>
        <a
          className={styles.action}
          href={reportUrl(kind, 'xlsx')}
          target="_blank"
          rel="noopener noreferrer"
        >
          Скачать Excel
        </a>
        <a
          className={styles.actionPdf}
          href={reportUrl(kind, 'pdf')}
          target="_blank"
          rel="noopener noreferrer"
        >
          Скачать PDF
        </a>
      </div>
    </div>
  );
}

export function ReportsPage() {
  return (
    <div className="page">
      <h2 className={styles.heading}>
        Формирование и скачивание аналитических отчетов по продажам, остаткам, спросу и поставкам
      </h2>
      <div className={styles.cards}>
        {REPORTS.map((r) => (
          <ReportCard key={r.kind} {...r} />
        ))}
      </div>
    </div>
  );
}
