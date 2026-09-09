#!/usr/bin/env python3
"""
Planetlambo — generador de los espejos en Markdown.

Por cada pagina HTML escribe un .md con la misma prosa, sin nav, footer,
estilos, scripts ni envoltorios de layout. Son los que sirve el middleware
cuando un agente pide `Accept: text/markdown`.

Se generan, no se escriben a mano, por el mismo motivo que las paginas en
ingles: si se editaran aparte, quedarian desincronizadas con el sitio.

Uso:
    python3 scripts/build-md.py
"""

import os
import re
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Falta beautifulsoup4. Instalar con: pip3 install beautifulsoup4")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = "https://www.planetlambo.com"

# html de origen -> (.md de salida, url canonica)
PAGINAS = [
    ("index.html", "index.md", "/"),
    ("en/index.html", "en/index.md", "/en/"),
    ("productora-ia/index.html", "productora-ia/index.md", "/productora-ia/"),
    ("en/ai-production-company/index.html",
     "en/ai-production-company/index.md", "/en/ai-production-company/"),
    ("about/index.html", "about/index.md", "/about/"),
    ("contact/index.html", "contact/index.md", "/contact/"),
    ("privacy/index.html", "privacy/index.md", "/privacy/"),
]

# se descartan enteros: son chrome de la pagina, no prosa
DESCARTAR = ("script", "style", "noscript", "nav", "header", "footer",
             "canvas", "video", "svg", "form", "select", "button")
IDS_DESCARTAR = ("loader", "caseModal", "cinema", "siteNav")


def limpio(texto):
    return re.sub(r"[ \t]+", " ", texto).strip()


def enlaces_inline(el):
    """Convierte <a href> en [texto](url) y deja el resto como texto."""
    partes = []
    for hijo in el.descendants:
        if getattr(hijo, "name", None) == "a" and hijo.get("href"):
            continue
    # se reconstruye desde el arbol para no perder el orden
    def caminar(nodo):
        salida = ""
        for h in nodo.children:
            nombre = getattr(h, "name", None)
            if nombre is None:
                salida += str(h)
            elif nombre == "a" and h.get("href"):
                href = h["href"]
                if href.startswith("/"):
                    href = SITIO + href
                salida += "[{}]({})".format(limpio(h.get_text(" ")), href)
            elif nombre in ("strong", "b"):
                salida += "**{}**".format(limpio(caminar(h)))
            elif nombre in ("em", "i", "mark"):
                salida += limpio(caminar(h))
            elif nombre == "br":
                salida += " "
            else:
                salida += caminar(h)
        return salida
    return limpio(caminar(el))


def convertir(html, url):
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.title.string if soup.title else ""
    descripcion = ""
    meta = soup.select_one('meta[name="description"]')
    if meta:
        descripcion = meta.get("content", "")
    idioma = soup.html.get("lang", "es")

    for tag in soup(list(DESCARTAR)):
        tag.decompose()
    for ident in IDS_DESCARTAR:
        el = soup.find(id=ident)
        if el:
            el.decompose()

    raiz = soup.find("main") or soup.body
    if raiz is None:
        return None

    lineas = []
    vistos = set()

    for el in raiz.find_all(["h1", "h2", "h3", "p", "li", "details"]):
        # un <li> que envuelve otros bloques se procesa por sus hijos
        if el.name == "li" and el.find(["h1", "h2", "h3", "p"]):
            continue
        if el.name == "details":
            resumen = el.find("summary")
            cuerpo = el.find("p")
            if resumen and cuerpo:
                q = limpio(resumen.get_text(" ")).rstrip("+").strip()
                a = enlaces_inline(cuerpo)
                if q and a:
                    lineas.append("### {}\n\n{}".format(q, a))
                    vistos.add(id(cuerpo))
            continue
        if id(el) in vistos or el.find_parent("details"):
            continue

        texto = enlaces_inline(el)
        if not texto or len(texto) < 2:
            continue
        clave = texto.lower()
        if clave in vistos:
            continue
        vistos.add(clave)

        if el.name == "h1":
            lineas.append("# " + texto)
        elif el.name == "h2":
            lineas.append("## " + texto)
        elif el.name == "h3":
            lineas.append("### " + texto)
        elif el.name == "li":
            lineas.append("- " + texto)
        else:
            lineas.append(texto)

    cuerpo = "\n\n".join(lineas)
    cuerpo = re.sub(r"\n{3,}", "\n\n", cuerpo)

    cabecera = [
        "<!-- Espejo en Markdown de {}{}".format(SITIO, url),
        "     Generado por scripts/build-md.py — no editar a mano.",
        "     Se sirve por negociacion de contenido: Accept: text/markdown -->",
        "",
        "> {}".format(limpio(descripcion)) if descripcion else "",
        "",
        "Idioma: {} · Canonica: {}{}".format(idioma, SITIO, url),
        "",
        "---",
        "",
    ]
    pie = [
        "",
        "---",
        "",
        "Mapa del sitio: {}/sitemap.xml".format(SITIO),
        "Resumen para modelos: {}/llms.txt".format(SITIO),
    ]
    return "\n".join([l for l in cabecera if l is not None]) + cuerpo + "\n".join(pie) + "\n"


def main():
    print("Generando espejos en Markdown")
    hechos = 0
    for origen, destino, url in PAGINAS:
        ruta = os.path.join(RAIZ, origen)
        if not os.path.exists(ruta):
            print("  omitida (no existe): {}".format(origen))
            continue
        md = convertir(open(ruta, encoding="utf-8").read(), url)
        if md is None:
            print("  sin contenido: {}".format(origen))
            continue
        salida = os.path.join(RAIZ, destino)
        os.makedirs(os.path.dirname(salida), exist_ok=True)
        with open(salida, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        palabras = len(re.sub(r"[#>\-\[\]()]", " ", md).split())
        print("  ok  {:38s} {:5d} palabras".format(destino, palabras))
        hechos += 1
    print("  {} archivos".format(hechos))


if __name__ == "__main__":
    main()
