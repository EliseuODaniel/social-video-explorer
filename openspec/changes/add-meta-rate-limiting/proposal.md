# Change: Add Meta Provider Rate Limiting and Production Hardening

## Why
O Meta Provider MVP está funcionando em produção, mas sem proteção contra rate limiting. Isso cria riscos críticos:

**Riscos de Produção:**
- **API Block:** Meta Graph API pode bloquear o app após muitos requests (HTTP 429)
- **Custos Inesperados:** Sem controle de volume, custos podem disparar
- **Degradação:** Sem fallback coordenado quando limites são atingidos
- **Experiência do Usuário:** Falhas silenciosas ou erros não tratados

## What Changes

### 1. Rate Limiting Conservador
- Implementar throttling de 150 requests por hora por IP/app
- Adicionar circuit breaker automático para detectar falhas
- Configurar retry com exponential backoff
- Proteger tanto Instagram Basic Display API quanto Facebook Graph API

### 2. Cache em Memória
- Implementar cache LRU para tokens OAuth (TTL: 1 hora)
- Cache de resultados de busca (TTL: 15 minutos)
- Cache de health status (TTL: 5 minutos)
- Cache de hashtags populares (TTL: 1 hora)

### 3. Métricas e Monitoramento
- Logs estruturados para rate limit events
- Contadores para requests, cache hits, retries
- Métricas de latência e error rate
- Health checks que incluem status do rate limiter

### 4. Ajustes na UI
- Indicadores visuais de rate limiting status
- Mensagens informativas quando próximo de limites
- Fallback graceful para dados em cache
- Notificações de erro amigáveis

### 5. Resiliência Aprimorada
- Fallback automático para mock quando APIs indisponíveis
- Cache warming para consultas populares
- Configuração de timeouts adequados
- Error handling específico para diferentes falhas

## Impact
- **Affected specs:** video-providers (rate limiting), video-search (cache), video-ui (status indicators)
- **External dependencies:** Apenas bibliotecas Python existentes (não novas APIs)
- **Performance:** Redução de chamadas API em 60-80% através de cache
- **Cost Control:** Proteção contra picos de uso e custos inesperados
- **Production Readiness:** Meta Provider pronto para scale seguro

## Success Criteria
- [ ] Rate limiting configurado para 150 req/hora
- [ ] Cache implementa com hit rate >50%
- [ ] UI mostra status de rate limiting
- [ ] Logs e métricas funcionando em produção
- [ ] Zero downtime durante implementação

## Risks e Mitigações
- **Cache Staleness:** Dados podem ficar desatualizados até 1h → mitigado com TTLs apropriados
- **Complexidade:** Adiciona mais componentes ao stack → mitigado com código simples e testado
- **Memory Usage:** Cache consome RAM → mitigado com LRU e limits adequados