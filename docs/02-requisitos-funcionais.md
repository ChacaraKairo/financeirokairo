# 2. Requisitos funcionais

## RF-01 — Cadastros básicos

O sistema deve permitir cadastrar, editar, arquivar e consultar:

- contas e carteiras;
- cartões;
- formas de pagamento;
- estabelecimentos;
- categorias e subcategorias;
- tags;
- marcas;
- produtos-base;
- variantes de produto;
- unidades e tipos de embalagem.

## RF-02 — Lançamentos financeiros

Deve registrar receitas, despesas e transferências com:

- data de competência e data de pagamento;
- descrição;
- valor;
- conta ou cartão;
- categoria;
- status previsto, pendente, pago ou cancelado;
- recorrência;
- parcelamento;
- observações e anexos.

## RF-03 — Compras detalhadas

Uma compra deve possuir cabeçalho e itens. Cada item pode conter:

- descrição original;
- produto-base;
- marca;
- variante;
- quantidade comprada;
- conteúdo da embalagem;
- unidade;
- preço unitário comercial;
- preço total;
- desconto;
- categoria sugerida e confirmada;
- confiança do reconhecimento.

## RF-04 — Comparação entre marcas

O sistema deve comparar marcas do mesmo produto-base considerando:

- preço pago;
- quantidade da embalagem;
- preço normalizado por unidade padrão;
- estabelecimento;
- data;
- promoção ou desconto;
- média, mínimo, máximo e mediana;
- evolução histórica.

Exemplo: comparar arroz de 1 kg e 5 kg somente após converter ambos para preço por quilograma.

## RF-05 — Importação JSON

O sistema deve:

1. selecionar um arquivo;
2. validar estrutura e tipos;
3. mostrar pré-visualização;
4. detectar possíveis duplicidades;
5. reconhecer produtos e marcas;
6. sugerir categorias;
7. destacar itens desconhecidos ou ambíguos;
8. permitir correções;
9. importar tudo em uma única transação de banco.

## RF-06 — Autocomplete

Campos de texto devem oferecer sugestões filtradas para produtos, marcas, categorias, estabelecimentos, contas e tags.

- busca sem diferenciar maiúsculas e acentos;
- correspondência pelo início ou por trecho;
- navegação por setas;
- confirmação com Enter;
- preenchimento com Tab;
- criação rápida quando nenhum resultado existir.

## RF-07 — Aprendizado local

Ao confirmar ou corrigir um item, o sistema deve registrar aliases e preferências para melhorar importações futuras.

## RF-08 — Filtros

Deve filtrar dados por:

- hoje, semana, mês, ano e intervalo personalizado;
- tipo de lançamento;
- status;
- conta ou cartão;
- categoria e subcategoria;
- produto-base, marca e variante;
- estabelecimento;
- faixa de valores;
- tags;
- texto livre.

## RF-09 — Relatórios

Deve gerar relatórios visuais e exportáveis por período, categoria, conta, produto, marca e estabelecimento.

## RF-10 — Backup e restauração

Deve gerar backup consistente do banco, anexos e configurações, validar sua integridade e permitir restauração controlada.

## Requisitos não funcionais

- Aplicação local e offline.
- Interface responsiva dentro do desktop.
- Consultas comuns em até aproximadamente 300 ms em base doméstica.
- Operações de importação atômicas.
- Testes automatizados para regras financeiras.
- Logs técnicos sem exposição indevida de dados.
- Compatibilidade inicial com Linux.