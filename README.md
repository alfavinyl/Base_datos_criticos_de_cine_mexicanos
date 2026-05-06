# 🎬 Base de Datos: Críticos de Cine Mexicanos

🚧 **Proyecto en desarrollo activo**

Sistema de gestión y consulta de críticos de cine mexicanos, sus textos, publicaciones y películas reseñadas. Construido con FastAPI, MySQL y Jinja2.

---

## 🛠️ Tecnologías

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![Jinja2](https://img.shields.io/badge/Jinja2-Templates-red)

---

## 🗃️ Estructura de la base de datos

El proyecto maneja 7 tablas con relaciones entre ellas:

- `criticos` — Datos de cada crítico
- `peliculas` — Películas reseñadas
- `publicaciones` — Medios donde publican los críticos
- `textos` — Reseñas y artículos escritos
- `palabras_clave` — Etiquetas temáticas
- `textos_peliculas` — Relación many-to-many entre textos y películas
- `textos_palabras_clave` — Relación many-to-many entre textos y palabras clave

---

## ✅ Avance actual

- [x] Diseño y creación de base de datos relacional (7 tablas)
- [x] Conexión segura a MySQL con variables de entorno
- [x] Buscador general funcional (`index.html`)
- [ ] CRUD de críticos
- [ ] CRUD de películas
- [ ] CRUD de publicaciones
- [ ] CRUD de textos
- [ ] Filtros avanzados de búsqueda

---

## 📂 Estructura del proyecto

Base_datos_criticos_de_cine_mexicanos/
├── database.py        # Conexión a MySQL

├── main.py            # Rutas y lógica principal (FastAPI)

├── templates/         # Vistas HTML con Jinja2

├── requirements.txt   # Dependencias

├── test_db.py         # Prueba de conexión

└── .env               # Variables de entorno (no incluido en el repo)
---

## 🚀 Cómo ejecutar el proyecto

**1. Clona el repositorio**
```bash
git clone https://github.com/alfavinyl/Base_datos_criticos_de_cine_mexicanos.git
cd Base_datos_criticos_de_cine_mexicanos
```

**2. Instala las dependencias**
```bash
pip install -r requirements.txt
```

**3. Crea tu archivo `.env`** con tus credenciales de MySQL:

DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_NAME=criticos

**4. Levanta el servidor**
```bash
uvicorn main:app --reload
```

**5. Abre en tu navegador**

http://localhost:8000

---

## 👤 Autor

**Fernando Teodoro Gabino**  
[LinkedIn](https://www.linkedin.com/in/fernandoteodorogabino/) • [GitHub](https://github.com/alfavinyl)
