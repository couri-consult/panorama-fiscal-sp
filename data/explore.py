import requests, json, sys
from collections import OrderedDict

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ID = 35  # São Paulo

def fetch(endpoint, **params):
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=120)
    r.raise_for_status()
    return r.json().get("items", [])

def explore_rreo(anexo, ano=2023, per=6):
    items = fetch("rreo", an_exercicio=ano, nr_periodo=per,
                  co_tipo_demonstrativo="RREO", no_anexo=anexo,
                  co_esfera="E", id_ente=ID)
    print(f"\n########## RREO {anexo} ({ano}/{per}) -> {len(items)} items")
    cols = list(OrderedDict.fromkeys(i['coluna'] for i in items))
    print("COLUNAS:", cols)
    seen = OrderedDict()
    for i in items:
        k = i['cod_conta']
        if k not in seen:
            seen[k] = i['conta']
    for k, v in seen.items():
        print(f"  {k}  ::  {v}")

def explore_rgf(anexo, ano=2023, per=3, poder="E"):
    items = fetch("rgf", an_exercicio=ano, in_periodicidade="Q", nr_periodo=per,
                  co_tipo_demonstrativo="RGF", no_anexo=anexo,
                  co_poder=poder, co_esfera="E", id_ente=ID)
    print(f"\n########## RGF {anexo} ({ano}/{per} poder={poder}) -> {len(items)} items")
    cols = list(OrderedDict.fromkeys(i['coluna'] for i in items))
    print("COLUNAS:", cols)
    seen = OrderedDict()
    for i in items:
        k = i['cod_conta']
        if k not in seen:
            seen[k] = i['conta']
    for k, v in seen.items():
        print(f"  {k}  ::  {v}")

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("all", "rreo1"):
        explore_rreo("RREO-Anexo 01")
    if what in ("all", "rreo3"):
        explore_rreo("RREO-Anexo 03")
    if what in ("all", "rreo6"):
        explore_rreo("RREO-Anexo 06")
    if what in ("all", "rgf1"):
        explore_rgf("RGF-Anexo 01")
    if what in ("all", "rgf2"):
        explore_rgf("RGF-Anexo 02")
    if what in ("all", "rgf3"):
        explore_rgf("RGF-Anexo 03")
    if what in ("all", "rgf4"):
        explore_rgf("RGF-Anexo 04")
    if what in ("all", "rgf5"):
        explore_rgf("RGF-Anexo 05")
