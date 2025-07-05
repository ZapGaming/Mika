# --- IMPORTS ---
# Standard libraries
import discord
# THIS LINE IS CRUCIAL FOR SLASH COMMANDS! ENSURE IT IS PRESENT.
from discord.ext import commands 
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import asyncio
from PIL import Image 
import io 
import threading          
from http.server import BaseHTTPRequestHandler, HTTPServer 
import socketserver       
import json               

# --- ENVIRONMENT VARIABLE LOADING & VALIDATION ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found. Please set it in your .env file.")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# --- GEMINI AI CONFIGURATION ---
genai.configure(api_key=GOOGLE_API_KEY)
GEMINI_MODEL_NAME = 'gemini-2.5-flash-lite-preview-06-17' 
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

# --- DISCORD BOT INITIALIZATION ---
intents = discord.Intents.default()
intents.guilds = True            
intents.messages = True          
intents.message_content = True   # REQUIRED for reading message content.

# --- USING commands.Bot for Slash Commands ---
# IMPORTANT: THIS IS WHERE 'commands' IS USED.
# If this line is present AND the import at the top is correct, NameError should be gone.
bot = commands.Bot(command_prefix='!', intents=intents)

# --- THEMATIC CONFIGURATION FOR EMBEDS ---
CHILLAX_EMBED_COLORS = {
    "celestial_lavender": discord.Color(0xD8BFD8),  
    "celestial_gold_wash": discord.Color(0xC7A87A), # Mika's chosen signature color
    "imperial_gold": discord.Color(0xFFD700),       
    "ambient_blue": discord.Color(0xADD8E6),        
    "burnished_bronze": discord.Color(0xB8860B),    
    "gemini_glow": discord.Color(0xAA78BE),         
}
SELECTED_EMBED_COLOR = CHILLAX_EMBED_COLORS["celestial_gold_wash"] 

# --- AI CHAT HISTORY MANAGEMENT ---
channel_chat_history = {} 
MAX_HISTORY_TURNS = 6   
HISTORY_FILE = "chat_history.json" 

# --- HELPER FUNCTIONS (Copied from previous version, ALL SHOULD BE PRESENT) ---

def clean_message_content(message_content: str) -> str:
    if not message_content: return ""
    cleaned = message_content
    if bot and bot.user: # Check using 'bot' as we are using commands.Bot
        mention_id = f"<@{bot.user.id}>"
        mention_name = f"@{bot.user.name}"
        cleaned = cleaned.replace(mention_id, "").replace(mention_name, "").strip()
    return cleaned

async def get_gemini_response(prompt_text: str, channel_id: int) -> str:
    prompt_text_cleaned = clean_message_content(prompt_text)
    if not prompt_text_cleaned: return "" 

    if channel_id not in channel_chat_history:
        channel_chat_history[channel_id] = []
    history_for_gemini = channel_chat_history[channel_id]

    ai_persona_instruction = (
        "You ARE MIKA! Act as a cute, sassy anime girl with a friendly but confident attitude. "
        "Your inspiration comes from the 'Celestial Reforge' and 'Chillax' themes – think elegant, serene beauty, luxurious cosmic vibes, and calming technology. "
        "Use expressive language, natural interjections (like 'Hehe!', 'Oh dear!', 'Hmph!', 'Seriously?!', 'Naturally!', 'Well, obviously!'), "
        "and sprinkle fitting emojis (💖🌟✨🌸😉🚀💫🎀) liberally but naturally in your responses to convey your emotions and personality. "
        "Your tone should be pleasant, quick, and helpful, balancing sweet charm with playful sass. "
        "You're happy to chat and assist, but don't hesitate to show a little confidence or playful surprise. "
        "If you encounter a link, be enthusiastic about creating a fabulous, thematic preview with celestial, gilded touches! "
        "Proactively engage if a conversation feels natural for you to join, even without a direct mention, but don't interrupt or spam. "
        "Maintain conversational flow and emotional expressiveness. You are Mika, a delightful and memorable AI companion. "
        f"Current context from channel {channel_id} (your recent conversations here):\n"
    )

    try:
        chat = model.start_chat(history=history_for_gemini)
        response = await chat.send_message_async(f"{ai_persona_instruction}\nUser: {prompt_text_cleaned}")
        ai_response_text = response.text

        history_for_gemini.append({'role': 'user', 'content': prompt_text_cleaned})
        history_for_gemini.append({'role': 'model', 'content': ai_response_text})
        
        if len(history_for_gemini) > MAX_HISTORY_TURNS * 2: 
            channel_chat_history[channel_id] = history_for_gemini[-MAX_HISTORY_TURNS * 2:]

        asyncio.create_task(save_chat_history(channel_chat_history))
        
        return ai_response_text

    except Exception as e:
        print(f"Error getting response from Gemini for channel {channel_id}: {e}")
        return "Oh dear! Mika's celestial processors encountered a tiny glitch trying to respond! 🌸 Hmph, please try asking me again! 💖"

def get_image_dimensions(url: str) -> tuple[int, int] | None:
    try:
        headers = {'User-Agent': 'MikaBotImageFetcher/1.0'} 
        response = requests.get(url, stream=True, timeout=5, headers=headers)
        response.raise_for_status() 
        with Image.open(io.BytesIO(response.content)) as img:
            return img.size 
    except (requests.exceptions.RequestException, Image.UnidentifiedImageError, Exception) as e:
        return None

def get_link_metadata(url: str) -> dict | None:
    parsed_url_base = urlparse(url) 
    try:
        headers = { 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 MikaBot/1.0',
            'Accept-Language': 'en-US,en;q=0.9', 
        }
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        response.raise_for_status() 
        soup = BeautifulSoup(response.content, 'html.parser')

        title = "✨ Celestial Link Preview ✨" 
        og_title = soup.find('meta', property='og:title')
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        html_title = soup.find('title')

        if og_title and og_title.get('content'): title = og_title['content'].strip()
        elif twitter_title and twitter_title.get('content'): title = twitter_title['content'].strip()
        elif html_title and html_title.string: title = html_title.string.strip()
        
        if not title or title == "✨ Celestial Link Preview ✨" or len(title) < 5:
            path_parts = parsed_url_base.path.split('/')
            if path_parts and path_parts[-1] and len(path_parts[-1]) > 2:
                candidate_title = path_parts[-1].replace('-', ' ').replace('_', ' ')
                if len(candidate_title) > 4 and len(candidate_title) < 60:
                     title = candidate_title.title()

        description = "🌟 Mika's personal curation: a link glowing with cosmic insight! 💎" 
        og_description = soup.find('meta', property='og:description')
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        meta_description = soup.find('meta', attrs={'name': 'description'})

        scraped_desc = "" 
        if og_description and og_description.get('content'): scraped_desc = og_description['content'].strip()
        elif twitter_description and twitter_description.get('content'): scraped_desc = twitter_description['content'].strip()
        elif meta_description and meta_description.get('content'): scraped_desc = meta_description['content'].strip()
        
        if scraped_desc and len(scraped_desc) > 50: 
            description = f"💖 {scraped_desc[:300]}..." 
        else: 
            description = "✨ Glimmering with cosmic insight. A refined experience. Mika's touch ensures beauty and clarity. 💎"
             
        thumbnail_url = None
        og_image = soup.find('meta', property='og:image')
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})

        image_candidates = [] 
        if og_image and og_image.get('content'): image_candidates.append(og_image['content'].strip())
        if twitter_image and twitter_image.get('content'): image_candidates.append(twitter_image['content'].strip())
        
        if not image_candidates: 
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src')
                if src and src.startswith(('http', 'https')):
                    if any(src.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                        dims = get_image_dimensions(src)
                        if dims and dims[0] > 80 and dims[1] > 80: 
                            image_candidates.append(src)

        for candidate in image_candidates:
            processed_url = candidate
            if not processed_url.startswith('http'): 
                processed_url = urljoin(url, processed_url)
            
            if processed_url.startswith(('http://', 'https://')) and \
               any(processed_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                thumbnail_url = processed_url
                break
        
        if thumbnail_url and not (isinstance(thumbnail_url, str) and thumbnail_url.startswith(('http://', 'https://'))):
             thumbnail_url = None

        return {
            'url': url,
            'title': title,
            'description': description,
            'thumbnail_url': thumbnail_url,
            'site_domain': parsed_url_base.netloc if parsed_url_base and parsed_url_base.netloc else None 
        }

    except requests.exceptions.Timeout:
        print(f"Timeout fetching metadata for {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"HTTP error fetching metadata for {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing metadata for {url}: {e}")
        return None

async def create_themed_embed(url_data: dict, message: discord.Message) -> discord.Embed:
    """ Constructs a Discord embed with Mika's persona, theme, emojis, and stylized text. """
    title_emojis_left = "💖🌟" 
    title_emojis_right = "🔗 | ⭐"
    embed_title = f"{title_emojis_left} {url_data.get('title', 'No Title Found')} {title_emojis_right}"

    embed_description = url_data.get('description', '🌟 A celestial link resource, curated by Mika! 💎')
    
    if len(embed_description) < 100 or any(w in embed_description.lower() for w in ["celestial", "mika's touch", "curated", "link resource", "beauty", "clarity", "found something lovely"]):
        padding_top = "Hehe! ✨ Mika found something lovely for you! 💖"
        padding_bottom = "This is a little sparkle from the cosmos, just for you! 😉🌟"
        combined_desc = f"{padding_top}\n\n{embed_description}\n\n{padding_bottom}"
        embed_description = combined_desc[:4093]
    else: 
        embed_description = f"Oh! A {url_data.get('title', 'link')}! Let me make it shine. ✨ {embed_description}"
        if len(embed_description) > 4000: embed_description = embed_description[:4093] + "..."

    embed = discord.Embed(
        title=embed_title,
        description=embed_description,
        url=url_data.get('url'), 
        color=SELECTED_EMBED_COLOR 
    )
    
    thumbnail_url = url_data.get('thumbnail_url')
    if thumbnail_url and isinstance(thumbnail_url, str) and thumbnail_url.startswith(('http://', 'https://')):
        embed.set_thumbnail(url=thumbnail_url)
    
    site_domain = url_data.get('site_domain')
    if site_domain:
        domain_field_name = "🌟 **Cosmic Origin**" 
        domain_field_value = f"`{site_domain}`"
        embed.add_field(name=domain_field_name, value=domain_field_value, inline=True)

    footer_parts = [f"Shared by: {message.author.display_name}"] 
    if message.guild: 
        footer_parts.append(f"Channel: #{message.channel.name}") 
        
    footer_text = f"💖 Mika's Craftsmanship | {' | '.join(footer_parts)} | ✨ So magical! ✨"
    
    footer_icon_url = message.author.avatar.url if message.author.avatar else bot.user.default_avatar.url 
    embed.set_footer(text=footer_text, icon_url=footer_icon_url)
    
    return embed

# --- PERSISTENT CHAT HISTORY FUNCTIONS ---
def load_chat_history():
    """Loads chat history from JSON, handling errors and ensuring dictionary format."""
    global channel_chat_history
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            if isinstance(loaded_data, dict):
                channel_chat_history = loaded_data
                print(f"Successfully loaded chat history from {HISTORY_FILE}")
            else:
                print(f"Error: Loaded chat history from {HISTORY_FILE} is not a dictionary. Initializing empty.")
                channel_chat_history = {}
    except FileNotFoundError:
        print(f"Chat history file not found: {HISTORY_FILE}. Initializing empty.")
        channel_chat_history = {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {HISTORY_FILE}. File might be corrupted. Initializing empty.")
        channel_chat_history = {}
    except Exception as e:
        print(f"An unexpected error occurred loading chat history: {e}. Initializing empty.")
        channel_chat_history = {}

async def save_chat_history(history_data: dict):
    """ Asynchronously saves current chat history to JSON, avoiding blocking I/O. """
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _save_chat_history_sync, history_data)
    except Exception as e:
        print(f"Error saving chat history: {e}")

def _save_chat_history_sync(history_data: dict):
    """ Synchronous helper to save chat history to a JSON file. """
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Sync error saving chat history: {e}")

# --- BOT EVENT: ON READY ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    
    load_chat_history() 

    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.playing, 
        name=" chats & links with celestial sparkle! 💖"
    ))
    print(f"{bot.user.name} is ONLINE and ready to dazzle! ✨")

    # --- START THE HEALTH CHECK SERVER IN A SEPARATE THREAD ---
    try:
        render_port = int(os.environ.get('PORT', 8080)) 
        server_thread = threading.Thread(target=run_health_server, args=(render_port,), daemon=True)
        server_thread.start()
        print(f"Health check server thread initiated on port {render_port}.")
    except Exception as e:
        print(f"Error starting the health check server: {e}")


# --- DUMMY HTTP SERVER HANDLER AND RUNNER FOR RENDER HEALTH CHECKS ---
PORT = int(os.environ.get('PORT', 8080)) 

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for Render health checks."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        # CORRECTED LINE: Removed emojis from byte literal for ASCII compatibility.
        self.wfile.write(b"Mika is online and processing messages!") 

def run_health_server(port: int):
    """ Starts the HTTP server on a separate thread, running indefinitely. """
    server_address = ('0.0.0.0', port) 
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"Health check server is running on port {port}...")
    httpd.serve_forever()

# --- BOT EVENT: ON MESSAGE ---
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user: # Ignore messages from Mika herself.
        return

    # --- 1. PROCESS LINK PREVIEWS ---
    potential_links = []
    if message.content: 
        words = message.content.split() 
        for word in words:
            if word.startswith(('http://', 'https://')):
                try:
                    parsed_url = urlparse(word)
                    if parsed_url.scheme in ['http', 'https'] and parsed_url.netloc:
                        potential_links.append(word)
                except ValueError: continue 

    if potential_links:
        first_link_url = potential_links[0] 
        print(f"Detected link from {message.author.display_name}: {first_link_url}")
        
        metadata = get_link_metadata(first_link_url)
        
        if metadata: 
            themed_embed = await create_themed_embed(metadata, message)
            try:
                await message.channel.send(embed=themed_embed)
            except discord.Forbidden:
                print(f"Permission error: Mika cannot send embeds in {message.channel.name}.")
            except discord.HTTPException as e:
                print(f"HTTP error sending embed for {first_link_url}: {e}")
        else:
            print(f"Failed to fetch metadata for link: {first_link_url}.")
    
    # --- 2. PROCESS AI CHAT ---
    # Mika responds to DMs, mentions, OR when the prompt suggests proactive engagement (per AI instructions).
    # Important: she should NOT respond to messages starting with '/', as those are commands.
    if message.content.startswith('/'):
        return # Let the command handler manage messages starting with slash commands.
    
    # Triggers for AI chat: DM or Mention.
    is_mentioned = bot.user.mentioned_in(message)
    is_dm = message.guild is None 

    if is_mentioned or is_dm: 
        ai_prompt_content = message.content 
        if not ai_prompt_content: return 
            
        print(f"Received AI query from {message.author.display_name} in '{message.channel.name if message.guild else 'DM'}': '{ai_prompt_content}'")

        try:
            bot_response = await get_gemini_response(ai_prompt_content, message.channel.id)
            if bot_response:
                for i in range(0, len(bot_response), 2000):
                    await message.channel.send(bot_response[i:i+2000])
        except discord.Forbidden:
            print(f"Permission error: Mika cannot send messages in {message.channel.name}.")
        except discord.HTTPException as e:
            print(f"HTTP error sending AI response: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during AI response processing: {e}")

# --- SLASH COMMANDS DEFINITIONS ---
# These are registered with discord.ext.commands to be usable with '/'.

@bot.command(name='chat', help='Chat with Mika using the AI. Example: /chat Hello there!')
async def chat_command(ctx, *, user_input: str):
    """
    Triggers a chat interaction with Mika via a slash command.
    Takes all subsequent text as input.
    """
    print(f"Received /chat command from {ctx.author.display_name}: '{user_input}'")
    
    ai_response = await get_gemini_response(user_input, ctx.channel.id)
    
    if ai_response:
        # Split response if it exceeds Discord's character limit per message.
        for i in range(0, len(ai_response), 2000):
            await ctx.send(ai_response[i:i+2000])

@bot.command(name='embed', help='Creates a stylish link preview. Example: /embed <URL>')
async def embed_command(ctx, url: str):
    """
    Generates a themed link embed for a provided URL via a slash command.
    """
    print(f"Received /embed command from {ctx.author.display_name} with URL: {url}")
    
    # Basic validation to ensure the input is a URL.
    if not url.startswith('http://', 'https://'):
        await ctx.send("🌸 Oops! That doesn't look like a valid web link, darling. Please provide a URL starting with http:// or https://")
        await ctx.send("🌸 Oops! That doesn't look like a valid web link, darling. Please provide a URL starting with http:// or https://. 😉")
        return

    metadata = get_link_metadata(url)
    
    if metadata:
        themed_embed = await create_themed_embed(metadata, ctx.message) 
        try:
            await ctx.send(embed=themed_embed)
        except discord.Forbidden:
            await ctx.send(f"Mika doesn't have permission to send embeds here, hmph! 😞")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while trying to create that embed: {e}")
    else:
        await ctx.send("I couldn't fetch the details for that link, maybe it's a bit shy? 🌸 Let's try another one!")

# --- EVENT: ON COMMAND ERROR ---
@bot.event
async def on_command_error(ctx, error):
    """Handles errors that occur during command execution gracefully."""
    if isinstance(error, commands.CommandNotFound):
        pass # Ignore unknown commands silently.
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Oopsie! You missed a required part for that command. Try `/help {ctx.command}` for guidance. 💖")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("That argument format seems a bit off, darling. Please check `/help` for the correct usage! ✨")
    elif isinstance(error, commands.CommandInvokeError):
        print(f"Error executing command {ctx.command}: {error.original}")
        await ctx.send("Mika encountered a little trouble processing that command. Please try again! 🥺")
    else:
        print(f"Unhandled command error: {error}")
        await ctx.send("Hmm, something unexpected happened with that command. Let's try again! ✨")

# --- RUN THE BOT ---
if __name__ == "__main__": 
    try:
        # Load chat history BEFORE starting the bot client.
        load_chat_history() 
        
        # Run the bot using bot.run() as we're using commands.Bot.
        bot.run(DISCORD_TOKEN) 
    except discord.LoginFailure:
        print("ERROR: Login failed! Invalid Discord Token. Please check your .env file and ensure DISCORD_TOKEN is correctly set.")
    except Exception as e:
        print(f"An error occurred while running the bot: {e}")
