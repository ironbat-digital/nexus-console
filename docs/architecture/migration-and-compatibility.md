# Migración y compatibilidad — de Console/Platform (v0.13.8) al Portal Gestionado

- **Estado:** Diseño aprobado · no implementado
- **Versión de arquitectura:** `v1alpha1` con la capa aditiva `v1alpha2` (producto Personal + Hub); este documento cubre la transición v0.13.8 -> Portal Gestionado y el delta aditivo v1alpha1 -> v1alpha2.
- **Fecha:** 2026-07-19
- **Relacionadas:** [ADR-0001](../adr/0001-hub-operator-runtime-registry-split.md), [arquitectura de Nexus OS §16](nexus-os-architecture.md), RFC-002

## Principio rector

La migración al portal gestionado es **opt-in, no destructiva, reversible** y permite **operación
standalone indefinida**. Nadie pierde funcionalidad ni queda obligado a conectarse al Hub. Esto es la
aplicación directa del principio de soberanía del dato a la propia infraestructura.

## Qué pasa con cada activo actual

| Activo actual (v0.13.8) | Qué le ocurre | Reversible / standalone |
|---|---|---|
| **Console local** (`docker compose up`) | Sigue funcionando **idéntico**. Modo local single-tenant intacto. El Hub es opcional. | Sí, indefinidamente |
| **`nexus.instance.yaml`** (wizard) | Es base directa del `Blueprint`. Un adaptador puede derivar `nexus.blueprint.yaml` de un `nexus.instance.yaml` existente sin pérdida. | Sí; el instance.yaml sigue siendo válido |
| **Outputs de handoff** (`SETUP.md`, plan de provisioning) | `SETUP.md` se conserva como checklist humano; el plan se formaliza como `setup.plan.yaml`. Los outputs actuales siguen siendo usables tal cual. | Sí |
| **Despliegues Fly.io** existentes | Siguen operando bajo el flujo Console/Fly manual. La adopción del Operator es **opcional**; sin él, nada cambia. | Sí |
| **Platform desplegadas** | Se renombran conceptualmente a **NexusOS Runtime**; el protocolo RFC-002 (HTTP + JWT firmado) sigue vigente y es el antecedente del canal Hub↔Operator. | Sí |
| **Plantillas de agente / áreas** (`console/agent_templates/`) | Se empaquetan como **packs** del Registry sin cambiar su frontmatter (`_schema.md`). Las asignaciones de área (`area_recommender`) se preservan. | Sí; el catálogo local sigue disponible |
| **Ecosystem registry / integraciones** | El modelo de "integraciones como datos" (referencias a secretos por nombre, nunca valores) es coherente con [ADR-0005](../adr/0005-secrets-bundle-and-oauth.md) y se conserva. | Sí |
| **Instancias v0.13.8** | Pueden enrolarse en el Hub instalando el Operator (P1), o seguir sin él. El enrolamiento no toca datos de negocio. | Sí; kill switch disponible |

## Ruta de migración opt-in (cuando exista Operator, P1)

1. El operador instala el **Operator** junto a su instancia (sidecar/systemd/pod).
2. El Hub emite un **token de enrolamiento de un solo uso**; el Operator genera su par de claves e
   intercambia el token ([ADR-0004](../adr/0004-operator-enrollment-and-identity.md)).
3. A partir de ahí, el Operator reconcilia estado deseado firmado. **Ningún dato de negocio migra al
   Hub.**
4. En cualquier momento, el **kill switch** desconecta el Operator; la instancia sigue operando en
   modo autónomo.

## Compatibilidad de versiones

- El **contrato de arquitectura** se versiona como `v1alpha1`, independiente de la versión del paquete
  `nexus-console` (hoy `0.13.8`). Ver [nota de versionado](#versionado).
- Los packs declaran `compatibility.runtime` (rango SemVer); una **matriz de compatibilidad** pública
  evita romper packs instalados ([ADR-0007](../adr/0007-update-channels-and-rollout.md)).
- Backward compatibility del protocolo: una versión minor, igual que RFC-002.

## Licencia durante la migración

El modelo de **licencia por componente** está aprobado ([ADR-0008](../adr/0008-oss-commercial-boundary-and-license.md)):
Apache-2.0 para Runtime/Operator/CLI/SDK/contratos públicos, propietario para Hub y servicios
gestionados, SPDX obligatorio por pack. **La relicencia del código actual no se ha ejecutado:** el
`LICENSE` raíz sigue siendo **MIT** y **todos** los archivos de `console/` conservan MIT hasta completar
la auditoría de titularidad/contribución, el consentimiento de titulares y la decisión CLA/DCO. La
adopción del portal gestionado **no** depende de esa relicencia ni altera la licencia de las instancias
existentes.

## Reversibilidad

- Blueprints versionados (nunca sobrescriben): se puede volver a una versión anterior.
- Packs con `uninstall`/rollback obligatorio y overlays no destructivos.
- Export/portabilidad de la instancia completa disponible en OSS (no se retiene fuera del OSS).

<a id="v1alpha2"></a>
## Transición de contrato `v1alpha1` → `v1alpha2` (capa de producto)

La capa de producto Personal + Hub se versiona como **`v1alpha2`** y es **aditiva y backward
compatible** sobre `v1alpha1`:

- **Sin ruptura de contratos existentes.** `v1alpha2` reutiliza las primitivas crypto/identificador de
  `v1alpha1` (`Signature`, `InstanceId`, `Timestamp`, ...) por `$id` absoluto; no las redefine ni las
  rompe. Los esquemas y ejemplos `v1alpha1` siguen validando sin cambios.
- **Extensión aditiva del pack.** `nexus.pack.schema.json` (`v1alpha1`) gana campos **opcionales**
  (`metadata.visibility`, `metadata.commercial_terms_ref`, `spec.required_entitlements`,
  `publisher.verification: official`). Un pack sin `visibility` se trata como **público** (compatible).
- **Edición por defecto.** Una instancia v0.13.8 o `v1alpha1` se declara **Personal** por defecto
  (`source: personal_base`); no requiere entitlement ni Hub.
- **Modalidad por defecto.** Las instancias existentes se declaran `self_hosted` (Operator `absent`);
  adoptar BYOC/managed es opt-in.
- **Identificadores lowercase-canónicos.** `OrganizationId`/`UserRef` son `^org_[a-z0-9]{4,40}$` /
  `^usr_[a-z0-9]{4,40}$`: el Hub que los emite debe normalizarlos a minúsculas y el Registry/Runtime que
  los consumen los usan sin cambios, de modo que un `org_id` viaje intacto dentro de un `PackageScope`
  `private-organization:<org_id>`. Un id con mayúsculas se rechaza por contrato. Un implementador que
  genere ids debe normalizar en el borde de emisión, nunca en el de consumo.

### Política de degradación (downgrade) al expirar

La degradación es **reversible y no destructiva** (invariante de [ADR-0009](../adr/0009-editions-entitlements-and-subscription-degradation.md)):

- El **propietario conserva acceso y exportación en todos los estados**.
- Al expirar/suspender/cancelar: usuarios adicionales a **solo lectura**; agentes premium y tareas
  programadas **pausados (no borrados)**; nuevas invitaciones **bloqueadas**; capacidades Personal
  **continúan**.
- Al **renovar**, todo se **reactiva** al estado previo; no hay pérdida de datos ni de configuración.

<a id="versionado"></a>
## Nota de versionado

`console/pyproject.toml` está en `0.13.8` y sigue SemVer del paquete. Este trabajo es **solo
documentación y contratos de una arquitectura futura no implementada**, por lo que **no** se bumpea la
versión del paquete: no hay cambio de comportamiento del código. En su lugar, la arquitectura y los
esquemas se versionan por separado como **`v1alpha1`** (`x-nexus-contract-version` en cada esquema),
señalando que es un contrato en fase alfa, sujeto a cambios antes de la implementación. Cuando el
primer componente (P0 del Hub) se implemente, ese código seguirá el versionado SemVer del paquete que
corresponda.
