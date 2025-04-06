# Marvel Rivals Discord Bot

A Discord bot that provides player statistics and rankings for Marvel Rivals players using data from MRivals.gg.

## Features

- `!rank <username>` - Get detailed player statistics including rank, level, win rate, and recent matches
- `!top` - View the current top players ranked by rank and win rate
- `!ping` - Check if the bot is responsive
- `!hello` - Get a friendly greeting

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- Discord Bot Token (get it from [Discord Developer Portal](https://discord.com/developers/applications))

## Installation

1. Clone this repository:
```bash
git clone https://github.com/nguyd1/discordbotmarvelrivals.git
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

4. Configure player data:
   - Copy `player_data.py.example` to `player_data.py`
   - Edit `player_data.py` to add your list of players to track

## Usage

1. Start the bot:
```bash
python bot.py
```

2. Invite the bot to your Discord server using the OAuth2 URL from the Discord Developer Portal

3. Use the commands in your Discord server:
```
!rank <username>  # Get player stats
!top             # View top players
!ping            # Check bot status
!hello           # Get a greeting
```

## Configuration

You can customize the bot's behavior by modifying these environment variables in `.env`:

- `DISCORD_TOKEN` - Your Discord bot token (required)
- `DEBUG` - Set to "True" to enable debug logging (optional)
- `SELENIUM_WORKERS` - Number of workers for Selenium operations (default: 2)
- `SELENIUM_TIMEOUT` - Timeout for Selenium operations in seconds (default: 2)

## Logging

The bot logs all activities to `bot.log`. When `DEBUG=True`, more detailed logs are generated.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data provided by [MRivals.gg](https://mrivals.gg)
- Built with [discord.py](https://discordpy.readthedocs.io/)
- Uses [Selenium](https://www.selenium.dev/) for web scraping 
