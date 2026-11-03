# Hakua / Strata

Chatbot Hakua sobre Strata. Esta bifurcación ofrece una vista previa de Windows con Hakua memory y runtimes GPU separados. [zapabob/Strata](https://github.com/zapabob/Strata) · upstream [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Instalación (vista previa Windows)

1. Descarga el [EXE de instalación](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.4/Strata_0.4.0-preview.20261103.4_x64-setup.exe).
2. Compáralo con [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.4/SHA256SUMS.txt) antes de ejecutarlo. No hay firma de código Windows. SHA-256 del EXE: `9bf5f4c9090484a35a8e3534d310840303cd7d3b1684ebbce272e01fd9937724` (114.979.368 bytes).
3. Sal de Strata por completo (bandeja → Salir de Strata) si ya está instalado y ejecuta el EXE.
4. En el primer inicio, instala el motor firmado ofrecido o importa el `.tar.gz` correspondiente de la misma release. Luego elige una carpeta de modelos y carga un modelo.

La secuencia de clics es corta. Descargas, activación del motor y carga del modelo tardan más y necesitan disco y VRAM. Detalles: [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md). Límites medidos: [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md).

## Qué incluye el instalador

| En el instalador de la app | Por separado |
| --- | --- |
| GUI / Host, Node privado 24.22.2, Control / CPython 3.12.15, Hakua-memory 0.3.5, Harness | Componente CUDA firmado (~1,4 GB): Strata nativo + PrismML + TurboQuant |
| Actualizaciones manuales con este EXE | Pesos del modelo (decenas o cientos de GB) |

No necesitas Node, Python, pip ni compilador del sistema para la app publicada. El instalador upstream de Niko1221 no incluye los cambios de esta bifurcación.

## Cargar un modelo local

- **Paquetes Strata nativos** (paquetes de texto Qwen admitidos): ruta nativa prepare / load de la app.
- **Hikari / PQ2_0 GGUF**: usa **Load with Strata** (PrismML). No uses prepare nativo para PQ2_0.
- **GGUF habitual + caché TurboQuant**: backend `TurboQuant`, K=`FP16`, V=`TURBO2` / `TURBO3` / `TURBO4`, y vuelve a cargar. Los modos K de TurboQuant siguen desactivados tras respuestas corruptas en pruebas reales.

PrismML y TurboQuant son ejecutables distintos dentro del componente del motor. Detalles: [LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md). Prefiere paquetes que quepan: ISTA-DASLab → Unsloth → Gyro.

Cuando un modelo sirve por la ruta Strata / supervisor, Agent puede usar esa instancia local para herramientas que el modelo soporte (por ejemplo búsqueda web). Una sesión solo nativa no expone el mismo camino.

## Hakua memory

Tras cargar un modelo admitido, abre **Hakua memory** en la barra lateral. Consentimientos de lectura y guardado independientes; se reinician en cada turno.

- Nativo: pega la clave del diálogo en About → Settings y marca memoria en la página local.
- PrismML / TurboQuant: la app aporta la clave local; termina las peticiones activas antes de abrirlo la primera vez.

Guía: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md). Las herramientas Hermes SOUL/MEMORY son aparte del chat y no hacen falta para el uso básico.

## Versiones

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261103.4` |
| Engine / Control | `0.4.0` (CUDA sm_120) |
| Hakua-memory | `0.3.5` |
| Congelación upstream | `ffa80d73` · 0.2.10 |

Página de release: [v0.4.0-preview.20261103.4](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.4). El instalador y el paquete de motor Qwen3.6 de esta etiqueta no están firmados. El feed Ed25519 y el motor firmado de `v0.4.0-preview.20261101.1` siguen en su sitio. Las actualizaciones automáticas firmadas de la app no están cualificadas; actualiza con este instalador. El instalador no incluye el motor CUDA. El paquete Qwen3.6 no tiene lector de imágenes y `signature` es null. PrismML y TurboQuant siguen en el componente firmado. La línea principal es Qwen3.6-35B-A3B UD-Q4_K_XL, contexto 65536, KV FP32, MTP 2, prefill auto. Las rutas nuevas son opt-in. Un ajuste no aplicado, o una petición de caché privada, se rechaza antes de arrancar. El mapped expert pack solo si se pide y el SHA-256 del motor es `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5` o `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046`. El resumen anterior sigue permitido. El arena de host anterior sigue siendo el predeterminado. El tiempo de arranque y la velocidad de tokens no se midieron. El CUDA spill guard no pasó la baseline revisada. En un PC de 32 GB, UD-Q4_K_XL puede rechazarse antes del arranque si la RAM física libre no cubre el arena legacy de 18,75 GiB más la reserva. Eso no es una medida de que quepa en 16 GB de VRAM.

## Límites (vista previa medida)

Windows x64, NVIDIA RTX 50 / CUDA sm_120, comprobado en RTX 5060 Ti. Incluye texto nativo. No incluye entrada de imagen nativa ni el motor DeepSeek nativo separado. Otras GPU y SO necesitan sus propios paquetes. Mantén modelos y memoria personal fuera de la carpeta de la app. La release no incluye memorias personales, claves ni packs completos de pesos.

Spin(8) / Triality / Query-v3 / Bonsai siguen siendo experimentos opcionales. No hay promesa general de velocidad o calidad.

## Desarrollo

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

Bifurcación Strata con licencia MIT. Hakua-memory y los pesos tienen licencias propias. Se mantiene el crédito a autores y upstream. El vector de control opcional (~480 KB) permanece desactivado por defecto bajo [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
