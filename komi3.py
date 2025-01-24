import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime
import threading  # esto es nuevo, para escuchar la consola en un hilo separado con el comando !

# Ruta principal del directorio, donde está todo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cargar frases desde el archivo frases
def load_phrases():
    try:
        with open(os.path.join(BASE_DIR, "frases.txt"), "r", encoding="utf-8") as file:  # Ruta absoluta para 'frases'
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'frases' en {os.path.join(BASE_DIR, 'frases')}.")
        exit(1)

# Cargar application_id desde el archivo id
def load_application_id():
    try:
        with open(os.path.join(BASE_DIR, "id.txt"), "r", encoding="utf-8") as file:
            return int(file.read().strip())
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'id' en {os.path.join(BASE_DIR, 'id')}.")
        exit(1)
    except ValueError:
        print(f"Error: El archivo 'id' en {os.path.join(BASE_DIR, 'id')} no contiene un ID válido.")
        exit(1)

# Cargar configuraciones desde el archivo tiempo
def load_time_config():
    try:
        with open(os.path.join(BASE_DIR, "tiempo.txt"), "r", encoding="utf-8") as file:
            lines = file.readlines()
            if len(lines) != 3:
                raise ValueError("El archivo 'tiempo.txt' debe contener exactamente 3 líneas.")

            # Leer y procesar cada línea
            interval_line = lines[0].strip()
            start_time_line = lines[1].strip()
            end_time_line = lines[2].strip()

            # Extraer valores de cada línea
            interval = int(interval_line.replace("Intervalo:", "").strip())
            start_time = datetime.strptime(start_time_line.replace("Inicio:", "").strip(), "%H:%M").time()
            end_time = datetime.strptime(end_time_line.replace("Termino:", "").strip(), "%H:%M").time()

            # Validar valores
            if interval <= 0:
                raise ValueError("El intervalo debe ser mayor a 0.")
            if start_time >= end_time:
                raise ValueError("La hora de inicio debe ser menor que la hora de término.")

            return interval, start_time, end_time

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'tiempo.txt' en {os.path.join(BASE_DIR, 'tiempo.txt')}.")
        exit(1)
    except ValueError as e:
        print(f"Error en 'tiempo.txt': {e}")
        exit(1)

# Cargar configuraciones iniciales
application_id = load_application_id()
interval, start_time, end_time = load_time_config()

# Configuración inicial
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Clase personalizada
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=application_id  # ID cargado desde id
        )
        self.synced = False
        self.running = True
        self.messages_sent = set()  # Frases ya enviadas

    def get_next_message(self):
        """Cargar frases y seleccionar la siguiente sin repetir"""
        phrases = load_phrases()
        # Encontrar las frases no enviadas
        remaining_phrases = [phrase for phrase in phrases if phrase not in self.messages_sent]
        if not remaining_phrases:  # Si ya se enviaron todas, reiniciar
            self.messages_sent.clear()
            remaining_phrases = phrases.copy()
            random.shuffle(remaining_phrases)  # Mezclar para evitar orden fijo
        # Seleccionar la siguiente frase
        next_message = remaining_phrases.pop(0)
        self.messages_sent.add(next_message)
        return next_message

bot = MyBot()

# Comando /hola es un disclaimer
@bot.tree.command(name="hola", description="Esto es solo un disclaimer")
async def hola(interaction: discord.Interaction):
    """Responder al comando /hola"""
    await interaction.response.send_message("Contigo es 1 amigo más. Todas las opiniones vertidas por este bot son de exclusiva responsabilidad del bot y no reflejan el pensamiento de los miembros del grupo. Cualquier comentario racista/homofobico/odio/terraplanista no es con la intención de atacar, si se siente ofendido debe reevaluar su manera de pensar.")

# Función para enviar mensajes aleatorios automáticamente
async def send_random_messages():
    """Enviar mensajes aleatorios según el intervalo y horario definidos en tiempo.txt"""
    while True:
        # Recargar configuración antes de cada mensaje
        interval, start_time, end_time = load_time_config()

        current_time = datetime.now().time()
        if start_time <= current_time <= end_time:
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        message = bot.get_next_message()  # Obtener el siguiente mensaje
                        await channel.send(message)
                        # Log en la consola
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mensaje enviado: '{message}' en el servidor '{guild.name}' en el canal '{channel.name}'")
                        break  # Enviar a un solo canal por servidor
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fuera del horario de envío ({start_time} - {end_time}).")

        # Esperar el intervalo definido
        await asyncio.sleep(interval * 60)

# Hilo para escuchar la consola y enviar mensajes personalizados
def console_listener():
    while True:
        user_input = input()  # Leer entrada del usuario
        if user_input.startswith("!"):  # Detectar mensajes con prefijo '!'
            message = user_input[1:]  # Obtener el mensaje después de '!'
            # Enviar la tarea al event loop principal del bot
            asyncio.run_coroutine_threadsafe(send_custom_message(message), bot.loop)

# Función para enviar mensajes personalizados
async def send_custom_message(message):
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(message)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mensaje personalizado enviado: '{message}' en el servidor '{guild.name}' en el canal '{channel.name}'")
                return  # Solo enviar a un canal por servidor

# Evento al estar listo el bot
@bot.event
async def on_ready():
    print(f"Komi conectada como {bot.user}")  # Log
    asyncio.create_task(send_random_messages())  # Iniciar el envío de mensajes aleatorios automáticamente
    threading.Thread(target=console_listener, daemon=True).start()  # Iniciar el hilo para la consola

# Iniciar el bot
if __name__ == "__main__":
    token = input("Ingresa el token del bot: ").strip()
    bot.run(token)
