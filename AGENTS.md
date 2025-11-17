<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.




# AGENTS.md – Governança Geral de Agentes

Este repositório é usado por múltiplos agentes (por exemplo: Codex CLI, Claude Code, SuperClaude e outros).  
Este arquivo define **regras gerais de colaboração** entre agentes, ferramentas e humanos.

Regras específicas de cada agente **não** ficam aqui:
- O agente de orquestração em nível macro deve seguir **`CODEX.md`**.
- Os agentes de desenvolvimento (Claude / SuperClaude) devem seguir **`CLAUDE.md`**.
- O OpenSpec pode ter regras adicionais em `openspec/AGENTS.md`.

**Prioridade de arquivos por agente**

- O **Codex** deve seguir principalmente o que está em `CODEX.md`.  
- O **Claude / SuperClaude** deve seguir principalmente o que está em `CLAUDE.md`.  
- Este `AGENTS.md` funciona como uma camada de governança geral (constituição):  
  em caso de conflito entre o que está aqui e o que estiver em `CODEX.md` ou `CLAUDE.md`, o arquivo específico do agente prevalece.



Pense neste arquivo como a “constituição” do projeto:  
define papéis, fluxo de trabalho e princípios que todos os agentes devem respeitar.


## 1. Papéis e Responsabilidades (visão geral)

Este projeto assume a seguinte divisão de papéis:

- **Orquestrador de Projeto (macro)**  
  - Responsável por:
    - Entender o estado geral do repositório,
    - Planejar a ordem das tarefas,
    - Garantir que o fluxo siga boas práticas (OpenSpec, Gitflow, testes, documentação),
    - Coordenar quais agentes executarão cada etapa (SuperClaude, Claude, etc.).
  - Normalmente este papel é desempenhado por um agente dedicado (por exemplo, Codex CLI), que deve seguir o arquivo `CODEX.md`.

- **Desenvolvedor Principal (SuperClaude)**  
  - Responsável por:
    - Implementar novas features,
    - Fazer refactors estruturais,
    - Trabalhar em múltiplos arquivos/módulos,
    - Ajustar arquitetura, contratos de API e performance,
    - Cuidar de blocos significativos de testes e documentação.
  - Normalmente implementado pelo **SuperClaude** (framework avançado em cima do Claude Code).
  - As regras detalhadas de como o desenvolvedor principal deve se comportar ficam em `CLAUDE.md`.

- **Desenvolvedor Secundário (Claude “normal”)**  
  - Responsável por:
    - Pequenas alterações localizadas (ex.: ajustes em uma função, mensagem de log, rótulo de UI),
    - Micro correções e pequenas melhorias em documentação.
  - Só deve ser usado quando a mudança é realmente pequena ou quando indicado explicitamente pelo orquestrador.
  - Também segue as instruções de `CLAUDE.md`.

- **Ferramentas de Especificação (OpenSpec / Tessl)**  
  - OpenSpec:
    - Ferramenta central para desenvolvimento guiado por especificações (Spec-Driven Development).
    - Mantém specs e changes em diretórios como `openspec/specs/` e `openspec/changes/`.
  - Tessl:
    - Registry/framework para specs reutilizáveis (libs externas, APIs, etc.).
    - Ajudar a evitar uso incorreto de APIs e divergência entre código e documentação.

- **Conectores e Contexto (MCPs, skills, outros agents)**  
  - MCPs, skills e outros agentes podem:
    - Buscar documentação,
    - Integrar com ferramentas externas (CI, monitoramento, registries, etc.),
    - Fornecer contexto adicional.
  - Devem ser usados quando trouxerem benefício concreto, não apenas “porque existem”.


## 2. Princípios Gerais de Trabalho

Todos os agentes devem respeitar estes princípios:

1. **Spec primeiro, código depois**  
   - Antes de mudanças relevantes:
     - Verificar se existe spec correspondente em OpenSpec.
     - Se não existir, criar/atualizar uma change/spec antes de implementar.
   - Implementação deve seguir a spec aprovada; divergências devem ser resolvidas atualizando a spec ou o código de forma explícita.

2. **OpenSpec como fonte funcional de verdade**  
   - O comportamento do sistema deve estar refletido em:
     - `openspec/specs/` → estado atual do sistema,
     - `openspec/changes/` → mudanças em andamento.
   - Nenhuma mudança grande deve ir para produção sem passar pelo fluxo do OpenSpec.

3. **Orquestração clara entre agentes**  
   - O agente orquestrador define:
     - Qual tarefa é feita agora,
     - Qual agente executa (SuperClaude, Claude, ferramenta externa),
     - Em qual branch e com qual fluxo de git.
   - Os agentes de desenvolvimento não devem “inventar” fluxos paralelos; devem seguir as orientações do orquestrador (documentadas em `CODEX.md`).

4. **SuperClaude como padrão, Claude como exceção**  
   - Sempre que uma tarefa envolver:
     - Mais de um pequeno trecho de código,
     - Vários arquivos,
     - Arquitetura, contratos de API ou testes em lote,
     - Refactors estruturais,
     - Deve ser tratada pelo **SuperClaude**.
   - Claude “normal” é usado apenas para ajustes muito pequenos, pontuais.

5. **Gitflow como referência de versionamento**  
   - Recomenda-se usar:
     - `main` para produção estável,
     - `develop` para integração,
     - `feature/...` para novas features,
     - `hotfix/...` e `release/...` quando fizer sentido.
   - Commits devem ser pequenos, coesos e com mensagens descritivas.
   - Branches e PRs devem estar alinhados ao que o orquestrador definir.

6. **Qualidade contínua (testes, docs, débito técnico)**  
   - Mudanças relevantes devem vir acompanhadas de:
     - Testes adequados (unitários, integração, contrato, conforme o projeto suportar),
     - Atualização de documentação (README, docs, comentários significativos).
   - TODO/FIXME e gambiarras devem ser:
     - Sinalizados,
     - Registrados como débito técnico,
     - Convertidos em tarefas/changes específicas quando possível.


## 3. Fluxo Macro por Feature / Mudança Importante

Para qualquer **feature nova**, **mudança de comportamento relevante** ou **refactor estrutural**, o fluxo recomendado é:

1. **Especificar**
   - Criar ou atualizar uma spec em OpenSpec:
     - Descrever contexto, objetivo, regras de negócio,
     - Definir entradas, saídas, casos de uso e critérios de aceitação.
   - Registrar a mudança em `openspec/changes/` (quando apropriado).

2. **Validar a spec**
   - O orquestrador e os devs (SuperClaude / Claude) devem:
     - Ler a spec,
     - Confirmar entendimento,
     - Sugerir ajustes se algo estiver ambíguo ou incompleto.

3. **Preparar o ambiente de desenvolvimento**
   - Garantir que:
     - Branch correta exista (`feature/...`),
     - Ambiente (uv/venv/containers) esteja configurado conforme diretrizes do projeto.

4. **Implementar**
   - Preferencialmente com **SuperClaude**:
     - Seguir o que estiver em `CLAUDE.md` sobre comandos e fluxo de trabalho,
     - Implementar em pequenos passos, com testes frequentes.
   - Usar Claude “normal” apenas se a mudança for mínima.

5. **Testar e revisar**
   - Rodar testes automatizados e linters.
   - Revisar:
     - Organização de pastas e módulos,
     - Aderência ao estilo do projeto,
     - Coerência com a spec de OpenSpec.

6. **Sincronizar spec e código**
   - Se o resultado final divergir da spec original:
     - Ajustar a spec,
     - Ou ajustar o código,
     - Garantir que `openspec/specs/` esteja alinhado ao estado real do sistema.

7. **PR e merge**
   - Abrir Pull Request,
   - Revisar (pelo menos conceitualmente, via orquestrador ou ferramentas de review),
   - Aprovar e fazer merge conforme o fluxo de Git definido para o projeto.


## 4. Uso de Ferramentas e Contexto Externo

- Agentes podem (e devem) consultar:
  - Documentação oficial de bibliotecas e frameworks,
  - Specs instaladas via Tessl,
  - Docs internas do repositório (`README.md`, `ARCHITECTURE.md`, etc.),
  - Arquivos específicos de cada agente (`CODEX.md`, `CLAUDE.md`, `openspec/AGENTS.md`).
- MCPs, skills e outros agentes:
  - Devem ser usados quando:
    - Facilitarem acesso a conhecimento confiável,
    - Automatizarem tarefas repetitivas (ex.: abrir issues, consultar logs),
    - Melhorarem a segurança ou a qualidade das decisões.

Evitar:
- Introduzir ferramentas extras sem motivo claro,
- Criar dependências complexas sem benefício concreto.

Qualquer proposta de mudança estrutural (novo fluxo de CI, nova ferramenta, novo padrão de spec) deve ser:
- Explicada de forma clara,
- Integrada à documentação (por exemplo, neste `AGENTS.md`, em `CODEX.md` ou em `CLAUDE.md`).


## 5. Estilo de Comunicação entre Agentes e Humanos

Todos os agentes devem:

- Usar linguagem clara, objetiva e didática.
- Explicar:
  - O que pretendem fazer,
  - Por que estão escolhendo certo fluxo/ferramenta,
  - Qual é o próximo passo concreto.
- Evitar jargão desnecessário ou decisões implícitas:
  - Sempre que uma escolha for relevante (ex.: usar SuperClaude vs Claude, criar nova spec vs reaproveitar uma existente), isso deve ser dito explicitamente.

Resumindo:

> Este projeto é guiado por **specs (OpenSpec)**, orquestrado por um agente macro (definido em `CODEX.md`) e implementado principalmente pelo **SuperClaude**, com o Claude como apoio em tarefas pequenas.  
> Todos os agentes devem usar este `AGENTS.md` como base de governança e buscar os arquivos específicos (`CODEX.md`, `CLAUDE.md`, `openspec/AGENTS.md`) para detalhes do seu papel.
