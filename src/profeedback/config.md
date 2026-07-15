# Opciones de ProFeedback

Ajusta todo desde el botón **Configuración** del complemento (Herramientas → Complementos → ProFeedback → Configuración). Los cambios se aplican al instante; los visuales se ven en la siguiente tarjeta.

## Carpetas de sonidos

Los sonidos se leen de la carpeta `sonidos` (dentro de `user_files` si existe), con esta estructura:

- `sonidos/correcto`: suenan al acertar (Bien/Fácil).
- `sonidos/finalizado/mazo`: al terminar el mazo actual, cuando todavía quedan otros mazos.
- `sonidos/finalizado/todo`: cuando ya no queda ningún mazo pendiente.
- `sonidos/perfecto-mazo`: al terminar un mazo con todas las respuestas Bien/Fácil (momento dorado). Si está vacía, suena el de `finalizado/mazo`.
- `sonidos/perfecto-todo`: al terminar todos los mazos con el día perfecto. Si está vacía, suena el de `finalizado/todo`.

En cada carpeta puedes poner varios archivos `.mp3` y elegir el que quieras en el panel, con su botón **Probar** al lado.

## Opciones

- **answerSoundEnabled** (`true`/`false`): reproducir sonido al acertar. Por defecto: `true`.
- **sessionSoundsEnabled** (`true`/`false`): reproducir sonido al terminar de repasar. Por defecto: `true`.
- **confettiEnabled** (`true`/`false`): confeti al terminar (dorado si todo fue Bien/Fácil). Por defecto: `true`.
- **styledButtonsEnabled** (`true`/`false`): botones de respuesta 3D de colores. Por defecto: `true`.
- **flagsEnabled** (`true`/`false`): insignias en la tarjeta. Por defecto: `true`.
- **answerSound**, **deckFinishSound**, **allDoneSound**, **deckPerfectSound**, **allPerfectSound** (`string`): archivo elegido de su carpeta. Vacío o inexistente ⇒ se elige uno al azar.

## Notas

- Solo se usan archivos `.mp3`.
- El volumen es el del propio Anki (el mismo que el audio de tus tarjetas).
- La interfaz del panel se muestra en el idioma de Anki (57 idiomas; inglés como respaldo).
- Las claves `confettiDay...` son estado interno del contador diario: no las edites.
