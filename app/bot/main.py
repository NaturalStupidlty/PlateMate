# -*- coding: utf-8 -*-
import sys
import os
import httpx
import io
import asyncio


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    CallbackContext
)
from app.core.config import settings


API_BASE_URL = "http://127.0.0.1:8001/api/v1/nutrition"
CLIENT_TIMEOUT = 60.0


PHOTO, CHOOSING = range(2)
BARCODE, AI_ANALYSIS = "barcode", "ai_analysis"



async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Hello! I'm your personal dietitian, PlateMate. "
        "Send me a photo of your meal or a product with a barcode. "
        "Type /menu to see all available commands."
    )
    await update.message.reply_text(welcome_message)

async def menu(update: Update, context: CallbackContext) -> None:
    """Handler for the /menu command. Displays available commands."""
    menu_text = (
        "Here are the available commands:\n"
        "/start - Welcome message\n"
        "/menu - Show this menu\n"
        "/upload - Instructions on how to upload a photo\n"
        "/stats - (Coming soon) View your nutritional statistics"
    )
    await update.message.reply_text(menu_text)

async def upload(update: Update, context: CallbackContext) -> None:
    upload_text = (
        "To analyze a meal or a product, simply send a photo directly into this chat. "
        "I'll take care of the rest!"
    )
    await update.message.reply_text(upload_text)

async def stats(update: Update, context: CallbackContext) -> None:
    stats_text = (
        "The statistics feature is currently under development. "
        "Soon you'll be able to track your daily intake and progress!"
    )
    await update.message.reply_text(stats_text)


async def handle_photo(update: Update, context: CallbackContext) -> int:
    
    photo_file = await update.message.photo[-1].get_file()
    context.user_data['photo_file_id'] = photo_file.file_id

    keyboard = [
        [InlineKeyboardButton("📷 Barcode Scan", callback_data=BARCODE)],
        [InlineKeyboardButton("🧠 AI Meal Analysis", callback_data=AI_ANALYSIS)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Great photo! What would you like me to do?", reply_markup=reply_markup)
    
    return CHOOSING

async def handle_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer() 
    
    choice = query.data
    file_id = context.user_data.get('photo_file_id')

    if not file_id:
        await query.edit_message_text("Error: Couldn't find the photo. Please send it again.")
        return ConversationHandler.END

    await query.edit_message_text(f"Got it! Starting analysis...")

    
    try:
        photo_file = await context.bot.get_file(file_id)
        image_stream = io.BytesIO()
        await photo_file.download_to_memory(out=image_stream)
        image_bytes = image_stream.getvalue()
    except Exception as e:
        await query.message.reply_text(f"Error downloading the image: {e}")
        return ConversationHandler.END

    
    if choice == BARCODE:
        endpoint = "/analyze-barcode"
    else:
        endpoint = "/analyze-photo"

    await call_api(query.message, image_bytes, endpoint)
    
    
    return ConversationHandler.END

async def call_api(message, image_bytes: bytes, endpoint: str):
    try:
        files = {'image': ('photo.jpg', image_bytes, 'image/jpeg')}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}{endpoint}", files=files, timeout=CLIENT_TIMEOUT)
        
        response.raise_for_status() 

        data = response.json()
        reply_text = (
            f"✅ **{data['food_item']}**\n\n"
            f"Calories: {data['calories']} kcal\n"
            f"Protein: {data['protein']} g\n"
            f"Fat: {data['fat']} g\n"
            f"Carbohydrates: {data['carbohydrates']} g"
        )
        await message.reply_text(reply_text, parse_mode='Markdown')

        
        follow_up_message = "Maybe there's something else you're interested in? If so, use /upload"
        await message.reply_text(follow_up_message)
        

    except httpx.TimeoutException:
        await message.reply_text("The analysis is taking too long. Please try again with a clearer image.")
    except httpx.ConnectError:
        await message.reply_text("I can't connect to the analysis server. Please make sure the server is running on port 8001.")
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", "an unknown error occurred")
        await message.reply_text(f"An error occurred during analysis: {error_detail}")
    except Exception as e:
        await message.reply_text("A critical error occurred. Failed to process the request.")
        print(f"Critical error in call_api: {e}")

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def run_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={
            CHOOSING: [
                CallbackQueryHandler(handle_choice, pattern=f"^{BARCODE}$"),
                CallbackQueryHandler(handle_choice, pattern=f"^{AI_ANALYSIS}$"),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CommandHandler("stats", stats))

    print("Telegram bot has started. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    run_bot()