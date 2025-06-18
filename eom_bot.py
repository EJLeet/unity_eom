import discord
from discord.ext import commands
from discord import app_commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from datetime import datetime, timedelta
import calendar
import os
import json
from typing import Optional


class EOMBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)

        # Google Sheets setup
        self.gc = None
        self.setup_google_sheets()

    def setup_google_sheets(self):
        """Setup Google Sheets API connection"""
        try:
            # Define the scope
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']

            # Load credentials from JSON file
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'credentials.json', scope)
            self.gc = gspread.authorize(creds)
            print("✅ Google Sheets API connected successfully")
        except Exception as e:
            print(f"❌ Failed to connect to Google Sheets API: {e}")
            print("Make sure you have credentials.json file in the same directory")

    async def setup_hook(self):
        """Sync slash commands when bot starts"""
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")


bot = EOMBot()


@bot.event
async def on_ready():
    print(f'🚀 {bot.user} (EOM Bot) is ready!')
    print(f'📊 Connected to {len(bot.guilds)} server(s)')

    # Set bot status
    await bot.change_presence(
        activity=discord.Game(name="Use /EOM to export messages")
    )


def get_month_dates(month_name: str, year: int = None) -> tuple:
    """Get start and end dates for a given month"""
    if year is None:
        year = datetime.now().year

    # Convert month name to number
    month_map = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }

    month_num = month_map.get(month_name.lower())
    if not month_num:
        raise ValueError(f"Invalid month: {month_name}")

    # Get first and last day of the month
    start_date = datetime(year, month_num, 1)
    last_day = calendar.monthrange(year, month_num)[1]
    end_date = datetime(year, month_num, last_day, 23, 59, 59)

    return start_date, end_date


async def collect_messages(guild, start_date, end_date, progress_callback=None):
    """Collect all messages from all channels in the specified date range"""
    all_messages = []
    total_channels = len(
        [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)])
    processed_channels = 0

    for channel in guild.channels:
        if not isinstance(channel, discord.TextChannel):
            continue

        try:
            # Check if bot has permission to read message history
            if not channel.permissions_for(guild.me).read_message_history:
                continue

            async for message in channel.history(
                limit=None,
                after=start_date,
                before=end_date,
                oldest_first=True
            ):
                # Skip bot messages if desired (you can modify this)
                if message.author.bot:
                    continue

                message_data = {
                    'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'channel': channel.name,
                    'author': str(message.author),
                    'author_id': message.author.id,
                    'content': message.content[:1000],  # Limit content length
                    'attachments': len(message.attachments),
                    'reactions': len(message.reactions),
                    'message_id': message.id
                }
                all_messages.append(message_data)

            processed_channels += 1
            if progress_callback:
                await progress_callback(processed_channels, total_channels, channel.name)

        except discord.Forbidden:
            # Skip channels we can't access
            processed_channels += 1
            continue
        except Exception as e:
            print(f"Error processing channel {channel.name}: {e}")
            processed_channels += 1
            continue

    return all_messages


def create_google_sheet(sheet_name: str, messages: list):
    """Create a new Google Sheet and populate it with messages"""
    try:
        # Create a new spreadsheet
        spreadsheet = bot.gc.create(sheet_name)
        worksheet = spreadsheet.sheet1

        # Set up headers
        headers = [
            'Timestamp', 'Channel', 'Author', 'Author ID',
            'Content', 'Attachments', 'Reactions', 'Message ID'
        ]
        worksheet.append_row(headers)

        # Add messages in batches to avoid API limits
        batch_size = 100
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            rows_to_add = []

            for msg in batch:
                row = [
                    msg['timestamp'],
                    msg['channel'],
                    msg['author'],
                    str(msg['author_id']),
                    msg['content'],
                    str(msg['attachments']),
                    str(msg['reactions']),
                    str(msg['message_id'])
                ]
                rows_to_add.append(row)

            if rows_to_add:
                worksheet.append_rows(rows_to_add)

        # Format the sheet
        worksheet.format('A1:H1', {
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}}
        })

        # Auto-resize columns
        worksheet.columns_auto_resize(0, len(headers) - 1)

        # Make the spreadsheet shareable (anyone with link can view)
        spreadsheet.share('', perm_type='anyone', role='reader')

        return spreadsheet.url

    except Exception as e:
        raise Exception(f"Failed to create Google Sheet: {str(e)}")


@bot.tree.command(name="eom", description="Export messages from a specified month to Google Sheets")
@app_commands.describe(
    month="Month to export (e.g., July, Jan, December)",
    year="Year (optional, defaults to current year)",
    include_bots="Include bot messages (default: False)"
)
async def export_messages(
    interaction: discord.Interaction,
    month: str,
    year: Optional[int] = None,
    include_bots: bool = False
):
    """Export messages from specified month to Google Sheets"""

    # Check if user has permission (modify as needed)
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need administrator permissions to use this command.",
            ephemeral=True
        )
        return

    # Check if Google Sheets is set up
    if not bot.gc:
        await interaction.response.send_message(
            "❌ Google Sheets integration is not configured. Please check the bot setup.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        # Get date range
        if year is None:
            year = datetime.now().year
        start_date, end_date = get_month_dates(month, year)

        # Create progress embed
        embed = discord.Embed(
            title="📊 EOM - Message Export",
            description=f"Exporting messages from **{month.title()} {year}**...",
            color=0x0099ff
        )
        embed.add_field(
            name="Status", value="🔍 Scanning channels...", inline=False)
        embed.add_field(name="Progress", value="0%", inline=True)
        embed.add_field(name="Current Channel",
                        value="Starting...", inline=True)

        progress_message = await interaction.followup.send(embed=embed)

        # Progress callback function
        async def update_progress(processed, total, current_channel):
            percentage = int((processed / total) * 100)
            embed.set_field_at(1, name="Progress",
                               value=f"{percentage}%", inline=True)
            embed.set_field_at(2, name="Current Channel",
                               value=current_channel, inline=True)
            try:
                await progress_message.edit(embed=embed)
            except:
                pass  # Ignore edit failures

        # Collect messages
        messages = await collect_messages(
            interaction.guild,
            start_date,
            end_date,
            update_progress
        )

        if not messages:
            embed.set_field_at(
                0, name="Status", value="❌ No messages found in the specified period", inline=False)
            embed.set_field_at(1, name="Progress", value="100%", inline=True)
            embed.set_field_at(2, name="Current Channel",
                               value="Complete", inline=True)
            await progress_message.edit(embed=embed)
            return

        # Update progress for sheet creation
        embed.set_field_at(
            0, name="Status", value="📝 Creating Google Sheet...", inline=False)
        embed.set_field_at(1, name="Progress", value="90%", inline=True)
        embed.set_field_at(2, name="Current Channel",
                           value="Finalizing...", inline=True)
        await progress_message.edit(embed=embed)

        # Create Google Sheet
        sheet_name = f"{interaction.guild.name} - {month.title()} {year} Messages"
        sheet_url = create_google_sheet(sheet_name, messages)

        # Final success message
        success_embed = discord.Embed(
            title="✅ Export Complete!",
            description=f"Successfully exported **{len(messages)}** messages from **{month.title()} {year}**",
            color=0x00ff00
        )
        success_embed.add_field(
            name="📋 Google Sheet", value=f"[Click here to view]({sheet_url})", inline=False)
        success_embed.add_field(name="📊 Message Count",
                                value=str(len(messages)), inline=True)
        success_embed.add_field(
            name="📅 Date Range", value=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", inline=True)
        success_embed.set_footer(
            text=f"Exported by {interaction.user.display_name}")

        await progress_message.edit(embed=success_embed)

    except ValueError as e:
        await interaction.followup.send(f"❌ {str(e)}", ephemeral=True)
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Export Failed",
            description=f"An error occurred: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed, ephemeral=True)


@bot.tree.command(name="eom_help", description="Get help with EOM bot commands")
async def eom_help(interaction: discord.Interaction):
    """Show help information for EOM bot"""

    embed = discord.Embed(
        title="📋 EOM Bot Help",
        description="Export messages from your Discord server to Google Sheets",
        color=0x0099ff
    )

    embed.add_field(
        name="🔧 Main Command",
        value="`/eom <month> [year] [include_bots]`\n"
              "Export all messages from a specific month",
        inline=False
    )

    embed.add_field(
        name="📝 Examples",
        value="• `/eom July` - Export July messages (current year)\n"
              "• `/eom January 2023` - Export January 2023 messages\n"
              "• `/eom Dec 2023 True` - Include bot messages",
        inline=False
    )

    embed.add_field(
        name="⚡ Features",
        value="• Exports to Google Sheets automatically\n"
              "• Includes timestamps, authors, channels\n"
              "• Progress tracking during export\n"
              "• Handles large message volumes",
        inline=False
    )

    embed.add_field(
        name="🔒 Permissions",
        value="Administrator permissions required to use export commands",
        inline=False
    )

    embed.set_footer(text="EOM - End of Month Message Exporter")

    await interaction.response.send_message(embed=embed)

# Error handling for slash commands


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command!",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(error)}",
            ephemeral=True
        )

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')

    if not TOKEN:
        print("❌ Error: Please set your DISCORD_BOT_TOKEN environment variable")
        print("You can get a token from https://discord.com/developers/applications")
    else:
        print("🚀 Starting EOM Bot...")
        bot.run(TOKEN)
