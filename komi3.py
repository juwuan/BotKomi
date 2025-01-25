import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime


# ruta principal del directorio, donde esta todo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# carga frases desde el archivo frases
def load_phrases():
    try:
        with open(os.path.join(BASE_DIR, "frases.txt"), "r", encoding="utf-8") as file:  # ruta absoluta para 'frases'
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'frases' en {os.path.join(BASE_DIR, 'frases')}.")
        return []

# cargar application_id desde el archivo id
def load_application_id():
    try:
        with open(os.path.join(BASE_DIR, "id.txt"), "r", encoding="utf-8") as file:  # ruta absoluta para 'id'
            return int(file.read().strip())
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'id' en {os.path.join(BASE_DIR, 'id')}.")
        return None
    except ValueError:
        print(f"Error: El archivo 'id' en {os.path.join(BASE_DIR, 'id')} no contiene un ID válido.")
        return None

# cargar los txt
messages = load_phrases()
application_id = load_application_id()

if not messages or not application_id:
    print("No se pudo iniciar el bot debido a errores en los archivos de configuración.")
    exit(1)  # no ejecuta el bot si hay errores

# configuración inicial
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents) # prefix antiguo, nostalgia

# clase personalizada
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=application_id  # ID cargado desde id
        )
        self.synced = False  # evitar sincronización repetida
        self.running = True  # estado
        self.messages = []  # lista de mensajes mezclados
        self.message_index = 0  # indice actual de mensaje

    def shuffle_messages(self):
        """mezclar aleatoriamente los mensajes y reiniciar el indice"""
        self.messages = messages.copy()
        random.shuffle(self.messages)
        self.message_index = 0

bot = MyBot()

# Comando /hola es un disclaimer
@bot.tree.command(name="hola", description="Esto es solo un disclaimer")
async def hola(interaction: discord.Interaction):
    """responder al comando /hola"""
    await interaction.response.send_message("Contigo es 1 amigo más. Todas las opiniones vertidas por este bot son de exclusiva responsabilidad del bot y no reflejan el pensamiento de los miembros del grupo. Cualquier comentario racista/homofobico/odio/terraplanista no es con la intención de atacar, si se siente ofendido debe reevaluar su manera de pensar.")

# función para enviar mensajes aleatorios automáticamente
async def send_random_messages():
    """enviar mensajes aleatorios cada 23 minutos dentro del horario definido"""
    bot.shuffle_messages()  # mezclar los mensajes antes de empezar porque si no salen en orden
    while True:
        current_time = datetime.now().time()
        if datetime.strptime("05:00", "%H:%M").time() <= current_time <= datetime.strptime("23:59", "%H:%M").time():
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        # obtener el siguiente mensaje
                        if bot.message_index >= len(bot.messages):
                            bot.shuffle_messages()  # volver a mezclar si se terminaron los mensajes
                        message = bot.messages[bot.message_index]
                        bot.message_index += 1  # avanzar al siguiente mensaje
                        await channel.send(message)

                        # log en la consola
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mensaje enviado: '{message}' en el servidor '{guild.name}' en el canal '{channel.name}'")

                        break  # enviar a un solo canal por servidor
        await asyncio.sleep(23 * 60)  # esperar 23 minutos

# evento al estar listo el bot
# flag para controlar la ejecución de la tarea
is_task_running = False  # variable global para verificar si la tarea ya se inició
@bot.event
async def on_ready():
    global is_task_running
    print(f"Komi conectada como {bot.user}") # log
    if not is_task_running:  # verificar si la tarea ya esta corriendo
        is_task_running = True
    asyncio.create_task(send_random_messages())  # iniciar el envío de mensajes aleatorios automáticamente

# Iniciar el bot
if __name__ == "__main__":
    token = input("Ingresa el token del bot: ").strip() # pide el token en la terminal
    bot.run(token)
