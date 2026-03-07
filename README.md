````markdown
# 📚 Sistema de Gestión Papelería LyM

Sistema web desarrollado en **Python, Flask y MySQL** para la gestión de inventarios, usuarios, categorías y movimientos dentro de una papelería.  
El sistema permite administrar productos, controlar inventario y generar reportes automáticos en PDF mediante una interfaz web segura y moderna.

---

# 🚀 Características principales

- Gestión de **productos**
- Gestión de **usuarios**
- Gestión de **categorías**
- Registro de **movimientos de inventario**
- Generación de **reportes en PDF**
- Sistema de **roles de usuario**
- Interfaz web amigable
- Vista previa de imágenes de productos

---

# 🛠 Tecnologías utilizadas

- Python 3
- Flask
- MySQL
- HTML5
- CSS3
- JavaScript
- ReportLab (generación de PDF)

---

# 📦 Librerías utilizadas

```bash
flask
flask_mysqldb
werkzeug
reportlab
````

---

# ⚙️ Requisitos del sistema

Antes de ejecutar el proyecto debes tener instalado:

* Python **3.10 o superior**
* **MySQL 8**
* Navegador web moderno (Google Chrome o Microsoft Edge)

---

# 📁 Estructura del proyecto

```
Papeleria-LyM/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│
├── app.py
│
└── database.sql
```

### Descripción

* **static/** → Archivos estáticos como CSS, JavaScript e imágenes
* **templates/** → Vistas HTML del sistema
* **app.py** → Archivo principal que ejecuta la aplicación Flask
* **database.sql** → Script para crear la base de datos

---

# 🗄 Base de datos

El sistema utiliza **MySQL** con las siguientes tablas principales:

* usuarios
* productos
* categorias
* movimientos

Estas tablas permiten administrar la información del inventario y los registros del sistema.

---

# ▶️ Instalación y ejecución

## 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/erickgalindosc-hub/NOMBRE_DEL_REPOSITORIO.git
```

---

## 2️⃣ Crear la base de datos

En MySQL ejecutar:

```sql
CREATE DATABASE LyM;
```

Luego importar el archivo **database.sql** con las tablas del sistema.

---

## 3️⃣ Configurar la conexión

Editar el archivo **app.py** y configurar las credenciales de MySQL:

```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'tu_usuario'
MYSQL_PASSWORD = 'tu_contraseña'
MYSQL_DB = 'LyM'
```

---

## 4️⃣ Instalar dependencias

```bash
pip install flask flask_mysqldb werkzeug reportlab
```

---

## 5️⃣ Ejecutar el servidor

```bash
python app.py
```

---

## 6️⃣ Acceder al sistema

Abrir en el navegador:

```
http://localhost:5000
```

---

# 👥 Roles del sistema

## Administrador

* Gestión completa del sistema
* Crear, editar y eliminar productos
* Administrar usuarios
* Generar reportes PDF
* Reiniciar tablas

## Cliente

* Visualizar productos
* Registrar movimientos

---

# 📊 Funcionalidades

* CRUD completo de productos
* CRUD de usuarios
* CRUD de categorías
* Registro de movimientos
* Generación de reportes PDF
* Alertas informativas del sistema

---

# 📷 Vista previa del sistema

Puedes agregar capturas del sistema aquí.

```
/screenshots/login.png
/screenshots/dashboard.png
/screenshots/inventario.png
```

---

# 👨‍💻 Autor

**Erick Santiago Galindo Cepeda**

* Estudiante de **Análisis y Desarrollo de Software (SENA)**
* Interés en desarrollo **Full Stack**

GitHub:
https://github.com/erickgalindosc

---

# 📄 Licencia

Proyecto desarrollado con fines **educativos y académicos**.

```
```
