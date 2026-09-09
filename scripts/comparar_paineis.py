# -*- coding: utf-8 -*-
"""
comparar_paineis.py — detector de divergência entre os painéis SP e PI.

Os dois painéis compartilham um "motor" (o CSS + as funções de gráfico em JS) que
DEVE ser idêntico. Só os dados e o texto/narrativa é que mudam por estado. Este
script extrai o motor dos dois index.html e avisa se algo divergiu.

Uso:
    python comparar_paineis.py
    python comparar_paineis.py /caminho/sp/index.html /caminho/pi/index.html

Sai com código 0 se o motor está idêntico; 1 se há divergência.
"""
import sys, os, re, difflib

def default_paths():
    here = os.path.dirname(os.path.abspath(__file__))
    projetos = os.path.abspath(os.path.join(here, "..", ".."))
    return (os.path.join(projetos, "panorama-fiscal-sp", "index.html"),
            os.path.join(projetos, "panorama-fiscal-pi", "index.html"))

def read(p):
    return open(p, encoding="utf-8").read()

def get_css(html):
    m = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    return (m.group(1) if m else "").strip()

def get_main_script(html):
    # o <script> principal é o que NÃO é application/json
    for m in re.finditer(r"<script(?![^>]*application/json)[^>]*>(.*?)</script>", html, re.DOTALL):
        body = m.group(1)
        if "function" in body or "=>" in body:
            return body
    return ""

def extract_defs(js):
    """Retorna {nome: corpo_normalizado} para funções/const de nível superior."""
    defs = {}
    i, n = 0, len(js)
    # só definições de NÍVEL SUPERIOR (indentação de exatamente 2 espaços dentro da IIFE):
    # é aí que vive o motor. Locais de conteúdo ficam mais indentados e são ignorados.
    pat = re.compile(r"\n {2}(?! )(?:function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=)")
    for m in pat.finditer(js):
        name = m.group(1) or m.group(2)
        start = m.start()
        j = m.end()
        # encontra o fim: se houver '{' antes de ';' no nível 0, casa chaves; senão vai até ';'
        # varre a partir de j equilibrando () e {}
        depth_c = depth_p = 0
        seen_brace = False
        k = j
        while k < n:
            ch = js[k]
            if ch == "{":
                depth_c += 1; seen_brace = True
            elif ch == "}":
                depth_c -= 1
            elif ch == "(":
                depth_p += 1
            elif ch == ")":
                depth_p -= 1
            elif ch == ";" and depth_c == 0 and depth_p == 0:
                k += 1; break
            if seen_brace and depth_c == 0 and depth_p == 0:
                k += 1; break
            k += 1
        body = js[start:k]
        # normaliza espaços em branco para comparar lógica, não formatação
        norm = re.sub(r"\s+", " ", body).strip()
        defs[name] = norm
    return defs

def main():
    if len(sys.argv) >= 3:
        sp_path, pi_path = sys.argv[1], sys.argv[2]
    else:
        sp_path, pi_path = default_paths()
    for p in (sp_path, pi_path):
        if not os.path.exists(p):
            print(f"ERRO: não encontrei {p}"); return 2
    sp, pi = read(sp_path), read(pi_path)

    problemas = 0
    print("=" * 64)
    print("COMPARAÇÃO DO MOTOR  (SP  x  PI)")
    print(f"  SP: {sp_path}")
    print(f"  PI: {pi_path}")
    print("=" * 64)

    # 1) CSS
    css_sp, css_pi = get_css(sp), get_css(pi)
    if css_sp == css_pi:
        print("\n[CSS]  IDÊNTICO ✅  ({} linhas)".format(css_sp.count(chr(10)) + 1))
    else:
        problemas += 1
        print("\n[CSS]  DIVERGE ❌")
        for line in difflib.unified_diff(css_sp.splitlines(), css_pi.splitlines(),
                                         "SP/style", "PI/style", lineterm=""):
            print("   " + line)

    # 2) Funções do motor
    dsp, dpi = extract_defs(get_main_script(sp)), extract_defs(get_main_script(pi))
    comuns = sorted(set(dsp) & set(dpi))
    so_sp = sorted(set(dsp) - set(dpi))
    so_pi = sorted(set(dpi) - set(dsp))
    divergentes = [n for n in comuns if dsp[n] != dpi[n]]

    print(f"\n[JS] definições em comum: {len(comuns)} | só no SP: {len(so_sp)} | só no PI: {len(so_pi)}")
    if divergentes:
        problemas += 1
        print(f"\n[JS]  {len(divergentes)} DEFINIÇÃO(ÕES) EM COMUM QUE DIVERGEM ❌  (avalie se é motor ou conteúdo):")
        for nch in divergentes:
            print(f"   • {nch}")
    else:
        print("\n[JS]  todas as definições em comum estão IDÊNTICAS ✅")

    if so_sp:
        print(f"\n[JS]  definições SÓ no SP (provável conteúdo específico): {', '.join(so_sp)}")
    if so_pi:
        print(f"\n[JS]  definições SÓ no PI (provável conteúdo específico): {', '.join(so_pi)}")

    # 3) dados nacionais compartilhados (bloco <script id="natl">): devem ser idênticos
    def natl(html):
        m = re.search(r'<script id="natl"[^>]*>(.*?)</script>', html, re.DOTALL)
        return (m.group(1).strip() if m else None)
    nsp, npi = natl(sp), natl(pi)
    if nsp is None and npi is None:
        pass
    elif nsp == npi:
        print("\n[DADOS NACIONAIS]  bloco 'natl' IDÊNTICO ✅")
    else:
        problemas += 1
        print("\n[DADOS NACIONAIS]  bloco 'natl' DIVERGE ❌ (é dado compartilhado — atualize os dois)")

    print("\n" + "=" * 64)
    if problemas == 0:
        print("RESULTADO: motor IDÊNTICO ✅  — nada a propagar.")
    else:
        print("RESULTADO: há DIVERGÊNCIA no que deveria ser compartilhado ❌")
        print("Reveja os itens acima: se for do motor, replique no outro painel;")
        print("se for conteúdo específico do estado, tudo bem.")
    print("=" * 64)
    return 1 if problemas else 0

if __name__ == "__main__":
    sys.exit(main())
