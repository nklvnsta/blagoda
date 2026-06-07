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
  date: string;
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

export type SupplyStatus = 'scheduled' | 'ready_to_ship' | 'in_transit' | 'delivered' | 'cancelled';

export interface SuppliesFiltersResponse {
  shops: { id: string; name: string }[];
}

export interface SuppliesSummaryResponse {
  date: string;
  to_dispatch_count: number;
  to_dispatch_amount: string;
  shipped_count: number;
  shipped_amount: string;
  currency: string;
  filters: Record<string, string | null>;
}

export interface SuppliesDispatchPayload {
  shop_id: string;
  dispatch_date: string;
}

export interface SuppliesDispatchResponse {
  shop_id: string;
  shop_name: string;
  dispatch_date: string;
  dispatched_count: number;
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

export interface SupplyItem {
  id: string;
  product_name: string;
  product_sku: string;
  unit: string;
  quantity_shipped: number;
  price: string;
  amount: string;
  status: SupplyStatus;
  editable: boolean;
}

export interface SupplyItemsResponse {
  count: number;
  results: SupplyItem[];
}

export interface SupplyItemPatchPayload {
  quantity_shipped: number;
}

// ── Picking (Сбор заказа) ────────────────────────────────────────────────

export type GroupPickStatus = 'not_started' | 'in_progress' | 'partial' | 'picked';
export type RowPickStatus = 'not_started' | 'partial' | 'picked';

export interface PickingSummaryResponse {
  total_shops: number;
  not_started_count: number;
  in_progress_count: number;
  partial_count: number;
  picked_count: number;
  filters: Record<string, string | null>;
}

export interface PickingShopRow {
  shop_id: string;
  shop_name: string;
  positions_count: number;
  ordered_units: number;
  picked_units: number;
  pick_status: GroupPickStatus;
}

export interface PickingTodayResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PickingShopRow[];
  filters: Record<string, string | null>;
}

export type PickingTodaySort =
  | 'shop_name'
  | 'positions_count'
  | 'ordered_units'
  | 'picked_units';

export interface PickingItem {
  id: string;
  position_no: number;
  product_id: string;
  product_name: string;
  unit: string;
  ordered_quantity: number;
  picked_quantity: number;
  pick_status: RowPickStatus;
}

export interface PickingDetailResponse {
  shop: { id: string; name: string };
  dispatch_date: string;
  pick_status: GroupPickStatus;
  totals: { ordered_units: number; picked_units: number };
  items: PickingItem[];
}

export interface PickingBulkSavePayload {
  items: { id: string; picked_quantity: number }[];
}

export interface PickingBulkSaveResponse {
  updated_count: number;
  totals: { ordered_units: number; picked_units: number };
  pick_status: GroupPickStatus;
}

export interface PickingDispatchResponse {
  shop: { id: string; name: string };
  dispatch_date: string;
  ready_count: number;
  cancelled_count: number;
}
