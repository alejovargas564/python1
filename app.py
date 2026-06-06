from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
import psycopg2
import random

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-buscaminas-secreta")

# ── Conexión a PostgreSQL ──────────────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


# ── Ruta principal: registro de nombre ────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            error = "El nombre no puede estar vacío."
        elif len(nombre) < 2:
            error = "El nombre debe tener al menos 2 caracteres."
        elif len(nombre) > 50:
            error = "El nombre no puede superar 50 caracteres."
        else:
            session["nombre"] = nombre
            return redirect(url_for("juego"))
    return render_template("index.html", error=error)


# ── Ruta del juego ─────────────────────────────────────────────────────────────
@app.route("/juego")
def juego():
    if "nombre" not in session:
        return redirect(url_for("index"))
    return render_template("juego.html", nombre=session["nombre"])


# ── Ruta para guardar resultado ────────────────────────────────────────────────
@app.route("/guardar", methods=["POST"])
def guardar():
    if "nombre" not in session:
        return jsonify({"ok": False, "error": "Sesión expirada"}), 403

    try:
        data = request.get_json()
        resultado = int(data.get("resultado", 0))  # celdas descubiertas
        nombre = session["nombre"]

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO resultado_buscaminas (nombre, resultado) VALUES (%s, %s)",
                (nombre, resultado)
            )
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"ok": True})

        except psycopg2.OperationalError as e:
            # Error de conexión a la base de datos
            print(f"[DB ERROR] {e}")
            return jsonify({"ok": False, "error": "No se pudo conectar a la base de datos."}), 503

        except psycopg2.Error as e:
            # Cualquier otro error de PostgreSQL
            print(f"[DB ERROR] {e}")
            return jsonify({"ok": False, "error": "Error al guardar en la base de datos."}), 500

    except (ValueError, TypeError) as e:
        return jsonify({"ok": False, "error": "Datos inválidos recibidos."}), 400

    except Exception as e:
        print(f"[ERROR INESPERADO] {e}")
        return jsonify({"ok": False, "error": "Ocurrió un error inesperado."}), 500


# ── Ruta del ranking (consulta todos los estudiantes/jugadores) ────────────────
@app.route("/ranking")
def ranking():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT nombre, resultado FROM resultado_buscaminas ORDER BY resultado DESC LIMIT 20"
        )
        filas = cur.fetchall()
        cur.close()
        conn.close()
        jugadores = [{"nombre": f[0], "resultado": f[1]} for f in filas]
        return render_template("ranking.html", jugadores=jugadores)

    except psycopg2.OperationalError as e:
        print(f"[DB ERROR] {e}")
        return render_template("error.html",
                               titulo="Error de conexión",
                               mensaje="No se pudo conectar a la base de datos. Intenta más tarde."), 503

    except psycopg2.Error as e:
        print(f"[DB ERROR] {e}")
        return render_template("error.html",
                               titulo="Error de base de datos",
                               mensaje="Ocurrió un problema al consultar los datos."), 500

    except Exception as e:
        print(f"[ERROR INESPERADO] {e}")
        return render_template("error.html",
                               titulo="Error inesperado",
                               mensaje="Algo salió mal. Por favor intenta nuevamente."), 500


# ── Cerrar sesión / nueva partida ──────────────────────────────────────────────
@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False)
