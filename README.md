# Panorama Fiscal do Estado de São Paulo

Painel de indicadores fiscais do estado de **São Paulo** (2017–2026), a partir de **dados
abertos oficiais**: **SICONFI/Tesouro Nacional** (RREO + RGF + DCA, `id_ente=35`), os relatórios
de **CAPAG** da STN e o **IPCA** (BCB) para deflacionar.

`index.html` é uma página estática e **autocontida** — dados, CSS e o motor de gráficos (SVG
próprio, sem bibliotecas nem CDN) estão embutidos no arquivo. Abre por duplo-clique ou servido
por HTTP.

**🔗 Painel no ar:** https://couri-consult.github.io/panorama-fiscal-sp/

## Destaques (São Paulo)

- **Desalavancagem**: a Dívida Consolidada Líquida caiu de ~171% da RCL (2017) para ~124%
  (2025) — puxada pelo crescimento da RCL, não por quitação de dívida.
- **Pessoal sob controle**: ~41% da RCL, abaixo do limite de alerta (44,1%) da LRF.
- **Superávits primários** em toda a série; forte pico em 2021.
- **Rigidez estrutural**: despesa corrente ~90% da receita corrente; investimento direto em
  queda real, com migração para capitalização de estatais e PPP.

## Estrutura do repositório

```
panorama-fiscal-sp/
├── index.html          # o painel (autocontido)
├── capag/              # CSVs anuais da CAPAG (Tesouro), 2018–2025
└── scripts/            # pipeline de atualização
    ├── build.py        # orquestra coleta + deflator e reembute os dados no index.html
    ├── collect.py      # baixa RREO/RGF do SICONFI (parametrizado por ente)
    ├── process.py      # consolida o dataset fiscal
    ├── capag.py        # extrai a série da CAPAG do estado
    ├── deflate.py      # deflaciona pelo IPCA (BCB SGS 433) e decompõe a dívida/RCL
    ├── inversoes.py    # detalha inversões financeiras por elemento (DCA-Anexo I-D)
    └── comparar_paineis.py  # verifica se o "motor" está sincronizado com o painel do PI
```

O `index.html` **não depende** de nenhum outro arquivo em runtime — é autossuficiente. Os
scripts servem só para **regerar** os dados nele embutidos.

## Atualizar os dados

```bash
pip install requests
python scripts/build.py                 # coleta SICONFI + IPCA, deflaciona e reembute no index.html
git commit -am "atualiza dados" && git push
```

O GitHub Pages republica ~30–90s após o push (branch `main`, raiz `/`). Force reload com
`Ctrl+Shift+R`. Frequência das fontes: RREO é bimestral, RGF é quadrimestral, IPCA é mensal,
CAPAG é anual.

## Sincronia com o painel do Piauí

Este painel e o de **[Piauí](https://github.com/couri-consult/panorama-fiscal-pi)** compartilham
o mesmo **motor** — o CSS e as funções de gráfico em JS são idênticos; só mudam os **dados** e a
**narrativa** (textos, números e fontes de cada estado). O mesmo vale para o pipeline em
`scripts/` (difere apenas nos parâmetros do ente, no topo de cada arquivo).

Para não deixarem divergir sem querer, rode antes de publicar mudanças no motor:

```bash
python scripts/comparar_paineis.py      # assume os dois repos lado a lado em projetos/
```

Ele extrai o motor dos dois `index.html` e avisa: *"motor IDÊNTICO ✅"* ou lista exatamente o que
divergiu (para você decidir se é motor — replicar no outro — ou conteúdo específico do estado).

## Fontes

- **SICONFI / Tesouro Nacional** — https://apidatalake.tesouro.gov.br/docs/siconfi/
- **CAPAG / Tesouro Transparente** — https://www.tesourotransparente.gov.br/temas/estados-e-municipios/capacidade-de-pagamento-capag
- **IPCA** — Banco Central do Brasil, série SGS 433

Cifras em reais correntes (salvo séries deflacionadas, marcadas "base 2025"); dados parciais de
2026 sinalizados no painel.
