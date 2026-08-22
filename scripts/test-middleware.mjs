/**
 * Planetlambo — tests unitarios del middleware de negociacion.
 *
 * Verifica la logica de Accept sin depender de un deploy: parseo de
 * q-values, eleccion de representacion, 406 y manejo de rutas.
 * Los tests de integracion contra un host real estan en
 * scripts/test-agent-readiness.sh
 *
 * Uso:
 *   node scripts/test-middleware.mjs
 */

import middleware from "../middleware.js";

let ok = 0;
let fallo = 0;

function verificar(descripcion, esperado, obtenido) {
  const igual = JSON.stringify(esperado) === JSON.stringify(obtenido);
  if (igual) {
    console.log(`  \x1b[32m✓\x1b[0m ${descripcion}`);
    ok++;
  } else {
    console.log(
      `  \x1b[31m✗\x1b[0m ${descripcion}\n      esperaba ${JSON.stringify(
        esperado
      )}, obtuvo ${JSON.stringify(obtenido)}`
    );
    fallo++;
  }
}

/** Simula una peticion y describe que hizo el middleware. */
async function pedir(ruta, accept, { mdDisponible = true } = {}) {
  const original = globalThis.fetch;
  globalThis.fetch = async (url) => {
    const u = String(url);
    if (!mdDisponible) return new Response("no", { status: 404 });
    return new Response(`# Espejo de ${u}\n`, {
      status: 200,
      headers: { "content-type": "text/plain" },
    });
  };

  const headers = accept === null ? {} : { accept };
  const req = new Request("https://www.planetlambo.com" + ruta, { headers });
  let res;
  try {
    res = await middleware(req);
  } finally {
    globalThis.fetch = original;
  }

  if (res === undefined || res === null) return { accion: "continua" };
  return {
    accion: "responde",
    status: res.status,
    tipo: res.headers.get("content-type"),
    vary: res.headers.get("vary"),
    cuerpo: await res.text(),
  };
}

console.log("\n\x1b[1mNegociacion de contenido\x1b[0m");

{
  const r = await pedir("/", "text/markdown");
  verificar("Accept: text/markdown devuelve markdown", "responde", r.accion);
  verificar("  con Content-Type correcto", "text/markdown; charset=utf-8", r.tipo);
  verificar("  con Vary: Accept", "Accept, Accept-Encoding", r.vary);
  verificar("  con status 200", 200, r.status);
}

{
  const r = await pedir("/", "text/html");
  verificar("Accept: text/html continua al HTML estatico", "continua", r.accion);
}

{
  const r = await pedir(
    "/",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,*/*;q=0.8"
  );
  verificar("Accept de navegador real sirve HTML", "continua", r.accion);
}

{
  const r = await pedir("/", "*/*");
  verificar("Accept: */* (curl) sirve HTML", "continua", r.accion);
}

{
  const r = await pedir("/", null);
  verificar("sin header Accept no se interpone", "continua", r.accion);
}

console.log("\n\x1b[1mQ-values\x1b[0m");

{
  const r = await pedir("/", "text/html;q=0.8, text/markdown;q=0.9");
  verificar("markdown 0.9 gana a html 0.8", "responde", r.accion);
}

{
  const r = await pedir("/", "text/html;q=0.9, text/markdown;q=0.8");
  verificar("html 0.9 gana a markdown 0.8", "continua", r.accion);
}

{
  const r = await pedir("/", "text/markdown;q=0.5, */*;q=0.4");
  verificar("markdown explicito gana al comodin de menor q", "responde", r.accion);
}

{
  const r = await pedir("/", "text/markdown;q=0, text/html");
  verificar("markdown con q=0 se rechaza y sirve html", "continua", r.accion);
}

{
  const r = await pedir("/", "text/*");
  verificar("comodin text/* no fuerza markdown", "continua", r.accion);
}

console.log("\n\x1b[1m406 Not Acceptable\x1b[0m");

{
  const r = await pedir("/", "application/pdf");
  verificar("tipo no soportado devuelve 406", 406, r.status);
  verificar("  el 406 declara Vary", "Accept, Accept-Encoding", r.vary);
}

{
  const r = await pedir("/", "image/png, application/zip");
  verificar("varios tipos no soportados devuelven 406", 406, r.status);
}

console.log("\n\x1b[1m404 para agentes\x1b[0m");

{
  const r = await pedir("/ruta-inexistente/", "text/markdown");
  verificar("ruta desconocida en markdown devuelve 404", 404, r.status);
  verificar("  con Content-Type markdown", "text/markdown; charset=utf-8", r.tipo);
  verificar("  enlaza el sitemap", true, r.cuerpo.includes("sitemap.xml"));
  verificar("  enlaza llms.txt", true, r.cuerpo.includes("llms.txt"));
  verificar("  ofrece rutas de recuperacion", true, r.cuerpo.includes("/productora-ia/"));
}

{
  const r = await pedir("/ruta-inexistente/", "text/html");
  verificar("ruta desconocida en HTML usa el 404.html del sitio", "continua", r.accion);
}

console.log("\n\x1b[1mRutas\x1b[0m");

for (const ruta of [
  "/",
  "/en/",
  "/productora-ia/",
  "/en/ai-production-company/",
  "/about/",
  "/contact/",
  "/privacy/",
]) {
  const r = await pedir(ruta, "text/markdown");
  verificar(`${ruta} tiene espejo markdown`, 200, r.status);
}

{
  const r = await pedir("/about", "text/markdown");
  verificar("sin barra final tambien resuelve (canonicaliza)", 200, r.status);
}

console.log("\n\x1b[1mDegradacion\x1b[0m");

{
  const r = await pedir("/", "text/markdown", { mdDisponible: false });
  verificar("si falta el espejo .md sirve el HTML en vez de fallar", "continua", r.accion);
}

console.log(`\n\x1b[1mResultado\x1b[0m\n  ${ok} correctas · ${fallo} fallidas\n`);
process.exit(fallo === 0 ? 0 : 1);
