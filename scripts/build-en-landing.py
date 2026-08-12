#!/usr/bin/env python3
"""
Planetlambo — generador de la landing en ingles.

Genera en/ai-production-company/index.html a partir de productora-ia/index.html,
aplicando un mapa de traduccion sobre el contenido y reescribiendo head y JSON-LD.
Se mantiene toda la estructura, las clases y el CSS inline del original.

Criterio editorial:
  - Los nombres propios de campanas y clientes no se traducen.
  - Los titulos de notas de prensa quedan en su idioma original: son citas de
    articulos publicados en espanol.

Uso:
    python3 scripts/build-en-landing.py
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
ORIGEN = os.path.join(RAIZ, "productora-ia", "index.html")
DESTINO = os.path.join(RAIZ, "en", "ai-production-company", "index.html")
SITIO = "https://www.planetlambo.com"
URL_EN = SITIO + "/en/ai-production-company/"
URL_ES = SITIO + "/productora-ia/"

# --- head -----------------------------------------------------------------

TITLE = "AI Production Company in Latin America — Argentina & Brazil | Planetlambo"
DESCRIPTION = (
    "AI production company in Latin America: AI-driven advertising production, "
    "postproduction, immersive experiences, multimodal agents and workshops. "
    "Argentina and Brazil — Buenos Aires · São Paulo. With press coverage in "
    "LatinSpots and Adlatina."
)
OG_TITLE = "AI Production Company in Latin America — Planetlambo"
OG_DESCRIPTION = (
    "AI production company: AI-driven advertising production, immersive "
    "experiences, autonomous AI agents and workshops for brand teams. "
    "Buenos Aires · São Paulo."
)
TW_DESCRIPTION = (
    "AI-driven advertising production, immersive experiences and autonomous "
    "agents. Buenos Aires · São Paulo."
)

# --- contenido ------------------------------------------------------------
# clave: texto en espanol normalizado -> valor: HTML en ingles

T = {
"Servicios · Productora de IA": "Services · AI Production",

# etiquetas de seccion
"Servicios": "Services",
"Resultados y prensa": "Results and press",
"Criterios": "Criteria",
"Preguntas frecuentes": "Frequently asked questions",
"Productora de IA en Latinoamérica": "AI Production Company in Latin America",

"Una productora de IA es una productora publicitaria que usa modelos generativos y sistemas de IA para crear contenido — video, imagen, experiencias interactivas y agentes conversacionales — con tiempos y costos que la producción tradicional no puede alcanzar. No reemplaza el craft: lo acelera y lo escala.":
"<strong>An AI production company</strong> is an advertising production company that uses generative models and AI systems to create content — video, image, interactive experiences and conversational agents — at speeds and costs traditional production cannot reach. It does not replace craft: it accelerates and scales it.",

"Planetlambo es una productora de IA y Tech Market Lab con base en Buenos Aires y São Paulo. Producimos publicidad híbrida o 100% generada con inteligencia artificial, experiencias inmersivas (AR/VR y magic mirrors), agentes IA autónomos y workshops para equipos de marca. Trabajamos con marcas enterprise y startups en Argentina, Brasil y el resto de Latinoamérica.":
"<strong>Planetlambo</strong> is an AI production company and Tech Market Lab based in Buenos Aires and São Paulo. We produce hybrid or fully AI-generated advertising, immersive experiences (AR/VR and magic mirrors), autonomous AI agents and workshops for brand teams. We work with enterprise brands and startups across Argentina, Brazil and the rest of Latin America.",

"Combinamos estrategia, creatividad y modelos generativos de frontera. Decidimos por proyecto si la solución es producción 100% IA, un flujo híbrido con realización tradicional, una experiencia inmersiva o un agente autónomo — según lo que pida el brief, no según un dogma.":
"We combine strategy, creativity and frontier generative models. We decide project by project whether the answer is fully AI production, a hybrid flow with traditional filming, an immersive experience or an autonomous agent — based on what the brief asks for, not on dogma.",

"Qué producimos": "What we produce",
"Producción y Postproducción Publicitaria con IA": "AI Advertising Production &amp; Postproduction",
"Sistemas de contenido AI-native end-to-end. Del concepto a los hero assets y a los formatos always-on, híbrido o 100% producido con IA.":
"End-to-end AI-native content systems. From concept to hero assets and always-on formats, hybrid or fully AI-produced.",
"Experiencias Inmersivas": "Immersive Experiences",
"AR, VR, entornos interactivos, magic mirrors y experiencias espaciales impulsadas por computer vision.":
"AR, VR, interactive environments, magic mirrors and spatial experiences powered by computer vision.",
"Soluciones Autónomas con IA": "Autonomous AI Solutions",
"Agentes multimodales para engagement, personalización e interacción en tiempo real a escala de marca.":
"Multimodal agents for engagement, personalisation and real-time interaction at brand scale.",
"Workshops de IA Generativa": "Generative AI Workshops",
"Programas hands-on que integran IA generativa en la operación diaria de marca de los equipos.":
"Hands-on programmes that embed generative AI into a team's day-to-day brand operation.",

"Resultados": "Results",
"Tiempos de producción más rápidos": "Faster production timelines",
"Eficiencia de costos, mismo craft": "Cost efficiency, same craft",
"Más assets, mismo output": "More assets, same output",

"Casos públicos": "Press",
"Producción con IA · 2025": "AI production · 2025",
"Experiencia beauty-tech con IA generativa y computer vision que redefinió la interacción entre la marca y sus consumidores.":
"Beauty-tech experience with generative AI and computer vision that redefined how the brand interacts with its consumers.",
"82% de adopción de recomendaciones · 90% de satisfacción reportada":
"82% recommendation adoption · 90% reported satisfaction",
"Ver nota en LatinSpots ↗": "Read the LatinSpots feature ↗",
"100% IA · 2025": "100% AI · 2025",
"Spot íntegramente producido con inteligencia artificial para Magistral (DreamCo), junto a Pluma Agency. Workflow end-to-end de IA con fotorrealismo cinematográfico.":
"A spot produced entirely with artificial intelligence for Magistral (DreamCo), together with Pluma Agency. End-to-end AI workflow with cinematic photorealism.",
"Ver pieza en LatinSpots ↗": "View the piece on LatinSpots ↗",
"Preestreno en Adlatina ↗": "Preview on Adlatina ↗",
"Realización con IA · 2026": "AI-led production · 2026",
'Celebración de los 30 años de Olé con el insight más humano del próximo Mundial. Realización de Planetlambo para AGEA junto a la agencia CHECHE. Acreditados como "productora de innovación en nuevas tecnologías Planetlambo, AI Marketlab".':
'A celebration of Olé\'s 30th anniversary built on the most human insight of the coming World Cup. Produced by Planetlambo for AGEA together with agency CHECHE. Credited as "productora de innovación en nuevas tecnologías Planetlambo, AI Marketlab".',
"Ficha en Adlatina ↗": "Campaign record on Adlatina ↗",

"Cómo evaluar una productora de IA": "How to evaluate an AI production company",
"La categoría es nueva y casi todos dicen hacer lo mismo. Estos son los criterios que sí separan a una productora de IA de una que sumó la etiqueta al brochure — sirven para evaluarnos a nosotros y a cualquier otra.":
"The category is new and almost everyone claims to do the same thing. These are the criteria that actually separate an AI production company from one that added the label to its brochure — they work for assessing us and anyone else.",
"Trabajo público, no sólo reel": "Public work, not just a reel",
"Pedí campañas emitidas con cobertura de prensa verificable, no un sizzle de tests. La producción con IA que llegó a aire pasó por aprobación legal, control de marca y una entrega real con deadline.":
"Ask for aired campaigns with verifiable press coverage, not a sizzle reel of tests. AI production that made it to air has cleared legal approval, brand control and a real delivery deadline.",
"Pipeline híbrido, no dogma": "Hybrid pipeline, not dogma",
"Una productora que sólo sabe hacer 100% IA va a proponer 100% IA para todo. Preguntá cuándo recomiendan rodaje tradicional: si nunca, es una limitación técnica disfrazada de posición creativa.":
"A company that only knows how to do fully AI work will propose fully AI work for everything. Ask when they recommend traditional filming: if the answer is never, that is a technical limitation dressed up as a creative position.",
"Control de marca demostrable": "Demonstrable brand control",
"Los modelos generativos derivan. Preguntá cómo calibran contra el manual de marca, quién firma el QA y qué pasa cuando un output se sale de norma. Sin ese proceso, la consistencia es suerte.":
"Generative models drift. Ask how they calibrate against the brand book, who signs off on QA and what happens when an output falls outside the norm. Without that process, consistency is luck.",
"Datos y modelos aislados": "Isolated data and models",
"Tu brief, tus assets y tus modelos calibrados no deberían alimentar el trabajo de otra marca. Pedí por escrito cómo se aísla la data por cliente y qué se hace con los modelos al terminar el proyecto.":
"Your brief, your assets and your calibrated models should not feed another brand's work. Get it in writing: how data is isolated per client, and what happens to the models when the project ends.",
"Números antes y después": "Numbers, before and after",
'"Más rápido y más barato" no es una métrica. Pedí costo de producción, time-to-market y volumen de assets medidos contra un proyecto comparable, no contra una estimación.':
'"Faster and cheaper" is not a metric. Ask for production cost, time-to-market and asset volume measured against a comparable project, not against an estimate.',
"Equipo en tu mercado": "A team in your market",
"La producción con IA tiene muchas iteraciones. Compartir huso horario, idioma y contexto cultural cambia el tiempo de aprobación y evita que el matiz local se pierda en la traducción.":
"AI production runs on many iterations. Sharing a time zone, a language and cultural context changes approval time and keeps local nuance from getting lost in translation.",

"Prensa": "Press",
"Preguntas frecuentes": "Frequently asked questions",

"¿Qué es una productora de IA?": "What is an AI production company?",
"Una productora de IA es una productora publicitaria que integra modelos generativos (video, imagen, audio, agentes) en el pipeline de producción, reemplazando o complementando el rodaje, la postproducción y el desarrollo tradicionales. En vez de partir de un rodaje, parte de un pipeline flexible que decide en cada etapa cuánta IA usar según el brief.":
"An AI production company is an advertising production company that integrates generative models (video, image, audio, agents) into the production pipeline, replacing or complementing traditional filming, postproduction and development. Instead of starting from a shoot, it starts from a flexible pipeline that decides at each stage how much AI to use, based on the brief.",
"¿Qué diferencia a Planetlambo de una productora tradicional?": "What makes Planetlambo different from a traditional production company?",
"No partimos de un rodaje: partimos de un problema de marketing. Combinamos estrategia, creatividad e IA de frontera, y decidimos por proyecto si la solución es producción 100% IA, híbrida, una experiencia inmersiva o un agente autónomo. Somos un Tech Market Lab con capacidad de productora integrada.":
"We do not start from a shoot: we start from a marketing problem. We combine strategy, creativity and frontier AI, and decide project by project whether the answer is fully AI production, a hybrid flow, an immersive experience or an autonomous agent. We are a Tech Market Lab with an integrated production capability.",
"¿La publicidad hecha con IA se nota?": "Can you tell when advertising is made with AI?",
"Depende de la decisión creativa del brief. Producimos desde spots donde la IA es el lenguaje visual protagonista hasta piezas indistinguibles de una producción tradicional. En muchos casos, el objetivo es que la IA amplifique la producción sin ser evidente; en otros, es que sea parte del mensaje.":
"It depends on the creative decision in the brief. We produce everything from spots where AI is the leading visual language to pieces indistinguishable from traditional production. Often the goal is for AI to amplify the production without being obvious; sometimes it is for AI to be part of the message.",
"¿Cuánto tiempo lleva una producción con IA?": "How long does an AI production take?",
"Depende del proyecto, pero los tiempos son hasta 70% más rápidos que una producción tradicional comparable. Lo que antes requería semanas de rodaje y postproducción puede resolverse en días. Cada brief tiene su mapa de hitos y una entrega piloto temprana.":
"It depends on the project, but timelines run up to 70% faster than a comparable traditional production. What used to take weeks of filming and postproduction can be resolved in days. Every brief gets its own milestone map and an early pilot delivery.",
"¿Con qué marcas trabaja Planetlambo?": "Which brands does Planetlambo work with?",
"¿Desde dónde operan y para qué mercados?": "Where do you operate from, and for which markets?",
"Operamos desde Buenos Aires y São Paulo, con proyectos para toda Latinoamérica y mercados globales. El modelo bilingüe ES/EN y la doble sede nos permiten producir campañas regionales y hero assets globales sin cambios de equipo.":
"We operate from Buenos Aires and São Paulo, with projects across Latin America and global markets. The bilingual ES/EN model and dual base let us produce regional campaigns and global hero assets without changing teams.",
"¿Cuánto cuesta una producción publicitaria con IA?": "How much does AI advertising production cost?",
"¿Cómo elegir una productora de IA en Latinoamérica?": "How do you choose an AI production company in Latin America?",
"cómo evaluar una productora de IA": "how to evaluate an AI production company",
"¿La IA respeta los manuales de marca?": "Does AI respect brand guidelines?",
"Sí. Calibramos los modelos generativos con los guidelines visuales, tonales y de producto de cada marca antes de generar pieza alguna. Esto incluye paleta, tipografía, lenguaje, codes de packaging y do's & don'ts. Cada output pasa por QA de marca antes de la entrega.":
"Yes. We calibrate the generative models against each brand's visual, tonal and product guidelines before generating anything. That includes palette, typography, language, packaging codes and do's &amp; don'ts. Every output goes through brand QA before delivery.",

# nav
"Showreel": "Showreel",
"Capacidades": "Capabilities",
"Trabajos": "Work",
"Nuestro Lab": "Our Lab",
"Contacto": "Contact",

# footer
"Redefiniendo la intersección entre inteligencia y creatividad.":
"Redefining the intersection of intelligence and creativity.",
"Planetlambo · Productora de IA · Buenos Aires — São Paulo":
"Planetlambo · AI production company · Buenos Aires — São Paulo",
"© 2026 Planetlambo · TechMarketLab. Todos los derechos reservados.":
"© 2026 Planetlambo · TechMarketLab. All rights reserved.",
"Ubicaciones": "Locations",
"Más": "More",
"Inicio": "Home",
"Productora de IA": "AI Production Company",
"¿Firman NDA y cómo manejan la data del cliente?": "Do you sign NDAs, and how do you handle client data?",
"Firmamos NDA antes de cualquier conversación de brief sensible y operamos con flujos donde la data, los modelos y los assets de cada cliente se aíslan. Tenemos experiencia con marcas reguladas (alimentos, financial, retail) y con procesos legales corporativos.":
"We sign an NDA before any sensitive brief conversation and work with flows where each client's data, models and assets are isolated. We have experience with regulated categories (food, financial, retail) and with corporate legal processes.",

"¿Tenés un brief? Hablemos.": "Got a brief? Let's talk.",
"Agendá una llamada": "Book a call",
"← Volver al inicio": "← Back to home",
}

# respuestas largas que contienen HTML anidado
T_HTML = {
"marcas-faq": (
"Trabajamos con marcas enterprise y startups en Argentina, Brasil y el resto de Latinoamérica.",
"We work with enterprise brands and startups across Argentina, Brazil and the rest of Latin America."
),
"costo-faq": (
"No hay tarifa fija: cada proyecto se cotiza según alcance",
"There is no fixed rate: every project is quoted on scope, technical complexity and timing. We work with three models. <strong>Per project</strong>, for closed campaigns with defined deliverables. <strong>Monthly retainer</strong>, for brands with a continuous content flow. And <strong>innovation pilots</strong>, contained budgets to validate AI inside an existing operation before committing to a full campaign. Savings against a comparable traditional production reach up to 80% on cost and 70% on time, but it depends on the mix: a fully AI-generated piece and a hybrid one with filming have different cost structures."
),
"elegir-faq": (
"Seis criterios sirven para evaluar a cualquiera",
'Six criteria work for assessing anyone, us included. One, public work with verifiable press coverage, not a reel of tests. Two, the ability to recommend traditional filming when it fits: if they always recommend fully AI, that is a technical limitation dressed up as a creative position. Three, an explicit process for calibrating against the brand book, with signed QA. Four, written isolation of data, models and assets between clients. Five, metrics measured against a comparable project, not estimates. Six, a team in your time zone and language, because AI production is iterative and approvals multiply. It is laid out in <a href="#how-to-choose">how to evaluate an AI production company</a>.'
),
}

RELATIVAS = {"../assets/": "/assets/", "../css/": "/css/", "../js/": "/js/"}


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def traducir(soup):
    hechos, faltantes = 0, []
    for el in soup.find_all(["h1", "h2", "h3", "p", "span", "summary", "a"]):
        if el.find(["h1", "h2", "h3", "p", "span", "summary"]):
            continue
        txt = norm(el.get_text(" "))
        if not txt or len(txt) < 2:
            continue
        # los summary traen el "+" del icono
        limpio = norm(txt.rstrip("+"))
        if limpio in T:
            nuevo = T[limpio]
            # preservar el <i>+</i> de los summary
            icono = el.find("i")
            el.clear()
            el.append(BeautifulSoup(nuevo, "html.parser"))
            if icono:
                el.append(icono)
            hechos += 1
        elif re.match(r"^[\d%×·\s]+$", limpio):
            continue  # numeros y metricas
        else:
            faltantes.append((el.name, limpio[:80]))
    return hechos, faltantes


def traducir_html(soup):
    n = 0
    for _, (prefijo, ingles) in T_HTML.items():
        for p in soup.find_all("p"):
            if norm(p.get_text(" ")).startswith(prefijo[:50]):
                p.clear()
                p.append(BeautifulSoup(ingles, "html.parser"))
                n += 1
                break
    return n


def reescribir_head(soup):
    soup.html["lang"] = "en"
    soup.title.string = TITLE
    for sel, attr, val in [
        ('meta[name="description"]', "content", DESCRIPTION),
        ('meta[property="og:title"]', "content", OG_TITLE),
        ('meta[property="og:description"]', "content", OG_DESCRIPTION),
        ('meta[property="og:url"]', "content", URL_EN),
        ('meta[property="og:locale"]', "content", "en_US"),
        ('meta[name="twitter:title"]', "content", OG_TITLE),
        ('meta[name="twitter:description"]', "content", TW_DESCRIPTION),
        ('link[rel="canonical"]', "href", URL_EN),
    ]:
        el = soup.select_one(sel)
        if el:
            el[attr] = val
    # el origen ya trae su propio juego de hreflang; hay que sacarlo antes de
    # escribir el de esta pagina o quedan duplicados en conflicto
    for link in soup.select('link[rel="alternate"][hreflang]'):
        link.decompose()
    canonical = soup.select_one('link[rel="canonical"]')
    for code, href in (("en", URL_EN), ("es-419", URL_ES), ("x-default", URL_ES)):
        tag = soup.new_tag("link", rel="alternate", href=href)
        tag["hreflang"] = code
        canonical.insert_after(tag)


def reescribir_jsonld(soup):
    bloque = soup.select_one('script[type="application/ld+json"]')
    datos = json.loads(bloque.string)
    faq = []
    for det in soup.select("details.faq-item"):
        s, p = det.find("summary"), det.find("p")
        if s and p:
            faq.append({
                "@type": "Question",
                "name": norm(s.get_text(" ")).rstrip("+").strip(),
                "acceptedAnswer": {"@type": "Answer", "text": norm(p.get_text(" "))},
            })
    for n in datos.get("@graph", []):
        t = n.get("@type")
        if t == "BreadcrumbList":
            n["@id"] = URL_EN + "#breadcrumb"
            n["itemListElement"] = [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITIO + "/en/"},
                {"@type": "ListItem", "position": 2, "name": "AI Production Company", "item": URL_EN},
            ]
        elif t == "WebPage":
            n["@id"] = URL_EN + "#webpage"
            n["url"] = URL_EN
            n["name"] = "AI Production Company in Latin America — Planetlambo"
            n["description"] = (
                "What an AI production company is, what Planetlambo produces, measured "
                "results, public cases and frequently asked questions. Operating from "
                "Buenos Aires and São Paulo for Argentina, Brazil and Latin America."
            )
            n["inLanguage"] = "en"
            n["mainEntity"] = {"@id": URL_EN + "#service"}
            n["breadcrumb"] = {"@id": URL_EN + "#breadcrumb"}
        elif t == "Service":
            n["@id"] = URL_EN + "#service"
            n["serviceType"] = "AI advertising production"
            n["name"] = "AI advertising production"
            n["alternateName"] = ["AI production company", "productora de IA", "generative AI advertising production"]
            n["description"] = (
                "AI advertising production and postproduction: hybrid or fully "
                "AI-generated campaigns, immersive experiences (AR/VR, magic mirrors), "
                "autonomous AI agents and workshops for brand teams. Operating from "
                "Buenos Aires and São Paulo for enterprise brands and startups."
            )
            cat = n.get("hasOfferCatalog", {})
            cat["name"] = "AI production services"
            nombres = {
                "Producción y Postproducción Publicitaria con IA": ("AI Advertising Production & Postproduction", "End-to-end AI-native content systems: hybrid or fully AI-produced advertising, from concept to hero assets and always-on formats."),
                "Experiencias Inmersivas": ("Immersive Experiences", "AR, VR, interactive environments, magic mirrors and spatial experiences powered by computer vision."),
                "Soluciones Autónomas con IA": ("Autonomous AI Solutions", "Multimodal agents for engagement, personalisation and real-time interaction at brand scale."),
                "Workshops de IA Generativa": ("Generative AI Workshops", "Hands-on programmes that embed generative AI into a team's day-to-day brand operation."),
            }
            for oferta in cat.get("itemListElement", []):
                s = oferta.get("itemOffered", {})
                if s.get("name") in nombres:
                    s["name"], s["description"] = nombres[s["name"]]
        elif t == "FAQPage":
            n["@id"] = URL_EN + "#faq"
            if faq:
                n["mainEntity"] = faq
    bloque.string = json.dumps(datos, ensure_ascii=False, indent=2)
    return len(faq)


def main():
    print("Generando la landing en ingles desde productora-ia/index.html")
    soup = BeautifulSoup(open(ORIGEN, encoding="utf-8").read(), "html.parser")

    n = traducir_html(soup)
    print("  {} respuestas largas con HTML anidado".format(n))
    hechos, faltantes = traducir(soup)
    print("  {} nodos de texto traducidos".format(hechos))
    if faltantes:
        print("  SIN TRADUCIR ({}):".format(len(faltantes)))
        for tag, txt in faltantes:
            print("     <{}> {}".format(tag, txt))

    reescribir_head(soup)
    q = reescribir_jsonld(soup)
    print("  {} preguntas en el FAQPage".format(q))

    # anclas internas y rutas
    salida = str(soup)
    salida = salida.replace('id="como-elegir"', 'id="how-to-choose"')
    salida = salida.replace('href="#como-elegir"', 'href="#how-to-choose"')
    salida = salida.replace('id="que-producimos"', 'id="what-we-produce"')
    salida = salida.replace('id="faq-productora"', 'id="faq"')
    # el selector de idioma se invierte: en la pagina EN apunta al espanol
    salida = salida.replace(
        '<a href="/en/ai-production-company/" hreflang="en" lang="en">EN</a>',
        '<a href="/productora-ia/" hreflang="es-419" lang="es">ES</a>')
    # el nav apunta a las anclas de la home en ingles
    for ancla in ("showreel", "capabilities", "work", "studio"):
        salida = salida.replace('href="/#{}"'.format(ancla),
                                'href="/en/#{}"'.format(ancla))
    salida = salida.replace('href="/"', 'href="/en/"')
    for a, b in RELATIVAS.items():
        salida = salida.replace('"{}'.format(a), '"{}'.format(b))

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        f.write(salida)
    print("  escrito {} ({} caracteres)".format(
        os.path.relpath(DESTINO, RAIZ), len(salida)))


if __name__ == "__main__":
    main()
