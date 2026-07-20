# Especificaciones de Nexus OS (`v1alpha1` + `v1alpha2`)

Especificaciones detalladas, **listas para implementar**, de los componentes de Nexus OS. Son
**TARGET-STATE** (describen el estado objetivo, no código existente) salvo donde la spec marque ACTUAL.
Extienden de forma aditiva la [arquitectura system-wide](../architecture/nexus-os-architecture.md).

Existe **exactamente una** especificación canónica por componente. La [Spec B (Nexus Hub)](b-nexus-hub.md)
es el **único** documento de desarrollo del Hub; consolida portal, setup gestionado, onboarding y sitio
web.

Cada especificación sigue una estructura consistente: estado (actual vs objetivo), problema/contexto,
objetivos, no-objetivos, actores/responsabilidades/fronteras, conceptos/modelo de datos, interfaces/
contratos/APIs/eventos, requisitos funcionales (P0/P1/P2) y no funcionales, transiciones/flujos, seguridad/
privacidad y fronteras de confianza, comportamiento ante fallo/offline/degradado, observabilidad/SLOs,
criterios de aceptación (Given/When/Then), métricas de éxito, dependencias, migración/versionado, y
riesgos/preguntas abiertas. Cuando una sección no aplica, se indica el motivo.

| # | Especificación | Alcance |
|---|---|---|
| a | [Personal Runtime](a-personal-runtime.md) | Edición Personal libre, un propietario, sin Hub. |
| b | [Nexus Hub (app web)](b-nexus-hub.md) | **Único** documento de desarrollo del Hub: journeys, setup, secretos, catálogo, frontend/BFF, RBAC, API, entitlements. |
| c | [Team / Organization](c-team-organization.md) | Multiusuario, roles, políticas de organización. |
| d | [Operator y ciclo de vida de instancia](d-operator-instance-lifecycle.md) | Enrolamiento, reconciliación, salud. |
| e | [Registry / Catálogo y distribución](e-registry-catalog-distribution.md) | Cuatro carriles, mirrors, grants. |
| f | [Modelo de paquetes y artefactos](f-package-artifact-model.md) | Agentes, skills, flows, sidecars, skulls, tareas programadas, sector packs. |
| g | [Entitlements, suscripciones y degradación](g-entitlements-subscriptions-degradation.md) | Verificación offline, ciclo de vida. |
| h | [Seguridad, confianza, firma y secretos](h-security-trust-signing-secrets.md) | Ed25519, Cosign, minisign, age/X25519, mTLS. |
| i | [Studio: autoría y publicación](i-studio-authoring-publishing.md) | Creación verificada, overlays, publicación. |
| j | [Modalidades de despliegue](j-deployment-modalities.md) | self-hosted / BYOC / managed, ortogonal a edición. |
| k | [CLI, SDK, instalador/bootstrap y handoff](k-cli-sdk-installer-handoff.md) | Herramientas OSS y automatización de handoff a asistentes. |
| l | [Observabilidad, auditoría y operaciones](l-observability-audit-ops.md) | Telemetría, audit dual, backup/recuperación, soporte. |
| m | [Inferencia local, voz y edge](m-local-inference-voice-edge.md) | LiteRT, Voicebox, VAD (ownership canónico + enlaces; parcialmente ACTUAL). |

## Add-ons de sector (opcionales)

Capacidades de sector-pack opcionales que **componen** primitivas existentes del Runtime. **No** son
componentes centrales A-M ni introducen un motor de runtime nuevo.

| Add-on | Alcance |
|---|---|
| [Real Estate 3D Capture (PoC)](sector-packs/real-estate-3d-capture.md) | Captura/reconstruccion 3D local vía sidecar GPU (LingBot Map), sobre el pack `real-estate-agency`; reutiliza el patron de sidecar de la [Spec M](m-local-inference-voice-edge.md). |

**Arquitectura:** [system-wide](../architecture/nexus-os-architecture.md). **Contratos relacionados:**
[`docs/schemas/v1alpha2/`](../schemas/v1alpha2/) y [`v1alpha1/`](../schemas/v1alpha1/). **Validación:**
`console/tests/test_managed_platform_schemas.py`. **Mapa canónico:** [`docs/README.md`](../README.md).
