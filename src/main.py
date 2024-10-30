# src/main.py

import asyncio
from crawler import main as crawler_main

async def main():
    print("Starting data crawling...")
    result = await crawler_main()
    print("Data crawling completed.")
    return result

if __name__ == "__main__":
    asyncio.run(main())