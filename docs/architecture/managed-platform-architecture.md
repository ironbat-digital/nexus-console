# [SUPERADO] Especificación de arquitectura — Portal Gestionado de Nexus OS

> **Documento superado (no borrado).** Se ha dividido entre la **especificación de arquitectura
> system-wide** y la **especificación de desarrollo del Hub**. Este archivo se conserva como redirección
> para no romper enlaces entrantes ni historia.
>
> - Arquitectura system-wide: [**Especificación de arquitectura de Nexus OS**](nexus-os-architecture.md).
> - Aplicación web del Hub (journeys, setup, modelo de datos, API): [**Spec B: Nexus Hub**](../specs/b-nexus-hub.md).

- **Estado:** SUPERADO por [`nexus-os-architecture.md`](nexus-os-architecture.md) y [`../specs/b-nexus-hub.md`](../specs/b-nexus-hub.md) el 2026-07-19.
- **Motivo:** eliminación de especificaciones de arquitectura en competencia. Había solapamiento entre la
  arquitectura del portal y las necesidades de desarrollo del Hub; ahora hay una sola arquitectura
  system-wide y una sola spec de desarrollo del Hub.

## Dónde está ahora cada sección

- Contexto del sistema, fronteras de confianza, planos, reconciliación, entitlements, secuencias,
  dependencias → [arquitectura system-wide](nexus-os-architecture.md).
- Journeys de usuario, máquina de estados de setup, modelo de datos del Hub, contratos de API/eventos,
  amenazas del Hub, roadmap y MVP → [Spec B: Hub (app web)](../specs/b-nexus-hub.md).
- Ciclo de vida de paquetes → [arquitectura §8](nexus-os-architecture.md) y [Spec E](../specs/e-registry-catalog-distribution.md).
- Migración → [migración y compatibilidad](migration-and-compatibility.md).
- Observabilidad/auditoría/DR → [Spec L](../specs/l-observability-audit-ops.md).

<a id="origen"></a>
<a id="state-machine"></a>
<a id="migration"></a>
<a id="roadmap"></a>

> Anclajes históricos conservados. La máquina de estados de setup está ahora en la
> [Spec B §12.2](../specs/b-nexus-hub.md); la migración en [migración y compatibilidad](migration-and-compatibility.md);
> el roadmap en la [Visión §16](../vision/nexus-os-vision.md) y la [Spec B §14](../specs/b-nexus-hub.md).
