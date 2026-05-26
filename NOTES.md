# Notas

## Qué hice y por qué

### 1. Onboarding sin fricción

El repo original asumía que ya tenías Postgres corriendo localmente, sabías ejecutar las migraciones a mano y podías adivinar el comando de seed. Esa fricción se acumula: cada compañero nuevo, cada corrida de CI, cada "¿podés reproducir esto?".

Agregué `Dockerfile` + `compose.yml` + `Makefile` para que `make dev` sea todo el flujo de onboarding: construye la imagen, espera a que Postgres esté sano (healthcheck real con `pg_isready`, no un sleep), corre las migraciones automáticamente desde el entrypoint, seed a la DB y sigue los logs. Un comando, laptop limpia, app corriendo con datos.

### 2. Eliminación de N+1 en los endpoints de lista

`list_posts`, `search_posts` y `posts_by_tag` eran los peores casos. Cada uno iteraba sobre todos los posts y emitía una query separada para `post.author` y `post.tags.all()`. Sin paginación, la tabla completa de 100 k filas se devolvía y serializaba en cada request. Bajo tráfico real eso hubiera colapado

La corrección tiene dos partes. Primero, `select_related("author").prefetch_related("tags")` colapsa las queries por post en un join y un único `IN` — una página paginada de 20 posts ahora cuesta 3 queries sin importar el tamaño de página. Segundo, `@paginate(LimitOffsetPagination)` hace que el ORM solo traiga el slice pedido; la DB nunca ve el full scan.

También corregí `get_post`: traía el post desnudo y luego accedía a `post.author`, `post.tags.all()` e iteraba los comentarios tocando `c.author` en cada uno. Un post con 500 comentarios emitía 502+ queries. Pasar `select_related("author").prefetch_related("tags", "comments__author")` a `get_object_or_404` lo reduce a 4 queries fijas. El incremento de `view_count` pasó a ser un `UPDATE ... SET view_count = view_count + 1` atómico para eliminar la race condition de lectura-modificación-escritura.

### 3. Índice trigram para búsqueda

`search_posts` hacía `ILIKE '%término%'` sobre `title` y `body`. Eso compila a un full table scan — ningún índice B-tree puede acelerar un wildcard inicial. Con 100 k posts y cuerpos de 600 caracteres era la query más lenta del codebase por lejos.

La corrección es una migración que habilita `pg_trgm` y agrega un `GinIndex` con `gin_trgm_ops` en ambas columnas. Postgres enruta automáticamente las queries `ILIKE` por el índice trigram; no hay cambios en la query en sí. La extensión es estándar en cualquier Postgres 12+, así que no hay nueva dependencia de infraestructura.

---

## Qué deliberadamente no hice

**Búsqueda full-text con `SearchVector`.** Hubiera sido la respuesta "correcta" a largo plazo — ranking, stemming, soporte de idiomas. Pero requiere o desnormalizar una columna `tsvector` manteniéndola actualizada con un trigger, o calcular el vector en cada query. El índice trigram es un fix de una migración que hace que la query existente sea suficientemente rápida para esta escala. Lo revisaría si la calidad de búsqueda (ranking por relevancia) se convirtiera en un requerimiento de producto.

**Autenticación.** Los endpoints son abiertos. No agregué auth porque estaba fuera de scope y hacerlo a medias (p. ej. un token hardcodeado) hubiera sido peor que no hacerlo.

**Caché.** Los endpoints de lectura son ahora suficientemente rápidos desde la DB. Introducir una capa de caché (Redis, per-view caching) agrega complejidad operacional y bugs de invalidación. Querría benchmarks a nivel de query que muestren que realmente estamos bottlenecked antes de agregarlo.

**Tocar los modelos ORM.** Mantuve todos los cambios en la capa de queries. Agregar `db_index=True` en `Post.created_at` o `Post.is_published` podría ayudar a los endpoints de lista, pero quería que los cambios fueran auditables sin cuestionar el diseño del schema.

---

## Qué haría después con otro día

**Índice en `Post.is_published` y `Post.created_at`.** Cada query de lista filtra por `is_published = true` y ordena por `created_at DESC`. Un índice parcial en `(created_at DESC) WHERE is_published = true` permitiría a Postgres saltear las filas no publicadas completamente y servir el orden desde el índice.

**Benchmarkear `get_post` con distribución realista de comentarios.** El seed concentra comentarios en un pequeño porcentaje de posts (distribución long-tail). Algunos posts van a tener decenas de miles de comentarios. Devolverlos todos en una sola respuesta no es viable — `get_post` necesita su propia paginación de comentarios antes de ir a producción.

**Connection pooling.** Django abre una nueva conexión a Postgres por request. Bajo cualquier carga real eso se convierte en el cuello de botella antes que las queries. PgBouncer en modo transaction delante de Postgres es el fix estándar y sería mi próximo cambio de infraestructura.

**Definir qué significa "production-ready" para este codebase.** Por ahora es ambiguo. Querría alinear en un checklist corto antes de llamar a algo production-ready: estrategia de autenticación, `DEBUG = False` con un `SECRET_KEY` real, logging estructurado (JSON a stdout, no el default de Django), endpoint de health-check (`/healthz`), Sentry o equivalente para error tracking, y una política de seguridad para migraciones (sin locks en tablas grandes, plan de rollback). Sin esa definición acordada, "production readiness" se convierte en scope infinito y nada sale.
