from config.common_imports import *
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from config.logging_config import setup_logging
from config.settings import SEARCH_URL, REQUEST_PARAMS

logger = setup_logging("url_utils.log")

# URL 비동기 파싱
async def parse(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as response:
                html = await response.text()
                return bs(html, "html.parser")
    except aiohttp.ClientError as err:
        logger.error(f"요청 실패: {err} - URL: {url}")
        return None

# 검색 URL 생성(dtype)
def return_search_url(dType, currentPage=1):
    params = {**REQUEST_PARAMS, 'dType': dType, 'currentPage': currentPage}
    return f"{SEARCH_URL}{urlencode(params)}"

# URL 페이지 번호 update
def update_url_page(url, new_page):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['currentPage'] = [str(new_page)]
    
    updated_query = urlencode(query_params, doseq=True)
    return urlunparse(parsed_url._replace(query=updated_query))