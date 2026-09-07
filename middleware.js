/**
 * Planetlambo — negociacion de contenido para agentes.
 *
 * Implementa acceptmarkdown.com sobre un sitio estatico:
 *
 *   1. `Accept: text/markdown` devuelve el espejo .md de la pagina, con
 *      `Content-Type: text/markdown; charset=utf-8`.
 *   2. Toda respuesta negociada lleva `Vary: Accept`, para que la CDN no le
 *      sirva a un agente la variante HTML cacheada por otro visitante.
 *   3. Un `Accept` que no admite ninguna de las dos representaciones recibe
 *      406, no una respuesta que el cliente no pidio.
 *   4. Se respetan los q-values: `text/html;q=0.9, text/markdown;q=0.8`
 *      devuelve HTML, y al reves devuelve Markdown.
 *
 * Ademas responde 404 con cuerpo en Markdown a las rutas inexistentes,
 * para que un agente pueda recuperarse solo en vez de quedar en una pared.
 *
 * Notas de implementacion:
 *
 * - Sin dependencias: solo Web APIs. Devolver `undefined` continua la
 *   cadena, asi que el HTML se sigue sirviendo estatico desde la CDN y el
 *   middleware no se interpone en el camino normal.
 * - El matcher excluye assets y cualquier ruta con extension, de modo que
 *   el fetch interno al .md no vuelve a entrar aca.
 */

/** Paginas con espejo en Markdown. Clave: ruta canonica con barra final. */
const ESPEJOS = {
  "/": "/index.md",
  "/en/": "/en/index.md",
  "/productora-ia/": "/productora-ia/index.md",
  "/en/ai-production-company/": "/en/ai-production-company/index.md",
  "/about/": "/about/index.md",
  "/contact/": "/contact/index.md",
  "/privacy/": "/privacy/index.md",
};

/** Rutas sin extension que existen y no son paginas con espejo. */
const OTRAS_RUTAS = new Set(["/_vercel"]);

const SITIO = "https://www.planetlambo.com";

/** Cuerpo del 404 para agentes. Markdown, con salidas concretas. */
const CUERPO_404 = `# 404 — Esta página no existe

La ruta pedida no existe en planetlambo.com. Puede que el enlace esté
desactualizado o que la dirección tenga un error.

## Dónde buscar

- [Inicio](${SITIO}/) — qué es Planetlambo y el trabajo publicado
- [Productora de IA](${SITIO}/productora-ia/) — servicios, resultados y preguntas frecuentes
- [Sobre nosotros](${SITIO}/about/) — el negocio, el equipo y los casos públicos
- [Contacto](${SITIO}/contact/) — cómo iniciar una conversación
- [Privacidad](${SITIO}/privacy/) — qué datos recoge el sitio

## Índices legibles por máquina

- Mapa del sitio: ${SITIO}/sitemap.xml
- Resumen estructurado para modelos: ${SITIO}/llms.txt
- Reglas de rastreo: ${SITIO}/robots.txt

## In English

The requested path does not exist. Start at ${SITIO}/en/ or see
${SITIO}/en/ai-production-company/ for the services page.
`;

/**
 * Parsea un header Accept en pares { tipo, q }, respetando q-values.
 * Un q ausente vale 1, segun RFC 9110.
 */
function parsearAccept(header) {
  return header
    .split(",")
    .map((parte) => {
      const trozos = parte.trim().split(";");
      const tipo = (trozos.shift() || "").trim().toLowerCase();
      let q = 1;
      for (const p of trozos) {
        const m = p.trim().match(/^q=([0-9]*\.?[0-9]+)$/i);
        if (m) {
          const v = parseFloat(m[1]);
          if (!Number.isNaN(v)) q = v;
        }
      }
      return { tipo, q };
    })
    .filter((x) => x.tipo);
}

/**
 * Calidad con la que el cliente acepta un tipo concreto, considerando
 * los comodines `tipo/*` y `*​/*`. Devuelve -1 si no lo acepta.
 */
function calidadDe(lista, buscado) {
  const [rama] = buscado.split("/");
  let mejor = -1;
  for (const it of lista) {
    if (it.tipo === buscado || it.tipo === rama + "/*" || it.tipo === "*/*") {
      if (it.q > mejor) mejor = it.q;
    }
  }
  return mejor;
}

/** Normaliza a ruta con barra final, que es la forma canonica del sitio. */
function conBarra(ruta) {
  if (ruta.length > 1 && !ruta.endsWith("/")) return ruta + "/";
  return ruta;
}

/**
 * Cabeceras para las peticiones que el middleware hace al propio origen.
 * Reenvia las credenciales de la peticion original —sin ellas, en un
 * deployment de preview protegido el fetch interno recibe la pagina de
 * login— y marca la peticion para no reentrar al middleware.
 */
function cabecerasInternas(request, extra) {
  const h = Object.assign({ "x-pl-interno": "1" }, extra || {});
  const cookie = request.headers.get("cookie");
  if (cookie) h.cookie = cookie;
  const bypass = request.headers.get("x-vercel-protection-bypass");
  if (bypass) h["x-vercel-protection-bypass"] = bypass;
  return h;
}

function respuesta406(vary) {
  return new Response(
    "406 Not Acceptable\n\n" +
      "Este recurso se sirve como text/html o como text/markdown.\n" +
      "Volvé a pedirlo con Accept: text/markdown o Accept: text/html.\n",
    {
      status: 406,
      headers: {
        "content-type": "text/plain; charset=utf-8",
        vary: vary,
        "x-content-type-options": "nosniff",
      },
    }
  );
}

export default async function middleware(request) {
  // Las peticiones que origina este mismo middleware no vuelven a entrar:
  // sin esta guarda, la sonda de existencia se llamaria a si misma.
  if (request.headers.get("x-pl-interno")) return;

  const url = new URL(request.url);
  const ruta = conBarra(url.pathname);
  const accept = request.headers.get("accept") || "";
  const VARY = "Accept, Accept-Encoding";

  // Sin Accept no hay nada que negociar: comportamiento normal.
  if (!accept) return;

  const lista = parsearAccept(accept);
  const qMarkdown = calidadDe(lista, "text/markdown");
  const qHtml = calidadDe(lista, "text/html");
  const esPagina = Object.prototype.hasOwnProperty.call(ESPEJOS, ruta);

  // El cliente no admite ninguna representacion que sepamos producir.
  if (qMarkdown <= 0 && qHtml <= 0) {
    return respuesta406(VARY);
  }

  const quiereMarkdown = qMarkdown > qHtml;

  // ---- Ruta fuera de la lista de espejos ----------------------------------
  if (!esPagina && !OTRAS_RUTAS.has(url.pathname)) {
    // `/about` sin barra todavia no es 404: le toca el redirect a `/about/`.
    if (Object.prototype.hasOwnProperty.call(ESPEJOS, ruta)) return;

    // Para navegadores no nos metemos: si la ruta existe la sirve el origen,
    // y si no, aparece el 404.html con la marca.
    if (!quiereMarkdown) return;

    // No estar en ESPEJOS no significa no existir. El dominio sirve tambien
    // aplicaciones proxeadas que no viven en este repo —hoy /whatsnextia/— y
    // manana cualquier pagina nueva. Antes de declarar 404 hay que
    // preguntarle al origen, o le estariamos diciendo a un agente que una
    // seccion real de la marca no existe.
    let existe = false;
    try {
      const sonda = await fetch(new URL(url.pathname, url.origin), {
        method: "HEAD",
        headers: cabecerasInternas(request, { accept: "text/html,*/*" }),
        redirect: "manual",
      });
      // 2xx es que existe; 3xx tambien, porque hay algo a donde ir.
      existe = sonda.status < 400;
    } catch (e) {
      // Si la sonda falla, es preferible no afirmar que la ruta no existe.
      existe = true;
    }

    if (existe) {
      // Existe pero no tiene espejo .md: se entrega el HTML, que es honesto,
      // en vez de un 404 falso o de HTML rotulado como markdown.
      return;
    }

    return new Response(CUERPO_404, {
      status: 404,
      headers: {
        "content-type": "text/markdown; charset=utf-8",
        vary: VARY,
        "cache-control": "public, max-age=0, must-revalidate",
        "x-content-type-options": "nosniff",
      },
    });
  }

  // ---- Pagina conocida ----------------------------------------------------
  if (!quiereMarkdown) {
    // HTML: no nos interponemos. El Vary lo pone vercel.json en estatico,
    // asi que la pagina se sigue sirviendo desde la CDN sin pasar por aca.
    return;
  }

  const destino = new URL(ESPEJOS[ruta], url.origin);

  // Se reenvian las credenciales de la peticion original. En los deployments
  // de preview, protegidos por Vercel, sin esto el fetch interno recibe la
  // pagina de login en vez del archivo.
  const md = await fetch(destino, {
    headers: cabecerasInternas(request, { accept: "text/plain, */*" }),
    redirect: "follow",
  });

  if (!md.ok) {
    // Si el espejo falta, es preferible el HTML a un error.
    return;
  }

  // No alcanza con que responda 200: hay que confirmar que lo que volvio es
  // el espejo y no una pagina intermedia — un login, un error, una
  // interstitial de la CDN. Servir HTML rotulado como text/markdown le
  // entrega basura al agente, que es peor que devolverle el HTML honesto.
  const texto = await md.text();
  const arranque = texto.slice(0, 400).trimStart().toLowerCase();
  if (arranque.startsWith("<!doctype") || arranque.startsWith("<html")) {
    return;
  }

  return new Response(texto, {
    status: 200,
    headers: {
      "content-type": "text/markdown; charset=utf-8",
      vary: VARY,
      "cache-control": "public, max-age=0, must-revalidate",
      "x-content-type-options": "nosniff",
      link: '<' + SITIO + ruta + '>; rel="canonical"',
    },
  });
}

export const config = {
  // Solo rutas sin extension: quedan afuera los assets, el CSS, el JS y los
  // propios .md, para que el fetch interno no vuelva a entrar al middleware.
  matcher: ["/((?!assets/|css/|js/|_vercel/|.*\\.).*)"],
};
