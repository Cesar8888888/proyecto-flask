from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
import psycopg2

app = Flask(__name__)
# Clave secreta para gestionar las sesiones de usuario en Proyecto Desguace Colomi
app.secret_key = 'clave_secreta_desguace_colomi'

# -------------------------------------------------------------
# 1. Configuración de PostgreSQL (Base de datos en Docker)
# -------------------------------------------------------------
DB_HOST = "postgres_db"
DB_PORT = "5432"
DB_NAME = "desguace_db"
DB_USER = "desguace_user"
DB_PASSWORD = "desguace_password"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=3
    )

def init_db():
    """Crea la tabla de usuarios en PostgreSQL al arrancar la aplicación."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print(" [Proyecto Desguace Colomi] Base de datos inicializada correctamente.")
    except Exception as e:
        print(f" Error al inicializar la base de datos: {e}")

# Se ejecuta al iniciar el servidor
init_db()

# -------------------------------------------------------------
# 2. Configuración de Correo Electrónico (Mailtrap / Gmail)
# -------------------------------------------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''

mail = Mail(app)

# -------------------------------------------------------------
# 3. Rutas de Proyecto Desguace Colomi
# -------------------------------------------------------------

# A) Inicio
@app.route('/')
def home():
    return render_template('index.html')

# B) Catálogo de Piezas (Sin imágenes por el momento)
@app.route('/catalogo')
def catalogo():
    piezas = [
        {
            "nombre": "Faro Delantero Izquierdo",
            "categoria": "Iluminación",
            "precio": "45€",
            "imagen": "faro_izquierdo.jpg"
        },
        {
            "nombre": "Bombilla H7 Halógena 12V",
            "categoria": "Iluminación",
            "precio": "5€",
            "imagen": "bombilla_h7.jpg"
        },
        {
            "nombre": "Espejo Retrovisor Derecho",
            "categoria": "Carrocería",
            "precio": "30€",
            "imagen": "retrovisor_derecho.png"
        },
        {
            "nombre": "Piloto Trasero Mercedes",
            "categoria": "Iluminación",
            "precio": "35€",
            "imagen": "piloto_trasero_mercedes.jpg"
        }
    ]
    return render_template('catalogo.html', productos=piezas)

# C) Registro de Usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')

        # 1. Guardar en la base de datos
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s);",
                (nombre, email, password)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e_db:
            return render_template('registro.html', mensaje=f"Error en el registro (el correo podría estar ya registrado): {e_db}")

        # 2. Enviar correo de bienvenida
        try:
            msg = Message(
                subject="¡Bienvenido/a a Proyecto Desguace Colomi!",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"Hola {nombre},\n\nGracias por registrarte en Proyecto Desguace Colomi. Ya puedes iniciar sesión con tu correo y contraseña."
            mail.send(msg)
            return render_template('registro.html', mensaje=f"¡Usuario {nombre} registrado con éxito! Correo enviado a {email}.")
        except Exception as e_mail:
            return render_template('registro.html', mensaje=f"¡Usuario {nombre} guardado en la BD! (Nota: no se pudo enviar el correo de bienvenida).")

    return render_template('registro.html')

# D) Inicio de Sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM usuarios WHERE email = %s AND password = %s;", (email, password))
            usuario = cur.fetchone()
            cur.close()

            if usuario:
                session['usuario'] = usuario[0]  # Guardamos el nombre en la sesión
                return redirect(url_for('home'))
            
            return render_template('login.html', mensaje="Credenciales incorrectas. Inténtalo de nuevo.")
        except Exception as e:
            return render_template('login.html', mensaje=f"Error al conectar con la base de datos: {e}")
        finally:
            if conn:
                conn.close()

    return render_template('login.html')

# E) Cierre de Sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
