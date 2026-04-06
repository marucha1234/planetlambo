#!/usr/bin/env python3
"""
Planetlambo GEO Optimizer
Fetches HTML from planetlambo.com and applies all GEO optimizations.
Run: python optimize.py
Output: index.html (ES), en/index.html (EN)
"""
import urllib.request
import re
import json
import os

def fetch_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8')

def add_before_close_head(html, tag):
    return html.replace('</head>', tag + '\n</head>')

def add_after_open_body(html, tag):
    return html.replace('<body', tag + '\n<body', 1) if '<body' in html else html

def optimize_html(html, lang='es'):
    # 1. Add hreflang links
    if lang == 'es':
        hreflangs = '<link rel="alternate" hreflang="en" href="https://planetlambo.com/en/"/>\n<link rel="alternate" hreflang="x-default" href="https://planetlambo.com/"/>'
    else:
        hreflangs = '<link rel="alternate" hreflang="es" href="https://planetlambo.com/"/>\n<link rel="alternate" hreflang="x-default" href="https://planetlambo.com/"/>'
    html = add_before_close_head(html, hreflangs)

    # 2. Add llms.txt link
    html = add_before_close_head(html, '<link rel="alternate" type="text/plain" href="/llms.txt" title="LLMs.txt"/>')

    # 3. Add freshness meta
    html = add_before_close_head(html, '<meta property="article:modified_time" content="2025-06-01T00:00:00Z"/>')
    html = add_before_close_head(html, '<meta http-equiv="last-modified" content="2025-06-01T00:00:00Z"/>')

    # 4. Wrap nav in header
    html = re.sub(r'(<nav\b)', r'<header>\1', html, count=1)
    html = re.sub(r'(</nav>)', r'\1</header>', html, count=1)

    # 5. Fix heading hierarchy - add H2 to sections
    section_labels = {
        'es': {'about':'Sobre Nosotros','capabilities':'Capacidades','campaigns':'Campanas','team':'Equipo','faq':'Preguntas Frecuentes','cta':'Contacto'},
        'en': {'about':'About Us','capabilities':'Capabilities','campaigns':'Campaigns','team':'Team','faq':'FAQ','cta':'Contact'}
    }
    labels = section_labels[lang]
    for sid, label in labels.items():
        # Add aria-label to section
        aria = {'es':{'about':'Seccion sobre nosotros','capabilities':'Seccion de capacidades','campaigns':'Seccion de campanas','team':'Seccion del equipo','faq':'Seccion de preguntas frecuentes','cta':'Seccion de contacto'},
                'en':{'about':'About us section','capabilities':'Capabilities section','campaigns':'Campaigns section','team':'Team section','faq':'FAQ section','cta':'Contact section'}}
        pattern = f'id="{sid}"'
        replacement = f'id="{sid}" aria-label="{aria[lang][sid]}"'
        html = html.replace(pattern, replacement, 1)
        
        # Convert section-title spans to H2
        section_pattern = f'(id="{sid}"[^>]*>\\s*(?:<[^>]+>\\s*)*)<(span|div|p)(\\s+class="section-title")'
        html = re.sub(section_pattern, lambda m: m.group(1) + '<h2' + m.group(3), html, count=1)
        # Close tag
        close_pattern = f'(class="section-title"[^>]*>[^<]*)</(span|div|p)>'
        html = re.sub(close_pattern, lambda m: m.group(1) + '</h2>', html, count=1)

    # 6. Convert campaign cards to article elements
    html = re.sub(r'<div(\\s+class="campaign-card")', r'<article\1 itemscope itemtype="https://schema.org/CreativeWork"', html)
    html = html.replace('</div><!-- /campaign-card -->', '</article>')
    
    # 7. Add Person schema (Marina)
    person = {"@context":"https://schema.org","@type":"Person","name":"Marina Buiraz","jobTitle":"Founder & Creative Director","worksFor":{"@type":"Organization","name":"Planetlambo"}}
    html = add_before_close_head(html, f'<script type="application/ld+json">{json.dumps(person)}</script>')

    # 8. Add BreadcrumbList schema
    bc_name = "Inicio" if lang == "es" else "Home"
    bc_url = "https://planetlambo.com/" if lang == "es" else "https://planetlambo.com/en/"
    breadcrumb = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":bc_name,"item":bc_url}]}
    html = add_before_close_head(html, f'<script type="application/ld+json">{json.dumps(breadcrumb)}</script>')

    # 9. Fix EN-specific issues
    if lang == 'en':
        html = html.replace('Cuatro pilares que impulsan', 'Four pillars that drive our creative engine')
        html = html.replace('Founder de ', 'Founder of ')
        html = html.replace('Navegacion principal', 'Main navigation')
        html = html.replace('Experiencias Inmersivas', 'Immersive Experiences')
        html = html.replace('Agentes AI Autonomos', 'Autonomous AI Agents')

    # 10. Add extra FAQ questions
    faq_extra = {
        'es': [
            ('Que tipo de marcas trabajan con Planetlambo?', 'Trabajamos con marcas de todos los tamanos.'),
            ('Cuanto tiempo tarda un proyecto tipico?', 'Los tiempos varian segun la complejidad. De 2 a 12 semanas.'),
            ('Como garantizan la calidad del contenido generado por IA?', 'Todo pasa por revision humana rigurosa.')
        ],
        'en': [
            ('What types of brands does Planetlambo work with?', 'We work with brands of all sizes across multiple sectors.'),
            ('How long does a typical project take?', 'Timelines vary. An AI campaign can be ready in 2 to 4 weeks.'),
            ('How do you ensure AI content quality?', 'All AI content goes through rigorous human review.')
        ]
    }

    return html

if __name__ == '__main__':
    print('Fetching ES version...')
    es_html = fetch_html('https://planetlambo.com/')
    es_optimized = optimize_html(es_html, 'es')
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(es_optimized)
    print(f'ES saved: {len(es_optimized)} chars')

    print('Fetching EN version...')
    en_html = fetch_html('https://planetlambo.com/en/')
    en_optimized = optimize_html(en_html, 'en')
    os.makedirs('en', exist_ok=True)
    with open('en/index.html', 'w', encoding='utf-8') as f:
        f.write(en_optimized)
    print(f'EN saved: {len(en_optimized)} chars')
    print('Done!')
