from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Запуск браузера с максимизированным окном
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])  # для max window
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://axiom.trade/new-coins")


        # Получаем все карточки монет
        cards = await page.query_selector_all("div.flex.flex-row.w-full.gap-\\[12px\\]")

        for i, card in enumerate(cards):
            # Открываем новую вкладку
            new_tab = await context.new_page()
            await new_tab.goto("https://axiom.trade/new-coins")
            await new_tab.wait_for_selector("div.flex.flex-row.w-full.gap-\\[12px\\]")
            card_in_new_tab = (await new_tab.query_selector_all("div.flex.flex-row.w-full.gap-\\[12px\\]"))[i]

            # Кликаем на карточку в новой вкладке
            await card_in_new_tab.click()
            await new_tab.wait_for_timeout(3000)  # Ждём немного, пока страница загрузится

            # Можно задать размеры окна вручную, если нужно
            await new_tab.set_viewport_size({'width': 1920, 'height': 1080})

        await browser.close()

import asyncio
asyncio.run(run())
