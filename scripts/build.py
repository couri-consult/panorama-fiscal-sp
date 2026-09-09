# -*- coding: utf-8 -*-
"""
build.py — regenera os dados do painel e os reembute em index.html.

Uso:
    pip install requests
    python scripts/build.py
    git commit -am "atualiza dados" && git push

O painel (index.html) é autocontido: os dados ficam embutidos em 4 blocos
<script id="data|analysis|inv|ampl">. Este script roda o pipeline do SICONFI
(RREO + RGF + DCA), deflaciona pelo IPCA e substitui apenas esses 4 blocos,
preservando todo o texto e o layout do painel.

Parametrizado por ente no topo — troque ENTE/UF/NOME para outro estado.
"""
import os, sys, re, json, subprocess

# ---------------- parâmetros do ente ----------------
ENTE = "35"                       # código IBGE do estado (São Paulo = 35)
UF = "SP"                         # sigla (filtro dos CSVs da CAPAG)
NOME = "Governo do Estado de Sao Paulo"
# ----------------------------------------------------

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPTS)
BUILD = os.path.join(SCRIPTS, "_build")
INDEX = os.path.join(REPO, "index.html")
os.makedirs(BUILD, exist_ok=True)

FISCAL_JSON = "fiscal.json"
CAPAG_JSON = "capag.json"

env = dict(os.environ)
env.update(ENTE=ENTE, UF=UF, DATADIR=BUILD, FISCAL_JSON=FISCAL_JSON, CAPAG_JSON=CAPAG_JSON,
           PYTHONIOENCODING="utf-8")


def run(script):
    print(f"\n=== {script} ===")
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)], env=env, cwd=SCRIPTS)
    if r.returncode != 0:
        sys.exit(f"falha em {script}")


def fetch_ipca():
    """IPCA mensal (BCB SGS série 433) -> scripts/ipca_433.json (usado pelo deflate.py)."""
    import requests
    print("\n=== IPCA (BCB SGS 433) ===")
    url = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
           "?formato=json&dataInicial=01/01/2016&dataFinal=31/12/2030")
    d = requests.get(url, timeout=90).json()
    json.dump(d, open(os.path.join(SCRIPTS, "ipca_433.json"), "w"), ensure_ascii=False)
    print(f"IPCA: {len(d)} meses")


def load(name):
    return json.load(open(os.path.join(BUILD, name), encoding="utf-8"))


def build_embeds():
    """Gera dashboard_data.json, analysis_embed.json e invest_ampliado.json no BUILD."""
    fisc = load(FISCAL_JSON)
    capag = load(CAPAG_JSON)
    json.dump({"fiscal": fisc, "capag": capag,
               "meta": {"ente": NOME, "id_ente": int(ENTE),
                        "fonte": "SICONFI/STN (RREO e RGF) e Boletim CAPAG/STN"}},
              open(os.path.join(BUILD, "dashboard_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    a = load("analysis_real.json")
    comps = ["receita_corrente", "receita_impostos_taxas", "rcl", "desp_corrente_total",
             "desp_corr_pessoal", "desp_corr_juros", "desp_corr_outras", "desp_capital_total",
             "desp_cap_investimentos", "desp_cap_inversoes", "desp_cap_amortizacao"]
    labels = {"receita_corrente": "Receita corrente", "receita_impostos_taxas": "Impostos e taxas",
              "rcl": "RCL", "desp_corrente_total": "Despesa corrente", "desp_corr_pessoal": "Pessoal",
              "desp_corr_juros": "Juros da dívida", "desp_corr_outras": "Outras desp. correntes",
              "desp_capital_total": "Despesa de capital", "desp_cap_investimentos": "Investimentos",
              "desp_cap_inversoes": "Inversões financeiras", "desp_cap_amortizacao": "Amortização da dívida"}
    json.dump({"base": a["base"], "ipca_full": a["ipca_2017_2025"], "ipca_tarc": a["ipca_2022_2025"],
               "labels": labels, "comps": comps,
               "full": {k: a["full"][k] for k in comps},
               "tarcisio": {k: a["tarcisio"][k] for k in comps},
               "real_series": {k: a["real_series"][k] for k in comps},
               "decomp": a["decomp"]},
              open(os.path.join(BUILD, "analysis_embed.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    defl = a["deflator_flow"]
    fmap = {d["ano"]: d for d in fisc}
    inv = {d["ano"]: d for d in load("inversoes_series.json")}
    R = lambda v, ano: v * defl[str(ano)]
    series = [{"ano": y, "invdir": R(fmap[y]["desp_cap_investimentos"], y),
               "capital": R(inv[y]["capital"], y), "ppp": R(inv[y]["ppp"], y)}
              for y in range(2018, 2026) if y in fmap and y in inv]

    def avg(key, anos):
        vals = [next(s[key] for s in series if s["ano"] == a) for a in anos if any(s["ano"] == a for s in series)]
        return sum(vals) / len(vals) if vals else 0
    avgs = {"gestao_ant": {"label": "Gestão anterior (2019–2022)",
                           "invdir": avg("invdir", range(2019, 2023)),
                           "ampl": avg("invdir", range(2019, 2023)) + avg("capital", range(2019, 2023)) + avg("ppp", range(2019, 2023))},
            "tarcisio": {"label": "Gestão Tarcísio (2023–2025)",
                         "invdir": avg("invdir", range(2023, 2026)),
                         "ampl": avg("invdir", range(2023, 2026)) + avg("capital", range(2023, 2026)) + avg("ppp", range(2023, 2026))}}
    json.dump({"base": 2025, "series": series, "avgs": avgs},
              open(os.path.join(BUILD, "invest_ampliado.json"), "w", encoding="utf-8"),
              ensure_ascii=False)


def embed_into_index():
    """Substitui os 4 blocos <script id=...> em index.html pelos JSON recém-gerados."""
    html = open(INDEX, encoding="utf-8").read()
    mapping = {"data": "dashboard_data.json", "analysis": "analysis_embed.json",
               "inv": "inversoes_series.json", "ampl": "invest_ampliado.json"}
    for sid, fname in mapping.items():
        data = open(os.path.join(BUILD, fname), encoding="utf-8").read()
        pat = re.compile(r'(<script id="' + sid + r'" type="application/json">).*?(</script>)', re.DOTALL)
        new, n = pat.subn(lambda m: m.group(1) + data + m.group(2), html, count=1)
        if n != 1:
            sys.exit(f"bloco <script id=\"{sid}\"> não encontrado em index.html")
        html = new
    open(INDEX, "w", encoding="utf-8").write(html)
    print("\nindex.html atualizado (4 blocos de dados reembutidos).")


if __name__ == "__main__":
    fetch_ipca()
    run("collect.py")
    run("process.py")
    run("capag.py")
    run("deflate.py")
    run("inversoes.py")
    build_embeds()
    embed_into_index()
    print("\nOK. Revise o painel e rode:  git commit -am \"atualiza dados\" && git push")
