# Spec B: Nexus Hub — Especificación de desarrollo de la aplicación web

- **Estado:** Diseño aprobado, no implementado (TARGET-STATE salvo donde se marque ACTUAL)
- **Versión de arquitectura:** `v1alpha1` (infraestructura) + `v1alpha2` (producto)
- **Fecha:** 2026-07-19
- **Documento canónico único.** Esta es la **única especificación de desarrollo del Hub**. Consolida las
  antiguas notas de portal gestionado, setup gestionado, onboarding y sitio web. Un equipo de producto,
  diseño e ingeniería debe poder construir la aplicación web del Hub a partir de este documento sin
  recurrir a documentos en competencia.
- **Contratos:** [`entitlement`](../schemas/v1alpha2/entitlement.schema.json), [`subscription-state`](../schemas/v1alpha2/subscription-state.schema.json), [`package-download-grant`](../schemas/v1alpha2/package-download-grant.schema.json), [`edition.declaration`](../schemas/v1alpha2/edition.declaration.schema.json), [`organization-policy`](../schemas/v1alpha2/organization-policy.schema.json), [`deployment-modality`](../schemas/v1alpha2/deployment-modality.schema.json), [`nexus.blueprint`](../schemas/v1alpha1/nexus.blueprint.schema.json), [`setup.plan`](../schemas/v1alpha1/setup.plan.schema.json), [`setup.task`](../schemas/v1alpha1/setup.task.schema.json), [`desired-state`](../schemas/v1alpha1/desired-state.schema.json), [`status-report`](../schemas/v1alpha1/status-report.schema.json), [`secrets-bundle-manifest`](../schemas/v1alpha1/secrets-bundle-manifest.schema.json).
- **Relacionadas:** [arquitectura system-wide](../architecture/nexus-os-architecture.md), [visión](../vision/nexus-os-vision.md), [ADR-0001](../adr/0001-hub-operator-runtime-registry-split.md), [ADR-0003](../adr/0003-blueprint-and-setup-plan-contracts.md), [ADR-0005](../adr/0005-secrets-bundle-and-oauth.md), [ADR-0009](../adr/0009-editions-entitlements-and-subscription-degradation.md), [Spec D](d-operator-instance-lifecycle.md), [Spec E](e-registry-catalog-distribution.md), [Spec G](g-entitlements-subscriptions-degradation.md), [Spec H](h-security-trust-signing-secrets.md), [Spec K](k-cli-sdk-installer-handoff.md).

## 1. Problema y contexto

Las capacidades oficiales de Team/Organization y los paquetes premium/privados requieren un plano de
control hospedado que emita entitlements firmados, gestione cuentas, guíe la creación y el setup de
instancias, y sirva el catálogo curado. El Hub es la **cara pública de la aplicación web** del sistema
gestionado. El Hub **no** custodia datos de negocio ni memoria (principio de soberanía). Hoy no existe
como código; Nexus Console (v0.13.8) es su ancestro directo y su wizard es base reutilizable.

## 2. Objetivos

- Guiar a un usuario desde el registro hasta una instancia operativa (cuestionario → blueprint → setup →
  operación) con revisión humana en cada decisión de arquitectura, coste, permisos y riesgo.
- Emitir **entitlements firmados** (Ed25519) por capacidad, con expiry/gracia/nonce/revision.
- Publicar el **catálogo curado** y emitir **grants de descarga** de vida corta para carriles
  premium/privados; permitir navegación pública de paquetes sin login donde aplique.
- Exponer el **SubscriptionState** declarativo que gobierna la degradación graciosa.
- Generar artefactos de **handoff** (blueprint, setup plan, `SETUP.md`, bundle de secretos cifrado
  opcional) para ejecución por Operator, cowork o usuario.
- Gestionar **flota** (solo metadatos y salud), miembros, roles, actualizaciones, backups gestionados y
  soporte.

## 3. No-objetivos

- Custodiar memoria, conversaciones ni datos de negocio.
- Precios/facturación reales o elección de procesador de pago (facturación es una **abstracción**; no se
  hardcodean planes ni cifras).
- Shell remoto o control imperativo de instancias (solo estado deseado firmado).
- Marketplace público con transacciones y federación entre instancias (fuera de alcance).

## 4. Personas

| Persona | Descripción | Necesidad clave |
|---|---|---|
| **Propietario no técnico** | Individuo o dueño de negocio, ruta simple (managed) | Guía paso a paso, sin jerga, aprobar y avanzar |
| **Operador técnico (BYOC)** | Aporta su cloud, quiere soberanía | Control de infra, instalar Operator, orquestación del Hub |
| **Self-hoster / comunidad** | Control total, posiblemente offline | Handoff de artefactos, sin dependencia del Hub |
| **Admin de organización** | Gestiona miembros, roles, políticas | Invitaciones, RBAC, políticas de organización |
| **Miembro de equipo** | Usa la instancia | Acceso según rol, visibilidad de estado |
| **Explorador de catálogo** | Evalúa packs sin cuenta | Navegación pública, ver qué es premium |

## 5. Journeys de usuario

### 5.1 Común (registro → operativa)

registro/login → creación de instancia y elección de modalidad → cuestionario de descubrimiento →
generación de blueprint (recomendación de stack, 7 artefactos) → revisión/aprobación de arquitectura
(coste, permisos, riesgos) → elección de modalidad de despliegue → checklist de setup de cuentas
externas/plataformas → configuración guiada paso a paso → progreso/reanudación → selección de
agentes/áreas/packs → instancia operativa → dashboard de instancia → ciclo de vida continuo.

### 5.2 Managed
El Hub orquesta el despliegue en infraestructura de Ironbat. El **Operator es obligatorio**. El usuario
solo aprueba pasos y conecta cuentas OAuth cuando se le pide. Ejemplo:
[`blueprint.managed-real-estate.yaml`](../schemas/examples/blueprint.managed-real-estate.yaml).

### 5.3 BYOC (Bring Your Own Cloud)
El usuario conecta su cuenta cloud (Fly/AWS/GCP/on-prem). El Hub genera el plan; el **Operator** se
instala en la infraestructura del usuario y ejecuta el resto. El Operator es **opcional** pero
recomendado. Ejemplo: [`blueprint.byoc.yaml`](../schemas/examples/blueprint.byoc.yaml).

### 5.4 Self-Hosted / Offline
El Hub, si se usa, solo entrega artefactos de handoff (`SETUP.md`, `setup.plan.yaml`). **Sin Operator y
sin conexión al Hub.** La instancia opera indefinidamente en modo autónomo. Ejemplo:
[`blueprint.self-hosted-offline.yaml`](../schemas/examples/blueprint.self-hosted-offline.yaml).

### 5.5 Ciclo de vida continuo
Invitación de miembros y roles, estados de suscripción/entitlement, salud de flota, actualizaciones,
backups, soporte y offboarding/exportación (§7, §11, §16).

## 6. Handoff a asistentes (OpenClaw / cowork)

El Hub genera un fichero Markdown de handoff descargable (`SETUP.md`) para que un asistente OpenClaw o
cowork ejecute el setup. Detalle de la automatización de handoff en [Spec K](k-cli-sdk-installer-handoff.md).

- El handoff contiene: pasos ordenados con dependencias, `owner` por tarea, criterios de verificación
  (evidencia esperada: respuesta de API, hash, healthcheck) y puntos de escalado.
- **Nunca contiene secretos en texto plano.** Los secretos van por el bundle cifrado (§8) o por OAuth/
  device flow. El handoff referencia el secreto por nombre/rol, jamás su valor ([ADR-0005](../adr/0005-secrets-bundle-and-oauth.md)).
- El fichero es reproducible desde el `setup.plan.yaml` y el `nexus.blueprint.yaml`; el asistente puede
  reportar progreso de vuelta (`PATCH /v1/setup-tasks/{id}`) si está autorizado.

## 7. Flujo de secretos y claves de API

**Recolección opcional y segura. Nunca secretos en texto plano en Markdown.**

- **Opcionalidad:** el usuario puede completar el setup sin entregar secretos al Hub, usando OAuth/device
  flow o introduciendo secretos directamente en el vault local del Runtime.
- **Bundle de secretos cifrado:** cuando el usuario elige entregar secretos, el Hub genera/importa un
  `nexus.secrets.bundle` cuyo **manifiesto** ([`secrets-bundle-manifest`](../schemas/v1alpha1/secrets-bundle-manifest.schema.json))
  lleva solo referencias públicas (recipiente age/X25519, nombres de secreto), **nunca** ciphertext ni
  valores. El cifrado de sobre **age/X25519** se hace en el navegador contra la clave pública de la
  instancia.
- **Manejo local o backend seguro:** el ciphertext viaja fuera de banda hacia la instancia; el vault
  local lo descifra. Si se usa un broker OAuth gestionado (propietario), los tokens se orquestan cifrados
  y con consentimiento explícito.
- **Un solo uso:** el bundle se **invalida tras la importación** exitosa; no queda copia reutilizable en
  el Hub.
- **Redacción y auditoría:** la API nunca devuelve valores de secreto; expone flags de presencia. Toda
  emisión/importación queda en el audit log (§13). Cada referencia tiene **expiry** y puede **borrarse**.
- **Prohibición cowork:** los prompts de asistentes cowork tienen prohibido incrustar secretos.

## 8. Navegación pública de paquetes y acceso por entitlement

- Los carriles **public** y **community** se navegan **sin login** (catálogo abierto, replicable). El
  catálogo marca la visibilidad de cada pack (`public`/`community`/`verified-premium`/`private-organization`).
- Los carriles **verified-premium** y **private-organization** requieren cuenta Hub y entitlement; la
  descarga se hace vía **grant de vida corta** (un solo uso), nunca DRM. Ver [Spec E](e-registry-catalog-distribution.md)
  y [`package-access-policy`](../schemas/v1alpha2/package-access-policy.schema.json).

## 9. Arquitectura de información del producto

### 9.1 Sitemap / inventario de rutas

| Ruta | Acceso | Propósito |
|---|---|---|
| `/` | Público | Landing, propuesta de valor |
| `/catalog` | Público | Navegación de packs public/community |
| `/catalog/:pack` | Público/entitlement | Detalle de pack; premium/privado tras login |
| `/login`, `/register` | Público | Autenticación |
| `/instances` | Autenticado | Lista de instancias |
| `/instances/new` | Autenticado | Creación de instancia + modalidad |
| `/instances/:id/questionnaire` | Autenticado | Cuestionario de descubrimiento |
| `/instances/:id/blueprint` | Autenticado | Revisión/aprobación de arquitectura |
| `/instances/:id/setup` | Autenticado | Checklist y configuración guiada, progreso/reanudación |
| `/instances/:id` | Autenticado | Dashboard de instancia |
| `/instances/:id/packs` | Autenticado | Selección de agentes/áreas/packs |
| `/org/:id/members` | Admin | Invitaciones y roles |
| `/org/:id/subscription` | Admin | Estado de suscripción/entitlement |
| `/fleet` | Autenticado | Salud de flota, actualizaciones, backups |
| `/support` | Autenticado | Soporte y escalado |
| `/account`, `/export` | Autenticado | Cuenta, offboarding/exportación |

### 9.2 Navegación y responsive
Navegación primaria por instancia; navegación secundaria por sección (setup, packs, miembros, flota).
Diseño responsive mobile-first para consulta de estado; el setup guiado y la revisión de blueprint
priorizan desktop pero deben ser usables en tablet.

### 9.3 Accesibilidad, localización y voz visual
- **Accesibilidad:** objetivo WCAG 2.1 AA; navegación por teclado, foco visible, contraste, ARIA en
  estados de tarea.
- **Localización:** español como idioma canónico de documentación y primer idioma de UI; arquitectura
  i18n desde el día uno (sin strings hardcodeados).
- **Dirección visual/voz (Ironbat/Nexus):** tono directo, técnico, confiado y preciso; dark mode nativo;
  honestidad de estado (nada se sobrevende, cada capacidad marca su estado real).

## 10. Arquitectura frontend / backend (BFF)

- **Frontend:** SPA (Vite + React + Tailwind, coherente con el repo actual), `fetch` directo, dark mode
  nativo. Estado de UI por máquina de estados de setup (§12).
- **BFF / backend:** API del Hub (FastAPI, coherente con el stack actual). El BFF media entre la SPA y
  los servicios del Hub; no expone endpoints imperativos de shell.
- **Frontera:** el Hub produce estado deseado, entitlements, grants y catálogo; consume status-report del
  Operator. La ejecución sobre la instancia es del Operator/Runtime, nunca del Hub.

## 11. Modelo de organización/tenant y RBAC

- **Tenant:** `Organization` como agrupación facturable; multi-organización soportada en el modelo desde
  el día uno (UI de gestión puede llegar en P1).
- **Roles** (`organization-policy.schema.json`): `owner` (exactamente uno), `admin`, `member`,
  `readonly`, `guest`. El `owner` nunca pierde acceso (invariante de degradación).
- **Invitaciones:** en estados degradados (suspended/cancelled/expired) las `new_invitations` se fijan a
  `blocked`; en active/past_due/grace es política. Ver [Spec G](g-entitlements-subscriptions-degradation.md).

## 12. Modelo de datos del Hub y máquina de estados de setup

### 12.1 Entidades (ninguna contiene datos de negocio)

| Entidad | Propósito | Datos de negocio |
|---|---|---|
| `Account` | Cuenta de usuario del Hub | No |
| `Organization` | Agrupación facturable | No |
| `Instance` | Metadatos (nombre, modalidad, región declarada, versión) | No |
| `Blueprint` | Arquitectura recomendada (versionada) | No |
| `SetupPlan` / `SetupTask` | Plan y tareas con estado/ownership/evidencia | No |
| `Enrollment` | Registro de enrolamiento del Operator (claves, token usado) | No |
| `Package` / `PackageVersion` | Definición y versión de pack del Registry | No |
| `Installation` | Qué pack/versión está en qué instancia | No |
| `SecretReference` | Puntero a secreto (no el valor) | No |
| `Deployment` | Despliegue/actualización aplicada | No |
| `HealthSnapshot` | Telemetría de salud agregada | No |
| `AuditEvent` | Evento de auditoría del Hub | No |
| `Entitlement` / `SubscriptionState` | Capacidades firmadas y estado de suscripción | No |
| **Memoria, conversaciones, contenido de áreas** | — | **Solo Runtime** |

### 12.2 Máquina de estados de tareas de setup

Esquema: [`setup.task.schema.json`](../schemas/v1alpha1/setup.task.schema.json). Ver [ADR-0003](../adr/0003-blueprint-and-setup-plan-contracts.md).

```
not_started ─▶ waiting_user ─▶ waiting_oauth ─▶ ready ─▶ running ─▶ completed
     │              │                │            │         │
     └──────────────┴────────────────┴────────────┴─────────┴──▶ blocked
                                                             ├──▶ failed  (failure_reason obligatorio)
                                                             └──▶ skipped (decisión del usuario)
```

Cada tarea registra `owner` (`hub_automated`/`operator`/`user`/`cowork_assistant`), `prerequisites`,
`evidence` (respuesta de API, hash, healthcheck; nunca el secreto), `retry` (backoff con tope),
`rollback` y `escalation` a soporte. Una tarea bloqueada no detiene el resto si no hay dependencia
directa; el usuario ve siempre el punto exacto de su instancia. El estado del `SetupPlan` persiste: si el
usuario cancela a mitad, al volver reanuda exactamente donde lo dejó.

## 13. APIs, eventos, webhooks, idempotencia y manejo de errores

No es un OpenAPI completo; delimita la frontera Hub-Operator-Registry. Todo endpoint que muta estado
exige autenticación con la clave de esa instancia (respuestas del Operator) o sesión de usuario con rol
suficiente (acciones desde el Hub).

**Enrolamiento** ([ADR-0004](../adr/0004-operator-enrollment-and-identity.md)):
- `POST /v1/instances/{id}/enrollment-token` → token de un solo uso, vida corta.
- `POST /v1/enroll` → intercambia token por par de claves ([`enrollment.request`](../schemas/v1alpha1/enrollment.request.schema.json) → [`enrollment.response`](../schemas/v1alpha1/enrollment.response.schema.json)).

**Estado deseado** ([`desired-state`](../schemas/v1alpha1/desired-state.schema.json)):
- `GET /v1/instances/{id}/desired-state` (poll) o evento `desired_state.updated` (push WebSocket).

**Reporte de estado** ([`status-report`](../schemas/v1alpha1/status-report.schema.json)):
- `POST /v1/instances/{id}/status-report`. Evento `instance.health_changed` a dashboards internos.

**Paquetes:**
- `POST /v1/instances/{id}/packages/install` · `POST /v1/instances/{id}/packages/{id}/rollback`.
- Eventos `package.install.completed` / `package.install.failed`.

**Plan de setup:**
- `GET /v1/instances/{id}/setup-plan` · `PATCH /v1/setup-tasks/{id}` (Operator o cowork autorizado).

**Registry:**
- `GET /v1/registry/packages?area=legal&compatibility=runtime>=1.0`.
- `GET /v1/registry/packages/{id}/versions/{version}/manifest` → manifiesto firmado.

**Entitlements/suscripción:**
- `POST /v1/orgs/{id}/entitlements` (emisión firmada), `GET /v1/instances/{id}/entitlement`,
  `GET /v1/orgs/{id}/subscription-state`, `POST /v1/registry/packages/{id}/download-grant` (grant de vida
  corta).

**Idempotencia y errores:** las mutaciones aceptan `Idempotency-Key`; los reintentos del Operator son
seguros por `revision` monotónica y `nonce`. Errores tipados con código estable y mensaje sin fugas de
datos de negocio.

## 14. Requisitos funcionales

- **P0:** registro/login; creación de instancia + modalidad; cuestionario; motor de blueprint (genera 7
  artefactos: `nexus.blueprint.yaml`, `setup.plan.yaml`, `SETUP.md`, checklist humano y demás);
  máquina de estados de tareas operativa aunque la ejecución sea manual (handoff a cowork/usuario);
  navegación pública de catálogo; emisión de entitlements firmados; publicación de catálogo; emisión de
  grants; bundle de secretos cifrado opcional de un solo uso.
- **P1:** Operator conectado (enrolamiento, estado deseado firmado, telemetría); dashboard de instancia
  con salud; invitaciones y roles; revocación por `revision`; ventana de gracia offline configurable
  (0-90 días).
- **P2:** panel de flota (solo metadatos y salud); canales de actualización y staged rollout; backups
  gestionados (opcional, cifrado, consentido); auditoría de emisiones; soporte/escalado.

## 15. Requisitos no funcionales

- **Seguridad/privacidad:** frontera solo-Runtime; mTLS por instancia; claves de firma en KMS/HSM;
  break-glass auditado ([ADR-0002](../adr/0002-signing-and-verification.md)).
- **Rendimiento/SLO:** latencia baja de emisión de grant; verificación de entitlement offline 100%; el
  Hub no es dependencia de disponibilidad del plano de datos.
- **Observabilidad:** audit log dual; telemetría de flota solo agregada (ver [Spec L](l-observability-audit-ops.md)).
- **Analítica con privacidad:** métricas de producto sin contenido de negocio; sin PII innecesaria.
- **Feature flags:** capacidades tras flag por instancia; rollout gradual.

## 16. Seguridad, privacidad y modelo de amenazas

| Amenaza | Control |
|---|---|
| Shell remoto / ejecución arbitraria | No existe canal de shell; solo capacidades acotadas en `desired-state` |
| Estado deseado manipulado | Firma Ed25519 (KMS/HSM, pineada) + canonicalización + verificación 100% offline |
| Replay | `nonce` + `issued_at`/`expires_at` + `revision` monotónica |
| Robo de credencial del Operator | mTLS por instancia, credenciales de vida corta con rotación |
| Fuga de secretos | Cifrado age/X25519 en navegador, de un solo uso; OAuth preferente; prohibición en prompts cowork |
| Hub recibe datos de negocio | Frontera solo-Runtime; backups solo con consentimiento explícito y cifrado |
| Brecha multi-tenant | Aislamiento estricto por instancia; sin BD compartida de contenido |

## 17. Comportamiento ante fallo/offline y reanudación

- Si el Hub no está disponible, las instancias operan con entitlements cacheados dentro de la gracia. La
  edición Personal no depende del Hub en ningún caso.
- Setup interrumpido: el `SetupPlan` persiste; reanudación exacta.
- Pérdida de red durante el setup: los pasos completados quedan con evidencia; los pendientes se reanudan.

## 18. Testing, entornos y despliegue

- **Testing:** unit (motor de blueprint, máquina de estados), contract (validación de esquemas, ya
  cubierta por `console/tests/test_managed_platform_schemas.py`), e2e de journeys (registro→operativa),
  accesibilidad, negativos (rechazo de secretos en Markdown).
- **Entornos:** dev/staging/prod; feature flags por instancia; migraciones de contrato aditivas.
- **Despliegue:** SPA + BFF; el Hub hospedado es propietario ([ADR-0008](../adr/0008-oss-commercial-boundary-and-license.md)).

## 19. Criterios de aceptación (Given/When/Then)

- **Given** un usuario nuevo, **when** completa el cuestionario, **then** el Hub genera los 7 artefactos
  del blueprint sin intervención manual.
- **Given** un `setup.plan.yaml` + `SETUP.md` entregados a un cowork, **when** el asistente ejecuta cada
  tarea, **then** ningún secreto aparece en texto plano en su contexto.
- **Given** un `nexus.secrets.bundle`, **when** se importa con éxito, **then** se invalida y no queda
  copia reutilizable en el Hub.
- **Given** una tarea que supera el máximo de reintentos, **when** falla, **then** pasa a `failed` con
  motivo y opción de escalar.
- **Given** un setup cancelado a mitad, **when** el usuario vuelve, **then** encuentra su plan
  exactamente donde lo dejó.
- **Given** una cuenta suscrita, **when** el Hub emite un entitlement Team, **then** está firmado Ed25519
  con `trust_domain` y es verificable offline.
- **Given** un pack premium y un usuario con entitlement, **when** lo solicita, **then** el Hub emite un
  grant de vida corta (un solo uso), no un artefacto DRM.
- **Given** un pack public, **when** un visitante sin cuenta lo abre, **then** puede navegarlo y
  replicarlo sin login.
- **Given** un Hub caído, **when** el Operator arranca, **then** usa el entitlement cacheado dentro de la
  gracia sin degradar.

## 20. Métricas de éxito

% de usuarios que completan cuestionario→blueprint; % de instancias blueprint→operativa sin soporte
humano; tiempo medio registro→primer Jarvis; % de tareas en `failed` sin reintento exitoso; reparto de
modalidades; tickets de soporte por instancia en el primer setup; cero fugas de datos de negocio al Hub;
verificación offline de entitlement 100%.

## 21. Dependencias

[Spec D](d-operator-instance-lifecycle.md) (Operator), [Spec E](e-registry-catalog-distribution.md)
(Registry), [Spec G](g-entitlements-subscriptions-degradation.md) (entitlements/degradación),
[Spec H](h-security-trust-signing-secrets.md) (crypto/secretos), [Spec K](k-cli-sdk-installer-handoff.md)
(handoff/instalador), [Spec L](l-observability-audit-ops.md) (observabilidad/backups).

## 22. Migración y versionado

Reutiliza `desired-state` y crypto de `v1alpha1` por `$id` absoluto; añade contratos `v1alpha2`. Los
outputs actuales del wizard/handoff (`nexus.instance.yaml`, `SETUP.md`) son base directa del
blueprint/plan; los despliegues Fly actuales siguen funcionando sin Operator. Ver
[migración y compatibilidad](../architecture/migration-and-compatibility.md).

## 23. Estado actual vs. objetivo

**Actual:** no existe Hub como código; Nexus Console (wizard de 6 pasos, deployer, instance registry,
secret manager por instancia) es el ancestro reutilizable. **Objetivo:** la aplicación web del Hub
descrita aquí. No se afirma que ninguna funcionalidad TARGET-STATE exista hoy.

## 24. Identificadores canónicos y nomenclatura

El Hub es el **emisor** de `OrganizationId`/`UserRef` y debe emitirlos **lowercase-canónicos**
(`^org_[a-z0-9]{4,40}$` / `^usr_[a-z0-9]{4,40}$`), normalizándolos a minúsculas antes de firmar
entitlements/grants; un id con mayúsculas se rechaza por contrato
([common.defs](../schemas/v1alpha2/common.defs.schema.json)). `Nexus OS` es el nombre de producto de
visualización; los identificadores técnicos (`NexusOS`, `nexus`, `$id` de esquema) se preservan sin
cambios (ver [glosario §nomenclatura](../architecture/glossary.md#nomenclatura)).

## 25. Riesgos y preguntas abiertas

- Proveedor de KMS/HSM definitivo; política de rotación de `trust_domain`; región de datos por defecto.
- Alcance del broker OAuth gestionado vs. introducción directa de secretos en el vault local.
- Profundidad de la UI multi-organización en P1.
