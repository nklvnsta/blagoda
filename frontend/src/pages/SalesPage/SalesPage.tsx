import { useState } from "react";
import { useApi } from "../../api";
import { StatCard } from "../../components/features/StatCard";
import { FilterDropdown } from "../../components/features/FilterDropdown";
import type { FiltersResponse, SalesData } from "../../api/types";
import { FiltersComponent } from "../../components/features/FiltersComponent/FiltersComponent";
export function SalesPage() {
  

  

  return (
    <div className="page">
      <h1 className="heading">Продажи</h1>
      <FiltersComponent></FiltersComponent>
    </div>
  );
}