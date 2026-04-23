from fastapi import FastAPI, Request, Form 
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from database import get_connection

app = FastAPI()
templates = Jinja2Templates(directory="templates")

#----------------------------------------------------------------------#
# BUSCADOR
# main.py (añade esta función después de las importaciones)

def buscar_en_todas_tablas(termino: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    termino_busqueda = f"%{termino}%"

    # Consulta con UNION ALL (13 parámetros en total)
    query = """
    (SELECT 
        id,
        titulo AS nombre,
        CONCAT(titulo, ' (', anio, ')') AS descripcion,
        'pelicula' AS tipo
     FROM peliculas
     WHERE titulo LIKE %s OR titulo_original LIKE %s OR director LIKE %s)
    
    UNION ALL
    
    (SELECT 
        id,
        CONCAT(nombre, ' ', apellidos) AS nombre,
        seudonimo AS descripcion,
        'critico' AS tipo
     FROM criticos
     WHERE nombre LIKE %s OR apellidos LIKE %s OR seudonimo LIKE %s OR biografia LIKE %s)
    
    UNION ALL
    
    (SELECT 
        id,
        titulo AS nombre,
        resumen AS descripcion,
        'texto' AS tipo
     FROM textos
     WHERE titulo LIKE %s OR resumen LIKE %s OR texto_completo LIKE %s)
    
    UNION ALL
    
    (SELECT 
        id,
        etiqueta AS nombre,
        NULL AS descripcion,
        'palabra_clave' AS tipo
     FROM palabras_clave
     WHERE etiqueta LIKE %s)
    
    UNION ALL
    
    (SELECT 
        id,
        nombre,
        descripcion,
        'publicacion' AS tipo
     FROM publicaciones
     WHERE nombre LIKE %s OR descripcion LIKE %s)
    
    ORDER BY tipo, nombre;
    """

    # Parámetros: 3 (pelis) + 4 (criticos) + 3 (textos) + 1 (palabras) + 2 (publicaciones) = 13
    params = (termino_busqueda, termino_busqueda, termino_busqueda,
              termino_busqueda, termino_busqueda, termino_busqueda, termino_busqueda,
              termino_busqueda, termino_busqueda, termino_busqueda,
              termino_busqueda,
              termino_busqueda, termino_busqueda)

    cursor.execute(query, params)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados
#----------------------------------------------------------------------#
# RUTA DEL BUSCADOR 
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/buscar", response_class=HTMLResponse)
async def buscar(request: Request, q: str = ""):
    if not q:
        # Si no hay término, redirigir al inicio o mostrar mensaje
        return RedirectResponse(url="/", status_code=302)
    
    resultados = buscar_en_todas_tablas(q)
    
    # Agrupar resultados por tipo para mostrarlos organizados en la plantilla
    # (esto también se puede hacer en la plantilla con filters de Jinja2, pero lo haremos aquí para simplificar)
    agrupados = {}
    for r in resultados:
        tipo = r['tipo']
        if tipo not in agrupados:
            agrupados[tipo] = []
        agrupados[tipo].append(r)
    
    # Definir nombres amigables para cada tipo
    nombres_tipo = {
        'pelicula': 'Películas',
        'critico': 'Críticos',
        'texto': 'Textos',
        'palabra_clave': 'Palabras clave',
        'publicacion': 'Publicaciones'
    }
    
    return templates.TemplateResponse(
        "resultados.html",
        {
            "request": request,
            "resultados": agrupados,
            "nombres_tipo": nombres_tipo,
            "busqueda": q
        }
    ) 
#----------------------------------------------------------------------#
# RUTA PARA DETALLE DE PELICULA 
@app.get("/pelicula/{id}", response_class=HTMLResponse)
async def detalle_pelicula(request: Request, id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener datos de la película
    cursor.execute("SELECT * FROM peliculas WHERE id = %s", (id,))
    pelicula = cursor.fetchone()
    
    # Obtener los textos asociados a esta película (a través de textos_peliculas)
    cursor.execute("""
        SELECT t.id, t.titulo, t.tipo_texto
        FROM textos t
        JOIN textos_peliculas tp ON t.id = tp.id_texto
        WHERE tp.id_pelicula = %s
    """, (id,))
    textos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not pelicula:
        return HTMLResponse("Película no encontrada", status_code=404)
    
    return templates.TemplateResponse(
        "detalle_pelicula.html",
        {"request": request, "pelicula": pelicula, "textos": textos}
    )
#----------------------------------------------------------------------#
# RUTA PARA DETALLE DE CRITICO
@app.get("/critico/{id}", response_class=HTMLResponse)
async def detalle_critico(request: Request, id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM criticos WHERE id = %s", (id,))
    critico = cursor.fetchone()
    
    # Obtener textos escritos por este crítico
    cursor.execute("SELECT id, titulo, tipo_texto, fecha FROM textos WHERE id_critico = %s", (id,))
    textos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not critico:
        return HTMLResponse("Crítico no encontrado", status_code=404)
    
    return templates.TemplateResponse(
        "detalle_critico.html",
        {"request": request, "critico": critico, "textos": textos}
    )
#----------------------------------------------------------------------#
# RUTA PARA DETALLE DE TEXTO
@app.get("/texto/{id}", response_class=HTMLResponse)
async def detalle_texto(request: Request, id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Información básica del texto
    cursor.execute("SELECT * FROM textos WHERE id = %s", (id,))
    texto = cursor.fetchone()
    
    if texto:
        # Datos del crítico
        cursor.execute("SELECT id, nombre, apellidos FROM criticos WHERE id = %s", (texto['id_critico'],))
        texto['critico'] = cursor.fetchone()
        
        # Datos de la publicación
        cursor.execute("SELECT id, nombre, tipo FROM publicaciones WHERE id = %s", (texto['id_publicacion'],))
        texto['publicacion'] = cursor.fetchone()
        
        # Películas asociadas
        cursor.execute("""
            SELECT p.id, p.titulo, p.anio
            FROM peliculas p
            JOIN textos_peliculas tp ON p.id = tp.id_pelicula
            WHERE tp.id_texto = %s
        """, (id,))
        texto['peliculas'] = cursor.fetchall()
        
        # Palabras clave asociadas
        cursor.execute("""
            SELECT pk.id, pk.etiqueta
            FROM palabras_clave pk
            JOIN textos_palabras_clave tpk ON pk.id = tpk.id_palabra_clave
            WHERE tpk.id_texto = %s
        """, (id,))
        texto['palabras_clave'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not texto:
        return HTMLResponse("Texto no encontrado", status_code=404)
    
    return templates.TemplateResponse(
        "detalle_texto.html",
        {"request": request, "texto": texto}
    ) 

#----------------------------------------------------------------------#
# RUTA PARA DETALLE DE PALABRA CLAVE
@app.get("/palabra_clave/{id}", response_class=HTMLResponse)
async def detalle_palabra_clave(request: Request, id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM palabras_clave WHERE id = %s", (id,))
    palabra = cursor.fetchone()
    
    # Textos que tienen esta palabra clave
    if palabra:
        cursor.execute("""
            SELECT t.id, t.titulo, t.tipo_texto
            FROM textos t
            JOIN textos_palabras_clave tpk ON t.id = tpk.id_texto
            WHERE tpk.id_palabra_clave = %s
        """, (id,))
        palabra['textos'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not palabra:
        return HTMLResponse("Palabra clave no encontrada", status_code=404)
    
    return templates.TemplateResponse(
        "detalle_palabra.html",
        {"request": request, "palabra": palabra}
    )
#----------------------------------------------------------------------#
# RUTA PARA DETALLE DE PUBLICACION
@app.get("/publicacion/{id}", response_class=HTMLResponse)
async def detalle_publicacion(request: Request, id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM publicaciones WHERE id = %s", (id,))
    publicacion = cursor.fetchone()
    
    # Textos publicados en esta publicación
    if publicacion:
        cursor.execute("""
            SELECT id, titulo, tipo_texto, fecha
            FROM textos
            WHERE id_publicacion = %s
            ORDER BY fecha DESC
        """, (id,))
        publicacion['textos'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not publicacion:
        return HTMLResponse("Publicación no encontrada", status_code=404)
    
    return templates.TemplateResponse(
        "detalle_publicacion.html",
        {"request": request, "publicacion": publicacion}
    )

# EMPIEZA EL CODIGO DE PAO
#----------------------------------------------------------------------#
# MOSTRAR FORM
@app.get("/form", response_class=HTMLResponse)
def mostrar_formulario(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {"request": request}
    )

#----------------------------------------------------------------------#
# ENDPOINT CREAR USUARIO
@app.post("/guardar")
def guardar_usuario(
    nombre: str = Form(...),
    edad: int = Form(...)
):
    conn = get_connection()
    cursor = conn.cursor()

    sql = "INSERT INTO usuarios (nombre, edad) VALUES (%s, %s)"
    valores = (nombre, edad)

    cursor.execute(sql, valores)
    conn.commit()

    cursor.close()
    conn.close()

    return RedirectResponse(
            url="/usuarios",
            status_code = 303)

#----------------------------------------------------------------------#
# ENDPOINT OBTENER USUARIOS
@app.get("/usuarios")
def mostrar_usuarios(request : Request):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary = True)
        cursor.execute("SELECT id, nombre, edad FROM usuarios")
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return templates.TemplateResponse(
            "usuarios.html",{
                "request" : request,
                "usuarios" : usuarios
            }
        )
    except Exception as e:
        return {"error" : str(e)}

#----------------------------------------------------------------------#
# ENDPOINT EDITAR USUARIO       
@app.get("/usuarios/editar/{id}", response_class=HTMLResponse)
def editar_usuario_form(request: Request, id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT id, nombre, edad FROM usuarios WHERE id = %s"
        cursor.execute(sql, (id,))
        usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        return templates.TemplateResponse(
            "editar.html",
            {
                "request": request,
                "usuario": usuario
            }
        )

    except Exception as e:
        return {"error": str(e)}
@app.post("/usuarios/editar/{id}")
def editar_usuario(
    id: int,
    nombre: str = Form(...),
    edad: int = Form(...)
):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            UPDATE usuarios
            SET nombre = %s, edad = %s
            WHERE id = %s
        """
        cursor.execute(sql, (nombre, edad, id))
        conn.commit()

        cursor.close()
        conn.close()

        return RedirectResponse(
            url="/usuarios",
            status_code=303
        )

    except Exception as e:
        return {"error": str(e)}

#----------------------------------------------------------------------#
# ENDPOINT ELIMINAR USUARIO
@app.post("/eliminar/usuario/{id}")
def eliminar_usuario(id : int):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = "DELETE FROM usuarios WHERE id = %s"
        cursor.execute(sql, (id,))
        conn.commit()

        cursor.close()
        conn.close()
        return RedirectResponse(
            url="/usuarios",
            status_code = 303)
        
    except Exception as e:
        return {"error" : str(e)}
