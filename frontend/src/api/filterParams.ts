import type { FilterValues } from '../components/features/FiltersComponent/FiltersComponent';

export function buildFilterParams(
  filters: FilterValues,
): Record<string, string | undefined> {
  const params: Record<string, string | undefined> = {
    shop: filters.shopId,
    category: filters.categoryId,
    period: filters.periodCode,
  };

  if (filters.periodCode === 'custom') {
    params.date_from = filters.dateFrom;
    params.date_to = filters.dateTo;
  }

  return params;
}
