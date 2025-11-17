# Change: Setup Core Video Explorer Architecture

## Why
O projeto Social Video Explorer atualmente existe apenas como configuração básica (git, arquivos de governança), sem código implementado. Precisamos estabelecer a arquitetura fundamental para suportar busca e análise de vídeos de múltiplas plataformas sociais, começando com Meta e expandindo para outras plataformas.

## What Changes
- Criar estrutura de pastas base following the specified layered architecture (ui/, core/, services/, providers/, workflows/)
- Implementar contrato BaseVideoProvider com método get_capabilities() para padronizar integração com APIs sociais
- Definir schemas Pydantic para VideoResult e SearchParams com raw_payload para dados brutos das APIs
- Criar search_service que orquestra múltiplos providers respeitando max_results
- Implementar UI básica em Streamlit com integração mock ao serviço e exibição em grid
- Estabelecer uso de .env para gestão segura de segredos e tokens de API

## Impact
- Affected specs: Nenhuma (criando novas capabilities do zero)
- Affected code: Estrutura completa do projeto base
- External dependencies: APIs do Meta, YouTube, TikTok, Instagram via providers específicos
- Security: Implementa gestão segura de credenciais via variáveis de ambiente