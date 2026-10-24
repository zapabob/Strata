<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <b>Español</b> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Caché KV Spin(8) Triality, DeepSeek-V4.1 Sin Censura, Cargador GGUF y Memoria a Largo Plazo</h3>

<p align="center">
  <b>Fork de ingeniería de <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Upstream Integrado · Atención Spin(8) $\mathrm{Cl}(8,0)$ Triality · DeepSeek-V4.1-Flash MLA Sin Censura · Verificación de Contenido GGUF · Memoria a Largo Plazo Hermes y Hakua · Optimizado para 32 GB RAM
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Visión general de este Fork (`zapabob/Strata`)

**`zapabob/Strata`** es un fork avanzado sincronizado con la última versión upstream v0.2.4.2 / motor 0.1.49.2 de [Strata](https://github.com/Niko1221/Strata). Además de ejecutar modelos MoE de 125B parámetros (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) en una sola PC mediante streaming coordinado entre VRAM, RAM y SSD, este fork integra **Caché KV Spin(8) Triality**, **derivados sin censura DeepSeek-V4.1**, **carga segura de modelos GGUF basada en contenido** y **memoria a largo plazo para agentes**:

1. **Biblioteca de Transformación Ortogonal Spin(8) Triality y $\mathrm{Cl}(8,0)$ ([`spin8/`](spin8/README.md))**
   - Basada en octoniones reales ($1, e_1, \dots, e_7$) y generadores de Clifford simétricos $\mathrm{Cl}(8,0)$.
   - Descompone espinores 16×16 en tres representaciones octodimensionales: **Vector ($V$)**, **Semiespín Positivo ($S_+$)** y **Semiespín Negativo ($S_-$)**.
   - Auditoría matemática de cada plan de rotación antes de su admisión ($E_F \le 10^{-12}$).
   - Transformadas de Sylvester-Hadamard y monitor de invariantes en tiempo de ejecución (`spin8_monitor`).

2. **Caché KV Triality de Tres Vistas y Dialectos TurboQuant CUDA ([`tqcodec/`](tqcodec/README.md))**
   - **Caché CUDA de Tres Vistas (`cache_cuda.cu`)**: Matrices de claves rotadas ($V, S_+, S_-$), valores cuantizados compartidos, softmax online y corrección de residuos **QJL**.
   - **Dialectos asíncronos**: `TQ4_1S` (4.25 bpw), `TQ3_0S` (3.3125 bpw) y `PQ2_0` (2.50 bpw).
   - **Optimización SM120 (Serie RTX 50)**: Memoria compartida dinámica que ahorra 3.375 GiB de reserva de pila VRAM en CUDA.

3. **Derivados Sin Censura DeepSeek-V4.1-Flash-1017 y Backend MLA ([`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py))**
   - Soporte nativo para matrices de proyección Multi-Head Latent Attention (MLA) mediante el backend `strata-dsv41`.
   - Modelos precalificados: Base ISTA, receta de reemplazo abliterada Kiwimaker Maya-S y paquete independiente AtomicChat.
   - Supresión automática de vectores de rechazo en modelos abliterados para evitar distorsiones de respuesta.

4. **Resolver ModelBundle Basado en Contenido y Enrutador Local ([`strata_control/model_bundle.py`](strata_control/model_bundle.py))**
   - Análisis acotado de cabeceras ($\le 16$ MiB) y prevención de desbordamientos ($\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$, mitigando GHSA-vgg9-87g3-85w8).
   - Resumen SHA-256 en flujo continuo y detección de alteraciones.
   - Enrutamiento local determinista (`strata-dsv41`, `strata-native`, `prism`, `llama-cpp`) con **prohibición estricta de respaldo en la nube** (100% privacidad local).

5. **Memoria a Largo Plazo Hermes Agent y Hakua ([`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py))**
   - Servidor MCP stdio + CLI:
     - `SOUL.md`: Personalidad principal y directiva de afinidad Hakua con copia de seguridad automática.
     - `MEMORY.md`: Memoria episódica estructurada en formato `§ [category] YYYY-MM-DD: Title`.
     - Base SQLite de Hermes Agent (`~/.hermes/ebbinghaus_memory.db`, ~5.000 memorias indexadas).
     - Hakua Composite Memory (`~/.hakua-memory`).
   - Inyección automática en sesiones de chat mediante `apps/host/server/memory.mjs`.

6. **Presupuesto de Hardware 32GB RAM / 16GB VRAM y Ciclo de Vida Drafter Zero-VRAM**
   - Verificado en Windows 11 con 32 GB RAM y RTX 5060 Ti 16 GB (`sm_120`).
   - Respeto estricto: RAM de host $\le 24.0$ GiB, reserva de SO $\ge 4.0$ GiB, presupuesto VRAM $\le 14.0$ GiB.
   - Descarga automática del modelo borrador ante presión de memoria sin detener el proceso principal.

---

## Verificación e Integración Upstream: `v0.3.0` Upstream Integrated Edition

- **Upstream SHA**: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`
- **Parche de seguridad GUI**: `c487c875d05075113965bc61d822b27179f70639`
- **Contratos del Fork (F01–F11)**: Preservados en su totalidad.
- **Pruebas**: **71/71 pruebas Python aprobadas**, **13/13 pruebas Node.js aprobadas**.

---

## Licencia

Publicado bajo la [Licencia MIT](LICENSE).
