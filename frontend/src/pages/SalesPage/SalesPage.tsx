import { FilterDropdown } from '../../components/ui/FilterDropdown';

export function SalesPage() {
  return (
    <div className="page">
      <h1 className="heading">Продажи</h1>
      <FilterDropdown label="Период" options={[{ value: '1', label: '1' }, { value: '2', label: '2' }]} onChange={() => {}} />
      <FilterDropdown label="Фильтр" options={[{ value: '1', label: '1' }, { value: '2', label: '2' }]} onChange={() => {}} />
      <FilterDropdown label="Фильтр" options={[{ value: '1', label: '1' }, { value: '2', label: '2' }]} onChange={() => {}} />
    </div>
  );
}