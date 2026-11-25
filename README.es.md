# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**IA local diseñada para aprovechar cada recurso de tu PC con Windows: GPU, núcleos físicos + hilos SMT de la CPU, memoria RAM del sistema y almacenamiento NVMe/SSD.** Hakua es el fork independiente `zapabob/Strata` de [Niko1221/Strata](https://github.com/Niko1221/Strata), alineado con el upstream oficial **v0.2.21** (`d46f5f268`, motor/Control `0.1.67`), conservando todos los motores propios del fork, los flujos de memoria/agentes y las optimizaciones Blackwell CUDA 13.5.

## Novedades en 0.8.1 (Motor 0.7.0)

- **Inferencia heterogénea de máquina completa en los 4 niveles de hardware (GPU + CPU 6P/6SMT + RAM + SSD)**:
  - **Backend nativo Windows `aux_cpus` CPU Sets + división SMT para E/S** (`engine/include/strata/platform/aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`): fija el bucle host de GPU y el cómputo AVX2 MoE estrictamente a los núcleos físicos primarios, mientras dedica todos los hilos SMT secundarios (`io_smt=[1,3,5,7,9,11]` en una CPU 6C/12T) a Direct I/O solapado de 6 hilos y streaming asíncrono `PrefetchVirtualMemory`.
  - **5 motores nativos compilados con CUDA 13.5 / SM120 Blackwell** (`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`) con doorbells zero-copy mapeados Gen-K/L, protección VRAM WDDM de 1536 MiB, presupuestos de RAM Windows seguros en commit (`hy4_cpu_experts.cpp`, `inkling2_engine.cu`), fijación a núcleos físicos en Windows + esperas `_mm_pause` (`ink_hybrid.cuh`), y staging de embeddings en memoria fijada + `PrefetchVirtualMemory` por lotes en SM120 Q38 (`engine/q38/src/engine.cu`).
  - **Lanzador unificado de máquina completa y perfiles**: `tools/full_machine_infer.py` (`--list-models`, `--plan`, `--bench`, `--serve`) sondea automáticamente GPU, topología física/SMT de CPU, margen de RAM/commit y SSDs para generar planes de ejecución en 3 niveles y configuraciones listas bajo `configs/`.
- **Fusión 3-way con el upstream oficial v0.2.21**: integra el MoE unificado de 4 niveles GPU+RAM+CPU+SSD, `--layer-split` multi-GPU, actualizaciones de GUI/host y correcciones de Control/motor `0.1.67` junto con todas las funciones del fork (`/btw`, `/deepresearch`, RustXNG Full, habilidades de flujo de trabajo, ejecutor denso Q38, extensión DeepSeek, proveedor Hermes `inkling2` y tablas de perfiles Inkling-2 MIT de kuraneko1).

## Benchmarks medidos en hardware real

Medido en **NVIDIA GeForce RTX 5060 Ti 16 GB (SM120, CUDA 13.5) · AMD Ryzen 5 4500 (6C/12T) · 32 GB DDR4 · Doble SSD (`C:` Crucial P3 NVMe + `H:` S5-1TB SSD)** con prompts de 16 tokens y decodificación greedy de 32 tokens:

| Modelo (Tamaño) | Motor y contexto | Niveles activos | Prefill (`pp`) | Decode (`tg`) | Paridad |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10.85 GiB (2232 exps) + RAM fijada 4.34 GiB (840 exps) + 6P/6SMT | **85.08 t/s** | **42.22–42.33 t/s** | **32/32 exacto** |
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | Desborde 3 niveles: GPU 10.85 GiB + RAM 3.60 GiB + **SSD mmap 0.74 GiB (`prefetch=on`)** + 6P/6SMT | 64.80 t/s | 14.24 t/s | **32/32 exacto** |
| **Inkling-2-Mini UD Q4_K_M** (15.47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10.42 GiB (2339 exps) + RAM fijada 3.34 GiB (733 exps) + 6P/6SMT | **109.64 t/s** | **53.28 t/s** | Greedy limpio |
| **Qwen3.8-27B 3.69bpw MTP** (11.73 GiB) | `strata-q38.exe` · 4K (F16 KV) | Pesos GPU SM120 (10.44 GiB) + staging emb en RAM fijada + `PrefetchVirtualMemory` | 6.21 s en frío | **29.95 t/s** | Greedy limpio |

*Nota de hilos CPU (A/B en Ryzen 5 4500)*: mantener los workers de cómputo en los 6 núcleos físicos (`host=0`, `workers=2,4,6,8,10`) con los hilos SMT (`1,3,5,7,9,11`) dedicados a E/S alcanzó **42.22–42.33 t/s**, frente a **29.68 t/s** (-21.9 %) al sobresuscribir 11 workers de cómputo sobre hermanos SMT.

## Versión y descargas

Versión actual: **0.8.1** — GitHub Latest: [página de la release v0.8.1](https://github.com/zapabob/Strata/releases/tag/v0.8.1).

- **Instalador de escritorio**: `Strata-0.8.1-windows-x64-setup.exe` (app Tauri/NSIS por usuario con Node 24.22.3, Python, Control 0.6.3 y RustXNG Full incluidos).
- **Paquete del instalador**: `Strata-0.8.1-windows-x64.tar.7z` (instalador + `SHA256SUMS.txt`).
- **Componente de motor CUDA 13.5 SM120 (opcional)**: `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` (los cinco motores SM120 recompilados: `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`).
- **Componente Hy4-Flash (opcional)**: `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`.

Descarga siempre directamente desde la lista **Assets** de la release y verifica los hashes SHA-256. La verificación de firma ed25519 de componentes está desactivada (sin clave de firma); no hay firma Windows Authenticode; **`releaseQualified=false`**.

![Hakua / Strata chat japonés real en Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*Escritorio Hakua / Strata ejecutando `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` con `strata-q38.exe` (CUDA 13.5 / RTX 5060 Ti 16 GB).*

## Inicio rápido (CLI de máquina completa y Escritorio)

### Instalación de escritorio o actualización por sobrescritura

1. Finaliza las solicitudes activas, descarga los modelos, haz copia de seguridad de tus datos de la app y cierra Strata (incluido el icono en la bandeja del sistema).
2. Ejecuta `Strata-0.8.1-windows-x64-setup.exe` en tu carpeta de instalación actual para actualizar conservando modelos, chats, memoria, herramientas, claves API y aprobaciones.
3. Importa `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` mediante *I already have the file*, elige un modelo compatible o un GGUF local y pulsa **Load**. Consulta [instalación y reversión](docs/HAKUA_INSTALL.md).

### Lanzador de máquina completa (`tools/full_machine_infer.py`)

```powershell
# Inspeccionar niveles GPU/CPU/RAM/SSD y detectar modelos locales
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Ejecutar benchmark Sakura Inkling-2-Mini 131K con ajustes de máquina completa
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# Iniciar servidor API local OpenAI/Anthropic (127.0.0.1:8092) con RAM squeeze
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## GGUF recomendado y funciones del fork

- **Chat local Qwen3.8-27B en 16 GB de VRAM**: probado con [el GGUF cuantizado mixto 3.69 bpw de soyaakinohara](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) (créditos a **soyaakinohara** y **AEON-7**). Empieza con contexto de 4,096 tokens; la etiqueta `12GB` del nombre no garantiza ajuste en tarjetas de 12 GB.
- **Ejecutor denso propio Q38 (`strata-q38.exe`)**: polimorfismo de cuantización mixta por tensor en 11 formatos (`F32`, `F16`, `BF16`, `Q8_0`, `Q4_K`, `Q5_K`, `Q6_K`, `IQ3_S`, `IQ2_S`, `IQ4_XS`, `PQ2_0`), prefill con Tensor Cores, modos KV Spin(8) / TurboQuant (`auto`: `f16` → `f16_turbo4` → `spin8_k8v4`), borrador/verificación MTP `K=3` y perfil ortográfico japonés opcional. Ver [QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md).
- **Herramientas de agentes y flujos de trabajo**: subagente de consulta lateral `/btw` sin herramientas con parada independiente, `/research` y `/deepresearch` con RustXNG Full integrado (consulta proveedores externos cuando está habilitado), aprendizaje/aplicación privada opcional de habilidades de flujo, CRUD de archivos en workspace/barra lateral y memoria de chat con ámbito. Ver [WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md) y [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md).

## Límites de seguridad y alcance

Sin cambios: **3 GiB de RAM disponible**, **4 GiB de margen de commit**, **>= 768 MiB de reserva GPU** (`1536 MiB` WDDM por defecto para Inkling-2 `<= 17 GiB`), **5 GiB libres en `C:`** y **10 GiB libres en `H:`**. La calidad general del modelo, la generación de ventana completa y la concurrencia multi-cliente simultánea en GPU siguen sin calificar (**`releaseQualified=false`**). Esta versión Windows del fork no incluye entrada nativa de imágenes ni inferencia calificada en Linux/macOS. Los registros históricos conservan sus versiones originales en [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Documentación y desarrollo

[Instalación](docs/HAKUA_INSTALL.md) · [Evidencia de release](docs/HAKUA_RELEASE.md) · [API y hardware](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [Compilación desde fuente](docs/SOURCE_INSTALL.md) · [Empaquetado](tools/packaging/README.md) · [Contribuir](.github/CONTRIBUTING.md) · [Seguridad](.github/SECURITY.md) · [Licencia](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [Avisos de terceros](third_party/)

## Agradecimientos

Sincero agradecimiento a **Niko1221/Strata**, **kuraneko1 (`_ryu15_`)**, **ggml & llama.cpp**, **NousResearch (Hermes Agent)**, **Qwen Team (Alibaba Cloud)**, **NVIDIA**, **RustXNG**, **libstrix**, **Node.js / Python / Tauri**, **Microsoft**, **ISTA-DASLab**, **PrismML**, **TurboQuant**, **Spin(8)**, **soyaakinohara** y **AEON-7** por las bases de código abierto, pesos e investigación que hacen posible Hakua / Strata.
