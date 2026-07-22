# 7. Interface e experiência de uso

## Navegação principal

- Dashboard
- Lançamentos
- Compras
- Contas e cartões
- Planejamento
- Relatórios
- Catálogo
- Configurações

## Dashboard

Exibir apenas os indicadores prioritários:

- saldo atual;
- receitas e despesas do período;
- resultado líquido;
- despesas por categoria;
- próximas contas;
- orçamento consumido;
- variação em relação ao período anterior.

## Tela de compras

A compra possui cabeçalho e grade de itens. A grade deve permitir edição por teclado, semelhante a uma planilha, sem perder validação.

Colunas recomendadas:

- descrição;
- produto;
- marca;
- variante;
- embalagem;
- quantidade;
- valor unitário;
- total;
- categoria;
- estado do reconhecimento.

## Autocomplete

Campos devem usar `QCompleter` ou componente equivalente com:

- filtro por trecho;
- busca sem acento;
- popup imediato após digitação;
- setas para navegação;
- Enter para selecionar;
- Tab para aceitar a melhor opção e avançar;
- Escape para fechar;
- opção `Criar novo...`.

Ao selecionar uma variante, o sistema pode preencher marca, produto-base, unidade, embalagem e categoria.

## Tela de revisão da importação

Deve mostrar:

- resumo da compra;
- inconsistências;
- duplicidade possível;
- tabela editável;
- confiança por item;
- filtro `mostrar somente itens pendentes`;
- ação para aplicar uma correção a itens semelhantes;
- confirmação final.

## Comparador de preços

O usuário seleciona um produto-base e visualiza:

- marcas e variantes;
- último preço;
- preço normalizado;
- menor preço histórico;
- média por período;
- estabelecimento;
- gráfico de evolução;
- filtros por embalagem, marca, mercado e intervalo.

## Simplicidade progressiva

Recursos avançados ficam em painéis expansíveis. O fluxo normal deve exigir poucos campos, enquanto detalhes permanecem disponíveis para quem precisar.

## Acessibilidade e consistência

- suporte integral ao teclado;
- foco visual claro;
- atalhos documentados;
- mensagens de erro próximas ao campo;
- confirmação para ações destrutivas;
- temas claro e escuro;
- números e datas no padrão brasileiro;
- contraste adequado;
- nenhuma informação dependente apenas de cor.

## Atalhos iniciais

- `Ctrl+N`: novo lançamento.
- `Ctrl+I`: importar compra.
- `Ctrl+F`: focar pesquisa.
- `Ctrl+S`: salvar.
- `Ctrl+Enter`: confirmar formulário.
- `Esc`: cancelar ou fechar diálogo.
- `F2`: editar célula selecionada.