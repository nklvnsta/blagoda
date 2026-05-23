import { useState } from 'react';
import { API_BASE } from '../../api';
import { getAuthHeaders } from '../../auth/authStorage';
import { handleUnauthorized } from '../../auth/AuthContext';
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

async function downloadReport(kind: ReportKind, output: OutputFormat) {
  const url = `${API_BASE}/reports/${kind}/?output=${output}`;
  const res = await fetch(url, { headers: getAuthHeaders() });

  if (res.status === 401) {
    handleUnauthorized();
    throw new Error('HTTP 401');
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const disposition = res.headers.get('Content-Disposition') ?? '';
  const match = disposition.match(/filename="(.+?)"/);
  const filename = match?.[1] ?? `${kind}.${output}`;

  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(blobUrl);
}

function ReportCard({ kind, title, description }: ReportCardData) {
  const [loading, setLoading] = useState<OutputFormat | null>(null);

  const handleDownload = async (output: OutputFormat) => {
    if (loading) return;
    setLoading(output);
    try {
      await downloadReport(kind, output);
    } catch {
      alert('Не удалось сформировать отчёт');
    } finally {
      setLoading(null);
    }
  };

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
        <button
          type="button"
          className={styles.action}
          disabled={loading !== null}
          onClick={() => handleDownload('xlsx')}
        >
          {loading === 'xlsx' ? 'Формируется…' : 'Скачать Excel'}
        </button>
        <button
          type="button"
          className={styles.actionPdf}
          disabled={loading !== null}
          onClick={() => handleDownload('pdf')}
        >
          {loading === 'pdf' ? 'Формируется…' : 'Скачать PDF'}
        </button>
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
