# Change: Add Meta Provider Production Support

## Why
O esqueleto base do Social Video Explorer já existe com modo mock, mas precisamos integrar o Meta Provider (Facebook + Instagram) em modo produção. Esta change habilitará autenticação OAuth2 real, busca de conteúdo nas plataformas Meta, e mapeamento dos dados para o VideoResult unificado, permitindo testes reais com APIs de produção.

## What Changes
- Implementar cliente OAuth2 para Facebook Graph API e Instagram Basic Display API
- Criar integração real com Meta APIs substituindo stubs existentes
- Adicionar suporte a token único unificado para FB+IG (app-based authentication)
- Implementar mapeamento de campos específicos do Meta para VideoResult padrão
- Configurar fallback automático para mock quando APIs indisponíveis
- Implementar busca básica por hashtag e conteúdo de mídia
- Adicionar tratamento de erro específico para APIs Meta (rate limits, permissões)

## Impact
- Affected specs: `specs/video-providers.md` (Meta provider real), `specs/video-search.md` (busca real), `specs/video-ui.md` (status de produção)
- Affected code: `core/providers/meta.py` (implementação real), `core/services/search_service.py` (integração)
- External dependencies: `facebook-sdk`, `requests-oauthlib`, ou cliente HTTP personalizado
- Security: Gestão segura de OAuth tokens, refresh tokens, e credenciais de app
- Future work: Multi-app support, caching avançado, rate limiting virão em changes futuras

## MVP Scope
**Incluso:**
- OAuth2 token único para FB+IG via app-level authentication
- Busca básica de conteúdo por hashtag
- Mapeamento essencial para VideoResult (id, title, url, thumbnail, created_at)
- Fallback mock quando APIs indisponíveis
- Status UI simples indicando modo produção vs mock
- Testes com sandbox e mocks

**Excluído (futuro):**
- Multi-app authentication
- Caching inteligente
- Rate limiting avançado
- Monitoramento e analytics
- Busca avançada com filtros complexos