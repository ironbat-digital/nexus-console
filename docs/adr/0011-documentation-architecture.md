# ADR-0011: Arquitectura de documentación y canonicidad

- **Estado:** Aceptada (solo documentación; sin cambios de contrato)
- **Fecha:** 2026-07-19
- **Versión de arquitectura:** `v1alpha1` + `v1alpha2` (documental)
- **Relacionadas:** [Visión de Nexus OS](../vision/nexus-os-vision.md), [arquitectura system-wide](../architecture/nexus-os-architecture.md), [Spec B](../specs/b-nexus-hub.md), [mapa de documentación](../README.md), [glosario §nomenclatura](../architecture/glossary.md#nomenclatura)

## Contexto

El conjunto documental tenía **especificaciones canónicas en competencia**: dos documentos de visión
(Portal Gestionado `v1alpha1` y Personal + Hub `v1alpha2`) y solapamiento entre la "arquitectura del
portal gestionado" y las necesidades de desarrollo del Hub. Esto obligaba a un lector a reconciliar
documentos para saber cuál era autoritativo. Además, el nombre de producto de visualización (`Nexus OS`)
y los identificadores técnicos (`NexusOS`, `nexus`, `$id` de esquema) se usaban de forma inconsistente.

Esta ADR **no reescribe** decisiones históricas (ADR-0001…0010); fija la arquitectura de documentación y
la política de canonicidad.

## Decisión

1. **Un documento canónico por rol.** Existe exactamente uno de cada:
   - Visión: [`vision/nexus-os-vision.md`](../vision/nexus-os-vision.md).
   - Arquitectura system-wide: [`architecture/nexus-os-architecture.md`](../architecture/nexus-os-architecture.md).
   - Desarrollo del Hub: [`specs/b-nexus-hub.md`](../specs/b-nexus-hub.md), que consolida portal, setup
     gestionado, onboarding y sitio web.
   - Una especificación canónica por cada componente no-Hub ([`specs/`](../specs/README.md), a–m).
2. **Sin borrar historia.** Los documentos superados se conservan como **stubs de redirección** que
   apuntan al canónico, para no romper enlaces entrantes.
3. **Nomenclatura.** `Nexus OS` es el nombre de visualización; los identificadores técnicos estables
   (`NexusOS`, `nexus`, `$id` de esquema, repos, paquetes, APIs, símbolos) **no** se renombran para
   insertar un espacio. Regla en el [glosario §nomenclatura](../architecture/glossary.md#nomenclatura).
4. **Índice autoritativo.** [`docs/README.md`](../README.md) es el mapa canónico: documento, alcance,
   estado y superados.
5. **Guarda automática.** Un test verifica la unicidad de los documentos canónicos y que los stubs
   declaran su redirección, además del test existente de resolución de enlaces relativos.
6. **Contratos intactos.** No se cambia ningún `$id`, esquema ni semántica `v1alpha1`/`v1alpha2`. Los
   cambios son puramente documentales.

## Consecuencias

- Un lector encuentra un único documento autoritativo por tema, sin reconciliar competidores.
- Los enlaces entrantes y la historia se preservan vía stubs.
- Coste: mantener los stubs y la guarda de unicidad; a cambio, se elimina la ambigüedad.

## Canonicidad respecto a `ironbat-jarvis`

La Visión histórica de Nexus OS y RFC-001 viven en `ironbat-jarvis` (Nexus Platform). La visión y la
arquitectura de este repositorio son autoritativas para el plano de control y la capa de producto (Hub,
Operator, Registry, ediciones, entitlements). Un PR compañero incorpora este delta a la visión de
`ironbat-jarvis`.

## Alternativas consideradas

- **Borrar los documentos superados:** rechazado; rompería enlaces entrantes e historia.
- **Renombrar identificadores técnicos a `Nexus OS`:** rechazado; rompería compatibilidad de contratos,
  namespaces y APIs sin beneficio.
- **Mantener visiones múltiples con nota de reconciliación:** rechazado; es justo la ambigüedad que se
  quiere eliminar.
