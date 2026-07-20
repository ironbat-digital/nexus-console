# ADR-0010: Separación entre edición y modalidad de despliegue

- **Estado:** Aceptada (contrato de producto `v1alpha2`)
- **Fecha:** 2026-07-19
- **Versión de arquitectura:** `v1alpha2`
- **Relacionadas:** [ADR-0009](0009-editions-entitlements-and-subscription-degradation.md), [Spec J](../specs/j-deployment-modalities.md), [Visión de Nexus OS §10](../vision/nexus-os-vision.md)

## Contexto

La [Visión de Nexus OS §10](../vision/nexus-os-vision.md) define tres modalidades de
despliegue (self-hosted, BYOC, managed). El nuevo modelo de producto define tres ediciones (Personal,
Team, Organization). Confundir ambos ejes llevaría a suponer, por ejemplo, que "managed" equivale a un
plan concreto o que Personal no puede autohospedarse. Hace falta fijar que son **ejes ortogonales**.

## Decisión

- **La edición y la modalidad son ejes independientes.** `deployment-modality.schema.json` declara
  `modality` (`self_hosted | byoc | managed`) y `edition` por separado, más `operator`
  (`required|optional|absent`), `managed_by` (`owner|ironbat`) y `data_region`.
- **Combinaciones válidas:** Personal self-hosted, Team BYOC, Team managed, Organization BYOC/managed,
  etc. Cambiar de modalidad no altera la edición ni migra datos.
- **Única combinación rechazada por contrato: `managed` + `personal`.** La operación gestionada por
  Ironbat presupone edición Team/Organization. Conditionals del esquema:
  - `managed` => `operator: required`, `managed_by: ironbat`, `edition` en {team, organization}.
  - `self_hosted` => `operator: absent`, `managed_by: owner`.
  - `byoc` => `managed_by: owner`.

## Consecuencias

- Se evita acoplar soberanía (dónde corre) con capacidad de producto (qué edición). Personal siempre
  puede autohospedarse; Team puede ser BYOC o managed.
- Coste: un contrato adicional y su validación; claridad a cambio.

## Alternativas consideradas

- **Un solo eje "plan = despliegue":** rechazado; mezcla conceptos y contradice la soberanía.
- **Permitir managed+personal:** rechazado; no hay caso de negocio y confunde el modelo (Personal es
  autogestionado por definición).
