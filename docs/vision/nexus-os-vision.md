# Visión de Nexus OS

- **Estado:** Aprobado como dirección de producto y arquitectura · diseño, no implementado (TARGET-STATE salvo donde se marque ACTUAL)
- **Versión de arquitectura:** `v1alpha1` (infraestructura de cuatro partes) + `v1alpha2` (capa de producto Personal + Hub, aditiva)
- **Fecha:** 2026-07-19
- **Autor:** Ironbat Digital LLC
- **Reconciliado con:** `main` (Console v0.13.8), RFC-002 (Protocolo Console ↔ Platform), catálogo de agentes/áreas, ecosystem registry, esquemas `v1alpha1`/`v1alpha2`.
- **Documento canónico único.** Este documento sustituye y unifica las dos visiones previas: la extensión de Portal Gestionado (`v1alpha1`) y la de Personal + Hub por suscripción (`v1alpha2`). Ambos archivos antiguos quedan como stubs superados que redirigen aquí.

> **Nota de nomenclatura (normativa).** `Nexus OS` es el **nombre de producto canónico de visualización**
> en prosa, títulos y material de cara al usuario. La nomenclatura puede revisarse más adelante **sin
> cambiar ningún contrato de arquitectura**. Los **identificadores técnicos estables** se preservan tal
> cual: `NexusOS` (símbolo compacto heredado), `nexus` (namespaces, prefijos de artefacto como
> `nexus.pack.yaml`), los `$id` de esquema (`.../schemas/v1alphaN/...`), nombres de repositorio, paquetes,
> APIs y símbolos de código. Ninguno de esos identificadores se renombra para insertar un espacio. Ver la
> [nota de terminología del glosario](../architecture/glossary.md#nomenclatura).

> **Canonicidad respecto a `ironbat-jarvis`.** La Visión histórica de Nexus OS (`docs/vision.md`,
> RFC-001) vive en el repositorio `ironbat-jarvis` (Nexus Platform). Este documento es la **visión
> canónica operativa del plano de control y de la capa de producto**, escrita en `nexus-console` porque
> es aquí donde se preparan contratos y esquemas. Un PR compañero debe incorporar este delta a la visión
> de `ironbat-jarvis`; hasta entonces, este es el documento autoritativo para todo lo relativo a Hub,
> Operator, Registry, ediciones, entitlements y suscripción.

---

## 1. Misión

Dar a cualquier persona u organización un sistema operativo de agentes de IA **soberano, verificable y
componible**: instalable gratis para un único propietario, y ampliable con capacidades oficiales de
equipo, organización y catálogo curado mediante una suscripción al Nexus Hub. El valor se cobra por
**conveniencia, curaduría, operación y confianza**, nunca por soberanía, seguridad ni portabilidad
básicas.

## 2. Problema

Montar un stack de agentes útil hoy exige integrar modelos, memoria, áreas de negocio, secretos,
despliegue y actualizaciones a mano. Las soluciones gestionadas atan al usuario (datos rehenes, DRM,
shell remoto), y las OSS puras dejan toda la operación y la curaduría en manos del usuario. Nexus OS
resuelve ambos extremos: un núcleo OSS que funciona sin conexión y un plano de control opcional que
automatiza lo tedioso sin apropiarse de los datos.

## 3. Usuarios objetivo

| Segmento | Necesidad | Edición típica |
|---|---|---|
| Individuo, desarrollador, comunidad | Runtime completo, sin cuenta, self-hosted | Personal |
| Equipos pequeños y profesionales | Multiusuario, roles, packs premium, flota | Team |
| Organizaciones y verticales | Políticas de organización, packs privados, gobernanza | Organization |

## 4. Estado actual vs. estado objetivo

Distinción **normativa** en todo el conjunto documental: nada etiquetado TARGET-STATE existe hoy como
código.

| Capa | ESTADO ACTUAL (v0.13.8, implementado) | ESTADO OBJETIVO (diseño aprobado, no implementado) |
|---|---|---|
| Control | **Nexus Console**: wizard de 6 pasos, deployer (Docker/Fly/K8s), instance registry, secret manager por instancia, agent factory, Jarvis-Console. Habla con Platform por HTTP + JWT firmado (RFC-002). | **Nexus Hub** (`v1alpha1`): app web multi-cuenta con cuestionario, motor de blueprint, estado de setup, metadatos de flota, catálogo; emisor de entitlements (`v1alpha2`). |
| Reconciliación | Console ejecuta comandos privilegiados directamente (`_console/command`). | **Nexus Operator** (`v1alpha1`): agente OSS, conexión saliente, reconcilia estado deseado firmado, sin shell arbitrario. |
| Datos | **Nexus Platform**: Jarvis, espacios, áreas, agentes, memoria, usuarios. | **Nexus OS Runtime/Platform** (`v1alpha1`): mismo plano de datos soberano; opera sin Hub. |
| Distribución | `agent_templates/` en el repo + ecosystem registry. | **Nexus Registry** (`v1alpha1`): catálogo firmado y versionado de packs. |
| Edición | No hay concepto de edición. | **Personal / Team / Organization** (`v1alpha2`), eje declarado, ortogonal a la modalidad de despliegue. |
| Habilitación | No hay habilitación por capacidad. | **Entitlements** firmados (Ed25519), verificables offline, por capacidad, nunca por plan ni precio (`v1alpha2`). |
| Suscripción | No existe. | **SubscriptionState** declarativo con degradación graciosa (`v1alpha2`). |
| Acceso a paquetes | Todo abierto. | Cuatro carriles: public/community (OSS, sin cuenta) y verified-premium/private-organization (entitlement + grant) (`v1alpha2`). |

## 5. Arquitectura de cuatro partes (`v1alpha1`)

Cara del sistema gestionado, con fronteras de confianza explícitas (ver
[ADR-0001](../adr/0001-hub-operator-runtime-registry-split.md) y la
[especificación de arquitectura](../architecture/nexus-os-architecture.md)):

```
Usuario ──> Nexus Hub (registro, cuestionario, blueprint, entitlements, catálogo)
                │  (estado deseado firmado, vía conexión saliente del Operator)
                ▼
        Nexus Operator (junto a la instancia, OSS, sin shell)
                │  (aplica cambios acotados, instala packs, reporta salud)
                ▼
   Nexus OS Runtime/Platform (Jarvis, áreas, agentes, memoria, usuarios)
                │  (consulta packs firmados)
                ▼
        Nexus Registry (catálogo firmado y versionado)
```

- **Nexus Hub:** plano de control hospedado. Cuentas, cuestionario, blueprint, estado de setup,
  metadatos de flota, catálogo y emisión de entitlements. **No** custodia memoria, conversaciones ni
  datos de negocio.
- **Nexus Operator:** agente OSS junto a cada instancia. Conexión **saliente**; reconcilia estado
  deseado firmado; instala packs firmados; reporta salud. **Sin shell arbitrario.**
- **Nexus OS Runtime/Platform:** plano de datos soberano. Jarvis, espacios, áreas, agentes, memoria,
  usuarios, vault local. **Funciona sin Hub.**
- **Nexus Registry:** catálogo versionado de packs, consultable con o sin Hub.

## 6. Ediciones y audiencias (`v1alpha2`)

| Edición | Para quién | Capacidades típicas (cualitativo) | Requiere Hub |
|---|---|---|---|
| **Personal** | Cualquier individuo, comunidad, self-hosted | Un único propietario. Runtime completo, áreas, agentes, memoria, packs public/community, verificación de firmas, exportación total. | No |
| **Team** | Equipos pequeños y profesionales | Multiusuario, roles, colaboración, packs premium, actualizaciones de flota. | Sí (suscripción) |
| **Organization** | Organizaciones y verticales | Todo lo de Team más políticas de organización, packs privados, gobernanza avanzada. | Sí (suscripción) |

La edición es un **eje declarado** (`edition.declaration.schema.json`). Su `source` puede ser
`personal_base` (base libre, sin Hub), `verified_entitlement` (entitlement firmado vigente) o
`cached_entitlement` (entitlement en ventana de gracia offline). Personal no requiere entitlement ni
conexión.

## 7. Edición Personal open-source

Cualquiera puede instalar una edición **Personal libre y gratuita** de Nexus OS para un único
propietario. Runtime completo, áreas, agentes, memoria, packs public/community, verificación de firmas y
exportación total, sin Hub y sin login. Es la base OSS del producto y permanece gratuita
indefinidamente.

## 8. Suscripción al Hub y capacidades de Team/Organization

Las capacidades oficiales multiusuario, de equipo y de organización, junto con los paquetes premium y
privados, se habilitan mediante una **suscripción al Nexus Hub**. La suscripción se representa como
**entitlements firmados verificables localmente** (`entitlement.schema.json`), no como control remoto ni
DRM. Team/Organization operan offline dentro de la ventana de gracia usando un entitlement cacheado. Las
capacidades se expresan por id estable (`team_collaboration`, `fleet_management`, `premium_pack_access`,
...), nunca por nombre de plan ni precio.

## 9. Acceso a paquetes: público, comunidad, premium y privado

| Carril | Cuenta Hub | Replicable (mirror) | Distribución | Entitlement |
|---|---|---|---|---|
| **public** | No | Sí | Descarga directa | No |
| **community** | No | Sí | Descarga directa | No |
| **verified-premium** | Sí | No | Grant de vida corta | Sí (>=1) |
| **private-organization** | Sí | No | Grant de vida corta | Sí (>=1) |

Los carriles public y community son **OSS, replicables sin cuenta Hub y de descarga directa**. Premium y
privados usan **metadatos firmados + grants de descarga de vida corta** (`package-download-grant`),
**nunca DRM**. Un fork puede replicar libremente los carriles abiertos.

## 10. Modalidades de despliegue (ortogonales a la edición)

La **modalidad** (`self_hosted` / `byoc` / `managed`) es **independiente** de la edición
(`deployment-modality.schema.json`). Personal puede ser self-hosted; Team puede ser BYOC o managed. La
**única** combinación rechazada por contrato es **managed + personal**: la operación gestionada por
Ironbat presupone edición Team/Organization. Ver [ADR-0010](../adr/0010-edition-vs-deployment-modality.md).

## 11. Principios de confianza (invariantes)

- **Soberanía del dato:** el Hub nunca recibe datos de negocio ni memoria por defecto.
- **Aislamiento fuerte** por instancia también dentro del Hub multi-tenant; sin BD compartida de
  contenido.
- **Auditoría dual:** toda orden aplicada queda en un log auditable en Hub **y** en la instancia.
- **Reversibilidad:** blueprints versionados, packs con rollback obligatorio, migración opt-in.
- **Sin shell remoto:** solo estado deseado firmado con capacidades acotadas.
- **Sin datos rehenes:** el propietario conserva acceso y exportación en todo estado de suscripción.
- **Agnosticismo de modelo:** el blueprint elige proveedores por instancia; nada se fuerza.
- **Operación self-hosted:** `docker compose up` sigue existiendo intacto; el Operator es opcional.

## 12. Propuesta de valor y foso (moat)

El foso de Ironbat es **conveniencia, curaduría, actualizaciones, compatibilidad, operación de flota,
soporte, confianza y efectos de red**, no el DRM ni restricciones anti-fork. El forking del OSS es
**explícitamente aceptado**: un fork puede reconstruir capacidades libres, pero no obtiene la curaduría
verificada, el catálogo oficial, las actualizaciones coordinadas ni el soporte con SLA. Se cobra por
comodidad operativa y confianza, nunca por soberanía ni seguridad básica.

## 13. Principios de monetización y fronteras

- **Precios no decididos:** no se fija ninguna cifra ni nombre de plan en código, esquemas ni docs. La
  facturación es una **abstracción**; los entitlements se expresan por capacidad.
- **La edición Personal es libre y gratuita indefinidamente.**
- **Nunca se retiene fuera del OSS** nada de seguridad, exportación o portabilidad.
- El coste de los servicios gestionados escala con volumen de uso, número de usuarios y nivel de
  soporte, no con funcionalidades de soberanía. Ver [frontera OSS/comercial](../architecture/product-oss-boundary.md).

## 14. Ciclo de vida ante expiración (degradación graciosa)

**Nunca se retienen los datos como rehén.** En cualquier estado de suscripción
(`subscription-state.schema.json`):

- **El propietario conserva acceso siempre** (`owner_access` fijado a `preserved`).
- **La exportación total está siempre disponible** (`export_available` fijado a `true`).
- Al expirar/suspender/cancelar: los **usuarios adicionales pasan a solo lectura**, los **agentes
  premium y las tareas programadas se PAUSAN (no se eliminan)** y se reactivan al renovar. Las
  **capacidades Personal continúan**.
- **No hay eliminación de datos** en ningún estado. Ver [ADR-0009](../adr/0009-editions-entitlements-and-subscription-degradation.md).

## 15. Licencia: estado actual vs objetivo

El modelo de **licencia por componente** está aprobado ([ADR-0008](../adr/0008-oss-commercial-boundary-and-license.md)):
Apache-2.0 (tras auditoría legal) para Runtime, Operator, CLI, SDK, contratos/esquemas e instaladores;
**propietario** para el Hub y el **Team Capability Pack**. El repositorio mixto actual **sigue siendo
MIT** hasta completar la auditoría de titularidad/contribución. **No se afirma que las licencias ya
hayan cambiado.**

## 16. Estrategia por fases (roadmap)

| Fase | Contenido | Objetivo |
|---|---|---|
| **P0 (MVP)** | Cuestionario + motor de Blueprint en el Hub; generación de artefactos y checklist; handoff manual (cowork o usuario ejecuta sin Operator); máquina de estados de tareas operativa | Validar cuestionario→blueprint y handoff a cowork, sin control remoto |
| **P1 (Operator)** | Operator OSS: enrolamiento, conexión saliente, aplicación de estado deseado firmado, comandos acotados, telemetría | Automatizar lo que en P0 era manual |
| **P2 (Registry y packs)** | Registry con `nexus.pack.yaml`, ciclo de vida completo (instalar, validar, activar, rollback, overlays) | Extender instancias con contenido seguro y versionado |
| **P3 (Flota gestionada)** | Canales, matriz de compatibilidad, staged rollout, aprobación de críticos a escala de flota | Cerrar la operación de flota sin perder control |

## 17. No-objetivos (explícitos)

No se implementan ni se especifican como existentes: precios de facturación, integración de pago real,
acceso a shell remoto, DRM, eliminación de datos ante expiración, federación entre instancias,
marketplace público con transacciones, ni restricciones ocultas sobre la edición Personal OSS. Las
capacidades de runtime aquí descritas son **especificación**, no implementación; la entrega es por fases.

## 18. Terminología y especificaciones

Los términos formales (Hub, Operator, Runtime, Registry, Instance, Blueprint, SetupPlan/Task, Area,
Agent, Skull/Agent Cognition Profile, Sidecar, Flow, Pack, Overlay, Desired State, Installation, Edition,
Entitlement, Capability, SubscriptionState, Package Visibility, Download Grant, Deployment Modality,
Organization Policy) se definen en el [glosario](../architecture/glossary.md). La arquitectura
system-wide está en la [especificación de arquitectura](../architecture/nexus-os-architecture.md) y las
especificaciones por componente, listas para implementar, en [`docs/specs/`](../specs/README.md). El
mapa completo de documentación canónica está en [`docs/README.md`](../README.md).
