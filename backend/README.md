# Backend — API del portafolio

Flask 3 + PostgreSQL 16 + SQLAlchemy 2. Sirve el contenido que antes estaba hardcoded en
`frontend/src/data/profile.js` y `frontend/src/i18n/{es,en}.js`.

- Lecturas públicas sin auth, escrituras con JWT de admin.

## Despliegue con Docker (todo: Postgres + Flask + frontend)

Desde la raíz del repo (donde está `docker-compose.yml`):

```bash
cp .env.example .env          # pon secretos reales dentro
docker compose up -d --build  # levanta db + backend + frontend
```

El backend aplica las migraciones al arrancar (`docker-entrypoint.sh` espera a Postgres y
corre `flask db upgrade`), así que la primera vez el esquema se crea solo. **No siembra
datos: las tablas quedan vacías.**

Falta un único paso manual, la cuenta de admin:

```bash
docker compose exec backend flask users create-admin \
  --email tu@email.com --full-name "Tu Nombre" --password 'TuClaveDe8OMas'
```

Comprobar:

```bash
curl localhost:5001/api/v1/health          # {"status":"ok","db":"ok"}
curl localhost:5001/api/v1/projects        # {"data":[], ...}
```

| Servicio | Host | Dentro de la red Docker |
|---|---|---|
| Postgres | `localhost:5433` | `db:5432` |
| Backend | `localhost:5001` | `backend:5000` |
| Frontend | `localhost:8080` | `frontend:80` |

Puertos elegidos así porque en macOS el 5000 lo ocupa AirPlay y el 5432 suele tenerlo otro
Postgres local.

Con la base vacía, `GET /bio` y `GET /about` devuelven **404** hasta que crees la bio:

```bash
TOKEN=$(curl -s -X POST localhost:5001/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"tu@email.com","password":"TuClaveDe8OMas"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")

curl -X PUT localhost:5001/api/v1/admin/bio \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"full_name":"Clara Justino Limaco","email":"...","phone":"...",
       "translations":{"es":{"role_label":"Ingeniera de Software"},
                       "en":{"role_label":"Software Engineer"}}}'
```

El resto del contenido se crea igual, con `POST /admin/<recurso>`.

### Operaciones habituales

```bash
docker compose logs -f backend            # logs
docker compose restart backend            # reiniciar (vuelve a aplicar migraciones)
docker compose exec backend flask routes-json   # listar rutas
docker compose down                       # parar (los datos siguen en el volumen pgdata)
docker compose down -v                    # parar Y BORRAR la base entera
```

## Desarrollo local sin Docker

Solo Postgres en Docker, Flask en el host:

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
docker compose -f ../docker-compose.yml up -d db
.venv/bin/python -m flask db upgrade                     # crea el esquema (11 tablas)
.venv/bin/python -m flask users create-admin --email tu@email.com
.venv/bin/python -m flask run --port 5001
```

`flask seed-all` existe pero es **opcional**: carga contenido de ejemplo (el que estaba
hardcoded en el frontend). No lo corras si quieres la base vacía.

## Comandos

| Comando | Qué hace |
|---|---|
| `flask db upgrade` / `db migrate -m "..."` | aplicar / generar migraciones Alembic |
| `flask db check` | avisa si los modelos difieren del esquema |
| `flask seed-all` | **opcional**: carga contenido de DEMO (idempotente) |
| `flask users create-admin` / `users set-password` | cuentas de admin |
| `flask routes-json` | lista todas las rutas |
| `flask db-reset` | borra y recrea el esquema (solo desarrollo) |
| `pytest` | 43 tests (requiere la DB `website_test`) |
| `ruff check . && black .` | lint y formato |

Para los tests, crea la base una vez:

```bash
docker exec website-db-1 psql -U website -d website -c "CREATE DATABASE website_test;"
```

## API

Prefijo `/api/v1`. Todos los GET aceptan `?lang=es|en` (default `es`). Si falta la
traducción pedida se devuelve la del idioma por defecto y `meta.lang_fallback: true`.

### Público

Un módulo por sección de la web: [app/api/about.py](app/api/about.py),
[app/api/projects.py](app/api/projects.py) y [app/api/beyond.py](app/api/beyond.py).

| Método | Ruta | Notas |
|---|---|---|
| GET | `/health` | `{"status":"ok","db":"ok"}` |
| GET | `/bio` | contacto + redes + foto |
| GET | `/about` | agregado: bio + experiencia + educación + idiomas |
| GET | `/education`, `/experience`, `/languages` | listas ordenadas |
| GET | `/social-links` | |
| GET | `/projects` | `?tag=&featured=&page=&per_page=` |
| GET | `/projects/<slug>` | detalle + galería |
| GET | `/tags` | tags de proyectos en uso, con su conteo |
| GET | `/beyond` | lista de entradas, `?tag=&status=&page=&per_page=` |
| GET | `/beyond/tags` | tags en uso con su conteo |
| GET | `/beyond/<slug>` | detalle + galería |
| GET | `/files/<filename>` | imagen (en producción la sirve nginx) |

### Auth

`POST /auth/login` (5/min) · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me`

### Admin (requiere `Authorization: Bearer <token>`)

CRUD uniforme para `education`, `experience`, `languages`, `projects`, `beyond`:

```
GET|POST       /admin/<recurso>
GET|PUT|DELETE /admin/<recurso>/<group_id>
PATCH          /admin/<recurso>/reorder   body: {"items":[{"id":..,"display_order":..}]}
```

El `<group_id>` de la URL es el `<entidad>_id`, no el `id` de una fila: identifica el ítem
completo, con sus dos idiomas. Un `DELETE` borra las dos filas.

`GET|PUT /admin/bio` (singleton, PUT hace upsert) ·
`GET|POST|PUT|DELETE /admin/social-links[/<uuid>]` ·
`GET|POST /admin/media`, `PATCH|DELETE /admin/media/<uuid>`

Cuerpo de escritura: lo neutro arriba, el texto agrupado por idioma. Cada clave de
`translations` es una fila.

```json
{
  "is_featured": true,
  "tags": ["Flask", "Postgres"],
  "translations": {
    "es": { "title": "Backend del portafolio", "data": "API Flask con Postgres." },
    "en": { "title": "Portfolio backend", "data": "Flask API with Postgres." }
  }
}
```

Un `PUT` con un solo idioma actualiza solo esa fila; la otra se conserva. Los campos
neutros se escriben en **todas** las filas del grupo, para que no se desincronicen.

Galerías: `images` va dentro de cada idioma (los captions se traducen) como
`[{"media_id": "...", "caption": "..."}]`. El backend resuelve la URL al escribir.

### Respuestas

```json
{ "data": [...], "meta": { "lang": "es", "page": 1, "per_page": 12, "total": 34 } }
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": { "campo": "..." } } }
```

## Estructura

```
app/
├── api/
│   ├── about.py      # Sobre mí: /bio, /about, /education, /experience, /languages
│   ├── projects.py   # Proyectos: /projects, /projects/<slug>, /tags
│   ├── beyond.py     # Más allá del código: /beyond, /beyond/tags, /beyond/<slug>
│   ├── admin.py      # CRUD generado desde una tabla de recursos
│   ├── auth.py  media.py  health.py  helpers.py
├── models/           # una clase por entidad, filas por idioma
├── schemas/          # payloads.py (entrada, Pydantic) · output.py (serializers)
├── services/         # i18n.py (localized/fallback) · query.py · storage.py
└── config.py  errors.py  extensions.py  cli.py

tests/                # test_about.py · test_projects.py · test_beyond.py ·
                      # test_admin.py · test_media_and_i18n.py · test_health.py
```

## Modelo de datos

**11 tablas.** Las traducciones viven en la misma tabla que el contenido: una fila por
idioma, con `language` y un id de grupo compartido.

```
education(id, education_id, language, title, institution, start_date, ...)

 id  education_id  language  title                       institution
 A1  G1            es        Ingeniería en Sistemas...   Universidad Nacional
 A2  G1            en        B.Eng. in Computer Sys...   Universidad Nacional
 B1  G2            es        Certificación en Arqui...   Plataforma de Certificación
 B2  G2            en        Cloud Architecture Cert...  Plataforma de Certificación
```

- `id` — único por fila.
- `education_id` — el id del ítem: lo comparten sus traducciones. Es el `id` que devuelve la
  API y el que aceptan las rutas de admin.
- `language` — `'es'` o `'en'`, con `CHECK`. `UNIQUE(education_id, language)` impide dos
  filas del mismo idioma.

Tablas de contenido: `bio`, `education`, `experience`, `language_skill`, `project`,
`beyond_item`. Sin idioma: `social_link` (LinkedIn no se traduce), `media_asset`.
Infra: `admin_user`, `token_blocklist`, `alembic_version`.

`project` y `beyond_item` comparten forma: neutros `slug`, `tags varchar[]`, `cover_id`
(+ `status` en beyond); traducidos `title`, `data` y `images JSONB`. El texto largo se
llama `data` en las dos. En `education` y `experience` ese campo sigue siendo
`description`.

`beyond_item` no tiene categorías ni columnas por afición: qué es cada entrada sale de
`tags`, y lo específico (autor, cámara, disciplina) va en `metadata_json`. `status` acepta
`reading | finished | wishlist | ongoing | archived`.

Todas las de contenido llevan `metadata_json JSONB`, `display_order`, `is_published`,
`created_at`, `updated_at`, y PK `uuid` con `gen_random_uuid()` (pgcrypto).

### Consecuencias de tener una sola tabla por entidad

Conviene tenerlas presentes antes de escribir SQL a mano:

1. **Los campos neutros se repiten** en la fila ES y en la EN (fechas, `slug`, `institution`,
   `tags`, `cover_id`). La API los escribe siempre en todas las filas del grupo
   (`_write_group` en `app/api/admin.py`); un `UPDATE` manual a una sola fila las
   desincroniza.
2. **No hay FKs hacia una entidad**, porque una FK no puede apuntar a algo que ocupa dos
   filas. Por eso los tags son una columna `varchar[]` (con índice GIN) y las galerías son
   `images JSONB` — no existen `tag`, `project_tag` ni `project_image`.
3. **`UNIQUE(slug)` pasa a `UNIQUE(slug, language)`**: el mismo slug existe dos veces, uno por
   idioma. La unicidad real se comprueba por grupo (`unique_group_slug`).
4. **Leer es un `WHERE`, no un `JOIN`**: `localized()` en `app/services/i18n.py` hace
   `WHERE language IN (pedido, default)` + `DISTINCT ON (group_id)` para caer al idioma por
   defecto cuando falta la traducción, marcándolo con `meta.lang_fallback`.
5. **`GET` devuelve `id` (el del grupo) y `row_id`** (el de la fila servida), más `language`.
   El frontend usa `id`; `row_id` es para depurar.

### Otras decisiones

- **Fechas, no etiquetas.** `experience.start_date`/`end_date` son `DATE`; el
  `"2022 — Presente"` se calcula en `app/schemas/output.py:format_period` según el idioma.
- **`metadata_json` como escape.** Los campos propios de cada afición (autor de un libro,
  cámara de una foto, disciplina de flex) viven ahí: añadir una afición nueva no necesita
  migración. Los seeds guardan ahí su `seed_key`.
- **Los tags son una columna** `varchar[]`, slugificados y deduplicados al escribir.
  `GET /tags` los lista con su conteo.
- **`language_skill` tiene dos "idiomas"**: `code` es el idioma del que habla la fila
  (`en` = inglés) y `language` es el idioma en que está escrita.
- **`meta` en Python = `metadata_json` en la DB**: `metadata` es un nombre reservado por
  SQLAlchemy.
- **Los seeds son idempotentes** por `metadata_json->>'seed_key'`, no por slug o
  institución: esos se pueden editar desde la API y el match crearía un duplicado.

## Seguridad

- `.env` no se commitea. Genera secretos reales antes de exponer nada:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
  Los `change-me` de `.env.example` sirven solo en local (los tests avisan de que la clave
  HMAC es corta).
- No hay endpoint de registro: los admins se crean por CLI.
- El upload decodifica la imagen con Pillow en vez de confiar en la extensión, limita a 5 MB
  y deduplica por SHA-256.
- Login con rate limit y mensaje idéntico para email inexistente y password incorrecta.
- Logout mete el JWT en `token_blocklist`.
- El límite en memoria de Flask-Limiter no se comparte entre workers de gunicorn: para
  producción, apunta `RATELIMIT_STORAGE_URI` a Redis.

## Pendiente para el frontend

El backend ya sirve todo esto, pero el frontend sigue leyendo sus diccionarios estáticos:

- `fetch` con `VITE_API_URL` y `?lang={locale}` desde `src/i18n/LanguageContext.jsx`.
- Adelgazar `es.js`/`en.js` a solo labels de UI (`nav.*`, `common.*`); el contenido viene de la API.
- El nav tiene `nav.beyond_code` sin backend detrás: esa sección quedó fuera del alcance.
- Los tags sirven para agrupar en la UI: pedir `/tags` y filtrar con `?tag=flask`.
- `ProjectCard` con `tags`, `data` y `cover.url` reales; `ImageSlot` recibiendo `src`.
- Proxy `/api` en `vite.config.js` para evitar CORS en desarrollo.
