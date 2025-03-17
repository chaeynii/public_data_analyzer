from config.common_imports import *
from config.logging_config import setup_logging

logger = setup_logging("html_utils.log")

# 총 페이지 수 추출
def get_page_count(soup):
    page_nav = soup.select("nav.pagination") # pagination 네비게이션 가져오기

    if not page_nav:
        logger.warning("page_nav 없음. 0 반환")
        return 0

    page_links = page_nav[0].select("a")
    
    # 페이지가 1개일 경우 > a 태그 없음
    if not page_links:
        active_page = page_nav[0].select("strong.active")
        if active_page and active_page[0].text.strip() == '1':
            return 1

    try:
        last_a = page_nav[0].select("a.control.last")

        if not last_a:
            count_a = len(page_nav[0].select("a"))
            return count_a + 1  # 발견된 a 태그 개수를 기반으로 페이지 수 추정

        # "마지막 페이지" 버튼의 onclick 속성에서 페이지 번호 추출
        onclick_value = last_a[0].get('onclick')
        numbers = re.findall(r'\d+', onclick_value)
        page_count = int(numbers[0])

    except Exception as e:
        logger.error(f"페이지 수 추출 중 오류 발생: {e}")
        page_count = 1  # 기본적으로 1페이지로 간주

    return page_count
