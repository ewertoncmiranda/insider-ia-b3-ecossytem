---
tipo: fundamentos
colecao: formulas
titulo: Perfil de operacao e riscos
origem: painel-ativos-frontend/public/js/pages/FormulasPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 34c3c72e60962504f7c44ff2343ba6e380fd9d2f409fd905021bb7c39e284af3
---

## Resumo

Pra qual tipo de operacao o ativo serve agora, e o risco de comprar/vender neste exato momento.

- **Fonte dos dados:** Derivado no Java a partir dos sinais acima - sem consulta nova

## Perfis aplicaveis (nao exclusivos)

Um ativo pode servir a mais de um perfil ao mesmo tempo.

- **Fórmula:** Day trade se sinal de momentum != neutro; Swing/reversao se sinal de reversao != neutro; Longo prazo se margem conservadora >=20% e earnings yield Atrativo/Razoavel
- **Situação:** implementado
- **Contextos de uso:** Day trade; Swing / reversão; Longo prazo

## Risco de comprar / vender agora

Separado em dois numeros - o risco de comprar nao e o inverso do risco de vender.

- **Fórmula:** risco de comprar: Alto se perto da maxima 52s e margem base =10%
- **Situação:** implementado
- **Contextos de uso:** Day trade; Swing / reversão; Longo prazo

## Confluencia de sinais

Quantos dos 3 sinais independentes (fundamentalista, momentum, reversao) apontam pro mesmo lado. E concordancia, nao e probabilidade de sucesso.

- **Fórmula:** contagem de sinais em COMPRA vs. VENDA vs. NEUTRO
- **Situação:** implementado
- **Contextos de uso:** Day trade; Swing / reversão; Longo prazo
