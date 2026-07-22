# 11. Requisitos não funcionais

## 1. Objetivo

Este documento estabelece atributos de qualidade mensuráveis para o Financeiro Kairo. Eles complementam os requisitos funcionais e servem como critérios para decisões técnicas, testes e aceite de versões.

## 2. Plataforma e operação

- A primeira versão deve executar em distribuições Linux desktop atuais.
- O sistema deve funcionar sem conexão com a internet.
- A ausência de rede não pode impedir cadastro, consulta, importação local, relatórios ou backup.
- O banco principal e os anexos devem ficar em diretórios configuráveis pelo usuário.
- O aplicativo deve identificar claramente o caminho do banco ativo e do diretório de backups.

## 3. Desempenho

Metas iniciais em hardware doméstico intermediário:

- abertura da aplicação em até 5 segundos para uma base de referência;
- resposta visual a ações comuns em até 300 ms;
- filtros e buscas comuns em até 1 segundo com 100 mil transações;
- abertura paginada de tabelas sem carregar todos os registros na memória;
- importação de 1.000 itens em até 10 segundos, excluindo revisão humana;
- geração de relatório mensal comum em até 5 segundos;
- operações demoradas devem exibir progresso e permitir cancelamento quando seguro.

As metas devem ser medidas em ambiente de teste documentado antes de cada versão estável.

## 4. Confiabilidade e integridade

- Operações financeiras compostas devem ser atômicas.
- Transferências devem criar os dois lados do movimento na mesma transação de banco.
- Falhas de importação não podem deixar registros definitivos parciais.
- Chaves estrangeiras do SQLite devem estar habilitadas em toda conexão.
- O sistema deve detectar tentativas de importação duplicada por hash e metadados de origem.
- Exclusões de registros já utilizados devem ser lógicas quando a remoção física comprometer histórico.
- Migrações devem ser versionadas, testáveis e reversíveis quando tecnicamente viável.

## 5. Segurança e privacidade

- Dados financeiros não devem ser enviados para serviços externos sem consentimento explícito.
- Logs não devem registrar senhas, conteúdo integral de documentos, números completos de cartão ou dados financeiros desnecessários.
- Arquivos temporários sensíveis devem ser removidos após o uso.
- Backups devem poder ser armazenados em local escolhido pelo usuário.
- Criptografia do banco pode ser adicionada como recurso opcional, sem substituir boas práticas de backup.
- Qualquer integração futura deve documentar dados enviados, finalidade, retenção e forma de revogação.

## 6. Backup e recuperação

- Deve existir backup manual e automático.
- Backups devem ser criados por mecanismo seguro para banco em uso, preferencialmente API de backup do SQLite ou `VACUUM INTO`.
- Cada backup deve registrar data, versão do esquema, tamanho e resultado da verificação.
- A restauração deve validar o arquivo antes de substituir a base ativa.
- O sistema deve manter política rotativa configurável; sugestão inicial: 7 diários, 4 semanais e 12 mensais.
- O fluxo de restauração deve preservar uma cópia de segurança da base substituída.

## 7. Usabilidade e acessibilidade

- Fluxos frequentes devem ser executáveis por teclado.
- Campos devem ter rótulos explícitos e ordem de foco previsível.
- Erros devem informar o que ocorreu e como corrigir, sem expor detalhes internos desnecessários.
- A interface deve oferecer tema claro e escuro.
- Cores não podem ser o único meio de indicar estado, categoria ou erro.
- Tabelas devem permitir ordenação, filtros, navegação e leitura de detalhes sem perda de contexto.
- Ações destrutivas devem exigir confirmação proporcional ao impacto.

## 8. Manutenibilidade

- A camada de apresentação não deve acessar SQL diretamente.
- Casos de uso devem depender de interfaces de repositório, não de implementações concretas.
- Regras de domínio devem ser testáveis sem iniciar a interface gráfica.
- Código público deve possuir tipagem estática suficiente para análise pelo `mypy` ou ferramenta equivalente.
- Formatação e lint devem ser automatizados.
- Toda alteração de esquema deve incluir migração e teste correspondente.
- Dependências devem ser fixadas de maneira reproduzível.

## 9. Testabilidade

A suíte deve incluir:

- testes unitários para dinheiro, quantidades, recorrências, parcelamentos e normalização de preços;
- testes de integração para repositórios, transações e migrações;
- testes de contrato para formatos importados;
- testes de regressão para duplicidade e reconhecimento;
- testes de interface para fluxos críticos;
- teste periódico de backup e restauração.

A meta de cobertura não substitui análise de risco. Módulos financeiros, migrações, importação e backup exigem cobertura mais rigorosa.

## 10. Observabilidade

- Logs devem usar níveis consistentes: debug, info, warning, error e critical.
- Cada importação deve possuir identificador de correlação.
- Erros inesperados devem registrar contexto técnico suficiente para diagnóstico.
- A interface deve apresentar mensagem amigável e oferecer acesso ao arquivo de log quando apropriado.
- Eventos de auditoria devem ser separados de logs técnicos.

## 11. Compatibilidade e evolução

- A leitura de bancos antigos deve ocorrer somente após migração controlada.
- Formatos de exportação devem declarar versão quando puderem ser reimportados.
- Mudanças incompatíveis em JSON devem gerar nova versão de contrato.
- O sistema deve permitir adicionar novos importadores e exportadores sem alterar regras centrais do domínio.

## 12. Critério de avaliação

Um requisito não funcional somente é considerado atendido quando existe ao menos uma evidência verificável: teste automatizado, medição reproduzível, inspeção de arquitetura, checklist de release ou demonstração documentada.