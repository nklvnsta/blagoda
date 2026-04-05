import { useEffect, useRef, useState } from "react";
import styles from "./FilterDropdown.module.css";
import { ChevronDown } from "../../icons";

type Option = {
  label: string;
  value: string;
};

type FilterDropdownProps = {
  label?: string;
  options: Option[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
};

export function FilterDropdown({
  label,
  options,
  value,
  defaultValue,
  onChange,
}: FilterDropdownProps) {
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = useState(defaultValue || options[0]?.value);
  const [open, setOpen] = useState(false);

  const ref = useRef<HTMLDivElement>(null);

  const selectedValue = isControlled ? value : internalValue;
  const selectedOption = options.find((o) => o.value === selectedValue);

  const handleSelect = (val: string) => {
    if (!isControlled) setInternalValue(val);
    onChange?.(val);
    setOpen(false);
  };

  // закрытие при клике вне
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className={styles.wrapper} ref={ref}>
      <div className={styles.control} onClick={() => setOpen((o) => !o)}>
        {label && <span className={styles.label}>{label}</span>}

        <div className={styles.valueBlock}>
          <span className={styles.value}>
            {selectedOption?.label}
          </span>

          <span className={`${styles.icon} ${open ? styles.open : ""}`}>
            <ChevronDown />
          </span>
        </div>
      </div>

      <div className={`${styles.menu} ${open ? styles.menuOpen : ""}`}>
        {options.map((option) => (
          <div
            key={option.value}
            className={`${styles.option} ${
              option.value === selectedValue ? styles.selected : ""
            }`}
            onClick={() => handleSelect(option.value)}
          >
            {option.label}
          </div>
        ))}
      </div>
    </div>
  );
};