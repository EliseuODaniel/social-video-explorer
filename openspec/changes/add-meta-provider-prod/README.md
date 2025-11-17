# Add Meta Provider Production Support

Esta change implementa integração real com as APIs do Meta (Facebook + Instagram) no Social Video Explorer.

## Overview

Transforma o esqueleto existente com modo mock em um sistema funcional capaz de buscar conteúdo real das plataformas Meta usando OAuth2 e APIs Graph.

## Prerequisites

- Esqueleto base implementado (change `add-setup-social-video-explorer`)
- App Facebook Developers configurado com Graph API permissions
- Instagram Basic Display API configurada
- Credenciais OAuth2 disponíveis

## Key Changes

### 1. OAuth2 Integration
- Cliente OAuth2 para Facebook Graph API
- Cliente OAuth2 para Instagram Basic Display API
- Gestão unificada de tokens (app-level authentication)
- Refresh automático de tokens

### 2. Meta API Real Integration
- Substituição de stubs por implementações reais
- Busca de conteúdo por hashtag
- Tratamento específico de erros das APIs Meta
- Fallback automático para modo mock

### 3. Data Mapping
- Mapeamento de campos específicos do Meta para VideoResult
- Preservação de dados brutos em `raw_payload`
- Extração de thumbnails e metadados
- Normalização de URLs

### 4. UI Enhancements
- Indicadores de modo produção vs mock
- Status de autenticação OAuth2
- Health checks das APIs
- Mensagens de erro específicas

## Files Modified

### Core Implementation
- `core/providers/meta.py` - Implementação real das APIs Meta
- `core/services/search_service.py` - Integração com provider produção

### Configuration
- `.env.example` - Novas variáveis de ambiente Meta
- `requirements.txt` - Dependências OAuth2

### UI Updates
- `ui/streamlit_app.py` - Indicadores de produção e status

### Testing
- Novos testes para OAuth2, API integration, e fallback

## MVP Scope

**Incluso:**
- ✅ OAuth2 token único para FB+IG
- ✅ Busca básica por hashtag
- ✅ Mapeamento essencial VideoResult
- ✅ Fallback automático para mock
- ✅ Status UI simples
- ✅ Testes sandbox/mock

**Excluído (futuro):**
- ❌ Multi-app authentication
- ❌ Caching avançado
- ❌ Rate limiting avançado
- ❌ Monitoramento
- ❌ Busca avançada

## Validation

```bash
# Validate change structure
openspec validate add-meta-provider-prod --strict

# Run tests
pytest tests/test_meta_provider.py -v
pytest tests/test_search_integration.py -v

# Test production mode
streamlit run ui/streamlit_app.py -- --mode=production
```

## Deployment Notes

1. Configure variáveis de ambiente com credenciais Meta
2. Teste em sandbox antes de produção
3. Monitore rate limits das APIs
4. Verifique fallback para mock funciona

## Future Work

Próximas changes focarão em:
- Multi-app support
- Caching inteligente
- Rate limiting avançado
- Monitoramento e analytics