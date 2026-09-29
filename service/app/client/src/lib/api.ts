const BASE = '/api';

function buildParams(companyCodes: string[], fiscalYears: string[]): string {
  const params = new URLSearchParams();
  if (companyCodes.length) params.set('companyCodes', companyCodes.join(','));
  if (fiscalYears.length) params.set('fiscalYears', fiscalYears.join(','));
  return params.toString();
}

/** Convert snake_case keys to camelCase recursively */
function camelizeKey(key: string): string {
  return key.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
}

function camelizeKeys(obj: any): any {
  if (Array.isArray(obj)) return obj.map(camelizeKeys);
  if (obj !== null && typeof obj === 'object') {
    const out: any = {};
    for (const [k, v] of Object.entries(obj)) {
      out[camelizeKey(k)] = camelizeKeys(v);
    }
    return out;
  }
  return obj;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const json = await res.json();
  return camelizeKeys(json) as T;
}

export function fetchFilters(): Promise<{ companyCodes: string[]; fiscalYears: string[] }> {
  return get('/filters');
}

export function fetchOverview(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/overview?${qs}`);
}

export function fetchGeneralLedger(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/general-ledger?${qs}`);
}

export function fetchCostCenters(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/cost-centers?${qs}`);
}

export function fetchProfitCenters(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/profit-centers?${qs}`);
}

export function fetchAccountsPayable(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/accounts-payable?${qs}`);
}

export function fetchLargestInvoices(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any[]>(`/accounts-payable/largest?${qs}`);
}

export function fetchAccountsReceivable(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/accounts-receivable?${qs}`);
}

export function fetchOverdueInvoices(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any[]>(`/accounts-receivable/overdue?${qs}`);
}

export function fetchPeriodAnalysis(cc: string[], fy: string[]) {
  const qs = buildParams(cc, fy);
  return get<any>(`/period-analysis?${qs}`);
}

export function fetchLineage() {
  return get<any>('/lineage');
}

export async function fetchAnalyst(messages: { role: string; content: string }[]) {
  const res = await fetch(`${BASE}/analyst`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
