---
tipo: fundamentos
colecao: formulas
titulo: Decisao consolidada (historico)
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 9af54f86a73528094bf1321996f7460768262ab5bf39490feb42199f79313884
---

## Resumo

A mesma logica de valuation acima, mas resumida sobre todo o historico de analises do ativo - nao um ciclo isolado.

- **Fonte dos dados:** Media de detalhes_json de todas as analises do simbolo

## Recomendacao, risco e confianca

Regras fixas sobre margem de seguranca media e earnings yield medio, mostradas em Consulta e na coluna "Decisao" de Monitorados.

- **Fórmula:** COMPRA_FORTE: margem conservadora >=20% e earnings yield >=12%; VENDA_VALUATION: margem base negativa; senao MANTER
- **Situação:** implementado
- **Contextos de uso:** Longo prazo
