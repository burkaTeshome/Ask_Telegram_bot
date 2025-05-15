import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
import re

load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Mistral API configuration
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Function to convert Markdown to Telegram-compatible HTML
def markdown_to_html(text: str) -> str:
    # Convert Markdown bold (**text**) to HTML <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert Markdown italic (*text* or _text_) to HTML <i>text</i>
    text = re.sub(r'(\*|_)(.*?)\1', r'<i>\2</i>', text)
    # Convert Markdown headings (### text) to bold HTML
    text = re.sub(r'#{1,6}\s*(.*?)\n', r'<b>\1</b>\n', text)
    # Convert numbered list items (e.g., "1. Item") to HTML list
    text = re.sub(r'(\d+)\.\s*(.*?)\n', r'<b>\1.</b> \2\n', text)
    # Convert code blocks (```text```) to HTML <pre>text</pre>
    text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    # Replace multiple newlines with single newline for Telegram
    text = re.sub(r'\n\s*\n+', r'\n', text)
    return text.strip()

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
        # Convert Markdown to HTML for Telegram
        return markdown_to_html(content)
    except requests.RequestException as e:
        logger.error(f"Mistral API error: {e}")
        return markdown_to_html("Error: Unable to get a response from the Mistral API.")

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm a bot powered by Mistral AI. Ask me anything!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    response = query_mistral(user_message)

    try:
        # Send response with HTML parsing
        await update.message.reply_text(response, parse_mode="HTML")
    except Exception as e:
        logger.error(f"HTML parsing error: {e}")
        # Fallback to plain text if HTML parsing fails
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