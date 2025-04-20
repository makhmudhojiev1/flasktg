import os
import logging
import tempfile
import json
from flask import Flask, request, jsonify, render_template_string
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Dispatcher,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler
)
from dotenv import load_dotenv
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Configuration (previously config.py)
class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    SUPPORTED_LANGUAGES = ['en', 'ru', 'uz']
    DEFAULT_LANGUAGE = 'ru'
    REQUIRED_CHANNELS = ['@xtarjima', '@moshinabozorim_n']

# Locales (previously locales/*.json files, now as dictionaries)
LOCALES = {
    'en': {
        "welcome": "🔥 Hello! Welcome to Social Downloader Bot. You can download from:",
        "platforms": {
            "instagram": "Instagram - post and IGTV + audio",
            "tiktok": "TikTok - video without watermark + audio",
            "youtube": "YouTube - video and shorts + audio",
            "snapchat": "Snapchat - video without watermark + audio",
            "likee": "Likee - video without watermark + audio",
            "pinterest": "Pinterest - video and image without watermarks + audio",
            "threads": "Threads - video and image + audio"
        },
        "shazam_features": {
            "title": "Shazam Features:",
            "features": [
                "Song title or artist name",
                "Lyrics",
                "Voice message",
                "Video",
                "Audio",
                "Video message"
            ]
        },
        "instructions": "🚀 Send me a link to the video you want to download!\n😎 The bot also works in groups!",
        "language_changed": "Language changed to English",
        "processing": "🔍 Processing your link, please wait...",
        "error": "❌ An error occurred: {error}",
        "unsupported": "❌ Unsupported platform",
        "audio_recognizing": "🎵 Recognizing audio, please wait...",
        "subscribe_prompt": "📢 To use the bot, please subscribe to the following channels:",
        "subscribed_success": "✅ Thank you for subscribing! You can now use the bot.",
        "not_subscribed": "❌ You are not subscribed to all required channels. Please subscribe and try again.",
        "buttons": {
            "download": "📥 Download",
            "shazam": "🎵 Shazam",
            "settings": "⚙️ Settings",
            "help": "❓ Help",
            "back": "⬅️ Back",
            "check_subscription": "✅ Check Subscription"
        },
        "song": {
            "title": "Title",
            "artist": "Artist",
            "no_lyrics": "Lyrics not available",
            "not_recognized": "Song not recognized"
        }
    },
    'ru': {
        "welcome": "🔥 Здравствуйте! Добро пожаловать в Social Downloader Bot. Через бота можно скачать:",
        "platforms": {
            "instagram": "Instagram - пост и IGTV + аудио",
            "tiktok": "TikTok - видео без водяного знака + аудио",
            "youtube": "YouTube - Видео и shorts + аудио",
            "snapchat": "Snapchat - видео без водяного знака + аудио",
            "likee": "Likee - видео без водяного знака + аудио",
            "pinterest": "Pinterest - видео и изображение без водяных знаков + аудио",
            "threads": "Threads - видео и изображение + аудио"
        },
        "shazam_features": {
            "title": "Функция Шазама:",
            "features": [
                "Название песни или имя исполнителя",
                "Текст песни",
                "Голосовое сообщение",
                "Видео",
                "Аудио",
                "Видео сообщение"
            ]
        },
        "instructions": "🚀 Отправьте мне ссылку на видео, которое хотите скачать!\n😎 Бот тоже может работать в группах!",
        "language_changed": "Язык изменен на русский",
        "processing": "🔍 Обрабатываю вашу ссылку, пожалуйста подождите...",
        "error": "❌ Произошла ошибка: {error}",
        "unsupported": "❌ Неподдерживаемая платформа",
        "audio_recognizing": "🎵 Распознаю аудио, пожалуйста подождите...",
        "subscribe_prompt": "📢 Для использования бота, пожалуйста, подпишитесь на следующие каналы:",
        "subscribed_success": "✅ Спасибо за подписку! Теперь вы можете использовать бота.",
        "not_subscribed": "❌ Вы не подписаны на все необходимые каналы. Пожалуйста, подпишитесь и попробуйте снова.",
        "buttons": {
            "download": "📥 Скачать",
            "shazam": "🎵 Shazam",
            "settings": "⚙️ Настройки",
            "help": "❓ Помощь",
            "back": "⬅️ Назад",
            "check_subscription": "✅ Проверить подписку"
        },
        "song": {
            "title": "Название",
            "artist": "Исполнитель",
            "no_lyrics": "Текст песни недоступен",
            "not_recognized": "Песня не распознана"
        }
    },
    'uz': {
        "welcome": "🔥 Salom! Social Downloader Botga xush kelibsiz. Bot orqali yuklab olishingiz mumkin:",
        "platforms": {
            "instagram": "Instagram - post va IGTV + audio",
            "tiktok": "TikTok - suv belgisi yo'q video + audio",
            "youtube": "YouTube - video va shorts + audio",
            "snapchat": "Snapchat - suv belgisi yo'q video + audio",
            "likee": "Likee - suv belgisi yo'q video + audio",
            "pinterest": "Pinterest - suv belgisiz video va rasm + audio",
            "threads": "Threads - video va rasm + audio"
        },
        "shazam_features": {
            "title": "Shazam funksiyalari:",
            "features": [
                "Qo‘shiq nomi yoki ijrochi ismi",
                "Qo‘shiq matni",
                "Ovozli xabar",
                "Video",
                "Audio",
                "Video xabar"
            ]
        },
        "instructions": "🚀 Yuklamoqchi bo'lgan video havolasini menga yuboring!\n😎 Bot guruhlarda ham ishlaydi!",
        "language_changed": "Til o'zbekchaga o'zgartirildi",
        "processing": "🔍 Havolangizni qayta ishlashmoqda, iltimos kuting...",
        "error": "❌ Xatolik yuz berdi: {error}",
        "unsupported": "❌ Qo'llab-quvvatlanmaydigan platforma",
        "audio_recognizing": "🎵 Audiyni aniqlashmoqda, iltimos kuting...",
        "subscribe_prompt": "📢 Botdan foydalanish3e3e dalanish uchun quyidagi kanallarga obuna bo'ling:",
        "subscribed_success": "✅ Obuna bo'lganingiz uchun rahmat! Endi botdan foydalanishingiz mumkin.",
        "not_subscribed": "❌ Siz barcha kerakli kanallarga obuna bo'lmagansiz. Iltimos, obuna bo'lib qayta urinib ko'ring.",
        "buttons": {
            "download": "📥 Yuklab olish",
            "shazam": "🎵 Shazam",
            "settings": "⚙️ Sozlamalar",
            "help": "❓ Yordam",
            "back": "⬅️ Orqaga",
            "check_subscription": "✅ Obunani tekshirish"
        },
        "song": {
            "title": "Nomi",
            "artist": "Ijrochi",
            "no_lyrics": "Matn mavjud emas",
            "not_recognized": "Qo‘shiq aniqlanmadi"
        }
    }
}

# Translation helpers (previously utils/helpers.py)
def get_translation(lang, key):
    """Get translation for a key in specified language."""
    keys = key.split('.')
    value = LOCALES.get(lang, LOCALES.get(Config.DEFAULT_LANGUAGE, {}))
    
    for k in keys:
        value = value.get(k, {})
        if not value:
            return key  # Return key if translation not found
    
    return value if isinstance(value, str) else key

def get_user_language(user_id):
    """Get user's preferred language."""
    return Config.DEFAULT_LANGUAGE  # Default to 'ru' since Redis is removed

def set_user_language(user_id, lang):
    """Set user's preferred language."""
    if lang in Config.SUPPORTED_LANGUAGES:
        return True
    return False

def check_subscription(bot: Bot, user_id: int) -> bool:
    """Check if user is subscribed to all required channels."""
    for channel in Config.REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logger.error(f"Error checking subscription for {channel}: {e}")
            return False
    return True

# Keyboard helpers (previously keyboards.py)
def language_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
            InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru'),
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='lang_uz')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def main_menu_keyboard(lang='ru'):
    keyboard = [
        [InlineKeyboardButton(get_translation(lang, 'buttons.download'), callback_data='download')],
        [InlineKeyboardButton(get_translation(lang, 'buttons.shazam'), callback_data='shazam')],
        [InlineKeyboardButton(get_translation(lang, 'buttons.settings'), callback_data='settings')],
        [InlineKeyboardButton(get_translation(lang, 'buttons.help'), callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def platform_keyboard(lang='ru'):
    keyboard = [
        [InlineKeyboardButton("Instagram", callback_data='platform_instagram')],
        [InlineKeyboardButton("TikTok", callback_data='platform_tiktok')],
        [InlineKeyboardButton("YouTube", callback_data='platform_youtube')],
        [InlineKeyboardButton("Snapchat", callback_data='platform_snapchat')],
        [InlineKeyboardButton("Likee", callback_data='platform_likee')],
        [InlineKeyboardButton("Pinterest", callback_data='platform_pinterest')],
        [InlineKeyboardButton("Threads", callback_data='platform_threads')],
        [InlineKeyboardButton(get_translation(lang, 'buttons.back'), callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

def subscription_keyboard(lang='ru'):
    """Keyboard with links to required channels and a check subscription button."""
    keyboard = [
        [InlineKeyboardButton("📢 Join @xtarjima", url="https://t.me/xtarjima")],
        [InlineKeyboardButton("📢 Join @moshinabozorim_n", url="https://t.me/moshinabozorim_n")],
        [InlineKeyboardButton(get_translation(lang, 'buttons.check_subscription'), callback_data='check_subscription')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Decorators (previously utils/decorators.py)
def send_typing_action(func):
    """Sends typing action while processing func."""
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action='typing'
        )
        return func(update, context, *args, **kwargs)
    return command_func

# Downloaders (previously utils/downloaders.py)
def download_content(url):
    """Placeholder for downloading content from a URL."""
    # Implement actual download logic using pytube, youtube-dl, etc.
    return {'type': 'video', 'content': 'path_or_url_to_content', 'caption': 'Downloaded content'}

# Shazam (previously utils/shazam.py)
def recognize_audio(file_path):
    """Placeholder for audio recognition using Shazam-like functionality."""
    # Implement actual audio recognition logic
    return {'title': 'Song Title', 'artist': 'Artist Name', 'lyrics': 'Lyrics not available'}

# Templates (previously templates/result.html, now as a string)
RESULT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Social Downloader Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Poppins', sans-serif;
        }
        .gradient-bg {
            background: linear-gradient(135deg, #6B7280, #1F2937);
        }
        .hover-scale {
            transition: transform 0.3s ease;
        }
        .hover-scale:hover {
            transform: scale(1.05);
        }
        .section-divider {
            border-top: 1px solid #4B5563;
            margin: 2rem 0;
        }
    </style>
</head>
<body class="gradient-bg text-gray-100">
    <!-- Header Section -->
    <header class="bg-gray-900 shadow-lg">
        <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 text-center">
            <h1 class="text-4xl font-bold text-white">Social Downloader Bot</h1>
            <p class="mt-2 text-lg text-gray-300">Your Ultimate Tool for Downloading Social Media Content</p>
            <a href="https://t.me/your_bot_username" target="_blank" class="mt-4 inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 hover-scale">
                Start Using the Bot
            </a>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <!-- About Section -->
        <section id="about" class="mb-12">
            <h2 class="text-3xl font-semibold text-white mb-6">About the Bot</h2>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
                <p class="text-gray-300 mb-4">
                    The <strong>Social Downloader Bot</strong> is a powerful Telegram bot designed to help you download content from your favorite social media platforms with ease. Whether it's videos, images, or audio, our bot supports a wide range of platforms, including:
                </p>
                <ul class="list-disc list-inside text-gray-300 mb-4">
                    <li>Instagram (Posts, IGTV, and Audio)</li>
                    <li>TikTok (Videos without Watermarks)</li>
                    <li>YouTube (Videos and Shorts)</li>
                    <li>Snapchat (Videos without Watermarks)</li>
                    <li>Likee (Videos without Watermarks)</li>
                    <li>Pinterest (Videos and Images)</li>
                    <li>Threads (Videos and Images)</li>
                </ul>
                <p class="text-gray-300">
                    Additionally, our bot features a <strong>Shazam-like audio recognition</strong> tool that can identify songs from voice messages, audio files, or videos, providing you with song titles, artists, and lyrics when available. The bot is multilingual, supporting English, Russian, and Uzbek, and works seamlessly in both private chats and group conversations.
                </p>
            </div>
        </section>

        <div class="section-divider"></div>

        <!-- Features Section -->
        <section id="features" class="mb-12">
            <h2 class="text-3xl font-semibold text-white mb-6">Key Features</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover-scale">
                    <h3 class="text-xl font-semibold text-indigo-400 mb-2">Multi-Platform Support</h3>
                    <p class="text-gray-300">Download content from Instagram, TikTok, YouTube, Snapchat, Likee, Pinterest, and Threads effortlessly.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover-scale">
                    <h3 class="text-xl font-semibold text-indigo-400 mb-2">Audio Recognition</h3>
                    <p class="text-gray-300">Identify songs with our Shazam-like feature, including song titles, artists, and lyrics.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover-scale">
                    <h3 class="text-xl font-semibold text-indigo-400 mb-2">Multilingual Interface</h3>
                    <p class="text-gray-300">Use the bot in English, Russian, or Uzbek, with easy language switching.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover-scale">
                    <h3 class="text-xl font-semibold text-indigo-400 mb-2">Group Compatibility</h3>
                    <p class="text-gray-300">Works in both private chats and Telegram groups for maximum flexibility.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover-scale">
                    <h3 class="text-xl font-semibold text-indigo-400 mb-2">Watermark-Free Downloads</h3>
                    <p class="text-gray-300">Get clean, watermark-free videos from platforms like TikTok and Snapchat.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover-scale">
                    <h3 class="text-xl font-semibold text-indigo-400 mb-2">User-Friendly Interface</h3>
                    <p class="text-gray-300">Navigate easily with intuitive menus and clear instructions.</p>
                </div>
            </div>
        </section>

        <div class="section-divider"></div>

        <!-- Privacy Policy Section -->
        <section id="privacy" class="mb-12">
            <h2 class="text-3xl font-semibold text-white mb-6">Privacy Policy</h2>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg">
                <p class="text-gray-300 mb-4">
                    At Social Downloader Bot, we are committed to protecting your privacy. Here's how we handle your data:
                </p>
                <ul class="list-disc list-inside text-gray-300 mb-4">
                    <li><strong>Data Collection</strong>: We only collect the minimum necessary information, such as your Telegram user ID, to provide bot functionality and improve user experience.</li>
                    <li><strong>Data Usage</strong>: Your data is used solely to process your requests (e.g., downloading content or recognizing audio) and to maintain your language preferences.</li>
                    <li><strong>Data Storage</strong>: We do not store personal data beyond what is required for the bot to function. Any temporary files (e.g., audio for recognition) are deleted immediately after processing.</li>
                    <li><strong>Third-Party Sharing</strong>: We do not share your data with third parties, except as required to interact with Telegram's API or to comply with legal obligations.</li>
                    <li><strong>Security</strong>: We implement industry-standard security measures to protect your data from unauthorized access.</li>
                    <li><strong>User Rights</strong>: You can contact us to request information about your data or to request its deletion.</li>
                </ul>
                <p class="text-gray-300">
                    By using the Social Downloader Bot, you agree to this privacy policy. For any questions or concerns, please contact our support team via Telegram.
                </p>
            </div>
        </section>

        <div class="section-divider"></div>

        <!-- Contact Section -->
        <section id="contact" class="mb-12">
            <h2 class="text-3xl font-semibold text-white mb-6">Get in Touch</h2>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg text-center">
                <p class="text-gray-300 mb-4">
                    Have questions or need help? Reach out to us on Telegram or join our community channels for updates and support.
                </p>
                <div class="flex justify-center space-x-4">
                    <a href="https://t.me/your_bot_username" target="_blank" class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 hover-scale">Contact Support</a>
                    <a href="https://t.me/xtarjima" target="_blank" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 hover-scale">Join @xtarjima</a>
                    <a href="https://t.me/moshinabozorim_n" target="_blank" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 hover-scale">Join @moshinabozorim_n</a>
                </div>
            </div>
        </section>
    </main>

    <!-- Footer Section -->
    <footer class="bg-gray-900 py-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p class="text-gray-400">© 2025 Social Downloader Bot. All rights reserved.</p>
            <p class="text-gray-400 mt-2">Built with ❤️ for Telegram users worldwide.</p>
        </div>
    </footer>
</body>
</html>
"""

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize bot
bot = Bot(token=app.config['TELEGRAM_TOKEN'])

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation handler
SELECTING_ACTION, SELECTING_PLATFORM, PROCESSING_LINK = range(3)

def check_subscription_middleware(func):
    """Middleware to check if user is subscribed to required channels."""
    def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        lang = get_user_language(user_id)
        
        if not check_subscription(bot, user_id):
            update.message.reply_text(
                get_translation(lang, 'subscribe_prompt'),
                reply_markup=subscription_keyboard(lang)
            )
            return None
        return func(update, context, *args, **kwargs)
    return wrapper

@send_typing_action
@check_subscription_middleware
def start(update, context):
    """Send welcome message with language selection."""
    user_id = update.effective_user.id
    lang = get_user_language(user_id) or app.config['DEFAULT_LANGUAGE']
    
    update.message.reply_text(
        get_translation(lang, 'welcome'),
        reply_markup=main_menu_keyboard(lang)
    )
    return SELECTING_ACTION

@send_typing_action
def language_command(update, context):
    """Change language command."""
    update.message.reply_text(
        "🌍 Please select your language:",
        reply_markup=language_keyboard()
    )

def language_callback(update, context):
    """Handle language selection callback."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = query.data.split('_')[1]
    
    set_user_language(user_id, lang)
    query.answer()
    query.edit_message_text(
        text=get_translation(lang, 'language_changed'),
        reply_markup=main_menu_keyboard(lang)
    )
    return SELECTING_ACTION

def check_subscription_callback(update, context):
    """Handle check subscription button callback."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_user_language(user_id) or app.config['DEFAULT_LANGUAGE']
    
    if check_subscription(bot, user_id):
        query.edit_message_text(
            text=get_translation(lang, 'subscribed_success'),
            reply_markup=main_menu_keyboard(lang)
        )
        query.answer()
        return SELECTING_ACTION
    else:
        query.edit_message_text(
            text=get_translation(lang, 'not_subscribed'),
            reply_markup=subscription_keyboard(lang)
        )
        query.answer()
        return None

@send_typing_action
@check_subscription_middleware
def main_menu_callback(update, context):
    """Handle main menu callbacks."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_user_language(user_id) or app.config['DEFAULT_LANGUAGE']
    action = query.data
    
    if action == 'download':
        query.edit_message_text(
            text="📥 Select platform to download from:",
            reply_markup=platform_keyboard(lang)
        )
        return SELECTING_PLATFORM
    elif action == 'shazam':
        query.edit_message_text(
            text=get_translation(lang, 'shazam_features.title') + "\n\n" +
                 "\n".join(get_translation(lang, 'shazam_features.features')) + 
                 "\n\n🎤 Send me an audio message to recognize music!"
        )
        return PROCESSING_LINK
    elif action == 'settings':
        query.edit_message_text(
            text="⚙️ Settings",
            reply_markup=language_keyboard()
        )
    elif action == 'help':
        query.edit_message_text(
            text=get_translation(lang, 'instructions')
        )
    
    query.answer()
    return SELECTING_ACTION

@send_typing_action
@check_subscription_middleware
def handle_platform_selection(update, context):
    """Handle platform selection for download."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_user_language(user_id) or app.config['DEFAULT_LANGUAGE']
    platform = query.data.split('_')[1]
    
    query.edit_message_text(
        text=get_translation(lang, 'instructions'),
        reply_markup=main_menu_keyboard(lang)
    )
    query.answer()
    return PROCESSING_LINK

@send_typing_action
@check_subscription_middleware
def handle_message(update, context):
    """Handle incoming messages."""
    user_id = update.effective_user.id
    lang = get_user_language(user_id) or app.config['DEFAULT_LANGUAGE']
    message = update.message.text if update.message.text else None
    
    if message and any(domain in message for domain in ['instagram.com', 'tiktok.com', 'youtube.com', 'snapchat.com', 'likee.video', 'pinterest.com', 'threads.net']):
        update.message.reply_text(get_translation(lang, 'processing'))
        
        try:
            result = download_content(message)
            if result.get('error'):
                update.message.reply_text(get_translation(lang, 'error').format(error=result["error"]))
            else:
                send_content(update, result, lang)
        except Exception as e:
            logger.error(f"Error processing link: {e}")
            update.message.reply_text(get_translation(lang, 'error').format(error=str(e)))
    
    elif update.message.voice or update.message.audio:
        update.message.reply_text(get_translation(lang, 'audio_recognizing'))
        
        try:
            file = update.message.voice or update.message.audio
            file_id = file.file_id
            file = bot.get_file(file_id)
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f'temp_audio_{file_id}.ogg')
            file.download(temp_file)
            
            result = recognize_audio(temp_file)
            os.remove(temp_file)
            
            if result:
                response = (f"🎶 {get_translation(lang, 'song.title')}: {result['title']}\n"
                           f"🎤 {get_translation(lang, 'song.artist')}: {result['artist']}\n\n"
                           f"{result.get('lyrics', get_translation(lang, 'song.no_lyrics'))}")
                update.message.reply_text(response)
            else:
                update.message.reply_text(get_translation(lang, 'song.not_recognized'))
        except Exception as e:
            logger.error(f"Error recognizing audio: {e}")
            update.message.reply_text(get_translation(lang, 'error').format(error=str(e)))
    else:
        update.message.reply_text(get_translation(lang, 'instructions'))

def send_content(update, content, lang):
    """Send downloaded content with appropriate method."""
    if content['type'] == 'video':
        update.message.reply_video(
            video=content['content'],
            caption=content.get('caption', ''),
            reply_markup=main_menu_keyboard(lang)
        )
    elif content['type'] == 'audio':
        update.message.reply_audio(
            audio=content['content'],
            caption=content.get('caption', ''),
            reply_markup=main_menu_keyboard(lang)
        )
    elif content['type'] == 'photo':
        update.message.reply_photo(
            photo=content['content'],
            caption=content.get('caption', ''),
            reply_markup=main_menu_keyboard(lang)
        )

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def setup_dispatcher(dp):
    """Set up the command handlers."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(main_menu_callback),
                CallbackQueryHandler(language_callback, pattern='^lang_'),
                CallbackQueryHandler(check_subscription_callback, pattern='^check_subscription$')
            ],
            SELECTING_PLATFORM: [
                CallbackQueryHandler(handle_platform_selection),
                CallbackQueryHandler(start, pattern='^back$')
            ],
            PROCESSING_LINK: [
                MessageHandler(Filters.text & ~Filters.command, handle_message),
                MessageHandler(Filters.voice | Filters.audio, handle_message)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('lang', language_command))
    dp.add_error_handler(error)
    return dp

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook view that receives updates from Telegram."""
    update = Update.de_json(request.get_json(force=True), bot)
    dp = Dispatcher(bot, None, workers=0)
    dp = setup_dispatcher(dp)
    dp.process_update(update)
    return jsonify({'status': 'ok'})

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    """Set webhook for Telegram bot."""
    webhook_url = f"{os.getenv('VERCEL_URL', 'https://your-vercel-app.vercel.app')}/webhook"
    s = bot.set_webhook(webhook_url)
    if s:
        return f"Webhook setup ok: {webhook_url}"
    else:
        return "Webhook setup failed"

@app.route('/')
def index():
    """Render the result.html template."""
    return render_template_string(RESULT_HTML)

if __name__ == '__main__':
    app.run(debug=True)
