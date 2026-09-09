# -*- coding: utf-8 -*-
"""Extrai a serie historica da CAPAG de SP dos CSVs em ../capag/."""
import csv, os, json, re

CAPDIR = os.path.join(os.path.dirname(__file__), "..", "capag")
OUT = os.environ.get("DATADIR", os.path.dirname(__file__))
UF = os.environ.get("UF", "SP")
CAPAG_JSON = os.environ.get("CAPAG_JSON", "capag_sp.json")

def parse_pct(s, decimal_fmt):
    """decimal_fmt=True quando o arquivo usa fracao decimal (0,9368) em vez de %."""
    if s is None: return None
    s = s.strip()
    if s in ("", "n.d", "-", "nd"): return None
    had_pct = "%" in s
    s = s.replace("%", "").replace(".", "").replace(",", ".").strip()
    try:
        v = float(s)
    except ValueError:
        return None
    if decimal_fmt and not had_pct:
        v = v * 100  # fracao -> %
    return v

def get_sp_row(path):
    with open(path, encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f, delimiter=";")]
    # acha header (linha que comeca com UF)
    hdr_idx = next((i for i, r in enumerate(rows) if r and r[0].strip().upper() == "UF"), 0)
    header = [c.strip() for c in rows[hdr_idx]]
    for r in rows[hdr_idx + 1:]:
        if r and r[0].strip().upper() == UF:
            return header, r
    return header, None

def main():
    series = {}
    for ano in range(2018, 2026):
        path = os.path.join(CAPDIR, f"capagdosestados{ano}.csv")
        if not os.path.exists(path):
            continue
        header, row = get_sp_row(path)
        if row is None:
            continue
        raw = [c.strip() for c in row]
        has_notes = "Nota 1" in header
        # formato decimal (fracao) se nenhuma celula de indicador tiver '%'
        decimal_fmt = "%" not in ";".join(raw)
        rec = {"ano": ano}
        if has_notes:
            # UF;Ind1;Nota1;Ind2;Nota2;Ind3;Nota3;Classificacao;...
            rec["ind1"] = parse_pct(raw[1], decimal_fmt); rec["nota1"] = raw[2]
            rec["ind2"] = parse_pct(raw[3], decimal_fmt); rec["nota2"] = raw[4]
            rec["ind3"] = parse_pct(raw[5], decimal_fmt); rec["nota3"] = raw[6]
            rec["capag"] = raw[7]
        else:
            # 2018: UF;Ind1;Ind2;Ind3;Classificacao
            rec["ind1"] = parse_pct(raw[1], decimal_fmt); rec["nota1"] = None
            rec["ind2"] = parse_pct(raw[2], decimal_fmt); rec["nota2"] = None
            rec["ind3"] = parse_pct(raw[3], decimal_fmt); rec["nota3"] = None
            rec["capag"] = raw[4]
        rec["capag"] = re.sub(r"\*.*$", "", rec["capag"]).strip()
        # infere notas ausentes (arquivo 2018) pelos limites da metodologia STN
        if rec["nota1"] in (None, ""):
            rec["nota1"] = "A" if rec["ind1"] < 60 else ("B" if rec["ind1"] <= 150 else "C")
            rec["nota1_inferida"] = True
        if rec["nota2"] in (None, ""):
            rec["nota2"] = "A" if rec["ind2"] < 90 else ("B" if rec["ind2"] <= 95 else "C")
            rec["nota2_inferida"] = True
        if rec["nota3"] in (None, ""):
            rec["nota3"] = "A" if rec["ind3"] < 100 else "C"
            rec["nota3_inferida"] = True
        series[ano] = rec
    data = [series[a] for a in sorted(series)]
    json.dump(data, open(os.path.join(OUT, CAPAG_JSON), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("ano | CAPAG | Ind1(End) N1 | Ind2(Poup) N2 | Ind3(Liq) N3")
    for r in data:
        print(f"{r['ano']} |  {r['capag']:3} | {r['ind1']:7.2f} {r['nota1']} | "
              f"{r['ind2']:6.2f} {r['nota2']} | {r['ind3']:8.2f} {r['nota3']}")

if __name__ == "__main__":
    main()
