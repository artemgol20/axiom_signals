from playwright.async_api import async_playwright
import asyncio
import json
from datetime import datetime


seen_tokens = set()



async def intercept_axiom_ws(page):
    async def on_websocket(ws):
        print(f"[INFO] Подключен к WebSocket: {ws.url}")





        def format_new_token(token: dict) -> str:
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
            website = token.get("website") or "N/A"
            twitter = token.get("twitter") or "N/A"
            telegram = token.get("telegram") or "N/A"
            discord = token.get("discord") or "N/A"
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

            return f"""
        📢 Новая пара на рынке!
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        📛 Название: {name} (${ticker})
        🌐 Адрес пары: {address}
        🔗 CA: {token_address}
        🧑‍ Деплойер: {deployer}
        🧪 Протокол: {protocol}
        📜 Подпись: {signature}
        💻 Програма: {program_of_token}
        📦 Эмиссия: {fmt_or_na(supply, '{:,}')}
        💧 Ликвидность: {fmt_or_na(liquidity_sol, '{:.2f}')} SOL / {fmt_or_na(liquidity_token, '{:,}')} токенов
        🌐 Сайт: {website}
        📜 Твиттер: {twitter}
        🧪 Телеграм: {telegram}
        🔗 Дискорд: {discord}
        📦 Комиссия: {fees}%
        ⏰ Время создания и начало торгов: {created_time} ━━━ {time_to_trade}
        📢 Начало торгов через: {time_difference}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """

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

                    # 🔍 Фильтруем только по Raydium
                    if protocol == "Raydium V4" or protocol == "Raydium CPMM":
                        print(format_new_token(content))


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