export const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";
export const BACKEND_URL_STORAGE_KEY = "roleChatbotDesktopBackendUrl";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getBackendUrl(): string {
  return window.localStorage.getItem(BACKEND_URL_STORAGE_KEY) || DEFAULT_BACKEND_URL;
}

export function setBackendUrl(value: string): string {
  const normalized = value.trim().replace(/\/+$/, "");
  if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
    throw new Error("后端地址必须以 http:// 或 https:// 开头");
  }
  window.localStorage.setItem(BACKEND_URL_STORAGE_KEY, normalized);
  return normalized;
}

export function resolveAssetUrl(path: string | null | undefined): string {
  if (!path) {
    return "";
  }
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  return `${getBackendUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const body = options.body;
  const isFormData = body instanceof FormData;
  const response = await fetch(`${getBackendUrl()}${path}`, {
    ...options,
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || `${response.status} ${response.statusText}`;
    throw new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail), response.status);
  }
  return payload as T;
}
