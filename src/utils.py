# src/utils.py

import requests
from bs4 import BeautifulSoup as bs
import config
import re

session = requests.Session()

def parse(url):
    """입력된 URL을 HTML로 파싱"""
    try:
        req = session.get(url, timeout=20)
        req.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"Request error occurred: {err} - URL: {url}")
        return None
    return bs(req.text, "html.parser")

def return_search_url(dType, currentPage=1):
    """검색 URL을 생성"""
    params = config.REQUEST_PARAMS.copy()
    org = config.REQUEST_PARAMS['org']
    params.update({
        'dType': dType,
        'orgFullName': org,
        'orgFilter': org,
        'org': org,
        'currentPage': currentPage
    })
    search_url = config.BASE_URL + '/tcs/dss/selectDataSetList.do?' + '&'.join([f"{key}={value}" for key, value in params.items()])
    return search_url

def update_url_page(url, new_page):
    """URL의 페이지 번호만 업데이트"""
    return re.sub(r'currentPage=\d+', f'currentPage={new_page}', url)

def get_page_count(soup):
    """총 페이지 수를 추출"""
    page_div = soup.select("nav.pagination")
    
    if not page_div:
        # Pagination이 없는 경우 검색 결과가 없다고 가정
        print("No search results found.")
        return 0  # 검색 결과가 없는 경우 0을 반환
    
    # 페이지 네비게이션이 있는데 a 태그가 없는 경우
    page_links = page_div[0].select("a")
    
    if not page_links:
        # <strong> 태그가 하나만 존재하고 그 안에 '1'이라는 숫자가 있는 경우
        active_page = page_div[0].select("strong.active")
        if active_page and active_page[0].text.strip() == '1':
            return 1  # 페이지가 1개뿐이므로 1을 반환
        
    try:
        last_a = page_div[0].select("a.control.last")
        
        if not last_a:
            # "마지막 페이지" 버튼이 없는 경우
            count_a = len(page_div[0].select("a"))
            return count_a + 1  # 해당 페이지에서 발견된 a 태그의 수를 페이지 수로 사용
            
        # a 태그의 onclick 속성에서 페이지 번호를 추출
        onclick_value = last_a[0].get('onclick')
        numbers = re.findall(r'\d+', onclick_value)
        page_count = int(numbers[0])
        
    except Exception as e:
        print(f"An error occurred while trying to get the page count: {e}")
        page_count = 1  # 기본적으로 1페이지로 간주
    
    return page_count