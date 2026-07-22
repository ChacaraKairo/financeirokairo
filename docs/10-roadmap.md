# 10. Roadmap

## Fase 0 — Fundação

- Estrutura do projeto e ambiente Python.
- Configuração de qualidade, testes e logs.
- SQLite, SQLAlchemy e Alembic.
- Tipos de dinheiro, datas e quantidades.
- Tema visual e janela principal.

## Fase 1 — MVP financeiro

- Contas e formas de pagamento.
- Categorias e subcategorias.
- Receitas, despesas e transferências.
- Filtros por período e categoria.
- Dashboard mensal.
- Backup e restauração básicos.

## Fase 2 — Compras detalhadas

- Estabelecimentos.
- Produtos-base, marcas e variantes.
- Tela de compra em formato de grade.
- Autocomplete com Tab e popup filtrado.
- Histórico de preços.

## Fase 3 — Importação inteligente

- Contrato JSON 1.0.
- Validação com Pydantic.
- Pré-visualização e transação atômica.
- Aliases e correspondência exata.
- RapidFuzz e níveis de confiança.
- Aprendizado por confirmação.

## Fase 4 — Comparações e relatórios

- Preço normalizado por unidade.
- Comparador entre marcas.
- Gráficos por produto e estabelecimento.
- Relatórios PDF, XLSX e CSV.
- Indicadores de variação e economia.

## Fase 5 — Planejamento financeiro

- Orçamentos por categoria.
- Metas.
- Recorrências e parcelamentos.
- Projeções de fluxo de caixa.
- Alertas locais.

## Fase 6 — Robustez

- Auditoria.
- Anexos e comprovantes.
- Importação e exportação integral.
- Melhorias de acessibilidade.
- Testes de interface.
- Empacotamento para Linux.

## Evoluções posteriores

- XML de NFC-e.
- Leitura de código de barras.
- OCR de comprovantes.
- Aplicativo móvel.
- Sincronização opcional.
- Classificador local treinado com o histórico do usuário.

## Critérios para concluir cada fase

- requisitos implementados;
- migrações testadas;
- testes automatizados passando;
- documentação atualizada;
- fluxo manual validado;
- backup criado antes de mudança estrutural relevante.

## Ordem recomendada de implementação

A importação inteligente deve começar somente depois de catálogo e compras estarem estáveis. Relatórios avançados devem usar dados reais gerados pelas fases anteriores, evitando construir gráficos sobre um modelo ainda instável.