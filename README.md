# Planetlambo — sitio estatico

Copia versionada y automatizada del sitio de **Planetlambo**, el Tech Market Lab de
produccion y postproduccion publicitaria con IA, martech y experiencias inmersivas
(Buenos Aires · Sao Paulo).

**Fuente de verdad: https://www.planetlambo.com**

Este repositorio no se edita a mano. El contenido se genera espejando el sitio en
produccion, para que la copia estatica y los archivos de SEO/GEO nunca queden
desactualizados respecto de lo que ve el usuario final.

## Estructura

    index.html      Home en espanol, generada desde produccion
    en/index.html   Home en ingles (hoy es un stub con redirect: no hay EN publicado)
    llms.txt        Resumen estructurado del negocio para modelos de lenguaje
    robots.txt      Reglas de crawling, incluidos los crawlers de IA
    sitemap.xml     Mapa del sitio
    optimize.py     Script de sincronizacion y optimizacion GEO

## Como regenerar el contenido

Requiere Python 3.11 o superior, sin dependencias externas:

    python optimize.py

El script descarga la home de produccion, reescribe las rutas relativas a
absolutas (para que el video y las imagenes funcionen aunque los assets pesados
no esten versionados), refresca la marca de tiempo de ultima modificacion,
enlaza llms.txt y baja tambien robots.txt y sitemap.xml.

## Automatizacion

El workflow **Sync site from production** (.github/workflows/build.yml) corre:

- cada lunes a las 06:00 UTC,
- en cada push a main que toque optimize.py o el propio workflow,
- y a demanda desde la pestana Actions (Run workflow).

Si detecta cambios, commitea los archivos regenerados automaticamente.

## Assets

Los videos e imagenes de campanas no se versionan en este repo: pesan demasiado
y ya estan servidos desde produccion. Por eso el HTML generado apunta a URLs
absolutas de www.planetlambo.com. Si en algun momento se quiere un mirror 100%
autonomo, hay que subir la carpeta de media y desactivar la absolutizacion de
rutas en optimize.py.

## Version en ingles

Hoy https://www.planetlambo.com/en/ devuelve 404, asi que en/index.html es un
stub con noindex y redirect a la home en espanol. Cuando se publique la version
EN en produccion, el script la va a espejar sola, sin cambios de codigo.

## Que NO vive aca

Proyectos que no son el sitio (TrendRadar, apps internas, experimentos) viven en
repositorios propios. Este repo es unicamente el sitio publico.
