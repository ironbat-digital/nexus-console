# Nexus OS Real Estate 3D Capture PoC (add-on de sector)

> **Estado:** TARGET-STATE / PoC. Diseno aprobado, **no implementado**. Es una **capacidad de
> sector-pack** (add-on opcional), **no** un nuevo componente central A-M de la arquitectura. Los
> contratos referenciados estan en alfa (`v1alpha1`/`v1alpha2`). `Nexus OS` es el nombre de producto
> de visualizacion; los identificadores tecnicos (`NexusOS`, `nexus`, `$id`) no cambian.

Esta spec define, lista para implementar, un add-on **opcional** que anade **captura y reconstruccion
3D en streaming** a una agencia inmobiliaria sobre Nexus OS, envolviendo el proyecto OSS
[LingBot Map](https://github.com/Robbyant/lingbot-map) como **sidecar GPU local**. Extiende de forma
aditiva el [pack `real-estate-agency`](../../schemas/examples/pack.real-estate-agency.yaml) y reutiliza el
patron de sidecar de inferencia local de la [Spec M](../m-local-inference-voice-edge.md). No modifica
ninguna primitiva del Runtime ni contrato de produccion.

## 1. Registro de decision y alcance

- **Decision:** envolver (wrap) LingBot Map como sidecar externo con adaptador tipado; **no** copiar ni
  vendorizar su codigo dentro del Runtime; **no** exponer publicamente su viewer `viser`.
- **Empaquetado en dos capas:** un **core OSS** publico y espejable, y un **add-on premium verificado**
  que distribuye el sidecar GPU y la provenance firmada del modelo. Ver §12.
- **Alcance (in-scope):** captura 3D a partir de video/imagenes de una propiedad; generacion de artefactos
  (GLB, nube de puntos, MP4); publicacion y adjunto a fichas de propiedad existentes; comparticion con
  control de acceso; retencion/borrado; degradacion sin GPU.
- **No-objetivo explicito (out-of-scope):** esto **NO** es mapas de calle, **NO** geocodificacion, **NO**
  busqueda por barrio, **NO** isocronas, **NO** mapas de cartera (portfolio maps), **NO** enrutamiento de
  leads. LingBot Map es reconstruccion 3D en streaming, **no** cartografia geoespacial.

## 2. Problema, valor y personas

**Problema.** Las agencias necesitan tours 3D navegables de inmuebles sin subir material sensible a
terceros ni depender de hardware de captura especializado. Los servicios SaaS de tours atan datos de
propiedad y clientes a un proveedor externo.

**Valor.** Reconstruccion 3D **local** (el material nunca sale de la instancia del cliente), integrada en
el flujo de trabajo del asesor inmobiliario ya existente, con artefactos exportables y sin lock-in.

**Personas.**
- *Asesor comercial:* graba un walkthrough con el movil, lanza la captura y adjunta el tour a la ficha.
- *Coordinador de operaciones:* controla cuotas, retencion y visibilidad de los artefactos.
- *Propietario de la instancia (Personal/owner):* conserva acceso y exportacion en todo estado.

**Escenario (agencia Madrid / Marbella).** Una agencia con dos oficinas y **cinco agentes por oficina**.
Cada agente captura 3-6 propiedades por semana. La GPU vive en un servidor de oficina (BYOC o
self-hosted); los agentes envian trabajos desde el Hub y reciben el GLB navegable cuando termina.

## 3. Arquitectura y fronteras de componente

El add-on **compone** primitivas existentes. Ningun elemento nuevo es un motor de runtime.

| Artefacto | Tipo Nexus | Capa | Rol |
|---|---|---|---|
| `real-estate-3d-sidecar` | proceso sidecar GPU externo | premium | Envuelve LingBot Map tras una API tipada local; unico consumidor de la GPU y de los pesos. |
| `re_3d_capture` (`re-3d-capture`) | sidecar / adaptador tipado | premium | Contrato tipado que el Runtime usa para hablar con el sidecar por su base URL + healthcheck. |
| `property_3d_tour` | skill | core OSS | Orquesta el sub-flujo de captura desde el asesor; sin GPU degrada a informativo. |
| `property-3d-panel` | extension de UI | premium | Panel de progreso/visor del tour en el Hub (descriptor de UI, ver brecha en §6). |
| `listing_3d_tour_generation` | flow | core OSS | Plantilla de flujo de extremo a extremo (subir, encolar, publicar, adjuntar). |
| retencion de artefactos 3D | tarea programada | premium | Purga artefactos vencidos segun politica (ver §6: el id no es un Slug valido). |
| `real_estate_advisor` | skull (reutilizado) | core OSS | Perfil de cognicion reutilizado de `real-estate-agency`. |

**Por que el skill por si solo no basta.** Un skill se ejecuta dentro del Runtime y no puede ni cargar
pesos de varios GB, ni monopolizar una GPU CUDA, ni mantener el proceso de inferencia en streaming con
estado. La reconstruccion 3D exige un proceso externo dedicado (sidecar) con su propio ciclo de vida,
healthcheck y aislamiento de recursos, exactamente como Voicebox/VAD en la [Spec M](../m-local-inference-voice-edge.md).
El skill orquesta; el sidecar computa.

## 4. Secuencias de extremo a extremo

1. **Subida/captura.** El asesor sube video/imagenes vía el Hub. El BFF valida tipo/tamano, **elimina EXIF**
   y almacena el material como fuente con una referencia opaca. El material **no** se envia al Hub ni a
   terceros.
2. **Envio de trabajo.** El skill `property_3d_tour` crea un *capture job* y lo envia al sidecar por
   `POST /v1/jobs` (idempotente por `Idempotency-Key`).
3. **Progreso.** El Hub sondea `GET /v1/jobs/{id}` (o SSE) y muestra estado en `property-3d-panel`.
4. **Publicacion de artefacto.** Al completar, el sidecar expone el GLB/nube/MP4; el Runtime los persiste
   con provenance (modelo, version, SHA) y devuelve referencias.
5. **Adjunto a ficha.** El flow adjunta las referencias del artefacto a la ficha de propiedad existente.
6. **Comparticion/acceso.** La visibilidad del artefacto hereda el control de acceso de la ficha; los
   enlaces de comparticion son de alcance y caducidad acotados.
7. **Retencion/borrado.** La tarea programada purga artefactos vencidos; el borrado es **irreversible** y
   auditado.
8. **Cancelacion.** `POST /v1/jobs/{id}/cancel` cancela un trabajo en curso; el sidecar libera la GPU.
9. **Recuperacion ante fallo.** Un trabajo fallido queda en estado `failed` con causa; el skill ofrece
   reintento. Si el sidecar cae, los trabajos en curso pasan a `failed` tras timeout; la instancia sigue.

## 5. Contrato de API del sidecar (TARGET-STATE)

Binding **solo local** (`127.0.0.1` o socket UNIX) o mTLS en BYOC. Nunca binding publico. Auth por token
de sesion **por referencia** (nunca en claro en documentos). El sidecar **nunca** sube material a la red.

| Metodo | Ruta | Proposito |
|---|---|---|
| `GET` | `/v1/health` | Liveness. |
| `GET` | `/v1/ready` | Readiness (pesos cargados, GPU disponible). |
| `POST` | `/v1/jobs` | Crear trabajo (idempotente por `Idempotency-Key`). |
| `GET` | `/v1/jobs/{id}` | Estado del trabajo. |
| `GET` | `/v1/jobs?cursor=` | Listado paginado por cursor. |
| `POST` | `/v1/jobs/{id}/cancel` | Cancelar. |
| `GET` | `/v1/jobs/{id}/artifacts` | Referencias de artefactos publicados. |
| `DELETE` | `/v1/jobs/{id}` | Borrado irreversible del trabajo y artefactos. |

**Estados de trabajo:** `queued -> running -> (completed | failed | cancelled)`.

**Ejemplo de peticion (`POST /v1/jobs`):**

```json
{
  "idempotency_key": "job-2026-07-20-0001",
  "source_media_ref": "runtime://media/prop_1837/walkthrough.mp4",
  "outputs": ["glb", "point_cloud", "mp4"],
  "max_frames": 3000,
  "listing_ref": "prop_1837"
}
```

**Ejemplo de respuesta:**

```json
{
  "job_id": "j_9f2a",
  "state": "queued",
  "created_at": "2026-07-20T09:12:00Z",
  "model": { "id": "robbyant/lingbot-map", "version": "0.1.0", "sha256": "PENDIENTE-PIN-EN-RELEASE" }
}
```

**Modelo de error (uniforme):** `{ "error": { "code": "gpu_unavailable", "message": "...", "retryable": true } }`.
Codigos: `validation_failed`, `gpu_unavailable`, `model_unavailable`, `job_not_found`, `quota_exceeded`,
`timeout`, `internal`.

## 6. Modelo de datos y brechas de contrato (preguntas abiertas)

**Modelo de datos.** *Capture job* (id, estado, timestamps, `listing_ref`, provenance de modelo);
*source media* (referencia opaca, tipo, hash, EXIF eliminado); *artifact refs* (GLB/nube/MP4 por
referencia); *provenance* (modelo id/version/SHA-256, licencia, deps heredadas); *politica de retencion*;
*eventos de auditoria* (creacion, publicacion, comparticion, borrado).

**Brechas de contrato (NO se extiende ningun esquema de produccion).** El esquema
[`nexus.pack.schema.json`](../../schemas/v1alpha1/nexus.pack.schema.json) tiene `metadata` y `spec` con
`additionalProperties: false`. Por tanto **no** se pueden representar como campos de manifiesto:

1. **Configuracion del sidecar** (base URL, modo de ejecucion, GPU/device, timeouts, concurrencia,
   whitelist de descarga). Estado objetivo: bloque `sidecar_config` propuesto abajo; hoy va como
   `default_mappings` no normativos + [ejemplo desired-state](../../schemas/examples/desired-state.real-estate-3d-capture.example.json).
2. **Provenance de pesos del modelo** (SHA-256/version/licencia por peso). Estado objetivo: descriptor
   `model_provenance`; hoy se referencia por `provenance.sbom_attestation_ref` del pack y por
   `model_provenance_ref` en el desired-state.
3. **Descriptor del panel de UI** (`property-3d-panel`). No hay campo de manifiesto para extensiones de UI.
4. **Id de tarea programada `3d_artifact_retention`.** Empieza por digito, asi que **no** es un `Slug`
   valido (`^[a-z][a-z0-9_-]*$`). Se mantiene como concepto de spec, **no** como id de campo de manifiesto.

**Recomendacion:** llevar estas cuatro necesidades a una RFC de contrato antes de implementar. No
introducir cambios de contrato no revisados.

**Propuesta de esquema de configuracion (TARGET-STATE, aun no un contrato validado):**

```yaml
# PROPUESTA (no validada contra ningun $id). Solo referencias, nunca secretos en claro.
sidecar_config:
  base_url: "http://127.0.0.1:8791"      # solo-local; healthcheck GET /v1/ready
  execution_mode: local_sidecar           # local_sidecar | byoc_mtls
  device: "cuda:0"
  model:
    id: "robbyant/lingbot-map"
    version: "0.1.0"
    sha256: "PENDIENTE-PIN-EN-RELEASE"
    license: "Apache-2.0"
    source_whitelist: ["https://huggingface.co/robbyant/lingbot-map"]
  storage: { artifacts_ref: "runtime://artifacts/3d" }
  quotas: { max_concurrent_jobs: 1, max_frames: 10000, max_upload_mb: 2048 }
  retention: { ttl_days: 90, on_expiry: purge }
  outputs: ["glb", "point_cloud", "mp4"]
  visibility: inherit_from_listing
  timeouts: { job_seconds: 900, request_seconds: 30 }
  auth_token_ref: "secretref://sidecars/re_3d_capture/session"   # referencia, no valor
```

## 7. Runtime, contenedor y provenance de pesos

- **Baseline:** GPU NVIDIA con CUDA 12.8, PyTorch 2.8.0; contenedor con toolkit CUDA. FlashInfer opcional,
  fallback a SDPA.
- **Dependencias fijadas (pinning):** todas las versiones fijadas en el artefacto del sidecar; sin rangos
  flotantes.
- **Provenance del modelo:** SHA-256 + version + licencia de cada peso, y de `skyseg.onnx`
  ([`JianyuanWang/skyseg`](https://huggingface.co/JianyuanWang/skyseg)). Los pesos se **empaquetan** en el
  artefacto del sidecar; **no** hay descarga dinamica no confiable en ejecucion. La whitelist de origen
  limita cualquier fetch de aprovisionamiento a HuggingFace del modelo declarado.
- **Instalacion offline / air-gapped:** el artefacto del sidecar incluye pesos y deps; instalable sin red.

## 8. Seguridad, privacidad y GDPR

- **PII incidental / consentimiento:** el material puede captar caras/matriculas/interiores. Requiere
  consentimiento del propietario del inmueble; el add-on no infiere identidad.
- **EXIF:** se elimina en la subida (geolocalizacion, dispositivo).
- **Aislamiento de tenant:** trabajos y artefactos aislados por instancia/organizacion.
- **SSRF / URLs arbitrarias:** prohibido; solo referencias `runtime://` y whitelist de origen; sin fetch
  de URLs suministradas por el usuario.
- **Validacion de subida:** tipo/tamano/mimetype; rechazo de payloads no media.
- **Escaneo de malware:** el material subido se escanea antes de procesar.
- **Cuotas / backpressure / DoS:** `max_concurrent_jobs`, `max_frames`, `max_upload_mb`, cola acotada.
- **Prompt injection vía metadatos:** los metadatos de media se tratan como datos, nunca como
  instrucciones para un agente.
- **Secretos por referencia:** tokens de sesion del sidecar por `secretref://`; nunca en claro (los
  bundles de secretos usan age/X25519, ver [Spec H](../h-security-trust-signing-secrets.md)).
- **Procesamiento local:** el material nunca se sube al Hub ni a terceros.
- **Control de acceso:** los artefactos heredan el control de acceso de la ficha.
- **Borrado irreversible:** la purga elimina binarios y referencias; auditada.

## 9. Licencias y NOTICE (requisitos de revision, no conclusiones legales)

- **Codigo LingBot Map:** declarado Apache-2.0 en GitHub. **Pesos:** `LICENSE.txt` del modelo en
  HuggingFace declara **Apache-2.0**. **Requisito de revision legal:** confirmar ausencia de terminos de
  uso adicionales del modelo y la atribucion NOTICE de dependencias heredadas (VGGT, DINOv2, FlashInfer).
- Estas son **tareas de revision**, no conclusiones legales. El repositorio mixto **permanece MIT** hasta
  la auditoria (ver [ADR-0008](../../adr/0008-oss-commercial-boundary-and-license.md)).

## 10. Frontera OSS / premium, visibilidad y entitlement

- **Core OSS (`real-estate-3d-capture-core`):** carril `public`, espejable, sin cuenta Hub, **sin**
  entitlement. Contiene el contrato del adaptador tipado, el skill, las plantillas de flow y la
  documentacion. Ver [manifiesto](../../schemas/examples/pack.real-estate-3d-capture-core.yaml) y
  [politica de acceso](../../schemas/examples/package-access-policy.real-estate-3d-capture-core.example.json).
- **Add-on premium (`real-estate-3d-capture`):** carril `verified-premium`, requiere el entitlement de
  capacidad **`real_estate_3d_capture`** y se obtiene por download grant de un solo uso. Distribuye el
  sidecar, la provenance firmada del modelo, el panel de UI y los workflows de operacion. Ver
  [manifiesto](../../schemas/examples/pack.real-estate-3d-capture.yaml) y
  [politica de acceso](../../schemas/examples/package-access-policy.real-estate-3d-capture.example.json).
- **Sin DRM.** La degradacion es graciosa (ver [Spec G](../g-entitlements-subscriptions-degradation.md)):
  el acceso del owner y la exportacion se preservan siempre.
- **Nota de id:** el brief sugeria `real_estate.3d_capture`, pero el patron de `required_entitlements`
  (`^[a-z][a-z0-9_]*$`) prohibe puntos; el id canonico es **`real_estate_3d_capture`**.

## 11. Degradacion graciosa

- **Personal sin GPU:** el skill `property_3d_tour` se instala pero opera en modo informativo; explica que
  requiere el add-on premium y una GPU. Nunca falla la instancia.
- **Sidecar/modelo no disponible:** los trabajos nuevos se rechazan con `gpu_unavailable`/`model_unavailable`
  (reintentable); los artefactos ya publicados siguen accesibles y exportables.
- **Team BYOC:** GPU en infraestructura del cliente; el add-on habla al sidecar por mTLS.
- **Team managed:** la GPU la aporta el operador gestionado segun la modalidad
  ([Spec J](../j-deployment-modalities.md)).

## 12. Observabilidad

- **Metricas:** trabajos por estado, latencia p50/p95 de reconstruccion, uso de GPU/VRAM, coste estimado,
  tasa de fallo, profundidad de cola.
- **Eventos estructurados** sin PII: `job_created`, `job_completed`, `job_failed`, `artifact_published`,
  `artifact_deleted`, `quota_rejected`.
- **Logs sin PII** y **trazas** por trabajo. **SLOs** y **contabilidad de coste/GPU** por instancia y por
  organizacion (ver [Spec L](../l-observability-audit-ops.md)).

## 13. Plan P0 / P1 / P2

- **P0 (PoC):** wrapper FastAPI estrecho sobre LingBot Map con `POST /v1/jobs`, `GET /v1/jobs/{id}`,
  `GET /v1/jobs/{id}/artifacts`, `DELETE /v1/jobs/{id}` y **un** GLB visible en navegador. Skill + flow
  minimos; sin cuotas avanzadas.
- **P1:** cuotas/backpressure, retencion, panel de UI, cancelacion, provenance firmada, mTLS BYOC.
- **P2:** multiples formatos/optimizaciones, contabilidad de coste fina, contribucion upstream o fork
  mantenido.

## 14. Criterios de aceptacion (Given/When/Then), tests, benchmark y go/no-go

- **Given** un walkthrough de 2-3 min y una GPU baseline, **When** el asesor lanza la captura, **Then** se
  obtiene geometria reconocible y un **GLB visible en navegador en menos de 10 min**.
- **Given** el carril public, **When** el core declara `required_entitlements`, **Then** la validacion
  **falla** (fixture negativo).
- **Given** el carril premium, **When** falta el entitlement, **Then** el add-on **no se activa**.
- **Tests:** los definidos en ambos manifiestos (`skill_installs`, `graceful_without_sidecar`,
  `sidecar_health`, `entitlement_gate`, `poc_walkthrough`, `retention_purge`).
- **Benchmark:** definir hardware baseline y medir latencia/calidad; **tratar los umbrales de calidad como
  baselines medidos, no como garantias**. Las metricas ~20 FPS / >10k cuadros son **claims** del paper, no
  reproducidos aqui.
- **Gates de seguridad:** EXIF eliminado, sin binding publico, sin fetch de URL arbitraria, cuotas activas.
- **Go/No-go:** PoC supera el walkthrough dentro de presupuesto y los gates de seguridad.

## 15. Dependencias, riesgos, preguntas abiertas y estrategia upstream

- **Dependencias:** proyecto OSS LingBot Map (GPU, PyTorch/CUDA), pack `real-estate-agency`, patron de
  sidecar de la Spec M.
- **Riesgos:** **sin API de servicio, sin tests, sin CI, sin releases/tags, sin PyPI** en el upstream
  (confirmado vía GitHub API y PyPI 404 el 2026-07-20). Version `0.1.0` solo en `pyproject`. Coste GPU.
  Confirmacion legal de terminos/atribucion pendiente.
- **Preguntas abiertas:** (1) RFC de contrato para sidecar-config/model-provenance/UI-extension; (2) pin
  exacto de SHA-256 de pesos al fijar una release; (3) formato del descriptor de panel de UI.
- **Estrategia upstream:** **envolver y fijar** (wrap/pin) una revision concreta; **no** copiar a ciegas ni
  exponer el viewer `viser` publicamente. Contribuir aguas arriba fixes de empaquetado/estabilidad; si el
  upstream no publica releases estables, mantener un **fork fijado**.

## 16. Fuentes (verificadas 2026-07-20)

- **Repositorio oficial:** <https://github.com/Robbyant/lingbot-map> (Apache-2.0).
- **Paper arXiv:** <https://arxiv.org/abs/2604.14141> ("Geometric Context Transformer for Streaming 3D
  Reconstruction").
- **Modelo y licencia (HuggingFace):** <https://huggingface.co/robbyant/lingbot-map> (Apache-2.0,
  `LICENSE.txt`).
- **Peso auxiliar `skyseg`:** <https://huggingface.co/JianyuanWang/skyseg>.
- **Contexto de evaluacion:** informe interno `Nexus_OS_Evaluacion_LingBot_Map_Real_Estate.md`.

**Contratos relacionados:** [`nexus.pack`](../../schemas/v1alpha1/nexus.pack.schema.json),
[`package-access-policy`](../../schemas/v1alpha2/package-access-policy.schema.json),
[`desired-state`](../../schemas/v1alpha1/desired-state.schema.json). **Arquitectura:**
[system-wide](../../architecture/nexus-os-architecture.md). **Modelo de paquete:**
[Spec F](../f-package-artifact-model.md). **Mapa canonico:** [`docs/README.md`](../../README.md).
