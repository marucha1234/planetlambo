# Planetlambo — sitio estático

Sitio oficial de **Planetlambo**, el Tech Market Lab de producción y postproducción
publicitaria con IA, martech y experiencias inmersivas (Buenos Aires · São Paulo).

**Producción: https://www.planetlambo.com**
**Hosting: Vercel · Auto-deploy desde `main`**

## Fuente de verdad

Desde 2026-08-12 **este repositorio es la fuente de verdad del sitio**. Vercel
observa la rama `main` y publica cada push en planetlambo.com automáticamente
(≈20 s por deploy). No hay build step: es HTML/CSS/JS estático.

> Antes de esa fecha el flujo era inverso: el sitio vivía fuera y este repo lo
> espejaba con `optimize.py`. Ese script quedó archivado en
> [`scripts/legacy-mirror.py`](scripts/legacy-mirror.py) sólo como referencia
> histórica. Correrlo hoy sobrescribiría los cambios locales — leer el aviso
> dentro del archivo antes de tocarlo.

## Estructura

    index.html              Home ES (con toggle EN embebido vía data-en)
    productora-ia/          Landing AEO/GEO "Productora de IA en Argentina y Brasil"
    en/index.html           Stub EN (redirect a la home mientras no haya versión propia)
    css/                    Estilos
    js/                     Scripts del sitio
    assets/                 Imágenes, videos, fonts
    favicon.ico
    llms.txt                Resumen estructurado del negocio para modelos de lenguaje
    robots.txt              Reglas de crawling (permite GPTBot, ClaudeBot, PerplexityBot, Google-Extended)
    sitemap.xml             Mapa del sitio (home + /productora-ia/)
    scripts/legacy-mirror.py   Script del modelo espejo antiguo (desactivado)
    .github/workflows/build.yml   Workflow del mirror legacy (desactivado; sólo manual con confirmación)

## Cómo editar el sitio

1. Clonar el repo y crear una rama.
2. Editar los archivos HTML/CSS/JS directamente.
3. Abrir PR o pushear a `main`.
4. Vercel deploya solo. Verificar en https://www.planetlambo.com.

Para preview local basta con abrir `index.html` en el navegador o servir la
carpeta con cualquier estático (p. ej. `python3 -m http.server 4000`).

## SEO / GEO

- `sitemap.xml` incluye `/` y `/productora-ia/`.
- `robots.txt` permite explícitamente los crawlers de IA (GPTBot, ClaudeBot,
  PerplexityBot, Google-Extended).
- `llms.txt` da un resumen estructurado del negocio pensado para LLMs.
- Cada página tiene su bloque de JSON-LD (Organization, WebSite, FAQPage,
  Service, BreadcrumbList) — validar con https://validator.schema.org antes
  de mergear cambios grandes.
- Regla editorial: sólo se puede afirmar públicamente que una campaña fue
  hecha con IA cuando ya salió en prensa. Los tres casos públicos hoy son
  Sedal "Look-IA-te" (Unilever), "Decisiones" (Magistral / DreamCo) y
  "Olé 30 años — Mundial 2026" (AGEA / Olé con agencia CHECHE). Para
  cualquier otro cliente hay que respetar el lenguaje que ya usa el sitio.

## Assets pesados

Los videos e imágenes de campañas viven en `/assets/` versionadas en el repo.
Si en el futuro pesan demasiado para un repo de Git, la alternativa limpia es
moverlas a un CDN (p. ej. Vercel Blob o un bucket) y actualizar las URLs en
el HTML — no volver al modelo espejo.

## Versión en inglés

`https://www.planetlambo.com/en/` hoy es un stub con `noindex` y redirect a la
home en español. La home en español ya trae un toggle ES/EN embebido usando
atributos `data-en`. Cuando exista una versión EN completa, publicarla en
`/en/index.html` y actualizar el sitemap.

## Qué NO vive acá

Los demás proyectos de Planetlambo (TrendRadar, ÓRBITA, apps internas,
experimentos) viven en repositorios propios. Este repo es únicamente el sitio
público planetlambo.com.
