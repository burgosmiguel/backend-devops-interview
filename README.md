# Blog API

A small content service: users, posts, comments, tags. Django + Ninja + Postgres.

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con el plugin Compose

## Quickstart

```sh
make dev
```

Construye las imágenes, levanta la DB, corre migraciones, seed y sigue los logs. La app queda disponible en <http://localhost:8000/api/docs>.

El seed escribe ~100 k posts y ~500 k comentarios — espera unos minutos la primera vez.

## Otros comandos

```sh
make test        # corre la suite de tests
make shell       # shell dentro del contenedor
make logs        # tail de logs de la app
make seed-force  # borra y re-seed la DB
make down        # detiene y elimina los contenedores
```

## API

| Método | Path | Descripción |
|--------|------|-------------|
| GET    | `/api/posts` | Posts publicados, más nuevos primero |
| GET    | `/api/posts/search?q=` | Búsqueda por título y cuerpo |
| GET    | `/api/posts/by-tag/{slug}` | Posts con un tag dado |
| GET    | `/api/posts/{id}` | Detalle de post con comentarios |
| POST   | `/api/posts` | Crear un post |
| POST   | `/api/posts/{id}/comments` | Agregar un comentario |
| GET    | `/api/users/{id}` | Perfil de usuario con conteos |
| GET    | `/api/users/find?email=` | Buscar usuario por email |

## Stack

- Python 3.14 · Django 5 · django-ninja · Postgres 16
- `uv` para gestión de dependencias
- Docker + Compose para el entorno de desarrollo
