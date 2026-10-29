// Same-origin by default: Vite (dev) and nginx (Docker) both proxy /api to
// Flask. VITE_API_URL is only needed when the API lives on another host.
const API_BASE = `${import.meta.env.VITE_API_URL ?? ""}/api/v1`;

export async function apiGet(path, lang) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${API_BASE}${path}${separator}lang=${lang}`);
  if (!response.ok) throw new Error(`GET ${path} failed with ${response.status}`);
  return (await response.json()).data;
}
