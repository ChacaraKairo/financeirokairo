# 14. Critérios de aceite do MVP

## 1. Objetivo

Este documento transforma o escopo do MVP em resultados verificáveis. Uma funcionalidade só integra a primeira versão quando os critérios correspondentes forem demonstrados e testados.

## 2. Inicialização e persistência

- A aplicação inicia em Linux sem depender de internet.
- Na primeira execução, cria ou seleciona um diretório de dados válido.
- O banco é criado e atualizado por migrações versionadas.
- O aplicativo recusa abrir uma base incompatível sem orientar o usuário.
- Após fechar e reabrir, todos os dados confirmados permanecem íntegros.

## 3. Contas e formas de pagamento

- O usuário cadastra, edita, arquiva e consulta contas.
- Cada conta possui nome, tipo, moeda, saldo inicial e estado.
- Contas arquivadas não aparecem por padrão em novos lançamentos.
- O saldo exibido corresponde ao saldo inicial somado aos movimentos válidos.
- Formas de pagamento podem ser reutilizadas em compras e transações.

## 4. Receitas, despesas e transferências

- O usuário registra receita ou despesa com data, valor, conta e categoria.
- Valores iguais a zero ou inválidos são rejeitados com mensagem clara.
- Uma transferência debita a conta de origem e credita a conta de destino atomicamente.
- Editar ou excluir logicamente uma transferência mantém os dois lados consistentes.
- Filtros por período, conta, categoria, tipo e texto retornam resultados corretos.

## 5. Categorias e etiquetas

- O usuário cria categorias e subcategorias sem ciclos hierárquicos.
- Categorias utilizadas podem ser arquivadas sem destruir o histórico.
- Uma transação pode possuir múltiplas etiquetas.
- Relatórios respeitam a hierarquia de categorias definida.

## 6. Compras detalhadas

- O usuário registra uma compra com estabelecimento, data, pagamento e itens.
- A soma dos itens, descontos e ajustes é conciliada com o total da compra.
- Divergências são destacadas antes da confirmação.
- Cada item preserva sua descrição original.
- Confirmar uma compra cria os registros financeiros e de preços na mesma transação.

## 7. Catálogo de produtos

- O usuário cadastra produto-base, marca e variante separadamente.
- A variante define quantidade, unidade e embalagem quando aplicável.
- Código de barras informado não pode ser duplicado.
- Produtos equivalentes podem ser comparados por unidade-base.
- Marca desconhecida permanece desconhecida até confirmação; não é inventada pelo sistema.

## 8. Importação JSON

- Arquivos válidos são validados conforme versão de contrato.
- Arquivos inválidos apresentam erros associados aos campos ou linhas correspondentes.
- A importação possui pré-visualização antes de persistir dados definitivos.
- O usuário pode corrigir correspondências, categorias e valores antes da confirmação.
- O mesmo arquivo não pode ser importado novamente sem alerta explícito.
- Cancelar ou falhar não deixa compra parcial no banco.
- O lote confirmado registra origem, hash, data e resultado.

## 9. Reconhecimento e aprendizado

- Código de barras confirmado tem prioridade sobre correspondência textual.
- Alias exato confirmado tem prioridade sobre busca fuzzy.
- Sugestões exibem nível de confiança e candidato correspondente.
- Unidades incompatíveis impedem confirmação automática.
- Correções do usuário podem criar ou atualizar aliases auditáveis.
- O usuário pode desfazer uma regra aprendida sem alterar compras históricas confirmadas.

## 10. Histórico e comparação de preços

- Cada item confirmado gera ou referencia uma observação de preço.
- O sistema calcula preço líquido por unidade-base com regra de arredondamento definida.
- O usuário compara variantes equivalentes por estabelecimento e período.
- Promoções e descontos são diferenciados do preço bruto quando os dados existirem.
- O histórico mantém o valor originalmente pago e o valor normalizado.

## 11. Orçamentos e metas

- O usuário define orçamento por período e categoria.
- O realizado considera apenas transações válidas dentro do período.
- O sistema mostra valor planejado, realizado, restante e percentual utilizado.
- O usuário cria meta financeira com valor-alvo e prazo opcional.
- Alterações de transações atualizam os indicadores correspondentes.

## 12. Dashboard e relatórios

- O dashboard mostra saldo consolidado, receitas, despesas e resultado do período.
- Indicadores respeitam filtros de período e contas selecionadas.
- Os números apresentados no dashboard coincidem com os relatórios detalhados.
- O usuário exporta ao menos relatórios essenciais em CSV e PDF.
- Relatórios vazios apresentam estado informativo, não erro técnico.

## 13. Backup e restauração

- O usuário cria backup manual sem fechar abruptamente a aplicação.
- Backups automáticos seguem uma política configurável.
- O arquivo gerado passa por verificação de integridade.
- Antes da restauração, o sistema valida versão e integridade da base escolhida.
- A base atual é preservada antes de ser substituída.
- Após restaurar, saldos, compras, catálogo e configurações correspondem ao backup.

## 14. Interface e tratamento de erros

- Fluxos principais são utilizáveis por teclado e mouse.
- Campos obrigatórios são identificados antes da gravação.
- Mensagens explicam o problema e a ação corretiva esperada.
- Operações demoradas não congelam permanentemente a janela.
- Ações destrutivas relevantes exigem confirmação.
- Tema claro e escuro mantêm contraste e legibilidade adequados.

## 15. Qualidade técnica

- Testes unitários e de integração críticos passam.
- Migrações são testadas em base vazia e na versão anterior.
- Lint, formatação e análise estática passam.
- Nenhum widget executa SQL diretamente.
- Logs não expõem dados sensíveis desnecessários.
- O pacote é validado em ambiente Linux limpo.
- A documentação correspondente está atualizada.

## 16. Cenário mínimo de demonstração

O MVP deve concluir, sem manipulação manual do banco, o seguinte fluxo:

1. criar duas contas;
2. cadastrar categorias;
3. registrar receita e despesa;
4. transferir valor entre contas;
5. importar uma compra JSON com vários itens;
6. revisar e confirmar produtos sugeridos;
7. consultar preço normalizado de um produto;
8. visualizar orçamento e dashboard atualizados;
9. exportar um relatório;
10. criar backup, alterar dados e restaurar o estado anterior.

A execução bem-sucedida desse cenário é necessária, mas não substitui os demais testes e critérios deste documento.