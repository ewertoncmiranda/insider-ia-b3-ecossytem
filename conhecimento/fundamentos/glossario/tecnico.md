---
tipo: fundamentos
colecao: glossario
titulo: Termos tecnicos deste sistema
origem: painel-ativos-frontend/public/js/pages/GlossarioPage.js
disponivel_ate: 2000-01-01
gerado_em: 2026-10-08
hash: 8e337cf95e50a3a228f8309acb477bee4699e450ce37082f7b52a663c8d14f6a
---

## Resumo

Vocabulario de engenharia que aparece nas telas e na documentacao.

## ETL

Buscar o dado na fonte, arrumar e gravar no banco. E o que o etl-fundamentos-cvm faz com os arquivos da CVM.

- **Sigla:** Extract, Transform, Load

## Landing e mart

Landing e o dado cru como veio; mart e o dado pronto para consumo. Guardar os dois permite recalcular sem baixar tudo de novo.

## De-para

A tabela de traducao entre o nome da conta na CVM e o nome do indicador aqui. E a peca mais delicada do sistema, porque o mesmo codigo de conta significa coisas diferentes em empresas diferentes.

## Plano de contas

O indice padronizado das contas contabeis. Banco, seguradora e industria usam planos diferentes - dai a complicacao.

- **Onde aparece no painel:** O campo "plano de contas" nos fundamentos diz qual foi detectado.

## Idempotencia

Rodar duas vezes produzir o mesmo resultado que rodar uma. Sem isso, reprocessar duplicaria dado.

## Upsert

Grava se nao existe, atualiza se ja existe. E o mecanismo que garante a idempotencia.

## ETag

Uma "impressao digital" que o servidor da CVM da a cada arquivo. Se nao mudou, nao precisamos baixar de novo.
