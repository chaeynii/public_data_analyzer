from config.common_imports import *
from crawlers.org_crawler import main as org_crawler_main
from crawlers.opendata_crawler import main as opendata_crawler_main

async def main(run_org_crawler: bool = True):
    if run_org_crawler:
        print("기관 목록 크롤링 시작...")
        await org_crawler_main()
        print("기관 목록 크롤링 완료.")
    else:
        print("기관 목록 크롤링 생략.")

    print("오픈데이터 크롤링 시작...")
    result = await opendata_crawler_main()
    print("오픈데이터 크롤링 완료.")

    return result

if __name__ == "__main__":
    # 기관 목록 크롤링 여부
    asyncio.run(main(run_org_crawler=False))
    
    
