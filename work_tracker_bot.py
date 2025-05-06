import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PASSWORD, MAIN_MENU, SETTINGS, SETTING_MEAL, SETTING_BREAK, SETTING_WORK_HOURS = range(6)
SETTING_MORNING_MEAL, SETTING_EVENING_MEAL, SETTING_SHORT_BREAK = range(6, 9)
SETTING_SLEEP_TIME, SETTING_WORK_START, MANAGE_USERS = range(9, 12)
ADDING_USER, REMOVING_USER = range(12, 14)

CONFIG_DIR = "config"
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
USERS_FILE = os.path.join(CONFIG_DIR, "users.json")
ADMIN_FILE = os.path.join(CONFIG_DIR, "admin.json")

os.makedirs(CONFIG_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "meal_time": 30,
    "break_time": 15,
    "work_hours": 8,
    "morning_meal": 20,
    "evening_meal": 30,
    "short_break": 10,
    "sleep_time": 8,
    "work_start": "09:00",
}

DEFAULT_ADMIN = {
    "password": "sardor1107",
    "admin_id": 7178962248
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    else:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    else:
        with open(USERS_FILE, 'w') as f:
            users = {"authorized_users": []}
            json.dump(users, f, indent=4)
        return users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_admin():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            return json.load(f)
    else:
        with open(ADMIN_FILE, 'w') as f:
            json.dump(DEFAULT_ADMIN, f, indent=4)
        return DEFAULT_ADMIN

def save_admin(admin):
    with open(ADMIN_FILE, 'w') as f:
        json.dump(admin, f, indent=4)

def make_schedule(settings):
    try:
        hour, minute = map(int, settings["work_start"].split(":"))
        start_time = datetime.now().replace(hour=hour, minute=minute)

        if start_time < datetime.now():
            start_time = start_time + timedelta(days=1)

        activities = []
        work_mins = settings["work_hours"] * 60

        breakfast_time = start_time - timedelta(minutes=60)
        activities.append({
            "type": "meal",
            "name": "Breakfast",
            "start": breakfast_time,
            "duration": settings["morning_meal"]
        })

        morning_short_break = start_time + timedelta(minutes=60)
        activities.append({
            "type": "break",
            "name": "Morning Short Break",
            "start": morning_short_break,
            "duration": settings["short_break"]
        })

        morning_break = start_time + timedelta(minutes=120)
        activities.append({
            "type": "break",
            "name": "Morning Break",
            "start": morning_break,
            "duration": settings["break_time"]
        })

        lunch_time = start_time + timedelta(minutes=work_mins // 2 - settings["meal_time"] // 2)
        activities.append({
            "type": "meal",
            "name": "Lunch",
            "start": lunch_time,
            "duration": settings["meal_time"]
        })

        after_lunch_break = lunch_time + timedelta(minutes=settings["meal_time"] + 60)
        activities.append({
            "type": "break",
            "name": "After Lunch Break",
            "start": after_lunch_break,
            "duration": settings["short_break"]
        })

        afternoon_break = lunch_time + timedelta(minutes=settings["meal_time"] + 120)
        activities.append({
            "type": "break",
            "name": "Afternoon Break",
            "start": afternoon_break,
            "duration": settings["break_time"]
        })

        work_end = start_time + timedelta(minutes=work_mins)
        dinner_time = work_end + timedelta(minutes=60)
        activities.append({
            "type": "meal",
            "name": "Dinner",
            "start": dinner_time,
            "duration": settings["evening_meal"]
        })

        sleep_start = dinner_time + timedelta(hours=3)
        activities.append({
            "type": "sleep",
            "name": "Sleep Time",
            "start": sleep_start,
            "duration": settings["sleep_time"] * 60
        })

        result = "Your daily schedule:\n\n"

        sorted_activities = sorted(activities, key=lambda x: x["start"])

        for activity in sorted_activities:
            end_time = activity["start"] + timedelta(minutes=activity["duration"])
            result += f"{activity['name']}: {format_datetime(activity['start'])} - "
            result += f"{format_datetime(end_time)} ({format_time(activity['duration'])})\n"

        result += f"\nWork Start: {format_datetime(start_time)}\n"
        result += f"Work End: {format_datetime(work_end)}\n"
        result += f"Total Work Time: {settings['work_hours']} hours\n"
        result += f"Sleep Time: {format_time(settings['sleep_time'] * 60)}\n"

        return result

    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        return f"Error creating schedule: {e}"

def format_time(minutes):
    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        if mins > 0:
            return f"{hours} hours {mins} minutes"
        return f"{hours} hours"

    return f"{mins} minutes"

def format_datetime(dt):
    return dt.strftime("%H:%M")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    users = load_users()

    if str(user_id) in users["authorized_users"]:
        keyboard = [
            ["📋 My Schedule", "⚙️ Settings"],
            ["📱 Contacts", "❓ Help"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Welcome to the Work Tracker Bot!\n"
            "Use the menu to navigate.",
            reply_markup=reply_markup
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Sorry, you do not have access to this bot.\n"
            "If you want access, please contact the administrator."
        )
        return ConversationHandler.END

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter the administrator password:")
    return PASSWORD

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text
    admin = load_admin()

    if password == admin["password"]:
        if not admin["admin_id"]:
            admin["admin_id"] = str(update.effective_user.id)
            save_admin(admin)

        keyboard = [
            ["📊 Manage Users", "⚙️ Schedule Settings"],
            ["🔙 Back"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Admin Panel.\nSelect an action:",
            reply_markup=reply_markup
        )
        return MAIN_MENU # Or a dedicated ADMIN_MENU state
    else:
        await update.message.reply_text("Incorrect password.")
        return ConversationHandler.END

async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    settings = load_settings()
    schedule = make_schedule(settings)
    await update.message.reply_text(schedule)
    return MAIN_MENU

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    settings = load_settings()

    message = "Current settings:\n\n"
    message += f"🍽️ Lunch: {settings['meal_time']} minutes\n"
    message += f"☕ Break: {settings['break_time']} minutes\n"
    message += f"⏰ Work Hours: {settings['work_hours']} hours\n"
    message += f"🍳 Breakfast: {settings['morning_meal']} minutes\n"
    message += f"🍲 Dinner: {settings['evening_meal']} minutes\n"
    message += f"🧘‍♂️ Short Break: {settings['short_break']} minutes\n"
    message += f"😴 Sleep Time: {settings['sleep_time']} hours\n"
    message += f"🏢 Work Start: {settings['work_start']}\n\n"
    message += "What would you like to change?"

    keyboard = [
        ["🍽️ Lunch", "☕ Break", "⏰ Work Hours"],
        ["🍳 Breakfast", "🍲 Dinner", "🧘‍♂️ Short Break"],
        ["😴 Sleep Time", "🏢 Work Start"],
        ["🔙 Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)
    return SETTINGS

async def manage_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users = load_users()

    message = "Manage Users:\n\n"
    message += "Authorized Users:\n"

    if users["authorized_users"]:
        for idx, user_id in enumerate(users["authorized_users"], 1):
            message += f"{idx}. ID: {user_id}\n"
    else:
        message += "No authorized users\n"

    keyboard = [
        ["➕ Add User", "➖ Remove User"],
        ["🔙 Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(message, reply_markup=reply_markup)
    return MANAGE_USERS

async def add_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter the User ID to add:")
    return ADDING_USER

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.text.strip()
    users = load_users()

    if user_id.isdigit():
        if user_id not in users["authorized_users"]:
            users["authorized_users"].append(user_id)
            save_users(users)
            await update.message.reply_text(f"User with ID {user_id} added.")
        else:
            await update.message.reply_text(f"User with ID {user_id} is already authorized.")
    else:
        await update.message.reply_text("Invalid ID format. Please enter a numeric ID.")

    return await manage_users(update, context)

async def remove_user_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users = load_users()

    if not users["authorized_users"]:
        await update.message.reply_text("No authorized users to remove.")
        return await manage_users(update, context)

    await update.message.reply_text("Enter the User ID to remove:")
    return REMOVING_USER

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.text.strip()
    users = load_users()

    if user_id in users["authorized_users"]:
        users["authorized_users"].remove(user_id)
        save_users(users)
        await update.message.reply_text(f"User with ID {user_id} removed.")
    else:
        await update.message.reply_text(f"User with ID {user_id} not found.")

    return await manage_users(update, context)

async def update_meal_time_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter lunch time in minutes:")
    return SETTING_MEAL

async def update_meal_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        meal_time = int(update.message.text)
        settings = load_settings()
        settings["meal_time"] = meal_time
        save_settings(settings)
        await update.message.reply_text(f"Lunch time set to {meal_time} minutes.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_break_time_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter break time in minutes:")
    return SETTING_BREAK

async def update_break_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        break_time = int(update.message.text)
        settings = load_settings()
        settings["break_time"] = break_time
        save_settings(settings)
        await update.message.reply_text(f"Break time set to {break_time} minutes.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_work_hours_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter the number of work hours:")
    return SETTING_WORK_HOURS

async def update_work_hours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        work_hours = int(update.message.text)
        settings = load_settings()
        settings["work_hours"] = work_hours
        save_settings(settings)
        await update.message.reply_text(f"Work hours set to {work_hours} hours.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_morning_meal_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter breakfast time in minutes:")
    return SETTING_MORNING_MEAL

async def update_morning_meal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        morning_meal = int(update.message.text)
        settings = load_settings()
        settings["morning_meal"] = morning_meal
        save_settings(settings)
        await update.message.reply_text(f"Breakfast time set to {morning_meal} minutes.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_evening_meal_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter dinner time in minutes:")
    return SETTING_EVENING_MEAL

async def update_evening_meal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        evening_meal = int(update.message.text)
        settings = load_settings()
        settings["evening_meal"] = evening_meal
        save_settings(settings)
        await update.message.reply_text(f"Dinner time set to {evening_meal} minutes.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_short_break_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter short break time in minutes:")
    return SETTING_SHORT_BREAK

async def update_short_break(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        short_break = int(update.message.text)
        settings = load_settings()
        settings["short_break"] = short_break
        save_settings(settings)
        await update.message.reply_text(f"Short break time set to {short_break} minutes.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_sleep_time_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter sleep time in hours:")
    return SETTING_SLEEP_TIME

async def update_sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        sleep_time = int(update.message.text)
        settings = load_settings()
        settings["sleep_time"] = sleep_time
        save_settings(settings)
        await update.message.reply_text(f"Sleep time set to {sleep_time} hours.")
    except ValueError:
        await update.message.reply_text("Please enter a numeric value.")

    return await settings_menu(update, context)

async def update_work_start_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter work start time (HH:MM format):")
    return SETTING_WORK_START

async def update_work_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    work_start = update.message.text.strip()

    import re
    if not re.match(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$", work_start):
        await update.message.reply_text("Invalid format. Please use HH:MM format (e.g., 09:00).")
        return SETTING_WORK_START

    settings = load_settings()
    settings["work_start"] = work_start
    save_settings(settings)
    await update.message.reply_text(f"Work start time set to {work_start}.")

    return await settings_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_text = (
        "Help using the bot:\n\n"
        "📋 My Schedule - shows your daily schedule\n"
        "⚙️ Settings - change schedule settings\n"
        "📱 Contacts - contact the administrator\n"
        "❓ Help - show this message\n\n"
        "Commands:\n"
        "/start - start interacting with the bot\n"
        "/admin - access the admin panel\n"
        "/help - show this help message"
    )
    await update.message.reply_text(help_text)
    return MAIN_MENU

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "To contact the administrator:\n"
        "Telegram: @admin_username\n" # Change this
        "Email: admin@example.com"   # Change this
    )
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Action cancelled.")
    user_id = update.effective_user.id
    users = load_users()
    if str(user_id) in users["authorized_users"]:
         keyboard = [
            ["📋 My Schedule", "⚙️ Settings"],
            ["📱 Contacts", "❓ Help"]
         ]
         reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
         await update.message.reply_text(
            "Main menu.",
            reply_markup=reply_markup
         )
         return MAIN_MENU
    else:
         await update.message.reply_text("Use /start to begin interacting with the bot.")
         return ConversationHandler.END

def main() -> None:
    # IMPORTANT: Replace "YOUR_BOT_TOKEN" with your actual Bot Token
    application = Application.builder().token("7795562395:AAFtIpNFBSCP8vSQv4j5iUxNoAOFcvWn6Ow").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("admin", admin_command)],
        states={
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
            MAIN_MENU: [
                MessageHandler(filters.Regex("^📋 My Schedule$"), show_schedule),
                MessageHandler(filters.Regex("^⚙️ Settings$"), settings_menu),
                MessageHandler(filters.Regex("^⚙️ Schedule Settings$"), settings_menu),
                MessageHandler(filters.Regex("^📱 Contacts$"), contacts),
                MessageHandler(filters.Regex("^❓ Help$"), help_command),
                MessageHandler(filters.Regex("^📊 Manage Users$"), manage_users),
                MessageHandler(filters.Regex("^🔙 Back$"), start), # General handler for Back button
            ],
            SETTINGS: [
                MessageHandler(filters.Regex("^🍽️ Lunch$"), update_meal_time_prompt),
                MessageHandler(filters.Regex("^☕ Break$"), update_break_time_prompt),
                MessageHandler(filters.Regex("^⏰ Work Hours$"), update_work_hours_prompt),
                MessageHandler(filters.Regex("^🍳 Breakfast$"), update_morning_meal_prompt),
                MessageHandler(filters.Regex("^🍲 Dinner$"), update_evening_meal_prompt),
                MessageHandler(filters.Regex("^🧘‍♂️ Short Break$"), update_short_break_prompt),
                MessageHandler(filters.Regex("^😴 Sleep Time$"), update_sleep_time_prompt),
                MessageHandler(filters.Regex("^🏢 Work Start$"), update_work_start_prompt),
                MessageHandler(filters.Regex("^🔙 Back$"), start), # Return to main menu for regular users
            ],
            SETTING_MEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_meal_time)],
            SETTING_BREAK: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_break_time)],
            SETTING_WORK_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_work_hours)],
            SETTING_MORNING_MEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_morning_meal)],
            SETTING_EVENING_MEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_evening_meal)],
            SETTING_SHORT_BREAK: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_short_break)],
            SETTING_SLEEP_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_sleep_time)],
            SETTING_WORK_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_work_start)],
            MANAGE_USERS: [
                MessageHandler(filters.Regex("^➕ Add User$"), add_user_prompt),
                MessageHandler(filters.Regex("^➖ Remove User$"), remove_user_prompt),
                 # Back should return to the admin panel menu (state after check_password)
                 # Currently returns to re-enter password, or could go to a specific ADMIN_MENU state
                MessageHandler(filters.Regex("^🔙 Back$"), check_password),
            ],
            ADDING_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user)],
            REMOVING_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_user)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == "__main__":
    main()