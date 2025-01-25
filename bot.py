from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
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

# Функция, которая будет запускаться при вводе команды /add
async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Начнем пошаговый процесс добавления
    await update.message.reply_text("Введите слово для добавления:")

    # Устанавливаем флаг, что мы ожидаем слово
    context.user_data['step'] = 'word'

# Обработчик для сообщений, когда мы ожидаем слово, транскрипцию и перевод
async def handle_add_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('step')

    if step == 'word':
        context.user_data['word'] = update.message.text
        await update.message.reply_text("Введите транскрипцию для слова:")
        context.user_data['step'] = 'transcription'

    elif step == 'transcription':
        context.user_data['transcription'] = update.message.text
        await update.message.reply_text("Введите перевод для слова:")
        context.user_data['step'] = 'translation'

    elif step == 'translation':
        word = context.user_data.get('word')
        transcription = context.user_data.get('transcription')
        translation = update.message.text

        # Добавляем слово в словарь
        words_dict[word] = {"translation": translation, "transcription": transcription}
        save_words(words_dict)

        await update.message.reply_text(f"Слово '{word}' добавлено с транскрипцией '{transcription}' и переводом '{translation}'.")

        # Сбрасываем шаг
        context.user_data['step'] = None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Используйте команды:\n"
                                    "/add - добавить новое слово\n"
                                    "/delete слово - удалить слово\n"
                                    "/list - список слов")

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
        await update.message.reply_text("Неверный формат. Используйте:\n/delete слово")

# Команда /list
async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if words_dict:
        response = "Ваши слова:\n"
        for word, info in words_dict.items():
            response += f"{word} - {info['translation']} ({info['transcription']})\n"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("Список слов пуст.")

# Функция main
def main():
    # Создаём приложение
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_word))
    application.add_handler(CommandHandler("delete", delete_word))
    application.add_handler(CommandHandler("list", list_words))

    # Добавляем обработчик для ввода
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_input))

    # Запуск приложения
    application.run_polling()

if __name__ == "__main__":
    main()
