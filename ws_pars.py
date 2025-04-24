from playwright.async_api import async_playwright
import asyncio
import json

WATCHLIST = {"FLOPY", "NEW MOONPAY MASCOT NAME"}
seen_tokens = set()



async def intercept_axiom_ws(page):
    async def on_websocket(ws):
        print(f"[INFO] Подключен к WebSocket: {ws.url}")



        seen_tokens = set()

        def format_new_token(token: dict) -> str:
            print(token)
            name = token.get("token_name") or "Unknown"
            ticker = token.get("token_ticker") or "???"
            address = token.get("pair_address") or "N/A"
            token_address = token.get("token_address") or "N/A"
            deployer = token.get("deployer_address") or "N/A"
            protocol = token.get("protocol") or "N/A"
            signature = token.get("signature") or "N/A"
            website = token.get("website") or "N/A"
            twitter = token.get("twitter") or "N/A"
            telegram = token.get("telegram") or "N/A"
            discord = token.get("discord") or "N/A"

            supply = token.get("supply")
            liquidity_sol = token.get("initial_liquidity_sol")
            liquidity_token = token.get("initial_liquidity_token")
            lp_burned = token.get("lp_burned")
            dev_percent = token.get("dev_holds_percent")
            snipers_percent = token.get("snipers_hold_percent")

            def fmt_or_na(value, fmt):
                return fmt.format(value) if value is not None else "N/A"

            return f"""
        📢 Новая пара на рынке!
        ━━━━━━━━━━━━━━━━━━━━━━━
        📛 Название: {name} (${ticker})
        🌐 Адрес пары: {address}
        🔗 Token Mint: {token_address}
        🧑‍💻 Деплойер: {deployer}
        🧪 Протокол: {protocol}
        📜 Подпись: {signature}

        📦 Эмиссия: {fmt_or_na(supply, '{:,}')}
        💧 Ликвидность: {fmt_or_na(liquidity_sol, '{:.2f}')} SOL / {fmt_or_na(liquidity_token, '{:,}')} токенов
        🔥 Сожжено LP: {fmt_or_na(lp_burned, '{:.2f}')}%
        🧬 У разработчиков: {fmt_or_na(dev_percent, '{:.2f}')}%
        🎯 У снайперов: {fmt_or_na(snipers_percent, '{:.2f}')}%

        🌍 Ссылки:
        🔗 Website: {website}
        🐦 Twitter: {twitter}
        💬 Telegram: {telegram}
        📣 Discord: {discord}
        ━━━━━━━━━━━━━━━━━━━━━━━
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
        ws.on("framesent", lambda msg: print(f"[WS FRAME SENT] {msg}"))
        ws.on("close", lambda _: print("[WS CLOSED]"))

    page.on("websocket", on_websocket)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
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
