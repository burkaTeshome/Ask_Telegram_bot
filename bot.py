import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.webhook import WebhookUpdate
import os
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Mistral API configuration
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"  # Replace with actual Mistral API endpoint
# Replace these lines in bot.py
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Function to query Mistral API
def query_mistral(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-large-latest",  # Specify the Mistral model (adjust as needed)
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.7
    }
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("choices", [{}])[0].get("text", "Sorry, I couldn't process the response.")
    except requests.RequestException as e:
        logger.error(f"Mistral API error: {e}")
        return "Error: Unable to get a response from the Mistral API."

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm a bot powered by Mistral AI. Ask me anything!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    response = query_mistral(user_message)
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("An error occurred. Please try again later.")

# Webhook handler
async def webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_message(update, context)

def main():
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Set up webhook
    import os
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL", "YOUR_RENDER_WEBHOOK_URL")  # Set this after creating the service
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{webhook_url}/{TELEGRAM_TOKEN}"
    )
    logger.info(f"Bot started with webhook at {webhook_url}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    main()