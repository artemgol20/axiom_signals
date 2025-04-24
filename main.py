from playwright.sync_api import sync_playwright
import time


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        page.goto("https://axiom.trade")
        input("Настрой фильтры на сайте и нажми Enter для запуска парсера...")

        print("Парсер запущен...\n")

        seen_contracts = set()  # Сюда будем складывать уже увиденные адреса

        try:
            while True:
                cards = page.query_selector_all("div[style*='height: 3480px'] > div")

                for card in cards:
                    try:
                        # Название монеты (слева, например: CTROLL)
                        title_span = card.query_selector("span.text-textPrimary")
                        title = title_span.inner_text().strip() if title_span else None


                        ca_button = card.query_selector("button:has(i.ri-file-copy-fill)")
                        contract_address = ca_button.query_selector("span.text-inherit").inner_text().strip() if ca_button else None

                        # Market Cap и Volume
                        market_cap = card.query_selector("span:text('MC') + span")
                        volume = card.query_selector("span:text('V') + span")

                        if contract_address and contract_address not in seen_contracts:
                            seen_contracts.add(contract_address)

                            print({
                                "title": title,
                                "full_title": contract_address,
                                "market_cap": market_cap.inner_text().strip() if market_cap else None,
                                "volume": volume.inner_text().strip() if volume else None
                            })

                    except Exception as e:
                        print("Ошибка при парсинге карточки:", e)

                time.sleep(2)

        except KeyboardInterrupt:
            print("\nПарсинг остановлен пользователем.")
        finally:
            browser.close()


run()
