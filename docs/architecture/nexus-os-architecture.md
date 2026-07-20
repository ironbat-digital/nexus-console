# Especificación de arquitectura de Nexus OS (system-wide)

- **Estado:** Diseño aprobado · **no implementado** (TARGET-STATE salvo donde se marque ACTUAL)
- **Versión de arquitectura:** `v1alpha1` (infraestructura) + `v1alpha2` (capa de producto, aditiva)
- **Fecha:** 2026-07-19
- **Autor:** Ironbat Digital LLC
- **Documento canónico único.** Esta es la **especificación de arquitectura autoritativa system-wide** de
  Nexus OS. Sustituye a la antigua "arquitectura del Portal Gestionado", que queda como stub superado. El
  detalle de la aplicación web del Hub (journeys, máquina de estados de setup, modelo de datos del Hub,
  API/eventos) vive ahora en la [especificación de desarrollo del Hub](../specs/b-nexus-hub.md).
- **Documentos relacionados:** [Visión de Nexus OS](../vision/nexus-os-vision.md), [glosario](glossary.md), [migración y compatibilidad](migration-and-compatibility.md), [frontera OSS/comercial](product-oss-boundary.md), [ADR-0001…0011](../adr/), [especificaciones por componente](../specs/README.md), [esquemas](../schemas/README.md).

> **Origen y alcance.** Este documento desarrolla la propuesta estratégica aprobada como especificación
> técnica de referencia system-wide. **No** implementa Hub, Operator, Registry, ejecución remota,
> facturación ni provisioning. Ningún componente descrito como TARGET-STATE existe como código.

## Índice

1. [Contexto y objetivos](#contexto)
2. [Contexto del sistema y mapa de componentes](#componentes)
3. [Fronteras de confianza](#confianza)
4. [Plano de control vs. plano de datos](#planos)
5. [Frontera OSS/propietaria](#oss)
6. [Personal vs. Team/Organization](#ediciones)
7. [Relaciones Hub/Operator/Runtime/Registry/Studio](#relaciones)
8. [Ciclo de vida de paquetes y artefactos](#packages)
9. [Modelo de estado deseado y reconciliación](#reconciliacion)
10. [Flujo de entitlements](#entitlements)
11. [Modalidades de despliegue](#modalidades)
12. [Identidad y tenancy](#identidad)
13. [Propiedad de los datos y frontera de secretos](#datos)
14. [Modelo de eventos y observabilidad](#observabilidad)
15. [Comportamiento ante fallo/offline](#fallo)
16. [Versionado y migraciones](#versionado)
17. [Flujos de secuencia extremo a extremo](#secuencias)
18. [Estado actual vs. objetivo y mapa de dependencias](#estado)
19. [Índice de componentes y contratos](#indice-componentes)

---

<a id="contexto"></a>
## 1. Contexto y objetivos

Nexus OS es un sistema operativo de agentes de IA soberano y componible. Esta especificación fija la
arquitectura system-wide: qué componentes existen, dónde están sus fronteras de confianza, cómo fluyen el
estado deseado y los entitlements, y cómo se relacionan las capas OSS y propietaria. Objetivos de la
arquitectura:

- Un núcleo (Runtime) que **funciona sin conexión** y sin Hub.
- Un plano de control (Hub) opcional que **automatiza operación** sin apropiarse de datos.
- Habilitación por **capacidad firmada**, no por control remoto ni DRM.
- **Reversibilidad, auditoría y aislamiento** como invariantes transversales.

No-objetivos de la arquitectura: shell remoto, federación entre instancias, marketplace transaccional y
cualquier ejecución arbitraria remota (ver [visión §17](../vision/nexus-os-vision.md)).

<a id="componentes"></a>
## 2. Contexto del sistema y mapa de componentes

```
                         Zona de confianza: Ironbat (hospedado)
        ┌───────────────────────────────────────────────────────┐
        │  Nexus Hub  ── cuentas, cuestionario, blueprint,        │
        │               estado de setup, metadatos de flota,      │
        │               catálogo, emisión de entitlements.        │
        │               NO datos de negocio.                      │
        └───────▲───────────────────────────────────┬────────────┘
                │ estado deseado firmado             │ catálogo + grants firmados
   status-report│ (saliente, iniciada por Operator)  │
                │                                    ▼
        ┌───────┴────────────┐             ┌──────────────────────┐
        │  Nexus Operator     │            │   Nexus Registry      │
        │  (OSS, sin shell)   │            │ (packs firmados)      │
        └───────┬────────────┘             └──────────────────────┘
                │ Runtime Admin API (local, autenticación fuerte)
                ▼
   Zona de confianza: instancia soberana del usuario
        ┌───────────────────────────────────────────────────────┐
        │  Nexus OS Runtime/Platform ── Jarvis, espacios, áreas,  │
        │  agentes, memoria, usuarios, vault local de secretos.   │
        └───────────────────────────────────────────────────────┘
```

Componentes y su especificación canónica:

| Componente | Rol | Spec canónica |
|---|---|---|
| Personal Runtime | Edición Personal libre, un propietario, sin Hub | [Spec A](../specs/a-personal-runtime.md) |
| Nexus Hub (app web) | Plano de control hospedado + emisor de entitlements | [Spec B](../specs/b-nexus-hub.md) |
| Team / Organization | Multiusuario, roles, políticas de organización | [Spec C](../specs/c-team-organization.md) |
| Nexus Operator | Enrolamiento, reconciliación, salud | [Spec D](../specs/d-operator-instance-lifecycle.md) |
| Nexus Registry | Catálogo, cuatro carriles, grants | [Spec E](../specs/e-registry-catalog-distribution.md) |
| Modelo de paquetes/artefactos | Agentes, skills, flows, sidecars, skulls, tareas, packs | [Spec F](../specs/f-package-artifact-model.md) |
| Entitlements/suscripción | Verificación offline, degradación graciosa | [Spec G](../specs/g-entitlements-subscriptions-degradation.md) |
| Seguridad/confianza/secretos | Firma, identidad, secretos | [Spec H](../specs/h-security-trust-signing-secrets.md) |
| Studio | Autoría, overlays, validación, publicación | [Spec I](../specs/i-studio-authoring-publishing.md) |
| Modalidades de despliegue | self-hosted / BYOC / managed | [Spec J](../specs/j-deployment-modalities.md) |
| CLI/SDK/instalador/handoff | Herramientas y automatización de bootstrap | [Spec K](../specs/k-cli-sdk-installer-handoff.md) |
| Observabilidad/auditoría/ops | Telemetría, backup/recuperación, soporte | [Spec L](../specs/l-observability-audit-ops.md) |
| Inferencia local/voz/edge | LiteRT, Voicebox, VAD (ownership + enlaces) | [Spec M](../specs/m-local-inference-voice-edge.md) |

<a id="confianza"></a>
## 3. Fronteras de confianza (normativas)

- **Hub ↔ Operator:** solo el Operator inicia la conexión (saliente). El Hub solo envía **estado deseado
  firmado** y recibe **status-report** (metadatos/salud). Sin canal de shell.
- **Operator ↔ Runtime:** el Operator invoca el **Runtime Admin API** local con capacidades acotadas.
  Nunca ejecuta código arbitrario.
- **Datos de negocio y memoria:** viven **solo** en el Runtime. El Hub no los recibe por defecto.
- **Secretos:** en el vault local del Runtime; el Hub solo maneja el manifiesto público del bundle
  cifrado (ver [ADR-0005](../adr/0005-secrets-bundle-and-oauth.md), [Spec H](../specs/h-security-trust-signing-secrets.md)).

<a id="planos"></a>
## 4. Plano de control vs. plano de datos

- **Plano de control (Hub):** intención y coordinación. Emite estado deseado, entitlements, grants y
  catálogo. No es dependencia de disponibilidad del plano de datos.
- **Plano de datos (Runtime):** ejecución y custodia. Jarvis, áreas, agentes, memoria, usuarios. Fuente
  de verdad de los datos y de la auditoría de instancia.
- **Mediador (Operator):** reconcilia el delta entre estado deseado y estado real mediante el Runtime
  Admin API, con capacidades acotadas y auditables.

<a id="oss"></a>
## 5. Frontera OSS/propietaria

Detalle en [frontera OSS/comercial](product-oss-boundary.md) y [ADR-0008](../adr/0008-oss-commercial-boundary-and-license.md).

- **OSS (Apache-2.0 objetivo):** Runtime, Operator, CLI, SDK, esquemas/contratos, verificador/instalador
  de packs, cliente de Registry comunitario, Entitlement Verifier, capacidades locales básicas.
- **Propietario:** Hub hospedado, servicios gestionados, orquestación de secretos a escala, catálogo
  curado gestionado y **Team Capability Pack**.
- **Seguridad, exportación y portabilidad permanecen en OSS en todas las ediciones.** El repositorio
  mixto actual permanece **MIT** hasta la auditoría legal.

<a id="ediciones"></a>
## 6. Personal vs. Team/Organization

La **edición** es un eje declarado (`edition.declaration.schema.json`) ortogonal a la modalidad de
despliegue. Personal (`personal_base`) no requiere entitlement ni conexión. Team/Organization requieren
un entitlement firmado vigente (`verified_entitlement`) o cacheado en gracia (`cached_entitlement`). Ver
[Spec C](../specs/c-team-organization.md) y [Spec G](../specs/g-entitlements-subscriptions-degradation.md).

<a id="relaciones"></a>
## 7. Relaciones Hub / Operator / Runtime / Registry / Studio

- **Hub → Operator:** publica estado deseado firmado; recibe salud.
- **Operator → Runtime:** aplica capacidades acotadas vía Admin API; instala packs.
- **Runtime → Registry:** consulta y descarga packs firmados (directo para carriles OSS; vía grant para
  premium/privados).
- **Studio → Registry:** publica packs firmados (Ironbat verificado, comunidad, organización privada);
  produce overlays que el Runtime aplica sin editar el pack original. Ver [Spec I](../specs/i-studio-authoring-publishing.md).
- **Hub → Registry:** presenta el catálogo curado y emite grants de descarga para carriles restringidos.

<a id="packages"></a>
## 8. Ciclo de vida de paquetes y artefactos

Ver [ADR-0006](../adr/0006-nexus-pack-format.md), [ADR-0007](../adr/0007-update-channels-and-rollout.md),
[Spec E](../specs/e-registry-catalog-distribution.md) y [Spec F](../specs/f-package-artifact-model.md).

Explorar → previsualizar (diff + coste incremental) → instalar (staging local + verificación de firma) →
validar (`tests` del manifiesto) → activar → canales (`stable`/`beta`/`pinned`) → staged rollout →
rollback → fork local (overlay) → publicar de vuelta (opcional). Un **Pack** es la unidad atómica de
distribución que empaqueta áreas, agentes, skulls, flows y sidecars; compone primitivas del Runtime,
nunca es un runtime nuevo.

<a id="reconciliacion"></a>
## 9. Modelo de estado deseado y reconciliación

Esquema: [`desired-state`](../schemas/v1alpha1/desired-state.schema.json). El Hub publica un documento de
**estado deseado firmado** (Ed25519, con `trust_domain`, `nonce`, `issued_at`/`expires_at`, `revision`
monotónica). El Operator obtiene el documento (poll o push WebSocket), lo verifica **100% offline** con
la clave pineada, calcula el delta contra el estado real y aplica solo **intents de capacidad acotada**.
No hay comandos imperativos ni shell. La `revision` monotónica y el `nonce` previenen replay.

<a id="entitlements"></a>
## 10. Flujo de entitlements

Esquema: [`entitlement`](../schemas/v1alpha2/entitlement.schema.json). Flujo:

1. La cuenta se suscribe (proceso comercial fuera de alcance) y el Hub emite un **entitlement firmado**
   por capacidad, con `expires_at`, gracia, `nonce`, `revision` y `organization_id` (para
   team/organization).
2. El Operator/Runtime obtiene y **cachea** el entitlement; lo verifica offline con la clave del Hub
   pineada por `trust_domain`.
3. El **Entitlement Verifier** (OSS, en runtime) comprueba enlace de clave, orden temporal y anti-replay
   (ver [Spec H](../specs/h-security-trust-signing-secrets.md)).
4. Ante renovación/expiración, el Hub actualiza `SubscriptionState`; el Runtime aplica los efectos de
   degradación graciosa (ver [Spec G](../specs/g-entitlements-subscriptions-degradation.md)).
5. Para un pack premium/privado, el Hub emite un `PackageDownloadGrant` de vida corta (un solo uso).

Personal no requiere ninguna verificación online.

<a id="modalidades"></a>
## 11. Modalidades de despliegue

`self_hosted` / `byoc` / `managed`, ortogonales a la edición
(`deployment-modality.schema.json`). Única combinación prohibida por contrato: **managed + personal**.
Ver [Spec J](../specs/j-deployment-modalities.md) y [ADR-0010](../adr/0010-edition-vs-deployment-modality.md).

<a id="identidad"></a>
## 12. Identidad y tenancy

- **Identidad de instancia:** mTLS por instancia, credenciales de vida corta con rotación; sin credencial
  maestra (ver [ADR-0004](../adr/0004-operator-enrollment-and-identity.md)).
- **Identidad de cuenta/organización:** el Hub es el **emisor** de `OrganizationId`/`UserRef` y los emite
  **lowercase-canónicos** (`^org_[a-z0-9]{4,40}$` / `^usr_[a-z0-9]{4,40}$`), normalizando en el borde de
  emisión, nunca en el de consumo. Así un `org_id` viaja sin cambios dentro de un `PackageScope`
  `private-organization:<org_id>`.
- **Tenancy:** aislamiento estricto por instancia también dentro del Hub multi-tenant; sin BD compartida
  de contenido.

<a id="datos"></a>
## 13. Propiedad de los datos y frontera de secretos

- **Datos y memoria:** solo en el Runtime. El Hub nunca los recibe por defecto.
- **Secretos:** en el vault local. El bundle de secretos se cifra con **age/X25519** a la clave pública
  de la instancia, en el navegador y de un solo uso; se invalida tras importar. El Hub solo maneja el
  manifiesto público (referencias, nunca valores). OAuth/device flow preferente. Prohibición de secretos
  en prompts cowork. Ver [ADR-0005](../adr/0005-secrets-bundle-and-oauth.md) y [Spec H](../specs/h-security-trust-signing-secrets.md).

<a id="observabilidad"></a>
## 14. Modelo de eventos y observabilidad

Detalle en [Spec L](../specs/l-observability-audit-ops.md).

- **Audit log dual:** toda orden aplicada y todo cambio de estado quedan en el audit log del Hub **y** de
  la instancia. En la instancia es exportable (NDJSON, como RFC-002 `/_console/audit`).
- **Telemetría de flota:** solo métricas de salud agregadas (versión, uptime, CPU/mem %, paquetes
  instalados, progreso de setup). Nunca contenido.
- **Eventos representativos:** `desired_state.updated`, `instance.health_changed`,
  `package.install.completed` / `package.install.failed`.

<a id="fallo"></a>
## 15. Comportamiento ante fallo/offline

- **Caída del Hub:** Runtime y Operator siguen operando en modo autónomo; el Hub es plano de control, no
  dependencia de disponibilidad del plano de datos.
- **Operator desconectado (kill switch):** la instancia sigue funcionando; se detienen solo las
  actualizaciones automatizadas.
- **Pérdida de red:** el Operator hace fallback a polling; reanuda aplicando la `revision` más reciente.
- **Setup interrumpido:** el estado del `SetupPlan` persiste; el usuario reanuda exactamente donde lo
  dejó.
- **Entitlement:** dentro de la ventana de gracia, Team/Organization operan offline con el entitlement
  cacheado; Personal no depende del Hub en ningún caso.

<a id="versionado"></a>
## 16. Versionado y migraciones

Los contratos se versionan por separado del código (`x-nexus-contract-version`). `v1alpha2` es **aditivo
y backward-compatible** sobre `v1alpha1` y reutiliza crypto/identificadores por `$id` absoluto. La
migración de despliegues Console/Fly actuales es **opt-in, no destructiva, reversible** (ver
[migración y compatibilidad](migration-and-compatibility.md)).

<a id="secuencias"></a>
## 17. Flujos de secuencia extremo a extremo

**Alta gestionada (managed):**

```
Usuario → Hub: registro, crea instancia, responde cuestionario
Hub → Usuario: blueprint (7 artefactos) para revisión/aprobación
Usuario → Hub: aprueba arquitectura, coste, permisos, riesgos
Hub → Operator: publica estado deseado firmado (revision N)
Operator → Runtime: aplica intents acotados, instala packs firmados
Operator → Hub: status-report (salud, progreso de setup)
Runtime: operativa (Jarvis, áreas, agentes)
```

**Instalación de pack premium:**

```
Runtime/Usuario → Hub: solicita pack premium
Hub: verifica entitlement (premium_pack_access)
Hub → Runtime: emite PackageDownloadGrant de vida corta (un solo uso)
Runtime → Registry: descarga artefacto con grant; verifica firma offline
Runtime: staging → validación (tests) → activación
```

**Expiración de suscripción (degradación graciosa):**

```
Hub → Runtime: SubscriptionState = expired
Runtime: usuarios adicionales → readonly; agentes premium y tareas → paused
Runtime: owner_access = preserved; export_available = true (invariantes)
Usuario → Hub: renueva → entitlement nuevo → reactivación (sin pérdida de datos)
```

<a id="estado"></a>
## 18. Estado actual vs. objetivo y mapa de dependencias

**Actual (implementado, v0.13.8):** Console (wizard, deployer, instance registry, secret manager, agent
factory, Jarvis-Console), Platform, `agent_templates/`, ecosystem registry, inferencia local
(LiteRT/VAD) y Voicebox. Ningún componente `v1alpha1`/`v1alpha2` de Hub/Operator/Registry/entitlements
existe como código.

**Mapa de dependencias (objetivo):**

```
Runtime (base)  ─┐
                 ├─> Operator ─> Hub ─> Team/Org, Entitlements
Registry ────────┘                 └─> Studio ─> Packs
Seguridad/firma  ── transversal a todos
Observabilidad/ops ── transversal a todos
```

- Personal Runtime no depende de nada aguas arriba.
- Operator depende de Runtime Admin API y de crypto de firma.
- Hub depende de Operator (canal) y de emisión de entitlements.
- Team/Organization dependen de Hub y entitlements.
- Registry es consultable de forma independiente (cliente OSS).

<a id="indice-componentes"></a>
## 19. Índice de componentes y contratos

- **Especificaciones por componente:** [`docs/specs/README.md`](../specs/README.md) (A–M).
- **Contratos machine-readable:** [`docs/schemas/`](../schemas/README.md) (`v1alpha1` + `v1alpha2`).
- **Decisiones:** [`docs/adr/`](../adr/) (ADR-0001…0011).
- **Mapa de documentación canónica:** [`docs/README.md`](../README.md).
