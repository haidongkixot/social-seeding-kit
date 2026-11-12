# Social Seeding Kit

Un plugin de Claude Code que ayuda a una persona a hacer seeding de su marca en grupos y fanpages de Facebook sin romper las reglas de los grupos ni de Facebook. Claude encuentra hilos adecuados, redacta respuestas que encajan con cada conversación, las contrasta con tus datos aprobados y te presenta una cola numerada. **Tú apruebas cada elemento. Claude no publica nada por su cuenta.**

Una página web (el centro de control) es donde configuras el sistema, marcas aprobaciones, lo pausas y sigues los resultados.

Idiomas de la página y de estos documentos: English ([README.en.md](README.en.md)), Tiếng Việt ([README.vi.md](README.vi.md)), Español.

## Qué incluye
- **Scout**: lee las últimas publicaciones de tus grupos activos (solo lectura) y puntúa los hilos.
- **Conversation manager**: sigue cada conversación desde la primera respuesta hasta una invitación (Semilla, Con interacción, Cualificado, Invitado, Unido).
- **Redactor, revisor y gestor de riesgo**: redactan borradores, revisan datos y tono, y mantienen la cola del día dentro de los límites diarios, el ritmo y el calentamiento. Un control de salud califica tu cuenta VERDE, ÁMBAR o ROJA.
- **Centro de control** (una página publicada por Claude): Configuración, Canales, Aprobaciones, Panel, Control.
- **Informes** cada dos semanas, con sugerencias basadas en datos.

## Instalación
Guía paso a paso (en/vi): [GUIDE.en.md](GUIDE.en.md). Consulta también [INSTALL.md](INSTALL.md). En resumen:
```
/plugin marketplace add <ruta-o-repositorio-github>
/plugin install social-seeding@social-seeding-kit
```
Después, en una carpeta vacía, abre Claude Code y ejecuta `/social-seeding:seeding-setup`.

## Configuración (una vez por marca)
1. `/seeding-setup` comprueba las herramientas, hace unas preguntas y crea tu carpeta de **espacio de trabajo** (configuración, datos, playbooks, ejecuciones, conversaciones). Tus datos viven ahí; actualizar el plugin nunca los toca.
2. Publica el **centro de control**. Abre su pestaña **Configuración**: marca y representante, categorías, destinos del embudo (un grupo de WhatsApp, Telegram, Zalo, Messenger o un sitio web por categoría), idiomas, datos, canales, límites y horario.
3. Ejecuta `/sync-control`. Tus cambios se escriben en el espacio de trabajo y se validan.
4. El primer día es **solo borrador**: ves borradores y no se puede publicar nada.

## La rutina diaria
| Cuándo | Comando | Qué ocurre |
|---|---|---|
| Por la mañana | `/daily-run` | Control de salud, escaneo, borradores, revisión y filtro de riesgo. La cola aparece en la pestaña Aprobaciones. |
| Cuando la hayas mirado | marca en la página y dile a Claude "aprobado como marqué", o responde "aprobar 1-5; editar 3: ...; descartar 6" | Claude te muestra lo aprobado y `/post-approved` publica solo eso, espaciado y con la identidad correcta. |
| Por la tarde | `/hot-replies` | Otra pasada para buscar publicaciones nuevas de compradores. |
| Cada hora | `/check-replies` | Comentarios y mensajes nuevos, a partir de los correos de notificación de Facebook si Gmail está conectado. Redacta respuestas y te avisa. |
| Cuando quieras | `/health-check`, `/sync-control`, `/publish-status` | Salud de la cuenta, aplicar cambios de la página, actualizar el panel. |
| Cada dos viernes | `/biweekly-report` | Informe de embudo, calidad, riesgo y canales. |

## Reglas de seguridad (fijas)
Están en `plugins/social-seeding/SAFETY.md` y no se pueden cambiar desde la configuración, la página ni el chat.
1. Solo identidad real y declarada: tu perfil, indicando el rol en la marca. Sin personajes falsos.
2. No se publica nada sin tu aprobación en el chat. Las marcas de la página son propuestas.
3. Claude nunca inicia sesión, nunca gestiona 2FA ni CAPTCHA, y se une a grupos solo cuando se lo pides.
4. Solo conducta que cumpla las normas: límites, ritmo, relevancia, calentamiento. Nada de evasión.
5. Los datos salen únicamente de los archivos de conocimiento aprobados.
6. Sin mensajes privados en frío.
7. En tablones de venta al por mayor: responder solo a publicaciones de compradores, como máximo una publicación de oferta al día, enlaces solo tras el calentamiento.
8. Sin datos personales aparte de las personas que interactuaron contigo y un contacto que ellas mismas te dieron.

## Lo que tienes que hacer tú
- Iniciar sesión en Facebook en el navegador que usa Claude in Chrome y mantenerla abierta.
- Unirte tú mismo a los grupos y fanpages, una oleada cada vez, y poner cada canal en Activo con la fecha en que te uniste.
- Revisar cada idioma antes de usarlo en vivo (alguien que lo hable con fluidez, o tú).
- Aprobar los datos: márcalos en la página.
- Anotar cada semana los miembros de cada destino del embudo (las altas se miden a partir de ahí).
- Opcional: conectar Gmail y activar los correos de notificación de Facebook.

## Estructura de carpetas
```
plugins/social-seeding/   el plugin: agentes, skills, scripts, página, plantillas, SAFETY.md
workspace/ (el tuyo)      config/*.toml, knowledge/, playbooks/, runs/, conversations/, leads.csv, risk/, reports/
```
Archivos de configuración: `brand.toml`, `catalog.toml`, `funnel.toml`, `channels.toml`, `caps.toml` (con `[languages]`), `keywords.toml`. `python scripts/validate.py` los comprueba todos.
