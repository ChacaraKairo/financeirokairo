# 5. Importação JSON

## Objetivo

Permitir que compras detalhadas sejam importadas com segurança, reconhecendo itens conhecidos e solicitando revisão apenas quando necessário.

## Fluxo

1. Selecionar arquivo.
2. Ler UTF-8.
3. Validar JSON e versão do esquema.
4. Calcular hash do conteúdo.
5. Detectar possível duplicidade.
6. Normalizar textos e unidades.
7. Localizar estabelecimento, produto, marca e variante.
8. Sugerir categoria.
9. Exibir tela de revisão.
10. Confirmar e gravar atomicamente.

## Contrato inicial

```json
{
  "schema_version": "1.0",
  "purchase": {
    "date": "2026-07-22",
    "merchant": "Supermercado Exemplo",
    "payment_method": "credit_card",
    "account": "Cartão principal",
    "currency": "BRL",
    "total": "72.37",
    "items": []
  }
}
```

Valores monetários devem ser strings decimais para impedir perda de precisão.

## Item

```json
{
  "description": "ARROZ CAMIL TIPO 1 5KG",
  "base_product": "Arroz",
  "brand": "Camil",
  "variant": "Tipo 1",
  "package": {
    "quantity": "5",
    "unit": "kg",
    "type": "pacote"
  },
  "purchased_quantity": "1",
  "unit_price": "29.90",
  "discount": "0.00",
  "total": "29.90",
  "category": "Alimentação",
  "subcategory": "Mercearia",
  "barcode": null
}
```

Campos de catálogo são opcionais. Quando ausentes, o sistema tenta inferi-los e exige revisão quando a confiança for insuficiente.

## Validações

- `schema_version` suportada.
- data válida.
- moeda suportada.
- lista de itens não vazia.
- quantidades positivas.
- valores não negativos.
- soma dos itens compatível com o total dentro de tolerância configurável.
- unidades conhecidas ou marcadas para revisão.
- categoria existente ou candidata à criação.

## Duplicidade

A detecção combina:

- hash do arquivo;
- estabelecimento;
- data;
- total;
- quantidade de itens;
- descrições e valores.

O sistema deve alertar, nunca apagar ou substituir silenciosamente.

## Resultado da pré-visualização

Cada linha recebe um estado:

- Reconhecido.
- Sugestão de alta confiança.
- Revisão recomendada.
- Desconhecido.
- Inválido.

## Transação

Nenhum dado deve ser persistido antes da confirmação final. Uma falha em qualquer item cancela toda a importação.

## Compatibilidade futura

Novas versões do esquema deverão preservar leitura das versões anteriores por meio de adaptadores.