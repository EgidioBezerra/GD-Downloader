import asyncio
from playwright.async_api import async_playwright

async def test():
    print("Testando Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Aplicar anti-detecção nativo
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        """)
        
        await page.goto('https://www.google.com')
        print("✓ Sucesso! Playwright funciona!")
        
        await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())