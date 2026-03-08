# 📚 Sistema de Gestión Papelería LyM - Versión 2.0

Sistema web profesional desarrollado en **Python, Flask y MySQL** para la gestión integral de inventarios, usuarios, categorías y movimientos. Esta versión incluye un rediseño completo de la interfaz de usuario y optimizaciones críticas en el backend.

---

# 🚀 Novedades de esta Versión

- **Dashboard General**: Nueva vista con estadísticas en tiempo real (Total de productos, Alertas de stock bajo, Total de usuarios y movimientos recientes).
- **Interfaz Moderna**: Sidebar fijo y responsivo con iconos dinámicos y navegación intuitiva.
- **Experiencia de Usuario Mejorada**: Uso de ventanas modales para todas las operaciones CRUD, evitando recargas innecesarias de página.
- **Optimización del Backend**: Implementación de gestores de contexto (`with`) para conexiones seguras a la base de datos.
- **Seguridad Reforzada**: Decoradores de acceso restringido para rutas críticas y manejo seguro de sesiones.
- **Higiene del Repositorio**: Inclusión de `.gitignore` para mantener el código limpio de archivos temporales y datos sensibles.

---

# 🛠 Tecnologías y Librerías

- **Backend**: Python 3.10+, Flask, Flask-MySQLdb, Werkzeug (Security).
- **Frontend**: Bootstrap 5, Bootstrap Icons, Jinja2 Templates.
- **Reportes**: ReportLab (Generación de PDF).

```bash
pip install flask flask_mysqldb werkzeug reportlab
```

---

# 📁 Estructura del Proyecto Actualizada

```
Papeleria-LyM/
│
├── static/
│   ├── css/            # Estilos personalizados y Bootstrap
│   ├── js/             # Scripts de comportamiento y UI
│   ├── img/            # Logotipos y recursos visuales
│   └── uploads/        # Imágenes de productos (Grit-ignored)
│
├── templates/
│   ├── partials/       # Fragmentos de plantillas (Modales, etc.)
│   ├── base.html       # Estructura principal con Sidebar
│   ├── dashboard.html  # Nueva vista de estadísticas
│   └── ...             # Vistas de Productos, Usuarios, etc.
│
├── app.py              # Lógica central optimizada
├── .gitignore          # Reglas de exclusión de archivos
└── database.sql        # Script de inicialización de la BD
```

---

# ⚙️ Instalación y Configuración Rápida

1. **Base de Datos**: Crea una base de datos MySQL llamada `LyM` e importa el script `database.sql`.
2. **Configuración**: Ajusta las credenciales en `app.py`:
   ```python
   app.config["MYSQL_HOST"] = "localhost"
   app.config["MYSQL_USER"] = "tu_usuario"
   app.config["MYSQL_PASSWORD"] = "tu_clave"
   app.config["MYSQL_DB"] = "LyM"
   ```
3. **Ejecución**:
   ```bash
   python app.py
   ```
4. **Acceso**: Entra a `http://localhost:5000`.
   - *Admin por defecto*: `admin1@gmail.com` / `admin123`

---

# 📊 Roles y Funcionalidades

### 🛡️ Administrador
- Acceso total al **Dashboard**.
- Gestión de inventario (Crear, Editar, Eliminar productos con imágenes).
- Control de **Usuarios** y **Categorías**.
- Generación de reportes PDF detallados.
- Funciones de mantenimiento (Reiniciar tablas).

### 👥 Cliente / Usuario
- Acceso al catálogo de productos con búsqueda avanzada.
- Registro de **Movimientos** (Entradas y Salidas de mercancía).
- Alertas visuales de stock bajo.

---

# 👨‍💻 Autor y Mantenimiento

**Erick Santiago Galindo Cepeda**
*Desarrollador Full Stack en formación (SENA)*

Esta versión fue optimizada para ser escalable y fácil de versionar en el futuro.

---

# 📄 Licencia

Proyecto con fines educativos y de gestión empresarial básica.
