# Spec K: CLI, SDK, instalador/bootstrap y automatización de handoff

- **Estado:** Diseño aprobado, no implementado (TARGET-STATE salvo donde se marque ACTUAL)
- **Versión de arquitectura:** `v1alpha1` + `v1alpha2`
- **Fecha:** 2026-07-19
- **Documento canónico único** de las herramientas de línea de comandos, SDK, instalador/bootstrap y
  automatización de handoff a asistentes. Consolida lo que antes estaba disperso (wizard/handoff en
  Console, `nexus-core` SDK planeado, bootstrap local) en una única especificación con ownership claro.
- **Contratos:** [`nexus.blueprint`](../schemas/v1alpha1/nexus.blueprint.schema.json), [`setup.plan`](../schemas/v1alpha1/setup.plan.schema.json), [`setup.task`](../schemas/v1alpha1/setup.task.schema.json), [`secrets-bundle-manifest`](../schemas/v1alpha1/secrets-bundle-manifest.schema.json).
- **Relacionadas:** [arquitectura](../architecture/nexus-os-architecture.md), [Spec B (Hub §6 handoff)](b-nexus-hub.md), [Spec D](d-operator-instance-lifecycle.md), [Spec H](h-security-trust-signing-secrets.md), [ADR-0005](../adr/0005-secrets-bundle-and-oauth.md).

## 1. Estado actual vs. objetivo

**Actual (implementado):** Console incluye un wizard de 6 pasos que emite `nexus.instance.yaml` y un
`SETUP.md`, un deployer local (Docker Compose) y un flujo de bootstrap (`console/tests/test_bootstrap_flow.py`).
**Objetivo:** una familia coherente de herramientas OSS (CLI, SDK, instalador/bootstrap) y la
automatización de handoff a asistentes (OpenClaw/cowork) que reutilizan los mismos contratos que el Hub.

## 2. Problema y contexto

Los usuarios necesitan operar Nexus OS sin depender del Hub (self-hosted/offline) y automatizar el setup.
Sin una herramienta canónica, la lógica de bootstrap, generación de artefactos y handoff se duplica. Esta
spec fija una sola cadena de herramientas que produce y consume los mismos artefactos que el Hub.

## 3. Objetivos, no-objetivos y actores

- **Objetivos:** CLI para operar Runtime/packs sin Hub; SDK (`nexus-core`) con los tipos de contrato;
  instalador/bootstrap reproducible; generación de handoff Markdown ejecutable por cowork.
- **No-objetivos:** shell remoto; ejecución arbitraria; incrustar secretos en artefactos de texto plano;
  reemplazar al Operator (la CLI es para operación local/offline, no canal de control remoto).
- **Actores:** usuario self-hoster, asistente cowork/OpenClaw, integrador que usa el SDK, instalador.

## 4. Conceptos y modelo de datos

- **CLI:** comandos de capacidad acotada sobre el Runtime Admin API local (instalar pack, ver estado,
  exportar, validar firma).
- **SDK (`nexus-core`):** tipos y validadores de los contratos (`docs/schemas/`) para clientes.
- **Instalador/bootstrap:** produce una instancia Runtime desde un blueprint (`docker compose up` sigue
  intacto como ruta base).
- **Handoff:** `SETUP.md` derivado de `setup.plan.yaml` + `nexus.blueprint.yaml`, con pasos, `owner`,
  evidencia esperada y escalado. **Nunca contiene secretos en texto plano.**

## 5. Interfaces/contratos

- La CLI y el SDK consumen los mismos esquemas que el Hub; no definen contratos propios.
- El handoff es reproducible y verificable: el asistente puede reportar progreso vía `PATCH /v1/setup-tasks/{id}`
  cuando hay Hub; en modo offline, la evidencia se registra localmente.

## 6. Requisitos funcionales

- **P0:** generación local de blueprint/plan/`SETUP.md`; bootstrap local (Docker Compose); CLI de
  instalación/validación de packs firmados; export/portabilidad.
- **P1:** SDK publicado con tipos de contrato; instalador para BYOC (Fly/K8s/on-prem); handoff con
  reporte de progreso al Hub.
- **P2:** plantillas de instalador para más targets; canales de actualización vía CLI.

## 7. Requisitos no funcionales

- OSS (Apache-2.0 objetivo). Verificación de firma offline. Sin telemetría silenciosa. Reproducibilidad
  del bootstrap.

## 8. Transiciones/flujos

blueprint → `setup.plan.yaml` → `SETUP.md` → ejecución (CLI/cowork/usuario) → evidencia por tarea →
instancia operativa. Reanudable: el estado del plan persiste localmente.

## 9. Seguridad/privacidad y fronteras de confianza

- Secretos por bundle cifrado (age/X25519) o vault local; nunca en Markdown ([ADR-0005](../adr/0005-secrets-bundle-and-oauth.md)).
- La CLI opera solo sobre capacidades acotadas del Admin API local; no abre canal de shell remoto.

## 10. Fallo/offline/degradado

Diseñada para operar **sin Hub**. Todo el ciclo local funciona offline; el handoff no requiere conexión.

## 11. Observabilidad/SLOs

Logs locales exportables (NDJSON), coherentes con el audit log de instancia (ver [Spec L](l-observability-audit-ops.md)).

## 12. Criterios de aceptación (Given/When/Then)

- **Given** un blueprint, **when** se ejecuta el bootstrap local, **then** se levanta una instancia
  Runtime operativa sin Hub.
- **Given** un `SETUP.md` generado, **when** se inspecciona, **then** no contiene ningún secreto en texto
  plano.
- **Given** un pack firmado, **when** la CLI lo instala, **then** verifica la firma offline antes de
  activar.

## 13. Métricas de éxito

% de setups offline completados sin soporte; tiempo de bootstrap local; adopción del SDK.

## 14. Dependencias

[Spec B](b-nexus-hub.md) (artefactos de handoff), [Spec D](d-operator-instance-lifecycle.md) (Admin API),
[Spec H](h-security-trust-signing-secrets.md) (firma/secretos).

## 15. Migración/versionado

Reutiliza los contratos `v1alpha1`/`v1alpha2` por `$id`. El wizard/handoff actual de Console es la base
directa. No introduce contratos nuevos.

## 16. Riesgos y preguntas abiertas

Alcance del SDK `nexus-core` (repo aparte, planeado); matriz de targets de instalador soportados;
estandarización del formato de reporte de evidencia offline.
