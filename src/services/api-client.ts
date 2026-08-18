export type ApiPagination = {
  page: number;
  page_size: number;
  total: number;
};

export type ApiSuccess<T> = {
  success: true;
  data: T;
};

export type ApiList<T> = {
  success: true;
  data: T[];
  pagination: ApiPagination;
};

export type ApiErrorBody = {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string | null;
  };
};

export class ApiClientError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function formatApiErrorMessage(
  message: string | undefined,
  details: Record<string, unknown>,
  status: number,
): string {
  const errors = details.errors;
  if (Array.isArray(errors) && errors.length > 0) {
    const first = errors[0] as { loc?: unknown[]; msg?: string };
    const field = Array.isArray(first.loc)
      ? first.loc.filter((part) => part !== "body").join(".")
      : "";
    const detail = first.msg ?? "Invalid value";
    if (field) return `${field}: ${detail}`;
    return detail;
  }
  return message ?? `Request failed (${status})`;
}

function baseUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  // Empty/unset => same-origin requests via next.config.ts rewrite proxy (avoids CORS).
  if (url == null || url.trim() === "") {
    return "";
  }
  return url.replace(/\/$/, "");
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  signal?: AbortSignal;
};

function buildQuery(query?: RequestOptions["query"]): string {
  if (!query) return "";
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}${buildQuery(options.query)}`, {
      method: options.method ?? (options.body ? "POST" : "GET"),
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(typeof window !== "undefined" && window.localStorage.getItem("ps_access_token")
          ? { Authorization: `Bearer ${window.localStorage.getItem("ps_access_token")}` }
          : {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: options.signal,
      cache: "no-store",
    });
  } catch {
    throw new ApiClientError(
      0,
      "NETWORK_ERROR",
      "Cannot reach the API. Is the backend running on port 8000? If you just changed env/config, restart `next dev`.",
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let payload: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      const snippet = text.replace(/\s+/g, " ").slice(0, 180);
      throw new ApiClientError(
        response.status,
        "INVALID_JSON",
        response.status === 504 || /timeout|gateway|html/i.test(snippet)
          ? "The API took too long or returned an HTML error. Retry the step — long AI runs are split into shorter stages."
          : `API returned non-JSON response (${response.status}): ${snippet || "empty body"}`,
      );
    }
  }

  if (!response.ok) {
    const err = payload as ApiErrorBody | null;
    const details = err?.error?.details ?? {};
    throw new ApiClientError(
      response.status,
      err?.error?.code ?? "HTTP_ERROR",
      formatApiErrorMessage(err?.error?.message, details, response.status),
      details,
    );
  }

  return payload as T;
}

export async function apiGetData<T>(path: string, query?: RequestOptions["query"]): Promise<T> {
  const body = await apiRequest<ApiSuccess<T>>(path, { query });
  return body.data;
}

export async function apiGetList<T>(
  path: string,
  query?: RequestOptions["query"],
): Promise<{ items: T[]; pagination: ApiPagination }> {
  const body = await apiRequest<ApiList<T>>(path, { query });
  return { items: body.data, pagination: body.pagination };
}

export async function apiMutateData<T>(path: string, method: string, body?: unknown): Promise<T> {
  const response = await apiRequest<ApiSuccess<T>>(path, { method, body });
  return response.data;
}
