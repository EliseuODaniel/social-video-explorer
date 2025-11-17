# Change: Setup Basic Video Explorer Skeleton

## Why
O projeto Social Video Explorer atualmente existe apenas como configuração básica (git, arquivos de governança), sem código implementado. Precisamos estabelecer o esqueleto fundamental da arquitetura com modo mock para permitir desenvolvimento iterativo futuro.

## What Changes
- Criar estrutura de pastas base following the specified layered architecture (ui/, core/, services/, providers/, workflows/)
- Implementar contrato BaseVideoProvider com método get_capabilities() para padronizar futuras integrações
- Definir schemas Pydantic básicos para VideoResult e SearchParams com raw_payload
- Criar search_service básico que opera com provider único e modo mock
- Implementar UI simples em Streamlit com formulário básico, grid simples e modo demo
- Estabelecer uso de .env para configuração e credenciais futuras
- Incluir Meta provider stub e mock provider para demonstração

## Impact
- Affected specs: Nenhuma (criando novas capabilities básicas do zero)
- Affected code: Esqueleto estrutural do projeto base
- External dependencies: Nenhuma para modo mock; preparação para APIs futuras
- Security: Prepara estrutura para gestão segura de credenciais via variáveis de ambiente
- Future work: Funcionalidades avançadas (caching, rate limiting, múltiplos providers) virão em changes futuras