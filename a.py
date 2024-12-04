from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import requests
from urllib.parse import urlparse
import time

# Bot token
BOT_TOKEN = "7274954327:AAEB_LIWNe9xVf4lPCNlij6BFuBPAt5_tjo"

# Rate limiting: max requests per user within a specific time frame
RATE_LIMIT = 5  # Max requests
TIME_WINDOW = 60  # Seconds
user_requests = {}  # Track user requests: {user_id: [timestamps]}

# Blocked URLs cache to avoid redundant lookups
cache = {}

# Forbidden words to block
FORBIDDEN_WORDS = ["scam", "hack"]

# Check a website for scams
def check_website(url):
    try:
        # Extract the domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path

        # Cache check
        if domain in cache:
            return cache[domain]

        # Query ScamMinder
        scamminder_url = f"https://scamminder.com/websites/{domain}"
        response = requests.get(scamminder_url)

        if response.status_code == 200:
            if "This domain has been reported as a scam" in response.text:
                result = f"⚠️ The website **{domain}** is reported as a scam!\nDetails: {scamminder_url}"
            elif "No reports for this domain" in response.text:
                result = f"✅ The website **{domain}** seems safe.\nDetails: {scamminder_url}"
            else:
                result = f"❓ The status of **{domain}** is unclear.\nDetails: {scamminder_url}"
            # Cache result
            cache[domain] = result
            return result
        else:
            return "❌ Unable to connect to ScamMinder."
    except Exception as e:
        return f"⚠️ Error while checking the website: {e}"

# Rate limiter
def is_rate_limited(user_id):
    now = time.time()
    if user_id not in user_requests:
        user_requests[user_id] = []
    # Remove expired requests
    user_requests[user_id] = [
        t for t in user_requests[user_id] if now - t < TIME_WINDOW
    ]
    # Check if the limit is exceeded
    if len(user_requests[user_id]) >= RATE_LIMIT:
        return True
    # Log the new request
    user_requests[user_id].append(now)
    return False

# Handle messages
def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    user_id = update.message.from_user.id

    # Check for forbidden words
    if any(word in user_message.lower() for word in FORBIDDEN_WORDS):
        update.message.reply_text("🚫 Your message contains prohibited content.")
        return

    # Rate limit check
    if is_rate_limited(user_id):
        update.message.reply_text(
            "⏳ You're sending too many requests. Please wait a moment."
        )
        return

    # Validate and check the URL
    if user_message.startswith("http://") or user_message.startswith("https://"):
        update.message.reply_text("⏳ Checking the website...")
        result = check_website(user_message)
        update.message.reply_text(result)
    else:
        update.message.reply_text(
            "❗ Please send a valid URL (e.g., https://example.com)."
        )

# Start the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Add message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
