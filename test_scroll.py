import asyncio
from playwright.async_api import async_playwright

async def diagnose():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto('https://arxiv.org/pdf/1706.03762.pdf')
        await asyncio.sleep(5)
        
        # 1. Verifica iframes
        frames = page.framesd
        print(f"Frames encontrados: {len(frames)}")
        
        # 2. Tenta achar o viewer
        viewer = await page.query_selector('iframe')
        if viewer:
            print("Iframe encontrado!")
        
        # 3. Tenta scroll no documento principal
        print("\nTestando scroll no documento principal...")
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(0.5)
        
        # 4. Se tiver iframe, tenta scroll nele
        if len(frames) > 1:
            print("\nTestando scroll no iframe...")
            pdf_frame = frames[1]  # Geralmente o PDF está no segundo frame
            for i in range(5):
                await pdf_frame.evaluate("window.scrollBy(0, 1000)")
                await asyncio.sleep(0.5)
        
        input("Você viu rolar? Pressione Enter...")
        await browser.close()

asyncio.run(diagnose())