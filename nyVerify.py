from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Variables globales
archivos = {}
cupones = {}
usuarios = {}

# Función para generar códigos únicos
def generar_codigo():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Comando /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("¡Hola! 🤖 Soy el bot de gestión de cupones. Usa /subir_archivo 📤 para comenzar.")

# Subir archivo (solo admin)
def subir_archivo(update: Update, context: CallbackContext):
    if update.message.document:
        archivo = update.message.document
        archivo_id = archivo.file_id
        archivos[archivo_id] = {
            "nombre": archivo.file_name,
            "fecha_subida": datetime.now(),
            "cupones": []
        }
        update.message.reply_text(f"Archivo '{archivo.file_name}' subido correctamente. ✅")
    else:
        update.message.reply_text("Por favor, envía un archivo válido. ❌")

# Generar cupones (solo admin)
def generar_cupones(update: Update, context: CallbackContext):
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("Uso: /generar_cupones <cantidad> ⚙️")
        return

    cantidad = int(context.args[0])
    if not archivos:
        update.message.reply_text("No hay archivos disponibles para generar cupones. 📂❌")
        return

    ultimo_archivo_id = list(archivos.keys())[-1]
    for _ in range(cantidad):
        codigo = generar_codigo()
        while codigo in cupones:  # Asegurar unicidad
            codigo = generar_codigo()
        cupones[codigo] = {
            "estado": "Disponible",
            "fecha_creacion": datetime.now(),
            "fecha_expiracion": datetime.now() + timedelta(days=730),
            "archivo_id": ultimo_archivo_id,
            "usuario_redimido": None
        }
        archivos[ultimo_archivo_id]["cupones"].append(codigo)

    update.message.reply_text(f"🎉 {cantidad} cupones generados para el archivo '{archivos[ultimo_archivo_id]['nombre']}'.")

# Redimir cupón
def redimir(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("Uso: /redimir <código> 🎟️")
        return

    codigo = context.args[0]
    if codigo not in cupones:
        update.message.reply_text("El código ingresado no es válido. ❌")
        return

    if cupones[codigo]["estado"] == "Redimido":
        update.message.reply_text("Este cupón ya ha sido redimido. 🔁")
        return

    cupones[codigo]["estado"] = "Redimido"
    cupones[codigo]["usuario_redimido"] = update.message.from_user.id
    archivo_id = cupones[codigo]["archivo_id"]

    if update.message.from_user.id not in usuarios:
        usuarios[update.message.from_user.id] = {"archivos_redimidos": []}
    usuarios[update.message.from_user.id]["archivos_redimidos"].append(archivo_id)

    update.message.reply_text(f"✅ Cupón redimido. Ahora tienes acceso al archivo '{archivos[archivo_id]['nombre']}'. 📂")

# Configuración del bot
def main():
    # Reemplaza 'YOUR_TOKEN_HERE' con el token de tu bot
    updater = Updater("YOUR_TOKEN_HERE", use_context=True)
    dispatcher = updater.dispatcher

    # Registrar comandos
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("subir_archivo", subir_archivo))
    dispatcher.add_handler(CommandHandler("generar_cupones", generar_cupones, pass_args=True))
    dispatcher.add_handler(CommandHandler("redimir", redimir, pass_args=True))

    # Iniciar el bot
    updater.start_polling()
    print("Bot iniciado. Presiona Ctrl+C para detenerlo.")
    updater.idle()  # Mantener el bot activo

if __name__ == "__main__":
    main()
