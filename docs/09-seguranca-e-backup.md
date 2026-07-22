# 9. Segurança e backup

## Princípios

- Dados locais por padrão.
- Privilégio mínimo.
- Nenhuma senha, token ou dado sensível no repositório.
- Backups verificáveis antes de serem considerados válidos.
- Recuperação testada, não apenas geração de arquivo.

## Banco de dados

- SQLite com `PRAGMA foreign_keys = ON`.
- Modo WAL quando adequado.
- Transações atômicas.
- Migrações versionadas.
- Verificação de integridade com `PRAGMA integrity_check`.
- Cópia do banco somente por API de backup ou após checkpoint seguro.

## Valores e dados

- Dinheiro em centavos inteiros ou `Decimal`.
- Quantidades em `Decimal`.
- Datas em ISO 8601.
- Entradas JSON validadas por Pydantic.
- Tamanho máximo de importação configurável.
- Nomes de arquivos tratados como dados não confiáveis.

## Proteção local

Opcionalmente, o sistema poderá oferecer:

- bloqueio por senha local;
- criptografia do arquivo de backup;
- banco criptografado por tecnologia compatível;
- bloqueio automático após inatividade;
- ocultação de valores na interface.

Nunca deve ser criada criptografia própria.

## Backup

O pacote de backup deve incluir:

- banco de dados;
- anexos;
- configurações exportáveis;
- versão do esquema;
- manifesto com hashes;
- data e versão do aplicativo.

Formato sugerido:

```text
financeiro-kairo-backup-2026-07-22.zip
├── manifest.json
├── database/financeiro.db
├── attachments/
└── settings/settings.json
```

## Política recomendada

- backup automático diário local;
- retenção diária por 7 dias;
- retenção semanal por 8 semanas;
- retenção mensal por 12 meses;
- cópia periódica em dispositivo externo;
- teste de restauração.

## Restauração

1. Validar formato e hashes.
2. Verificar versão do esquema.
3. Criar backup preventivo do estado atual.
4. Restaurar em área temporária.
5. Executar teste de integridade.
6. Substituir o estado atual somente após sucesso.

## Logs e auditoria

Logs técnicos não devem registrar senhas, documentos completos ou conteúdo integral de anexos. Alterações críticas devem registrar operação, entidade, horário e origem.