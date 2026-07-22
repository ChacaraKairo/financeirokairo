# 1. Visão geral

## Problema

Planilhas financeiras oferecem flexibilidade, mas exigem preenchimento manual, repetem informações e dificultam análises históricas detalhadas. O Financeiro Kairo pretende manter a flexibilidade das planilhas com automação, consistência e navegação simples.

## Público e contexto

Aplicação desktop de uso pessoal e familiar, executada inicialmente em Linux e operando offline.

## Princípios

1. Simples na interface, robusto internamente.
2. Dados pertencem ao usuário e permanecem locais por padrão.
3. Toda automação deve ser revisável e corrigível.
4. O sistema aprende com confirmações anteriores sem esconder suas decisões.
5. Valores monetários nunca usam ponto flutuante binário.
6. Produto, marca, variante e preço são conceitos separados.

## Escopo funcional

- Dashboard financeiro.
- Contas, carteiras, cartões e formas de pagamento.
- Receitas, despesas, transferências, recorrências e parcelamentos.
- Categorias, subcategorias, tags e centros de custo.
- Compras com detalhamento por item.
- Cadastro de produtos, marcas, variantes, unidades e embalagens.
- Importação JSON com validação e pré-visualização.
- Reconhecimento de itens conhecidos e sugestões de categoria.
- Histórico e comparação de preços.
- Orçamentos, metas e projeções.
- Relatórios e exportações.
- Backup, restauração e auditoria.

## Fora do MVP

- Sincronização em nuvem.
- Aplicativo móvel.
- Integração bancária automática.
- Leitura automática de NFC-e ou OCR.
- Inteligência artificial externa.

Esses recursos poderão ser adicionados após a base local estar estável.

## Indicadores de sucesso

- Registrar uma despesa simples em poucos segundos.
- Importar uma compra completa sem duplicar dados.
- Categorizar automaticamente itens já conhecidos.
- Comparar o preço unitário de marcas diferentes.
- Encontrar qualquer gasto por período, categoria, produto, marca ou estabelecimento.
- Restaurar o sistema integralmente a partir de um backup.