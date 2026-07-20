# Nexus Console

**Plano de control de [Nexus OS](https://github.com/royramosparaiso/ironbat-jarvis).**

Nexus Console es el meta-orquestador que despliega y gestiona instancias de Nexus Platform. Se instala **una sola vez** por operador y desde ella se administran N instancias con arquitecturas potencialmente distintas.

> **Impulsado por Ironbat Digital LLC.** Licencia MIT. Todavía en construcción — v0.1 en curso.

## Qué hace

- **Wizard de arquitectura por instancia.** Cuestionario de 6 pasos (persona, modalidad de despliegue, LLMs, memoria/grafos, áreas activas, governance) que emite `nexus.instance.yaml`.
- **Deployer.** Sabe desplegar Nexus Platform a Docker Compose local, Fly.io, Kubernetes u on-prem según la elección del wizard.
- **Instance Registry.** Catálogo persistente de instancias Platform gestionadas.
- **Secret Manager.** Rota y sincroniza credenciales (LLM providers, DB, storage) con cada instancia.
- **Agent Factory.** Crea, edita, versiona y despliega agentes, áreas y coordinadores a las instancias.
- **Jarvis-Console.** Agente propio con el que el operador dialoga en lenguaje natural.

## No hace

- **No gestiona espacios ni usuarios finales.** Eso vive en cada instancia Platform.
- **No accede a datos de negocio de las instancias.** Solo infra + catálogo de agentes.
- **No lee espacios personales.** Ni siquiera con rol `superadmin` de una instancia.

## Arquitectura de referencia

```
                    ┌─────────────────────────┐
                    │    Nexus Console        │  ← este repo
                    │  (control plane)        │
                    └───────────┬─────────────┘
                                │  JWT firmado
                    ┌───────────┼──────────────┐
                    ▼           ▼              ▼
             ┌──────────┐ ┌──────────┐  ┌──────────┐
             │ Platform │ │ Platform │  │ Platform │
             │  local   │ │  Fly.io  │  │   K8s    │
             └──────────┘ └──────────┘  └──────────┘
```

Ver docs de Nexus OS para el modelo completo: [Vision](https://github.com/royramosparaiso/ironbat-jarvis/blob/main/docs/vision.md) · [Specifications](https://github.com/royramosparaiso/ironbat-jarvis/blob/main/docs/specifications.md) · [RFC-001](https://github.com/royramosparaiso/ironbat-jarvis/blob/main/docs/rfc/001-nexus-framework.md).

### Portal gestionado (diseño aprobado, no implementado)

La evolución hacia un **portal web gestionado** de cuatro partes — **Nexus Hub** (plano de control
hospedado), **Nexus Operator** (agente saliente OSS, sin shell), **NexusOS Runtime/Platform** (plano
de datos soberano) y **Nexus Registry** (packs firmados) — está documentada como arquitectura
`v1alpha1` en [`docs/`](docs/README.md). Es **diseño aprobado, todavía no implementado**: ver la
[Visión de Nexus OS](docs/vision/nexus-os-vision.md), la
[especificación de arquitectura](docs/architecture/nexus-os-architecture.md), la
[especificación de desarrollo del Hub](docs/specs/b-nexus-hub.md), las
[ADR](docs/adr/) y los [esquemas + ejemplos](docs/schemas/README.md).

## Modo local single-tenant

Con un `docker compose up` levantas Console + Postgres + Redis en tu máquina, sin necesidad de tokens cloud. Console detecta que está sola, despliega una Platform local con arquitectura por defecto y crea el `superadmin`.

```bash
git clone https://github.com/royramosparaiso/nexus-console.git
cd nexus-console
docker compose up
```

Console UI: [http://localhost:7000](http://localhost:7000)
Platform UI (auto-desplegada): [http://localhost:7100](http://localhost:7100)

## Ecosystem registry

The **Ecosystem** page (`/ecosystem`, backed by `GET /ecosystem`) is an honest
catalogue of the AI building blocks Nexus can plug into — LLMs, frameworks,
vector databases, data extraction, open-model access, text embeddings, and
evaluation — plus the two local-first capabilities this repo actually ships.
Every entry carries an explicit **status** so nothing is oversold:

- `available` — works today with what's in the repo, no setup.
- `configurable` — supported, but needs an endpoint/key/flag first.
- `experimental` — real code, early / behind a flag.
- `planned` — a discoverable catalogue entry only; no integration code yet.

Real, in-repo capabilities:

- **LiteRT.js** (`experimental`, native) — small `.tflite` models run in the
  browser via WebGPU with a deterministic CPU/WASM fallback. Backs the Silero
  VAD slice in the Voice cockpit. Model access is gated by the
  `agent_local_model` registry (`GET/POST /local-models`): every model carries
  provenance (`sha256`, `license`, `size_bytes`) so an agent can only load
  whitelisted URLs. Enabled per-instance via the `local_inference` flag.
- **Voicebox** (`configurable`, external) — optional local voice sidecar
  ([jamiepine/voicebox](https://github.com/jamiepine/voicebox)) for TTS/STT and
  an HTTP MCP server. It runs as a **separate local process**; Nexus only talks
  to a configured base URL and **never uploads audio**. Enable with
  `CONSOLE_VOICEBOX_ENABLED=true` + `CONSOLE_VOICEBOX_BASE_URL`; check health at
  `GET /voicebox/status`. **Voice cloning is opt-in** — gated behind
  `CONSOLE_VOICEBOX_VOICE_CLONING_CONSENT=true` and only for voices you own.

### Integration adapters

Everything else in the reference ecosystem diagram (Chroma, Qdrant, LangChain,
Firecrawl, Nomic, Giskard, …) is now a real **`configurable`** integration
rather than a logo-only `planned` row. A single generic adapter layer
(`app/services/integrations`) describes each provider as data — typed config
fields, secret **references**, capability metadata, a docs link, and a health
probe — so no per-vendor SDK is vendored. Manage them on **Ecosystem →
Integrations** or via the API:

- `GET  /integrations/adapters` — the adapter catalogue (fields + secret env
  names; never any secret values).
- `POST /integrations/profiles` — create a connection profile (endpoint +
  secret env-name references + optional agent-template scoping).
- `POST /integrations/profiles/{id}/test` — run the adapter's health probe
  (OpenAI-compatible, header/query key, basic auth, HTTP health, or Postgres
  `SELECT 1`, depending on the provider). Bedrock is config-only (`no_probe`).
- `GET  /integrations/capabilities` / `GET /integrations/resolve` — the enabled
  capabilities exposed to agents/sidecars, with secrets redacted to presence
  flags.

Coverage: LLMs (OpenAI, Anthropic, Gemini, Mistral, Bedrock, DeepSeek, Cohere,
Groq, Together, Ollama), open-weight families via an OpenAI-compatible runtime
(Phi-4, Gemma 3, Llama 4, Qwen 3, Hugging Face), embeddings (Nomic, SBERT,
OpenAI, Voyage, Google, Cohere), vector stores (Chroma, Pinecone, Qdrant,
Weaviate, Milvus, pgvector, Cassandra, OpenSearch), framework bridges
(LangChain, LlamaIndex, Haystack, txtai), data extraction (Crawl4AI, Firecrawl,
ScrapeGraphAI, MegaParser, Docling, LlamaParse, ExtractThinker), and evaluation
(Giskard, Ragas, DeepEval).

**Secret model.** There is no encrypted vault in this repo, so profiles store
environment-variable **names**, not values. Secret values are read from the
process environment only at probe/resolve time and are never persisted to the
database nor returned by the API. See `.env.example` for the provider env vars.

## Stack

- **Backend:** FastAPI (Python 3.12+), SQLAlchemy 2.x, Postgres, Redis, JWT (Ed25519).
- **Frontend:** Vite + React 19 + Tailwind, raw `fetch` (no TanStack Query), dark mode nativo.
- **Deployer:** Docker SDK for Python + adaptadores Fly.io / kubectl / SSH.
- **Contratos:** paquete compartido `nexus-core` (SDK — repo aparte, planeado).

## Roadmap corto

- [ ] Backend `/health`, `/instances` CRUD, `/_platform/notify` stub
- [ ] Admin panel LLM Providers (migrado desde `ironbat-jarvis`)
- [ ] Wizard de arquitectura UI (6 pasos)
- [ ] Deployer para modo local (Docker Compose)
- [ ] Deployer para Fly.io
- [ ] Instance Registry con salud en tiempo real
- [ ] Agent Factory + catalog
- [ ] Jarvis-Console

## Licencia

MIT — ver [LICENSE](LICENSE).
