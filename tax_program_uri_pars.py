import asyncio
from playwright.async_api import async_playwright, Page
import json
import re
from time import sleep


async def parse_token_extensions(page: Page, token_address: str) -> dict:
    url = f"https://solscan.io/token/{token_address}#metadata"
    await page.goto(url, wait_until='domcontentloaded')
    sleep(2)
    result = {"token": token_address}

    try:
        xpath = '/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/div/div[2]/div[4]/div/div/div[2]'
        neutral_value_elem = await page.query_selector(f'xpath={xpath}')
        neutral_value = await neutral_value_elem.text_content() if neutral_value_elem else None
        result["TAX"] = neutral_value.strip() if neutral_value else None

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


async def parse_uri_socials(page: Page, uri: str) -> dict:
    await page.goto(uri, wait_until='domcontentloaded')
    html_content = await page.content()

    match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL)
    if not match:
        return {"twitter": "NaN", "website": "NaN", "telegram": "NaN"}

    try:
        json_data = json.loads(match.group(1))
        socials = json_data.get("properties", {}).get("socials", {})
        return {
            "twitter": socials.get("twitter", "NaN"),
            "website": socials.get("website", "NaN"),
            "telegram": socials.get("telegram", "NaN")
        }
    except json.JSONDecodeError:
        return {"twitter": "NaN", "website": "NaN", "telegram": "NaN"}


async def process_token(page: Page, token_address: str) -> dict:
    data = await parse_token_extensions(page, token_address)

    TAX = data.get("TAX")
    token_program = data.get("token_program", {}).get("name") if data.get("token_program") else None
    uri = ''
    for item in data.get('pushed_content', []):
        if 'uri' in item:
            uri = item['uri'].strip('"')
            break

    result = {
        "TAX": TAX,
        "token_program": token_program,
        "uri": uri,
    }

    if uri:
        socials = await parse_uri_socials(page, uri)
        result.update(socials)

    return result


# Главная функция, которая будет запускать обработку токена
async def main_tax(token_address: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        result = await process_token(page, token_address)
        print(result)

        await browser.close()


# Запуск теста с одним токеном
if __name__ == "__main__":
    token_address = "2eGu6tM4oHqjFkQYsH2HThTDdpr1yc2V1v9KuNLdrESP"  # Замените на нужный адрес токена
    asyncio.run(main_tax(token_address))
