import aiohttp
import asyncio
import json
from typing import Optional

async def translate_text(text: str, target_lang: str = "ru", source_lang: str = "en") -> str:
    """Асинхронно переводит текст с сохранением структуры"""
    if not text or len(text.strip()) == 0:
        return ""
    
    # Если текст короткий или уже содержит перевод, возвращаем как есть
    if len(text.strip()) < 3 or '💬' in text:
        return text
    
    # API endpoints для перевода
    apis = [
        {
            "url": "https://translate.googleapis.com/translate_a/single",
            "params": {
                "client": "gtx",
                "sl": source_lang,
                "tl": target_lang,
                "dt": "t",
                "q": text
            },
            "method": "GET"
        },
        {
            "url": "https://api.mymemory.translated.net/get",
            "params": {
                "q": text,
                "langpair": f"{source_lang}|{target_lang}"
            },
            "method": "GET"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for api in apis:
            try:
                if api["method"] == "GET":
                    async with session.get(
                        api["url"], 
                        params=api["params"], 
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if "googleapis" in api["url"]:
                                if result and len(result) > 0 and len(result[0]) > 0:
                                    translated = "".join([part[0] for part in result[0] if part[0]])
                                    return translated
                            elif "mymemory" in api["url"]:
                                if "responseData" in result and "translatedText" in result["responseData"]:
                                    return result["responseData"]["translatedText"]
                else:
                    async with session.post(
                        api["url"], 
                        data=api["params"], 
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            # Обработка ответа для POST API
                            return text
            except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError):
                continue
    
    return text