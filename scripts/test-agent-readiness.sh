#!/usr/bin/env bash
#
# Planetlambo — verificacion de preparacion para agentes.
#
# Cubre los cinco puntos de la auditoria "Is Agentic":
#   1. 404 real, con cuerpo en Markdown para agentes
#   2. Negociacion de contenido segun acceptmarkdown.com
#   3. Instruccion "cuando usarnos" en llms.txt
#   4. Paginas de confianza (about, contact, privacy) con 500+ caracteres
#   5. Organization schema con contactPoint y address
#
# Uso:
#   ./scripts/test-agent-readiness.sh                      # produccion
#   ./scripts/test-agent-readiness.sh https://otro.host    # un preview
#
# Sale con codigo 1 si algo falla, para poder encadenarlo en CI.

set -uo pipefail

BASE="${1:-https://www.planetlambo.com}"

# Los previews de Vercel estan detras de Deployment Protection. Con el
# secreto de bypass en PL_BYPASS los tests pueden correr contra un preview
# antes de tocar produccion. Sin la variable, curl se comporta igual que
# siempre y esto no afecta al uso normal contra el sitio publico.
CURL=(curl -s)
if [ -n "${PL_BYPASS:-}" ]; then
  CURL=("${CURL[@]}" -H "x-vercel-protection-bypass: ${PL_BYPASS}")
fi
OK=0
FALLO=0

verde()  { printf "  \033[32m✓\033[0m %s\n" "$1"; OK=$((OK+1)); }
rojo()   { printf "  \033[31m✗\033[0m %s\n" "$1"; FALLO=$((FALLO+1)); }
titulo() { printf "\n\033[1m%s\033[0m\n" "$1"; }

# comparar: descripcion, esperado, obtenido
comparar() {
  if [ "$2" = "$3" ]; then verde "$1"; else rojo "$1 — esperaba '$2', obtuvo '$3'"; fi
}
contiene() {
  if printf '%s' "$3" | grep -qi -- "$2"; then verde "$1"; else rojo "$1 — no encontro '$2'"; fi
}

echo "Verificando $BASE"

# ---------------------------------------------------------------- 1. 404 ----
titulo "1 · 404 para agentes"

COD=$("${CURL[@]}" -o /dev/null -w "%{http_code}" -L "$BASE/ruta-que-no-existe-jamas")
comparar "ruta inexistente devuelve 404" "404" "$COD"

COD_ASSET=$("${CURL[@]}" -o /dev/null -w "%{http_code}" "$BASE/assets/no-existe-esto.jpg")
comparar "asset inexistente devuelve 404" "404" "$COD_ASSET"

MD404=$("${CURL[@]}" -L -H "Accept: text/markdown" "$BASE/ruta-que-no-existe-jamas")
CT404=$("${CURL[@]}" -o /dev/null -L -w "%{content_type}" -H "Accept: text/markdown" "$BASE/ruta-que-no-existe-jamas")
contiene "404 en Markdown declara text/markdown" "text/markdown" "$CT404"
contiene "404 en Markdown enlaza el sitemap" "sitemap.xml" "$MD404"
contiene "404 en Markdown enlaza llms.txt" "llms.txt" "$MD404"
contiene "404 en Markdown ofrece rutas de recuperacion" "/productora-ia/" "$MD404"

COD_MD404=$("${CURL[@]}" -o /dev/null -L -w "%{http_code}" -H "Accept: text/markdown" "$BASE/ruta-que-no-existe-jamas")
comparar "404 en Markdown mantiene el status 404" "404" "$COD_MD404"

# la pagina 404 de navegador conserva su diseño
HTML404=$("${CURL[@]}" -L "$BASE/ruta-que-no-existe-jamas")
contiene "404 HTML conserva la marca" "Planetlambo" "$HTML404"

# ------------------------------------------------- 2. acceptmarkdown.com ----
titulo "2 · Negociacion de contenido (acceptmarkdown.com)"

for RUTA in "/" "/en/" "/productora-ia/" "/en/ai-production-company/" "/about/" "/contact/" "/privacy/"; do
  CT=$("${CURL[@]}" -o /dev/null -w "%{content_type}" -H "Accept: text/markdown" "$BASE$RUTA")
  contiene "$RUTA sirve markdown con Accept: text/markdown" "text/markdown" "$CT"
done

VARY=$("${CURL[@]}" -I -H "Accept: text/markdown" "$BASE/" | grep -i '^vary:' | tr -d '\r')
contiene "Vary incluye Accept en la respuesta markdown" "accept" "$VARY"

VARY_HTML=$("${CURL[@]}" -I "$BASE/" | grep -i '^vary:' | tr -d '\r')
contiene "Vary incluye Accept en la respuesta HTML" "accept" "$VARY_HTML"

CT_HTML=$("${CURL[@]}" -o /dev/null -w "%{content_type}" -H "Accept: text/html" "$BASE/")
contiene "Accept: text/html sigue sirviendo HTML" "text/html" "$CT_HTML"

CT_NAV=$("${CURL[@]}" -o /dev/null -w "%{content_type}" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" "$BASE/")
contiene "Accept de navegador real sirve HTML" "text/html" "$CT_NAV"

CT_CURL=$("${CURL[@]}" -o /dev/null -w "%{content_type}" -H "Accept: */*" "$BASE/")
contiene "Accept: */* sirve HTML por defecto" "text/html" "$CT_CURL"

# q-values en ambas direcciones
CT_Q1=$("${CURL[@]}" -o /dev/null -w "%{content_type}" \
  -H "Accept: text/html;q=0.8, text/markdown;q=0.9" "$BASE/")
contiene "q-values: markdown 0.9 > html 0.8 sirve markdown" "text/markdown" "$CT_Q1"

CT_Q2=$("${CURL[@]}" -o /dev/null -w "%{content_type}" \
  -H "Accept: text/html;q=0.9, text/markdown;q=0.8" "$BASE/")
contiene "q-values: html 0.9 > markdown 0.8 sirve html" "text/html" "$CT_Q2"

COD406=$("${CURL[@]}" -o /dev/null -w "%{http_code}" -H "Accept: application/pdf" "$BASE/")
comparar "tipo no soportado devuelve 406" "406" "$COD406"

# el markdown es prosa, no HTML disfrazado
MD=$("${CURL[@]}" -H "Accept: text/markdown" "$BASE/productora-ia/")
if printf '%s' "$MD" | grep -q "<script"; then
  rojo "el markdown no debe contener <script>"
else
  verde "el markdown viene sin scripts ni layout"
fi
contiene "el markdown conserva el encabezado principal" "# Productora de IA" "$MD"

# --------------------------------------------------- 3. instruccion agente ---
titulo "3 · Instruccion para agentes"

LLMS=$("${CURL[@]}" "$BASE/llms.txt")
contiene "llms.txt trae la seccion cuando usarnos (ES)" "Cuándo recurrir a Planetlambo" "$LLMS"
contiene "llms.txt trae la seccion cuando usarnos (EN)" "When to use Planetlambo" "$LLMS"
contiene "llms.txt dice cuando NO somos la respuesta" "No somos la respuesta correcta" "$LLMS"
contiene "llms.txt explica como derivar" "Cómo derivar" "$LLMS"
contiene "llms.txt documenta la negociacion markdown" "Accept: text/markdown" "$LLMS"

# ------------------------------------------------ 4. paginas de confianza ----
titulo "4 · Paginas de confianza"

for P in about contact privacy; do
  COD=$("${CURL[@]}" -o /dev/null -w "%{http_code}" "$BASE/$P/")
  comparar "/$P/ responde 200" "200" "$COD"
  LARGO=$("${CURL[@]}" "$BASE/$P/" \
    | python3 -c "import sys,re;h=sys.stdin.read();b=re.sub(r'<(script|style)[^>]*>.*?</\1>','',h,flags=re.S|re.I);t=re.sub(r'<[^>]+>',' ',b);print(len(' '.join(t.split())))")
  if [ "$LARGO" -ge 500 ]; then
    verde "/$P/ tiene $LARGO caracteres de contenido (minimo 500)"
  else
    rojo "/$P/ solo tiene $LARGO caracteres (minimo 500)"
  fi
done

SITEMAP=$("${CURL[@]}" "$BASE/sitemap.xml")
for P in about contact privacy; do
  contiene "/$P/ figura en el sitemap" "/$P/" "$SITEMAP"
done

# --------------------------------------------- 5. Organization schema --------
titulo "5 · Organization schema"

"${CURL[@]}" "$BASE/" | python3 -c "
import sys,re,json,html
src=sys.stdin.read()
bloques=re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',src,re.S|re.I)
org=None
for b in bloques:
    d=json.loads(html.unescape(b))
    for n in d.get('@graph',[d]):
        if n.get('@type')=='Organization': org=n
if org is None:
    print('FALTA_ORG'); raise SystemExit
faltan=[c for c in ('contactPoint','address','name','url') if c not in org]
print('OK' if not faltan else 'FALTAN:'+','.join(faltan))
cps=org.get('contactPoint',[])
cps=cps if isinstance(cps,list) else [cps]
print('TIPOS:'+','.join(c.get('contactType','?') for c in cps))
print('VIAS:'+','.join('url' if c.get('url') else ('email' if c.get('email') else ('tel' if c.get('telephone') else 'ninguna')) for c in cps))
" > /tmp/_org.txt 2>/dev/null

ORG=$(cat /tmp/_org.txt 2>/dev/null | head -1)
comparar "Organization tiene contactPoint, address, name y url" "OK" "$ORG"
TIPOS=$(grep '^TIPOS:' /tmp/_org.txt 2>/dev/null | sed 's/TIPOS://')
contiene "contactPoint declara un contactType" "sales" "$TIPOS"
rm -f /tmp/_org.txt

# ------------------------------------------------------ regresiones ----------
titulo "Regresiones · lo que ya funcionaba"

for RUTA in "/" "/en/" "/productora-ia/" "/en/ai-production-company/" "/llms.txt" "/sitemap.xml" "/robots.txt"; do
  COD=$("${CURL[@]}" -o /dev/null -w "%{http_code}" "$BASE$RUTA")
  comparar "$RUTA responde 200" "200" "$COD"
done

HL=$("${CURL[@]}" "$BASE/" | grep -o '<link[^>]*hreflang[^>]*>' | grep -c . || true)
comparar "la home mantiene 3 hreflang" "3" "$HL"

for V in reel-lite.mp4 case-mostaza.mp4 poster.jpg; do
  COD=$("${CURL[@]}" -o /dev/null -w "%{http_code}" "$BASE/assets/$V")
  comparar "assets/$V responde 200" "200" "$COD"
done

REL=$("${CURL[@]}" "$BASE/en/" | grep -cE '(data-video|data-desk|data-mob|src)="(assets|css|js)/' || true)
comparar "la pagina EN no tiene rutas relativas" "0" "$REL"

# ------------------------------------------------------------- resumen -------
printf "\n\033[1mResultado\033[0m\n"
printf "  %d correctas · %d fallidas\n" "$OK" "$FALLO"
[ "$FALLO" -eq 0 ] || exit 1
