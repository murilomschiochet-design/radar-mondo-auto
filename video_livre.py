"""Vídeo REAL e LIVRE para o reel do @radar_mondo (YouTube com licença Creative Commons BY ou canal oficial de governo).

  python video_livre.py buscar "termo em inglês" ["outro termo" ...]
      -> lista só vídeos marcados Creative Commons, com canal, duração, data e se o canal é OFICIAL ou SUSPEITO (reenvio).
  python video_livre.py baixar <video_id> <iid> [inicio fim]
      -> confere a licença de novo, baixa até 720p, corta [inicio, fim] (máx. 20 s, sem som) em videos/<iid>.mp4
         e gera videos/<iid>-folha.jpg (1 quadro a cada 2 s) para você OLHAR antes de usar.

Regras (ver ROTINA.md): só quem FILMOU (o próprio veículo/pessoa) ou canal OFICIAL (exército, governo, agência espacial, defesa civil).
Canal que só reenvia vídeo dos outros (Kanal13, "Daily News Explained", compilações, react) NÃO serve, mesmo marcado CC.
Nada gráfico (corpos, feridos, momento de morte). Sem acesso ao YouTube aqui -> o script avisa e o reel segue com foto.
"""
import json
import os
import subprocess
import sys
import urllib.parse

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
for _ca in ("/root/.ccr/ca-bundle.crt", os.environ.get("SSL_CERT_FILE", "")):
    if _ca and os.path.exists(_ca):
        os.environ.setdefault("SSL_CERT_FILE", _ca)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", _ca)
        break
try:
    import yt_dlp
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"], check=False)
    import yt_dlp

BASE = os.path.dirname(os.path.abspath(__file__))
OFICIAIS = ("the u.s. army", "u.s. army", "u.s. navy", "u.s. air force", "u.s. marine corps", "u.s. department of defense",
            "department of war", "dvids", "u.s. central command", "nasa", "esa", "nato", "the white house", "un video", "united nations",
            "protezione civile", "vigili del fuoco", "polizia di stato", "carabinieri", "guardia costiera", "esercito italiano",
            "ministry of defence of ukraine", "ministry of defense of ukraine", "general staff of the armed forces of ukraine",
            "israel defense forces", "idf", "european commission", "european parliament", "noaa", "usgs", "fema", "jaxa", "spacex")
SUSPEITOS = ("kanal13", "daily news explained", "the matrix is glitching", "opinion_reports", "new informative", "masked woman",
             "useful advice", "global trending", "youth pilot", "world war", "react", "compilation", "breaking news 24", "news hub")


def tipo_canal(canal):
    c = (canal or "").lower()
    if any(s in c for s in SUSPEITOS):
        return "SUSPEITO (reenvio — não usar)"
    if any(o == c or o in c for o in OFICIAIS):
        return "OFICIAL"
    return "verificar: é quem filmou?"


def buscar(termos):
    for q in termos:
        print(f"\n### {q}")
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q) + "&sp=EgIwAQ%253D%253D"   # filtro Creative Commons
        try:
            with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True, "no_warnings": True, "playlistend": 15}) as y:
                ents = (y.extract_info(url, download=False).get("entries") or [])[:15]
        except Exception as e:
            print("SEM ACESSO AO YOUTUBE AQUI:", str(e)[:160], "-> siga com foto.")
            return
        for e in ents:
            print(f"{e.get('id')} | {e.get('channel')} | {e.get('duration')} s | {tipo_canal(e.get('channel'))} | {e.get('title')}")


def baixar(vid, iid, ini=None, fim=None):
    url = f"https://www.youtube.com/watch?v={vid}"
    os.makedirs(os.path.join(BASE, "videos"), exist_ok=True)
    tmp = os.path.join(BASE, "videos", f"_{iid}.%(ext)s")
    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "outtmpl": tmp, "merge_output_format": "mp4",
            "format": "bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]"}
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(url, download=False)
            lic = info.get("license") or ""
            if "creative commons" not in lic.lower() and tipo_canal(info.get("channel")) != "OFICIAL":
                sys.exit(f"RECUSADO: licença '{lic or 'padrão do YouTube'}' e canal não oficial ({info.get('channel')}).")
            if tipo_canal(info.get("channel")).startswith("SUSPEITO"):
                sys.exit(f"RECUSADO: canal de reenvio ({info.get('channel')}).")
            info = y.extract_info(url, download=True)
            bruto = y.prepare_filename(info)
    except SystemExit:
        raise
    except Exception as e:
        sys.exit(f"SEM ACESSO AO YOUTUBE AQUI: {str(e)[:160]} -> siga com foto.")
    if not os.path.exists(bruto):
        bruto = os.path.splitext(bruto)[0] + ".mp4"
    ini = float(ini or 0)
    fim = float(fim) if fim else min(float(info.get("duration") or 20), ini + 20)
    fim = min(fim, ini + 20)
    saida = os.path.join(BASE, "videos", f"{iid}.mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(ini), "-to", str(fim), "-i", bruto, "-an",
                    "-vf", "scale='min(1080,iw)':-2", "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", saida], check=True)
    os.remove(bruto)
    folha = os.path.join(BASE, "videos", f"{iid}-folha.jpg")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", saida, "-vf", "fps=1/2,scale=240:-2,tile=5x2", "-frames:v", "1", folha])
    print(json.dumps({"arquivo": f"videos/{iid}.mp4", "duracao": round(fim - ini, 1), "canal": info.get("channel"),
                      "licenca": info.get("license") or "oficial", "fonte_url": url, "titulo": info.get("title"),
                      "folha": f"videos/{iid}-folha.jpg (OLHE e depois NÃO faça commit dela)",
                      "tamanho_mb": round(os.path.getsize(saida) / 1e6, 1)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "buscar":
        buscar(sys.argv[2:])
    elif len(sys.argv) >= 4 and sys.argv[1] == "baixar":
        baixar(*sys.argv[2:6])
    else:
        print(__doc__)
