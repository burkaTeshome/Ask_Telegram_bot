import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Mistral API configuration
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Telegram MarkdownV2 special characters that need escaping
TELEGRAM_SPECIAL_CHARS = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

# Function to escape special characters for Telegram MarkdownV2
def escape_markdown_v2(text: str) -> str:
    for char in TELEGRAM_SPECIAL_CHARS:
        text = text.replace(char, f'\\{char}')
    return text

# Function to query Mistral API
system_prompt = """
    You are a helpful research assistant who specializes in Ethiopian and African history. For questions other than this,
    tell the user to consult other generic models and that you can't handle their request.
"""
def query_mistral(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "system", 
                "content": system_prompt
            },
            {
                "role": "user", 
                "content": prompt
            },
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "Sorry, I couldn't process the response.")
        # Escape special characters for Telegram MarkdownV2
        return escape_markdown_v2(content)
    except requests.RequestException as e:
        logger.error(f"Mistral API error: {e}")
        return escape_markdown_v2("Error: Unable to get a response from the Mistral API.")

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm a bot powered by Mistral AI. Ask me anything!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    response = query_mistral(user_message)

    try:
        # Try sending with MarkdownV2 parsing
        await update.message.reply_text(response, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"Markdown parsing error: {e}")
        # Fallback to plain text if MarkdownV2 fails
        await update.message.reply_text(response, parse_mode=None)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update.message:
        await update.message.reply_text("An error occurred. Please try again later.")

def main():
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Set up webhook
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        logger.error("WEBHOOK_URL not set in environment variables")
        return
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{webhook_url}/{TELEGRAM_TOKEN}"
    )
    logger.info(f"Bot started with webhook at {webhook_url}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    main()