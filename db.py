import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = "LyM.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table: usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('admin', 'cliente')) DEFAULT 'cliente',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        tema TEXT DEFAULT 'light',
        idioma TEXT DEFAULT 'es'
    );
    """)

    # Table: categorias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT
    );
    """)

    # Table: productos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio REAL NOT NULL,
        stock INTEGER DEFAULT 0,
        id_categoria INTEGER,
        imagen TEXT,
        FOREIGN KEY (id_categoria) REFERENCES categorias(id) ON DELETE SET NULL
    );
    """)

    # Table: movimientos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT CHECK(tipo IN ('entrada', 'salida')) NOT NULL,
        cantidad INTEGER NOT NULL,
        id_producto INTEGER,
        id_usuario INTEGER,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_producto) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Create admin if not exists
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol='admin'")
    if cursor.fetchone()[0] == 0:
        nombre = "Administrador"
        correo = "admin1@gmail.com"
        password = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO usuarios (nombre, correo, password, rol, tema, idioma) VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, correo, password, "admin", "light", "es")
        )
        conn.commit()
        print("✅ Default admin created successfully.")

    # Check if there are initial categories
    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        categorias_iniciales = [
            ('Papelería', 'Productos de oficina y papelería'),
            ('Escolar', 'Útiles escolares'),
            ('Arte', 'Material artístico')
        ]
        cursor.executemany("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", categorias_iniciales)
        conn.commit()

        # Add initial products if categories were just populated
        cursor.execute("SELECT COUNT(*) FROM productos")
        if cursor.fetchone()[0] == 0:
            productos_iniciales = [
                ('Cuaderno', 'Cuaderno rayado de 100 hojas', 4500.0, 50, 1, None),
                ('Lápiz HB', 'Lápiz de grafito estándar', 1200.0, 100, 2, None),
                ('Pincel #3', 'Pincel fino para pintura', 3000.0, 30, 3, None)
            ]
            cursor.executemany(
                "INSERT INTO productos (nombre, descripcion, precio, stock, id_categoria, imagen) VALUES (?, ?, ?, ?, ?, ?)",
                productos_iniciales
            )
            conn.commit()

    conn.close()

def migrate_db():
    # Make sure we have latest schema
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure 'tema' and 'idioma' columns exist on 'usuarios'
    cursor.execute("PRAGMA table_info(usuarios)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'tema' not in columns:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN tema TEXT DEFAULT 'light'")
    if 'idioma' not in columns:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN idioma TEXT DEFAULT 'es'")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    migrate_db()
    print("Database initialisation complete.")
