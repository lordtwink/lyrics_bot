import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold

from genius_scraper import GeniusScraper
from config import TELEGRAM_BOT_TOKEN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


scraper = GeniusScraper()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_message = """
🎵 Добро пожаловать в Lyrics Bot!

Я помогу найти текст любой песни с Genius.com

Как использовать:
• Просто напишите название песни и исполнителя
• Например: "Bohemian Rhapsody Queen" или "Марафеты Дэббэквуд"

Команды:
/start - показать это сообщение
/help - справка
    """
    await message.answer(welcome_message)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_message = """
📖 Справка по использованию бота

🔍 Поиск текста песни:
Просто отправьте название песни и исполнителя в любом формате.

Примеры запросов:
• "Bohemian Rhapsody Queen"
• "Марафеты Дэббэквуд"
• "Баратриум Анакондаз"
• "Hotel California Eagles"

⚠️ Важно:
• Указывайте название песни и исполнителя для лучшего поиска
• Бот ищет на сайте Genius.com
• Если песня не найдена, попробуйте изменить запрос

🔄 Если бот не отвечает, попробуйте позже - сайт может быть временно недоступен.
    """
    await message.answer(help_message)

@dp.message(F.text)
async def search_lyrics(message: Message):

    query = message.text.strip()
    
    if not query:
        await message.answer("Пожалуйста, укажите название песни и исполнителя.")
        return
    
    try:
        # Отправляем сообщение о поиске
        search_msg = await message.answer("🔍 Ищу текст песни...")
        
        # Ищем песню (синхронный вызов)
        result, error = scraper.search_song(query)
        
        if error:
            await search_msg.edit_text(f"❌ {error}")
            return
        
        if not result:
            await search_msg.edit_text("❌ Песня не найдена. Попробуйте изменить запрос.")
            return
        

        title = result['title']
        lyrics = result['lyrics']
        url = result['url']
        

        response_text = f"🎵 {hbold(title)}\n\n{lyrics}\n\n🔗 {url}"
        

        max_length = 4000
        if len(response_text) > max_length:
            # Разбиваем на части
            parts = []
            current_part = f"🎵 {hbold(title)}\n\n"
            
            lines = lyrics.split('\n')
            for line in lines:
                if len(current_part + line + '\n') > max_length and current_part != f"🎵 {hbold(title)}\n\n":
                    parts.append(current_part)
                    current_part = line + '\n'
                else:
                    current_part += line + '\n'
            
            if current_part:
                parts.append(current_part)
            

            await search_msg.delete()
            

            for i, part in enumerate(parts):
                if i == 0:
                    await message.answer(part, parse_mode=ParseMode.HTML)
                else:
                    await message.answer(f"📄 Продолжение {i+1}:\n{part}", parse_mode=ParseMode.HTML)
                await asyncio.sleep(0.3)
            
            await message.answer(f"🔗 Полный текст: {url}")
        else:
            await search_msg.edit_text(response_text, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        try:
            await search_msg.edit_text("❌ Произошла ошибка при поиске. Попробуйте позже.")
        except:
            await message.answer("❌ Произошла ошибка при поиске. Попробуйте позже.")

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    logger.error(f"Ошибка: {exception}")
    if update.message:
        await update.message.answer("❌ Произошла ошибка. Попробуйте позже.")
    return True

async def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Ошибка: Не указан токен бота!")
        print("Создайте файл .env и добавьте TELEGRAM_BOT_TOKEN=your_token_here")
        return
    

    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
