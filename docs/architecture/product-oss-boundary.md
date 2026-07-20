# Frontera producto / open-source y forma de pricing

- **Estado:** Frontera y **modelo de licencia por componente APROBADOS** · relicencia del código existente bloqueada hasta auditoría legal · pricing numérico pendiente
- **Versión de arquitectura:** `v1alpha1`
- **Fecha:** 2026-07-19
- **Relacionadas:** [ADR-0008](../adr/0008-oss-commercial-boundary-and-license.md), [ADR-0009](../adr/0009-editions-entitlements-and-subscription-degradation.md), [Visión de Nexus OS §12–§15](../vision/nexus-os-vision.md)

> **Actualización de producto (`v1alpha2`).** La habilitación de capacidades pasa a expresarse mediante
> **ediciones** (Personal/Team/Organization) y **entitlements de capacidad** firmados, no mediante
> planes. La edición **Personal es libre y gratuita** para un propietario, sin Hub. La tabla "Forma de
> pricing" de más abajo es **ilustrativa y no decidida**: no se hardcodean precios ni nombres de plan en
> código, esquemas ni contratos. Ver [ADR-0009](../adr/0009-editions-entitlements-and-subscription-degradation.md).

## Regla de diseño explícita

**No se retiene fuera del OSS nada relacionado con seguridad, exportación o portabilidad.** Un usuario
autohospedado puede verificar firmas de packs, exportar su instancia completa y auditar su propio
sistema sin depender de ningún componente de pago. Lo que se cobra es **comodidad operativa**
(gestión, soporte, catálogo curado), **no** la soberanía ni la seguridad básica.

## Qué es OSS y qué es hospedado

| OSS (siempre disponible) | Hospedado (servicio de pago) |
|---|---|
| Runtime completo | Aprovisionamiento gestionado (Managed) |
| Operator | Hub hospedado |
| Admin API local | Broker OAuth centralizado |
| Esquemas de manifiesto (`nexus.pack.yaml`, `nexus.blueprint.yaml`, `setup.plan.yaml`) | Orquestación de secretos cifrados a escala |
| SDK y CLI | Monitorización y alertas de flota gestionadas |
| Verificador e instalador de packs | Backups gestionados |
| Cliente de Registry comunitario | Actualizaciones de flota coordinadas |
| Wizard/generador local básico | Catálogo curado y verificado |
| **Seguridad, exportación y portabilidad** | Soporte y SLA; facturación y gestión de cuenta |

## Licencia — modelo por componente APROBADO (relicencia efectiva bloqueada)

**No es consejo legal.** Decisión aprobada; detalle y procedimiento en
[ADR-0008](../adr/0008-oss-commercial-boundary-and-license.md):

- **Apache-2.0** para Runtime, Operator, CLI, SDK, esquemas/contratos públicos, verificador/instalador
  de packs, cliente de Registry comunitario y capacidades básicas locales.
- **Propietario** para Hub hospedado, facturación, provisioning/orquestación gestionada, operaciones de
  flota y catálogo curado gestionado.
- **Packs:** licencia por paquete (Apache/comunidad, comercial/propietaria u otra compatible), con
  **metadatos SPDX obligatorios**. La marca NexusOS/Ironbat es **independiente** de la licencia de
  código.

**Seguridad, exportación, portabilidad y self-hosted permanecen en OSS.** La relicencia del código
actual **no se aplica todavía**: el `LICENSE` raíz sigue siendo **MIT** y todos los archivos de
`console/` conservan MIT hasta completar una **auditoría de titularidad/contribución** bloqueante, el
consentimiento de los titulares y la decisión **CLA/DCO**, validadas por asesoría legal antes de
publicar Runtime/Operator (procedimiento y matriz ruta→licencia en ADR-0008). No bloquea el MVP.

## Forma de pricing (sin cifras)

| Plan | Para quién | Qué incluye (cualitativo) | Qué dirige el coste |
|---|---|---|---|
| **Community Free** | Desarrolladores, comunidad, self-hosted | Runtime, Operator, CLI, Registry comunitario; sin soporte garantizado | Cero para Ironbat salvo mantenimiento |
| **Managed Starter** | Individuos, freelancers (ruta simple) | Instancia gestionada, cuestionario+blueprint, catálogo curado básico, soporte por ticket/comunidad | Infra de instancia pequeña, bajo volumen LLM |
| **Pro** | Equipos pequeños, profesionales | Multi-usuario, más áreas, actualizaciones de flota, backups gestionados, SLA básico | Volumen LLM, nº usuarios, almacenamiento de memoria |
| **Business/Enterprise** | Organizaciones, verticales | BYOC o infra dedicada, catálogo verificado ampliado, SSO, auditoría avanzada, soporte prioritario | Complejidad de integración, nº usuarios, SLA contractual |

El eje de coste crece con **volumen de LLM, usuarios activos, áreas/packs instalados y nivel de
soporte**, no con funcionalidades básicas de soberanía o seguridad (disponibles en todos los planes).
**Community Free permanece gratuito indefinidamente**; el cobro empieza solo al usar infraestructura
gestionada de Ironbat (decisión #6).
