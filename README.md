# Sistema de Control de Asistencia Biométrico

Este proyecto es una aplicación web funcional desarrollada para gestionar y automatizar el control de asistencia de personal mediante reconocimiento facial en tiempo real. Está diseñado para ofrecer una solución ágil en el marcaje diario de entradas o salidas y proporcionar a los administradores una consola centralizada con métricas de la jornada y un asistente de auditoría inteligente basado en lenguaje natural.

---

## Características Principales

* **Procesamiento Facial en Memoria RAM:** El registro de entradas y salidas extrae las características del rostro directamente desde el flujo de la cámara web. Las imágenes se decodifican y procesan en memoria como arreglos numéricos sin guardarse en el almacenamiento local, optimizando los tiempos de respuesta y protegiendo la privacidad física.
* **Enrolamiento Biométrico Guiado (5 Ángulos):** Al registrar un nuevo empleado, el backend valida primero que el RUT sea real y no esté duplicado. Si la verificación es exitosa, la interfaz guía al usuario en un proceso de 5 capturas desde diferentes perspectivas (frente, izquierda, derecha, arriba y abajo). El sistema calcula el vector promedio de estos ángulos mediante NumPy para consolidar un perfil maestro resistente a cambios de postura o iluminación.
* **Búsqueda Vectorial Optimizada:** Almacena los embeddings de 128 dimensiones generados por el modelo Facenet en una base de datos relacional PostgreSQL en Supabase, utilizando la extensión nativa `pgvector`. La identificación se resuelve en milisegundos directamente en el servidor SQL mediante el cálculo de distancia coseno (`<=>`).
* **Asistente de Auditoría con IA:** El panel privado integra un chat analítico interactivo desarrollado con LangChain y Google Gemini 2.5 Flash. Este módulo recopila el estado actual de los registros de asistencia y personal, permitiendo al administrador realizar consultas complejas en texto libre (ej: *"¿Quién faltó hoy?"* o *"A qué hora ingresó Juan Pérez"*) obteniendo respuestas basadas estrictamente en la base de datos.

---

## Tecnologías Utilizadas

### Backend y Visión Artificial
* **FastAPI (Python 3.12):** Framework principal para la construcción del servidor web, enrutamiento estático y exposición de endpoints asíncronos.
* **DeepFace (Modelo Facenet):** Librería encargada de la detección y extracción de los vectores faciales únicos de 128 dimensiones.
* **OpenCV:** Manipulación, lectura y conversión de matrices de imágenes recibidas por el flujo de red.
* **LangChain y Google Gemini 2.5 Flash:** Pipeline para la orquestación del contexto de datos y la ejecución del modelo generativo Gemini.

### Base de Datos y Almacenamiento
* **Supabase (PostgreSQL):** Persistencia en la nube para las tablas de empleados, marcas de asistencia y el control relacional del sistema.
* **Extensión pgvector:** Almacenamiento indexado y comparación geométrica de vectores matemáticos de rostros.

### Frontend Web
* **HTML5, CSS3 y JavaScript Nativo (Vanilla JS):** Interfaz ligera y responsiva construida sin frameworks externos pesados para garantizar que la transmisión de video por la Web API `getUserMedia` no sufra caídas de frames ni cuellos de botella.

---

## Estructura del Proyecto

A continuación se detalla la organización del código fuente del sistema:

```text
sistema-asistencia-facial/
├── .env                  # Archivo local con credenciales y llaves API (Oculto)
├── .gitignore            # Exclusiones de control de versiones (entorno, cachés, .env)
├── conexion_bd.py        # Conexión a Supabase, inserciones y validaciones de duplicados
├── inteligencia.py       # Descarga de contexto analítico y pipeline con LangChain + Gemini
├── main.py               # Servidor FastAPI, middleware CORS, enrutamiento y endpoints API
├── README.md             # Documentación principal, arquitectura y guía de instalación
├── reconocimiento.py     # Procesamiento de imágenes con OpenCV y extracción con DeepFace
├── requirements.txt      # Listado definitivo de dependencias y versiones del proyecto
├── validaciones.py       # Algoritmo Módulo 11 para validación y formateo del RUT chileno
└── estaticos/            # Archivos fuente de la interfaz gráfica de usuario
    ├── estilos.css       # Hoja de estilos compartida, responsive y con efectos visuales
    ├── index.html        # Pantalla principal pública: Marcador de Entrada y Salida
    ├── login.html        # Formulario de acceso restringido para el Administrador
    ├── panel.html        # Consola del administrador: Visualización de KPIs y Chat con IA
    └── registro.html     # Interfaz del proceso de enrolamiento facial guiado por pasos
```

---

## Instalación y Configuración Local

Siga estos pasos para desplegar y configurar el entorno de ejecución desde cero en una nueva máquina:

### 1. Clonar el Repositorio
Abra una terminal en su directorio de proyectos y descargue el código fuente:
```bash
git clone url-del-repositorio
cd sistema-asistencia-facial
```

### 2. Crear e Inicializar el Entorno Virtual
Se requiere estrictamente utilizar Python 3.11 o Python 3.12. Versiones más recientes (como Python 3.14) presentan incompatibilidades críticas en sistemas de escritorio con TensorFlow (motor subyacente que DeepFace necesita obligatoriamente).

Cree un entorno aislado para evitar conflictos globales de dependencias:
```bash
# Crear entorno virtual llamado 'entorno_env'
py -3.12 -m venv entorno_env

# Activar en Windows (PowerShell)
entorno_env\Scripts\activate
# Nota: Si PowerShell arroja un error de políticas, ejecute primero: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Activar en Windows (CMD Tradicional)
entorno_env\Scripts\activate.bat

# Activar en Linux / macOS
source entorno_env/bin/activate
```

### 3. Instalar Dependencias del Sistema
Con el entorno virtual activo (verá el prefijo `(entorno_env)` en su terminal), ejecute la instalación:
```bash
pip install -r requirements.txt
```
*Nota: Este proceso puede tomar unos minutos en la primera ejecución ya que frameworks como TensorFlow y OpenCV descargan binarios de compilación pesados.*

### 4. Configurar Variables de Entorno (.env)
Los accesos confidenciales están protegidos y omitidos en Git. Cree un archivo de texto plano llamado exactamente `.env` en la raíz del proyecto (al mismo nivel que `main.py`) con la siguiente estructura:
```env
SUPABASE_URL="[https://tu-proyecto-id.supabase.co]"
SUPABASE_KEY="tu-anon-public-key"
ADMIN_USUARIO="admin@empresa.com"
ADMIN_CLAVE="tu-clave-segura"
GEMINI_API_KEY="tu-api-key-de-google-ai-studio"
```

### 5. Preparar la Base de Datos (Supabase SQL)
1. Ingrese a la consola web de Supabase.
2. Abra la sección **SQL Editor** e inicie una nueva consulta en blanco.
3. Pegue y ejecute (*Run*) el siguiente script estructural para inicializar el esquema y compilar la función RPC de comparación:

```sql
-- 1. Habilitar la extensión para manejo de vectores matemáticos
create extension if not exists vector;

-- 2. Esquema relacional para el personal y su embedding facial maestro
create table empleados (
    id uuid default gen_random_uuid() primary key,
    rut text unique not null,
    nombre_completo text not null,
    vector_facial vector(128), -- Embedding de 128 dimensiones de Facenet
    creado_el timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Esquema relacional para el registro diario de entradas y salidas
create table asistencia (
    id uuid default gen_random_uuid() primary key,
    empleado_id uuid references empleados(id) on delete cascade not null,
    fecha_date date default current_date not null,
    hora_time time default current_time not null,
    tipo_registro text check (tipo_registro in ('ENTRADA', 'SALIDA')) not null
);

-- 4. Función almacenada (RPC) para la búsqueda rápida por Distancia Coseno
create or replace function buscar_rostro_coincidente(vector_buscado vector(128))
returns table (id uuid, rut text, nombre_completo text, distancia float)
language plpgsql as $$
begin
    return query
    select e.id, e.rut, e.nombre_completo, (e.vector_facial <=> vector_buscado) as distancia
    from empleados e
    order by e.vector_facial <=> vector_buscado asc
    limit 1;
end;
$$;
```

---

## Ejecución del Servidor

Una vez completadas las configuraciones, inicialice el servidor local de desarrollo mediante Uvicorn:
```bash
uvicorn main:app --reload
```

El servidor web de FastAPI se desplegará localmente y gestionará las redirecciones internas automáticas hacia el frontend. Abra su navegador web e ingrese a la siguiente dirección:
```text
[http://127.0.0.1:8000/]
```

Desde esta pantalla, el personal podrá registrar sus marcas diarias, mientras que los administradores podrán iniciar sesión para dar de alta trabajadores o auditar métricas mediante el chat inteligente.

---

## Autor

Hyans Nicolás Parra Valdivia - Desarrollo e Implementación - https://github.com/HyansParra

Proyecto desarrollado en el contexto de práctica profesional en Gestpyme.
