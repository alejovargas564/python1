from flask import Flask, render_template, request, session
import random

app = Flask(__name__)
app.secret_key = "clave-super-secreta"  # Necesaria para manejar sesiones

@app.route("/", methods=["GET", "POST"])
def index():
    # Si no existe número en sesión, lo crea
    if "numero" not in session:
        session["numero"] = random.randint(1, 100)
    if "veces" not in session:
        session["veces"] = 0

    mensaje = ""
    
    if request.method == "POST":
        try:
            intento = int(request.form["intento"])
            numero = session["numero"]
            veces_actual = int(session.get("veces", 0))
            veces_actual += 1
            session["veces"] = veces_actual

            if intento < numero:
                mensaje = "El número es MAYOR."
            elif intento > numero:
                mensaje = "El número es MENOR."
            else:
                nombre = request.args.get("nombre", "")
                mensaje = "¡Adivinaste! "+nombre+" lo lograste en " + str(session["veces"]) + " oportunidades. Se generó un nuevo número."
                
                session["numero"] = random.randint(1, 100)
                session["veces"] = 0
        
        except ValueError:
            mensaje = "Ingresa un número válido."

    return render_template("index.html", mensaje=mensaje)
