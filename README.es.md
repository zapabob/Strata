# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata es la bifurcación de [Niko1221/Strata](https://github.com/Niko1221/Strata) orientada a Windows. Ejecuta modelos locales para chat, programación y tareas con agentes. El motor nativo puede distribuir los pesos de expertos entre la memoria gráfica, la RAM y el SSD en modelos MoE compatibles.

## Primeros pasos

Descarga el instalador de Windows para tu cuenta desde las [versiones de Hakua](https://github.com/zapabob/Strata/releases). El motor CUDA se distribuye por separado. En **Modelos**, elige el perfil asociado a los pesos instalados. Inkling 2 Mini SC117 ofrece perfiles SQ-10, SQ-15 y SQ-20. Ajusta el contexto a la memoria disponible. Consulta la [guía de Windows](docs/HAKUA_INSTALL.md) y la [documentación de modelos](docs/MODELS.md).

## Reutilizar flujos de trabajo

Activa la búsqueda de habilidades bajo demanda en **Configuración → Herramientas**. El agente puede buscar y abrir las que necesite sin cargar el catálogo completo. En **Habilidades**, el aprendizaje de tareas terminadas y la aplicación automática se activan por separado. Las instrucciones se guardan en un archivo `SKILL.md` editable. La selección automática usa nombres, frases de activación y el espacio de trabajo. Las habilidades, los agentes auxiliares, las operaciones con archivos y `/goal` tienen controles independientes. [Guía de flujos de trabajo](docs/WORKFLOW_SKILLS.md)

## Mediciones y límites

Con una RTX 5060 Ti de 16 GB, SC117 SQ-10 generó mediante `/goal` una escena Pagoda Bench en un único HTML y corrigió su propio renderizador tras recibir diagnósticos. Chrome mostró cinco tejados al alejar la vista. La escena informó de 7.079 vóxeles. La vista inicial recortaba la parte superior y no se midió una puntuación oficial. Las [mediciones del motor 0.8.5](_docs/2026-11-27_v085-release-notes.md) corresponden a entradas cortas con la capacidad de contexto indicada.

El [registro de versiones](docs/HAKUA_RELEASE.md) describe compatibilidad, firmas y alcance de las pruebas. Hakua se distribuye con [licencia MIT](LICENSE). Los modelos y componentes tienen condiciones propias.
