#!/usr/bin/env python3
"""
Planetlambo — generador de las paginas de confianza.

Escribe /about/, /contact/ y /privacy/ con el mismo nav, footer y sistema
visual del resto del sitio. Son las paginas que un agente de IA consulta
para verificar que el negocio existe antes de recomendarlo.

Se generan en vez de escribirse a mano para no triplicar el nav y el
footer en tres archivos que despues se desincronizan.

Uso:
    python3 scripts/build-pages.py
"""

import os
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Falta beautifulsoup4. Instalar con: pip3 install beautifulsoup4")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = "https://www.planetlambo.com"
MOLDE = os.path.join(RAIZ, "productora-ia", "index.html")

PAGINAS = {
    "about": {
        "slug": "/about/",
        "title": "Sobre Planetlambo — Tech Market Lab en Buenos Aires y São Paulo",
        "description": (
            "Quiénes somos: Planetlambo es un Tech Market Lab y productora de IA "
            "independiente con base en Buenos Aires y São Paulo. Fundada por Marina "
            "Saroka. Cómo trabajamos, con qué marcas y qué casos son públicos."),
        "eyebrow": "Nosotros",
        "h1": "Sobre Planetlambo",
        "bloques": [
            ("p", "<strong>Planetlambo</strong> —siempre escrito junto, una sola palabra— es un "
                  "Tech Market Lab independiente y una productora de IA con base en Buenos Aires "
                  "y São Paulo. Trabajamos para marcas de Argentina, Brasil y el resto de "
                  "Latinoamérica, y también para mercados globales."),
            ("p", "Nuestro core es integrar tecnología de vanguardia —IA generativa, computer "
                  "vision, agentes multimodales— en el proceso creativo y productivo de las "
                  "marcas. Trabajamos de dos maneras: directo con la marca, o como partner "
                  "tecnológico de la agencia creativa que la marca ya tiene."),
            ("h2", "Qué nos diferencia"),
            ("p", "No partimos de un rodaje: partimos de un problema de marketing. Decidimos por "
                  "proyecto si la solución es producción 100% con IA, un flujo híbrido con "
                  "realización tradicional, una experiencia inmersiva o un agente autónomo. La "
                  "decisión la manda el brief, no un dogma sobre la herramienta."),
            ("p", "Eso se traduce en números medidos contra proyectos comparables: hasta 70% menos "
                  "de tiempo de producción, hasta 80% de eficiencia en costos y 6× más assets con "
                  "el mismo output."),
            ("h2", "Quién lo dirige"),
            ("p", "Planetlambo fue fundada por <strong>Marina Saroka</strong>, que dirige el lab. "
                  "El equipo integra tecnólogos, realizadores audiovisuales, diseñadores y "
                  "estrategas, con hubs en Buenos Aires y São Paulo. El modelo bilingüe "
                  "español/inglés y la doble sede permiten producir campañas regionales y hero "
                  "assets globales sin cambiar de equipo."),
            ("h2", "Trabajo público"),
            ("p", "Los casos donde nuestra producción con IA tiene cobertura de prensa verificable "
                  "son tres: <strong>Sedal (Unilever)</strong> con Look-IA-te, "
                  "<strong>Magistral (DreamCo)</strong> con la campaña Decisiones junto a Pluma "
                  "Agency, y <strong>Olé (AGEA)</strong> con la celebración de sus 30 años y el "
                  "Mundial 2026, realizada junto a la agencia CHECHE. Están documentados en "
                  "LatinSpots y Adlatina, con los enlaces en "
                  "<a href=\"/productora-ia/\">la página de productora de IA</a>."),
            ("p", "Trabajamos además con marcas como McDonald's, Danone, Mostaza, Lemon y Wanama "
                  "en proyectos de own media, experiencias inmersivas y agentes conversacionales."),
            ("h2", "Cómo contratarnos"),
            ("p", "Trabajamos por proyecto para campañas cerradas, con retainer mensual para "
                  "marcas con flujo continuo de contenido, y con pilots de innovación de "
                  "presupuesto acotado para validar IA en una operación existente. Firmamos NDA "
                  "antes de cualquier conversación de brief sensible. "
                  "Escribinos desde <a href=\"/contact/\">contacto</a>."),
        ],
    },
    "contact": {
        "slug": "/contact/",
        "title": "Contacto — Planetlambo | Buenos Aires · São Paulo",
        "description": (
            "Cómo contactar a Planetlambo: agenda directa, LinkedIn e Instagram. "
            "Oficinas en Buenos Aires y São Paulo. Respondemos en 24 horas hábiles."),
        "eyebrow": "Contacto",
        "h1": "Hablemos",
        "bloques": [
            ("p", "La vía más rápida es <strong>agendar una llamada de 30 minutos</strong>, sin "
                  "costo y sin compromiso. Sirve tanto para un brief concreto como para explorar "
                  "si la IA aplica a un problema que todavía no tiene forma."),
            ("p", "<a href=\"https://calendly.com/marinaplanetlambo/meeting-with-marina\" "
                  "target=\"_blank\" rel=\"noopener\"><strong>Agendar una llamada →</strong></a>"),
            ("h2", "Qué conviene traer"),
            ("p", "No hace falta un brief cerrado, pero la conversación rinde más si sabemos tres "
                  "cosas: qué problema de negocio hay detrás, qué plazo manejás y si ya existe una "
                  "agencia creativa involucrada. Con eso podemos decirte en la primera llamada si "
                  "el camino es producción con IA, un flujo híbrido o algo que ni siquiera es un "
                  "proyecto nuestro."),
            ("h2", "Otros canales"),
            ("ul", [
                "<a href=\"https://www.linkedin.com/company/planetlambo/\" target=\"_blank\" "
                "rel=\"noopener\">LinkedIn de Planetlambo</a> — novedades del lab y trabajo publicado.",
                "<a href=\"https://www.linkedin.com/in/marinasaroka/\" target=\"_blank\" "
                "rel=\"noopener\">LinkedIn de Marina Saroka</a> — contacto directo con la fundadora.",
                "<a href=\"https://www.instagram.com/planetlambo/\" target=\"_blank\" "
                "rel=\"noopener\">Instagram</a> — piezas y detrás de escena.",
            ]),
            ("h2", "Dónde estamos"),
            ("p", "Tenemos base en <strong>Buenos Aires, Argentina</strong> y en "
                  "<strong>São Paulo, Brasil</strong>. Trabajamos en español, portugués e inglés, "
                  "y operamos para toda Latinoamérica y mercados globales."),
            ("h2", "Tiempos de respuesta"),
            ("p", "Respondemos las consultas en <strong>24 horas hábiles</strong>. Para briefs "
                  "sensibles firmamos NDA antes de entrar en detalle. Si tu consulta es de prensa "
                  "o sobre un caso publicado, mencionalo en el asunto y lo derivamos directo."),
        ],
    },
    "privacy": {
        "slug": "/privacy/",
        "title": "Política de privacidad — Planetlambo",
        "description": (
            "Qué datos recoge planetlambo.com, con qué terceros se comparten "
            "(Google Analytics, Google Fonts, Calendly, Vercel) y cómo ejercer "
            "tus derechos sobre ellos."),
        "eyebrow": "Legales",
        "h1": "Política de privacidad",
        "bloques": [
            ("p", "Esta política explica qué datos recoge <strong>planetlambo.com</strong>, para "
                  "qué se usan y con quién se comparten. Está escrita para que se entienda, no "
                  "para cubrirnos. Última actualización: agosto de 2026."),
            ("h2", "Qué recogemos"),
            ("p", "El sitio no tiene formularios de registro, no pide datos personales para "
                  "navegar y no vende información a nadie. Lo que sí ocurre es medición de uso "
                  "agregada y algunas conexiones a servicios de terceros, que se detallan abajo."),
            ("h2", "Analítica"),
            ("p", "Usamos <strong>Google Analytics 4</strong> (identificador G-3SPLVJLK64) para "
                  "entender qué páginas se leen y desde dónde llega la gente. Google instala "
                  "cookies en tu navegador y procesa la dirección IP de forma abreviada. No "
                  "usamos esos datos para identificar personas ni los cruzamos con otras fuentes."),
            ("p", "Podés bloquear esta medición con el "
                  "<a href=\"https://tools.google.com/dlpage/gaoptout\" target=\"_blank\" "
                  "rel=\"noopener\">complemento de inhabilitación de Google Analytics</a>, con el "
                  "modo de no seguimiento de tu navegador o con cualquier bloqueador de scripts. "
                  "El sitio funciona igual sin analítica."),
            ("h2", "Terceros que intervienen"),
            ("ul", [
                "<strong>Vercel</strong> — hosting del sitio. Registra los datos técnicos "
                "habituales de un servidor web: IP, agente de usuario, ruta pedida y momento.",
                "<strong>Google Analytics</strong> — medición de uso agregada, con cookies.",
                "<strong>Google Fonts</strong> — las tipografías se cargan desde los servidores "
                "de Google, que reciben tu IP al pedirlas.",
                "<strong>Calendly</strong> — sólo si hacés clic para agendar una llamada. Ahí "
                "los datos que cargues se rigen por la política de privacidad de Calendly.",
            ]),
            ("h2", "Cookies"),
            ("p", "Las únicas cookies que instala el sitio son las de Google Analytics. No hay "
                  "cookies publicitarias ni de remarketing. El sitio también guarda tu "
                  "preferencia de idioma en el almacenamiento local del navegador: eso no es una "
                  "cookie, no se envía a ningún servidor y podés borrarlo limpiando los datos del "
                  "sitio."),
            ("h2", "Datos de clientes y briefs"),
            ("p", "Los briefs, materiales y datos que nos comparten los clientes en el marco de "
                  "un proyecto no se tratan en este sitio. Se rigen por el NDA y el contrato de "
                  "cada trabajo, y se aíslan por cliente: la data, los modelos y los assets de "
                  "una marca no alimentan el trabajo de otra."),
            ("h2", "Tus derechos"),
            ("p", "Podés pedirnos acceso, corrección o eliminación de cualquier dato personal que "
                  "tengamos sobre vos, y podés oponerte a la medición. La vía es "
                  "<a href=\"/contact/\">la página de contacto</a>. Respondemos en 30 días "
                  "corridos como máximo."),
            ("h2", "Cambios"),
            ("p", "Si esta política cambia, se actualiza la fecha del primer párrafo. Los cambios "
                  "de fondo se anuncian en la página de inicio."),
        ],
    },
}

ESTILO = """
.page-doc { padding: 8rem clamp(1.4rem,4vw,3rem) 4rem; max-width: 820px; margin: 0 auto; }
.page-doc .page-eyebrow { display:flex; align-items:center; gap:.8rem; font-family:var(--body);
  font-size:11px; font-weight:600; letter-spacing:2px; text-transform:uppercase;
  color:var(--secondary,#645c5d); margin-bottom:1rem; }
.page-doc .page-eyebrow::before { content:""; width:1.8rem; height:2px; background:var(--lime,#d4ff00); }
.page-doc h1 { font-family:var(--display); font-weight:800; font-size:clamp(2.2rem,5vw,3.6rem);
  line-height:1.03; letter-spacing:-.03em; margin:0 0 2rem; max-width:18ch; text-wrap:balance; }
.page-doc h2 { font-family:var(--display); font-weight:800; font-size:clamp(1.3rem,2.4vw,1.8rem);
  line-height:1.1; letter-spacing:-.02em; margin:3rem 0 1rem; }
.page-doc p { font-size:1.02rem; line-height:1.62; color:var(--secondary,#645c5d);
  max-width:66ch; margin:0 0 1.1rem; }
.page-doc p strong { color:var(--ink,#1c1b1b); font-weight:700; }
.page-doc a { color:var(--ink,#1c1b1b); text-decoration:none; border-bottom:1px solid var(--hairline,#c4c7c7); }
.page-doc a:hover { border-bottom-color:var(--ink,#1c1b1b); }
.page-doc ul { margin:0 0 1.4rem; padding-left:1.1rem; max-width:66ch; }
.page-doc li { font-size:1.02rem; line-height:1.6; color:var(--secondary,#645c5d); margin-bottom:.6rem; }
.page-doc li strong { color:var(--ink,#1c1b1b); }
"""


def bloques_html(bloques):
    salida = []
    for tipo, contenido in bloques:
        if tipo == "ul":
            items = "".join("<li>{}</li>".format(i) for i in contenido)
            salida.append("<ul>{}</ul>".format(items))
        else:
            salida.append("<{0}>{1}</{0}>".format(tipo, contenido))
    return "\n".join(salida)


def main():
    molde = BeautifulSoup(open(MOLDE, encoding="utf-8").read(), "html.parser")
    nav = molde.find("header")
    pie = molde.find("footer")
    idioma_script = molde.find("script", string=lambda s: s and "Idioma por defecto" in s)

    # el nav de la landing apunta al selector de idioma de esa pagina
    nav_limpio = BeautifulSoup(str(nav), "html.parser")
    for a in nav_limpio.select("a[hreflang]"):
        a.decompose()

    print("Generando paginas de confianza")
    for nombre, cfg in PAGINAS.items():
        carpeta = os.path.join(RAIZ, nombre)
        os.makedirs(carpeta, exist_ok=True)
        html = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#fdf8f8">
<link rel="canonical" href="{sitio}{slug}">
<link rel="alternate" hreflang="x-default" href="{sitio}{slug}">
<meta property="article:modified_time" content="2026-08-18T00:00:00Z">
<link rel="alternate" type="text/markdown" href="{slug}index.md" title="Versión en Markdown">
<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/favicon-96.png">
<link rel="apple-touch-icon" href="/assets/favicon-180.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Planetlambo">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{sitio}{slug}">
<meta property="og:image" content="{sitio}/assets/poster.jpg">
<meta property="og:image:secure_url" content="{sitio}/assets/poster.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="720">
<meta property="og:image:alt" content="Planetlambo — Showreel 2026, producción publicitaria con IA">
<meta property="og:locale" content="es_AR">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300;400;800&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/styles.css">
<style>{estilo}</style>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "{sitio}{slug}#webpage",
  "url": "{sitio}{slug}",
  "name": "{title}",
  "description": "{description}",
  "inLanguage": "es",
  "isPartOf": {{"@id": "{sitio}/#website"}},
  "about": {{"@id": "{sitio}/#org"}},
  "dateModified": "2026-08-18"
}}
</script>
</head>
<body>
{nav}
<main class="page-doc" id="top">
  <span class="page-eyebrow">{eyebrow}</span>
  <h1>{h1}</h1>
{cuerpo}
</main>
{pie}
</body>
</html>
""".format(
            title=cfg["title"], description=cfg["description"], slug=cfg["slug"],
            sitio=SITIO, estilo=ESTILO, nav=str(nav_limpio), pie=str(pie),
            eyebrow=cfg["eyebrow"], h1=cfg["h1"], cuerpo=bloques_html(cfg["bloques"]))

        destino = os.path.join(carpeta, "index.html")
        with open(destino, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)

        texto = BeautifulSoup(html, "html.parser").find("main").get_text(" ")
        print("  ok  {:16s} {:5d} caracteres de prosa".format(
            nombre + "/index.html", len(" ".join(texto.split()))))


if __name__ == "__main__":
    main()
