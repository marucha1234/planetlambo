import type { SupabaseClient } from "@supabase/supabase-js";
import { supabaseAdmin } from "@/lib/supabase/admin";
import { sleep } from "@/lib/scraper/http";
import {
  fetchHashtags,
  fetchSounds,
  fetchVideos,
  type ScrapedHashtag,
  type ScrapedSound,
} from "@/lib/scraper/creative-center";
import {
  COUNTRIES,
  SCRAPE_TARGETS,
  type CountryCode,
  type ScrapeTarget,
} from "@/lib/constants";

/**
 * Orquestación de la ingesta. Corre secuencialmente target×país con pausa
 * entre requests (politeness / rate limit). Cada combinación se registra en
 * scrape_runs: si una falla, se loguea y se sigue con la siguiente — una
 * corrida parcial es mejor que ninguna, y el histórico nunca se corrompe
 * porque los snapshots son append-only.
 */

/** Pausa entre targets para no golpear el rate limit del Creative Center. */
const DELAY_BETWEEN_TARGETS_MS = 1_500;

export interface TargetResult {
  target: ScrapeTarget;
  country: CountryCode;
  status: "success" | "failed";
  items: number;
  error?: string;
}

export interface IngestionSummary {
  capturedAt: string;
  results: TargetResult[];
  succeeded: number;
  failed: number;
}

async function openRun(
  db: SupabaseClient,
  target: ScrapeTarget,
  country: CountryCode
): Promise<number> {
  const { data, error } = await db
    .from("scrape_runs")
    .insert({ target, country_code: country })
    .select("id")
    .single();
  if (error) throw new Error(`No pude abrir scrape_run: ${error.message}`);
  return data.id as number;
}

async function closeRun(
  db: SupabaseClient,
  runId: number,
  outcome:
    | { status: "success"; items: number }
    | { status: "failed"; message: string; detail?: unknown }
): Promise<void> {
  const patch =
    outcome.status === "success"
      ? { status: "success", items_ingested: outcome.items, finished_at: new Date().toISOString() }
      : {
          status: "failed",
          error_message: outcome.message.slice(0, 2000),
          error_detail: outcome.detail ?? null,
          finished_at: new Date().toISOString(),
        };
  const { error } = await db.from("scrape_runs").update(patch).eq("id", runId);
  if (error) console.error(`[ingest] no pude cerrar scrape_run ${runId}: ${error.message}`);
}

/**
 * Upsert de entidades en `trends` y devuelve mapa external_id → uuid.
 * `last_seen_at` se actualiza en cada aparición; `first_seen_at` queda fijo.
 */
async function upsertTrends(
  db: SupabaseClient,
  entityType: "hashtag" | "sound",
  entities: { externalId: string; displayName: string; author?: string | null }[]
): Promise<Map<string, string>> {
  if (entities.length === 0) return new Map();
  const rows = entities.map((entity) => ({
    entity_type: entityType,
    external_id: entity.externalId,
    display_name: entity.displayName,
    author: entity.author ?? null,
    last_seen_at: new Date().toISOString(),
  }));
  const { data, error } = await db
    .from("trends")
    .upsert(rows, { onConflict: "entity_type,external_id" })
    .select("id, external_id");
  if (error) throw new Error(`Upsert de trends falló: ${error.message}`);
  return new Map(data.map((row) => [row.external_id as string, row.id as string]));
}

async function ingestHashtags(
  db: SupabaseClient,
  runId: number,
  country: CountryCode,
  capturedAt: string
): Promise<number> {
  const hashtags: ScrapedHashtag[] = await fetchHashtags(country);
  const idMap = await upsertTrends(db, "hashtag", hashtags);
  const snapshots = hashtags.map((hashtag) => ({
    trend_id: idMap.get(hashtag.externalId),
    scrape_run_id: runId,
    captured_at: capturedAt,
    country_code: country,
    category_id: hashtag.categoryId,
    category_name: hashtag.categoryName,
    rank: hashtag.rank,
    rank_diff: hashtag.rankDiff,
    video_count: hashtag.videoCount,
    view_count: hashtag.viewCount,
    raw: hashtag.raw,
  }));
  const { error } = await db.from("trend_snapshots").insert(snapshots);
  if (error) throw new Error(`Insert de snapshots de hashtags falló: ${error.message}`);
  return snapshots.length;
}

async function ingestSounds(
  db: SupabaseClient,
  runId: number,
  country: CountryCode,
  capturedAt: string
): Promise<number> {
  const sounds: ScrapedSound[] = await fetchSounds(country);
  const idMap = await upsertTrends(db, "sound", sounds);
  const snapshots = sounds.map((sound) => ({
    trend_id: idMap.get(sound.externalId),
    scrape_run_id: runId,
    captured_at: capturedAt,
    country_code: country,
    rank: sound.rank,
    rank_diff: sound.rankDiff,
    raw: sound.raw,
  }));
  const { error } = await db.from("trend_snapshots").insert(snapshots);
  if (error) throw new Error(`Insert de snapshots de sonidos falló: ${error.message}`);
  return snapshots.length;
}

async function ingestVideos(
  db: SupabaseClient,
  runId: number,
  country: CountryCode,
  capturedAt: string
): Promise<number> {
  const videos = await fetchVideos(country);
  const rows = videos.map((video) => ({
    scrape_run_id: runId,
    captured_at: capturedAt,
    country_code: country,
    video_id: video.videoId,
    title: video.title,
    video_url: video.videoUrl,
    cover_url: video.coverUrl,
    duration_seconds: video.durationSeconds,
    view_count: video.viewCount,
    like_count: video.likeCount,
    comment_count: video.commentCount,
    share_count: video.shareCount,
    raw: video.raw,
  }));
  const { error } = await db.from("video_snapshots").insert(rows);
  if (error) throw new Error(`Insert de video_snapshots falló: ${error.message}`);
  return rows.length;
}

const INGESTORS: Record<
  ScrapeTarget,
  (db: SupabaseClient, runId: number, country: CountryCode, capturedAt: string) => Promise<number>
> = {
  hashtags: ingestHashtags,
  sounds: ingestSounds,
  videos: ingestVideos,
};

export async function runIngestion(): Promise<IngestionSummary> {
  const db = supabaseAdmin();
  // Todos los snapshots de la corrida comparten timestamp → series limpias.
  const capturedAt = new Date().toISOString();
  const results: TargetResult[] = [];

  for (const country of COUNTRIES) {
    for (const target of SCRAPE_TARGETS) {
      const runId = await openRun(db, target, country);
      try {
        const items = await INGESTORS[target](db, runId, country, capturedAt);
        await closeRun(db, runId, { status: "success", items });
        results.push({ target, country, status: "success", items });
        console.log(`[ingest] ok ${target}/${country}: ${items} items`);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        const detail =
          err instanceof Error && "context" in err
            ? (err as { context: unknown }).context
            : null;
        await closeRun(db, runId, { status: "failed", message, detail });
        results.push({ target, country, status: "failed", items: 0, error: message });
        console.error(`[ingest] FALLO ${target}/${country}: ${message}`, detail ?? "");
      }
      await sleep(DELAY_BETWEEN_TARGETS_MS);
    }
  }

  const succeeded = results.filter((result) => result.status === "success").length;
  return {
    capturedAt,
    results,
    succeeded,
    failed: results.length - succeeded,
  };
}
