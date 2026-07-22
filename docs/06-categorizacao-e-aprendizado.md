# 6. Categorização e aprendizado local

## Objetivo

Reconhecer itens previamente classificados sem depender de serviços externos.

## Ordem de decisão

1. Código de barras exato.
2. Alias exato normalizado.
3. Variante exata por produto, marca e embalagem.
4. Regra personalizada do usuário.
5. Correspondência aproximada.
6. Palavras-chave.
7. Solicitação de revisão.

## Normalização

- converter para minúsculas;
- remover acentos e pontuação dispensável;
- reduzir espaços;
- padronizar unidades (`quilo`, `kg`, `kgs` → `kg`);
- separar números e unidades (`5kg` → `5 kg`);
- preservar termos relevantes de marca e variante.

## Faixas de confiança iniciais

- 0,95 a 1,00: preenchimento automático.
- 0,80 a 0,94: sugestão destacada para confirmação.
- abaixo de 0,80: revisão obrigatória.

Os limites devem ser configuráveis e calibrados por testes.

## Aprendizado por confirmação

Quando o usuário confirma uma sugestão:

- o texto original torna-se alias da variante;
- a associação produto/categoria ganha evidência;
- a marca e a embalagem confirmadas são preservadas;
- o histórico da decisão é registrado.

Quando o usuário corrige:

- a correção passa a ter prioridade;
- a sugestão errada não deve continuar sendo aplicada;
- a regra anterior pode ser rebaixada ou desativada.

## Ambiguidades

Termos genéricos, como `LEITE 1L`, não devem forçar uma marca. O sistema pode reconhecer o produto-base e a categoria, mantendo marca e variante como desconhecidas.

## Regras personalizadas

O usuário poderá criar regras como:

```text
Se descrição contém "UBER" → categoria Transporte / Aplicativos
Se produto-base é "Detergente" → categoria Casa / Limpeza
Se estabelecimento é "Farmácia X" e descrição contém "SHAMPOO" → Higiene pessoal
```

## Auditoria

Cada decisão automatizada deve registrar:

- método utilizado;
- confiança;
- resultado sugerido;
- resultado confirmado;
- data da confirmação.

## Evolução futura

Após existir volume suficiente de dados, poderá ser adicionado um classificador local. Ele deve complementar, e não substituir, regras determinísticas, aliases e revisão humana.