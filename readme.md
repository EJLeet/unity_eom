# EOM Discord Bot - Local Setup Guide

**EOM (End of Month)** is a Discord bot that exports all messages from a specified month to Google Sheets using slash commands.

## 📋 Prerequisites

- Python 3.8 or higher
- A Discord account
- A Google account
- Basic command line knowledge

## 🚀 Quick Start

### 1. Download and Setup Files

1. Create a new folder for your bot (e.g., `EOM-Bot`)
2. Save the bot code as `eom_bot.py`
3. Create a `requirements.txt` file with the dependencies
4. Create a `.env` file (we'll add the token later)

Your folder structure should look like:
```
EOM-Bot/
├── eom_bot.py
├── requirements.txt
├── .env
└── credentials.json (we'll create this)
```

### 2. Install Python Dependencies

Open terminal/command prompt in your bot folder and run:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install discord.py gspread oauth2client python-dotenv
```

### 3. Set Up Google Sheets API

#### Step 3.1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "EOM Discord Bot")
4. Click "Create"

#### Step 3.2: Enable APIs
1. In the search bar, type "Google Sheets API"
2. Click on it and press "Enable"
3. Go back and search for "Google Drive API"
4. Click on it and press "Enable"

#### Step 3.3: Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Enter a name (e.g., "eom-bot-service")
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

#### Step 3.4: Generate Key File
1. Click on your newly created service account
2. Go to "Keys" tab
3. Click "Add Key" → "Create New Key"
4. Select "JSON" and click "Create"
5. A file will download - rename it to `credentials.json`
6. Move this file to your bot folder

### 4. Set Up Discord Bot

#### Step 4.1: Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name it "EOM" and click "Create"

#### Step 4.2: Create Bot
1. Go to "Bot" section in the left sidebar
2. Click "Add Bot" → "Yes, do it!"
3. Under "Token" section, click "Copy" to copy your bot token
4. **Keep this token secret!**

#### Step 4.3: Configure Bot Settings
1. Scroll down to "Privileged Gateway Intents"
2. Enable "Message Content Intent"
3. Save changes

#### Step 4.4: Add Bot Token to Environment File
Edit your `.env` file and add:
```
DISCORD_BOT_TOKEN=your_bot_token_here
```
Replace `your_bot_token_here` with the actual token you copied.

### 5. Invite Bot to Your Server

#### Step 5.1: Generate Invite Link
1. In Discord Developer Portal, go to "OAuth2" → "URL Generator"
2. Under "Scopes", select:
   - `bot`
   - `applications.commands`
3. Under "Bot Permissions", select:
   - `Administrator` (or customize as needed)
4. Copy the generated URL at the bottom

#### Step 5.2: Invite Bot
1. Paste the URL in your browser
2. Select your Discord server
3. Click "Authorize"
4. Complete any captcha if prompted

### 6. Run the Bot

Open terminal/command prompt in your bot folder and run:

```bash
python bot.py
```

You should see:
```
✅ Google Sheets API connected successfully
✅ Synced 2 command(s)
🚀 EOM#1234 (EOM Bot) is ready!
📊 Connected to 1 server(s)
```

## 🎯 Usage

### Available Commands

- `/eom <month>` - Export messages from specified month (current year)
- `/eom <month> <year>` - Export messages from specific month and year
- `/eom <month> <year> <include_bots>` - Include/exclude bot messages
- `/eom_help` - Show help information

### Examples

```
/eom July
/eom January 2023
/eom December 2023 True
```

### What Gets Exported

The bot exports the following data to Google Sheets:
- Timestamp
- Channel name
- Author name and ID
- Message content (first 1000 characters)
- Number of attachments
- Number of reactions
- Message ID

## 🛠️ Troubleshooting

### Common Issues

**"Google Sheets API not connected"**
- Make sure `credentials.json` exists in your bot folder
- Verify you enabled both Google Sheets API and Google Drive API

**"Failed to sync commands"**
- Make sure your bot token is correct in `.env` file
- Ensure bot has proper permissions in your server

**"You don't have permission to use this command"**
- Only server administrators can use export commands
- Grant yourself administrator permissions or modify the permission check in code

**"No messages found"**
- Check if the bot has "Read Message History" permission in channels
- Verify the month name is spelled correctly
- Make sure there were actually messages in that time period

### Bot Not Responding
1. Check if the bot is online in your server (green dot)
2. Make sure you're using `/` for slash commands, not `!`
3. Try running `/eom_help` first to test if commands work

### Permission Issues
The bot needs these permissions:
- Read Messages
- Read Message History
- Use Slash Commands
- Send Messages
- Embed Links

## 📁 File Structure

Your final folder should look like:
```
EOM-Bot/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── credentials.json    # Google API credentials (keep secret!)
├── .env               # Discord bot token (keep secret!)
└── README.md          # This file
```

## 🔒 Security Notes

- **Never share your bot token or credentials.json**
- Add `.env` and `credentials.json` to `.gitignore` if using version control
- The bot only exports messages from channels it can access
- Exported sheets are set to "view only" for anyone with the link

## 🚫 Limitations (Local Hosting)

- Bot only works when your computer is on
- Bot goes offline if you lose internet connection
- You need to keep the terminal window open
- No automatic restarts if the bot crashes

## 🆙 Next Steps

Once you're comfortable with local hosting, consider:
- **Railway** - Free cloud hosting for Discord bots
- **Google Cloud Run** - Serverless hosting with generous free tier
- **DigitalOcean** - VPS hosting for more control

## 📞 Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all setup steps were completed
3. Ensure all files are in the correct locations
4. Test with a small server first

---

**Happy message exporting! 📊✨**