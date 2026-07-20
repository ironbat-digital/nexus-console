# Changelog de documentación y contratos de NexusOS

Registra cambios en la documentación de arquitectura/producto y en los contratos machine-readable
(`docs/schemas/`). No sigue la versión del paquete `nexus-console` (SemVer del código); los contratos se
versionan por separado (`x-nexus-contract-version`). Formato inspirado en Keep a Changelog.

## [re-3d-capture] - 2026-07-20 — Add-on de sector: Real Estate 3D Capture (PoC)

**Estado:** solo documentación, contratos y ejemplos (TARGET-STATE / PoC). **No** cambia ningún esquema de
producción, `$id` ni semántica de contrato. **No** es un componente central A-M; es una capacidad de
sector-pack opcional.

### Añadido

- **Spec de add-on de sector:** [`specs/sector-packs/real-estate-3d-capture.md`](specs/sector-packs/real-estate-3d-capture.md),
  que envuelve el proyecto OSS LingBot Map como sidecar GPU local, reutilizando el patrón de la
  [Spec M](specs/m-local-inference-voice-edge.md) y componiendo el pack `real-estate-agency`.
- **Manifiestos de pack (fixtures válidos):** core OSS público
  [`pack.real-estate-3d-capture-core.yaml`](schemas/examples/pack.real-estate-3d-capture-core.yaml) (sin
  entitlement, espejable) y add-on premium verificado
  [`pack.real-estate-3d-capture.yaml`](schemas/examples/pack.real-estate-3d-capture.yaml) (entitlement
  `real_estate_3d_capture`).
- **Políticas de acceso (`v1alpha2`):**
  [core](schemas/examples/package-access-policy.real-estate-3d-capture-core.example.json) (public,
  mirrorable) y [premium](schemas/examples/package-access-policy.real-estate-3d-capture.example.json)
  (verified-premium, grant de un solo uso).
- **Ejemplo compañero desired-state:**
  [`desired-state.real-estate-3d-capture.example.json`](schemas/examples/desired-state.real-estate-3d-capture.example.json),
  instalación de ambos packs vía intents acotados (sin secretos, solo referencias).
- **Fixtures negativos:** core en carril público que exige entitlement, y premium sin entitlement; ambos
  deben ser rechazados por `nexus.pack.schema.json`.
- **Índices:** `docs/README.md` y `docs/specs/README.md` ganan una sección de add-ons de sector.

### Sin cambios (invariantes preservadas)

- Ningún esquema de producción se extiende. Las brechas de contrato (configuración de sidecar, provenance
  de pesos, extensión de UI, tarea de retención) se documentan como **preguntas abiertas** en la spec del
  add-on, no como cambios de contrato. El repositorio mixto permanece MIT hasta la auditoría legal.

## [docs-reorg] - 2026-07-19 — Reorganización canónica de la documentación

**Estado:** solo documentación. No cambia ningún contrato, `$id` ni semántica de esquema.

### Añadido

- **Visión canónica única:** [`vision/nexus-os-vision.md`](vision/nexus-os-vision.md), que unifica las dos
  visiones previas (Portal Gestionado `v1alpha1` + Personal + Hub `v1alpha2`).
- **Arquitectura canónica única system-wide:** [`architecture/nexus-os-architecture.md`](architecture/nexus-os-architecture.md).
- **Especificación de desarrollo del Hub consolidada:** [`specs/b-nexus-hub.md`](specs/b-nexus-hub.md)
  reescrita como **único** documento de desarrollo del Hub (journeys, setup, secretos, catálogo,
  frontend/BFF, RBAC, API/eventos, seguridad, testing, criterios de aceptación).
- **Nuevas specs de componente:** [Spec K](specs/k-cli-sdk-installer-handoff.md) (CLI/SDK/instalador/
  handoff), [Spec L](specs/l-observability-audit-ops.md) (observabilidad/auditoría/ops/backup/soporte) y
  [Spec M](specs/m-local-inference-voice-edge.md) (inferencia local/voz/edge, ownership canónico).
- **ADR:** [ADR-0011](adr/0011-documentation-architecture.md) (arquitectura de documentación y canonicidad).
- **Nota de nomenclatura** en el [glosario](architecture/glossary.md#nomenclatura): `Nexus OS` es el
  nombre de visualización; `NexusOS`, `nexus`, `$id` de esquema y símbolos son identificadores estables.
- **Guarda de test:** unicidad de documentos canónicos y stubs de redirección en
  `console/tests/test_managed_platform_schemas.py`.

### Cambiado

- **Índices:** [`docs/README.md`](README.md) reescrito como mapa canónico (documento, alcance, estado,
  superados) y [`specs/README.md`](specs/README.md) ampliado con k/l/m.
- **Enlaces internos** de ADRs y docs de soporte reapuntados a la visión y arquitectura canónicas.

### Superado (conservado como redirección, no borrado)

- [`vision/nexus-os-vision-managed-portal.md`](vision/nexus-os-vision-managed-portal.md) y
  [`vision/nexus-os-vision-personal-hub-subscription.md`](vision/nexus-os-vision-personal-hub-subscription.md)
  → [`vision/nexus-os-vision.md`](vision/nexus-os-vision.md).
- [`architecture/managed-platform-architecture.md`](architecture/managed-platform-architecture.md) →
  [`architecture/nexus-os-architecture.md`](architecture/nexus-os-architecture.md) + [`specs/b-nexus-hub.md`](specs/b-nexus-hub.md).

## [v1alpha2] - 2026-07-19 — Capa de producto Personal + Hub por suscripción

**Estado:** diseño aprobado, no implementado (TARGET-STATE). Aditivo y backward compatible sobre
`v1alpha1`.

### Añadido

- **Visión:** [Personal + Hub por suscripción](vision/nexus-os-vision-personal-hub-subscription.md)
  (ediciones, audiencias, propuesta de valor, fronteras, monetización por capacidad, cuatro carriles de
  paquete, modalidades de despliegue, ciclo de vida ante expiración, promesa OSS, no-objetivos).
- **Especificaciones (a–j):** [`docs/specs/`](specs/README.md) — Personal Runtime, Hub, Team/Org,
  Operator/ciclo de vida, Registry/distribución, modelo de paquetes/artefactos, entitlements/suscripción/
  degradación, seguridad/firma/secretos, Studio y modalidades de despliegue.
- **ADR:** [ADR-0009](adr/0009-editions-entitlements-and-subscription-degradation.md) (ediciones,
  entitlements de capacidad, degradación graciosa) y
  [ADR-0010](adr/0010-edition-vs-deployment-modality.md) (edición ortogonal a modalidad).
- **Esquemas `v1alpha2`** ([`docs/schemas/v1alpha2/`](schemas/v1alpha2/)): `common.defs`,
  `edition.declaration`, `entitlement`, `subscription-state`, `organization-policy`,
  `package-access-policy`, `package-download-grant`, `deployment-modality`.
- **Fixtures:** 17 ejemplos válidos `v1alpha2` y 15 negativos en [`examples/invalid/`](schemas/examples/invalid/)
  con su índice; `examples/index.json` gana `contract_versions` y el campo `version` por caso. Cada
  negativo falla por **una sola** invariante (fixtures mínimos).
- **Tests:** `console/tests/test_managed_platform_schemas.py` valida ambas versiones, resuelve `$ref`
  cross-version por `$id`, rechaza los fixtures negativos y comprueba invariantes de producto (firma
  Ed25519, anti-replay, preservación del owner/exportación, pausa-no-borrado, mirrorabilidad pública,
  entitlements premium, managed≠personal, cardinalidad de owner, acoplamiento edición/source,
  organization_id por edición, grant de un solo uso).

### Corregido (endurecimiento de invariantes de contrato)

- **`edition.declaration`:** el conditional estaba **inerte** (apuntaba a `spec.edition`, inexistente).
  Movido a nivel raíz sobre `metadata.edition`: `personal_base` fuerza edición `personal` y prohíbe
  `entitlement_ref`; `verified_entitlement`/`cached_entitlement` exigen `entitlement_ref` y edición
  team/organization.
- **`organization-policy`:** se exige **exactamente un owner** (`contains`/`minContains`/`maxContains`);
  cero o dos owners se rechazan.
- **`package-access-policy`:** las lanes public/community **requieren** `mirrorable`/`requires_hub_account`/
  `distribution` (no basta con que estén ausentes); las restringidas fijan `mirrorable:false` y
  `requires_hub_account:true` (un pack con grant no puede anunciarse como replicable sin cuenta).
- **`common.defs.OrganizationId`/`UserRef`:** ahora lowercase-canónicos (`^org_[a-z0-9]{4,40}$`) para que
  un `org_id` viaje sin cambios dentro de un `PackageScope` `private-organization:<org_id>`.
- **`entitlement`:** `organization_id` es obligatorio para team/organization y prohibido para personal.
- **`package-download-grant`:** `max_uses` fijado a `1` (un solo uso por construcción) y `scope`
  restringido a lanes premium/privadas.
- **`deployment-modality`:** el modo `managed` **requiere** `managed_by`.
- **`nexus.pack` (`v1alpha1`):** las lanes OSS explícitas (public/community) prohíben
  `required_entitlements`; `publisher.verification` reconcilia su vocabulario con v1alpha2 añadiendo
  `unverified` (aditivo).
- **Docs:** cabeceras de versión de `migration-and-compatibility` y ADR-0008 actualizadas; Spec H asigna
  las invariantes de campo cruzado (enlace de clave, orden temporal, anti-replay) al Entitlement Verifier
  en runtime y resuelve la rotación de claves con un keyring por `trust_domain` con solapamiento.
- **`edition.declaration`:** `personal_base` fija `subscription_state` a `active` cuando está presente
  (una instancia Personal no tiene suscripción que pueda degradarse); ausente sigue siendo válido. Nuevo
  fixture negativo `edition.personal-base-degraded.json`.
- **`subscription-state`:** `new_invitations` se fija a `blocked` **solo** en suspended/cancelled/expired;
  en active/past_due/grace es política (no fijado), con cobertura de regresión que documenta el porqué.
- **`package-download-grant`:** `max_uses` pasa a ser **obligatorio** (además de `const 1`) para que el
  carácter de un solo uso sea auditable en el propio documento, sin depender de un default implícito.
- **Fixtures negativos mínimos:** `entitlement.missing-nonce` (añade `organization_id` válido) y
  `entitlement.wrong-algorithm` (`key_custody: kms`) vuelven a fallar por **una sola** razón.
- **Normalización de identificadores documentada** en Hub (Spec B), Registry (Spec E), modelo de paquete
  (Spec F), migración y glosario: `OrganizationId`/`UserRef` se normalizan en el borde de **emisión**
  (Hub), nunca en el de consumo.

### Cambiado

- **`nexus.pack.schema.json` (`v1alpha1`)**, extensión **aditiva**: `publisher.verification` añade
  `official`; nuevos opcionales `metadata.visibility`, `metadata.commercial_terms_ref`,
  `spec.required_entitlements`; conditional que exige entitlements para visibilidad premium/privada. Los
  packs y ejemplos existentes siguen validando.
- **ADR revisadas:** 0006 (visibilidad/entitlements de pack), 0007 (cadencia de actualización como efecto
  de suscripción + políticas de organización), 0008 (Team Capability Pack propietario + Entitlement
  Verifier OSS).
- **Índices y guías:** `docs/README.md`, `docs/schemas/README.md`, `docs/architecture/glossary.md`
  (sección `v1alpha2`), `docs/architecture/migration-and-compatibility.md` (transición
  `v1alpha1`→`v1alpha2` y política de downgrade), `docs/architecture/product-oss-boundary.md` (nota de
  producto por capacidad).

### Sin cambios (invariantes preservadas)

- Nada de seguridad, exportación o portabilidad se retira del OSS. La edición Personal es libre y
  gratuita, sin Hub. No se hardcodean precios ni planes. El repositorio mixto **permanece MIT** hasta la
  auditoría legal ([ADR-0008](adr/0008-oss-commercial-boundary-and-license.md)).

## [v1alpha1] - 2026-07-19 — Portal Gestionado (línea base)

- Arquitectura de cuatro partes (Hub/Operator/Runtime/Registry), ADR-0001..0008, esquemas `v1alpha1` y
  fixtures. Ver [Visión del Portal Gestionado](vision/nexus-os-vision-managed-portal.md).
