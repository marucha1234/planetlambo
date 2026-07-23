# TrendRadar

Detector de tendencias tempranas de TikTok para planners y equipos de marca.
El valor no está en el top 10 de hashtags: está en detectar señales **antes**
de que exploten y traducirlas en insight accionable para marcas.

**Bloomberg para cultura**: dark mode, denso en datos, cero dashboard genérico.

## Estado del proyecto

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Schema de base + scraper del Creative Center + cron | ✅ esta versión |
| 2 | Motor de detección (Heat Index) + tests + alertas | pendiente |
| 3 | Capa de insight con la API de Anthropic | pendiente |
| 4 | UI: Radar / Detalle / Watchlist | pendiente |

## Stack

- Next.js 14 (App Router) + TypeScript
- Tailwind (+ shadcn/ui en la fase de UI)
- Supabase (Postgres) — el histórico es el producto: todo es append-only
- Vercel (deploy + cron cada 6 horas)

## Setup

### 1. Supabase

1. Crear un proyecto en [supabase.com](https://supabase.com).
2. Aplicar las migraciones versionadas de `supabase/migrations/`:

```bash
npm i -g supabase
supabase link --project-ref <ref-del-proyecto>
supabase db push
```

(Alternativa rápida: pegar el SQL de la migración en el SQL Editor del dashboard.)

### 2. Variables de entorno

```bash
cp .env.example .env.local
```

Completar `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y
`CRON_SECRET` (cualquier string aleatorio largo). Ninguna credencial vive en
el código.

### 3. Correr local

```bash
npm install
npm run dev
```

La home muestra el estado de ingesta. Para disparar una ingesta a mano:

```bash
curl -H "Authorization: Bearer $CRON_SECRET" http://localhost:3000/api/cron/ingest
```

### 4. Deploy en Vercel

1. Importar el repo en Vercel con **Root Directory = `trendradar/`**.
2. Cargar las mismas variables de entorno del `.env.example`.
3. El cron queda definido en `vercel.json` (`0 */6 * * *`, cada 6 horas).
   Vercel manda automáticamente `Authorization: Bearer $CRON_SECRET` si la
   env está definida en el proyecto.
   > Nota: el endpoint declara `maxDuration = 300`; en plan Hobby verificá
   > que Fluid Compute esté activo o bajá la cantidad de páginas por target
   > en `src/lib/constants.ts`.

## Cómo funciona la ingesta (Fase 1)

Cada 6 horas, `/api/cron/ingest` recorre **5 países** (AR, MX, BR, ES, US) ×
**3 targets** (hashtags, sonidos, videos top) contra la API JSON interna del
[Creative Center](https://ads.tiktok.com/business/creativecenter)
(`creative_radar_api/v1/popular_trend/...`) — la misma que alimenta la web,
sin scraping de DOM ni headless browser.

Garantías de robustez:

- **Append-only**: cada corrida inserta snapshots nuevos con `captured_at`
  compartido. Nunca se sobreescribe nada; las series temporales salen del
  histórico completo.
- **Retries**: backoff exponencial con jitter (2s/4s/8s) ante errores de red,
  429 y 5xx. Pausa de 1.5s entre targets como rate limit propio.
- **Falla ruidosa**: los schemas Zod exigen los campos que persistimos. Si
  TikTok renombra un campo, cambia el envelope o responde `code != 0`, la
  corrida se marca `failed` en `scrape_runs` con el mensaje y un snippet del
  payload — jamás se degrada en silencio.
- **Degradación en lectura**: la UI consulta la vista
  `latest_successful_runs` y muestra siempre el último dato bueno con su
  timestamp, aunque la última corrida haya fallado.
- Las corridas parciales valen: si falla `sounds/BR`, el resto de los
  targets sigue y queda registrado qué falló y por qué.

### Si TikTok exige firma

Los listados públicos suelen responder con un `anonymous-user-id` cualquiera.
Si el endpoint empieza a devolver `code != 0`, copiá los headers `user-sign`,
`timestamp` y `web-id` desde DevTools (request a `creative_radar_api`) y
cargalos como env (`TIKTOK_CC_*`). El cliente los agrega automáticamente.
Los paths de los endpoints están centralizados en
`src/lib/scraper/creative-center.ts` (`ENDPOINTS`) por si los mueven.

## Modelo de datos

Ver `supabase/migrations/20260723120000_initial_schema.sql` (comentado tabla
por tabla). Resumen:

- `trends` — dimensión canónica (hashtag/sonido), única por tipo+id.
- `trend_snapshots` — serie temporal append-only por (trend, país, corrida),
  con categoría del Creative Center para detectar saltos de nicho.
- `video_snapshots` — videos top por país (ejemplos + ratio comentarios/views).
- `scrape_runs` — observabilidad: cada target×país por corrida, con errores.
- `trend_scores` — Heat Index y componentes (Fase 2).
- `insights` — fichas generadas por Claude (Fase 3).
- `watchlist_items` / `alerts` — seguimiento y notificaciones.
