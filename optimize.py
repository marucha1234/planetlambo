#!/usr/bin/env python3
"""
Planetlambo - Sync & GEO Optimizer

Descarga el sitio de produccion (https://www.planetlambo.com) y genera en este
repositorio una copia estatica lista para desplegar, junto con los archivos de
SEO/GEO (llms.txt, robots.txt, sitemap.xml).

La fuente de verdad del contenido es SIEMPRE el sitio en produccion: este repo
no edita textos a mano, se regenera con este script (o con GitHub Actions).

Uso:
    python optimize.py

Salida:
    index.html      home en espanol
    en/index.html   home en ingles (stub con redirect si todavia no existe)
    llms.txt        resumen estructurado para modelos de lenguaje
    robots.txt      reglas de crawling (incluye crawlers de IA)
    sitemap.xml     mapa del sitio
"""

import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

SITE = "https://www.planetlambo.com"
USER_AGENT = "Mozilla/5.0 (compatible; PlanetlamboSync/1.0; +https://www.planetlambo.com/)"
TIMEOUT = 30

MIRRORED_FILES = ("llms.txt", "robots.txt", "sitemap.xml")

SKIP_URL = re.compile(r"^(?:https?:|//|#|mailto:|tel:|data:|javascript:)", re.I)
DYNAMIC_URL = re.compile(r"['+{}$]")
ASSET_ATTR = re.compile(r'\b(src|href|poster|data-src|data-video)=(")([^"]*)"')


def fetch(path, required=True):
    """Descarga un recurso del sitio de produccion."""
    url = path if path.startswith("http") else SITE + path
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        if required:
            raise SystemExit("ERROR: {} devolvio HTTP {}".format(url, error.code))
        print("  aviso: {} devolvio HTTP {}; se omite".format(url, error.code))
        return None


def absolutize(html):
    """Reescribe rutas relativas a absolutas para que la copia funcione aunque
    los assets pesados (video, imagenes) vivan unicamente en produccion."""

    def replace(match):
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        value = url.strip()
        if not value or SKIP_URL.match(value) or DYNAMIC_URL.search(value):
            return match.group(0)
        if value.startswith("/"):
            absolute = SITE + value
        else:
            absolute = SITE + "/" + re.sub(r"^\./", "", value)
        return "{}={}{}{}".format(attr, quote, absolute, quote)

    return ASSET_ATTR.sub(replace, html)


def drop(html, pattern):
    return re.sub(pattern, "", html, flags=re.I)


def add_metadata(html):
    """Anade senal de frescura y el enlace a llms.txt, sin duplicar etiquetas.

    No se tocan hreflang ni canonical: los define el sitio de produccion y
    duplicarlos aca solo genera conflictos de SEO.
    """
    html = drop(html, r"[ \t]*<meta[^>]+(?:article:modified_time|last-modified)[^>]*>[ \t]*\n?")
    html = drop(html, r'[ \t]*<link[^>]+rel="alternate"[^>]+text/plain[^>]*>[ \t]*\n?')
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for tag in (
        '<meta property="article:modified_time" content="{}"/>'.format(stamp),
        '<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt"/>',
    ):
        html = html.replace("</head>", "  " + tag + "\n</head>", 1)
    return html


def write(path, content):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print("  ok  {} ({} caracteres)".format(path, len(content)))


EN_STUB = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Planetlambo - Tech Market Lab</title>
<meta name="robots" content="noindex, follow"/>
<link rel="canonical" href="https://www.planetlambo.com/"/>
<meta http-equiv="refresh" content="0; url=https://www.planetlambo.com/"/>
</head>
<body>
<p>The English version is not published yet. Redirecting to
<a href="https://www.planetlambo.com/">planetlambo.com</a>.</p>
</body>
</html>
"""


def main():
    print("Sincronizando desde " + SITE)

    write("index.html", add_metadata(absolutize(fetch("/"))))

    english = fetch("/en/", required=False)
    if english:
        write("en/index.html", add_metadata(absolutize(english)))
    else:
        print("  aviso: no hay version EN publicada; se escribe un stub con redirect")
        write("en/index.html", EN_STUB)

    for name in MIRRORED_FILES:
        data = fetch("/" + name, required=False)
        if data:
            write(name, data)

    print("Listo.")


if __name__ == "__main__":
    main()
