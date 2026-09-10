# -*- coding: utf-8 -*-
"""Processa os JSON brutos do SICONFI e gera dataset consolidado (fiscal_sp.json / .csv)."""
import json, os, csv

DATADIR = os.environ.get("DATADIR", os.path.dirname(__file__))
RAW = os.path.join(DATADIR, "raw")
OUT = DATADIR
FISCAL_JSON = os.environ.get("FISCAL_JSON", "fiscal_sp.json")
FISCAL_CSV = FISCAL_JSON.replace(".json", ".csv")
ANOS = list(range(2017, 2027))

def load(ano, tag):
    return json.load(open(os.path.join(RAW, f"{ano}_{tag}.json"), encoding="utf-8"))

def num(v):
    if v in (None, "", "n.d", "-"):
        return None
    try:
        return float(v)
    except Exception:
        return None

def pick(items, code, col_patterns, rotulo=None, conta_pat=None):
    """Retorna o primeiro valor de `code` cuja coluna casa (por prefixo/substring)
    com algum padrao em col_patterns (na ordem de prioridade)."""
    cand = [i for i in items if i["cod_conta"] == code]
    if rotulo is not None:
        cand = [i for i in cand if i.get("rotulo") == rotulo]
    if conta_pat is not None:
        cand = [i for i in cand if conta_pat.lower() in i["conta"].lower()]
    for pat in col_patterns:
        pl = pat.lower()
        for i in cand:
            col = i["coluna"].strip().lower()
            if col.startswith(pl) or pl in col:
                v = num(i["valor"])
                if v is not None:
                    return v
    return None

def quad_cols():
    # ordem: pega o quadrimestre mais recente com dado
    return ["Até o 3º Quadrimestre", "Até o 2º Quadrimestre", "Até o 1º Quadrimestre"]

def pick_quad(items, code):
    cand = [i for i in items if i["cod_conta"] == code]
    for col in quad_cols():
        for i in cand:
            if i["coluna"].strip() == col:
                v = num(i["valor"])
                if v is not None:
                    return v
    return None

def process_year(ano):
    d = {"ano": ano}
    a1 = load(ano, "rreo01")
    a3 = load(ano, "rreo03")
    a6 = load(ano, "rreo06")
    g1 = load(ano, "rgf01")
    g2 = load(ano, "rgf02")
    g3 = load(ano, "rgf03")
    g4 = load(ano, "rgf04")
    try:
        g5 = load(ano, "rgf05")
    except Exception:
        g5 = []

    REC = ["Até o Bimestre (c)"]
    DESP = ["DESPESAS LIQUIDADAS ATÉ O BIMESTRE (h)", "DESPESAS LIQUIDADAS ATÉ O BIMESTRE"]

    # --- RREO Anexo 01: receitas e despesas por natureza ---
    d["receita_corrente"]        = pick(a1, "ReceitasCorrentes", REC)
    d["receita_impostos_taxas"]  = pick(a1, "ReceitaTributaria", REC)   # Impostos, Taxas e Contrib. Melhoria
    d["receita_impostos"]        = pick(a1, "Impostos", REC)
    d["desp_corrente_total"]     = pick(a1, "DespesasCorrentes", DESP)
    d["desp_corr_pessoal"]       = pick(a1, "PessoalEEncargosSociais", DESP)
    d["desp_corr_juros"]         = pick(a1, "JurosEEncargosDaDivida", DESP)
    d["desp_corr_outras"]        = pick(a1, "OutrasDespesasCorrentes", DESP)
    d["desp_capital_total"]      = pick(a1, "DespesasDeCapital", DESP)
    d["desp_cap_investimentos"]  = pick(a1, "Investimentos", DESP)
    d["desp_cap_inversoes"]      = pick(a1, "InversoesFinanceiras", DESP)
    d["desp_cap_amortizacao"]    = pick(a1, "AmortizacaoDaDivida", DESP)

    # resultado corrente = receita corrente - despesa corrente
    if d["receita_corrente"] is not None and d["desp_corrente_total"] is not None:
        d["resultado_corrente"] = d["receita_corrente"] - d["desp_corrente_total"]
    else:
        d["resultado_corrente"] = None
    # despesa corrente / receita corrente
    if d["receita_corrente"]:
        d["desp_corr_sobre_rec_corr"] = 100 * d["desp_corrente_total"] / d["receita_corrente"]
    else:
        d["desp_corr_sobre_rec_corr"] = None

    # --- RREO Anexo 03: RCL ---
    d["rcl"] = pick(a3, "RREO3ReceitaCorrenteLiquida", ["TOTAL (ÚLTIMOS 12 MESES)", "TOTAL"]) \
               or pick(a3, "ReceitaCorrenteLiquida", ["TOTAL (ÚLTIMOS 12 MESES)", "TOTAL"])

    # --- RREO Anexo 06: primário ---
    d["receita_primaria"] = pick(a6, "RREO6TotalReceitaPrimaria",
                                 ["RECEITAS REALIZADAS (a)", f"Até o Bimestre / {ano}"])
    d["despesa_primaria"] = pick(a6, "RREO6TotalDespesaPrimaria",
                                 ["DESPESAS LIQUIDADAS", f"Despesas Liquidadas Até o Bimestre / {ano}"])
    res = pick(a6, "ResultadoPrimarioComRPPSAcimaDaLinha", ["VALOR"])
    if res is None:
        res = pick(a6, "RREO6ResultadoPrimarioEstadosMunicipios",
                   ["VALOR", f"Despesas Liquidadas Até o Bimestre / {ano}"])
    d["resultado_primario"] = res

    # --- projeção anual (Previsão/Dotação Atualizada) — p/ o ano parcial corrente ---
    PREV = ["PREVISÃO ATUALIZADA"]
    DOT = ["DOTAÇÃO ATUALIZADA (e)", "DOTAÇÃO ATUALIZADA"]
    proj = {
        "receita_primaria": pick(a6, "RREO6TotalReceitaPrimaria", PREV),
        "despesa_primaria": pick(a6, "RREO6TotalDespesaPrimaria", DOT),
        "desp_corr_pessoal": pick(a1, "PessoalEEncargosSociais", DOT),
        "desp_corr_outras": pick(a1, "OutrasDespesasCorrentes", DOT),
        "desp_cap_investimentos": pick(a1, "Investimentos", DOT),
        "desp_cap_inversoes": pick(a1, "InversoesFinanceiras", DOT),
    }
    if proj["receita_primaria"] is not None and proj["despesa_primaria"] is not None:
        proj["resultado_primario"] = proj["receita_primaria"] - proj["despesa_primaria"]
    else:
        proj["resultado_primario"] = None
    d["projecao"] = proj

    # --- RGF Anexo 01: pessoal ---
    VALP = ["TOTAL (ÚLTIMOS 12 MESES) (a)", "DESPESAS LIQUIDADAS", "Valor"]
    PCT = ["% sobre a RCL Ajustada", "% sobre a RCL"]
    d["pessoal_dtp"]        = pick(g1, "DespesaComPessoalTotal", VALP)
    d["pessoal_rcl_ajust"]  = pick(g1, "ReceitaCorrenteLiquidaAjustada", VALP) or \
                              pick(g1, "ReceitaCorrenteLiquidaLimiteLegal", VALP)
    d["pessoal_pct_rcl"]    = pick(g1, "DespesaComPessoalTotal", PCT)
    d["pessoal_lim_max"]    = pick(g1, "LimiteMaximoDespesaComPessoalTotal", PCT)
    d["pessoal_lim_prud"]   = pick(g1, "LimitePrudencialDespesaComPessoalTotal", PCT)
    d["pessoal_lim_alerta"] = pick(g1, "LimiteDeAlertaDespesaComPessoalTotal", PCT)

    # --- RGF Anexo 02: dívida ---
    d["dc_bruta"]      = pick_quad(g2, "DividaConsolidada")
    d["dcl"]           = pick_quad(g2, "DividaConsolidadaLiquida")
    d["divida_rcl_aj"] = pick_quad(g2, "ReceitaCorrenteLiquidaAjustadaParaCalculoDosLimitesDeEndividamento") \
                         or pick_quad(g2, "RGF2ReceitaCorrenteLiquida")
    d["dc_pct_rcl"]    = pick_quad(g2, "PercentualDaDCSobreARCL")
    d["dcl_pct_rcl"]   = pick_quad(g2, "PercentualDaDCLSobreARCL")
    d["divida_limite"] = pick_quad(g2, "LimiteDefinidoPorResolucaoDoSenadoFederal")
    d["caixa_bruta_a2"] = pick_quad(g2, "DisponibilidadeDeCaixaBrutaAnexo02")

    # --- RGF Anexo 03: garantias ---
    d["garantias_total"]   = pick_quad(g3, "TotalGarantiasConcedidas")
    d["garantias_pct_rcl"] = pick_quad(g3, "PercentualDoTotalDasGarantiasSobreARCL")
    d["garantias_limite"]  = pick_quad(g3, "LimiteDefinidoPorResolucaoDoSenadoFederal")

    # --- RGF Anexo 04: operações de crédito ---
    VALOC = ["Até o Quadrimestre de Referência (a)", "VALOR"]
    d["opcredito_total"]   = pick(g4, "RGF4OperacoesDeCreditoTotal", VALOC)
    d["opcredito_apurado"] = pick(g4, "TotalConsideradoParaFinsDaApuracaoDoCumprimentoDoLimiteOperacoesDeCredito", VALOC)
    d["opcredito_pct_rcl"] = pick(g4, "TotalConsideradoParaFinsDaApuracaoDoCumprimentoDoLimiteOperacoesDeCredito", PCT) \
                             or pick(g4, "RGF4OperacoesDeCreditoTotal", PCT)
    d["opcredito_limite"]  = pick(g4, "LimiteGeralDefinidoPorResolucaoDoSenadoFederalParaAsOperacoesDeCreditoInternasEExternas", PCT)

    # --- RGF Anexo 05: disponibilidade de caixa (linha TOTAL) ---
    def caixa(col_prefixes, code):
        cand = [i for i in g5 if i["cod_conta"] == code
                and i["conta"].strip().startswith("TOTAL (")
                and ("= (I" in i["conta"] or "I + II" in i["conta"])]
        for i in cand:
            for p in col_prefixes:
                if i["coluna"].strip().startswith(p):
                    v = num(i["valor"])
                    if v is not None:
                        return v
        return None
    d["caixa_bruta"]   = caixa(["DISPONIBILIDADE DE CAIXA BRUTA"], "DisponibilidadeDeCaixaBruta")
    d["caixa_liquida"] = caixa(["DISPONIBILIDADE DE CAIXA LÍQUIDA (ANTES"], "DisponibilidadeDeCaixaLiquida")
    if d["caixa_bruta"] is None:
        d["caixa_bruta"] = d["caixa_bruta_a2"]
    return d

def main():
    data = [process_year(a) for a in ANOS]
    json.dump(data, open(os.path.join(OUT, FISCAL_JSON), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    keys = list(data[0].keys())
    with open(os.path.join(OUT, FISCAL_CSV), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys, delimiter=";")
        w.writeheader()
        for row in data:
            w.writerow(row)
    # imprime tabela de conferência
    print("ano | RecCorr | DespCorr | RCL | DCbruta | DCL | DCL% | Pessoal% | ResPrim | CaixaLiq")
    for d in data:
        def f(x, sc=1e9):
            return "  n/a" if x is None else f"{x/sc:6.1f}"
        print(f"{d['ano']} | {f(d['receita_corrente'])} | {f(d['desp_corrente_total'])} | {f(d['rcl'])} |"
              f" {f(d['dc_bruta'])} | {f(d['dcl'])} | {('n/a' if d['dcl_pct_rcl'] is None else format(d['dcl_pct_rcl'],'.1f'))} |"
              f" {('n/a' if d['pessoal_pct_rcl'] is None else format(d['pessoal_pct_rcl'],'.1f'))} |"
              f" {f(d['resultado_primario'])} | {f(d['caixa_liquida'])}")

if __name__ == "__main__":
    main()
