from telegram import Bot
from telegram.error import TelegramError
from playwright.async_api import async_playwright
import asyncio
import json
from datetime import datetime
import textwrap
from telegram.constants import ParseMode
import re
from token_id import  TOKEN_BOT,CHAT_ID
seen_tokens = set()
# Твой токен бота
TELEGRAM_API_TOKEN = TOKEN_BOT()

# ID чата или канала для отправки сообщений
TELEGRAM_CHAT_ID = CHAT_ID()

bot = Bot(token=TELEGRAM_API_TOKEN)



def extract_socials(extensions: dict, uri: str):
    socials = {
        "website": extensions.get("website") or "",
        "twitter": extensions.get("twitter") or "",
        "telegram": extensions.get("telegram") or "",
        "discord": ""
    }

    # Поиск ссылок в uri если их нет в extensions
    if uri:
        if not socials["website"]:
            website_match = re.search(r'(https?://[^\s"]+\.[a-z]{2,})', uri)
            if website_match:
                socials["website"] = website_match.group(1)

        if not socials["twitter"]:
            twitter_match = re.search(r'(https?://(twitter\.com|x\.com)/[^\s"/]+)', uri)
            if twitter_match:
                socials["twitter"] = twitter_match.group(1)

        if not socials["telegram"]:
            telegram_match = re.search(r'(https?://t\.me/[^\s"/]+)', uri)
            if telegram_match:
                socials["telegram"] = telegram_match.group(1)

        discord_match = re.search(r'(https?://(discord\.gg|discord\.com/invite)/[^\s"/]+)', uri)
        if discord_match:
            socials["discord"] = discord_match.group(1)

    return socials






async def send_to_telegram(message: str):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except TelegramError as e:
        print(f"[ERROR] Ошибка при отправке в Telegram: {e}")

async def intercept_axiom_ws(page):
    async def on_websocket(ws):
        print(f"[INFO] Подключен к WebSocket: {ws.url}")

        def format_new_token(token: dict, website, twitter, telegram, discord) -> str:
            # Форматирование информации о токене
            name = token.get("token_name") or "Unknown"
            ticker = token.get("token_ticker") or "???"
            address = token.get("pair_address") or "N/A"
            token_address = token.get("token_address") or "N/A"
            deployer = token.get("deployer_address") or "N/A"
            protocol = token.get("protocol") or "N/A"
            signature = token.get("signature") or "N/A"
            supply = token.get("supply")
            liquidity_sol = token.get("initial_liquidity_sol")
            liquidity_token = token.get("initial_liquidity_token")
            protocol_details = token.get("protocol_details", {})
            program = protocol_details.get("tokenProgram") or "N/A"
            fees = protocol_details.get("tradeFeeRate") or "N/A"

            '''website = token.get("website") or "N/A"
            twitter = token.get("twitter") or "N/A"
            telegram = token.get("telegram") or "N/A"
            discord = token.get("discord") or "N/A"'''

            created_time = token.get("created_at") or "N/A"
            time_to_trade = token.get("open_trading") or "N/A"
            if str(fees) != "N/A":
                fees = fees / 10000


            created_at_dt = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            open_trading_dt = datetime.strptime(time_to_trade, "%Y-%m-%dT%H:%M:%S.%fZ")
            if open_trading_dt < created_at_dt:
                time_difference = "Торговля уже началась"
            else:
                time_difference = open_trading_dt - created_at_dt
                time_difference = time_difference.total_seconds()

            program_of_token = "N/A"
            if program == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                program_of_token = "SPL Token Program"
            elif program == "TokenzQdNwGdsTbmPa3qzYjDdyCjTiMQuYzcuEGoVY":
                program_of_token = "Token 2022 Program"

            def fmt_or_na(value, fmt):
                return fmt.format(value) if value is not None else "N/A"

            message = f"""
            <b>📢 Новая пара на рынке!</b>
            ━━━━━━━━━━━━━━━━━━━━━━━
            📛 <b>Название:</b> {name} (<b>${ticker}</b>)\n
            🌐 <b>Адрес пары:</b> <code>{address}</code>\n
            🔗 <b>CA:</b> <code>{token_address}</code>\n
            🧑‍💻 <b>Деплойер:</b> <code>{deployer}</code>\n
            🧪 <b>Протокол:</b> {protocol}\n
            💻 <b>Программа:</b> {program_of_token}\n
            📦 <b>Эмиссия:</b> {fmt_or_na(supply, '{:,}')}\n
            💧 <b>Ликвидность:</b> {fmt_or_na(liquidity_sol, '{:.2f}')} SOL / {fmt_or_na(liquidity_token, '{:,}')} токенов\n
            🌐 <b>Сайт:</b> {website}\n
            📜 <b>Твиттер:</b> {twitter}\n
            🧪 <b>Телеграм:</b> {telegram}\n
            🔗 <b>Дискорд:</b> {discord}\n
            📦 <b>Комиссия:</b> {fees}%\n
            ⏰ <b>Время создания и начало торгов:</b> {created_time} ➝ {time_to_trade}\n
            ⏳ <b>До старта:</b> {time_difference}\n
            ━━━━━━━━━━━━━━━━━━━━━━━
            🔍 <a href="https://solscan.io/token/{token_address}#transactions">SolScan</a>\n
            📊 <a href="https://axiom.trade/meme/{token_address}">Axiom</a>
            """

            return textwrap.dedent(message)

        async def handle_frame(msg):
            try:
                # Декодируем и парсим сообщение
                if isinstance(msg, str):
                    data = json.loads(msg)
                elif isinstance(msg, bytes):
                    data = json.loads(msg.decode("utf-8"))
                elif isinstance(msg, dict):
                    data = msg
                else:
                    print("[INFO] Неизвестный тип сообщения:", type(msg))
                    return

                # Проверяем, что это новые пары
                if data.get("room") == "new_pairs":
                    content = data.get("content", {})
                    protocol = content.get("protocol")
                    protocol_details = content.get("protocol_details", {})
                    fees = protocol_details.get("tradeFeeRate") or "N/A"
                    program = protocol_details.get("tokenProgram") or "N/A"
                    program_of_token = "N/A"
                    if program == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                        program_of_token = "SPL Token Program"
                    elif program == "TokenzQdNwGdsTbmPa3qzYjDdyCjTiMQuYzcuEGoVY":
                        program_of_token = "Token 2022 Program"
                    created_time = content.get("created_at") or "N/A"
                    time_to_trade = content.get("open_trading") or "N/A"
                    created_at_dt = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                    open_trading_dt = datetime.strptime(time_to_trade, "%Y-%m-%dT%H:%M:%S.%fZ")
                    time_difference = open_trading_dt - created_at_dt
                    time_difference = time_difference.total_seconds()

                    # Извлекаем социальные сети из extensions
                    website = content.get("website", "N/A")
                    twitter = content.get("twitter", "N/A")
                    telegram = content.get("telegram", "N/A")
                    discord = content.get("discord", "N/A")

                    # Если значение в extensions отсутствует, проверяем в uri
                    uri = content.get("token_uri") # Проверяем, есть ли uri в данных
                    if uri:
                        # Используем регулярные выражения для поиска ссылок на социальные сети
                        if website == "N/A" and "website" in uri:
                            website_match = re.search(r"(https?://[^\s]+)", uri)
                            if website_match:
                                website = website_match.group(0)
                        if twitter == "N/A" and "twitter" in uri:
                            twitter_match = re.search(r"(https?://[^\s]+)", uri)
                            if twitter_match:
                                twitter = twitter_match.group(0)
                        if telegram == "N/A" and "telegram" in uri:
                            telegram_match = re.search(r"(https?://[^\s]+)", uri)
                            if telegram_match:
                                telegram = telegram_match.group(0)
                        if discord == "N/A" and "telegram" in uri:
                            discord_match = re.search(r"(https?://[^\s]+)", uri)
                            if discord_match:
                                discord = discord_match.group(0)

                    #ФИЛЬТР
                    '''if protocol == "Raydium V4" or protocol == "Raydium CPMM" and \
                        str(fees) != "N/A" and  fees / 10000 > 6 and \
                            program_of_token == "Token 2022 Program" and \
                                time_difference > 0:
                                    new_token_message = format_new_token(content)
                                    await send_to_telegram(new_token_message)  # Отправляем в Telegram'''
                    if protocol == "Raydium V4" or protocol == "Raydium CPMM":
                        new_token_message = format_new_token(content, website, twitter, telegram, discord)
                        await send_to_telegram(new_token_message)  # Отправляем в Telegram'''
            except Exception as e:
                print(f"[ERROR] Ошибка при обработке кадра: {e}")

        ws.on("framereceived", lambda msg: asyncio.create_task(handle_frame(msg)))


    page.on("websocket", on_websocket)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="state.json")
        page = await context.new_page()

        await intercept_axiom_ws(page)

        await page.goto("https://axiom.trade/pulse")
        print("[INFO] Авторизуйся вручную. После входа окно не закрывай.")
        await asyncio.sleep(60)

        await context.storage_state(path="state.json")
        print("[INFO] Состояние сессии сохранено в state.json")
        await asyncio.Future()

asyncio.run(main())
