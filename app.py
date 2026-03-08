from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

import os
from werkzeug.utils import secure_filename
app = Flask(__name__)


# Configuración de subida de imágenes
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear carpeta uploads si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Configuración MySQL ---
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "jannez"
app.config["MYSQL_PASSWORD"] = "12345"
app.config["MYSQL_DB"] = "LyM"
app.config["SECRET_KEY"] = "d5fb8c4fa8bd46638dadc4e751e0d68d"

mysql = MySQL(app)

# --- Crear usuario administrador si no existe ---
def create_admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios WHERE rol='admin'")
    existe_admin = cur.fetchone()[0]
    if existe_admin == 0:
        nombre = "Administrador"
        correo = "admin1@gmail.com"
        password = generate_password_hash("admin123")
        rol = "admin"
        cur.execute(
            "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s,%s,%s,%s)",
            (nombre, correo, password, rol)
        )
        mysql.connection.commit()
        print("✅ Usuario administrador creado: admin1@gmail.com / admin123")
    else:
        print("🟢 Usuario administrador ya existente.")
    cur.close()

with app.app_context():
    create_admin()

# --- Decoradores ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session:
            flash("Debes iniciar sesión primero.", "warning")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session or session["rol"] != "admin":
            flash("Acceso restringido solo para administradores.", "danger")
            return redirect(url_for("productos"))
        return f(*args, **kwargs)
    return decorated_function

# --- Autenticación ---
@app.route("/")
def index():
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    correo = request.form.get("correo")
    password = request.form.get("password")
    if not correo or not password:
        flash("Por favor completa todos los campos.", "warning")
        return redirect(url_for("index"))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, password, rol FROM usuarios WHERE correo=%s", (correo,))
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[2], password):
        session["id"] = user[0]
        session["usuario"] = user[1]
        session["rol"] = user[3]
        flash("Inicio de sesión exitoso", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Correo o contraseña incorrectos.", "danger")
        return redirect(url_for("index"))

# --- Dashboard ---
@app.route("/dashboard")
@login_required
def dashboard():
    with mysql.connection.cursor() as cur:
        # Total productos
        cur.execute("SELECT COUNT(*) FROM productos")
        total_productos = cur.fetchone()[0]

        # Stock bajo (menos de 10)
        cur.execute("SELECT COUNT(*) FROM productos WHERE stock < 10")
        stock_bajo = cur.fetchone()[0]

        # Total usuarios
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cur.fetchone()[0]

        # Últimos 5 movimientos
        cur.execute("""
            SELECT m.tipo, m.cantidad, p.nombre, m.fecha
            FROM movimientos m
            LEFT JOIN productos p ON m.id_producto = p.id
            ORDER BY m.fecha DESC LIMIT 5
        """)
        recientes = cur.fetchall()

    return render_template("dashboard.html",
                           total_productos=total_productos,
                           stock_bajo=stock_bajo,
                           total_usuarios=total_usuarios,
                           recientes=recientes,
                           rol=session["rol"],
                           usuario=session["usuario"])

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for("index"))

# --- Registro ---
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre_apellidos"]
        correo = request.form["correo"]
        password = request.form["passw"]

        if not all([nombre, correo, password]):
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("registro"))

        hash_pass = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
        existente = cur.fetchone()

        if existente:
            flash("El correo electrónico ya está registrado.", "warning")
            return redirect(url_for("registro"))

        cur.execute("INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s,%s,%s,%s)",
                    (nombre, correo, hash_pass, "cliente"))
        mysql.connection.commit()
        flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")





# --- CRUD USUARIOS ---
@app.route("/usuarios")
@admin_required
def usuarios():
    q = request.args.get("q", "").strip()
    cur = mysql.connection.cursor()
    if q:
        cur.execute("""
            SELECT id, nombre, correo, rol, fecha_registro 
            FROM usuarios 
            WHERE nombre LIKE %s OR correo LIKE %s OR rol LIKE %s
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT id, nombre, correo, rol, fecha_registro FROM usuarios")
    usuarios_data = cur.fetchall()
    cur.close()
    return render_template("usuarios.html",
                           usuarios=usuarios_data,
                           rol=session["rol"],
                           usuario=session["usuario"],
                           busqueda=q)

@app.route("/usuarios/agregar", methods=["POST"])
@admin_required
def agregar_usuario():
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = request.form["password"]
    rol = request.form["rol"]
    hash_pass = generate_password_hash(password)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s,%s,%s,%s)",
                (nombre, correo, hash_pass, rol))
    mysql.connection.commit()
    flash("Usuario agregado correctamente", "success")
    return redirect(url_for("usuarios"))

@app.route("/usuarios/editar/<id>", methods=["POST"])
@admin_required
def editar_usuario(id):
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    rol = request.form["rol"]
    cur = mysql.connection.cursor()
    cur.execute("UPDATE usuarios SET nombre=%s, correo=%s, rol=%s WHERE id=%s",
                (nombre, correo, rol, id))
    mysql.connection.commit()
    flash("Usuario actualizado correctamente", "info")
    return redirect(url_for("usuarios"))

@app.route("/usuarios/eliminar/<id>")
@admin_required
def eliminar_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    mysql.connection.commit()
    flash("Usuario eliminado correctamente", "danger")
    return redirect(url_for("usuarios"))

@app.route("/usuarios/reiniciar", methods=["POST"])
@admin_required
def reiniciar_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM usuarios WHERE id > 1")
    cur.execute("ALTER TABLE usuarios AUTO_INCREMENT = 2")
    mysql.connection.commit()
    cur.close()
    flash("Tabla de usuarios reiniciada correctamente (el admin se conservó).", "danger")
    return redirect(url_for("usuarios"))



# --- CRUD CATEGORÍAS ---
@app.route("/categorias")
@admin_required
def categorias():
    q = request.args.get("q", "").strip()
    cur = mysql.connection.cursor()
    if q:
        cur.execute("""
            SELECT id, nombre, descripcion FROM categorias
            WHERE nombre LIKE %s OR descripcion LIKE %s
        """, (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT id, nombre, descripcion FROM categorias")
    categorias_data = cur.fetchall()
    cur.close()
    return render_template("categorias.html",
                           categorias=categorias_data,
                           rol=session["rol"],
                           usuario=session["usuario"],
                           busqueda=q)

@app.route("/categorias/agregar", methods=["POST"])
@admin_required
def agregar_categoria():
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO categorias (nombre, descripcion) VALUES (%s,%s)", (nombre, descripcion))
    mysql.connection.commit()
    flash("Categoría agregada correctamente", "success")
    return redirect(url_for("categorias"))

@app.route("/categorias/editar/<id>", methods=["POST"])
@admin_required
def editar_categoria(id):
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    cur = mysql.connection.cursor()
    cur.execute("UPDATE categorias SET nombre=%s, descripcion=%s WHERE id=%s",
                (nombre, descripcion, id))
    mysql.connection.commit()
    flash("Categoría actualizada correctamente", "info")
    return redirect(url_for("categorias"))

@app.route("/categorias/eliminar/<id>")
@admin_required
def eliminar_categoria(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM categorias WHERE id=%s", (id,))
    mysql.connection.commit()
    flash("Categoría eliminada correctamente", "danger")
    return redirect(url_for("categorias"))

@app.route("/categorias/reiniciar", methods=["POST"])
@admin_required
def reiniciar_categorias():
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM categorias")
    cur.execute("ALTER TABLE categorias AUTO_INCREMENT = 1")
    mysql.connection.commit()
    cur.close()
    flash("Tabla de categorías reiniciada correctamente.", "danger")
    return redirect(url_for("categorias"))


# --- LISTAR PRODUCTOS  ---
@app.route("/productos")
@login_required
def productos():
    q = request.args.get("q", "").strip()
    cur = mysql.connection.cursor()

    if q:
        cur.execute("""
            SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock, c.nombre, p.imagen
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id
            WHERE p.nombre LIKE %s OR p.descripcion LIKE %s OR c.nombre LIKE %s
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
            SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock, c.nombre, p.imagen
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id
        """)

    productos_data = cur.fetchall()
    cur.execute("SELECT id, nombre FROM categorias")
    categorias = cur.fetchall()
    cur.close()

    return render_template("productos.html",
                           productos=productos_data,
                           categorias=categorias,
                           rol=session["rol"],
                           usuario=session["usuario"],
                           busqueda=q)



# --- CRUD PRODUCTOS ---
@app.route("/productos/agregar", methods=["POST"])
@admin_required
def agregar_producto():
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    stock = request.form["stock"]
    id_categoria = request.form["id_categoria"]

    imagen = request.files.get("imagen")
    filename = None
    if imagen and allowed_file(imagen.filename):
        filename = secure_filename(imagen.filename)
        imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO productos (nombre, descripcion, precio, stock, id_categoria, imagen)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (nombre, descripcion, precio, stock, id_categoria, filename))
    mysql.connection.commit()
    flash("Producto agregado correctamente", "success")
    return redirect(url_for("productos"))


@app.route("/productos/editar/<id>", methods=["POST"])
@admin_required
def editar_producto(id):
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    stock = request.form["stock"]
    id_categoria = request.form["id_categoria"]

    imagen = request.files.get("imagen")
    filename = None

    if imagen and allowed_file(imagen.filename):
        filename = secure_filename(imagen.filename)
        imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        query = """
            UPDATE productos
            SET nombre=%s, descripcion=%s, precio=%s, stock=%s, id_categoria=%s, imagen=%s
            WHERE id=%s
        """
        values = (nombre, descripcion, precio, stock, id_categoria, filename, id)
    else:
        query = """
            UPDATE productos
            SET nombre=%s, descripcion=%s, precio=%s, stock=%s, id_categoria=%s
            WHERE id=%s
        """
        values = (nombre, descripcion, precio, stock, id_categoria, id)

    cur = mysql.connection.cursor()
    cur.execute(query, values)
    mysql.connection.commit()
    flash("Producto actualizado correctamente", "info")
    return redirect(url_for("productos"))

@app.route("/productos/eliminar/<id>")
@admin_required
def eliminar_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM productos WHERE id=%s", (id,))
    mysql.connection.commit()
    flash("Producto eliminado correctamente", "danger")
    return redirect(url_for("productos"))

@app.route("/productos/reiniciar", methods=["POST"])
@admin_required
def reiniciar_productos():
    cur = mysql.connection.cursor()
    # Borrar todos los productos
    cur.execute("DELETE FROM productos")
    # Reiniciar el contador de auto_increment
    cur.execute("ALTER TABLE productos AUTO_INCREMENT = 1")
    mysql.connection.commit()
    cur.close()
    flash("Tabla de productos reiniciada correctamente.", "danger")
    return redirect(url_for("productos"))


# --- CRUD MOVIMIENTOS ---
@app.route("/movimientos")
@login_required
def movimientos():
    q = request.args.get("q", "").strip()
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre FROM productos")
    productos = cur.fetchall()

    if q:
        cur.execute("""
            SELECT m.id, m.tipo, m.cantidad, p.nombre, u.nombre, m.fecha
            FROM movimientos m
            LEFT JOIN productos p ON m.id_producto = p.id
            LEFT JOIN usuarios u ON m.id_usuario = u.id
            WHERE p.nombre LIKE %s OR u.nombre LIKE %s OR m.tipo LIKE %s
            ORDER BY m.fecha DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
            SELECT m.id, m.tipo, m.cantidad, p.nombre, u.nombre, m.fecha
            FROM movimientos m
            LEFT JOIN productos p ON m.id_producto = p.id
            LEFT JOIN usuarios u ON m.id_usuario = u.id
            ORDER BY m.fecha DESC
        """)
    movimientos_data = cur.fetchall()
    cur.close()
    return render_template("movimientos.html",
                           movimientos=movimientos_data,
                           productos=productos,
                           rol=session["rol"],
                           usuario=session["usuario"],
                           busqueda=q)

@app.route("/movimientos/agregar", methods=["POST"])
@login_required
def agregar_movimiento():
    tipo = request.form["tipo"]
    cantidad = int(request.form["cantidad"])
    id_producto = request.form["id_producto"]
    id_usuario = session["id"]

    cur = mysql.connection.cursor()
    cur.execute("SELECT stock FROM productos WHERE id=%s", (id_producto,))
    stock_actual_tuple = cur.fetchone()

    if not stock_actual_tuple:
        flash("El producto seleccionado no existe.", "danger")
        return redirect(url_for("movimientos"))

    stock_actual = stock_actual_tuple[0]
    nuevo_stock = stock_actual + cantidad if tipo == "entrada" else stock_actual - cantidad

    if nuevo_stock < 0:
        flash("No hay suficiente stock para realizar la salida.", "danger")
        return redirect(url_for("movimientos"))

    cur.execute("INSERT INTO movimientos (tipo, cantidad, id_producto, id_usuario) VALUES (%s,%s,%s,%s)",
                (tipo, cantidad, id_producto, id_usuario))
    cur.execute("UPDATE productos SET stock=%s WHERE id=%s", (nuevo_stock, id_producto))
    mysql.connection.commit()
    flash("Movimiento registrado correctamente", "success")
    return redirect(url_for("movimientos"))

@app.route('/movimientos/editar/<int:id>', methods=['GET', 'POST'])
def editar_movimiento(id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        tipo = request.form['tipo']
        cantidad = request.form['cantidad']
        cur.execute("UPDATE movimientos SET tipo=%s, cantidad=%s WHERE id=%s", (tipo, cantidad, id))
        mysql.connection.commit()
        flash('Movimiento actualizado correctamente.', 'success')
        return redirect(url_for('movimientos'))
    else:
        cur.execute("SELECT * FROM movimientos WHERE id=%s", (id,))
        movimiento = cur.fetchone()
        cur.close()
        return render_template('editar_movimiento.html', movimiento=movimiento)


@app.route('/movimientos/eliminar/<int:id>', methods=['POST'])
def eliminar_movimiento(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM movimientos WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Movimiento eliminado correctamente.', 'success')
    return redirect(url_for('movimientos'))

@app.route("/movimientos/reiniciar", methods=["POST"])
@admin_required
def reiniciar_movimientos():
    cur = mysql.connection.cursor()
    # Eliminar todos los registros
    cur.execute("DELETE FROM movimientos")
    # Reiniciar el contador AUTO_INCREMENT a 1
    cur.execute("ALTER TABLE movimientos AUTO_INCREMENT = 1")
    mysql.connection.commit()
    cur.close()
    flash("Tabla de movimientos reiniciada correctamente.", "danger")
    return redirect(url_for("movimientos"))


# --- REPORTES PDF ---
def generar_pdf(titulo, columnas, datos):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(titulo)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, titulo)
    pdf.setFont("Helvetica", 10)

    y = 720
    pdf.line(50, y + 10, 560, y + 10)
    pdf.drawString(50, y, " | ".join(columnas))
    pdf.line(50, y - 5, 560, y - 5)
    y -= 20

    for fila in datos:
        fila_texto = " | ".join([str(c) for c in fila])
        pdf.drawString(50, y, fila_texto)
        y -= 15
        if y < 60:
            pdf.showPage()
            y = 750
            pdf.setFont("Helvetica", 10)

    pdf.save()
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={titulo}.pdf"
    return response

@app.route("/reporte/usuarios")
@admin_required
def reporte_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, correo, rol, fecha_registro FROM usuarios")
    datos = cur.fetchall()
    cur.close()
    return generar_pdf("Reporte de Usuarios", ["ID", "Nombre", "Correo", "Rol", "Fecha"], datos)

@app.route("/reporte/productos")
@admin_required
def reporte_productos():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT p.id, p.nombre, c.nombre AS categoria, p.precio, p.stock
        FROM productos p
        LEFT JOIN categorias c ON p.id_categoria = c.id
    """)
    datos = cur.fetchall()
    cur.close()
    return generar_pdf("Reporte de Productos", ["ID", "Nombre", "Categoría", "Precio", "Stock"], datos)

@app.route("/reporte/movimientos")
@admin_required
def reporte_movimientos():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT m.id, m.tipo, m.cantidad, p.nombre, u.nombre, m.fecha
        FROM movimientos m
        LEFT JOIN productos p ON m.id_producto = p.id
        LEFT JOIN usuarios u ON m.id_usuario = u.id
        ORDER BY m.fecha DESC
    """)
    datos = cur.fetchall()
    cur.close()
    return generar_pdf("Reporte de Movimientos", ["ID", "Tipo", "Cantidad", "Producto", "Usuario", "Fecha"], datos)

# --- MAIN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
