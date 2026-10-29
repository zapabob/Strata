# Hakua / Strata

Chatbot Hakua basado en Strata. [zapabob/Strata](https://github.com/zapabob/Strata) · [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## TLDR · pasos de instalación en 30 segundos

Descarga y ejecuta el instalador Windows de este fork, elige un modelo compatible y cárgalo. Hakua memory en la barra lateral abre el chat de memoria. Los pasos llevan unos 30 segundos; descargar, instalar y cargar el modelo requiere tiempo adicional.

[Windows EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe) · [7z](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z) · [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt)

El archivo 7z contiene el mismo instalador. Extráelo y ejecuta el EXE de instalación.

## Funciones de este fork

Hakua solo lee recuerdos y guarda un resumen con tu consentimiento para esa solicitud. Las dos opciones son independientes y se restablecen después. Necesita un perfil `hakua_harness` habilitado y su propia clave, distinta de la del chat normal. Consulta la [guía de memoria](serve/MEMORY_HARNESS.md).

Las herramientas Hermes sincronizan SOUL.md / MEMORY.md aprobados e incluyen memoria Ebbinghaus, grafo semántico, exportación Obsidian y consolidación sleep. Son independientes del chat; no se incluyen las dependencias opcionales de RAG y embeddings.

Para un GGUF local PQ2_0, elige `PrismML` como motor llama-server en los ajustes avanzados del modelo. Para un GGUF estándar con TurboQuant, elige `TurboQuant` y configura K como `FP16` y V como `TURBO2`, `TURBO3` o `TURBO4`. Los formatos TurboQuant para K están desactivados en esta versión porque las pruebas reales produjeron respuestas corruptas. Vuelve a cargar el modelo después de cambiar el motor. Cada motor utiliza sus propios ejecutables y bibliotecas incluidos; PQ2_0 y TurboQuant son vías distintas. Consulta [la configuración y los límites](docs/LOCAL_LLAMA_BACKENDS.md).

Los experimentos Spin(8)/Triality, Query-v3 y Bonsai requieren ajustes compatibles y explícitos. No se promete una mejora general de velocidad o calidad.

Incluye Node y Python privados, Hakua-memory 0.3.5 y un motor CUDA compilado desde este fork. Al iniciar un modelo no se instalan paquetes Python ni se compila código.

## Compatibilidad y actualizaciones

Este paquete Windows es para NVIDIA RTX serie 50, CUDA sm_120. Otras GPU, Linux y macOS necesitan paquetes separados. El instalador original no contiene estos cambios. Los pesos se descargan aparte y pueden ocupar decenas o cientos de GB. Prefiere paquetes compatibles ISTA-DASLab, después Unsloth y Gyro.

Guarda modelos y recuerdos fuera de la carpeta del programa. No se distribuyen recuerdos personales, claves ni pesos. Cierra la aplicación antes de actualizar. Para volver atrás, conserva una copia de tus datos e instala una versión anterior del fork.

[Models](docs/MODELS.md) · [Install](docs/INSTALL.md) · [Hermes tools](tools/hakua_hermes_memory_stack.py)

## Versiones y verificación

| | |
| --- | --- |
| GUI / Product | `0.3.3-preview.20261030.1` |
| Engine | `0.3.3` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Upstream | `46c152a1` · 2026-10-28 |

<!-- App version in this preview tree: `0.3.3-preview.20261030.1` -->

Esta vista previa no está firmada. Comprueba SHA256SUMS.txt antes de instalar. El [informe de validación](docs/HAKUA_RELEASE.md) indica resultados reales y limitaciones. Compilar no demuestra una inferencia correcta. Esta vista previa sin firma se actualiza manualmente con el instalador; las actualizaciones automáticas firmadas aún no están verificadas.

## Desarrollo y soporte

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Fork de Strata con licencia MIT. Hakua-memory y los pesos tienen licencias propias. Se mantiene el reconocimiento a los autores originales.

El vector de control opcional de upstream (480 KB) está desactivado de forma predeterminada y usa [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE). Los pesos completos del modelo se descargan por separado.
