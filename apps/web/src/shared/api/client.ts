import { apiUrl } from "@/shared/config";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      `API ${response.status} for ${path}. Start the control plane with scripts/dev.ps1 or scripts/dev.sh.`,
      response.status,
      body,
    );
  }
  return body as T;
}
