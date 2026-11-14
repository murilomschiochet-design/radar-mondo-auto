"""Tira print de uma página HTML local (fundo transparente): Edge no Windows, Chromium (playwright) na nuvem/Linux."""
import os
import pathlib
import subprocess

EDGE = next((p for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                         r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"] if os.path.exists(p)), None)
SEM_JANELA = 0x08000000 if os.name == "nt" else 0
_pw = None


def url_arquivo(caminho, hash_txt=""):
    u = pathlib.Path(caminho).resolve().as_uri()
    return u + ("#" + hash_txt if hash_txt else "")


def print_pagina(url, destino, largura, altura, espera_ms=6000):
    if os.path.exists(destino):
        os.remove(destino)
    if EDGE and os.environ.get("USAR_PLAYWRIGHT") != "1":
        r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                            "--default-background-color=00000000", f"--virtual-time-budget={espera_ms}",
                            f"--window-size={largura},{altura}", f"--screenshot={destino}", url],
                           capture_output=True, text=True, creationflags=SEM_JANELA)
    else:
        global _pw
        from playwright.sync_api import sync_playwright
        if _pw is None:
            p = sync_playwright().start()
            args = ["--allow-file-access-from-files", "--no-sandbox"]
            try:
                _pw = p.chromium.launch(args=args)
            except Exception:                       # na nuvem: usa o Chrome já instalado
                _pw = p.chromium.launch(args=args, executable_path=next(
                    x for x in ["/usr/bin/google-chrome", "/opt/pw-browsers/chromium/chrome-linux/chrome"] if os.path.exists(x)))
        pg = _pw.new_page(viewport={"width": largura, "height": altura})
        pg.goto(url)
        pg.wait_for_function("document.title === 'ok' || document.title === 'grande'", timeout=espera_ms * 2)
        pg.screenshot(path=destino, omit_background=True)
        pg.close()
    import time
    for _ in range(60):                     # o Edge às vezes termina antes de gravar o arquivo: espera até 15 s
        if os.path.exists(destino) and os.path.getsize(destino) > 0:
            break
        time.sleep(0.25)
    if not os.path.exists(destino):
        raise RuntimeError("o navegador não gerou a imagem")
