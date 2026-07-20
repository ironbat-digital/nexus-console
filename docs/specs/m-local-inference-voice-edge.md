# Spec M: Inferencia local, voz y edge (ownership canónico)

- **Estado:** Parcialmente **ACTUAL** (implementado) + objetivo. Ver §1.
- **Versión de arquitectura:** `v1alpha1` + `v1alpha2`
- **Fecha:** 2026-07-19
- **Documento canónico único** que establece el **ownership de arquitectura** de las capacidades de
  inferencia local, voz y edge. **No duplica** la documentación técnica detallada existente: la referencia
  y enlaza. Estas capacidades **son de primera clase** en el repo actual (hay código real: LiteRT.js,
  Voicebox, Silero VAD).
- **Relacionadas:** [arquitectura](../architecture/nexus-os-architecture.md), [Spec A (Personal Runtime)](a-personal-runtime.md), [Spec F (modelo de paquetes)](f-package-artifact-model.md), [Spec H](h-security-trust-signing-secrets.md).
- **Documentación técnica existente (autoritativa por implementación):** [README del repo, sección Ecosystem](../../README.md), [conversión VAD](../../tools/vad-conversion/README.md), [modelos Silero VAD](../../web/public/models/silero-vad/README.md).

## 1. Estado actual vs. objetivo

**ACTUAL (implementado):**
- **LiteRT.js** (`experimental`, nativo): modelos `.tflite` en el navegador vía WebGPU con fallback
  determinista CPU/WASM. Sostiene el slice de Silero VAD en el Voice cockpit. El acceso a modelos está
  gobernado por el registro `agent_local_model` (`GET/POST /local-models`): cada modelo lleva procedencia
  (`sha256`, `license`, `size_bytes`). Se habilita por instancia con el flag `local_inference`.
- **Voicebox** (`configurable`, externo): sidecar de voz local opcional para TTS/STT y un servidor MCP
  HTTP. Corre como **proceso local separado**; Nexus solo habla con una base URL configurada y **nunca
  sube audio**. Clonación de voz **opt-in** y solo para voces propias.

**OBJETIVO:** integrar estas capacidades como packs/sidecars del Registry con procedencia firmada y
overlays, sin cambiar su naturaleza local-first.

## 2. Problema y contexto

La inferencia local y la voz deben ser soberanas (sin subir datos) y verificables (procedencia de
modelos). El riesgo es duplicar su documentación técnica o reintroducir dependencia de red. Esta spec fija
el ownership y las invariantes; el detalle técnico vive en los READMEs enlazados.

## 3. Objetivos, no-objetivos y actores

- **Objetivos:** ejecución local verificable; procedencia de modelos; voz sin subir audio; consentimiento
  explícito para clonación de voz.
- **No-objetivos:** subir audio o contenido a servicios remotos por defecto; cargar modelos sin
  procedencia; clonación de voz sin consentimiento.
- **Actores:** Runtime (host de inferencia), agente/sidecar (consumidor), usuario (consentimiento).

## 4. Conceptos y modelo de datos

- **Registro de modelo local** (`agent_local_model`): id, `sha256`, `license`, `size_bytes`, URL
  whitelist. Un agente solo carga URLs whitelisted.
- **Sidecar de voz** (Voicebox): proceso local externo; contrato por base URL + healthcheck
  (`GET /voicebox/status`).
- **VAD** (Silero): modelo local ejecutado en navegador (LiteRT/WASM).

## 5. Interfaces/contratos

- `GET/POST /local-models` (registro con procedencia), flag `local_inference` por instancia.
- `GET /voicebox/status` (salud del sidecar). Consentimiento de clonación por flag
  (`CONSOLE_VOICEBOX_VOICE_CLONING_CONSENT`).
- Como parte del Registry, un modelo/sidecar distribuido sigue [Spec F](f-package-artifact-model.md) y la
  procedencia firmada de [Spec H](h-security-trust-signing-secrets.md).

## 6. Requisitos funcionales

- **P0 (ACTUAL):** ejecución local de VAD; registro de modelo con procedencia; sidecar de voz opcional.
- **P1:** distribución de modelos/sidecars como packs firmados con overlays.
- **P2:** más targets edge; matriz de compatibilidad de aceleración.

## 7. Requisitos no funcionales

- Local-first: sin subida de datos por defecto. Procedencia obligatoria para cargar modelos.
  Determinismo del fallback CPU/WASM.

## 8. Transiciones/flujos

Habilitar `local_inference` → registrar modelo con `sha256`/`license` → cargar (verificando whitelist) →
inferir localmente. Voz: configurar base URL → healthcheck → usar TTS/STT sin subir audio.

## 9. Seguridad/privacidad y fronteras de confianza

- Modelos solo desde URLs whitelisted con procedencia. Audio nunca sale de la máquina. Clonación de voz
  opt-in y limitada a voces propias.

## 10. Fallo/offline/degradado

- Diseñado para operar offline (inferencia en el navegador/máquina local). El sidecar de voz es opcional;
  su ausencia degrada solo la voz, no el resto del Runtime.

## 11. Observabilidad/SLOs

- Healthcheck del sidecar; métricas locales de inferencia. Sin telemetría de contenido (ver [Spec L](l-observability-audit-ops.md)).

## 12. Criterios de aceptación (Given/When/Then)

- **Given** un modelo sin procedencia, **when** un agente intenta cargarlo, **then** se rechaza (URL no
  whitelisted / falta `sha256`).
- **Given** el sidecar de voz, **when** procesa audio, **then** no se sube ningún audio a servicios
  remotos.
- **Given** clonación de voz, **when** se solicita sin consentimiento, **then** se bloquea.

## 13. Métricas de éxito

% de instancias con inferencia local activa; latencia de VAD en navegador; cero subidas de audio.

## 14. Dependencias

[Spec A](a-personal-runtime.md) (host), [Spec F](f-package-artifact-model.md) (distribución),
[Spec H](h-security-trust-signing-secrets.md) (procedencia/firma).

Este patron de sidecar de inferencia local lo reutiliza el add-on de sector
[Real Estate 3D Capture (PoC)](sector-packs/real-estate-3d-capture.md), que envuelve una GPU de
reconstruccion 3D como sidecar externo.

## 15. Migración/versionado

Las capacidades actuales se preservan; su distribución como packs es aditiva. No cambia contratos
existentes.

## 16. Riesgos y preguntas abiertas

Estandarización de la procedencia de modelos en el manifiesto de pack; targets edge soportados;
gobernanza de la whitelist de modelos.
