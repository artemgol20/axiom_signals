import asyncio
from playwright.async_api import async_playwright, Page
from time import sleep
import json
import re

# Список адресов токенов
token_addresses = [
    "2eGu6tM4oHqjFkQYsH2HThTDdpr1yc2V1v9KuNLdrESP",
    # добавляй сюда другие адреса
]


async def parse_token_extensions(page: Page, token_address: str) -> dict:
    url = f"https://solscan.io/token/{token_address}#metadata"
    await page.goto(url, wait_until='domcontentloaded')
    sleep(2)
    result = {"token": token_address}

    try:
        xpath = '/html/body/div[1]/div[1]/div[3]/div[1]/div[2]/div[2]/div[2]/div[1]/div[2]/div/div[2]/div[4]/div/div/div[2]'
        neutral_value_elem = await page.query_selector(f'xpath={xpath}')
        neutral_value = await neutral_value_elem.text_content() if neutral_value_elem else None
        result["neutral_value"] = neutral_value.strip() if neutral_value else None

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


async def process_token(page: Page, token_address: str):
    data = await parse_token_extensions(page, token_address)

    TAX = data.get("neutral_value")
    token_program = data.get("token_program", {}).get("name") if data.get("token_program") else None
    uri = ''
    for item in data.get('pushed_content', []):
        if 'uri' in item:
            uri = item['uri'].strip('"')
            break

    print(f'token: {data["token"]}\nTAX: {TAX}\ntoken_program: {token_program}\nuri: {uri}')

    if uri:
        socials = await parse_uri_socials(page, uri)
        print(f"twitter: {socials['twitter']}")
        print(f"website: {socials['website']}")
        print(f"telegram: {socials['telegram']}")
    print("-" * 50)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        tasks = [process_token(page, addr) for addr in token_addresses]
        await asyncio.gather(*tasks)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
