export interface WeekData {
  qty: number;
  unit: string;
  period_start: string;
  period_end: string;
}

export interface DeviationResponse {
  current_week: WeekData;
  previous_week: WeekData;
  change_pct: number;
  filters: Record<string, string | null>;
}

export interface RevenueResponse {
  revenue: string;
  unit: string;
  period_start: string;
  period_end: string;
  filters: Record<string, string | null>;
}

export interface ForecastAccuracyResponse {
  accuracy_pct: number;
  period_start: string;
  period_end: string;
  total_forecasts: number;
  filters: Record<string, string | null>;
}

export interface ChartPoint {
  week_start: string;
  actual: string;
  forecast: string | null;
}

export interface SalesChartResponse {
  unit: string;
  period_start: string;
  period_end: string;
  points: ChartPoint[];
  filters: Record<string, string | null>;
}
