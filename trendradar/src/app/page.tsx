import { hasSupabaseEnv } from "@/lib/env";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { COUNTRY_NAMES, type CountryCode } from "@/lib/constants";

export const dynamic = "force-dynamic";

/**
 * Página de estado de la ingesta (placeholder hasta la UI de Fase 4).
 * Muestra el último dato bueno por target×país aunque la última corrida haya
 * fallado: la app nunca se cae porque el scraper falló.
 */

interface RunRow {
  target: string;
  country_code: string;
  finished_at: string | null;
  items_ingested: number;
  status: string;
  error_message: string | null;
}

async function loadStatus(): Promise<{
  lastGood: RunRow[];
  recentFailures: RunRow[];
  error?: string;
}> {
  try {
    const db = supabaseAdmin();
    const [goodResult, failResult] = await Promise.all([
      db.from("latest_successful_runs").select(
        "target, country_code, finished_at, items_ingested, status, error_message"
      ),
      db
        .from("scrape_runs")
        .select("target, country_code, finished_at, items_ingested, status, error_message")
        .eq("status", "failed")
        .order("started_at", { ascending: false })
        .limit(10),
    ]);
    if (goodResult.error) throw new Error(goodResult.error.message);
    if (failResult.error) throw new Error(failResult.error.message);
    return { lastGood: goodResult.data ?? [], recentFailures: failResult.data ?? [] };
  } catch (err) {
    return {
      lastGood: [],
      recentFailures: [],
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

function formatTs(ts: string | null): string {
  if (!ts) return "—";
  return new Date(ts).toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

export default async function StatusPage() {
  if (!hasSupabaseEnv()) {
    return (
      <p className="text-terminal-dim">
        Supabase sin configurar. Copiá <code>.env.example</code> a{" "}
        <code>.env.local</code> y completá las credenciales.
      </p>
    );
  }

  const { lastGood, recentFailures, error } = await loadStatus();

  return (
    <div className="space-y-8 max-w-4xl">
      <section>
        <h2 className="text-terminal-amber text-sm mb-2">
          ▌ESTADO DE INGESTA — último dato bueno por target × país
        </h2>
        {error ? (
          <p className="text-terminal-red text-sm">
            Error consultando la base: {error}
          </p>
        ) : lastGood.length === 0 ? (
          <p className="text-terminal-dim text-sm">
            Sin corridas exitosas todavía. Ejecutá el cron:{" "}
            <code>GET /api/cron/ingest</code> con{" "}
            <code>Authorization: Bearer $CRON_SECRET</code>
          </p>
        ) : (
          <table className="text-sm w-full">
            <thead>
              <tr className="text-terminal-dim text-left border-b border-terminal-border">
                <th className="py-1 pr-4">TARGET</th>
                <th className="py-1 pr-4">PAÍS</th>
                <th className="py-1 pr-4">ÍTEMS</th>
                <th className="py-1">DATOS AL</th>
              </tr>
            </thead>
            <tbody>
              {lastGood.map((run) => (
                <tr
                  key={`${run.target}-${run.country_code}`}
                  className="border-b border-terminal-border/50"
                >
                  <td className="py-1 pr-4">{run.target}</td>
                  <td className="py-1 pr-4">
                    {COUNTRY_NAMES[run.country_code as CountryCode] ??
                      run.country_code}
                  </td>
                  <td className="py-1 pr-4 text-terminal-green">
                    {run.items_ingested}
                  </td>
                  <td className="py-1 text-terminal-dim">
                    {formatTs(run.finished_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {recentFailures.length > 0 && (
        <section>
          <h2 className="text-terminal-red text-sm mb-2">▌FALLAS RECIENTES</h2>
          <ul className="text-xs space-y-1">
            {recentFailures.map((run, index) => (
              <li key={index} className="text-terminal-dim">
                <span className="text-terminal-red">
                  {formatTs(run.finished_at)}
                </span>{" "}
                {run.target}/{run.country_code} — {run.error_message}
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-terminal-dim text-xs">
        Radar / Detalle / Watchlist llegan en la fase de UI.
      </p>
    </div>
  );
}
