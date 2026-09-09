# -*- coding: utf-8 -*-
"""Decompõe Inversões Financeiras (grupo 4.5) por finalidade via DCA-Anexo I-D, 2018-2025.
Buckets: aumento de capital de empresas (elem 65), PPP (mod 67), intraorçamentária (mod 91),
títulos/imóveis/outros. Base liquidada."""
import requests, json, os

D = os.environ.get("DATADIR", os.path.dirname(__file__))
ENTE = int(os.environ.get("ENTE", "35"))

def fetch(ano):
    r = requests.get("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca",
                     params=dict(an_exercicio=ano, id_ente=ENTE, no_anexo="DCA-Anexo I-D"),
                     timeout=180)
    return r.json().get("items", [])

def val(items, core_code):
    for i in items:
        core = i["cod_conta"].replace("DO", "").replace("DI", "")
        if core == core_code and i["coluna"] == "Despesas Liquidadas":
            return i["valor"] or 0
    return 0

series = []
for ano in range(2018, 2026):
    items = fetch(ano)
    if not items:
        continue
    total = val(items, "4.5.00.00.00.00")            # grupo (inclui intra)
    capital = val(items, "4.5.90.65.00.00")          # aumento de capital de empresas
    ppp = val(items, "4.5.67.00.00.00")              # execução de PPP
    intra = val(items, "4.5.91.00.00.00")            # intraorçamentária (entre órgãos)
    titulos = val(items, "4.5.90.63.00.00")          # aquisição de títulos de crédito
    imoveis = val(items, "4.5.90.61.00.00")          # aquisição de imóveis
    outros = total - capital - ppp - intra - titulos - imoveis
    series.append({"ano": ano, "total": total, "capital": capital, "ppp": ppp,
                   "intra": intra, "titulos": titulos, "imoveis": imoveis, "outros": outros})

print(f"{'ano':4} {'total':>7} {'capital':>8} {'PPP':>7} {'intra':>7} {'títulos':>8} {'outros':>7}")
for s in series:
    b = lambda x: x/1e9
    print(f"{s['ano']:4} {b(s['total']):7.2f} {b(s['capital']):8.2f} {b(s['ppp']):7.2f} "
          f"{b(s['intra']):7.2f} {b(s['titulos']):8.2f} {b(s['outros']):7.2f}")

json.dump(series, open(os.path.join(D, "inversoes_series.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\ninversoes_series.json salvo.")
