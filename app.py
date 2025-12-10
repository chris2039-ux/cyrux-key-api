import json
import uuid
import datetime
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
# El archivo keys.json se guarda en el mismo directorio del script
KEY_FILE = 'keys.json'

# --- Funciones de Persistencia de Datos ---

def load_keys():
    """Carga las claves desde keys.json o devuelve un diccionario vacío si no existe."""
    # Render puede no tener el archivo al inicio, por eso usamos un try-except
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'w') as f:
            json.dump({}, f)
        return {}
        
    try:
        with open(KEY_FILE, 'r') as f:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except Exception as e:
        print(f"Error al cargar claves: {e}")
        return {}

def save_keys(keys_data):
    """Guarda las claves en keys.json."""
    try:
        with open(KEY_FILE, 'w') as f:
            json.dump(keys_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar claves: {e}")
        return False

# --- RUTA PRINCIPAL: Generador de Clave (Ahora en la URL Base /) ---

@app.route('/', methods=['GET'])
def generate_key():
    """Genera una nueva clave, la guarda y la muestra al usuario en HTML."""
    
    # 1. Generar clave y expiración
    new_key = str(uuid.uuid4()).replace('-', '')
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    expiration_str = expiration_time.isoformat().split('.')[0] + 'Z' 
    
    # 2. Almacenar la clave
    keys = load_keys()
    keys[new_key] = expiration_str
    save_keys(keys)
    
    # 3. Preparar la respuesta HTML para el usuario
    local_exp_time = expiration_time.astimezone() 
    exp_display = local_exp_time.strftime("%d/%m/%Y a las %H:%M:%S %Z")

    html_response = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Clave Generada</title>
        <style>
            body {{ font-family: sans-serif; background-color: #0A0A0C; color: #FFFFFF; text-align: center; padding-top: 50px; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 30px; background-color: #121214; border-radius: 10px; border: 2px solid #FFFFFF; }}
            h1 {{ color: #FFFFFF; border-bottom: 1px solid rgba(255, 255, 255, 0.2); padding-bottom: 10px; }}
            .key-box {{ background-color: #1E1E22; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #00FF96; }}
            .key-box p {{ font-size: 1.5em; font-weight: bold; color: #00FF96; word-break: break-all; }}
            .info {{ color: #C8C8C8; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔑 Tu Código de Acceso CyruX Hub Generado</h1>
            <p class="info">¡Proceso completado! Copia el código a continuación.</p>
            <div class="key-box">
                <p>{new_key}</p>
            </div>
            <p class="info">La clave es válida hasta el: <strong>{exp_display}</strong></p>
            <p style="margin-top: 30px;">Ahora regresa a Roblox, pega la clave en el script y disfruta.</p>
        </div>
    </body>
    </html>
    """
    return html_response

# --- Ruta 2: Validador de Clave (Backend para el Script de Roblox) ---

@app.route('/api/v1/validateKey', methods=['GET'])
def validate_key():
    """Valida si la clave enviada por el script de Roblox es válida y no ha expirado."""
    
    key_to_validate = request.args.get('key')
    
    if not key_to_validate:
        return jsonify({"status": "invalid", "message": "No key provided"}), 400

    keys = load_keys()
    
    if key_to_validate not in keys:
        return jsonify({"status": "invalid", "message": "Key not found"}), 404

    try:
        expiration_str = keys[key_to_validate]
        expiration_time = datetime.datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
        current_time = datetime.datetime.now(datetime.timezone.utc)

        if current_time < expiration_time:
            return jsonify({"status": "valid", "message": "Access Granted"}), 200
        else:
            return jsonify({"status": "invalid", "message": "Key Expired"}), 401

    except Exception:
        return jsonify({"status": "invalid", "message": "Internal format error"}), 500

# --- Inicio de la Aplicación ---

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
