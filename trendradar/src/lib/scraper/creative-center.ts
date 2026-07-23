import { z } from "zod";
import { fetchJson, ScrapeError } from "@/lib/scraper/http";
import { optionalEnv } from "@/lib/env";
import {
  PAGE_SIZE,
  PAGES_PER_TARGET,
  TREND_PERIOD_DAYS,
  type CountryCode,
} from "@/lib/constants";

/**
 * Cliente del TikTok Creative Center.
 *
 * En vez de scrapear el DOM (frágil, requiere headless browser), pegamos a la
 * API JSON interna que alimenta https://ads.tiktok.com/business/creativecenter.
 * Los paths están centralizados en ENDPOINTS: si TikTok los mueve, se corrige
 * en un solo lugar.
 *
 * Contrato defensivo: los schemas Zod declaran como REQUERIDOS los campos que
 * persistimos. Si TikTok renombra o elimina un campo, el parseo falla con
 * error descriptivo (incluye el payload ofensivo), la corrida queda marcada
 * como 'failed' en scrape_runs, y la UI sigue sirviendo el último dato bueno.
 * Nunca degradamos en silencio.
 */

const BASE = "https://ads.tiktok.com/creative_radar_api/v1/popular_trend";

const ENDPOINTS = {
  hashtags: `${BASE}/hashtag/list`,
  sounds: `${BASE}/sound/rank_list`,
  videos: `${BASE}/list`,
} as const;

function buildHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "user-agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    referer:
      "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en",
    accept: "application/json",
    lang: "en",
    // id anónimo por corrida: suficiente para los listados públicos
    "anonymous-user-id": crypto.randomUUID(),
  };
  // Si TikTok empieza a exigir firma, se setean estas env y se propagan acá
  // (se obtienen del DevTools del navegador en una sesión del Creative Center).
  const userSign = optionalEnv("TIKTOK_CC_USER_SIGN");
  const timestamp = optionalEnv("TIKTOK_CC_TIMESTAMP");
  const webId = optionalEnv("TIKTOK_CC_WEB_ID");
  if (userSign) headers["user-sign"] = userSign;
  if (timestamp) headers["timestamp"] = timestamp;
  if (webId) headers["web-id"] = webId;
  return headers;
}

// ---------------------------------------------------------------------------
// Schemas de respuesta. `passthrough()` conserva campos extra (van a `raw`),
// pero los campos que persistimos son requeridos: su ausencia = falla ruidosa.
// ---------------------------------------------------------------------------

const envelopeSchema = z.object({
  code: z.number(),
  msg: z.string().optional(),
  data: z.unknown(),
});

const trendPointSchema = z.object({
  time: z.number(),
  value: z.number(),
});

const hashtagItemSchema = z
  .object({
    hashtag_name: z.string().min(1),
    rank: z.number(),
    hashtag_id: z.string().optional(),
    rank_diff: z.number().nullish(),
    rank_diff_type: z.number().nullish(),
    publish_cnt: z.number().nullish(),
    video_views: z.number().nullish(),
    industry_info: z
      .object({
        id: z.number().nullish(),
        value: z.string().nullish(),
        label: z.string().nullish(),
      })
      .passthrough()
      .nullish(),
    trend: z.array(trendPointSchema).nullish(),
  })
  .passthrough();

const hashtagDataSchema = z
  .object({ list: z.array(hashtagItemSchema) })
  .passthrough();

const soundItemSchema = z
  .object({
    title: z.string().min(1),
    rank: z.number(),
    clip_id: z.string().nullish(),
    song_id: z.string().nullish(),
    author: z.string().nullish(),
    duration: z.number().nullish(),
    cover: z.string().nullish(),
    link: z.string().nullish(),
    rank_diff: z.number().nullish(),
    trend: z.array(trendPointSchema).nullish(),
  })
  .passthrough();

const soundDataSchema = z
  .object({ sound_list: z.array(soundItemSchema) })
  .passthrough();

const videoItemSchema = z
  .object({
    item_id: z.string().min(1),
    title: z.string().nullish(),
    cover_url: z.string().nullish(),
    item_url: z.string().nullish(),
    tt_link: z.string().nullish(),
    duration: z.number().nullish(),
    vv: z.number().nullish(),          // views
    liked_cnt: z.number().nullish(),
    comment_cnt: z.number().nullish(),
    share_cnt: z.number().nullish(),
  })
  .passthrough();

const videoDataSchema = z
  .object({ videos: z.array(videoItemSchema) })
  .passthrough();

// ---------------------------------------------------------------------------
// Tipos normalizados que consume la capa de persistencia
// ---------------------------------------------------------------------------

export interface ScrapedHashtag {
  externalId: string; // nombre en minúsculas, sin '#'
  displayName: string;
  rank: number;
  rankDiff: number | null;
  videoCount: number | null; // publish_cnt
  viewCount: number | null;  // video_views
  categoryId: number | null;
  categoryName: string | null;
  raw: Record<string, unknown>;
}

export interface ScrapedSound {
  externalId: string; // clip_id ?? song_id
  displayName: string;
  author: string | null;
  rank: number;
  rankDiff: number | null;
  raw: Record<string, unknown>;
}

export interface ScrapedVideo {
  videoId: string;
  title: string | null;
  videoUrl: string | null;
  coverUrl: string | null;
  durationSeconds: number | null;
  viewCount: number | null;
  likeCount: number | null;
  commentCount: number | null;
  shareCount: number | null;
  raw: Record<string, unknown>;
}

// ---------------------------------------------------------------------------

function buildUrl(
  endpoint: string,
  country: CountryCode,
  page: number,
  extra: Record<string, string>
): string {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(PAGE_SIZE),
    period: String(TREND_PERIOD_DAYS),
    country_code: country,
    ...extra,
  });
  return `${endpoint}?${params.toString()}`;
}

/** Valida el envelope {code, msg, data} y devuelve `data`. code!=0 = falla ruidosa. */
function unwrapEnvelope(url: string, payload: unknown): unknown {
  const envelope = envelopeSchema.safeParse(payload);
  if (!envelope.success) {
    throw new ScrapeError(
      `El envelope de la respuesta cambió de forma (esperaba {code, msg, data})`,
      { url, bodySnippet: JSON.stringify(payload).slice(0, 500) }
    );
  }
  if (envelope.data.code !== 0) {
    throw new ScrapeError(
      `El Creative Center devolvió code=${envelope.data.code} msg="${envelope.data.msg ?? ""}" — probable rate limit o firma requerida`,
      { url, bodySnippet: JSON.stringify(payload).slice(0, 500) }
    );
  }
  return envelope.data.data;
}

function parseListOrThrow<T>(
  url: string,
  schema: z.ZodType<T>,
  data: unknown,
  what: string
): T {
  const parsed = schema.safeParse(data);
  if (!parsed.success) {
    throw new ScrapeError(
      `El contrato de ${what} cambió: ${parsed.error.issues
        .slice(0, 3)
        .map((issue) => `${issue.path.join(".")}: ${issue.message}`)
        .join("; ")}`,
      { url, bodySnippet: JSON.stringify(data).slice(0, 500) }
    );
  }
  return parsed.data;
}

export async function fetchHashtags(
  country: CountryCode
): Promise<ScrapedHashtag[]> {
  const headers = buildHeaders();
  const items: ScrapedHashtag[] = [];
  for (let page = 1; page <= PAGES_PER_TARGET; page++) {
    const url = buildUrl(ENDPOINTS.hashtags, country, page, {
      sort_by: "popular",
    });
    const data = unwrapEnvelope(url, await fetchJson(url, headers));
    const { list } = parseListOrThrow(url, hashtagDataSchema, data, "hashtags");
    for (const item of list) {
      items.push({
        externalId: item.hashtag_name.toLowerCase().replace(/^#/, ""),
        displayName: item.hashtag_name,
        rank: item.rank,
        rankDiff: item.rank_diff ?? null,
        videoCount: item.publish_cnt ?? null,
        viewCount: item.video_views ?? null,
        categoryId: item.industry_info?.id ?? null,
        categoryName:
          item.industry_info?.value ?? item.industry_info?.label ?? null,
        raw: item,
      });
    }
    if (list.length < PAGE_SIZE) break; // no hay más páginas
  }
  return items;
}

export async function fetchSounds(country: CountryCode): Promise<ScrapedSound[]> {
  const headers = buildHeaders();
  const items: ScrapedSound[] = [];
  for (let page = 1; page <= PAGES_PER_TARGET; page++) {
    const url = buildUrl(ENDPOINTS.sounds, country, page, {
      rank_type: "popular",
    });
    const data = unwrapEnvelope(url, await fetchJson(url, headers));
    const { sound_list } = parseListOrThrow(url, soundDataSchema, data, "sonidos");
    for (const item of sound_list) {
      const externalId = item.clip_id ?? item.song_id;
      if (!externalId) {
        throw new ScrapeError(
          `Sonido sin clip_id ni song_id ("${item.title}") — cambió el identificador`,
          { url, bodySnippet: JSON.stringify(item).slice(0, 500) }
        );
      }
      items.push({
        externalId,
        displayName: item.title,
        author: item.author ?? null,
        rank: item.rank,
        rankDiff: item.rank_diff ?? null,
        raw: item,
      });
    }
    if (sound_list.length < PAGE_SIZE) break;
  }
  return items;
}

export async function fetchVideos(country: CountryCode): Promise<ScrapedVideo[]> {
  const headers = buildHeaders();
  const url = buildUrl(ENDPOINTS.videos, country, 1, { order_by: "vv" });
  const data = unwrapEnvelope(url, await fetchJson(url, headers));
  const { videos } = parseListOrThrow(url, videoDataSchema, data, "videos");
  return videos.map((item) => ({
    videoId: item.item_id,
    title: item.title ?? null,
    videoUrl: item.item_url ?? item.tt_link ?? null,
    coverUrl: item.cover_url ?? null,
    durationSeconds: item.duration ?? null,
    viewCount: item.vv ?? null,
    likeCount: item.liked_cnt ?? null,
    commentCount: item.comment_cnt ?? null,
    shareCount: item.share_cnt ?? null,
    raw: item,
  }));
}
