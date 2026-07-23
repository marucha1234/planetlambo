import { NextResponse } from "next/server";
import { runIngestion } from "@/lib/scraper/ingest";
import { requireEnv } from "@/lib/env";

export const dynamic = "force-dynamic";
// 15 targets × (requests + pausas): necesita más que los 10s default.
export const maxDuration = 300;

/**
 * Endpoint del cron de Vercel (cada 6h, ver vercel.json).
 * Vercel manda `Authorization: Bearer ${CRON_SECRET}` automáticamente cuando
 * la env CRON_SECRET está seteada en el proyecto.
 */
export async function GET(request: Request) {
  const auth = request.headers.get("authorization");
  if (auth !== `Bearer ${requireEnv("CRON_SECRET")}`) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const summary = await runIngestion();

  // Corrida totalmente fallida → 500 para que Vercel la marque y alerte.
  // Parcial → 200 con el detalle: hay dato nuevo, y las fallas quedaron
  // logueadas en scrape_runs.
  const status = summary.succeeded === 0 ? 500 : 200;
  return NextResponse.json(summary, { status });
}
