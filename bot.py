import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "7795562395:AAFtIpNFBSCP8vSQv4j5iUxNoAOFcvWn6Ow"
CHANNEL_IDS = [
    "-1002623602999",
    "-1002597949465",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Assalomu alaykum! Men kanalingiz uchun kontent yuborish botiman.\n"
        f"Menga yuborgan har qanday matn, rasm, audio va boshqa kontentlaringiz "
        f"quyidagi kanallarga yuboriladi:\n"
        f"{', '.join(CHANNEL_IDS)}"
    )


async def forward_to_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message

    sent_messages = []
    for channel_id in CHANNEL_IDS:
        try:
            if message.text:
                sent = await context.bot.send_message(
                    chat_id=channel_id,
                    text=message.text
                )
            elif message.photo:
                photo = message.photo[-1]  # Eng katta o'lchamdagi rasmni olish
                caption = message.caption if message.caption else ""
                sent = await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=photo.file_id,
                    caption=caption
                )
            elif message.voice:
                sent = await context.bot.send_voice(
                    chat_id=channel_id,
                    voice=message.voice.file_id,
                    caption=message.caption if message.caption else ""
                )
            elif message.audio:
                sent = await context.bot.send_audio(
                    chat_id=channel_id,
                    audio=message.audio.file_id,
                    caption=message.caption if message.caption else ""
                )
            elif message.video:
                sent = await context.bot.send_video(
                    chat_id=channel_id,
                    video=message.video.file_id,
                    caption=message.caption if message.caption else ""
                )
            elif message.document:
                sent = await context.bot.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id,
                    caption=message.caption if message.caption else ""
                )
            else:
                continue

            sent_messages.append(channel_id)
        except Exception as e:
            logging.error(f"Xabarni {channel_id} kanaliga yuborishda xatolik: {e}")

    if sent_messages:
        await message.reply_text(f"Sizning xabaringiz quyidagi kanallarga yuborildi: {', '.join(sent_messages)}")
    else:
        await message.reply_text("Xabaringizni hech qaysi kanalga yuborib bo'lmadi. Xatolik yuz berdi.")


def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND,
        forward_to_channels
    ))

    application.run_polling()


if __name__ == "__main__":
    main()
