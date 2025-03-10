from config.common_imports import *
from crawlers.org_crawler import main as crawler_main

async def main():
    print("Starting data crawling...")
    result = await crawler_main()
    print("Data crawling completed.")
    return result

if __name__ == "__main__":
    asyncio.run(main())