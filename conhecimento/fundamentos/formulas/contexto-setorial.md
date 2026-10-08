---
tipo: fundamentos
colecao: formulas
titulo: Contexto setorial
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 1622b1a018907c46d91579fc56b45388fb17f099d56e570fa9332179898156bd
---

## Resumo

Comparar multiplos do ativo contra o proprio setor, em vez de contra limiares fixos e iguais pra qualquer empresa.

- **Fonte dos dados:** BRAPI /v2/stocks/profile - confirmado gratis pra qualquer ticker (validado em 2026-09-25 com WEGE3)

## Setor, industria e resumo do negocio

Buscado ao vivo no Java (ServicoAtivo.buscarPerfilEmpresa) e anexado a resposta de /fundamentos - degrada pra null se a BRAPI falhar, sem quebrar o resto da resposta.

- **Fórmula:** campo direto: profile.sector / profile.industry / profile.longBusinessSummary
- **Situação:** implementado
- **Contextos de uso:** Comparação setorial

## P/L e earnings yield relativos ao setor

Em vez de "Atrativo >=12%" fixo pra qualquer ativo, comparar contra a media do earnings yield dos outros ativos monitorados do mesmo setor.

- **Fórmula:** earnings yield relativo = earnings yield do ativo - media do earnings yield do setor (entre os ativos monitorados)
- **Situação:** proposta
- **Contextos de uso:** Comparação setorial; Longo prazo
