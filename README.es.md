# Strata · Hakua

Modelos locales, chat, herramientas y memoria Hakua opcional. Este es el [fork de zapabob](https://github.com/zapabob/Strata) de [Niko1221/Strata](https://github.com/Niko1221/Strata).

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## Versión preliminar para Windows

**0.4.1-beta.1** se actualiza manualmente y no tiene firma de código de Windows. [Versión](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1) · [Instalación](docs/HAKUA_INSTALL.md) · [Pruebas y límites](docs/HAKUA_RELEASE.md).

1. Descarga el [instalador](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe) y compara su suma con [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt).
2. Cierra Strata, incluido el icono de la bandeja, y ejecuta el instalador. Guarda modelos y datos personales fuera de la carpeta de la aplicación.
3. Descarga `strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz` de esta versión beta e impórtalo desde la pantalla de preparación. El canal latest conserva el motor anterior.
4. Elige un modelo adecuado o **Use a local GGUF** para archivos existentes. Node y Python están incluidos; no necesitas un intérprete del sistema ni un compilador.

Las versiones siguen [SemVer 2.0.0](https://semver.org/): aplicación `0.4.1-beta.1`, motor nativo/Control `0.4.1`; los entornos PrismML/TurboQuant sin cambios mantienen `0.4.0`. La ubicación habitual de la aplicación es `%LOCALAPPDATA%\Programs\Strata` en C:, independiente de los modelos. Una instalación previa puede conservar otra ubicación.

## Reutilizar archivos existentes

Para un GGUF dividido, selecciona una parte: Strata comprueba el conjunto completo. Los pesos importados permanecen en su ubicación. Un nombre genérico como `Hf` se muestra usando el nombre del archivo. Los nombres personalizados se conservan después de comprobar y reiniciar.

Antes de preparar un modelo del catálogo, Strata realiza una búsqueda limitada de conjuntos compatibles en la carpeta elegida y sus subcarpetas. Reutiliza una única coincidencia válida; si hay varias, exige seleccionar el archivo. Las descargas habituales conservan la verificación de integridad y la reanudación. El motor y las capas opcionales de borrador se gestionan por separado.

Los modelos nativos Qwen/Swift pueden necesitar una conversión inicial a pack. La pantalla muestra las capas terminadas cuando el conversor las informa. Al reanudar un pack de bajo consumo de memoria, se cuenta el espacio ya asignado a su archivo temporal. Los GGUF Hikari/PQ2_0 compatibles usan PrismML mediante **Load with Strata**, sin conversión nativa Q2_0. Para GGUF ordinarios compatibles, TurboQuant ofrece K=`FP16` y V=`TURBO2/3/4`; después hay que recargar. Consulta los [motores locales](docs/LOCAL_LLAMA_BACKENDS.md).

## Caché privada y memoria

La nueva ruta Qwen3.6 conserva la caché dentro de la misma conversación autenticada. Otra conversación u otro usuario no la reutiliza. Cambiar de conversación, cancelar, sufrir un error o pasar cinco minutos sin actividad elimina la caché privada. Las solicitudes sin identificador de conversación no reutilizan caché.

Esta ruta exige el archivo de motor validado correspondiente y su confirmación al arrancar. Los motores antiguos siguen rechazándose. Por ahora se procesa una solicitud a la vez y las cachés compartidas permanecen desactivadas. El mapped expert pack sigue siendo opcional. Las mediciones y comprobaciones pendientes figuran en el [registro de versión](docs/HAKUA_RELEASE.md).

Abre **Hakua memory** en la barra lateral. Leer y guardar requieren consentimientos separados en cada turno. PrismML/TurboQuant reinicia su servidor con autenticación y cachés privadas; termina antes cualquier solicitud activa. [Guía](serve/MEMORY_HARNESS.md).

## Componentes y límites

Aplicación/Host: `0.4.1-beta.1`; motor nativo/Control: `0.4.0`; Node: `24.22.2`; CPython: `3.12.15`; Hakua-memory: `0.3.5`. Referencia upstream: `ffa80d73` / `0.2.10`.

El componente firmado CUDA/PrismML/TurboQuant sigue siendo el de [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1). El componente experimental Qwen3.6 separado no está firmado. El instalador no incluye el motor CUDA. Las actualizaciones automáticas firmadas de la aplicación no están calificadas.

Las pruebas Windows x64 corresponden a RTX 5060 Ti, CUDA sm_120 y 32 GB de RAM. No califican otros GPU o sistemas, entrada nativa de imágenes ni un motor nativo DeepSeek independiente. La asignación heredada en RAM de Qwen3.6 puede exigir unos 18,7 GiB más reserva; 32 GB no garantizan el arranque. Una respuesta corta con 131.072 tokens de contexto no valida toda la ventana ni su calidad. Los modos K de TurboQuant siguen desactivados tras fallar pruebas de calidad. Spin(8), Triality, Query-v3 y Bonsai son experimentos opcionales. El rendimiento y los recursos necesarios dependen del modelo y del equipo.

## Desarrollo

[Modelos](docs/AI_REFERENCE.md) · [Compilación](packaging/README.md) · [Contribuir](CONTRIBUTING.md) · [Seguridad](SECURITY.md)

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

Strata usa la licencia MIT. Los pesos, Hakua-memory y las dependencias conservan sus propias licencias y avisos. El pequeño vector de control opcional está desactivado por defecto y usa la [Qwen Community License 1.0](data/experimental-speed-projection/LICENSE).
