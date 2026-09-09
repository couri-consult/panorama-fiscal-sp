import json, os, sys
RAW = os.path.join(os.path.dirname(__file__), "raw")

def load(ano, tag):
    return json.load(open(os.path.join(RAW, f"{ano}_{tag}.json"), encoding="utf-8"))

def show(ano, tag, filt=None):
    items = load(ano, tag)
    cols = list(dict.fromkeys(i['coluna'] for i in items))
    rots = list(dict.fromkeys(i.get('rotulo','') for i in items))
    print(f"\n### {ano} {tag}: {len(items)} items")
    print("COLUNAS:", cols)
    print("ROTULOS:", rots)
    seen=set()
    for i in items:
        k=i['cod_conta']
        if filt and filt.lower() not in (k+i['conta']).lower(): continue
        key=(k,i.get('rotulo',''))
        if key in seen: continue
        seen.add(key)
        print(f"  [{i.get('rotulo','')}] {k} :: {i['conta'][:45]}")

if __name__=="__main__":
    args=sys.argv[1:]
    show(int(args[0]), args[1], args[2] if len(args)>2 else None)
