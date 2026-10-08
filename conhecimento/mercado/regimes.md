---
tipo: mercado
documento: regimes
disponivel_ate: 2025-12-31
fonte: [cotacao_b3_diaria, evento_corporativo, indice_macro, fator_mercado_mensal]
gerado_em: 2026-10-07
hash: f14b627584e6698cb9049b97892d55accf9683d6a34938f585365961d0abec07
---

## Resumo

Episódios de mercado com janelas fixas (definidas antes de olhar o resultado) e como a média igual-peso dos papéis líquidos e os fatores momentum (WML) e valor (HML) se comportaram.

## Regimes

| Regime | Janela | Pregões | Mercado | Queda máx. | Vol. | Selic fim | WML | HML |
|---|---|---|---|---|---|---|---|---|
| Recessão 2015–16 | 01/2015–12/2016 | 495 | -5,1% | -42% | 20% | 13,75% | -12,8% | +5,7% |
| Rali eleitoral 2018 | 08/2018–10/2018 | 64 | +11,7% | -9% | 20% | 6,50% | -7,1% | +15,1% |
| Covid: queda | 02/2020–03/2020 | 21 | -50,5% | -51% | 113% | 3,75% | — | — |
| Covid: recuperação | 03/2020–12/2020 | 193 | +96,5% | -15% | 34% | 2,00% | +12,2% | +6,8% |
| Rali eleitoral 2022 | 08/2022–10/2022 | 64 | +14,9% | -7% | 26% | 13,75% | -10,6% | +14,8% |
| Juros altos 2022–24 | 01/2022–12/2024 | 749 | -29,6% | -35% | 24% | 12,25% | -74,3% | +167,7% |

## Definições

- **Recessão 2015–16**: PIB caiu dois anos seguidos; Selic chegou a 14,25%.
- **Rali eleitoral 2018**: Agosto a outubro de ano de eleição presidencial.
- **Covid: queda**: Do pico de fevereiro ao fundo de março de 2020.
- **Covid: recuperação**: Do fundo de março ao fim de 2020.
- **Rali eleitoral 2022**: Agosto a outubro de ano de eleição presidencial.
- **Juros altos 2022–24**: Selic em dois dígitos na maior parte do período.

## Limitações

- Janelas de calendário, não detectadas pelos dados; regime futuro não precisa repetir.
- Selic só a partir de 2016; WML/HML desde 2010 (fator_mercado_mensal).
- Rali eleitoral de 2026 fica fora (ano corrente).
- 2 mês(es) de WML/HML acima de 100% em módulo ficaram fora (evento corporativo não inferido).
