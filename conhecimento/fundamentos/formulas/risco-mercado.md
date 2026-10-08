---
tipo: fundamentos
colecao: formulas
titulo: Risco relativo ao mercado (proposta)
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 9e498e3b93eba59e0fc3623d6d6416269affb48bcd31d73d720c5d22c14f5627
---

## Resumo

Quao volatil o ativo e, isolado e comparado ao Ibovespa - hoje o painel nao distingue uma recomendacao estavel de uma extremamente arriscada.

- **Fonte dos dados:** BRAPI /historical do ativo + do indice ^BVSP - ambos gratis, limitados a 3 meses

## Volatilidade historica

Desvio-padrao dos retornos diarios dos candles ja coletados em serie_historica. Nao exige nova coleta.

- **Fórmula:** volatilidade = desvio-padrao(retorno diario); retorno diario = (fechamento[i] - fechamento[i-1]) / fechamento[i-1]
- **Situação:** proposta
- **Contextos de uso:** Day trade; Swing / reversão; Longo prazo

## Beta vs. Ibovespa

O quanto o ativo amplifica ou amortece o movimento do indice. Precisa coletar a serie do ^BVSP no mesmo range ja usado pros ativos monitorados.

- **Fórmula:** beta = covariancia(retorno do ativo, retorno do Ibovespa) / variancia(retorno do Ibovespa)
- **Situação:** proposta
- **Contextos de uso:** Longo prazo; Comparação setorial

## Persistencia do sinal

Quantos ciclos consecutivos a recomendacao se mantem no mesmo sentido. Nao mede se a recomendacao "deu certo" - so mede estabilidade do sinal atual.

- **Fórmula:** contagem de analises consecutivas do simbolo com a mesma recomendacao, do mais recente pra tras
- **Situação:** proposta
- **Contextos de uso:** Day trade; Swing / reversão; Longo prazo
