export function getApiBaseUrl(): string {
  const explicit = import.meta.env.VITE_API_URL;
  if (typeof explicit === "string" && explicit.length > 0) {
    return explicit.replace(/\/$/, "");
  }
  return "";
}

export function apiUrl(path: string): string {
  const base = getApiBaseUrl();
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}
