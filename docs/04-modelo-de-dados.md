# 4. Modelo de dados

## Conceitos do catálogo

### Produto-base

Representa o conceito comparável: arroz, leite, detergente, café, papel higiênico.

### Marca

Fabricante ou marca comercial: Camil, Tio João, Italac, Ypê.

### Variante

Combinação comercial específica de produto-base e marca, com atributos próprios.

Exemplo:

- produto-base: Leite
- marca: Italac
- descrição: Leite integral UHT
- conteúdo: 1
- unidade: litro
- embalagem: caixa

### Alias

Descrição alternativa encontrada em notas, arquivos ou preenchimentos anteriores.

## Entidades principais

### categories

- id
- parent_id
- name
- normalized_name
- color
- icon
- active

### brands

- id
- name
- normalized_name
- manufacturer
- active

### base_products

- id
- name
- normalized_name
- category_id
- standard_unit_id
- active

### product_variants

- id
- base_product_id
- brand_id
- name
- normalized_name
- package_type_id
- package_quantity
- unit_id
- barcode
- active

### product_aliases

- id
- product_variant_id
- original_text
- normalized_text
- source
- confidence
- confirmed

### merchants

- id
- name
- normalized_name
- document
- city
- active

### purchases

- id
- purchased_at
- merchant_id
- account_id
- payment_method_id
- total_amount_cents
- discount_amount_cents
- source_type
- source_hash
- notes

### purchase_items

- id
- purchase_id
- product_variant_id
- original_description
- quantity
- unit_price_cents
- total_price_cents
- discount_cents
- category_id
- category_confidence
- category_confirmed

### price_observations

Pode ser derivada de itens de compra ou persistida para consultas otimizadas.

- id
- purchase_item_id
- product_variant_id
- merchant_id
- observed_at
- paid_price_cents
- purchased_units
- normalized_quantity
- normalized_unit_id
- normalized_price_cents
- promotion

## Modelo financeiro

Entidades adicionais:

- accounts
- cards
- payment_methods
- transactions
- transaction_installments
- recurrence_rules
- budgets
- goals
- tags
- transaction_tags
- attachments
- settings
- audit_logs

## Regra de preço normalizado

```text
preço normalizado = preço líquido ÷ quantidade normalizada
```

Exemplos:

- Arroz 5 kg por R$ 29,90 → R$ 5,98/kg.
- Arroz 1 kg por R$ 6,49 → R$ 6,49/kg.
- Leite 12 caixas de 1 L por R$ 59,88 → R$ 4,99/L.

## Regras de integridade

- Marca pode ser desconhecida, mas nunca deve ser inventada.
- Produto-base deve possuir unidade padrão comparável.
- Variante deve apontar para um produto-base.
- Código de barras, quando informado, deve ser único.
- Alias normalizado deve ser indexado.
- Uma compra importada deve possuir `source_hash` para detectar duplicidade.
- Exclusão lógica deve ser preferida para cadastros já utilizados.

## Índices recomendados

- `brands(normalized_name)`
- `base_products(normalized_name)`
- `product_variants(base_product_id, brand_id)`
- `product_aliases(normalized_text)`
- `purchases(purchased_at)`
- `purchase_items(product_variant_id)`
- `price_observations(product_variant_id, observed_at)`
- `price_observations(merchant_id, observed_at)`