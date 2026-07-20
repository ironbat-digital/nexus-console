# ADR-0003: Contratos versionados `nexus.blueprint.yaml` y `setup.plan.yaml`

- **Estado:** Aceptada (contrato `v1alpha1`)
- **Fecha:** 2026-07-19
- **Versión de arquitectura:** `v1alpha1`
- **Relacionadas:** esquemas [`nexus.blueprint`](../schemas/v1alpha1/nexus.blueprint.schema.json), [`setup.plan`](../schemas/v1alpha1/setup.plan.schema.json), [`setup.task`](../schemas/v1alpha1/setup.task.schema.json); [ADR-0007](0007-update-channels-and-rollout.md)

## Contexto

El cuestionario del Hub debe producir artefactos deterministas, versionados y consumibles tanto por
humanos como por el Operator o un asistente cowork. Hoy el wizard de Console emite
`nexus.instance.yaml` (`apiVersion: nexus.v0.6`, estilo K8s: `apiVersion/kind/metadata/spec`). Los
nuevos contratos deben ser coherentes con ese estilo.

## Decisión

- **`nexus.blueprint.yaml`** (`kind: Blueprint`): arquitectura recomendada (modalidad, región,
  áreas, agentes, stack LLM, memoria, permisos solicitados, estimación de coste por rango, señales de
  riesgo, rationale). **Versionado monotónico** (`metadata.blueprint_version`): una re-ejecución del
  cuestionario **crea una nueva versión, nunca sobrescribe** (principio P13). Incluye
  `questionnaire_hash` para trazabilidad.
- **`setup.plan.yaml`** (`kind: SetupPlan`): lista ordenada de `SetupTask` con dependencias, derivada
  de un `blueprint_version` concreto. Referencia el checklist humano (`SETUP.md`).
- **`SetupTask`**: máquina de estados (ver [ADR-0007](0007-update-channels-and-rollout.md) para
  aprobaciones y la [Spec B §12.2 máquina de estados de setup](../specs/b-nexus-hub.md)):
  `not_started → waiting_user → waiting_oauth → ready → running → completed`, con bifurcaciones
  `blocked | failed | skipped`. Cada tarea registra `owner`, `prerequisites`, `evidence`, `retry`,
  `rollback`, `escalation`. Cuando `state == failed`, `failure_reason` es obligatorio (constraint en
  el esquema).
- **Envoltorio común:** `apiVersion: nexus.io/v1alpha1`, `kind`, `metadata`, `spec`.
  `additionalProperties: false` en los objetos con forma cerrada.
- **Sin secretos:** ningún artefacto embebe valores de secreto; solo referencias.

## Consecuencias

- Reanudable, delegable y auditable: el estado del setup es dato de primera clase, no un checkbox.
- Coste: versionado explícito de blueprints (almacenar histórico).
- El estilo `apiVersion/kind/metadata/spec` mantiene continuidad con `nexus.instance.yaml`.

## Alternativas consideradas

- **Checkbox simple en vez de máquina de estados:** rechazada; impide reanudar/delegar/auditar.
- **Sobrescribir el blueprint al re-cuestionar:** rechazada; viola reversibilidad.
