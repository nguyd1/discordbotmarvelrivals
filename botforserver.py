import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import urllib.parse
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from player_data import TOP_PLAYERS, PLAYER_EMOJIS

# Load environment variables
load_dotenv()

# Get configuration from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SELENIUM_WORKERS = int(os.getenv('SELENIUM_WORKERS', '2'))
SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', '2'))
DUMP_HTML = os.getenv('DUMP_HTML', 'False').lower() == 'true'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,  # Set level based on DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'),
              logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Set logger level based on DEBUG
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Rank icons mapping
RANK_ICONS = {
    "one above all": "https://mrivals.gg/assets/ranks/oneaboveall.webp",
    "eternity": "https://mrivals.gg/assets/ranks/eternity.webp",
    "celestial": "https://mrivals.gg/assets/ranks/celestial.webp",
    "grandmaster": "https://mrivals.gg/assets/ranks/grandmaster.webp",
    "master": "https://mrivals.gg/assets/ranks/master.webp",
    "diamond": "https://mrivals.gg/assets/ranks/diamond.webp",
    "platinum": "https://mrivals.gg/assets/ranks/platinum.webp",
    "gold": "https://mrivals.gg/assets/ranks/gold.webp",
    "silver": "https://mrivals.gg/assets/ranks/silver.webp",
    "bronze": "https://mrivals.gg/assets/ranks/bronze.webp"
}

# Add hero emoji mapping
HERO_EMOJIS = {
    "Adam Warlock": "✨",
    "Black Panther": "🐆",
    "Black Widow": "🕷️",
    "Captain America": "🛡️",
    "Cloak & Dagger": "👫",
    "Doctor Strange": "🧙",
    "Groot": "🌳",
    "Hawkeye": "🏹",
    "Hela": "💀",
    "Hulk": "💪",
    "Invisible Woman": "👻",
    "Iron Fist": "👊",
    "Iron Man": "🤖",
    "Johnny Storm": "🔥",
    "Jeff The Land Shark": "🦈",
    "Loki": "🦹",
    "Luna Snow": "❄️",
    "Magik": "⚔️",
    "Magneto": "🧲",
    "Mantis": "🦋",
    "Moon Knight": "🌙",
    "Namor": "🌊",
    "Peni Parker": "🕸️",
    "Psylocke": "💫",
    "The Punisher": "🔫",
    "Rocket Raccoon": "🦝",
    "Scarlet Witch": "🔮",
    "Spider-Man": "🕷️",
    "Squirrel Girl": "🐿️",
    "Star-Lord": "🚀",
    "Storm": "🌪️",
    "The Thing": "🗿",
    "Thor": "⚡",
    "Venom": "🕷️",
    "Winter Soldier": "❄️",
    "Wolverine": "🦮"
}

# Add rank order mapping with more granular values
RANK_ORDER = {
    "one above all": -2,  # Lower value for higher rank
    "eternity": -1,
    "celestial": 0,
    "grandmaster": 1,
    "diamond": 2,
    "platinum": 3,
    "gold": 4,
    "silver": 5,
    "bronze": 6,
    "unknown": 999  # Unknown ranks at the bottom
}

# Add rank emoji mapping
RANK_EMOJIS = {
    "one above all": "👑",
    "eternity": "🌟",
    "celestial": "⭐",
    "grandmaster": "👑",
    "diamond": "💎",
    "platinum": "🔮",
    "gold": "🏆",
    "silver": "🥈",
    "bronze": "🥉",
    "unknown": "❓"
}

# Create a thread pool for Selenium operations
selenium_pool = ThreadPoolExecutor(max_workers=SELENIUM_WORKERS)


def parse_rank(rank_str):
    """Parse rank string to get rank tier and number"""
    try:
        # Special handling for One Above All and Eternity
        if rank_str.lower() == "one above all":
            return "one above all", 0
        elif rank_str.lower() == "eternity":
            return "eternity", 0

        parts = rank_str.lower().split()
        if len(parts) >= 2:
            tier = parts[0]
            # Convert roman numerals to numbers
            number_str = parts[1].upper()
            number_map = {'I': 1, 'II': 2, 'III': 3}
            number = number_map.get(number_str, 999)
            return tier, number
    except:
        pass
    return "unknown", 999  # Return unknown with high number to sort at bottom


def get_player_data(driver, username):
    """Get player data using Selenium"""
    try:
        # Navigate to the player profile page
        profile_url = f'https://mrivals.gg/player/{username}'
        driver.get(profile_url)

        # Wait for the content to load with a shorter timeout
        wait = WebDriverWait(driver,
                             SELENIUM_TIMEOUT)  # Reduced from 3 to 2 seconds

        try:
            # Wait for the JSON-LD script tag directly
            script_elements = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "script[type='application/ld+json']")))

            # Find the player data script
            player_data = None
            for script in script_elements:
                try:
                    script_content = script.get_attribute("innerHTML")
                    if "mainEntity" in script_content and "Rank" in script_content:
                        player_data = json.loads(script_content)
                        break
                except:
                    continue

            if player_data and "mainEntity" in player_data:
                # Dump HTML if enabled - moved here after content is loaded
                if DUMP_HTML:
                    try:
                        with open('page_source.html', 'w',
                                  encoding='utf-8') as f:
                            f.write(driver.page_source)
                        logger.debug(
                            f"HTML source saved to page_source.html for player {username}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to save HTML source: {str(e)}")

                # Extract stats from HTML
                try:
                    # Find time played
                    time_played_element = driver.find_element(
                        By.XPATH, "//*[contains(text(), 'Time Played:')]")
                    time_played = time_played_element.text.replace(
                        'Time Played:', '').strip()
                except:
                    time_played = "Unknown"

                try:
                    # Find total matches
                    total_matches_element = driver.find_element(
                        By.XPATH,
                        "//span[contains(@class, 'text-xl font-bold text-white') and following-sibling::span[contains(text(), 'Total Matches')]]"
                    )
                    total_matches = total_matches_element.text.strip()
                except:
                    total_matches = "Unknown"

                try:
                    # Find wins
                    wins_element = driver.find_element(
                        By.XPATH,
                        "//span[contains(@class, 'text-xl font-bold text-white') and following-sibling::span[contains(text(), 'Wins')]]"
                    )
                    wins = wins_element.text.strip()
                except:
                    wins = "Unknown"

                try:
                    # Find losses
                    losses_element = driver.find_element(
                        By.XPATH,
                        "//span[contains(@class, 'text-xl font-bold text-white') and following-sibling::span[contains(text(), 'Losses')]]"
                    )
                    losses = losses_element.text.strip()
                except:
                    losses = "Unknown"

                stats = {
                    "time_played": time_played,
                    "total_matches": total_matches,
                    "wins": wins,
                    "losses": losses
                }

                try:
                    # Extract stats from HTML using a single XPath query
                    stats_elements = driver.find_elements(
                        By.XPATH,
                        "//*[contains(text(), 'Time Played:') or contains(text(), 'Total Matches') or contains(text(), 'Wins') or contains(text(), 'Losses')]"
                    )
                    for element in stats_elements:
                        text = element.text
                        if 'Time Played:' in text:
                            stats['time_played'] = text.replace(
                                'Time Played:', '').strip()
                        elif 'Total Matches' in text:
                            # Find the parent div and then find the number span
                            parent_div = element.find_element(By.XPATH, "..")
                            stats['total_matches'] = parent_div.find_element(
                                By.CSS_SELECTOR,
                                "span.text-xl.font-bold.text-white"
                            ).text.strip()
                        elif 'Wins' in text:
                            # Find the parent div and then find the number span
                            parent_div = element.find_element(By.XPATH, "..")
                            stats['wins'] = parent_div.find_element(
                                By.CSS_SELECTOR,
                                "span.text-xl.font-bold.text-white"
                            ).text.strip()
                        elif 'Losses' in text:
                            # Find the parent div and then find the number span
                            parent_div = element.find_element(By.XPATH, "..")
                            stats['losses'] = parent_div.find_element(
                                By.CSS_SELECTOR,
                                "span.text-xl.font-bold.text-white"
                            ).text.strip()
                except Exception as e:
                    print(f"Error extracting stats: {str(e)}")
                    # Keep the default values if extraction fails

                # Extract top heroes data with optimized selectors
                top_heroes = []
                try:
                    hero_elements = driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'flex items-center bg-dark-200') and .//h3[contains(@class, 'text-white text-sm font-bold')]]"
                    )

                    for i, hero_element in enumerate(hero_elements[:3], 1):
                        try:
                            hero_data = {
                                "name":
                                hero_element.find_element(
                                    By.CSS_SELECTOR,
                                    "h3.text-white.text-sm.font-bold").text,
                                "matches":
                                hero_element.find_element(
                                    By.CSS_SELECTOR,
                                    "p.text-xs.text-gray-400").text,
                                "win_rate":
                                hero_element.find_element(
                                    By.CSS_SELECTOR,
                                    "div.text-right.flex.flex-col.justify-center div.text-white.font-bold.text-sm"
                                ).text,
                                "w_l":
                                hero_element.find_element(
                                    By.CSS_SELECTOR,
                                    "div.text-right.flex.flex-col.justify-center div.text-xs.text-gray-400.mt-1"
                                ).text,
                                "rank":
                                i
                            }

                            try:
                                img_element = hero_element.find_element(
                                    By.CSS_SELECTOR,
                                    "img.w-16.h-16.rounded-full")
                                img_url = img_element.get_attribute("src")
                                if img_url.startswith("/"):
                                    img_url = f"https://mrivals.gg{img_url}"
                                hero_data["image_url"] = img_url
                            except:
                                hero_data["image_url"] = None

                            top_heroes.append(hero_data)
                        except:
                            continue
                except:
                    pass

                # Extract recent matches data with optimized selectors
                recent_matches = []
                try:
                    match_elements = driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'bg-dark-200') and .//div[contains(@class, 'absolute left-0 top-0')]]"
                    )

                    for match_element in match_elements[:10]:
                        try:
                            result_div = match_element.find_element(
                                By.CSS_SELECTOR, "div.absolute.left-0.top-0")
                            is_win = "bg-green-500" in result_div.get_attribute(
                                "class")

                            match_stats = {}
                            for stat in match_element.find_elements(
                                    By.CSS_SELECTOR, "div.text-center"):
                                try:
                                    value = stat.find_element(
                                        By.CSS_SELECTOR,
                                        "div.text-2xl.font-bold").text
                                    label = stat.find_element(
                                        By.CSS_SELECTOR,
                                        "p.text-xs.text-gray-400").text
                                    match_stats[label] = value
                                except:
                                    continue

                            recent_matches.append({
                                "result":
                                "Victory" if is_win else "Defeat",
                                "is_win":
                                is_win,
                                "details":
                                match_element.find_element(
                                    By.CSS_SELECTOR,
                                    "p.text-xs.text-gray-400").text,
                                "stats":
                                match_stats
                            })
                        except:
                            continue
                except:
                    pass

                return player_data[
                    "mainEntity"], top_heroes, stats, recent_matches

        except Exception as e:
            return None, [], {
                "time_played": "Unknown",
                "total_matches": "Unknown",
                "wins": "Unknown",
                "losses": "Unknown"
            }, []

    except Exception as e:
        return None, [], {
            "time_played": "Unknown",
            "total_matches": "Unknown",
            "wins": "Unknown",
            "losses": "Unknown"
        }, []


async def get_player_data_async(driver, username):
    """Async wrapper for get_player_data"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(selenium_pool, get_player_data, driver,
                                      username)


def get_player_data_for_top(driver, username):
    """Get player data specifically for top command using an existing driver"""
    try:
        # Navigate to the player profile page
        profile_url = f'https://mrivals.gg/player/{username}'
        driver.get(profile_url)

        # Wait for the content to load with a shorter timeout
        wait = WebDriverWait(driver,
                             SELENIUM_TIMEOUT)  # Reduced from 3 to 2 seconds

        try:
            # Wait for the JSON-LD script tag directly
            script_elements = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "script[type='application/ld+json']")))

            # Find the player data script
            player_data = None
            for script in script_elements:
                try:
                    script_content = script.get_attribute("innerHTML")
                    if "mainEntity" in script_content and "Rank" in script_content:
                        player_data = json.loads(script_content)
                        break
                except:
                    continue

            if player_data and "mainEntity" in player_data:
                # Extract rank and win rate
                rank_value = "Unknown"
                win_rate = "Unknown"

                for prop in player_data["mainEntity"].get(
                        "additionalProperty", []):
                    name = prop.get("name")
                    if name == "Rank":
                        rank_value = prop.get("value", "Unknown")
                    elif name == "Win Rate":
                        win_rate = prop.get("value", "Unknown")

                # If we get Unranked and 0% win rate, show as Private Profile
                if rank_value == "Unranked" and win_rate == "0%":
                    return {
                        "name":
                        username,  # Use the provided username for private profiles
                        "rank": "Private Profile",
                        "win_rate": "Private Profile"
                    }

                return {
                    "name": player_data["mainEntity"].get(
                        "name", username),  # Use provided username as fallback
                    "rank": rank_value,
                    "win_rate": win_rate
                }

        except Exception as e:
            return {
                "name":
                username,  # Return the provided username when data can't be fetched
                "rank": "Unknown",
                "win_rate": "Unknown"
            }

    except Exception as e:
        return {
            "name":
            username,  # Return the provided username when data can't be fetched
            "rank": "Unknown",
            "win_rate": "Unknown"
        }

    return {
        "name": username,  # Return the provided username as a last resort
        "rank": "Unknown",
        "win_rate": "Unknown"
    }


async def get_player_data_for_top_async(driver, username):
    """Async wrapper for get_player_data_for_top"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(selenium_pool, get_player_data_for_top,
                                      driver, username)


# Event: Bot is ready
@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info('------')

    # Check bot permissions
    for guild in bot.guilds:
        permissions = guild.me.guild_permissions
        if not permissions.embed_links:
            logger.warning(
                f"Bot missing 'Embed Links' permission in {guild.name}")
            try:
                await guild.system_channel.send(
                    "⚠️ Warning: This bot requires the 'Embed Links' permission to display rank information properly. "
                    "Please contact a server administrator to enable this permission."
                )
            except Exception as e:
                logger.error(
                    f"Could not send warning message in {guild.name}: {str(e)}"
                )


# Command: Ping
@bot.command(name='ping')
async def ping(ctx):
    """Check if the bot is responsive"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')


# Command: Hello
@bot.command(name='hello')
async def hello(ctx):
    """Send a greeting"""
    await ctx.send(f'Hello {ctx.author.name}! 👋')


# Command: Rank
@bot.command(name='rank')
async def rank(ctx, *, username: str):
    """Show detailed player information"""
    driver = None
    start_time = time.time()  # Record start time
    try:
        # Send initial loading message
        loading_message = await ctx.send("🔍 Fetching player data...")

        # URL encode the username
        encoded_username = urllib.parse.quote(username)
        profile_url = f'https://mrivals.gg/player/{encoded_username}'

        # Set up Chrome options for cloud environment
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')

        # Check if we're on Render.com or local environment
        if os.getenv('RENDER'):
            chrome_options.binary_location = os.getenv('CHROME_BINARY', '/usr/bin/google-chrome-stable')
            service = Service(executable_path=os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver'))
        else:
            # Local Windows configuration
            chrome_binary_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if os.path.exists(chrome_binary_path):
                chrome_options.binary_location = chrome_binary_path
            else:
                # Try alternate Chrome installation path
                chrome_binary_path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                if os.path.exists(chrome_binary_path):
                    chrome_options.binary_location = chrome_binary_path
                else:
                    raise Exception("Chrome browser not found. Please install Google Chrome.")
            service = Service(ChromeDriverManager().install())

        # Initialize the Chrome WebDriver in the thread pool
        loop = asyncio.get_event_loop()
        driver = await loop.run_in_executor(
            selenium_pool,
            lambda: webdriver.Chrome(service=service, options=chrome_options))

        # Set user agent in the thread pool
        await loop.run_in_executor(
            selenium_pool, lambda: driver.execute_cdp_cmd(
                'Network.setUserAgentOverride', {
                    "userAgent":
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }))

        # Get player data using the driver
        player_data, top_heroes, stats, recent_matches = await get_player_data_async(
            driver, username)

        if player_data:
            # Extract data from additional properties
            additional_properties = player_data.get("additionalProperty", [])
            player_name = player_data.get("name", username)

            # Initialize values
            rank_value = "Unknown"
            level = "Unknown"
            win_rate = "Unknown"

            # Extract data efficiently
            for prop in additional_properties:
                name = prop.get("name")
                if name == "Rank":
                    rank_value = prop.get("value", "Unknown")
                elif name == "Level":
                    level = prop.get("value", "Unknown")
                elif name == "Win Rate":
                    win_rate = prop.get("value", "Unknown")

            # Get rank icon URL
            rank_lower = rank_value.lower(
            )  # Convert entire rank string to lowercase
            rank_icon_url = RANK_ICONS.get(rank_lower)

            # If no icon found, try getting just the first word
            if not rank_icon_url:
                rank_lower = rank_value.split()[0].lower()
                rank_icon_url = RANK_ICONS.get(rank_lower)

            # Get player emoji or rank emoji
            player_emoji = PLAYER_EMOJIS.get(player_name)
            if not player_emoji:
                tier, _ = parse_rank(rank_value)
                player_emoji = RANK_EMOJIS.get(tier, "🎮")

            # Create embed
            embed = discord.Embed(
                title=f"Player Information for {player_emoji} {player_name}",
                color=discord.Color.blue(),
                url=profile_url)

            # Add rank information with icon if available
            rank_display = f"{rank_value}"
            if rank_icon_url:
                embed.set_thumbnail(url=rank_icon_url)

            # Add basic stats
            embed.add_field(name="🎮 Rank", value=rank_display, inline=True)
            embed.add_field(name="⭐ Level", value=level, inline=True)
            embed.add_field(name="🏆 Win Rate", value=win_rate, inline=True)

            # Add detailed stats from HTML
            embed.add_field(name="⏱️ Time Played",
                            value=stats["time_played"],
                            inline=True)
            embed.add_field(name="🎯 Total Matches",
                            value=stats["total_matches"],
                            inline=True)
            embed.add_field(name="🏅 Wins", value=stats["wins"], inline=True)
            embed.add_field(name="💀 Losses",
                            value=stats["losses"],
                            inline=True)

            # Calculate time taken
            time_taken = round(time.time() - start_time, 2)

            # Add footer with timing information
            embed.set_footer(
                text=f"Data from MRivals.gg • Time taken: {time_taken}s")

            try:
                # Delete the loading message
                await loading_message.delete()
                # Send the main embed
                await ctx.send(embed=embed)

                # Send hero embeds if they exist
                if top_heroes:
                    for hero in top_heroes:
                        # Get hero emoji or use default crown
                        hero_emoji = HERO_EMOJIS.get(hero['name'], "👑")

                        hero_embed = discord.Embed(
                            title=f"{hero_emoji} {hero['name']}",
                            color=discord.Color.blue(),
                            url=profile_url)

                        # Add hero stats
                        hero_embed.add_field(name="🎯 Matches",
                                             value=hero['matches'],
                                             inline=True)
                        hero_embed.add_field(name="🏆 Win Rate",
                                             value=hero['win_rate'],
                                             inline=True)
                        hero_embed.add_field(name="📊 W/L Record",
                                             value=hero['w_l'],
                                             inline=True)

                        # Set hero image as thumbnail if available
                        if hero.get('image_url'):
                            hero_embed.set_thumbnail(url=hero['image_url'])

                        # Add footer with rank number
                        hero_embed.set_footer(
                            text=f"#{hero['rank']} Hero for {player_name}")

                        # Send the hero embed
                        await ctx.send(embed=hero_embed)

                # Send match embed if it exists
                if recent_matches:
                    # Create match embed
                    match_embed = discord.Embed(title="🎮 Recent Matches",
                                                color=discord.Color.blue(),
                                                url=profile_url)

                    # Add each match as a field
                    for match in recent_matches:
                        # Format KDA stats
                        kda_text = f"{match['stats'].get('K', '0')}/{match['stats'].get('D', '0')}/{match['stats'].get('A', '0')}"
                        kda_ratio = match['stats'].get('KDA', '0.00')

                        # Create match value with details
                        match_value = f"{match['details']}\n"
                        match_value += f"KDA: {kda_text} (Ratio: {kda_ratio})"

                        # Add match as a field with emoji in title
                        match_embed.add_field(
                            name=
                            f"{'✅' if match['is_win'] else '❌'} {match['result']}",
                            value=match_value,
                            inline=False)

                    # Set rank image as thumbnail if available from first match
                    if recent_matches and recent_matches[0].get(
                            'rank_img_url'):
                        match_embed.set_thumbnail(
                            url=recent_matches[0]['rank_img_url'])

                    # Add footer
                    match_embed.set_footer(
                        text=f"Recent matches for {player_name}")

                    # Send the match embed
                    await ctx.send(embed=match_embed)

            except discord.Forbidden:
                await loading_message.delete()
                await ctx.send(
                    "⚠️ This bot requires the 'Embed Links' permission to display rank information properly. Please contact a server administrator to enable this permission."
                )
            except Exception as e:
                await loading_message.delete()
                await ctx.send(
                    f"An error occurred while sending the embed: {str(e)}")
        else:
            await loading_message.delete()
            await ctx.send(
                f"Could not find player data. You can view the profile at: https://mrivals.gg/player/{encoded_username}"
            )

    except Exception as e:
        try:
            await loading_message.delete()
            await ctx.send(f"An error occurred: {str(e)}")
        except:
            await ctx.send(f"An error occurred: {str(e)}")
    finally:
        if driver:
            try:
                # Quit the driver in the thread pool
                await loop.run_in_executor(selenium_pool, driver.quit)
            except:
                pass


# Command: Top
@bot.command(name='top')
async def top(ctx):
    """Show top players ranked by rank and win rate"""
    driver = None
    start_time = time.time()  # Record start time
    try:
        # Send initial loading message
        loading_message = await ctx.send("🔍 Fetching top players data...")

        # Set up Chrome options for cloud environment
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')

        # Check if we're on Render.com or local environment
        if os.getenv('RENDER'):
            chrome_options.binary_location = os.getenv('CHROME_BINARY', '/usr/bin/google-chrome-stable')
            service = Service(executable_path=os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver'))
        else:
            # Local Windows configuration
            chrome_binary_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if os.path.exists(chrome_binary_path):
                chrome_options.binary_location = chrome_binary_path
            else:
                # Try alternate Chrome installation path
                chrome_binary_path = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                if os.path.exists(chrome_binary_path):
                    chrome_options.binary_location = chrome_binary_path
                else:
                    raise Exception("Chrome browser not found. Please install Google Chrome.")
            service = Service(ChromeDriverManager().install())

        # Initialize the Chrome WebDriver in the thread pool
        loop = asyncio.get_event_loop()
        driver = await loop.run_in_executor(
            selenium_pool,
            lambda: webdriver.Chrome(service=service, options=chrome_options))

        # Set user agent in the thread pool
        await loop.run_in_executor(
            selenium_pool, lambda: driver.execute_cdp_cmd(
                'Network.setUserAgentOverride', {
                    "userAgent":
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }))

        # Get data for all players using the same driver
        player_stats = []
        for username in TOP_PLAYERS:
            stats = await get_player_data_for_top_async(driver, username)
            if stats:
                player_stats.append(stats)
            else:
                player_stats.append({
                    "name":
                    username,  # Use the actual username from TOP_PLAYERS
                    "rank": "Unknown",
                    "win_rate": "Unknown"
                })

        # Sort players by rank and win rate
        def parse_win_rate(win_rate_str):
            """Parse win rate string to get numeric value"""
            try:
                if win_rate_str == "Private Profile" or win_rate_str == "Unknown":
                    return 0
                # Remove the % symbol and convert to float
                return float(win_rate_str.rstrip('%'))
            except:
                return 0

        def sort_key(player):
            if player["rank"] == "Unknown":
                return (999, 999, 0)  # Place unknown ranks at the bottom
            tier, number = parse_rank(player["rank"])
            rank_value = RANK_ORDER.get(tier, 999)
            win_rate = parse_win_rate(player["win_rate"])
            return (
                rank_value, number, -win_rate
            )  # Sort by rank tier, number, then win rate (negative for descending order)

        player_stats.sort(
            key=sort_key)  # Remove reverse=True to sort in ascending order

        # Create embed
        embed = discord.Embed(title="🏆 Top Players",
                              color=discord.Color.blue())

        # Add players to embed
        for i, player in enumerate(player_stats, 1):
            # Get rank icon URL
            tier, _ = parse_rank(player["rank"])
            rank_icon_url = RANK_ICONS.get(tier)

            # Get player emoji or rank emoji
            player_emoji = PLAYER_EMOJIS.get(player["name"])
            if not player_emoji:
                player_emoji = RANK_EMOJIS.get(tier, "🎮")

            # Create player value
            player_value = f"Rank: {player['rank']}\n"
            player_value += f"Win Rate: {player['win_rate']}"

            # Add player as a field with emoji
            embed.add_field(name=f"#{i} {player_emoji} {player['name']}",
                            value=player_value,
                            inline=False)

        # Calculate time taken
        time_taken = round(time.time() - start_time, 2)

        # Add footer with timing information
        embed.set_footer(
            text=f"Data from MRivals.gg • Time taken: {time_taken}s")

        try:
            # Delete the loading message
            await loading_message.delete()
            # Send the embed
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await loading_message.delete()
            await ctx.send(
                "⚠️ This bot requires the 'Embed Links' permission to display rank information properly. Please contact a server administrator to enable this permission."
            )
        except Exception as e:
            await loading_message.delete()
            await ctx.send(f"An error occurred while sending the embed: {str(e)}")

    except Exception as e:
        try:
            await loading_message.delete()
            await ctx.send(f"An error occurred: {str(e)}")
        except:
            await ctx.send(f"An error occurred: {str(e)}")
    finally:
        if driver:
            try:
                # Quit the driver in the thread pool
                await loop.run_in_executor(selenium_pool, driver.quit)
            except:
                pass


# Event: Command error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "Command not found. Use !help to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide a username. Usage: !rank <username>")
    else:
        logger.error(f'Command error: {error}')
        await ctx.send("An error occurred while processing your command.")


def main():
    """Main entry point for the bot"""
    if not DISCORD_TOKEN:
        logger.error(
            "No token found. Please set DISCORD_TOKEN in your .env file")
        raise ValueError(
            "No token found. Please set DISCORD_TOKEN in your .env file")

    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise


if __name__ == '__main__':
    main()