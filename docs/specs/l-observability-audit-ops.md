# Spec L: Observabilidad, auditoría, operaciones, backup/recuperación y soporte

- **Estado:** Diseño aprobado, no implementado (TARGET-STATE salvo donde se marque ACTUAL)
- **Versión de arquitectura:** `v1alpha1` + `v1alpha2`
- **Fecha:** 2026-07-19
- **Documento canónico único** de las preocupaciones transversales de observabilidad, auditoría,
  operación de flota, backup/recuperación y soporte. **Decisión de ownership:** la arquitectura trata
  estas preocupaciones como **transversales**, pero se les asigna esta especificación con ownership
  explícito para evitar dispersión; los componentes las consumen, esta spec las define.
- **Contratos:** [`status-report`](../schemas/v1alpha1/status-report.schema.json).
- **Relacionadas:** [arquitectura §14](../architecture/nexus-os-architecture.md), [Spec B](b-nexus-hub.md), [Spec D](d-operator-instance-lifecycle.md), [Spec H](h-security-trust-signing-secrets.md), [ADR-0007](../adr/0007-update-channels-and-rollout.md).

## 1. Estado actual vs. objetivo

**Actual:** RFC-002 define `/_console/audit` (audit log exportable NDJSON) y `/health`. **Objetivo:**
audit log dual (Hub + instancia), telemetría de flota agregada, backups gestionados opcionales y flujo de
soporte/escalado, sin que nada de contenido de negocio salga de la instancia.

## 2. Problema y contexto

Operar flota sin violar la soberanía del dato exige separar métricas de salud (agregadas, permitidas) de
contenido de negocio (nunca sale). Sin ownership canónico, cada componente inventa su propia telemetría.

## 3. Objetivos, no-objetivos y actores

- **Objetivos:** trazabilidad de toda orden y cambio de estado; telemetría de salud agregada; backup/DR
  con consentimiento; soporte con escalado desde la máquina de estados de setup.
- **No-objetivos:** enviar contenido, memoria o conversaciones al Hub; backups no consentidos;
  observabilidad que reintroduzca datos rehenes.
- **Actores:** Operator (emite status-report), Hub (agrega salud de flota), Runtime (audit log local),
  usuario/admin (consume dashboards, soporte).

## 4. Conceptos y modelo de datos

- **Audit log dual:** toda orden aplicada y todo cambio de estado quedan en el audit log del Hub **y** de
  la instancia. En la instancia es exportable (NDJSON).
- **Telemetría de flota:** solo métricas agregadas (versión, uptime, CPU/mem %, paquetes instalados,
  progreso de setup). **Nunca contenido.**
- **Backup:** gestionado (opcional, de pago, cifrado y consentido) o export/portabilidad OSS para
  self-hosted.

## 5. Interfaces/contratos

- `status-report` ([esquema](../schemas/v1alpha1/status-report.schema.json)) del Operator al Hub; evento
  `instance.health_changed`.
- Export NDJSON del audit log de instancia (compat RFC-002 `/_console/audit`).

## 6. Requisitos funcionales

- **P0:** audit log de instancia exportable; healthcheck básico.
- **P1:** audit log del Hub; dashboard de salud de flota (solo métricas agregadas); escalado a soporte
  desde tareas `failed`.
- **P2:** backups gestionados cifrados y consentidos; alertas de flota; retención/rotación configurable.

## 7. Requisitos no funcionales

- Frontera solo-Runtime para contenido. Retención auditable. Sin PII innecesaria en telemetría.

## 8. Transiciones/flujos

Orden aplicada → registro dual (Hub + instancia). Tarea `failed` → escalado a soporte con contexto (sin
secretos ni contenido). Backup → cifrado → almacenamiento consentido → restauración verificable.

## 9. Seguridad/privacidad y fronteras de confianza

- El Hub nunca recibe datos de negocio; los backups gestionados solo con consentimiento explícito y
  cifrado. La telemetría se limita a métricas agregadas.

## 10. Fallo/offline/degradado

- El Hub puede reconstruir metadatos de flota desde los status-report de los Operators.
- En modo offline, el audit log local sigue siendo la fuente de verdad; se sincroniza al reconectar.

## 11. Observabilidad/SLOs

- Objetivo: 100% de órdenes con registro dual; latencia baja de propagación de `instance.health_changed`;
  cero contenido de negocio en telemetría (verificable).

## 12. Criterios de aceptación (Given/When/Then)

- **Given** una orden aplicada, **when** se ejecuta, **then** queda en el audit log del Hub **y** de la
  instancia.
- **Given** telemetría de flota, **when** se inspecciona, **then** no contiene contenido de negocio.
- **Given** un backup gestionado, **when** se crea, **then** está cifrado y requiere consentimiento
  explícito previo.

## 13. Métricas de éxito

Cobertura de audit dual; % de instancias con salud reportada; tiempo de restauración de backup; tickets
de soporte resueltos con contexto suficiente.

## 14. Dependencias

[Spec D](d-operator-instance-lifecycle.md) (status-report), [Spec B](b-nexus-hub.md) (dashboards),
[Spec H](h-security-trust-signing-secrets.md) (cifrado de backups).

## 15. Migración/versionado

Reutiliza `status-report` (`v1alpha1`) y el audit log NDJSON de RFC-002. No introduce contratos nuevos.

## 16. Riesgos y preguntas abiertas

Región de datos por defecto para backups gestionados; política de retención por defecto; alcance de
alertas en P2.
