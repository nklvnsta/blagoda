import { getAuthHeaders } from '../auth/authStorage';
import { handleUnauthorized } from '../auth/AuthContext';
import { API_BASE } from './config';

export type MutateMethod = 'POST' | 'PATCH' | 'PUT' | 'DELETE';

export async function apiMutate<TResponse, TBody = unknown>(
  path: string,
  method: MutateMethod,
  body?: TBody,
): Promise<TResponse> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (res.status === 401) {
    handleUnauthorized();
    throw new Error('HTTP 401');
  }

  if (!res.ok) {
    let detail = '';
    try {
      const data = await res.json();
      detail = typeof data === 'string' ? data : JSON.stringify(data);
    } catch {
      detail = await res.text().catch(() => '');
    }
    throw new Error(`HTTP ${res.status}${detail ? `: ${detail}` : ''}`);
  }

  if (res.status === 204) {
    return undefined as TResponse;
  }

  return (await res.json()) as TResponse;
}
