import { FiltersComponent } from "../../components/features/FiltersComponent";

export function SalesPage() {
  return (
    <div className="page">
      <h1 className="heading">Продажи</h1>
      <FiltersComponent></FiltersComponent>
    </div>
  );
}