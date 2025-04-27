import asyncio
from playwright.async_api import async_playwright, Page
from time import sleep

token_address = "2eGu6tM4oHqjFkQYsH2HThTDdpr1yc2V1v9KuNLdrESP"  # замени на нужный адрес


async def parse_token_extensions(page: Page, token_address: str) -> dict:
    url = f"https://solscan.io/token/{token_address}#metadata"
    await page.goto(url, wait_until='domcontentloaded')
    sleep(2)
    result = {"token": token_address}

    try:
        # 1. Значение внутри специфичного обёрточного div
        xpath = '/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/div/div[2]/div[4]/div/div/div[2]'
        neutral_value_elem = await page.query_selector(f'xpath={xpath}')
        neutral_value = await neutral_value_elem.text_content() if neutral_value_elem else None
        result["neutral_value"] = neutral_value.strip() if neutral_value else None

        # 2. Название и ссылка "Token 2022 Program"
        token_program_elem = await page.query_selector('span.textLink a')
        if token_program_elem:
            program_name = await token_program_elem.text_content()
            program_href = await token_program_elem.get_attribute('href')
            result["token_program"] = {
                "name": program_name.strip() if program_name else None,
                "link": f"https://solscan.io{program_href}" if program_href else None
            }
        else:
            result["token_program"] = None

        # 3. Тексты всех вложенных div внутри pushed-content object-container
        container_values = []
        variable_rows = await page.query_selector_all('div.pushed-content.object-container div.variable-row')

        for row in variable_rows:
            key_el = await row.query_selector('span.object-key span')
            value_el = await row.query_selector('div.variable-value span.string-value')

            key = await key_el.inner_text() if key_el else None
            value = await value_el.inner_text() if value_el else None

            if key and value:
                container_values.append({key: value})

        result["pushed_content"] = container_values

    except Exception as e:
        result["error"] = str(e)

    return result


async def main(token_address: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        data = await parse_token_extensions(page, token_address)
        # print(data)

        TAX = data["neutral_value"]
        token_program = data["token_program"]["name"]
        uri = ''
        for item in data['pushed_content']:
            if 'uri' in item:
                uri = item['uri'].strip('"')
                break

        print(
            f'token: {data["token"]}\nTAX: {TAX}\ntoken_program: {token_program}\nuri: {uri}')
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(token_address))
