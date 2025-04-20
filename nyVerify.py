from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import nest_asyncio
import asyncio

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ¡Hola! Soy el bot de gestión de cupones. 📤 Usa /subir_archivo para comenzar.")

# Subir archivo (solo admin)
async def subir_archivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        archivo = update.message.document
        archivo_id = archivo.file_id
        archivos[archivo_id] = {
            "nombre": archivo.file_name,
            "fecha_subida": datetime.now(),
            "cupones": []
        }
        await update.message.reply_text(f"✅ Archivo '{archivo.file_name}' subido correctamente.")
    else:
        await update.message.reply_text("❌ Por favor, envía un archivo válido.")

# Generar cupones (solo admin)
async def generar_cupones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("⚙️ Uso: /generar_cupones <cantidad>")
        return

    cantidad = int(context.args[0])
    if not archivos:
        await update.message.reply_text("📂❌ No hay archivos disponibles para generar cupones.")
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

    await update.message.reply_text(f"🎉 {cantidad} cupones generados para el archivo '{archivos[ultimo_archivo_id]['nombre']}'.")

# Redimir cupón
async def redimir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("🎟️ Uso: /redimir <código>")
        return

    codigo = context.args[0]
    if codigo not in cupones:
        await update.message.reply_text("❌ El código ingresado no es válido.")
        return

    if cupones[codigo]["estado"] == "Redimido":
        await update.message.reply_text("🔁 Este cupón ya ha sido redimido.")
        return

    cupones[codigo]["estado"] = "Redimido"
    cupones[codigo]["usuario_redimido"] = update.message.from_user.id
    archivo_id = cupones[codigo]["archivo_id"]

    if update.message.from_user.id not in usuarios:
        usuarios[update.message.from_user.id] = {"archivos_redimidos": []}
    usuarios[update.message.from_user.id]["archivos_redimidos"].append(archivo_id)

    await update.message.reply_text(f"✅ Cupón redimido. 📂 Ahora tienes acceso al archivo '{archivos[archivo_id]['nombre']}'.")

# Configuración del bot
async def main():
    # Reemplaza 'YOUR_TOKEN_HERE' con el token de tu bot
    application = Application.builder().token('7987679597:AAHK4k-8kzUmDBfC9_R1cVroDqXEDqz6sB4').build()

    # Inicializar la aplicación
    await application.initialize()

    # Registrar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subir_archivo", subir_archivo))
    application.add_handler(CommandHandler("generar_cupones", generar_cupones))
    application.add_handler(CommandHandler("redimir", redimir))

    # Iniciar el bot
    print("Bot iniciado. Presiona Ctrl+C para detenerlo.")
    await application.start()
    await application.updater.start_polling()
    await application.idle()  # Mantener el bot encendido

# Ejecutar el bot en Google Colab
if __name__ == "__main__":
    nest_asyncio.apply()  # Permitir múltiples bucles de eventos
    asyncio.run(main())
