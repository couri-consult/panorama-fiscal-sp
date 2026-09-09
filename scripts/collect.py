"""Coleta dados fiscais de SP (id_ente=35) da API SICONFI, 2017-2026.
Salva JSON bruto em data/raw/ e imprime um resumo do que foi obtido."""
import requests, json, os, time, sys

BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ID = int(os.environ.get("ENTE", "35"))
DATADIR = os.environ.get("DATADIR", os.path.dirname(__file__))
RAW = os.path.join(DATADIR, "raw")
os.makedirs(RAW, exist_ok=True)

ANOS = list(range(2017, 2027))

def get(endpoint, **params):
    for attempt in range(4):
        try:
            r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=180)
            if r.status_code == 200:
                return r.json().get("items", [])
            time.sleep(2)
        except Exception as e:
            print(f"   ! erro {endpoint} {params.get('an_exercicio')} {params.get('no_anexo')}: {e}")
            time.sleep(3)
    return []

def collect_rreo(ano, anexo):
    """RREO bimestral: tenta periodo 6..1, usa o maior disponivel."""
    for per in range(6, 0, -1):
        items = get("rreo", an_exercicio=ano, nr_periodo=per,
                    co_tipo_demonstrativo="RREO", no_anexo=anexo,
                    co_esfera="E", id_ente=ID)
        if items:
            return per, items
    return None, []

def collect_rgf(ano, anexo):
    """RGF quadrimestral (Executivo): tenta periodo 3..1."""
    for per in range(3, 0, -1):
        items = get("rgf", an_exercicio=ano, in_periodicidade="Q", nr_periodo=per,
                    co_tipo_demonstrativo="RGF", no_anexo=anexo,
                    co_poder="E", co_esfera="E", id_ente=ID)
        if items:
            return per, items
    return None, []

RREO_ANEXOS = ["RREO-Anexo 01", "RREO-Anexo 03", "RREO-Anexo 06"]
RGF_ANEXOS  = ["RGF-Anexo 01", "RGF-Anexo 02", "RGF-Anexo 03", "RGF-Anexo 04", "RGF-Anexo 05"]

def main():
    manifest = {}
    for ano in ANOS:
        manifest[ano] = {}
        print(f"\n=== {ano} ===")
        for anexo in RREO_ANEXOS:
            per, items = collect_rreo(ano, anexo)
            tag = anexo.replace("RREO-Anexo ", "rreo").replace(" ", "")
            fn = os.path.join(RAW, f"{ano}_{tag}.json")
            json.dump(items, open(fn, "w", encoding="utf-8"), ensure_ascii=False)
            manifest[ano][anexo] = {"periodo": per, "n": len(items)}
            print(f"  {anexo}: periodo={per} n={len(items)}")
        for anexo in RGF_ANEXOS:
            per, items = collect_rgf(ano, anexo)
            tag = anexo.replace("RGF-Anexo ", "rgf").replace(" ", "")
            fn = os.path.join(RAW, f"{ano}_{tag}.json")
            json.dump(items, open(fn, "w", encoding="utf-8"), ensure_ascii=False)
            manifest[ano][anexo] = {"periodo": per, "n": len(items)}
            print(f"  {anexo}: periodo={per} n={len(items)}")
    json.dump(manifest, open(os.path.join(RAW, "_manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\nManifesto salvo.")

if __name__ == "__main__":
    main()
