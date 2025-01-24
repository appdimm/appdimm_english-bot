from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import random
import json
import os

# Файл для хранения слов
WORDS_FILE = "words.json"

# Загрузка слов из файла
def load_words():
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Сохранение слов в файл
def save_words(words):
    with open(WORDS_FILE, "w", encoding="utf-8") as file:
        json.dump(words, file, ensure_ascii=False, indent=4)

# Глобальный словарь слов
words_dict = load_words()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Используйте команды:\n"
                                    "/add слово перевод транскрипция - добавить слово\n"
                                    "/delete слово - удалить слово\n"
                                    "/list - список слов")

# Команда /add
async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, word, translation, transcription = update.message.text.split(maxsplit=3)
        words_dict[word] = {"translation": translation, "transcription": transcription}
        save_words(words_dict)
        await update.message.reply_text(f"Слово '{word}' добавлено.")
    except ValueError:
        await update.message.reply_text("Неверный формат. Используйте:\n"
                                        "/add слово перевод транскрипция")

# Команда /delete
async def delete_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, word = update.message.text.split(maxsplit=1)
        if word in words_dict:
            del words_dict[word]
            save_words(words_dict)
            await update.message.reply_text(f"Слово '{word}' удалено.")
        else:
            await update.message.reply_text(f"Слово '{word}' не найдено.")
    except ValueError:
        await update.message.reply_text("Неверный формат. Используйте:\n"
                                        "/delete слово")

# Команда /list
async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if words_dict:
        response = "Ваши слова:\n"
        for word, info in words_dict.items():
            response += f"{word} - {info['translation']} ({info['transcription']})\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Список слов пуст.")

# Обработка ответа на вопрос
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    word, correct_translation, transcription = data

    # Проверяем, правильный ли ответ
    selected_translation = query.data.split("|")[1]
    if selected_translation == correct_translation:
        await query.edit_message_text(f"Верно! {word} переводится как '{correct_translation}'.")
    else:
        await query.edit_message_text(f"Неверно. {word} переводится как '{correct_translation}'.")

# Обработка уровня сложности
async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Спасибо за ваш отзыв!")

# Вопрос пользователю
async def ask_question(context: ContextTypes.DEFAULT_TYPE):
    if not words_dict:
        return

    word, info = random.choice(list(words_dict.items()))
    translation = info['translation']
    transcription = info['transcription']

    # Генерируем варианты ответа
    all_translations = [w['translation'] for w in words_dict.values()]
    options = random.sample(all_translations, k=min(3, len(all_translations)))
    if translation not in options:
        options.append(translation)
    random.shuffle(options)

    # Генерируем кнопки
    buttons = [
        InlineKeyboardButton(text=opt, callback_data=f"{word}|{opt}|{transcription}")
        for opt in options
    ]
    reply_markup = InlineKeyboardMarkup.from_column(buttons)

    # Отправляем вопрос
    job = context.job
    await job.chat_data["chat"].send_message(
        text=f"Как переводится слово '{word}' ({transcription})?",
        reply_markup=reply_markup,
    )

# Функция main
def main():
    # Создаём приложение
    application = Application.builder().token("7704077017:AAFPiRoF7rHACYTjsneuva1ws76qj1MqIA0").build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_word))
    application.add_handler(CommandHandler("delete", delete_word))
    application.add_handler(CommandHandler("list", list_words))

    # Добавляем обработчики кнопок
    application.add_handler(CallbackQueryHandler(handle_answer, pattern=r"^[^|]+\|[^|]+\|[^|]+$"))
    application.add_handler(CallbackQueryHandler(handle_difficulty, pattern=r"^difficulty\|.*$"))

    # Настраиваем JobQueue
    async def on_startup(application):
        application.job_queue.run_repeating(ask_question, interval=1800, first=10)  # каждые 30 минут

    application.post_init = on_startup

    # Запуск приложения
    application.run_polling()


if __name__ == "__main__":
    main()
