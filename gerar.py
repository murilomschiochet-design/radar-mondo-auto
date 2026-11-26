"""Gera as artes de uma notícia do @radar_mondo a partir de itens/<id>.json.

  python gerar.py <id>   -> saida/<id>/: story.jpg (sempre), post.jpg + cta.jpg ("post"), reel.mp4 + capa.jpg ("reel" com foto, ou "reel_texto": estilo story, sem foto)
Fotos: só livres (Wikimedia Commons / governo), baixadas da URL do item, com crédito na arte.
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

import navegador

BASE = os.path.dirname(os.path.abspath(__file__))
ARTE = os.path.join(BASE, "modelo", "arte.html")
MUSICAS = sorted(os.path.join(BASE, "musica", f) for f in os.listdir(os.path.join(BASE, "musica")) if f.endswith(".mp3"))
MARCA, HANDLE = "Radar Mondo", "@radar_mondo"
UA = {"User-Agent": "RadarMondoBot/1.0 (free-image download)"}
CTA = ["🌍 Hai appena trovato la pagina che ti aggiorna su quello che succede nel mondo, ora per ora.",
       "Seguici e attiva le notifiche: l'algoritmo potrebbe non mostrarti più i nostri post."]
if os.name == "nt":
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass


def tela(dados, destino_png, w, h):
    url = navegador.url_arquivo(ARTE, urllib.parse.quote(json.dumps(dict(dados, marca=MARCA, handle=HANDLE), ensure_ascii=False)))
    navegador.print_pagina(url, destino_png, w, h)


def jpg(png, destino):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", png, "-q:v", "2", destino], check=True)


def ff(*a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *a], check=True)


def baixar_fotos(item, pasta):
    locais = []
    for i, f in enumerate(item.get("fotos", [])[:3]):
        destino = os.path.join(pasta, f"foto{i}.jpg")
        try:
            dados = urllib.request.urlopen(urllib.request.Request(f["url"], headers=UA), timeout=60).read()
            open(destino, "wb").write(dados)
            locais.append(dict(f, arquivo=destino))
        except Exception as e:
            print("foto não baixou:", f.get("url"), str(e)[:80])
    return locais


def main():
    iid = sys.argv[1]
    item = json.load(open(os.path.join(BASE, "itens", f"{iid}.json"), encoding="utf-8"))
    pasta = os.path.join(BASE, "saida", iid)
    os.makedirs(pasta, exist_ok=True)
    fonte = ", ".join(item.get("fontes", []))

    # STORY (sempre)
    tela({"modo": "story", "blocos": item["story"]["blocos"], "fonte": fonte}, os.path.join(pasta, "story.png"), 1080, 1920)
    jpg(os.path.join(pasta, "story.png"), os.path.join(pasta, "story.jpg"))

    formato = item.get("formato", "story")
    fotos = baixar_fotos(item, pasta) if formato in ("post", "reel", "reel_texto") else []
    if formato in ("post", "reel") and not fotos:
        print("sem foto livre: fica só o story")
        formato = "story"
    credito = " · ".join(dict.fromkeys(f.get("credito", "") for f in fotos if f.get("credito")))

    if formato == "post":
        f0 = fotos[0]
        tela({"modo": "post", "foto": navegador.url_arquivo(f0["arquivo"]), "pos": f0.get("pos", "50% 40%"), "chip": item["chip"],
              "titulo": item["titulo"], "credito": credito}, os.path.join(pasta, "post.png"), 1080, 1350)
        jpg(os.path.join(pasta, "post.png"), os.path.join(pasta, "post.jpg"))
        if len(fotos) > 1:   # 2ª foto do carrossel: outra imagem do assunto + o fato principal numa frase
            f1 = fotos[1]
            tela({"modo": "post", "foto": navegador.url_arquivo(f1["arquivo"]), "pos": f1.get("pos", "50% 40%"), "chip": item["chip"],
                  "titulo": item.get("titulo2") or item["titulo"], "credito": f1.get("credito", "")},
                 os.path.join(pasta, "post2.png"), 1080, 1350)
            jpg(os.path.join(pasta, "post2.png"), os.path.join(pasta, "post2.jpg"))
        tela({"modo": "cta", "blocos": CTA}, os.path.join(pasta, "cta.png"), 1080, 1350)
        jpg(os.path.join(pasta, "cta.png"), os.path.join(pasta, "cta.jpg"))

    vid = item.get("video") if formato == "reel_video" else None
    if formato == "reel_video" and not (vid and os.path.exists(os.path.join(BASE, vid.get("arquivo", "")))):
        print("vídeo livre não encontrado: vira reel_texto")
        formato = "reel_texto"
    if vid and formato == "reel_video":
        credito = vid.get("credito", credito)
    if formato in ("reel", "reel_video"):
        tmp = os.path.join(pasta, "_reel")
        os.makedirs(tmp, exist_ok=True)
        fatos = item.get("fatos") or [[b] for b in item["story"]["blocos"][:3]]
        dur_fato = 4.2
        total = 0.6 + dur_fato * len(fatos) + 0.6
        tela({"modo": "topo", "titulo": item["titulo"]}, os.path.join(tmp, "topo.png"), 1080, 620)
        for i, f in enumerate(fatos):
            tela({"modo": "fato", "blocos": f}, os.path.join(tmp, f"fato{i}.png"), 1080, 1920)
        tela({"modo": "cred2", "credito": credito}, os.path.join(tmp, "cred.png"), 1080, 1920)
        base = os.path.join(tmp, "base.mp4")
        if vid:   # VÍDEO REAL livre (CC BY de quem filmou / oficial) embaixo da faixa, trechos com fade, sem o som original
            trechos = vid.get("trechos") or [[0, total]]
            partes = []
            for n, (ini, d) in enumerate(trechos):
                s = os.path.join(tmp, f"v{n}.mp4")
                ff("-ss", str(ini), "-t", str(d), "-i", os.path.join(BASE, vid["arquivo"]), "-an", "-vf",
                   f"scale=1080:1300:force_original_aspect_ratio=increase,crop=1080:1300:(iw-1080)/2:(ih-1300)*{vid.get('foco', 0.5)},"
                   "fps=30,format=yuv420p,setsar=1", "-c:v", "libx264", "-crf", "19", s)
                partes.append((s, d))
            ent, filtro, ult, off = [], "", "[0:v]", 0.0
            for s, _ in partes:
                ent += ["-i", s]
            for i in range(1, len(partes)):
                off += partes[i - 1][1] - 0.4
                filtro += f"{ult}[{i}:v]xfade=transition=fade:duration=0.4:offset={off:.2f}[x{i}];"
                ult = f"[x{i}]"
            if len(partes) == 1:
                ff(*ent, "-vf", f"tpad=stop_mode=clone:stop_duration={total:.2f}", "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "19", base)
            else:
                ff(*ent, "-filter_complex", filtro.rstrip(";") + f";{ult}tpad=stop_mode=clone:stop_duration={total:.2f}[vv]",
                   "-map", "[vv]", "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "19", base)
            fotos = []
        # fotos embaixo da faixa, andando devagar (sem zoom), divididas no tempo do vídeo
        parte = total / max(len(fotos), 1) + (0.8 if len(fotos) > 1 else 0)
        segs = []
        for i, f in enumerate(fotos):
            cr = (f"crop=1080:1300:(iw-1080)*t/{parte:.2f}:(ih-1300)/2" if i % 2 == 0
                  else f"crop=1080:1300:(iw-1080)/2:(ih-1300)*(1-t/{parte:.2f})")
            s = os.path.join(tmp, f"f{i}.mp4")
            ff("-loop", "1", "-t", f"{parte:.2f}", "-i", f["arquivo"], "-vf",
               f"scale=1210:1456:force_original_aspect_ratio=increase,{cr},fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20", s)
            segs.append(s)
        if vid:
            pass
        elif len(segs) == 1:
            os.replace(segs[0], base)
        else:
            entradas, filtro, ult, off = [], "", "[0:v]", 0.0
            for s in segs:
                entradas += ["-i", s]
            for i in range(1, len(segs)):
                off += parte - 0.8
                filtro += f"{ult}[{i}:v]xfade=transition=fade:duration=0.8:offset={off:.2f}[x{i}];"
                ult = f"[x{i}]"
            ff(*entradas, "-filter_complex", filtro.rstrip(";"), "-map", ult, "-c:v", "libx264", "-crf", "20", base)
        ins = ["-i", base, "-loop", "1", "-t", f"{total:.2f}", "-i", os.path.join(tmp, "topo.png")]
        for i in range(len(fatos)):
            ins += ["-loop", "1", "-t", f"{total:.2f}", "-i", os.path.join(tmp, f"fato{i}.png")]
        ins += ["-loop", "1", "-t", f"{total:.2f}", "-i", os.path.join(tmp, "cred.png")]
        musica = MUSICAS[sum(map(ord, iid)) % len(MUSICAS)]
        ins += ["-ss", "20", "-i", musica]
        n = len(fatos)
        filtro = "[0:v]pad=1080:1920:0:620:black[b0];[b0][1:v]overlay=0:0[t0];"
        for i in range(n):
            a, b = 0.6 + i * dur_fato, 0.6 + (i + 1) * dur_fato
            filtro += f"[t{i}][{2 + i}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[t{i + 1}];"
        filtro += f"[t{n}][{2 + n}:v]overlay=0:0,format=yuv420p[v];[{3 + n}:a]volume=0.35,afade=t=in:d=0.5,afade=t=out:st={total - 0.8:.2f}:d=0.8[a]"
        ff(*ins, "-filter_complex", filtro, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-r", "30",
           "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(pasta, "reel.mp4"))
        ff("-ss", "1.2", "-i", os.path.join(pasta, "reel.mp4"), "-frames:v", "1", "-q:v", "2", os.path.join(pasta, "capa.jpg"))
        formato = "reel"

    if formato == "reel_texto":
        # reel no estilo do story: imagem parada com o texto inteiro, 10 s, música baixa
        blocos = item.get("reel_blocos") or item["story"]["blocos"]
        png = os.path.join(pasta, "reel_texto.png")
        extra = {}
        if fotos:   # foto livre do assunto atrás do texto (deixa o feed variado, não só fundo preto)
            extra = {"foto": navegador.url_arquivo(fotos[0]["arquivo"]), "pos": fotos[0].get("pos", "50% 40%"),
                     "credito": credito, "chip": item.get("chip", "")}
        tela(dict({"modo": "story", "blocos": blocos, "fonte": fonte}, **extra), png, 1080, 1920)
        musica = MUSICAS[sum(map(ord, iid)) % len(MUSICAS)]
        ff("-loop", "1", "-t", "10", "-i", png, "-ss", "20", "-i", musica,
           "-filter_complex", "[0:v]fps=30,format=yuv420p,setsar=1[v];[1:a]volume=0.35,afade=t=in:d=0.5,afade=t=out:st=9.2:d=0.8[a]",
           "-map", "[v]", "-map", "[a]", "-t", "10", "-r", "30", "-c:v", "libx264", "-crf", "20", "-tune", "stillimage",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", os.path.join(pasta, "reel.mp4"))
        jpg(png, os.path.join(pasta, "capa.jpg"))
        formato = "reel"

    json.dump({"formato": formato}, open(os.path.join(pasta, "gerado.json"), "w", encoding="utf-8"))
    print(iid, "->", formato)


if __name__ == "__main__":
    main()
