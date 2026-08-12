#!/usr/bin/env python3
"""
Planetlambo — generador de la home en ingles.

Genera en/index.html a partir de index.html, usando la traduccion que ya vive
en los atributos data-en del sitio en espanol. La idea es que el ingles no
pueda volver a quedar desactualizado: se edita el sitio en espanol y se
regenera.

Que hace:
  1. Reemplaza el innerHTML de cada elemento [data-en] por su traduccion, y
     guarda el original en data-es para que el toggle de idioma siga andando
     en las dos direcciones (el JS hace dataset.es = innerHTML si no existe,
     asi que sin este paso la pagina EN se quedaria trabada en ingles).
  2. Cambia lang="es" a lang="en".
  3. Reescribe el head: title, description, keywords, Open Graph, Twitter,
     canonical y hreflang.
  4. Convierte las rutas relativas en absolutas. Desde /en/ un href como
     "assets/x.jpg" apuntaria a /en/assets/x.jpg, que no existe.
  5. Manda los links internos a su equivalente en ingles.
  6. Reconstruye el JSON-LD en ingles, tomando la FAQ del DOM ya traducido.

Uso:
    python3 scripts/build-en.py

Requiere beautifulsoup4.
"""

import json
import os
import re
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Falta beautifulsoup4. Instalar con: pip3 install beautifulsoup4")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, "index.html")
DESTINO = os.path.join(RAIZ, "en", "index.html")

SITIO = "https://www.planetlambo.com"

# --- textos del head en ingles -------------------------------------------

TITLE = "Planetlambo — Tech Market Lab · AI Production Company for Brands | Buenos Aires · São Paulo"

DESCRIPTION = (
    "Planetlambo is a Tech Market Lab and AI production company: AI-driven "
    "advertising production and postproduction, martech, immersive experiences "
    "and multimodal agents — combining strategy, creativity and frontier "
    "generative models for enterprise brands and startups across Argentina, "
    "Brazil and the rest of Latin America."
)

KEYWORDS = (
    "AI production company, AI advertising production, generative AI "
    "advertising, AI postproduction, Tech Market Lab, AI production company "
    "Latin America, AI production company Argentina, martech, immersive "
    "experiences, multimodal agents, Buenos Aires, São Paulo"
)

OG_TITLE = "Planetlambo — Tech Market Lab · AI Production Company for Brands"
OG_DESCRIPTION = (
    "AI production company and Tech Market Lab: AI-driven advertising "
    "production and postproduction, immersive experiences, multimodal agents "
    "and martech for leading brands across Argentina, Brazil and Latin America."
)
TW_TITLE = "Planetlambo — AI Production Company · Tech Market Lab"
TW_DESCRIPTION = (
    "AI production company and Tech Market Lab. AI-driven advertising "
    "production, immersive experiences and multimodal agents. "
    "Buenos Aires · São Paulo."
)
OG_IMAGE_ALT = "Planetlambo — Showreel 2026, AI advertising production"

ORG_DESCRIPTION = (
    "Planetlambo is an independent Tech Market Lab: an AI production company "
    "that designs, produces and scales advertising campaigns, immersive "
    "experiences, multimodal agents and martech solutions for leading brands. "
    "AI advertising production and postproduction — hybrid or fully generative "
    "— with up to 80% more efficiency than traditional methods."
)

WEBPAGE_NAME = "Planetlambo — Tech Market Lab · AI Production Company for Brands"
WEBPAGE_DESCRIPTION = (
    "Tech Market Lab and AI production company: AI advertising production and "
    "postproduction, martech, immersive experiences and multimodal agents for "
    "brands across Argentina, Brazil and the rest of Latin America."
)

# links internos: ES -> EN
LINKS = {
    "/productora-ia/": "/en/ai-production-company/",
}

# rutas relativas que hay que absolutizar
RELATIVAS = ("assets/", "css/", "js/")


def swap_idiomas(soup):
    """Hornea la traduccion y preserva el original en data-es."""
    n = 0
    for el in soup.select("[data-en]"):
        original = el.decode_contents()
        traduccion = el["data-en"]
        if not el.has_attr("data-es"):
            el["data-es"] = original
        el.clear()
        el.append(BeautifulSoup(traduccion, "html.parser"))
        n += 1
    return n


def absolutizar(html):
    """assets/x.jpg -> /assets/x.jpg (desde /en/ la relativa se rompe)."""
    def reemplazo(m):
        attr, comilla, url = m.group(1), m.group(2), m.group(3)
        if url.startswith(RELATIVAS):
            return '{}={}/{}{}'.format(attr, comilla, url, comilla)
        return m.group(0)

    return re.sub(r'\b(src|href|poster|data-src)=(")([^"]*)"', reemplazo, html)


def reescribir_links(soup):
    for a in soup.find_all("a", href=True):
        if a["href"] in LINKS:
            a["href"] = LINKS[a["href"]]


def set_meta(soup, selector, attr, valor):
    el = soup.select_one(selector)
    if el:
        el[attr] = valor


def reescribir_head(soup):
    soup.html["lang"] = "en"

    if soup.title:
        soup.title.string = TITLE

    set_meta(soup, 'meta[name="description"]', "content", DESCRIPTION)
    set_meta(soup, 'meta[name="keywords"]', "content", KEYWORDS)
    set_meta(soup, 'meta[property="og:title"]', "content", OG_TITLE)
    set_meta(soup, 'meta[property="og:description"]', "content", OG_DESCRIPTION)
    set_meta(soup, 'meta[property="og:url"]', "content", SITIO + "/en/")
    set_meta(soup, 'meta[property="og:locale"]', "content", "en_US")
    set_meta(soup, 'meta[property="og:locale:alternate"]', "content", "es_AR")
    set_meta(soup, 'meta[property="og:image:alt"]', "content", OG_IMAGE_ALT)
    set_meta(soup, 'meta[name="twitter:title"]', "content", TW_TITLE)
    set_meta(soup, 'meta[name="twitter:description"]', "content", TW_DESCRIPTION)
    set_meta(soup, 'link[rel="canonical"]', "href", SITIO + "/en/")

    # hreflang: los mismos tres, iguales de los dos lados
    for link in soup.select('link[rel="alternate"][hreflang]'):
        link.decompose()
    canonical = soup.select_one('link[rel="canonical"]')
    for code, href in (
        ("en", SITIO + "/en/"),
        ("es-419", SITIO + "/"),
        ("x-default", SITIO + "/"),
    ):
        tag = soup.new_tag("link", rel="alternate", href=href)
        tag["hreflang"] = code
        canonical.insert_after(tag)


def faq_desde_dom(soup):
    """Arma la FAQ en ingles leyendo el DOM ya traducido."""
    preguntas = []
    for det in soup.select("details.faq-item"):
        s, p = det.find("summary"), det.find("p")
        if not (s and p):
            continue
        q = re.sub(r"\s+", " ", s.get_text(" ")).replace("+", "").strip()
        a = re.sub(r"\s+", " ", p.get_text(" ")).strip()
        if q and a:
            preguntas.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            })
    return preguntas


def reescribir_jsonld(soup):
    bloque = soup.select_one('script[type="application/ld+json"]')
    if not bloque:
        return 0
    datos = json.loads(bloque.string)
    grafo = datos.get("@graph", [])
    faq = faq_desde_dom(soup)

    for nodo in grafo:
        tipo = nodo.get("@type")
        if tipo == "Organization":
            nodo["description"] = ORG_DESCRIPTION
        elif tipo == "WebSite":
            nodo["@id"] = SITIO + "/#website"
        elif tipo == "WebPage":
            nodo["@id"] = SITIO + "/en/#webpage"
            nodo["url"] = SITIO + "/en/"
            nodo["name"] = WEBPAGE_NAME
            nodo["description"] = WEBPAGE_DESCRIPTION
            nodo["inLanguage"] = "en"
        elif tipo == "FAQPage":
            nodo["@id"] = SITIO + "/en/#faq"
            if faq:
                nodo["mainEntity"] = faq

    bloque.string = json.dumps(datos, ensure_ascii=False, indent=2)
    return len(faq)


def main():
    print("Generando la home en ingles desde index.html")
    html = open(ORIGEN, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")

    n = swap_idiomas(soup)
    print("  {} elementos traducidos".format(n))

    reescribir_head(soup)
    reescribir_links(soup)
    q = reescribir_jsonld(soup)
    print("  {} preguntas en el FAQPage".format(q))

    salida = absolutizar(str(soup))

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        f.write(salida)
    print("  escrito {} ({} caracteres)".format(
        os.path.relpath(DESTINO, RAIZ), len(salida)))


if __name__ == "__main__":
    main()
