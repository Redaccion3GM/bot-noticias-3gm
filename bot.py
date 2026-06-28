import os
import random
import feedparser
import anthropic
import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

FUENTES = [
    {"url": "https://actualidad.rt.com/rss", "nombre": "RT en Espanol", "idioma": "es"},
    {"url": "https://mundo.sputniknews.com/export/rss2/archive/index.xml", "nombre": "Sputnik Mundo", "idioma": "es"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "nombre": "Al Jazeera Espanol", "idioma": "es"},
    {"url": "https://feeds.feedburner.com/dw-es-noticias", "nombre": "DW Espanol", "idioma": "es"},
    {"url": "https://rebelion.org/feed/", "nombre": "Rebelion", "idioma": "es"},
    {"url": "https://elordenmundial.com/feed/", "nombre": "El Orden Mundial", "idioma": "es"},
    {"url": "https://www.nodal.am/feed/", "nombre": "Nodal", "idioma": "es"},
    {"url": "https://www.jornada.com.mx/rss/mundo.xml", "nombre": "La Jornada", "idioma": "es"},
    {"url": "https://www.telesurtv.net/rss/news", "nombre": "Telesur", "idioma": "es"},
    {"url": "https://feeds.reuters.com/reuters/es/", "nombre": "Reuters Espanol", "idioma": "es"},
    {"url": "https://feeds.reuters.com/reuters/worldNews", "nombre": "Reuters", "idioma": "en"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "nombre": "Al Jazeera English", "idioma": "en"},
    {"url": "https://www.scmp.com/rss/91/feed", "nombre": "South China Morning Post", "idioma": "en"},
    {"url": "https://foreignpolicy.com/feed/", "nombre": "Foreign Policy", "idioma": "en"},
    {"url": "https://warontherocks.com/feed/", "nombre": "War on the Rocks", "idioma": "en"},
    {"url": "https://thediplomat.com/feed/", "nombre": "The Diplomat", "idioma": "en"},
    {"url": "https://www.middleeasteye.net/rss", "nombre": "Middle East Eye", "idioma": "en"},
    {"url": "https://kyivindependent.com/feed/", "nombre": "Kyiv Independent", "idioma": "en"},
    {"url": "https://meduza.io/en/rss/all", "nombre": "Meduza", "idioma": "en"},
    {"url": "https://asiatimes.com/feed/", "nombre": "Asia Times", "idioma": "en"},
    {"url": "https://www.sipri.org/rss.xml", "nombre": "SIPRI", "idioma": "en"},
    {"url": "https://thewire.in/feed", "nombre": "The Wire India", "idioma": "en"},
    {"url": "https://www.al-monitor.com/rss", "nombre": "Al-Monitor", "idioma": "en"},
    {"url": "https://www.globaltimes.cn/rss/outbrain.xml", "nombre": "Global Times", "idioma": "zh"},
    {"url": "http://www.xinhuanet.com/world/news_world.xml", "nombre": "Xinhua", "idioma": "zh"},
    {"url": "https://www.taiwannews.com.tw/rss", "nombre": "Taiwan News", "idioma": "zh"},
    {"url": "https://www.aljazeera.net/aljazeerarss/a2/a2.xml", "nombre": "Al Jazeera Arabi", "idioma": "ar"},
    {"url": "https://www.presstv.ir/rss.xml", "nombre": "Press TV", "idioma": "fa"},
    {"url": "https://tass.com/rss/v2.xml", "nombre": "TASS", "idioma": "ru"},
    {"url": "https://asia.nikkei.com/rss/feed/nar", "nombre": "Nikkei Asia", "idioma": "ja"},
]

SUBFOROS = {"conflictos": 7, "escenarios_3gm": 6, "oriente_medio": 8, "indo_pacifico": 9, "geopolitica": 10, "geoeconomia": 11, "armamento": 12, "inteligencia": 13, "historia_militar": 14, "noticias_dia": 15}
MYBB_URL = "https://foro3gm.com"
MYBB_USER = os.environ.get("MYBB_USER", "Redaccion3GM")
MYBB_PASS = os.environ.get("MYBB_PASS", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def obtener_articulos():
    fuentes_hoy = random.sample(FUENTES, min(8, len(FUENTES)))
    articulos = []
    for fuente in fuentes_hoy:
        try:
            import feedparser as fp
            feed = fp.parse(fuente["url"])
            if feed.entries:
                entrada = random.choice(feed.entries[:10])
                articulos.append({"titulo": entrada.get("title", ""), "resumen": entrada.get("summary", entrada.get("description", ""))[:2000], "link": entrada.get("link", ""), "fuente": fuente["nombre"], "idioma": fuente["idioma"]})
        except Exception as e:
            print(f"Error con {fuente['nombre']}: {e}")
    return articulos

def generar_post(articulo):
    cliente = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    necesita_traduccion = articulo["idioma"] != "es"
    instruccion = f"El articulo esta en idioma '{articulo['idioma']}'. Traducelo al espanol." if necesita_traduccion else "El articulo esta en espanol."
    prompt = f"""Eres Redaccion 3GM, equipo editorial de foro3gm.com, especializado en geopolitica, conflictos globales y estrategia militar con perspectiva multipolar.

{instruccion}

Escribe un post para el foro con este formato:
1. TITULO EN MAYUSCULAS (max 90 caracteres)
2. Linea en blanco
3. Cuerpo: 3-4 parrafos de analisis con perspectiva propia y contexto geopolitico
4. Linea en blanco
5. Pregunta de debate (empieza con "Debate:")
6. Dos lineas en blanco
7. Fuente: {articulo['fuente']}
   Traduccion y elaboracion: Redaccion 3GM

Articulo:
Titulo: {articulo['titulo']}
Contenido: {articulo['resumen']}

Escribe directamente el post sin comentarios previos."""
    msg = cliente.messages.create(model="claude-sonnet-4-6", max_tokens=1000, messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text

def determinar_subforo(titulo, cuerpo):
    texto = (titulo + " " + cuerpo).lower()
    if any(p in texto for p in ["taiwan", "china", "japon", "corea", "indo-pacifico", "pacifico"]):
        return SUBFOROS["indo_pacifico"]
    if any(p in texto for p in ["israel", "gaza", "palestina", "iran", "siria", "libano", "oriente medio"]):
        return SUBFOROS["oriente_medio"]
    if any(p in texto for p in ["tercera guerra", "3gm", "wwiii", "guerra mundial", "nuclear"]):
        return SUBFOROS["escenarios_3gm"]
    if any(p in texto for p in ["misil", "arma", "tanque", "avion", "dron", "armamento"]):
        return SUBFOROS["armamento"]
    if any(p in texto for p in ["inteligencia", "espionaje", "cia", "fsb"]):
        return SUBFOROS["inteligencia"]
    if any(p in texto for p in ["sancion", "economia", "comercio", "brics", "dolar", "petroleo"]):
        return SUBFOROS["geoeconomia"]
    if any(p in texto for p in ["ucrania", "rusia", "otan", "nato", "conflicto"]):
        return SUBFOROS["conflictos"]
    return SUBFOROS["noticias_dia"]

def publicar_en_mybb(titulo, cuerpo, fid):
    sesion = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    datos_login = urllib.parse.urlencode({"action": "do_login", "username": MYBB_USER, "password": MYBB_PASS, "submit": "Login"}).encode()
    sesion.open(f"{MYBB_URL}/member.php", datos_login)
    resp = sesion.open(f"{MYBB_URL}/newthread.php?fid={fid}")
    html = resp.read().decode("utf-8", errors="ignore")
    post_key = html.split('name="my_post_key" value="')[1].split('"')[0] if 'name="my_post_key" value="' in html else ""
    datos_post = urllib.parse.urlencode({"my_post_key": post_key, "subject": titulo[:85], "message": cuerpo, "fid": fid, "action": "do_newthread", "submit": "Post Thread"}).encode()
    resp = sesion.open(f"{MYBB_URL}/newthread.php?fid={fid}", datos_post)
    return resp.geturl()

def main():
    print(f"Bot iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    num_posts = random.randint(4, 6)
    print(f"Publicando {num_posts} noticias hoy")
    articulos = obtener_articulos()
    if not articulos:
        print("No se obtuvieron articulos")
        return
    publicados = 0
    for i, articulo in enumerate(articulos[:num_posts]):
        try:
            print(f"[{i+1}/{num_posts}] {articulo['titulo'][:60]}... ({articulo['fuente']})")
            post = generar_post(articulo)
            lineas = post.strip().split("
")
            titulo_post = lineas[0].strip()
            cuerpo_post = "
".join(lineas[1:]).strip()
            fid = determinar_subforo(titulo_post, cuerpo_post)
            url = publicar_en_mybb(titulo_post, cuerpo_post, fid)
            print(f"  Publicado en subforo {fid}: {url}")
            publicados += 1
            if i < num_posts - 1:
                pausa = random.randint(180, 480)
                print(f"  Pausa {pausa//60} min...")
                time.sleep(pausa)
        except Exception as e:
            print(f"  Error: {e}")
    print(f"Sesion completada: {publicados}/{num_posts} posts")

if __name__ == "__main__":
    main()
