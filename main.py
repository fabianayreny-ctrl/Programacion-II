from contextlib import asynccontextmanager
import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

DB_NAME = "estudiantes.db"

def obtener_conexion():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    return conexion

def crear_tabla():
    with obtener_conexion() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cuenta TEXT NOT NULL UNIQUE,
                carrera TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                telefono TEXT NOT NULL,
                edad INTEGER NOT NULL
            )
        """)

@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tabla()
    yield

app = FastAPI(
    title="API de Gestión de Estudiantes",
    description="API CRUD para Programación II con FastAPI y SQLite",
    version="1.0.0",
    lifespan=lifespan,
)

class EstudianteBase(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    cuenta: str = Field(min_length=3, max_length=30)
    carrera: str = Field(min_length=3, max_length=100)
    correo: str = Field(min_length=5, max_length=120)
    telefono: str = Field(min_length=8, max_length=20)
    edad: int = Field(ge=15, le=100)

class EstudianteCrear(EstudianteBase):
    pass

class EstudianteRespuesta(EstudianteBase):
    id: int

@app.get("/")
def inicio():
    return {"mensaje": "API funcionando correctamente"}

@app.post("/estudiantes",
          response_model=EstudianteRespuesta,
          status_code=status.HTTP_201_CREATED)
def crear_estudiante(estudiante: EstudianteCrear):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.execute("""
                INSERT INTO estudiantes
                (nombre, cuenta, carrera, correo, telefono, edad)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                estudiante.nombre,
                estudiante.cuenta,
                estudiante.carrera,
                estudiante.correo,
                estudiante.telefono,
                estudiante.edad
            ))

            fila = conexion.execute(
                "SELECT * FROM estudiantes WHERE id = ?",
                (cursor.lastrowid,)
            ).fetchone()

            return dict(fila)

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="La cuenta o el correo ya están registrados"
        )

@app.get("/estudiantes", response_model=list[EstudianteRespuesta])
def listar_estudiantes():
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            "SELECT * FROM estudiantes ORDER BY id"
        ).fetchall()

    return [dict(fila) for fila in filas]

@app.get("/estudiantes/{estudiante_id}",
         response_model=EstudianteRespuesta)
def obtener_estudiante(estudiante_id: int):
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            "SELECT * FROM estudiantes WHERE id = ?",
            (estudiante_id,)
        ).fetchone()

    if fila is None:
        raise HTTPException(
            status_code=404,
            detail="Estudiante no encontrado"
        )

    return dict(fila)

@app.get("/estudiantes/cuenta/{cuenta}",
         response_model=EstudianteRespuesta)
def obtener_estudiante_por_cuenta(cuenta: str):
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            "SELECT * FROM estudiantes WHERE cuenta = ?",
            (cuenta,)
        ).fetchone()

    if fila is None:
        raise HTTPException(
            status_code=404,
            detail="Estudiante no encontrado"
        )

    return dict(fila)

@app.put("/estudiantes/{estudiante_id}",
         response_model=EstudianteRespuesta)
def actualizar_estudiante(estudiante_id: int,
                          estudiante: EstudianteCrear):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.execute("""
                UPDATE estudiantes
                SET nombre=?,
                    cuenta=?,
                    carrera=?,
                    correo=?,
                    telefono=?,
                    edad=?
                WHERE id=?
            """, (
                estudiante.nombre,
                estudiante.cuenta,
                estudiante.carrera,
                estudiante.correo,
                estudiante.telefono,
                estudiante.edad,
                estudiante_id
            ))

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Estudiante no encontrado"
                )

            fila = conexion.execute(
                "SELECT * FROM estudiantes WHERE id = ?",
                (estudiante_id,)
            ).fetchone()

            return dict(fila)

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="La cuenta o correo pertenecen a otro estudiante"
        )

@app.delete("/estudiantes/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int):
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "DELETE FROM estudiantes WHERE id = ?",
            (estudiante_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Estudiante no encontrado"
            )

    return {"mensaje": "Estudiante eliminado correctamente"}
