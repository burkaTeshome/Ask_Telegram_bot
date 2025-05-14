# Mistral-Powered Telegram Bot

This is a Telegram bot built with Python that answers user questions using the Mistral AI API. The bot is deployed on [Render.com](https://render.com) using webhooks for efficient communication with Telegram. It processes user messages, queries the Mistral API for responses, and sends answers back to the user.

## Features
- Responds to the `/start` command with a welcome message.
- Answers user questions by querying the Mistral AI API (`mistral-large-latest` model).
- Deployed on Render.com with secure webhook integration.
- Uses environment variables to securely manage API keys and configuration.
- Includes error handling for API and Telegram interactions.

## Prerequisites
- **Python 3.8+**: Required for running the bot locally or deploying on Render.
- **Telegram Bot Token**: Obtain from [BotFather](https://t.me/BotFather) on Telegram.
- **Mistral API Key**: Sign up at [Mistral AI](https://mistral.ai) to get an API key.
- **Render.com Account**: For deploying the bot.
- **GitHub Account**: To store the code in a repository.
