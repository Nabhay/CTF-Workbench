import { fetchJson } from "@/shared/api/client";

export type HealthResponse = {
  status: "ok";
  version: string;
  api: "ok";
  bind: string;
  data_root: string;
  database: string;
  docker_configured: boolean;
  worker: "separate_process";
};

export function getHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>("/api/v1/health");
}
