import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime


# Ruta base del directorio donde está el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Función para cargar frases desde el archivo frases
def load_phrases():
    try:
        with open(os.path.join(BASE_DIR, "frases.txt"), "r", encoding="utf-8") as file:  # Ruta absoluta para 'frases'
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'frases' en {os.path.join(BASE_DIR, 'frases')}.")
        return []

# Función para cargar el application_id desde el archivo id
def load_application_id():
    try:
        with open(os.path.join(BASE_DIR, "id.txt"), "r", encoding="utf-8") as file:  # Ruta absoluta para 'id'
            return int(file.read().strip())
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'id' en {os.path.join(BASE_DIR, 'id')}.")
        return None
    except ValueError:
        print(f"Error: El archivo 'id' en {os.path.join(BASE_DIR, 'id')} no contiene un ID válido.")
        return None

# Cargar frases y application_id
messages = load_phrases()
application_id = load_application_id()

if not messages or not application_id:
    print("No se pudo iniciar el bot debido a errores en los archivos de configuración.")
    exit(1)  # Salir del programa si hay errores

# Configuración inicial del bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Clase personalizada del bot
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=application_id  # Application ID cargado desde id
        )
        self.synced = False  # Para evitar sincronización repetida
        self.running = True  # Estado del bot
        self.messages = []  # Lista de mensajes mezclados
        self.message_index = 0  # Índice actual de mensaje

    def shuffle_messages(self):
        """Mezclar aleatoriamente los mensajes y reiniciar el índice"""
        self.messages = messages.copy()
        random.shuffle(self.messages)
        self.message_index = 0

bot = MyBot()

# Comando /hola
@bot.tree.command(name="hola", description="Komi está penosa")
async def hola(interaction: discord.Interaction):
    """Responder al comando /hola"""
    await interaction.response.send_message("Contigo es 1 amigo más. Todas las opiniones vertidas por este bot son de exclusiva responsabilidad del bot y no reflejan el pensamiento de los miembros del grupo. Cualquier comentario racista/homofobico/odio/terraplanista no es con la intención de atacar, si se siente ofendido debe reevaluar su manera de pensar.")

# Función para enviar mensajes aleatorios automáticamente
async def send_random_messages():
    """Enviar mensajes aleatorios cada 23 minutos dentro del horario definido"""
    bot.shuffle_messages()  # Mezclar los mensajes antes de empezar
    while True:
        current_time = datetime.now().time()
        if datetime.strptime("05:00", "%H:%M").time() <= current_time <= datetime.strptime("23:00", "%H:%M").time():
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        # Obtener el siguiente mensaje
                        if bot.message_index >= len(bot.messages):
                            bot.shuffle_messages()  # Volver a mezclar si se terminaron los mensajes
                        message = bot.messages[bot.message_index]
                        bot.message_index += 1  # Avanzar al siguiente mensaje
                        await channel.send(message)

                        # Log en la consola
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mensaje enviado: '{message}' en el servidor '{guild.name}' en el canal '{channel.name}'")

                        break  # Enviar a un solo canal por servidor
        await asyncio.sleep(23 * 60)  # Esperar 23 minutos

# Evento al estar listo el bot
@bot.event
async def on_ready():
    print(f"Komi conectada como {bot.user}")
    asyncio.create_task(send_random_messages())  # Iniciar el envío de mensajes aleatorios automáticamente

# Iniciar el bot
if __name__ == "__main__":
    token = input("Ingresa el token del bot: ").strip()
    bot.run(token)
