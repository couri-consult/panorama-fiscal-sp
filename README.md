# Panorama Fiscal do Estado de São Paulo

Painel de indicadores fiscais do estado de **São Paulo** (2017–2026), construído a partir de
**dados abertos oficiais**: o **SICONFI/Tesouro Nacional** (RREO + RGF + DCA, `id_ente=35`),
os relatórios de **CAPAG** da STN e o **IPCA** (BCB) para deflacionar.

`panorama_fiscal_sp.html` é uma página estática e **autocontida** — dados, CSS e o motor de
gráficos (SVG próprio, sem bibliotecas nem CDN) estão embutidos no arquivo. Abre por
duplo-clique ou servido por HTTP.

## Destaques (São Paulo)

- **Desalavancagem**: a Dívida Consolidada Líquida caiu de ~171% da RCL (2017) para ~124%
  (2025) — puxada pelo crescimento da RCL, não por quitação de dívida.
- **Pessoal sob controle**: ~41% da RCL, abaixo do limite de alerta (44,1%) da LRF.
- **Superávits primários** em toda a série; forte pico em 2021.
- **Rigidez estrutural**: despesa corrente ~90% da receita corrente; investimento direto
  em queda real, com migração para capitalização de estatais e PPP.

## Estrutura

```
panorama-fiscal-sp/
├── panorama_fiscal_sp.html   # o painel (autocontido)
├── capag/                    # CSVs anuais da CAPAG (Tesouro), 2018–2025
└── data/                     # pipeline + datasets processados
    ├── collect.py            # baixa RREO/RGF do SICONFI (parametrizado por ente) → raw/
    ├── process.py            # consolida o dataset fiscal
    ├── capag.py              # extrai a série da CAPAG do estado
    ├── deflate.py            # deflaciona pelo IPCA (BCB SGS 433) e decompõe a dívida/RCL
    ├── inversoes.py          # detalha inversões financeiras por elemento (DCA-Anexo I-D)
    ├── explore.py, inspect.py# utilitários de inspeção da API
    ├── fiscal_sp.csv/.json   # dataset consolidado
    └── *.json                # séries processadas (CAPAG, análise real, etc.)
```

Os dumps brutos do SICONFI (`data/raw/`) não são versionados — são regeneráveis pelos scripts.

## Regenerar os dados

```bash
pip install requests
cd data
python collect.py     # baixa SICONFI para data/raw/  (ente 35 = SP, padrão)
python process.py     # gera fiscal_sp.json/.csv
python capag.py       # gera capag_sp.json  (lê ../capag/)
python deflate.py     # gera analysis_real.json (deflator IPCA)
python inversoes.py   # gera inversoes_series.json (DCA)
```

O pipeline é parametrizado por ente via variáveis de ambiente (`ENTE`, `UF`, `DATADIR`), o que
permite gerar o painel de qualquer UF a partir das mesmas fontes.

## Fontes

- **SICONFI / Tesouro Nacional** — https://apidatalake.tesouro.gov.br/docs/siconfi/
- **CAPAG / Tesouro Transparente** — https://www.tesourotransparente.gov.br/temas/estados-e-municipios/capacidade-de-pagamento-capag
- **IPCA** — Banco Central do Brasil, série SGS 433

Cifras em reais correntes (salvo séries deflacionadas, marcadas "base 2025"); dados parciais de
2026 sinalizados no painel.
