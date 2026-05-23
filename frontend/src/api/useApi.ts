import { useEffect, useState } from 'react';
import { getAuthHeaders } from '../auth/authStorage';
import { handleUnauthorized } from '../auth/AuthContext';
import { API_BASE } from './config';

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApi<T>(path: string, params?: Record<string, string | undefined>): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const query = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) query.set(k, v);
    }
  }
  const qs = query.toString();
  const url = `${API_BASE}${path}${qs ? `?${qs}` : ''}`;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(url, { headers: getAuthHeaders() })
      .then((res) => {
        if (res.status === 401) {
          handleUnauthorized();
          throw new Error('HTTP 401');
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        if (!cancelled) setData(json as T);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [url]);

  return { data, loading, error };
}
