# -*- coding: utf-8 -*-
import sys
import os
import httpx
import io
import asyncio
import collections
from app.bot.scrape_calories import (
    find_best_match,
    get_product_nutrition,
)
import json

def load_local_product_catalog(path="app/bot/cache/products.json"):
    global PRODUCT_CATALOG
    try:
        with open(path, "r", encoding="utf-8") as f:
            PRODUCT_CATALOG = json.load(f)
        print(f"Loaded {len(PRODUCT_CATALOG)} products from local cache.")
    except Exception as e:
        print(f"FAILED to load local product list: {e}")
        PRODUCT_CATALOG = []

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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


API_BASE_URL = "http://127.0.0.1:8001/api/v1"
CLIENT_TIMEOUT = 60.0


PHOTO, CHOOSING = range(2)
BARCODE, AI_ANALYSIS = "barcode", "ai_analysis"

async def nutrition_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Enter product name",
        parse_mode="Markdown"
    )

async def nutrition_query_handler(update: Update, context: CallbackContext):
    global PRODUCT_CATALOG
    text = update.message.text.replace("/nutrition", "").strip()

    if not text:
        await update.message.reply_text("Enter product name.", parse_mode="Markdown")
        return

    if not PRODUCT_CATALOG:
        await update.message.reply_text(
            "Failed load catalogue. "
        )
        return

    matches = find_best_match(text, PRODUCT_CATALOG, limit=5)
    if not matches:
        await update.message.reply_text("Product not found. Try another product name.")
        return

    name, url, score = matches[0]
    await update.message.reply_text(f"🔎 Found best match: *{name}*", parse_mode="Markdown")

    try:
        info = get_product_nutrition(url)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        return

    reply = f"**{info.get('title', name)}**\n\n"
    reply += f"Calories: {info.get('energy_kcal', '?')}\n"
    reply += f"Proteins: {info.get('protein_g', '?')}\n"
    reply += f"Fats: {info.get('fat_g', '?')}\n"
    reply += f"Carbohydrates: {info.get('carbs_g', '?')}\n"

    await update.message.reply_text(reply, parse_mode="Markdown")

def update_user_history(context: CallbackContext, hot_vector: list):
    if not hot_vector or len(hot_vector) != 12:
        return
    if 'history' not in context.user_data:
        context.user_data['history'] = collections.deque(maxlen=5)
    context.user_data['history'].append(hot_vector)
    print(f"User history updated. Current size: {len(context.user_data['history'])}")

def get_aggregated_vector(context: CallbackContext) -> list:
    if 'history' not in context.user_data or not context.user_data['history']:
        return [0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0] 

    history = list(context.user_data['history'])
    n = len(history)
    summed_vector = [sum(x) for x in zip(*history)]
    threshold = 1 if n <= 2 else 2
    final_vector = [1 if x >= threshold else 0 for x in summed_vector]
    return final_vector



async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Hello! I'm PlateMate. Send me a photo of your food!\n"
        "I learn from what you eat to give you better recommendations."
    )
    await update.message.reply_text(welcome_message)

async def menu(update: Update, context: CallbackContext) -> None:
    menu_text = (
        "/start - Restart\n"
        "/recommend - Get recommendations based on your history\n"
        "/clear_history - Clear your food history"
    )
    await update.message.reply_text(menu_text)

async def clear_history(update: Update, context: CallbackContext) -> None:
    context.user_data['history'] = collections.deque(maxlen=5)
    await update.message.reply_text("Your food history has been cleared. I'm ready to learn again!")



async def handle_photo(update: Update, context: CallbackContext) -> int:
    photo_file = await update.message.photo[-1].get_file()
    context.user_data['photo_file_id'] = photo_file.file_id

    keyboard = [
        [InlineKeyboardButton("📷 Barcode Scan", callback_data=BARCODE)],
        [InlineKeyboardButton("🧠 AI Meal Analysis", callback_data=AI_ANALYSIS)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select analysis type:", reply_markup=reply_markup)
    return CHOOSING

async def handle_choice(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    file_id = context.user_data.get('photo_file_id')
    
    await query.edit_message_text(f"Analyzing photo...")

    try:
        photo_file = await context.bot.get_file(file_id)
        image_stream = io.BytesIO()
        await photo_file.download_to_memory(out=image_stream)
        image_bytes = image_stream.getvalue()
        
        endpoint = "/nutrition/analyze-barcode" if choice == BARCODE else "/nutrition/analyze-photo"
        
        files = {'image': ('photo.jpg', image_bytes, 'image/jpeg')}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}{endpoint}", files=files, timeout=CLIENT_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if choice == AI_ANALYSIS:
                hot_vector = data.get('hot_vector')
                if hot_vector:
                    update_user_history(context, hot_vector)

            reply_text = (
                f"✅ **{data['food_item']}**\n\n"
                f"Calories: {data['calories']} kcal\n"
                f"Protein: {data['protein']} g\n"
                f"Fat: {data['fat']} g\n"
                f"Carbohydrates: {data['carbohydrates']} g"
            )
            
            await query.message.reply_text(reply_text, parse_mode='Markdown')
            
            
            follow_up_message = "Maybe there's something else you're interested in? If so, just send another photo!"
            await query.message.reply_text(follow_up_message)
        else:
            await query.message.reply_text("Error analyzing image.")

    except Exception as e:
        await query.message.reply_text(f"Error: {e}")

    return ConversationHandler.END



async def recommend_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Analyzing your recent meals to find recommendations...")
    
    my_hot_vector = get_aggregated_vector(context)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/recommend/", 
                json={"hot_vector": my_hot_vector}, 
                timeout=CLIENT_TIMEOUT
            )
            response.raise_for_status()
            recommendations = response.json()
            
            top_3 = recommendations[:3]
            
            if not top_3:
                await update.message.reply_text("No recommendations found.")
                return

            await update.message.reply_text(f"Based on your history, here are 3 dishes you might like:")

            for item in top_3:
                item_id = item['id']
                item_name = item['food_item']
                
                img_resp = await client.get(f"{API_BASE_URL}/food/image/{item_id}", timeout=20.0)
                if img_resp.status_code == 200:
                    await update.message.reply_photo(photo=img_resp.content, caption=f"🍽 {item_name}")
                else:
                    await update.message.reply_text(f"🍽 {item_name} (Image unavailable)")

    except Exception as e:
        await update.message.reply_text("Failed to get recommendations. Please try again later.")
        print(f"Recommendation error: {e}")

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Restart"),
        BotCommand("menu", "Show menu"),
        BotCommand("recommend", "Get recommendations based on history"),
        BotCommand("clear_history", "Clear your food history")
    ])

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = (
        Application.builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .post_init(set_commands)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO, handle_photo)],
        states={CHOOSING: [CallbackQueryHandler(handle_choice)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("recommend", recommend_command))
    application.add_handler(CommandHandler("clear_history", clear_history))
    application.add_handler(CommandHandler("nutrition", nutrition_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/nutrition "), nutrition_query_handler))

    load_local_product_catalog()

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    run_bot()
