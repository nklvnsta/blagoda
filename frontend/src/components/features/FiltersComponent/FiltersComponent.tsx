import styles from "./FilterComponent.module.css";

import { ChevronRight } from "../../icons";
import { FilterDropdown } from "../FilterDropdown";
import { use, useEffect, useState } from "react";
import { useApi } from "../../../api";
import { Button } from "../../ui/Button";
import type { FiltersResponse } from "../../../api/types";


export function FiltersComponent() {
    const ALL_SHOPS_VALUE = "all";
    const ALL_CATEGORIES_VALUE = "all";
    
    const [selectedShop, setSelectedShop] = useState<string>(ALL_SHOPS_VALUE);
    const [selectedCategory, setSelectedCategory] = useState<string>(ALL_CATEGORIES_VALUE);
    const [selectedPeriod, setSelectedPeriod] = useState<string>();

    const filters = useApi<FiltersResponse>("/sales/filters");

    const shopOptions = filters.data
        ? [{ label: "Вся сеть", value: ALL_SHOPS_VALUE }, ...filters.data.shops.map((s) => ({ label: s.name, value: s.id }))]
        : [];
    const categoryOptions = filters.data
        ? [
            { label: "Все категории", value: ALL_CATEGORIES_VALUE },
            ...filters.data.categories.flatMap((category) => [
            { label: category.name, value: category.id },
            ...(category.children?.map((child) => ({ label: `— ${child.name}`, value: child.id })) ?? []),
            ]),
        ]
    : [];
    const periodOptions = filters.data
        ? filters.data.periods.map((p) => ({ label: p.label, value: p.code }))
        : [];
    
    useEffect(
        () => {
            if (periodOptions.length > 0 && !selectedPeriod) {
                setSelectedPeriod(periodOptions[0].value);
            }
        },
        [periodOptions, selectedPeriod]
    );

    return (
        <div className={styles.filters}>
            <div className={styles["filters-options"]}>
                <FilterDropdown
                    label="Магазин"
                    options={shopOptions}
                    value={selectedShop}
                    onChange={setSelectedShop}
                />
                <FilterDropdown
                    label="Категория"
                    options={categoryOptions}
                    value={selectedCategory}
                    onChange={setSelectedCategory}
                />
                <FilterDropdown
                    label="Период"
                    options={periodOptions}
                    value={selectedPeriod}
                    onChange={setSelectedPeriod}
                />
            </div>
            
            <div className={styles["filters-actions"]}>
                <Button type='secondary' onClick={() => console.log("Filters applied!")}>
                    Сбросить
                </Button>
                <Button onClick={() => console.log("Filters applied!")} icon={<ChevronRight />}>
                    Применить
                </Button>
            </div>
        </div>
    )
}