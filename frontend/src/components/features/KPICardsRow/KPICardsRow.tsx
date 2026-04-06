import styles from "./KPICardsRow.module.css";

interface KPICardsRowProps {
    children: React.ReactNode[];
}

export function KPICardsRow({ children }: KPICardsRowProps) {
  return (
    <div className={styles.cards}>
      {/* Здесь будут располагаться карточки с KPI */}
      {children}
    </div>
  );
}