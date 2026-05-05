const API_ROOT =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD
    ? "https://coupangproductresearchtool.vercel.app/api"
    : "http://127.0.0.1:8010");

async function request(path, options = {}) {
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers ?? {}),
  };

  const response = await fetch(`${API_ROOT}${path}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export function fetchScoredCompetitors() {
  return request("/competitors/scored");
}

export function fetchProfitHistory() {
  return request("/profit/history?limit=20");
}

export function fetchOpenApiStatus() {
  return request("/coupang/openapi/status");
}

export function fetchListingAssets(competitorId) {
  return request(`/competitors/${competitorId}/listing-assets`);
}

export function fetchCompetitorAnalysis(competitorId) {
  return request(`/competitors/${competitorId}/analysis`);
}

export function createProfitCalculation(payload) {
  return request("/profit/calculate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
