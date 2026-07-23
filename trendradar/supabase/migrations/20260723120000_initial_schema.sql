-- ============================================================================
-- TrendRadar — schema inicial
--
-- Principio de diseño: el histórico ES el producto. Las tablas de snapshots
-- son append-only: nunca se actualizan ni se borran filas. Cada corrida del
-- scraper agrega una capa nueva con timestamp, y las series temporales se
-- derivan de ahí.
--
-- Entidades:
--   trends            dimensión canónica (hashtag o sonido), única por tipo+id
--   trend_snapshots   serie temporal append-only por (trend, país, corrida)
--   video_snapshots   videos top por país y corrida (ejemplos, no entidades)
--   scrape_runs       observabilidad de la ingesta: cada target×país por corrida
--   trend_scores      salida del motor de scoring (Fase 2), append-only
--   insights          fichas generadas por Claude (Fase 3), append-only
--   watchlist_items   tendencias marcadas por el usuario
--   alerts            alertas disparadas por cruces de umbral
-- ============================================================================

-- ----------------------------------------------------------------------------
-- trends: dimensión canónica. Un hashtag o sonido existe una sola vez acá,
-- independientemente de en cuántos países/categorías aparezca.
-- ----------------------------------------------------------------------------
create table trends (
  id            uuid primary key default gen_random_uuid(),
  entity_type   text not null check (entity_type in ('hashtag', 'sound')),
  -- hashtag: nombre normalizado en minúsculas sin '#'. sound: id de TikTok.
  external_id   text not null,
  display_name  text not null,
  author        text,                -- solo sonidos (artista)
  first_seen_at timestamptz not null default now(),
  last_seen_at  timestamptz not null default now(),
  metadata      jsonb not null default '{}'::jsonb,
  unique (entity_type, external_id)
);

-- ----------------------------------------------------------------------------
-- scrape_runs: una fila por (target, país) por corrida del cron. Es la fuente
-- para "último dato bueno con timestamp" y para el logging de fallas.
-- ----------------------------------------------------------------------------
create table scrape_runs (
  id             bigint generated always as identity primary key,
  started_at     timestamptz not null default now(),
  finished_at    timestamptz,
  target         text not null check (target in ('hashtags', 'sounds', 'videos')),
  country_code   text not null check (country_code in ('AR', 'MX', 'BR', 'ES', 'US')),
  status         text not null default 'running'
                 check (status in ('running', 'success', 'failed')),
  items_ingested integer not null default 0,
  error_message  text,
  -- payload crudo / contexto del error para diagnosticar cambios de contrato
  error_detail   jsonb
);

create index scrape_runs_status_idx on scrape_runs (target, country_code, finished_at desc)
  where status = 'success';

-- ----------------------------------------------------------------------------
-- trend_snapshots: el corazón del histórico. Append-only.
-- category_* viene de industry_info del Creative Center y alimenta el
-- detector de salto de nicho. Los conteos nullable: TikTok no expone todos
-- los campos para todos los tipos (p.ej. sonidos no traen views).
-- ----------------------------------------------------------------------------
create table trend_snapshots (
  id            bigint generated always as identity primary key,
  trend_id      uuid not null references trends (id),
  scrape_run_id bigint not null references scrape_runs (id),
  -- timestamp de la corrida (no de la inserción): todos los snapshots de una
  -- misma corrida comparten captured_at para que la serie temporal sea limpia.
  captured_at   timestamptz not null,
  country_code  text not null check (country_code in ('AR', 'MX', 'BR', 'ES', 'US')),
  category_id   integer,
  category_name text,
  rank          integer,
  rank_diff     integer,             -- delta de ranking que reporta TikTok
  video_count   bigint,              -- publish_cnt: cantidad de posts
  view_count    bigint,
  like_count    bigint,
  comment_count bigint,
  share_count   bigint,
  -- respuesta cruda del item, incluida la mini-serie "trend" que da TikTok.
  -- Nos protege de perder señal si mañana queremos un campo que hoy no parseamos.
  raw           jsonb not null
);

create index trend_snapshots_series_idx
  on trend_snapshots (trend_id, country_code, captured_at desc);
create index trend_snapshots_captured_idx on trend_snapshots (captured_at desc);
-- para salto de nicho: "¿en qué categorías apareció X antes de esta fecha?"
create index trend_snapshots_category_idx
  on trend_snapshots (trend_id, category_id, captured_at desc);

-- ----------------------------------------------------------------------------
-- video_snapshots: videos top por país. No son entidades trackeadas (un video
-- no "tendencia" a lo largo de semanas), son ejemplos y fuente del ratio
-- comentarios/views a nivel país-momento.
-- ----------------------------------------------------------------------------
create table video_snapshots (
  id               bigint generated always as identity primary key,
  scrape_run_id    bigint not null references scrape_runs (id),
  captured_at      timestamptz not null,
  country_code     text not null check (country_code in ('AR', 'MX', 'BR', 'ES', 'US')),
  video_id         text not null,   -- item_id de TikTok
  title            text,
  video_url        text,
  cover_url        text,
  duration_seconds integer,
  view_count       bigint,
  like_count       bigint,
  comment_count    bigint,
  share_count      bigint,
  raw              jsonb not null
);

create index video_snapshots_country_idx
  on video_snapshots (country_code, captured_at desc);

-- ----------------------------------------------------------------------------
-- trend_scores: salida del motor de detección (Fase 2). Append-only para
-- poder graficar la evolución del propio Heat Index.
-- ----------------------------------------------------------------------------
create table trend_scores (
  id                  bigint generated always as identity primary key,
  trend_id            uuid not null references trends (id),
  country_code        text not null check (country_code in ('AR', 'MX', 'BR', 'ES', 'US')),
  computed_at         timestamptz not null default now(),
  heat_index          numeric(5, 2) not null
                      check (heat_index >= 0 and heat_index <= 100),
  phase               text not null
                      check (phase in ('emergente', 'acelerando', 'pico', 'declinando')),
  -- componentes 0-100 del score compuesto
  acceleration_score  numeric(5, 2) not null default 0,
  niche_jump_score    numeric(5, 2) not null default 0,
  conversation_score  numeric(5, 2) not null default 0,
  geo_migration_score numeric(5, 2) not null default 0,
  -- valores intermedios (derivadas, bases, países origen/destino) para debug
  components          jsonb not null default '{}'::jsonb
);

create index trend_scores_latest_idx
  on trend_scores (trend_id, country_code, computed_at desc);
create index trend_scores_ranking_idx
  on trend_scores (computed_at desc, heat_index desc);

-- ----------------------------------------------------------------------------
-- insights: fichas generadas por la API de Anthropic (Fase 3). Append-only:
-- una tendencia puede re-generarse a medida que evoluciona.
-- ----------------------------------------------------------------------------
create table insights (
  id                       bigint generated always as identity primary key,
  trend_id                 uuid not null references trends (id),
  generated_at             timestamptz not null default now(),
  model                    text not null,
  heat_index_at_generation numeric(5, 2),
  what_happening           text not null,   -- qué está pasando (una línea)
  cultural_tension         text not null,
  product_categories       text[] not null default '{}',
  brand_angle              text not null,
  reputational_risk        text not null
                           check (reputational_risk in ('bajo', 'medio', 'alto')),
  risk_reason              text not null,
  estimated_window         text not null,
  raw_response             jsonb not null   -- JSON crudo devuelto por el modelo
);

create index insights_trend_idx on insights (trend_id, generated_at desc);

-- ----------------------------------------------------------------------------
-- watchlist + alerts
-- ----------------------------------------------------------------------------
create table watchlist_items (
  id              bigint generated always as identity primary key,
  trend_id        uuid not null references trends (id) unique,
  created_at      timestamptz not null default now(),
  note            text,
  alerts_enabled  boolean not null default true,
  alert_threshold numeric(5, 2) not null default 70
);

create table alerts (
  id           bigint generated always as identity primary key,
  trend_id     uuid not null references trends (id),
  triggered_at timestamptz not null default now(),
  alert_type   text not null
               check (alert_type in ('heat_threshold', 'niche_jump', 'geo_migration')),
  country_code text,
  heat_index   numeric(5, 2),
  message      text not null,
  acknowledged boolean not null default false
);

create index alerts_pending_idx on alerts (triggered_at desc) where not acknowledged;

-- ----------------------------------------------------------------------------
-- Vista: último dato bueno por target y país. La UI la usa para mostrar
-- "datos al <timestamp>" aunque la última corrida haya fallado.
-- ----------------------------------------------------------------------------
create view latest_successful_runs as
select distinct on (target, country_code) *
from scrape_runs
where status = 'success'
order by target, country_code, finished_at desc;

-- ----------------------------------------------------------------------------
-- RLS: lectura pública (los datos no son sensibles), escritura solo vía
-- service role (el scraper y el motor corren server-side con la service key,
-- que bypassea RLS). No hay policies de insert/update/delete a propósito.
-- ----------------------------------------------------------------------------
alter table trends          enable row level security;
alter table scrape_runs     enable row level security;
alter table trend_snapshots enable row level security;
alter table video_snapshots enable row level security;
alter table trend_scores    enable row level security;
alter table insights        enable row level security;
alter table watchlist_items enable row level security;
alter table alerts          enable row level security;

create policy read_trends          on trends          for select using (true);
create policy read_scrape_runs     on scrape_runs     for select using (true);
create policy read_trend_snapshots on trend_snapshots for select using (true);
create policy read_video_snapshots on video_snapshots for select using (true);
create policy read_trend_scores    on trend_scores    for select using (true);
create policy read_insights        on insights        for select using (true);
create policy read_watchlist       on watchlist_items for select using (true);
create policy read_alerts          on alerts          for select using (true);
