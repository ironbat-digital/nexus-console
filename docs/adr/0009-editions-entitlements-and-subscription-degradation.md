# ADR-0009: Ediciones, entitlements de capacidad y degradación de suscripción

- **Estado:** Aceptada (contrato de producto `v1alpha2`, aditivo sobre `v1alpha1`)
- **Fecha:** 2026-07-19
- **Versión de arquitectura:** `v1alpha2`
- **Relacionadas:** [ADR-0002](0002-signing-and-verification.md), [ADR-0010](0010-edition-vs-deployment-modality.md), [Visión de Nexus OS §8, §14](../vision/nexus-os-vision.md), [Spec G](../specs/g-entitlements-subscriptions-degradation.md)

## Contexto

El modelo de producto aprobado ofrece una edición **Personal** libre y gratuita para un propietario, y
capacidades oficiales de **Team/Organization** y paquetes premium/privados por **suscripción**. Hace
falta representar esa habilitación sin acoplarla a precios ni a nombres de plan, verificable offline, y
garantizando que al expirar **nunca** se retienen los datos del usuario.

## Decisión

- **Ediciones como eje declarado:** `personal | team | organization` (`edition.declaration.schema.json`).
  El origen puede ser `personal_base` (libre, sin Hub), `verified_entitlement` o `cached_entitlement`.
  `personal_base` implica edición `personal` (conditional del esquema).
- **Entitlements de capacidad firmados:** `entitlement.schema.json`. Capacidades con ids estables
  (`team_collaboration`, `fleet_management`, `premium_pack_access`, ...), **nunca** nombres de plan ni
  precios. Firma **Ed25519** con `trust_domain`; se rechazan `sigstore-cosign`, `age`, `minisign`,
  `ecdsa-p256`. Campos obligatorios de sobre firmado: `issued_at`, `expires_at`, `revision`, `nonce`
  (anti-replay). Verificación **offline** con clave del Hub pineada; Personal no requiere verificación.
- **Degradación graciosa (invariante NO NEGOCIABLE):** `subscription-state.schema.json` fija
  `owner_access: preserved` (const) y `export_available: true` (const) en **todos** los estados. En
  suspended/cancelled/expired, los usuarios adicionales pasan a `read_only`, y los agentes premium y las
  tareas programadas se **pausan** (enum `running|paused`, sin estado de borrado); se reactivan al
  renovar. **No hay eliminación de datos.**
- **Precios fuera de alcance:** ningún precio ni plan se hardcodea en esquemas, docs ni código.

## Consecuencias

- La habilitación es verificable offline y no depende de un check online, alineada con la soberanía.
- Los datos nunca quedan como rehén: el propietario conserva acceso y exportación siempre.
- Coste: mantener el catálogo de capacidades y la lógica de gracia/revocación en el Operator.

## Alternativas consideradas

- **Check de licencia online obligatorio:** rechazado; rompe operación offline y soberanía.
- **Planes/precios en el contrato:** rechazado; acopla producto a comercial y no está decidido.
- **Deshabilitar o borrar capacidades al expirar:** rechazado; retiene datos como rehén.
