# ADR-0001: División de responsabilidades Hub / Operator / Runtime / Registry

- **Estado:** Aceptada (diseño; sin implementación)
- **Fecha:** 2026-07-19
- **Versión de arquitectura:** `v1alpha1`
- **Relacionadas:** RFC-002, [ADR-0002](0002-signing-and-verification.md), [ADR-0004](0004-operator-enrollment-and-identity.md), [Visión de Nexus OS §5](../vision/nexus-os-vision.md)

## Contexto

Nexus Console (v0.13.8) es hoy un plano de control que ejecuta comandos privilegiados directamente
sobre cada Platform (RFC-002: `POST /_console/command`). Para pasar a un portal gestionado donde
cualquier usuario crea su instancia sin conocimientos técnicos, hace falta separar la parte hospedada
(cuentas, cuestionario, catálogo) de la parte privilegiada (aplicar cambios sobre la instancia). El
riesgo central: que el portal se convierta en un shell remoto centralizado, rompiendo los principios
de aislamiento (P5), soberanía del dato (P15) y auditoría (P12).

## Decisión

Dividir el sistema gestionado en cuatro componentes con fronteras de confianza explícitas:

1. **Nexus Hub** — plano de control hospedado. Cuentas, facturación, cuestionario, motor de blueprint,
   estado de setup, metadatos de flota, catálogo. **Nunca** datos de negocio ni memoria.
2. **Nexus Operator** — agente open-source junto a la instancia. Conexión **saliente**, reconciliación
   de estado deseado firmado, comandos de capacidad acotada, telemetría de salud. **Sin shell.**
3. **NexusOS Runtime/Platform** — plano de datos soberano. Opera sin Hub. Expone un **Runtime Admin
   API** local (autenticación fuerte) que el Operator invoca para aplicar cambios.
4. **Nexus Registry** — distribución firmada y versionada de packs; consultable con/ sin Hub.

**Migración desde Console/Platform:** la parte hospedada de Console (wizard web, catálogo, estado de
despliegue) migra conceptualmente a Hub; las operaciones privilegiadas locales migran al Operator +
Runtime Admin API. **No es una reescritura**: el código de wizard actual es base reutilizable; el
protocolo RFC-002 (HTTP + JWT firmado) es el antecedente del canal Hub↔Operator.

## Consecuencias

- **Positivas:** desacople claro de responsabilidades; el plano de datos sobrevive a caídas del Hub;
  se preserva el modo self-hosted; el patrón (agente saliente + control plane declarativo) es probado
  (kubelet, Fleet/Rancher, Fly Machines).
- **Negativas / costes:** dos superficies de despliegue en vez de una; necesidad de un protocolo de
  enrolamiento y firma (ADR-0002, ADR-0004); mayor complejidad operativa para Ironbat.
- **Invariante:** el Hub no recibe datos de negocio/memoria por defecto; toda mutación remota es
  declarativa, acotada, firmada, protegida contra replay y auditable.

## Alternativas consideradas

- **Mantener Console como único control plane con comandos directos:** rechazada; no escala a
  usuarios no técnicos y concentra privilegio remoto.
- **Hub con acceso directo a la BD de cada instancia:** rechazada; rompe P5/P15/P12.
- **Reescritura completa desde cero:** rechazada; descarta código que ya funciona.
