# -*- coding: utf-8 -*-
"""Deflaciona a serie fiscal pelo IPCA (media anual, base = 2025) e analisa
crescimento real por componente: periodo completo (2017-2025) e gestao Tarcisio (2022-2025).
Tambem decompoe a queda de DCL/RCL em efeito-divida (numerador) vs efeito-RCL (denominador)."""
import json, os

D = os.environ.get("DATADIR", os.path.dirname(__file__))
IPCA_DIR = os.path.dirname(__file__)  # IPCA é nacional, compartilhado
ipca = json.load(open(os.path.join(IPCA_DIR, "ipca_433.json"), encoding="utf-8"))
fisc = json.load(open(os.path.join(D, os.environ.get("FISCAL_JSON", "fiscal_sp.json")), encoding="utf-8"))

# --- indice de precos mensal encadeado ---
idx = 100.0
monthly = []  # (ano, mes, indice_no_fim_do_mes, fator_do_mes)
for row in ipca:
    dd = row["data"]           # dd/mm/aaaa
    mes = int(dd[3:5]); ano = int(dd[6:10])
    var = float(row["valor"]) / 100.0
    idx *= (1 + var)
    monthly.append((ano, mes, idx))

# indice MEDIO anual (media dos indices mensais) — apropriado p/ deflacionar fluxos
from collections import defaultdict
byyear = defaultdict(list)
for ano, mes, i in monthly:
    byyear[ano].append(i)
avg_idx = {a: sum(v) / len(v) for a, v in byyear.items()}
# indice de DEZEMBRO (fim de ano) — apropriado p/ estoques (divida)
dec_idx = {}
for ano, mes, i in monthly:
    if mes == 12:
        dec_idx[ano] = i
# 2026 ainda sem dezembro: usa ultimo mes disponivel
last_by_year = {}
for ano, mes, i in monthly:
    last_by_year[ano] = i
for a in byyear:
    dec_idx.setdefault(a, last_by_year[a])

BASE = 2025
defl_flow = {a: avg_idx[BASE] / avg_idx[a] for a in avg_idx}   # multiplicador p/ fluxos
defl_stock = {a: dec_idx[BASE] / dec_idx[a] for a in dec_idx}  # multiplicador p/ estoques

# IPCA acumulado do periodo (para referencia)
ipca_2017_2025 = avg_idx[2025] / avg_idx[2017] - 1
ipca_2022_2025 = avg_idx[2025] / avg_idx[2022] - 1

FLOW_COMPS = {
    "receita_corrente": "Receita corrente",
    "receita_impostos_taxas": "Impostos, taxas e contrib.",
    "rcl": "RCL",
    "desp_corrente_total": "Despesa corrente total",
    "desp_corr_pessoal": "Pessoal e encargos",
    "desp_corr_juros": "Juros e encargos da dívida",
    "desp_corr_outras": "Outras despesas correntes",
    "desp_capital_total": "Despesa de capital total",
    "desp_cap_investimentos": "Investimentos",
    "desp_cap_inversoes": "Inversões financeiras",
    "desp_cap_amortizacao": "Amortização da dívida",
}

byano = {d["ano"]: d for d in fisc}

def real_flow(key, ano):
    v = byano[ano].get(key)
    return None if v is None else v * defl_flow[ano]

# --- serie real (fluxos, base 2025) para todos os anos completos + 2026 (parcial) ---
real_series = {}
for key in FLOW_COMPS:
    real_series[key] = {a: real_flow(key, a) for a in sorted(byano)}

# --- crescimento real por componente ---
def growth(key, y0, y1):
    a = real_flow(key, y0); b = real_flow(key, y1)
    if not a or not b: return None
    tot = (b / a - 1) * 100
    n = y1 - y0
    cagr = ((b / a) ** (1 / n) - 1) * 100
    return {"real_ini": a, "real_fim": b, "var_total_real": tot, "cagr_real": cagr}

print(f"IPCA acumulado (média anual): 2017→2025 = {ipca_2017_2025*100:.1f}% | 2022→2025 = {ipca_2022_2025*100:.1f}%\n")
print(f"{'Componente':32} | {'Real 2017 (bi)':>13} {'Real 2025 (bi)':>13} | {'Δreal 17-25':>11} {'a.a.':>7} | {'Δreal 22-25':>11} {'a.a.':>7}")
analysis = {"full": {}, "tarcisio": {}, "deflator_flow": defl_flow, "deflator_stock": defl_stock,
            "ipca_2017_2025": ipca_2017_2025*100, "ipca_2022_2025": ipca_2022_2025*100,
            "real_series": real_series, "base": BASE}
for key, lab in FLOW_COMPS.items():
    gf = growth(key, 2017, 2025)
    gt = growth(key, 2022, 2025)
    analysis["full"][key] = gf
    analysis["tarcisio"][key] = gt
    print(f"{lab:32} | {gf['real_ini']/1e9:13.1f} {gf['real_fim']/1e9:13.1f} | "
          f"{gf['var_total_real']:+10.1f}% {gf['cagr_real']:+6.1f}% | "
          f"{gt['var_total_real']:+10.1f}% {gt['cagr_real']:+6.1f}%")

# --- decomposicao DCL/RCL ---
print("\n=== Decomposição da queda de DCL/RCL ===")
def dcl_rcl(a): return byano[a]["dcl"]/byano[a]["rcl"]*100
for y0,y1,lab in [(2017,2025,"Período completo 2017→2025"),(2020,2021,"Salto 2020→2021"),(2022,2025,"Gestão Tarcísio 2022→2025")]:
    dcl0,dcl1=byano[y0]["dcl"],byano[y1]["dcl"]
    rcl0,rcl1=byano[y0]["rcl"],byano[y1]["rcl"]
    r0,r1=dcl0/rcl0*100,dcl1/rcl1*100
    # nominal
    dcl_g=(dcl1/dcl0-1)*100; rcl_g=(rcl1/rcl0-1)*100
    # real
    dcl0r=dcl0*defl_stock[y0]; dcl1r=dcl1*defl_stock[y1]
    rcl0r=rcl0*defl_flow[y0]; rcl1r=rcl1*defl_flow[y1]
    dcl_gr=(dcl1r/dcl0r-1)*100; rcl_gr=(rcl1r/rcl0r-1)*100
    # contrafactual: se DCL parada, ratio seria dcl0/rcl1; se RCL parada, dcl1/rcl0
    ratio_so_rcl = dcl0/rcl1*100   # mantendo DCL de y0, variando so RCL
    ratio_so_dcl = dcl1/rcl0*100   # mantendo RCL de y0, variando so DCL
    analysis.setdefault("decomp",{})[lab]={
        "r0":r0,"r1":r1,"dcl_nom_g":dcl_g,"rcl_nom_g":rcl_g,"dcl_real_g":dcl_gr,"rcl_real_g":rcl_gr,
        "ratio_so_rcl":ratio_so_rcl,"ratio_so_dcl":ratio_so_dcl}
    print(f"\n{lab}: DCL/RCL {r0:.0f}% → {r1:.0f}%")
    print(f"  DCL nominal {dcl_g:+.1f}% | real {dcl_gr:+.1f}%")
    print(f"  RCL nominal {rcl_g:+.1f}% | real {rcl_gr:+.1f}%")
    print(f"  se só RCL mudasse (DCL fixa em {y0}): {r0:.0f}% → {ratio_so_rcl:.0f}%  (variação {ratio_so_rcl-r0:+.0f} p.p.)")
    print(f"  se só DCL mudasse (RCL fixa em {y0}): {r0:.0f}% → {ratio_so_dcl:.0f}%  (variação {ratio_so_dcl-r0:+.0f} p.p.)")

json.dump(analysis, open(os.path.join(D,"analysis_real.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nanalysis_real.json salvo.")
