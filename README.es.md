<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <b>Español</b> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Caché KV Triality Spin(8), Dialectos CUDA TurboQuant y Motor de Inferencia MoE Nativo</h3>

<p align="center">
  <b>Fork de ingeniería de <a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a></b> · Atención Triality Spin(8) $\mathrm{Cl}(8,0)$ · Caché KV Cuantizada de Tres Vistas · Sidecars Query-v3 `.prismq3` · Control Completo en GUI y CLI
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## Descripción General de este Fork (`zapabob/Strata`)

**`zapabob/Strata`** es un fork de investigación e ingeniería basado en [Strata](https://github.com/Niko1221/Strata) (v0.2.2 / motor 0.1.47). Además de ejecutar modelos Mixture-of-Experts de 125 mil millones de parámetros (**Qwen3.8-Flash-Next**, **Qwen3.6-35B-A3B**, **Gyro**, **Swift 1.5**, **NVFP4**) en un solo PC combinando VRAM de la GPU, RAM del sistema y SSD, este fork incorpora una arquitectura completa de **Spin(8) Triality y Caché KV TurboQuant** en el motor C++/CUDA, el servidor Python, la CLI y la interfaz gráfica Desktop/Web:

### Las 4 Innovaciones Clave de este Fork

1. **Biblioteca de Transformaciones Ortogonales Spin(8) Triality y $\mathrm{Cl}(8,0)$ ([`spin8/`](spin8/README.md))**
   - Basada en la base real de octoniones ($1, e_1, \dots, e_7$) y generadores simétricos $\mathrm{Cl}(8,0)$ ($\Gamma_0, \dots, \Gamma_7$).
   - Descompone espinores 16×16 por quiralidad en tres representaciones de 8 dimensiones: **Vector ($V$)**, **Semispín Positivo ($S_+$)** y **Semispín Negativo ($S_-$)**, cumpliendo la identidad entrelazadora $U \Gamma(v) U^\top = \Gamma(Rv)$.
   - Cada plan de rotación se audita matemáticamente antes de su admisión: error de ortogonalidad de Frobenius $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$, error máximo de Gram $\le 10^{-12}$ y log-determinante con signo mediante factorización LU con pivoteo ($\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$).
   - Incluye transformaciones de Sylvester Hadamard normalizadas para bloques potencia de dos ($n = 1 \dots 1024$, incluyendo máscaras Spin(8) 8D y bloques Bonsai 128D) y un monitor de auditoría persistente (`spin8_monitor`) cada 1.024 tokens o 60 segundos.

2. **Caché KV Triality de Tres Vistas y Dialectos CUDA Asíncronos TurboQuant ([`tqcodec/`](tqcodec/README.md))**
   - **Caché CUDA física de tres vistas (`cache_cuda.cu`)**: Mantiene tres arreglos de claves (K) rotadas físicamente independientes ($V, S_+, S_-$) y un arreglo compartido de valores (V) cuantizados por cabezal de atención, evaluados mediante softmax en línea de una sola pasada con pesos de consenso en el símplex $(\alpha_0, \alpha_1, \alpha_2)$ y corrección residual gaussiana **QJL**.
   - **Dialectos CUDA asíncronos exactos**: `TQ4_1S` (4,25 bits/peso), `TQ3_0S` (3,3125 bits/peso) y `PQ2_0` (2,50 bits/peso).
   - **Optimización de memoria compartida dinámica para SM120 (RTX serie 50)**: El kernel `audit_kernel` emplea memoria compartida dinámica (`65.536` bytes) en lugar de arreglos locales `float f[128 * 128]` (64 KiB/hilo), eliminando la reserva de pila CUDA de **3,375 GiB (`3.623.878.656 B`)** durante `tqc_cache_cuda_initialize` (`audit_local=0`, `audit_delta=0`) y permitiendo que las tres vistas (`off`, `f32`, `compressed`) se ejecuten de forma estable en una GPU de 16 GiB / 32 GiB de RAM.

3. **Adaptador Query-v3 Versionado y Sidecars `.prismq3`**
   - Implementa una carta tangente racional acotada sobre los 7 generadores antisimétricos derivados de bloques $\mathrm{Cl}(8,0)$ auditados, controlada por un adaptador de rango 8 sobre consultas normalizadas ($Q$) antes de la codificación posicional (RoPE).
   - Soporta ejecución CUDA fusionada sin asignaciones dinámicas (`query_v3_cuda.h`) y archivos sidecar `.prismq3` verificados por SHA-256 (`--query-v3-sidecar`) para **Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** y **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)**.

4. **Integración Completa en GUI, CLI y Plano de Control**
   - **Interfaz Gráfica Desktop y Web (`apps/host`)**: Configura **K cache type**, **V cache type** (`f16`, `tq3`, `tq3_spin8_hadamard`, `tq3_spin8_native`), **Spin(8) KV cache mode** (`off`, `f32`, `compressed`), **Spin(8) native config path** y **Spin(8) native config SHA-256** directamente en **Settings → GPU & memory** con validación previa en tiempo real (`run-config-check.mjs`).
   - **CLI y Servidor Python (`strata_cli`, `strata_control`, `serve/server.py`)**: Soporte completo mediante `strata launch --set ...` y `strata serve` con verificación previa de cápsulas JSON y resumen SHA-256.

---

## Última Versión del Fork: `v0.3.0-preview.20261024.2`

- **Página de lanzamiento**: [GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **Archivo integrado (Motor + GUI + Control)**: `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **Tamaño**: `412.311.508` bytes
  - **SHA-256 del archivo**: `7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **SHA-256 del motor (`strata.exe`)**: `564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **Vista previa CLI anterior**: [`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [Notas técnicas](docs/releases/preview030.md) · [PoC de Triality](research/triality_poc/README.md)

---

## Inicio Rápido (Funciones del Fork)

### 1. En la Interfaz Gráfica (GUI)

1. Extrae `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z` (primero el `.7z` y luego el `.tar`) o sobrescribe tu instalación local en `%LOCALAPPDATA%\Programs\Strata` y `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13`.
2. Abre **Settings → GPU & memory**.
3. Configura los parámetros de caché KV y Spin(8) (`cache_type_k`, `cache_type_v`, `spin8_mode`, `spin8_native_config`, `spin8_native_sha256`).

### 2. Desde la Terminal (`strata` CLI)

```powershell
# Inicio predeterminado (compatible con upstream)
strata launch --model q2_0 --yes --no-tui

# Inicio con caché KV TurboQuant de 3 bits y rotación de Hadamard
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# Inicio con cápsula nativa Spin(8) de tres vistas verificada por SHA-256
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\ruta\a\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

---

## Requisitos de Hardware y Tamaños de Modelo

**Se requieren al menos 32 GB de memoria combinada (RAM del sistema + VRAM de la GPU)**. Strata ofrece endpoints compatibles con OpenAI (`/v1/chat/completions`, `/v1/responses`) y Anthropic (`/v1/messages`) para Claude Code, Codex CLI y OpenCode.

| Memoria combinada (RAM + VRAM) | Modelo recomendado | Notas |
| --- | --- | --- |
| **28–32 GB** | **[Gyro-S](docs/GYRO.md)** (27,6 GB) o **[Coder](docs/MODELS.md#coder)** | Gyro-S para equipos ajustados; Coder conserva la mitad de los expertos para programación. |
| **35–40 GB** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39,2 GB) o **Gyro-M** (35 GB) | Swift 1.5 razona más rápido; Gyro-M se acerca a IQ3_XXS con ~20 % menos de VRAM. |
| **48 GB** | **IQ3_XXS** (47,0 GB) | Mayor precisión que las cuantizaciones de 2 bits. |
| **64 GB** | **IQ3_S** (54,8 GB) o **Q2_0** | IQ3_S iguala al modelo completo en benchmarks; Q2_0 ofrece la máxima velocidad (94 tok/s en RTX 5070). |
| **96 GB o más** | **UD-IQ4_XS** (72 GB) a **Q8_0** (136 GB), **[NVFP4](docs/NVFP4.md)** | Modelos de 4 a 8 bits cuando todos los expertos caben en RAM. |

---

## Compilación y Pruebas desde el Código Fuente

```powershell
# Biblioteca de referencia Spin(8) (CPU)
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# Pruebas de integración tqcodec (CPU + CUDA + Spin8)
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure

# Motor CUDA nativo (strata.exe / spin8_verify)
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify

# Pruebas de interfaz Host GUI y control
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## Créditos y Licencia

- **Ingeniería del Fork (`zapabob/Strata`)**: Caché Triality Spin(8) $\mathrm{Cl}(8,0)$, dialectos CUDA `tqcodec`, adaptador Query-v3 `.prismq3`, optimización de memoria compartida dinámica SM120 `audit_kernel` e integración completa GUI/CLI.
- **Proyecto Upstream ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: Motor de streaming MoE de tres niveles, caché de expertos, decodificación especulativa, aplicación Desktop y Terminal CLI.
- **Licencia**: Publicado bajo la [Licencia MIT](LICENSE). Los binarios redistribuibles de CUDA/cuBLAS y Microsoft Visual C++ incluidos en los paquetes conservan los términos de sus respectivos fabricantes.
