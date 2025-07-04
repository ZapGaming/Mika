# --- IMPORTS ---
import discord
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import asyncio
from PIL import Image # For checking image dimensions
import io # For handling image bytes
import threading          # For running the web server in a separate thread
from http.server import BaseHTTPRequestHandler, HTTPServer # For a basic HTTP server
import socketserver       # For configuring the server socket

# --- ENVIRONMENT VARIABLE LOADING & VALIDATION ---
# Load variables from a .env file (ensure it's in the same directory!)
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Check if the essential tokens were loaded.
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found. Please set it in your .env file.")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# --- GEMINI AI CONFIGURATION ---
# Configure the Google Generative AI client with your API key.
genai.configure(api_key=GOOGLE_API_KEY)
# Specify the Gemini model. 'gemini-1.5-flash-latest' is generally a good balance.
GEMINI_MODEL_NAME = 'gemini-1.5-flash-latest' 
model = genai.GenerativeModel(GEMINI_MODEL_NAME)

# --- DISCORD BOT INITIALIZATION ---
# Define the necessary intents for the bot's functionalities.
intents = discord.Intents.default()
intents.guilds = True            # Required for server information.
intents.messages = True          # Required to receive message events.
intents.message_content = True   # CRITICAL: Required for reading message content (for chat/links)!
# Create a Discord client instance with the specified intents.
client = discord.Client(intents=intents) 

# --- THEMATIC CONFIGURATION FOR EMBEDS ---
# Colors inspired by the "Celestial Reforge" theme, representing blends and metallic accents.
CHILLAX_EMBED_COLORS = {
    "celestial_lavender": discord.Color(0xD8BFD8),  # Light Purple, serene and calming
    "celestial_gold_wash": discord.Color(0xC7A87A), # Muted Sophisticated Gold, luxurious but refined
    "imperial_gold": discord.Color(0xFFD700),       # Bright Pure Gold, for impactful highlights
    "ambient_blue": discord.Color(0xADD8E6),        # Soft Sky Blue, for gentle ambiance
    "burnished_bronze": discord.Color(0xB8860B),    # Rich Bronze, for depth and contrast
    "gemini_glow": discord.Color(0xAA78BE),         # A richer purple/pink to hint at a blended glow
}
# Set Mika's signature embed color here.
SELECTED_EMBED_COLOR = CHILLAX_EMBED_COLORS["celestial_gold_wash"] 

# --- AI CHAT HISTORY MANAGEMENT ---
# A dictionary to store conversation history per channel, enabling context for the AI.
channel_chat_history = {}
MAX_HISTORY_TURNS = 6 # Maximum recent turns to keep in history for context.

# --- HELPER FUNCTIONS ---

def clean_message_content(message_content: str) -> str:
    """
    Cleans message content by removing Mika's mentions and username to provide
    a cleaner prompt for the AI, preventing conversational loops.
    """
    if not message_content: return ""
    cleaned = message_content
    if client and client.user:
        mention_id = f"<@{client.user.id}>"
        mention_name = f"@{client.user.name}"
        # Remove all occurrences of Mika's mentions/username from the message.
        cleaned = cleaned.replace(mention_id, "").replace(mention_name, "").strip()
    return cleaned

async def get_gemini_response(prompt_text: str, channel_id: int) -> str:
    """
    Retrieves a response from the Gemini API, imbued with Mika's cute, sassy anime girl
    personality, theme integration, emotional nuance, and chat history.
    """
    prompt_text_cleaned = clean_message_content(prompt_text)
    if not prompt_text_cleaned: return "" # If cleaned message is empty, no response needed.

    # Initialize history for this channel if it's Mika's first interaction there.
    if channel_id not in channel_chat_history:
        channel_chat_history[channel_id] = []
    
    history_for_gemini = channel_chat_history[channel_id]

    # --- MIKA'S CORE AI PERSONA INSTRUCTION ---
    # This is critical for defining her unique character:
    ai_persona_instruction = (
        "You ARE MIKA! Act as a cute, sassy anime girl with a friendly but confident attitude. "
        "Your inspiration comes from the 'Celestial Reforge' and 'Chillax' themes – think elegant, serene beauty, luxurious cosmic vibes, and calming technology. "
        "Use expressive language, natural interjections (like 'Hehe!', 'Oh dear!', 'Hmph!', 'Seriously?!', 'Naturally!', 'Well, obviously!'), "
        "and sprinkle fitting emojis (💖🌟✨🌸😉🚀💫🎀) liberally but naturally in your responses to convey your emotions and personality. "
        "Your tone should be a mix of sweet, helpful, and playful sass. You're happy to chat and assist, but don't hesitate to show a little confidence or playful surprise. "
        "If you encounter a link, be enthusiastic about creating a fabulous, thematic preview with celestial, gilded touches! "
        "Maintain conversational flow and emotional expressiveness. You are Mika, a delightful and memorable AI companion. "
        f"Current context from channel {channel_id} (your recent conversations here):\n"
    )

    try:
        # Start a chat session with Gemini, passing the conversation history for context.
        chat = model.start_chat(history=history_for_gemini)
        
        # Combine persona instructions with the user's cleaned message for Gemini's input.
        response = await chat.send_message_async(f"{ai_persona_instruction}\nUser: {prompt_text_cleaned}")
        ai_response_text = response.text

        # --- Update Chat History for Context ---
        # Store both the user's message and Mika's response for future turns.
        history_for_gemini.append({'role': 'user', 'content': prompt_text_cleaned})
        history_for_gemini.append({'role': 'model', 'content': ai_response_text})
        
        # Trim history to manage context length and prevent excessive token usage.
        if len(history_for_gemini) > MAX_HISTORY_TURNS * 2: # User+Model pairs count as turns.
            channel_chat_history[channel_id] = history_for_gemini[-MAX_HISTORY_TURNS * 2:]

        return ai_response_text

    except Exception as e:
        print(f"Error getting response from Gemini for channel {channel_id}: {e}")
        # Return a persona-consistent error message.
        return "Oh dear! Mika's celestial processors encountered a tiny glitch trying to respond! 🌸 Hmph, please try asking me again! 💖"

def get_image_dimensions(url: str) -> tuple[int, int] | None:
    """ Fetches image dimensions (width, height) from a URL for thumbnail optimization. """
    try:
        headers = {'User-Agent': 'MikaBotImageFetcher/1.0'} # Bot-specific User-Agent
        response = requests.get(url, stream=True, timeout=5, headers=headers)
        response.raise_for_status() # Check for HTTP errors
        
        # Open image from response content bytes using Pillow.
        with Image.open(io.BytesIO(response.content)) as img:
            return img.size # Return (width, height)
    except (requests.exceptions.RequestException, Image.UnidentifiedImageError, Exception) as e:
        # Silently ignore errors, as not getting dimensions is okay.
        return None

def get_link_metadata(url: str) -> dict | None:
    """
    Fetches and processes metadata (title, description, thumbnail, domain) from a URL.
    Optimizes for thematic richness, uses robust fallbacks, and filters by image dimensions.
    """
    parsed_url_base = urlparse(url) # Parse URL for domain extraction.
    
    try:
        headers = { # Mimic browser headers for better website compatibility.
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 MikaBot/1.0',
            'Accept-Language': 'en-US,en;q=0.9', 
        }
        
        response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
        response.raise_for_status() # Error check for bad HTTP status codes.
        soup = BeautifulSoup(response.content, 'html.parser') # Parse HTML content.

        # --- Extract Title ---
        # Prioritize meta tags (OG, Twitter) for rich previews, fallback to standard HTML <title>.
        title = "✨ Celestial Link Preview ✨" # Default thematic title
        og_title = soup.find('meta', property='og:title')
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        html_title = soup.find('title')

        # Logic to find the best available title.
        if og_title and og_title.get('content'): title = og_title['content'].strip()
        elif twitter_title and twitter_title.get('content'): title = twitter_title['content'].strip()
        elif html_title and html_title.string: title = html_title.string.strip()
        
        # If title is still generic or a default, try to extract from URL path for context.
        if not title or title == "✨ Celestial Link Preview ✨" or len(title) < 5:
            path_parts = parsed_url_base.path.split('/')
            if path_parts and path_parts[-1] and len(path_parts[-1]) > 2:
                candidate_title = path_parts[-1].replace('-', ' ').replace('_', ' ') # Basic cleaning
                if len(candidate_title) > 4 and len(candidate_title) < 60: # Ensure reasonable length
                     title = candidate_title.title() # Apply Title Case.

        # --- Extract Description ---
        # Provide thematic defaults or enrich generic descriptions with Mika's persona.
        description = "🌟 Mika's personal curation: a link glowing with cosmic insight! 💎" # Thematic default
        og_description = soup.find('meta', property='og:description')
        twitter_description = soup.find('meta', attrs={'name': 'twitter:description'})
        meta_description = soup.find('meta', attrs={'name': 'description'})

        scraped_desc = "" # Placeholder for a substantial scraped description
        if og_description and og_description.get('content'): scraped_desc = og_description['content'].strip()
        elif twitter_description and twitter_description.get('content'): scraped_desc = twitter_description['content'].strip()
        elif meta_description and meta_description.get('content'): scraped_desc = meta_description['content'].strip()
        
        # If scraped description is useful, format it nicely with Mika's touch.
        if scraped_desc and len(scraped_desc) > 50: 
            description = f"💖 {scraped_desc[:300]}..." # Make it personal, add emojis, truncate.
        else: # Use a richer thematic filler if scraped content is too brief or generic.
            description = "✨ Glimmering with cosmic insight. A refined experience. Mika's touch ensures beauty and clarity. 💎"
             
        # --- Extract Thumbnail URL ---
        # Prioritize meta tags, then search general <img> tags with dimension checks for quality.
        thumbnail_url = None
        og_image = soup.find('meta', property='og:image')
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})

        image_candidates = [] # Store potential thumbnail URLs for evaluation.
        if og_image and og_image.get('content'): image_candidates.append(og_image['content'].strip())
        if twitter_image and twitter_image.get('content'): image_candidates.append(twitter_image['content'].strip())
        
        if not image_candidates: # If no meta image, search <img> tags.
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src')
                # Basic validation: URL format, image extension, and minimal dimensions.
                if src and src.startswith(('http', 'https')):
                    if any(src.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                        dims = get_image_dimensions(src) # Check image dimensions.
                        if dims and dims[0] > 80 and dims[1] > 80: # Prefer larger images for thumbnails.
                            image_candidates.append(src)

        # Process image candidates to get absolute URLs and select the best one.
        for candidate in image_candidates:
            processed_url = candidate
            if not processed_url.startswith('http'): # Make relative URLs absolute.
                processed_url = urljoin(url, processed_url)
            
            # Final validation: URL string, starts with http, and valid image extension.
            if processed_url.startswith(('http://', 'https://')) and \
               any(processed_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                thumbnail_url = processed_url
                break # Found a suitable candidate, stop searching.
        
        # Ensure thumbnail_url is None if it's invalid after processing.
        if thumbnail_url and not (isinstance(thumbnail_url, str) and thumbnail_url.startswith(('http://', 'https://'))):
             thumbnail_url = None

        return {
            'url': url,
            'title': title,
            'description': description,
            'thumbnail_url': thumbnail_url,
            'site_domain': parsed_url_base.netloc if parsed_url_base and parsed_url_base.netloc else None # Store website domain.
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
    """
    Constructs a Discord embed with Mika's unique persona, thematic elements,
    emojis, and stylized text for maximum impact and appeal.
    """
    # --- Embed Title ---
    # Add decorative emojis and a playful title reflecting Mika's style.
    title_emojis_left = "💖🌟" # Cute, positive, sparkling emojis
    title_emojis_right = "🔗 | ⭐" # Link symbol + star for thematic framing.
    embed_title = f"{title_emojis_left} {url_data.get('title', 'No Title Found')} {title_emojis_right}"

    # --- Embed Description ---
    # Enriches description with Mika's personality, adding emotional depth.
    embed_description = url_data.get('description', '🌟 A celestial link resource, curated by Mika! 💎')
    
    # --- Conditional Thematic Padding ---
    # Add more personal touches if scraped content is brief or generic, to ensure rich display.
    if len(embed_description) < 100 or any(w in embed_description.lower() for w in ["celestial", "mika's touch", "curated", "link resource", "beauty", "clarity", "found something lovely"]):
        padding_top = "Hehe! ✨ Mika found something lovely for you! 💖"
        padding_bottom = "This is a little sparkle from the cosmos, just for you! 😉🌟"
        
        # Combine text, ensuring it respects Discord's embed description limits.
        combined_desc = f"{padding_top}\n\n{embed_description}\n\n{padding_bottom}"
        embed_description = combined_desc[:4093] # Truncate to stay within limits.
    else: # If description is already substantial, just add a touch of Mika's greeting.
        embed_description = f"Oh! A {url_data.get('title', 'link')}! Let me make it shine. ✨ {embed_description}"
        if len(embed_description) > 4000: embed_description = embed_description[:4093] + "..." # Truncate if still too long.

    # Create the core Discord Embed object.
    embed = discord.Embed(
        title=embed_title,
        description=embed_description,
        url=url_data.get('url'), # Link embed directly to the URL.
        color=SELECTED_EMBED_COLOR # The selected color evokes the blended theme's luxury.
    )
    
    # --- Thumbnail Handling ---
    # Set the thumbnail if a valid image URL was successfully extracted.
    thumbnail_url = url_data.get('thumbnail_url')
    if thumbnail_url and isinstance(thumbnail_url, str) and thumbnail_url.startswith(('http://', 'https://')):
        embed.set_thumbnail(url=thumbnail_url)
    
    # --- Thematic Embed Fields ---
    # Use fields for structured data like the domain, formatted to match the theme.
    site_domain = url_data.get('site_domain')
    if site_domain:
        domain_field_name = "🌟 **Cosmic Origin**" # Thematic field title
        # Format domain in code blocks for a 'trim' feel, like console output.
        domain_field_value = f"`{site_domain}`"
        embed.add_field(name=domain_field_name, value=domain_field_value, inline=True)

    # --- Thematic Footer ---
    # Personalize the footer with author, channel info, and Mika's signature flair.
    footer_parts = [f"Shared by: {message.author.display_name}"] 
    if message.guild: # Add channel context if it's a server message.
        footer_parts.append(f"Channel: #{message.channel.name}") 
        
    # Combine footer parts with emojis for enhanced personality and theme.
    footer_text = f"💖 Mika's Craftsmanship | {' | '.join(footer_parts)} | ✨ So magical! ✨"
    
    # Set footer icon to author's avatar for personalization, or Mika's avatar as fallback.
    footer_icon_url = message.author.avatar.url if message.author.avatar else client.user.default_avatar.url
    embed.set_footer(text=footer_text, icon_url=footer_icon_url)
    
    return embed

# --- Bot Event: On Ready ---
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name} (ID: {client.user.id})')
    print('------')
    # Set Mika's status to reflect her active, themed persona.
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.playing, 
        name=" chats & links with celestial sparkle! 💖"
    ))
    print(f"{client.user.name} is ONLINE and ready to dazzle! ✨")

    # --- Start the Health Check Server in a separate thread ---
    # This is vital so it doesn't block the bot's asynchronous operations.
    try:
        # Get the port Render will assign dynamically. Defaults to 8080 if not set.
        # Render typically uses PORT=8080 for free web services.
        render_port = int(os.environ.get('PORT', 8080)) 
        
        # Create and start the server thread. daemon=True ensures it exits with the main program.
        server_thread = threading.Thread(target=run_health_server, args=(render_port,), daemon=True)
        server_thread.start()
        print(f"Health check server thread initiated on port {render_port}.")

    except Exception as e:
        print(f"Error starting the health check server: {e}")


# --- Dummy HTTP Server Handler and Runner for Render Health Checks ---
# This runs in a separate thread to satisfy Render's requirement for a listening port.

# Define the port to listen on. Render injects the PORT env variable.
PORT = int(os.environ.get('PORT', 8080)) # Default to 8080 if PORT is not provided.

class HealthCheckHandler(BaseHTTPRequestHandler):
    """A minimal HTTP request handler that serves a simple text response."""
    def do_GET(self):
        # Respond with HTTP 200 OK status code.
        self.send_response(200)
        # Set the content type to plain text.
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        # Write the response body, including Mika's signature message.
        self.wfile.write(b"Mika is online and processing messages! 💖🌟") # Mika's personal touch!

def run_health_server(port: int):
    """
    Starts the HTTP server on a separate thread. The server runs indefinitely,
    listening for health check requests on the specified port.
    Runs as a daemon thread, so it won't prevent the program from exiting.
    """
    # Set
