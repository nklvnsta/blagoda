import { useEffect, useState } from 'react';

/**
 * Возвращает значение `value`, «отложенное» на `delayMs` миллисекунд.
 * Полезно, чтобы не спамить сеть на каждое нажатие клавиши в поиске.
 */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}
