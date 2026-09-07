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
async function pedir(
  ruta,
  accept,
  { mdDisponible = true, cuerpoFalso = null, rutaExiste = false } = {}
) {
  const original = globalThis.fetch;
  const vistas = [];
  globalThis.fetch = async (url, opciones) => {
    const u = String(url);
    const metodo = (opciones && opciones.method) || "GET";
    vistas.push({ url: u, metodo, headers: (opciones && opciones.headers) || {} });
    // sonda de existencia sobre una ruta sin espejo
    if (metodo === "HEAD") {
      return new Response(null, { status: rutaExiste ? 200 : 404 });
    }
    if (!mdDisponible) return new Response("no", { status: 404 });
    if (cuerpoFalso !== null) {
      return new Response(cuerpoFalso, { status: 200 });
    }
    return new Response(`# Espejo de ${u}\n`, {
      status: 200,
      headers: { "content-type": "text/plain" },
    });
  };
  globalThis.__vistas = vistas;

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

console.log("\n\x1b[1mRutas sin espejo que si existen\x1b[0m");

{
  // Regresion real: /whatsnextia/ es una app proxeada que no vive en este
  // repo. Con la lista fija, un agente que pedia markdown recibia un 404
  // diciendo que una seccion real de la marca no existia.
  const r = await pedir("/whatsnextia/", "text/markdown", { rutaExiste: true });
  verificar("ruta proxeada existente no devuelve 404", "continua", r.accion);
}

{
  const r = await pedir("/seccion-futura/", "text/markdown", { rutaExiste: true });
  verificar("cualquier pagina nueva tampoco se declara inexistente", "continua", r.accion);
}

{
  const r = await pedir("/no-existe-de-verdad/", "text/markdown", { rutaExiste: false });
  verificar("una ruta realmente inexistente si devuelve 404", 404, r.status);
}

{
  const r = await pedir("/whatsnextia/", "text/html", { rutaExiste: true });
  verificar("en HTML no se sondea ni se interviene", "continua", r.accion);
}

console.log("\n\x1b[1mDegradacion\x1b[0m");

{
  const r = await pedir("/", "text/markdown", { mdDisponible: false });
  verificar("si falta el espejo .md sirve el HTML en vez de fallar", "continua", r.accion);
}

{
  // Detectado testeando contra un preview protegido: el fetch interno
  // recibia la pagina de login de Vercel con status 200 y el middleware la
  // servia rotulada como text/markdown.
  const r = await pedir("/", "text/markdown", {
    cuerpoFalso: "<!DOCTYPE html><html><head><title>Login</title></head></html>",
  });
  verificar("si el origen devuelve HTML no lo sirve como markdown", "continua", r.accion);
}

{
  const r = await pedir("/", "text/markdown", {
    cuerpoFalso: "<html lang=\"en\">pagina intermedia</html>",
  });
  verificar("tambien detecta HTML sin doctype", "continua", r.accion);
}

{
  const r = await pedir("/", "text/markdown", {
    cuerpoFalso: "# Un titulo\n\nProsa legitima con <em>algo</em> de html inline.\n",
  });
  verificar("markdown con html inline si se sirve", "responde", r.accion);
}

console.log("\n\x1b[1mAnti-recursion\x1b[0m");

{
  const req = new Request("https://www.planetlambo.com/", {
    headers: { accept: "text/markdown", "x-pl-interno": "1" },
  });
  const res = await middleware(req);
  verificar("una peticion interna no reentra al middleware", undefined, res);
}

console.log("\n\x1b[1mCredenciales en el fetch interno\x1b[0m");

{
  const original = globalThis.fetch;
  let capturado = null;
  globalThis.fetch = async (url, opciones) => {
    capturado = (opciones && opciones.headers) || {};
    return new Response("# ok\n", { status: 200 });
  };
  const req = new Request("https://www.planetlambo.com/", {
    headers: {
      accept: "text/markdown",
      cookie: "sesion=abc",
      "x-vercel-protection-bypass": "secreto",
    },
  });
  await middleware(req);
  globalThis.fetch = original;
  verificar("reenvia la cookie al espejo", "sesion=abc", capturado.cookie);
  verificar(
    "reenvia el bypass de proteccion",
    "secreto",
    capturado["x-vercel-protection-bypass"]
  );
}

console.log(`\n\x1b[1mResultado\x1b[0m\n  ${ok} correctas · ${fallo} fallidas\n`);
process.exit(fallo === 0 ? 0 : 1);
