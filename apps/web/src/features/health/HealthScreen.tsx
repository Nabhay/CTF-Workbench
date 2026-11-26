import { useQuery } from "@tanstack/react-query";

import { getHealth, type HealthResponse } from "@/shared/api/health";
import { getApiBaseUrl } from "@/shared/config";

export function HealthScreen() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 4000,
  });
  const apiBase = getApiBaseUrl() || "(same origin)";

  return (
    <main className="min-h-screen bg-chassis text-paper">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-between px-6 py-12 md:px-10 md:py-16">
        <header>
          <p className="font-mono text-sm text-lamp">CTF Workbench</p>
          <h1 className="mt-6 max-w-lg text-4xl font-semibold tracking-tight md:text-5xl">
            Bench check before the event.
          </h1>
          <p className="mt-5 max-w-md text-lg leading-relaxed text-mute">
            The control plane is up when the lamp is sage. Challenge files, tools, and agents
            arrive in later milestones.
          </p>
        </header>

        <section className="mt-16 border-t border-edge pt-8" aria-live="polite">
          {health.isPending ? <StatusLine label="Control plane" state="loading" /> : null}
          {health.isError ? (
            <>
              <StatusLine label="Control plane" state="down" />
              <p className="mt-6 max-w-lg text-fault">
                {health.error instanceof Error
                  ? health.error.message
                  : "The API did not respond."}{" "}
                Start it with <code className="font-mono text-paper">scripts/dev.ps1</code> or{" "}
                <code className="font-mono text-paper">scripts/dev.sh</code>, then wait for this
                page to refresh.
              </p>
            </>
          ) : null}
          {health.data ? <HealthDetails data={health.data} /> : null}
        </section>

        <footer className="mt-16 font-mono text-xs leading-6 text-mute">
          <div>API base {apiBase}</div>
          <div>GET /api/v1/health</div>
        </footer>
      </div>
    </main>
  );
}

function HealthDetails({ data }: { data: HealthResponse }) {
  return (
    <dl className="grid gap-4">
      <StatusLine label="Control plane" state="up" detail={`v${data.version} on ${data.bind}`} />
      <Row label="Data root" value={data.data_root} />
      <Row label="Database" value={`${data.database_status} · ${data.database}`} />
      <Row
        label="Docker"
        value={data.docker_configured ? "host configured" : "not configured yet"}
      />
      <Row label="Worker" value="separate process; use --check to prove it starts" />
    </dl>
  );
}

function StatusLine({
  label,
  state,
  detail,
}: {
  label: string;
  state: "up" | "down" | "loading";
  detail?: string;
}) {
  const lamp =
    state === "up" ? "bg-sage" : state === "down" ? "bg-fault" : "bg-lamp/60";
  const word = state === "up" ? "reachable" : state === "down" ? "not reachable" : "checking";
  return (
    <div className="flex items-baseline gap-3">
      <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${lamp}`} aria-hidden="true" />
      <span className="w-36 text-paper">{label}</span>
      <span className="font-mono text-sm text-mute">
        {word}
        {detail ? ` · ${detail}` : ""}
      </span>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-3">
      <dt className="w-36 shrink-0 text-mute">{label}</dt>
      <dd className="font-mono text-sm break-all">{value}</dd>
    </div>
  );
}
