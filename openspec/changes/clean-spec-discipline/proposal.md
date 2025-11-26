# Change: Clean Spec Discipline

## Why
O arquivamento anterior do change `add-meta-provider-prod` revelou inconsistências na disciplina de especificações: tarefas marcadas como incompletas mesmo após implementação 100% concluída, e falha na atualização automática das specs devido a headers ausentes. Isso indica necessidade de estabelecer práticas consistentes de finalização de changes e garantir estrutura adequada das specs para validações futuras.

## What Changes
- Revisar e atualizar status de tasks nos changes arquivados (2025-11-17-add-setup-social-video-explorer, 2025-11-18-add-meta-provider-prod)
- Corrigir headers e estrutura das specs atuais para garantir validação bem-sucedida
- Estabelecer padrão de finalização de change: marcar tasks como completas quando implementação estiver concluída
- Adicionar headers faltantes às specs para suportar atualizações automáticas do OpenSpec
- Documentar práticas de disciplina de especificações para referência futura

## Impact
- Affected specs: `video-providers`, `video-search`, `video-ui` (ajuste de headers/estrutura)
- Affected changes: `2025-11-17-add-setup-social-video-explorer`, `2025-11-18-add-meta-provider-prod` (atualização de status)
- External dependencies: Nenhuma (alterações restritas a openspec/)
- Process improvement: Estabelece padrões para finalização de changes e validação de specs
- Future work: Melhora a confiabilidade do processo de archiving e validação

## Scope
**Incluso:**
- Revisão e atualização de status de tasks em changes arquivados
- Correção de headers e estrutura das specs atuais
- Documentação de práticas de disciplina de especificações
- Validação da estrutura corrigida com `openspec validate --strict`

**Excluído:**
- Alterações de código ou configurações fora de openspec/
- Reabertura de changes já implementados
- Modificação de requisitos funcionais das specs