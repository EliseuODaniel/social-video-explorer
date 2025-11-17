# Project Context

## Purpose
Social Video Explorer é uma plataforma para exploração e análise de conteúdo de vídeo social. O projeto permite buscar, visualizar e analisar vídeos de plataformas sociais com foco em métricas de engajamento, tendências e insights de conteúdo.

## Tech Stack
- **Python 3.11** - Linguagem principal
- **Streamlit** - Interface web para análise de dados e visualização
- **httpx** - Cliente HTTP assíncrono para requisições a APIs
- **Pydantic** - Validação e serialização de dados
- **Docker** - Containerização e deployment
- **Temporal** - Orquestração de workflows (planejado para futuro)

## Project Conventions

### Code Style
- Seguir PEP 8 e formatação com black
- Type hints obrigatórios em todo código Python
- Nomenclatura: snake_case para variáveis/funções, PascalCase para classes
- Docstrings seguindo padrão Google-style para classes e funções públicas

### Architecture Patterns
Arquitetura em camadas organizada como:
- **UI/** (Streamlit frontend): Componentes de interface e visualização
- **core/**: Lógica de negócio e modelos de domínio
- **services/**: Serviços de integração e regras de negócio
- **providers/**: Clientes para APIs externas (YouTube, TikTok, Instagram, etc.)
- **workflows/**: Orquestração de processos complexos (Temporal no futuro)

### Testing Strategy
- **pytest** como framework principal de testes
- Testes unitários para lógica de negócio (core/services)
- Testes de integração para providers
- Testes de smoke/import para verificar funcionamento básico da aplicação
- Cobertura mínima: 80% para camadas core/services

### Git Workflow
Adoção de Gitflow com branches:
- **main**: Produção estável
- **develop**: Integração de features
- **feature/***: Desenvolvimento de novas funcionalidades
- **hotfix/***: Correções críticas em produção
- Commits semânticos: feat, fix, chore, refactor, docs, test

## Domain Context
O projeto lida com:
- APIs de redes sociais (YouTube, TikTok, Instagram, Twitter/X)
- Métricas de engajamento (views, likes, comments, shares)
- Análise de tendências e viralização
- Dados estruturados de vídeo social
- Limitações rate limits e autenticação de APIs

## Important Constraints
- Rate limits das APIs sociais devem ser respeitados rigorosamente
- Privacidade de dados dos usuários conforme GDPR/CCPA
- Processamento assíncrono para lidar com grandes volumes de dados
- Cache inteligente para minimizar chamadas às APIs
- Tratamento de erros robusto para instabilidades de APIs externas

## External Dependencies
- **YouTube Data API v3** - Dados de vídeos e canal
- **TikTok Research API** - Métricas e conteúdo (quando disponível)
- **Instagram Basic Display API** - Conteúdo e engajamento
- **Twitter/X API v2** - Dados de vídeos sociais
- Serviços de cloud (AWS/GCP) para deploy e storage
- Database (PostgreSQL/MongoDB) para persistência de dados
