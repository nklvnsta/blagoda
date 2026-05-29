import styles from "./FilterComponent.module.css";

import { ChevronRight } from "../../icons";
import { FilterDropdown } from "../FilterDropdown";
import { useEffect, useState } from "react";
import { useApi } from "../../../api";
import { Button } from "../../ui/Button";
import type { FiltersResponse } from "../../../api/types";

export interface FilterValues {
    shopId?: string;
    categoryId?: string;
    periodCode?: string;
    dateFrom?: string;
    dateTo?: string;
}

interface FiltersComponentProps {
    onApply?: (filters: FilterValues) => void;
}

const ALL_SHOPS_VALUE = "all";
const ALL_CATEGORIES_VALUE = "all";
const CUSTOM_PERIOD = "custom";

export function FiltersComponent({ onApply }: FiltersComponentProps) {
    const [selectedShop, setSelectedShop] = useState<string>(ALL_SHOPS_VALUE);
    const [selectedCategory, setSelectedCategory] = useState<string>(ALL_CATEGORIES_VALUE);
    const [selectedPeriod, setSelectedPeriod] = useState<string>();
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const [dateError, setDateError] = useState<string | null>(null);

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

    const defaultPeriod = filters.data?.defaults.period ?? "last_7_days";

    useEffect(() => {
        if (periodOptions.length > 0 && !selectedPeriod) {
            setSelectedPeriod(periodOptions[0].value);
        }
    }, [periodOptions, selectedPeriod]);

    const isCustomPeriod = selectedPeriod === CUSTOM_PERIOD;

    const buildValues = (): FilterValues | null => {
        if (isCustomPeriod) {
            if (!dateFrom || !dateTo) {
                setDateError("Укажите даты начала и конца периода");
                return null;
            }
            if (dateFrom > dateTo) {
                setDateError("Дата начала не может быть позже даты окончания");
                return null;
            }
        }
        setDateError(null);
        return {
            shopId: selectedShop !== ALL_SHOPS_VALUE ? selectedShop : undefined,
            categoryId: selectedCategory !== ALL_CATEGORIES_VALUE ? selectedCategory : undefined,
            periodCode: selectedPeriod,
            dateFrom: isCustomPeriod ? dateFrom : undefined,
            dateTo: isCustomPeriod ? dateTo : undefined,
        };
    };

    const handleApply = () => {
        const values = buildValues();
        if (values && onApply) {
            onApply(values);
        }
    };

    const handleReset = () => {
        setSelectedShop(ALL_SHOPS_VALUE);
        setSelectedCategory(ALL_CATEGORIES_VALUE);
        setSelectedPeriod(defaultPeriod);
        setDateFrom("");
        setDateTo("");
        setDateError(null);
        if (onApply) {
            onApply({
                shopId: undefined,
                categoryId: undefined,
                periodCode: defaultPeriod,
            });
        }
    };

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
                    onChange={(value) => {
                        setSelectedPeriod(value);
                        if (value !== CUSTOM_PERIOD) {
                            setDateFrom("");
                            setDateTo("");
                            setDateError(null);
                        }
                    }}
                />
                {isCustomPeriod && (
                    <div className={styles.dateRange}>
                        <label className={styles.dateField}>
                            <span className={styles.dateLabel}>С</span>
                            <input
                                type="date"
                                className={styles.dateInput}
                                value={dateFrom}
                                onChange={(e) => setDateFrom(e.target.value)}
                            />
                        </label>
                        <label className={styles.dateField}>
                            <span className={styles.dateLabel}>По</span>
                            <input
                                type="date"
                                className={styles.dateInput}
                                value={dateTo}
                                onChange={(e) => setDateTo(e.target.value)}
                            />
                        </label>
                    </div>
                )}
            </div>

            {dateError && <p className={styles.dateError}>{dateError}</p>}

            <div className={styles["filters-actions"]}>
                <Button type="secondary" onClick={handleReset}>
                    Сбросить
                </Button>
                <Button onClick={handleApply} icon={<ChevronRight />}>
                    Применить
                </Button>
            </div>
        </div>
    );
}
