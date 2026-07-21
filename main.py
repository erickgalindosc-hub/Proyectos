import flet as ft
from flet import Colors, Icons
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

from db import init_db, migrate_db, get_db_connection
from translations import TRANSLATIONS

# Helper for translation strings
def get_text(key, lang='es'):
    return TRANSLATIONS.get(lang, TRANSLATIONS['es']).get(key, key)

class SessionManager:
    def __init__(self):
        self.user_id = None
        self.username = None
        self.role = None
        self.theme = 'light'
        self.lang = 'es'

    def set_user(self, user_id, username, role, theme, lang):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.theme = theme if theme else 'light'
        self.lang = lang if lang else 'es'

    def clear(self):
        self.user_id = None
        self.username = None
        self.role = None
        self.theme = 'light'
        self.lang = 'es'

session = SessionManager()

def generate_pdf_report(titulo, columnas, datos):
    """
    Generates a ReportLab PDF and returns the file path.
    Saves in a local directory 'reports'
    """
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filename = os.path.join(reports_dir, f"{titulo.replace(' ', '_').lower()}.pdf")
    pdf = canvas.Canvas(filename, pagesize=letter)
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
    return filename

def main(page: ft.Page):
    page.title = "Papelería LyM"
    page.window_width = 450
    page.window_height = 850
    page.scroll = "auto"

    init_db()
    migrate_db()

    # Create snackbar for notifications
    snack_bar = ft.SnackBar(content=ft.Text(""))
    page.snack_bar = snack_bar

    def show_msg(text, color=Colors.GREEN):
        snack_bar.content = ft.Text(text, color=Colors.WHITE, weight=ft.FontWeight.BOLD)
        snack_bar.bgcolor = color
        snack_bar.open = True
        page.update()

    def navigate_to(route_name):
        page.go(route_name)

    # Main Navigation Layout Wrapper for logged-in screens
    def get_navigation_layout(current_view_title, selected_index=None):
        lang = session.lang

        # Build Navigation Bar
        nav_destinations = [
            ft.NavigationDestination(icon=Icons.DASHBOARD_ROUNDED, label=get_text('dashboard', lang)),
            ft.NavigationDestination(icon=Icons.SHOPPING_BAG_ROUNDED, label=get_text('products', lang)),
            ft.NavigationDestination(icon=Icons.SWAP_HORIZ_ROUNDED, label=get_text('movements', lang)),
        ]

        def on_nav_change(e):
            idx = e.control.selected_index
            if idx == 0:
                navigate_to("/dashboard")
            elif idx == 1:
                navigate_to("/products")
            elif idx == 2:
                navigate_to("/movements")

        bottom_nav = ft.NavigationBar(
            destinations=nav_destinations,
            selected_index=selected_index if selected_index is not None else 0,
            on_change=on_nav_change
        )

        # Drawer for other screens: Categories, Users, Settings, Logout
        drawer_items = [
            ft.NavigationDrawerDestination(
                icon=Icons.ACCOUNT_CIRCLE,
                label=f"{session.username} ({session.role.capitalize()})"
            ),
            ft.Divider(),
            ft.NavigationDrawerDestination(
                icon=Icons.DASHBOARD_ROUNDED,
                label=get_text('dashboard', lang)
            ),
            ft.NavigationDrawerDestination(
                icon=Icons.SHOPPING_BAG_ROUNDED,
                label=get_text('products', lang)
            ),
            ft.NavigationDrawerDestination(
                icon=Icons.SWAP_HORIZ_ROUNDED,
                label=get_text('movements', lang)
            ),
        ]

        if session.role == 'admin':
            drawer_items.extend([
                ft.NavigationDrawerDestination(
                    icon=Icons.CATEGORY_ROUNDED,
                    label=get_text('categories', lang)
                ),
                ft.NavigationDrawerDestination(
                    icon=Icons.PEOPLE_ROUNDED,
                    label=get_text('users', lang)
                ),
            ])

        drawer_items.extend([
            ft.NavigationDrawerDestination(
                icon=Icons.SETTINGS_ROUNDED,
                label=get_text('settings', lang)
            ),
            ft.Divider(),
            ft.NavigationDrawerDestination(
                icon=Icons.LOGOUT_ROUNDED,
                label=get_text('logout', lang)
            )
        ])

        def on_drawer_change(e):
            idx = e.control.selected_index
            selected_dest = drawer_items[idx]
            if not isinstance(selected_dest, ft.NavigationDrawerDestination):
                return

            label = selected_dest.label
            page.close_drawer()
            if label == get_text('dashboard', lang):
                navigate_to("/dashboard")
            elif label == get_text('products', lang):
                navigate_to("/products")
            elif label == get_text('movements', lang):
                navigate_to("/movements")
            elif label == get_text('categories', lang):
                navigate_to("/categories")
            elif label == get_text('users', lang):
                navigate_to("/users")
            elif label == get_text('settings', lang):
                navigate_to("/settings")
            elif label == get_text('logout', lang):
                session.clear()
                navigate_to("/login")
                show_msg("Sesión cerrada" if lang == 'es' else "Logged out successfully", Colors.BLUE)

        nav_drawer = ft.NavigationDrawer(
            controls=drawer_items,
            on_change=on_drawer_change
        )

        app_bar = ft.AppBar(
            title=ft.Text(current_view_title, weight=ft.FontWeight.BOLD),
            bgcolor=Colors.BLUE_700,
            color=Colors.WHITE,
            center_title=True,
            leading=ft.IconButton(
                icon=Icons.MENU,
                icon_color=Colors.WHITE,
                on_click=lambda _: page.show_drawer(nav_drawer)
            )
        )

        return app_bar, bottom_nav, nav_drawer

    # Route change logic
    def route_change(e):
        page.views.clear()
        lang = session.lang

        # Apply correct theme mode
        page.theme_mode = ft.ThemeMode.DARK if session.theme == 'dark' else ft.ThemeMode.LIGHT

        # Protect Routes
        if page.route not in ["/", "/login", "/register"] and not session.user_id:
            page.route = "/login"
            show_msg("Debes iniciar sesión primero.", Colors.ORANGE)

        # -------------------------------------------------------------
        # 1. Login View
        # -------------------------------------------------------------
        if page.route == "/" or page.route == "/login":
            txt_email = ft.TextField(label=get_text('email', lang), width=320, keyboard_type=ft.KeyboardType.EMAIL)
            txt_password = ft.TextField(label=get_text('password', lang), password=True, can_reveal_password=True, width=320)

            def do_login(ev):
                email = txt_email.value.strip()
                password = txt_password.value.strip()
                if not email or not password:
                    show_msg(get_text('all_fields_required', lang), Colors.RED)
                    return

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre, password, rol, tema, idioma FROM usuarios WHERE correo=?", (email,))
                user = cursor.fetchone()
                conn.close()

                if user and check_password_hash(user[2], password):
                    session.set_user(user[0], user[1], user[3], user[4], user[5])
                    show_msg(get_text('success', session.lang), Colors.GREEN)
                    navigate_to("/dashboard")
                else:
                    show_msg(get_text('invalid_credentials', lang), Colors.RED)

            btn_login = ft.ElevatedButton(get_text('login', lang), on_click=do_login, width=320, bgcolor=Colors.BLUE_700, color=Colors.WHITE)
            btn_to_register = ft.TextButton(get_text('no_account', lang), on_click=lambda _: navigate_to("/register"))

            page.views.append(
                ft.View(
                    "/login",
                    [
                        ft.AppBar(title=ft.Text("Papelería LyM - Login"), bgcolor=Colors.BLUE_700, color=Colors.WHITE, center_title=True),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Icon(Icons.BOOKMARK_ADDED_ROUNDED, size=80, color=Colors.BLUE_700),
                                    ft.Text("Papelería LyM", size=30, weight=ft.FontWeight.BOLD),
                                    ft.Text("Gestión de Inventario", size=16, color=Colors.GREY_600),
                                    ft.VerticalDivider(height=20),
                                    txt_email,
                                    txt_password,
                                    ft.VerticalDivider(height=10),
                                    btn_login,
                                    btn_to_register,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            alignment=ft.alignment.center,
                            padding=20,
                            expand=True
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )

        # -------------------------------------------------------------
        # 2. Register View
        # -------------------------------------------------------------
        elif page.route == "/register":
            txt_name = ft.TextField(label=get_text('full_name', lang), width=320)
            txt_email = ft.TextField(label=get_text('email', lang), width=320, keyboard_type=ft.KeyboardType.EMAIL)
            txt_password = ft.TextField(label=get_text('password', lang), password=True, can_reveal_password=True, width=320)
            txt_confirm = ft.TextField(label=get_text('confirm_password', lang), password=True, can_reveal_password=True, width=320)

            def do_register(ev):
                name = txt_name.value.strip()
                email = txt_email.value.strip()
                password = txt_password.value.strip()
                confirm = txt_confirm.value.strip()

                if not all([name, email, password, confirm]):
                    show_msg(get_text('all_fields_required', lang), Colors.RED)
                    return

                if password != confirm:
                    show_msg("Las contraseñas no coinciden" if lang == 'es' else "Passwords do not match", Colors.RED)
                    return

                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE correo=?", (email,))
                if cursor.fetchone():
                    conn.close()
                    show_msg(get_text('email_exists', lang), Colors.RED)
                    return

                hash_pass = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO usuarios (nombre, correo, password, rol, tema, idioma) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, email, hash_pass, "cliente", "light", "es")
                )
                conn.commit()
                conn.close()

                show_msg("Registro exitoso. Inicia sesión." if lang == 'es' else "Registration successful. Login.", Colors.GREEN)
                navigate_to("/login")

            btn_register = ft.ElevatedButton(get_text('register', lang), on_click=do_register, width=320, bgcolor=Colors.BLUE_700, color=Colors.WHITE)
            btn_to_login = ft.TextButton(get_text('have_account', lang), on_click=lambda _: navigate_to("/login"))

            page.views.append(
                ft.View(
                    "/register",
                    [
                        ft.AppBar(title=ft.Text("Papelería LyM - Registro"), bgcolor=Colors.BLUE_700, color=Colors.WHITE, center_title=True),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Icon(Icons.PERSON_ADD_ROUNDED, size=60, color=Colors.BLUE_700),
                                    ft.Text("Crear Cuenta", size=24, weight=ft.FontWeight.BOLD),
                                    ft.VerticalDivider(height=10),
                                    txt_name,
                                    txt_email,
                                    txt_password,
                                    txt_confirm,
                                    ft.VerticalDivider(height=10),
                                    btn_register,
                                    btn_to_login,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            alignment=ft.alignment.center,
                            padding=20,
                            expand=True
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )

        # -------------------------------------------------------------
        # 3. Dashboard View
        # -------------------------------------------------------------
        elif page.route == "/dashboard":
            app_bar, bottom_nav, nav_drawer = get_navigation_layout(get_text('dashboard', lang), 0)

            # Fetch DB statistics
            conn = get_db_connection()
            cursor = conn.cursor()

            # Total products
            cursor.execute("SELECT COUNT(*) FROM productos")
            total_productos = cursor.fetchone()[0]

            # Stock bajo (< 10)
            cursor.execute("SELECT COUNT(*) FROM productos WHERE stock < 10")
            stock_bajo = cursor.fetchone()[0]

            # Total users
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = cursor.fetchone()[0]

            # Last 5 movements
            cursor.execute("""
                SELECT m.tipo, m.cantidad, p.nombre, m.fecha
                FROM movimientos m
                LEFT JOIN productos p ON m.id_producto = p.id
                ORDER BY m.fecha DESC LIMIT 5
            """)
            recientes = cursor.fetchall()
            conn.close()

            # Alerts logic
            alert_boxes = []
            if stock_bajo > 0:
                alert_boxes.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(Icons.WARNING_AMBER_ROUNDED, color=Colors.RED_800),
                                ft.Text(f"{get_text('low_stock_warning', lang)} {stock_bajo} productos", color=Colors.RED_800, weight=ft.FontWeight.BOLD),
                            ]
                        ),
                        bgcolor=Colors.RED_100, # Handled elegantly, or Colors.RED_100, but Flet hex strings are great
                        border_radius=8,
                        padding=12
                    )
                )

            # Build recent movements list
            mov_list = []
            for mov in recientes:
                icon_color = Colors.GREEN if mov[0] == 'entrada' else Colors.RED
                icon_name = Icons.ARROW_UPWARD if mov[0] == 'entrada' else Icons.ARROW_DOWNWARD
                mov_list.append(
                    ft.ListTile(
                        leading=ft.Icon(icon_name, color=icon_color),
                        title=ft.Text(f"{mov[2]} ({mov[1]} uds)"),
                        subtitle=ft.Text(f"{mov[3]}"),
                    )
                )

            if not mov_list:
                mov_list.append(ft.Text("No hay movimientos registrados.", color=Colors.GREY_600, style=ft.TextThemeStyle.BODY_SMALL))

            page.views.append(
                ft.View(
                    "/dashboard",
                    [
                        app_bar,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(f"Bienvenido/a, {session.username}!", size=22, weight=ft.FontWeight.BOLD),
                                    ft.Text(get_text('main_panel', lang), size=14, color=Colors.GREY_600),
                                    ft.Divider(height=10),
                                    *alert_boxes,
                                    ft.Row(
                                        [
                                            ft.Card(
                                                content=ft.Container(
                                                    content=ft.Column(
                                                        [
                                                            ft.Icon(Icons.SHOPPING_BAG, color=Colors.BLUE_700),
                                                            ft.Text(str(total_productos), size=24, weight=ft.FontWeight.BOLD),
                                                            ft.Text(get_text('total_products', lang), size=11, text_align=ft.TextAlign.CENTER)
                                                        ],
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                                    ),
                                                    padding=12,
                                                    width=110
                                                )
                                            ),
                                            ft.Card(
                                                content=ft.Container(
                                                    content=ft.Column(
                                                        [
                                                            ft.Icon(Icons.WARNING, color=Colors.ORANGE_700),
                                                            ft.Text(str(stock_bajo), size=24, weight=ft.FontWeight.BOLD, color=Colors.ORANGE_700 if stock_bajo > 0 else None),
                                                            ft.Text(get_text('stock_bajo', lang), size=11, text_align=ft.TextAlign.CENTER)
                                                        ],
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                                    ),
                                                    padding=12,
                                                    width=110
                                                )
                                            ),
                                            ft.Card(
                                                content=ft.Container(
                                                    content=ft.Column(
                                                        [
                                                            ft.Icon(Icons.PEOPLE, color=Colors.GREEN_700),
                                                            ft.Text(str(total_usuarios), size=24, weight=ft.FontWeight.BOLD),
                                                            ft.Text(get_text('total_users', lang), size=11, text_align=ft.TextAlign.CENTER)
                                                        ],
                                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
                                                    ),
                                                    padding=12,
                                                    width=110
                                                )
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=5
                                    ),
                                    ft.Divider(height=10),
                                    ft.Text(get_text('recent_movements', lang), size=18, weight=ft.FontWeight.BOLD),
                                    ft.Column(mov_list, spacing=5)
                                ],
                                spacing=15
                            ),
                            padding=15
                        ),
                        bottom_nav
                    ],
                    drawer=nav_drawer,
                    scroll=ft.ScrollMode.AUTO
                )
            )

        # -------------------------------------------------------------
        # 4. Products View
        # -------------------------------------------------------------
        elif page.route == "/products":
            app_bar, bottom_nav, nav_drawer = get_navigation_layout(get_text('products', lang), 1)

            search_query = ft.TextField(label=get_text('search', lang), expand=True)
            products_list_column = ft.Column(spacing=10)

            def load_products(query=""):
                products_list_column.controls.clear()
                conn = get_db_connection()
                cursor = conn.cursor()
                if query:
                    cursor.execute("""
                        SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock, c.nombre as cat_nombre, p.imagen, p.id_categoria
                        FROM productos p
                        LEFT JOIN categorias c ON p.id_categoria = c.id
                        WHERE p.nombre LIKE ? OR p.descripcion LIKE ? OR c.nombre LIKE ?
                    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
                else:
                    cursor.execute("""
                        SELECT p.id, p.nombre, p.descripcion, p.precio, p.stock, c.nombre as cat_nombre, p.imagen, p.id_categoria
                        FROM productos p
                        LEFT JOIN categorias c ON p.id_categoria = c.id
                    """)
                prods = cursor.fetchall()
                conn.close()

                for p in prods:
                    # Stock Color formatting
                    stock_text_color = Colors.RED_800 if p["stock"] < 10 else Colors.GREEN_800

                    # Edit / Delete controls if Admin
                    action_buttons = []
                    if session.role == 'admin':
                        action_buttons = [
                            ft.IconButton(
                                icon=Icons.EDIT,
                                icon_color=Colors.BLUE,
                                on_click=lambda ev, prod_id=p["id"]: open_edit_product_dialog(prod_id)
                            ),
                            ft.IconButton(
                                icon=Icons.DELETE,
                                icon_color=Colors.RED,
                                on_click=lambda ev, prod_id=p["id"]: delete_product(prod_id)
                            ),
                        ]

                    # Local image or fallback placeholder icon
                    image_path = os.path.join("static", "uploads", p["imagen"]) if p["imagen"] else None
                    if image_path and os.path.exists(image_path):
                        avatar = ft.Image(src=image_path, width=50, height=50, fit=ft.ImageFit.COVER)
                    else:
                        avatar = ft.Icon(Icons.IMAGE_NOT_SUPPORTED_ROUNDED, size=40, color=Colors.GREY_400)

                    products_list_column.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                avatar,
                                                ft.Column(
                                                    [
                                                        ft.Text(p["nombre"], size=16, weight=ft.FontWeight.BOLD),
                                                        ft.Text(p["descripcion"] or "", size=12, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, width=220),
                                                        ft.Text(f"${p['precio']:.2f} | {p['cat_nombre'] or ''}", size=11, italic=True),
                                                    ],
                                                    tight=True,
                                                    spacing=2
                                                )
                                            ],
                                            alignment=ft.MainAxisAlignment.START,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                                        ),
                                        ft.Row(
                                            [
                                                ft.Text(f"{get_text('stock', lang)}: {p['stock']}", color=stock_text_color, weight=ft.FontWeight.BOLD),
                                                ft.Row(action_buttons, spacing=2)
                                            ],
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                        )
                                    ],
                                    spacing=8
                                ),
                                padding=12
                            )
                        )
                    )
                page.update()

            def delete_product(pid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM productos WHERE id=?", (pid,))
                conn.commit()
                conn.close()
                show_msg("Producto eliminado correctamente" if lang == 'es' else "Product deleted successfully", Colors.RED)
                load_products(search_query.value)

            def open_add_product_dialog(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM categorias")
                categories = cursor.fetchall()
                conn.close()

                cat_options = [ft.dropdown.Option(str(c["id"]), c["nombre"]) for c in categories]

                txt_pname = ft.TextField(label=get_text('name', lang))
                txt_pdesc = ft.TextField(label=get_text('description', lang), multiline=True)
                txt_pprice = ft.TextField(label=get_text('price', lang), keyboard_type=ft.KeyboardType.NUMBER)
                txt_pstock = ft.TextField(label=get_text('stock', lang), keyboard_type=ft.KeyboardType.NUMBER)
                dd_cat = ft.Dropdown(label=get_text('category', lang), options=cat_options)
                txt_pimg = ft.TextField(label="Nombre archivo imagen (ej: cuaderno.png)")

                def save_new_product(ev):
                    if not txt_pname.value or not txt_pprice.value or not txt_pstock.value:
                        show_msg("Nombre, precio y stock son obligatorios.", Colors.RED)
                        return

                    conn_add = get_db_connection()
                    cursor_add = conn_add.cursor()
                    cursor_add.execute(
                        "INSERT INTO productos (nombre, descripcion, precio, stock, id_categoria, imagen) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            txt_pname.value.strip(),
                            txt_pdesc.value.strip(),
                            float(txt_pprice.value),
                            int(txt_pstock.value),
                            int(dd_cat.value) if dd_cat.value else None,
                            txt_pimg.value.strip() if txt_pimg.value else None
                        )
                    )
                    conn_add.commit()
                    conn_add.close()
                    page.pop_dialog()
                    show_msg("Producto agregado correctamente", Colors.GREEN)
                    load_products(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Agregar Producto"),
                    content=ft.Column(
                        [
                            txt_pname, txt_pdesc, txt_pprice, txt_pstock, dd_cat, txt_pimg
                        ],
                        tight=True,
                        spacing=10
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_new_product)
                    ]
                )
                page.show_dialog(dlg)

            def open_edit_product_dialog(pid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, descripcion, precio, stock, id_categoria, imagen FROM productos WHERE id=?", (pid,))
                prod = cursor.fetchone()

                cursor.execute("SELECT id, nombre FROM categorias")
                categories = cursor.fetchall()
                conn.close()

                cat_options = [ft.dropdown.Option(str(c["id"]), c["nombre"]) for c in categories]

                txt_pname = ft.TextField(label=get_text('name', lang), value=prod["nombre"])
                txt_pdesc = ft.TextField(label=get_text('description', lang), value=prod["descripcion"] or "", multiline=True)
                txt_pprice = ft.TextField(label=get_text('price', lang), value=str(prod["precio"]), keyboard_type=ft.KeyboardType.NUMBER)
                txt_pstock = ft.TextField(label=get_text('stock', lang), value=str(prod["stock"]), keyboard_type=ft.KeyboardType.NUMBER)
                dd_cat = ft.Dropdown(label=get_text('category', lang), options=cat_options, value=str(prod["id_categoria"]) if prod["id_categoria"] else None)
                txt_pimg = ft.TextField(label="Nombre archivo imagen", value=prod["imagen"] or "")

                def save_edited_product(ev):
                    if not txt_pname.value or not txt_pprice.value or not txt_pstock.value:
                        show_msg("Campos obligatorios faltantes.", Colors.RED)
                        return

                    conn_edit = get_db_connection()
                    cursor_edit = conn_edit.cursor()
                    cursor_edit.execute("""
                        UPDATE productos
                        SET nombre=?, descripcion=?, precio=?, stock=?, id_categoria=?, imagen=?
                        WHERE id=?
                    """, (
                        txt_pname.value.strip(),
                        txt_pdesc.value.strip(),
                        float(txt_pprice.value),
                        int(txt_pstock.value),
                        int(dd_cat.value) if dd_cat.value else None,
                        txt_pimg.value.strip() if txt_pimg.value else None,
                        pid
                    ))
                    conn_edit.commit()
                    conn_edit.close()
                    page.pop_dialog()
                    show_msg("Producto actualizado correctamente", Colors.GREEN)
                    load_products(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Editar Producto"),
                    content=ft.Column(
                        [
                            txt_pname, txt_pdesc, txt_pprice, txt_pstock, dd_cat, txt_pimg
                        ],
                        tight=True,
                        spacing=10
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_edited_product)
                    ]
                )
                page.show_dialog(dlg)

            def reset_products_table(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM productos")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='productos'")
                conn.commit()
                conn.close()
                show_msg("Tabla de productos reiniciada correctamente.", Colors.RED)
                load_products()

            def on_pdf_report(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.nombre, c.nombre, p.precio, p.stock
                    FROM productos p
                    LEFT JOIN categorias c ON p.id_categoria = c.id
                """)
                datos = cursor.fetchall()
                conn.close()

                path = generate_pdf_report("Reporte de Productos", ["ID", "Nombre", "Categoría", "Precio", "Stock"], datos)
                show_msg(f"PDF generado: {path}", Colors.BLUE)

            # Build UI Header buttons
            action_row = ft.Row(spacing=5)
            if session.role == 'admin':
                action_row.controls.extend([
                    ft.ElevatedButton(get_text('add', lang), icon=Icons.ADD, on_click=open_add_product_dialog, bgcolor=Colors.BLUE_700, color=Colors.WHITE),
                    ft.IconButton(Icons.REFRESH_ROUNDED, tooltip=get_text('reset_table', lang), icon_color=Colors.RED, on_click=reset_products_table),
                    ft.IconButton(Icons.PICTURE_AS_PDF_ROUNDED, tooltip=get_text('generate_report', lang), icon_color=Colors.BLUE_700, on_click=on_pdf_report)
                ])

            search_query.on_change = lambda e: load_products(search_query.value)

            page.views.append(
                ft.View(
                    "/products",
                    [
                        app_bar,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row([search_query, ft.IconButton(Icons.SEARCH, on_click=lambda _: load_products(search_query.value))]),
                                    action_row,
                                    ft.Divider(),
                                    products_list_column
                                ],
                                spacing=10
                            ),
                            padding=15
                        ),
                        bottom_nav
                    ],
                    drawer=nav_drawer,
                    scroll=ft.ScrollMode.AUTO
                )
            )
            load_products()

        # -------------------------------------------------------------
        # 5. Categories View
        # -------------------------------------------------------------
        elif page.route == "/categories":
            app_bar, bottom_nav, nav_drawer = get_navigation_layout(get_text('categories', lang), None)

            search_query = ft.TextField(label=get_text('search', lang), expand=True)
            categories_list_column = ft.Column(spacing=10)

            def load_categories(query=""):
                categories_list_column.controls.clear()
                conn = get_db_connection()
                cursor = conn.cursor()
                if query:
                    cursor.execute("SELECT id, nombre, descripcion FROM categorias WHERE nombre LIKE ? OR descripcion LIKE ?", (f"%{query}%", f"%{query}%"))
                else:
                    cursor.execute("SELECT id, nombre, descripcion FROM categorias")
                cats = cursor.fetchall()
                conn.close()

                for c in cats:
                    categories_list_column.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Column(
                                            [
                                                ft.Text(c["nombre"], size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text(c["descripcion"] or "", size=12, width=240)
                                            ],
                                            tight=True,
                                            expand=True
                                        ),
                                        ft.Row(
                                            [
                                                ft.IconButton(Icons.EDIT, icon_color=Colors.BLUE, on_click=lambda ev, cid=c["id"]: open_edit_category_dialog(cid)),
                                                ft.IconButton(Icons.DELETE, icon_color=Colors.RED, on_click=lambda ev, cid=c["id"]: delete_category(cid))
                                            ],
                                            spacing=2
                                        )
                                    ]
                                ),
                                padding=12
                            )
                        )
                    )
                page.update()

            def delete_category(cid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categorias WHERE id=?", (cid,))
                conn.commit()
                conn.close()
                show_msg("Categoría eliminada correctamente", Colors.RED)
                load_categories(search_query.value)

            def open_add_category_dialog(e):
                txt_cname = ft.TextField(label=get_text('name', lang))
                txt_cdesc = ft.TextField(label=get_text('description', lang), multiline=True)

                def save_new_category(ev):
                    if not txt_cname.value:
                        show_msg("El nombre es obligatorio", Colors.RED)
                        return
                    conn_add = get_db_connection()
                    cursor_add = conn_add.cursor()
                    cursor_add.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (txt_cname.value.strip(), txt_cdesc.value.strip()))
                    conn_add.commit()
                    conn_add.close()
                    page.pop_dialog()
                    show_msg("Categoría agregada correctamente", Colors.GREEN)
                    load_categories(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Agregar Categoría"),
                    content=ft.Column([txt_cname, txt_cdesc], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_new_category)
                    ]
                )
                page.show_dialog(dlg)

            def open_edit_category_dialog(cid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, descripcion FROM categorias WHERE id=?", (cid,))
                cat = cursor.fetchone()
                conn.close()

                txt_cname = ft.TextField(label=get_text('name', lang), value=cat["nombre"])
                txt_cdesc = ft.TextField(label=get_text('description', lang), value=cat["descripcion"] or "", multiline=True)

                def save_edited_category(ev):
                    if not txt_cname.value:
                        show_msg("El nombre es obligatorio", Colors.RED)
                        return
                    conn_edit = get_db_connection()
                    cursor_edit = conn_edit.cursor()
                    cursor_edit.execute("UPDATE categorias SET nombre=?, descripcion=? WHERE id=?", (txt_cname.value.strip(), txt_cdesc.value.strip(), cid))
                    conn_edit.commit()
                    conn_edit.close()
                    page.pop_dialog()
                    show_msg("Categoría actualizada correctamente", Colors.GREEN)
                    load_categories(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Editar Categoría"),
                    content=ft.Column([txt_cname, txt_cdesc], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_edited_category)
                    ]
                )
                page.show_dialog(dlg)

            def reset_categories_table(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM categorias")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='categorias'")
                conn.commit()
                conn.close()
                show_msg("Tabla de categorías reiniciada correctamente.", Colors.RED)
                load_categories()

            search_query.on_change = lambda e: load_categories(search_query.value)

            page.views.append(
                ft.View(
                    "/categories",
                    [
                        app_bar,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row([search_query, ft.IconButton(Icons.SEARCH, on_click=lambda _: load_categories(search_query.value))]),
                                    ft.Row([
                                        ft.ElevatedButton(get_text('add', lang), icon=Icons.ADD, on_click=open_add_category_dialog, bgcolor=Colors.BLUE_700, color=Colors.WHITE),
                                        ft.IconButton(Icons.REFRESH_ROUNDED, tooltip=get_text('reset_table', lang), icon_color=Colors.RED, on_click=reset_categories_table)
                                    ], spacing=5),
                                    ft.Divider(),
                                    categories_list_column
                                ],
                                spacing=10
                            ),
                            padding=15
                        ),
                        bottom_nav
                    ],
                    drawer=nav_drawer,
                    scroll=ft.ScrollMode.AUTO
                )
            )
            load_categories()

        # -------------------------------------------------------------
        # 6. Users View
        # -------------------------------------------------------------
        elif page.route == "/users":
            app_bar, bottom_nav, nav_drawer = get_navigation_layout(get_text('users', lang), None)

            search_query = ft.TextField(label=get_text('search', lang), expand=True)
            users_list_column = ft.Column(spacing=10)

            def load_users(query=""):
                users_list_column.controls.clear()
                conn = get_db_connection()
                cursor = conn.cursor()
                if query:
                    cursor.execute("""
                        SELECT id, nombre, correo, rol, fecha_registro
                        FROM usuarios
                        WHERE nombre LIKE ? OR correo LIKE ? OR rol LIKE ?
                    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
                else:
                    cursor.execute("SELECT id, nombre, correo, rol, fecha_registro FROM usuarios")
                users = cursor.fetchall()
                conn.close()

                for u in users:
                    # Prevent admin deleting themselves in standard flow
                    action_buttons = []
                    if u["id"] != session.user_id:
                        action_buttons = [
                            ft.IconButton(Icons.EDIT, icon_color=Colors.BLUE, on_click=lambda ev, uid=u["id"]: open_edit_user_dialog(uid)),
                            ft.IconButton(Icons.DELETE, icon_color=Colors.RED, on_click=lambda ev, uid=u["id"]: delete_user(uid))
                        ]

                    users_list_column.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Column(
                                            [
                                                ft.Text(u["nombre"], size=16, weight=ft.FontWeight.BOLD),
                                                ft.Text(u["correo"], size=12),
                                                ft.Text(f"Rol: {u['rol'].upper()}", size=11, color=Colors.BLUE_700 if u["rol"] == 'admin' else Colors.GREY_600)
                                            ],
                                            tight=True,
                                            expand=True
                                        ),
                                        ft.Row(action_buttons, spacing=2)
                                    ]
                                ),
                                padding=12
                            )
                        )
                    )
                page.update()

            def delete_user(uid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM usuarios WHERE id=?", (uid,))
                conn.commit()
                conn.close()
                show_msg("Usuario eliminado correctamente", Colors.RED)
                load_users(search_query.value)

            def open_add_user_dialog(e):
                txt_uname = ft.TextField(label=get_text('full_name', lang))
                txt_uemail = ft.TextField(label=get_text('email', lang), keyboard_type=ft.KeyboardType.EMAIL)
                txt_upass = ft.TextField(label=get_text('password', lang), password=True)
                dd_urol = ft.Dropdown(
                    label=get_text('role', lang),
                    options=[
                        ft.dropdown.Option("admin", "Admin"),
                        ft.dropdown.Option("cliente", "Cliente")
                    ],
                    value="cliente"
                )

                def save_new_user(ev):
                    if not txt_uname.value or not txt_uemail.value or not txt_upass.value:
                        show_msg("Campos obligatorios faltantes.", Colors.RED)
                        return

                    conn_add = get_db_connection()
                    cursor_add = conn_add.cursor()
                    cursor_add.execute("SELECT id FROM usuarios WHERE correo=?", (txt_uemail.value.strip(),))
                    if cursor_add.fetchone():
                        conn_add.close()
                        show_msg(get_text('email_exists', lang), Colors.RED)
                        return

                    hash_pass = generate_password_hash(txt_upass.value.strip())
                    cursor_add.execute(
                        "INSERT INTO usuarios (nombre, correo, password, rol) VALUES (?, ?, ?, ?)",
                        (txt_uname.value.strip(), txt_uemail.value.strip(), hash_pass, dd_urol.value)
                    )
                    conn_add.commit()
                    conn_add.close()
                    page.pop_dialog()
                    show_msg("Usuario agregado correctamente", Colors.GREEN)
                    load_users(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Agregar Usuario"),
                    content=ft.Column([txt_uname, txt_uemail, txt_upass, dd_urol], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_new_user)
                    ]
                )
                page.show_dialog(dlg)

            def open_edit_user_dialog(uid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT nombre, correo, rol FROM usuarios WHERE id=?", (uid,))
                usr = cursor.fetchone()
                conn.close()

                txt_uname = ft.TextField(label=get_text('full_name', lang), value=usr["nombre"])
                txt_uemail = ft.TextField(label=get_text('email', lang), value=usr["correo"])
                dd_urol = ft.Dropdown(
                    label=get_text('role', lang),
                    options=[
                        ft.dropdown.Option("admin", "Admin"),
                        ft.dropdown.Option("cliente", "Cliente")
                    ],
                    value=usr["rol"]
                )

                def save_edited_user(ev):
                    if not txt_uname.value or not txt_uemail.value:
                        show_msg("Campos obligatorios faltantes.", Colors.RED)
                        return

                    conn_edit = get_db_connection()
                    cursor_edit = conn_edit.cursor()
                    cursor_edit.execute("SELECT id FROM usuarios WHERE correo=? AND id!=?", (txt_uemail.value.strip(), uid))
                    if cursor_edit.fetchone():
                        conn_edit.close()
                        show_msg(get_text('email_in_use', lang), Colors.RED)
                        return

                    cursor_edit.execute(
                        "UPDATE usuarios SET nombre=?, correo=?, rol=? WHERE id=?",
                        (txt_uname.value.strip(), txt_uemail.value.strip(), dd_urol.value, uid)
                    )
                    conn_edit.commit()
                    conn_edit.close()
                    page.pop_dialog()
                    show_msg("Usuario actualizado correctamente", Colors.GREEN)
                    load_users(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Editar Usuario"),
                    content=ft.Column([txt_uname, txt_uemail, dd_urol], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_edited_user)
                    ]
                )
                page.show_dialog(dlg)

            def reset_users_table(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                # Retain ID=1 (the main admin)
                cursor.execute("DELETE FROM usuarios WHERE id > 1")
                cursor.execute("UPDATE sqlite_sequence SET seq=1 WHERE name='usuarios'")
                conn.commit()
                conn.close()
                show_msg("Tabla de usuarios reiniciada correctamente.", Colors.RED)
                load_users()

            def on_pdf_report(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre, correo, rol, fecha_registro FROM usuarios")
                datos = cursor.fetchall()
                conn.close()

                path = generate_pdf_report("Reporte de Usuarios", ["ID", "Nombre", "Correo", "Rol", "Fecha"], datos)
                show_msg(f"PDF generado: {path}", Colors.BLUE)

            search_query.on_change = lambda e: load_users(search_query.value)

            page.views.append(
                ft.View(
                    "/users",
                    [
                        app_bar,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row([search_query, ft.IconButton(Icons.SEARCH, on_click=lambda _: load_users(search_query.value))]),
                                    ft.Row([
                                        ft.ElevatedButton(get_text('add', lang), icon=Icons.ADD, on_click=open_add_user_dialog, bgcolor=Colors.BLUE_700, color=Colors.WHITE),
                                        ft.IconButton(Icons.REFRESH_ROUNDED, tooltip=get_text('reset_table', lang), icon_color=Colors.RED, on_click=reset_users_table),
                                        ft.IconButton(Icons.PICTURE_AS_PDF_ROUNDED, tooltip=get_text('generate_report', lang), icon_color=Colors.BLUE_700, on_click=on_pdf_report)
                                    ], spacing=5),
                                    ft.Divider(),
                                    users_list_column
                                ],
                                spacing=10
                            ),
                            padding=15
                        ),
                        bottom_nav
                    ],
                    drawer=nav_drawer,
                    scroll=ft.ScrollMode.AUTO
                )
            )
            load_users()

        # -------------------------------------------------------------
        # 7. Movements View
        # -------------------------------------------------------------
        elif page.route == "/movements":
            app_bar, bottom_nav, nav_drawer = get_navigation_layout(get_text('movements', lang), 2)

            search_query = ft.TextField(label=get_text('search', lang), expand=True)
            movements_list_column = ft.Column(spacing=10)

            def load_movements(query=""):
                movements_list_column.controls.clear()
                conn = get_db_connection()
                cursor = conn.cursor()
                if query:
                    cursor.execute("""
                        SELECT m.id, m.tipo, m.cantidad, p.nombre as prod_nombre, u.nombre as usr_nombre, m.fecha
                        FROM movimientos m
                        LEFT JOIN productos p ON m.id_producto = p.id
                        LEFT JOIN usuarios u ON m.id_usuario = u.id
                        WHERE p.nombre LIKE ? OR u.nombre LIKE ? OR m.tipo LIKE ?
                        ORDER BY m.fecha DESC
                    """, (f"%{query}%", f"%{query}%", f"%{query}%"))
                else:
                    cursor.execute("""
                        SELECT m.id, m.tipo, m.cantidad, p.nombre as prod_nombre, u.nombre as usr_nombre, m.fecha
                        FROM movimientos m
                        LEFT JOIN productos p ON m.id_producto = p.id
                        LEFT JOIN usuarios u ON m.id_usuario = u.id
                        ORDER BY m.fecha DESC
                    """)
                moves = cursor.fetchall()
                conn.close()

                for m in moves:
                    icon_color = Colors.GREEN if m["tipo"] == 'entrada' else Colors.RED
                    icon_name = Icons.ARROW_UPWARD if m["tipo"] == 'entrada' else Icons.ARROW_DOWNWARD

                    action_buttons = []
                    if session.role == 'admin':
                        action_buttons = [
                            ft.IconButton(Icons.EDIT, icon_color=Colors.BLUE, on_click=lambda ev, mid=m["id"]: open_edit_movement_dialog(mid)),
                            ft.IconButton(Icons.DELETE, icon_color=Colors.RED, on_click=lambda ev, mid=m["id"]: delete_movement(mid))
                        ]

                    movements_list_column.controls.append(
                        ft.Card(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(icon_name, color=icon_color, size=30),
                                        ft.Column(
                                            [
                                                ft.Text(f"{m['prod_nombre'] or 'Desconocido'}", size=15, weight=ft.FontWeight.BOLD),
                                                ft.Text(f"{get_text('quantity', lang)}: {m['cantidad']} units", size=12),
                                                ft.Text(f"By: {m['usr_nombre'] or 'Desconocido'} | {m['fecha']}", size=10, italic=True)
                                            ],
                                            tight=True,
                                            expand=True
                                        ),
                                        ft.Row(action_buttons, spacing=2)
                                    ]
                                ),
                                padding=12
                            )
                        )
                    )
                page.update()

            def delete_movement(mid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM movimientos WHERE id=?", (mid,))
                conn.commit()
                conn.close()
                show_msg("Movimiento eliminado correctamente", Colors.RED)
                load_movements(search_query.value)

            def open_add_movement_dialog(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre, stock FROM productos")
                products = cursor.fetchall()
                conn.close()

                prod_options = [ft.dropdown.Option(str(p["id"]), f"{p['nombre']} (Stock: {p['stock']})") for p in products]

                dd_type = ft.Dropdown(
                    label=get_text('type', lang),
                    options=[
                        ft.dropdown.Option("entrada", "Entrada (Ingreso)"),
                        ft.dropdown.Option("salida", "Salida (Egreso)")
                    ],
                    value="entrada"
                )
                txt_qty = ft.TextField(label=get_text('quantity', lang), keyboard_type=ft.KeyboardType.NUMBER)
                dd_prod = ft.Dropdown(label=get_text('products', lang), options=prod_options)

                def save_new_movement(ev):
                    if not txt_qty.value or not dd_prod.value:
                        show_msg("Cantidad y producto son obligatorios.", Colors.RED)
                        return

                    qty = int(txt_qty.value)
                    prod_id = int(dd_prod.value)
                    mtype = dd_type.value

                    conn_db = get_db_connection()
                    cursor_db = conn_db.cursor()
                    cursor_db.execute("SELECT stock FROM productos WHERE id=?", (prod_id,))
                    stock_row = cursor_db.fetchone()
                    if not stock_row:
                        conn_db.close()
                        show_msg(get_text('invalid_product', lang), Colors.RED)
                        return

                    current_stock = stock_row["stock"]
                    new_stock = current_stock + qty if mtype == "entrada" else current_stock - qty

                    if new_stock < 0:
                        conn_db.close()
                        show_msg(get_text('no_stock', lang), Colors.RED)
                        return

                    cursor_db.execute("INSERT INTO movimientos (tipo, cantidad, id_producto, id_usuario) VALUES (?, ?, ?, ?)", (mtype, qty, prod_id, session.user_id))
                    cursor_db.execute("UPDATE productos SET stock=? WHERE id=?", (new_stock, prod_id))
                    conn_db.commit()
                    conn_db.close()

                    page.pop_dialog()
                    show_msg("Movimiento registrado correctamente", Colors.GREEN)
                    load_movements(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Registrar Movimiento"),
                    content=ft.Column([dd_type, dd_prod, txt_qty], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_new_movement)
                    ]
                )
                page.show_dialog(dlg)

            def open_edit_movement_dialog(mid):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT tipo, cantidad FROM movimientos WHERE id=?", (mid,))
                move = cursor.fetchone()
                conn.close()

                dd_type = ft.Dropdown(
                    label=get_text('type', lang),
                    options=[
                        ft.dropdown.Option("entrada", "Entrada"),
                        ft.dropdown.Option("salida", "Salida")
                    ],
                    value=move["tipo"]
                )
                txt_qty = ft.TextField(label=get_text('quantity', lang), value=str(move["cantidad"]), keyboard_type=ft.KeyboardType.NUMBER)

                def save_edited_movement(ev):
                    if not txt_qty.value:
                        show_msg("Cantidad es obligatoria.", Colors.RED)
                        return

                    conn_edit = get_db_connection()
                    cursor_edit = conn_edit.cursor()
                    cursor_edit.execute("UPDATE movimientos SET tipo=?, cantidad=? WHERE id=?", (dd_type.value, int(txt_qty.value), mid))
                    conn_edit.commit()
                    conn_edit.close()
                    page.pop_dialog()
                    show_msg("Movimiento actualizado correctamente", Colors.GREEN)
                    load_movements(search_query.value)

                dlg = ft.AlertDialog(
                    title=ft.Text("Editar Movimiento"),
                    content=ft.Column([dd_type, txt_qty], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: page.pop_dialog()),
                        ft.ElevatedButton("Guardar", on_click=save_edited_movement)
                    ]
                )
                page.show_dialog(dlg)

            def reset_movements_table(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM movimientos")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='movimientos'")
                conn.commit()
                conn.close()
                show_msg("Tabla de movimientos reiniciada correctamente.", Colors.RED)
                load_movements()

            def on_pdf_report(e):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.id, m.tipo, m.cantidad, p.nombre, u.nombre, m.fecha
                    FROM movimientos m
                    LEFT JOIN productos p ON m.id_producto = p.id
                    LEFT JOIN usuarios u ON m.id_usuario = u.id
                    ORDER BY m.fecha DESC
                """)
                datos = cursor.fetchall()
                conn.close()

                path = generate_pdf_report("Reporte de Movimientos", ["ID", "Tipo", "Cantidad", "Producto", "Usuario", "Fecha"], datos)
                show_msg(f"PDF generado: {path}", Colors.BLUE)

            search_query.on_change = lambda e: load_movements(search_query.value)

            page.views.append(
                ft.View(
                    "/movements",
                    [
                        app_bar,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Row([search_query, ft.IconButton(Icons.SEARCH, on_click=lambda _: load_movements(search_query.value))]),
                                    ft.Row([
                                        ft.ElevatedButton(get_text('add', lang), icon=Icons.ADD, on_click=open_add_movement_dialog, bgcolor=Colors.BLUE_700, color=Colors.WHITE),
                                        ft.IconButton(Icons.REFRESH_ROUNDED, tooltip=get_text('reset_table', lang), icon_color=Colors.RED, on_click=reset_movements_table),
                                        ft.IconButton(Icons.PICTURE_AS_PDF_ROUNDED, tooltip=get_text('generate_report', lang), icon_color=Colors.BLUE_700, on_click=on_pdf_report)
                                    ], spacing=5),
                                    ft.Divider(),
                                    movements_list_column
                                ],
                                spacing=10
                            ),
                            padding=15
                        ),
                        bottom_nav
                    ],
                    drawer=nav_drawer,
                    scroll=ft.ScrollMode.AUTO
                )
            )
            load_movements()

        # -------------------------------------------------------------
        # 8. Settings View
        # -------------------------------------------------------------
        elif page.route == "/settings":
            app_bar, bottom_nav, nav_drawer = get_navigation_layout(get_text('settings', lang), None)

            # Fetch current user settings
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, correo, tema, idioma FROM usuarios WHERE id=?", (session.user_id,))
            user_data = cursor.fetchone()
            conn.close()

            txt_name = ft.TextField(label=get_text('full_name', lang), value=user_data["nombre"])
            txt_email = ft.TextField(label=get_text('email', lang), value=user_data["correo"])
            dd_theme = ft.Dropdown(
                label=get_text('visual_theme', lang),
                options=[
                    ft.dropdown.Option("light", get_text('light', lang)),
                    ft.dropdown.Option("dark", get_text('dark', lang))
                ],
                value=user_data["tema"]
            )
            dd_lang = ft.Dropdown(
                label=get_text('language', lang),
                options=[
                    ft.dropdown.Option("es", "Español"),
                    ft.dropdown.Option("en", "English")
                ],
                value=user_data["idioma"]
            )

            def save_settings(ev):
                name = txt_name.value.strip()
                email = txt_email.value.strip()
                theme = dd_theme.value
                language = dd_lang.value

                if not name or not email:
                    show_msg("Todos los campos son obligatorios.", Colors.RED)
                    return

                conn_up = get_db_connection()
                cursor_up = conn_up.cursor()

                # Check email conflict
                cursor_up.execute("SELECT id FROM usuarios WHERE correo=? AND id!=?", (email, session.user_id))
                if cursor_up.fetchone():
                    conn_up.close()
                    show_msg(get_text('email_in_use', lang), Colors.RED)
                    return

                cursor_up.execute("""
                    UPDATE usuarios
                    SET nombre=?, correo=?, tema=?, idioma=?
                    WHERE id=?
                """, (name, email, theme, language, session.user_id))
                conn_up.commit()
                conn_up.close()

                # Refresh global session setting variables
                session.set_user(session.user_id, name, session.role, theme, language)

                show_msg(get_text('success', session.lang), Colors.GREEN)
                navigate_to("/settings")

            page.views.append(
                ft.View(
                    "/settings",
                    [
                        app_bar,
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(get_text('account', lang), size=18, weight=ft.FontWeight.BOLD),
                                    txt_name,
                                    txt_email,
                                    ft.Divider(height=10),
                                    ft.Text(get_text('settings', lang), size=18, weight=ft.FontWeight.BOLD),
                                    dd_theme,
                                    dd_lang,
                                    ft.VerticalDivider(height=15),
                                    ft.ElevatedButton(get_text('save_changes', lang), on_click=save_settings, width=320, bgcolor=Colors.BLUE_700, color=Colors.WHITE)
                                ],
                                spacing=15,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=15
                        ),
                        bottom_nav
                    ],
                    drawer=nav_drawer,
                    scroll=ft.ScrollMode.AUTO
                )
            )

        page.update()

    page.on_route_change = route_change
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)
