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

export interface SalesRevenueChartPoint {
  date: string;
  revenue: string;
  avg_ticket: string | null;
}

export interface SalesRevenueChartResponse {
  unit: string;
  average_unit: string;
  period_start: string;
  period_end: string;
  points: SalesRevenueChartPoint[];
  filters: Record<string, string | null>;
}

/** Ответ GET /dashboard/critical-stock/ — массив записей */
export interface CriticalStockItem {
  product: string;
  shop: string;
  deviation_qty: number;
  deviation_type: 'deficit' | 'surplus';
  calculated_at: string;
}

/** Элемент GET /dashboard/problem-products/ */
export interface ProblemProductItem {
  product_id: string;
  product: string;
  total_deviation_qty: number;
  deficit_qty: number;
  surplus_qty: number;
  affected_shops: number;
  last_calculated_at: string;
}

export interface Category {
  id: string;
  name: string;
  children?: Category[];
}

export interface FiltersResponse {
  shops: {
    id: string;
    name: string;
  }[];
  categories: Category[];
  periods: {
    code: string;
    label: string;
  }[]
}

export interface SalesData {
  revenue: string;
  sold_qty: number;
  avg_ticket: string;
  avg_daily_revenue: string;
  currency: string;
  quantity_unit: string;
  receipt_count: number;
  period_code: string;
  period_label: string;
  period_start: string;
  period_end: string;
  filters: {
    shop?: string;
    category?: string;
    period?: string;
    date_from?: string;
    date_to?: string;
  };
}

export interface ShopSalesRow {
  shop_id: string;
  shop_name: string;
  revenue: string;
  sold_qty: number;
  receipt_count: number;
}

export interface SalesByShopsResponse {
  currency: string;
  quantity_unit: string;
  rows: ShopSalesRow[];
  total: ShopSalesRow;
  period_start: string;
  period_end: string;
  period_code: string;
  period_label: string;
  filters: Record<string, string | null>;
}

export interface ProductSalesRow {
  product_id: string;
  product_name: string;
  category_name: string;
  sold_qty: number;
}

// ── Forecast (Прогноз спроса) ────────────────────────────────────────────

export interface DemandChartPoint {
  week_start: string;
  actual: number;
  forecast: number | null;
}

export interface ForecastDemandChartResponse {
  unit: string;
  period_start: string;
  period_end: string;
  points: DemandChartPoint[];
  filters: Record<string, string | null>;
}

export interface ForecastSummaryResponse {
  expected_sales: number;
  expected_sales_unit: string;
  accuracy_pct: number;
  total_forecasts: number;
  period_start: string;
  period_end: string;
  period_code: string;
  period_label: string;
  filters: Record<string, string | null>;
}

export interface ForecastProductRow {
  product_id: string;
  product_name: string;
  forecast_qty: number;
  previous_qty: number;
  deviation_qty: number;
}

export interface ForecastByProductsResponse {
  quantity_unit: string;
  rows: ForecastProductRow[];
  period_start: string;
  period_end: string;
  period_code: string;
  period_label: string;
  filters: Record<string, string | null>;
}

export interface SalesByProductsResponse {
  quantity_unit: string;
  rows: ProductSalesRow[];
  total: ProductSalesRow;
  period_start: string;
  period_end: string;
  period_code: string;
  period_label: string;
  filters: Record<string, string | null>;
}

// ── Supplies (Поставки) ──────────────────────────────────────────────────

export type SupplyStatus = 'scheduled' | 'in_transit' | 'delivered' | 'cancelled';

export interface SuppliesFiltersResponse {
  shops: { id: string; name: string }[];
}

export interface SuppliesSummaryResponse {
  date: string;
  shipped_qty_today: number;
  shipped_amount_today: string;
  in_transit_deliveries: number;
  tomorrow_positions: number;
  quantity_unit: string;
  currency: string;
  filters: Record<string, string | null>;
}

export interface ScheduledShopRow {
  shop_id: string;
  shop_name: string;
  positions_count: number;
}

export interface SuppliesScheduledResponse {
  date: string;
  rows: ScheduledShopRow[];
  total_positions: number;
  total_shops: number;
  filters: Record<string, string | number | null>;
}

export interface InTransitRow {
  shop_id: string;
  shop_name: string;
  dispatch_date: string;
  positions_count: number;
  status: SupplyStatus;
}

export interface SuppliesInTransitResponse {
  rows: InTransitRow[];
  total_deliveries: number;
  total_positions: number;
  filters: Record<string, string | number | null>;
}

export interface SupplyRow {
  shop_id: string;
  shop_name: string;
  dispatch_date: string;
  positions_count: number;
  amount: string;
  status: SupplyStatus;
}

export interface SuppliesTableResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: SupplyRow[];
  currency: string;
  filters: Record<string, string | null>;
}

export type SuppliesTableSort = 'positions_count' | 'amount';
