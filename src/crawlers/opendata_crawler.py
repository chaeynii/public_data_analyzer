from config.common_imports import *
from config.logging_config import setup_logging
from config.settings import BASE_URL, DATA_TYPES, REQUEST_PARAMS

logger = setup_logging("crawler.log")

async def parse(url):
    """입력된 URL을 HTML로 비동기적으로 파싱"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=20) as response:
                html = await response.text()
                return bs(html, "html.parser")
        except aiohttp.ClientError as err:
            logger.error(f"Request error occurred: {err} - URL: {url}")
            return None

def return_search_url(dType, currentPage=1):
    """검색 URL을 생성"""
    params = REQUEST_PARAMS.copy()
    params.update({
        'dType': dType,
        'currentPage': currentPage
    })
    search_url = BASE_URL+'&'.join([f"{key}={value}" for key, value in params.items()])
    return search_url

def update_url_page(url, new_page):
    """URL의 페이지 번호만 업데이트"""
    return re.sub(r'currentPage=\d+', f'currentPage={new_page}', url)

def get_page_count(soup):
    """총 페이지 수를 추출"""
    page_div = soup.select("nav.pagination")
    
    if not page_div:
        # Pagination이 없는 경우 검색 결과가 없다고 가정
        logger.warning("No search results found.")
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
        logger.error(f"An error occurred while trying to get the page count: {e}")
        page_count = 1  # 기본적으로 1페이지로 간주
    
    return page_count

async def get_page_data(dType, soup):
    result_list = soup.select("div.result-list")
    temp_list = []
    for result in result_list:
        li_list = result.find_all("li")
        for li in li_list:
            dt = li.find("dl").find("dt")
            title = dt.find("span", class_="title").text.strip()
            info_url = dt.find("a")["href"]
            tagset = ','.join(span.text.strip() for span in dt.find_all("span", class_="tagset"))
            div_info_list = li.find("div", class_="info-data").find_all("p")
            info_dict = {}
            for info in div_info_list:
                tit = info.find("span", class_="tit").text.strip()
                if (tit == "제공기관"):
                    if (dType == "LINKED"):
                        data = info.find("span", class_="data").text.strip()
                    else:
                        data = info.find("span", class_="data").find("span", class_="esHighlight").text.strip()
                elif(tit == "키워드"):
                    data = list(info.children)[-1].strip()
                else:
                    data = info.find("span", class_="data").text.strip()
                info_dict[tit] = data
                
            temp_data = {
                "데이터명": title,
                "상세링크": info_url,
                "제공기관": info_dict.get("제공기관", ""),
                "수정일": info_dict.get("수정일", ""),
                "조회수": info_dict.get("조회수", ""),
                "키워드": info_dict.get("키워드", "")
            }
            
            if dType == "API":
                temp_data["데이터포맷"] = tagset
                temp_data["활용신청"] = info_dict.get("활용신청", "")
            else:
                temp_data["확장자"] = tagset
            if dType == "FILE":
                temp_data["주기성 데이터"] = info_dict.get("주기성 데이터", "")
                temp_data["다운로드"] = info_dict.get("다운로드", "")
            
            # 상세 정보 가져오기
            nonl = lambda x:" ".join(x.split())
            def tel_no_format(telno: str) -> str:
                if telno and not re.findall(r"\d{2,3}-\d{4}-\d{4}", telno):
                    return "-".join(re.search(r"^(02.{0}|01.{1}|[0-9]{3})([0-9]+)([0-9]{4})", telno).groups())
                return telno

            detail_soup = await parse(BASE_URL + info_url)
            board = detail_soup.select_one("#contents").select_one("div.data-search-view")
            temp_data["설명"] = board.select_one(".cont").text.strip()
            
            table_data = {}
            for data_table_row in board.select("div.file-meta-table-pc > table > tr"):
                cols = data_table_row.find_all(["th", "td"])
                for th, td in zip(cols[::2], cols[1::2]):
                    if th.name != "th" or td.name != "td":
                        logger.error(f"data table error. {info_url}\nth: {th}\ntd: {td}")
                        break
                    key = nonl(th.text)
                    value = nonl(td.text)
                    if key == "관리부서 전화번호" and not value:
                        telno = re.search(r"telNo.+\"([\d.]+)\"", td.select_one("script").text).groups()[0]
                        value = tel_no_format(telno)
                    table_data[key] = value
            
            common_columns = {"설명", "등록일"}
            additional_columns = set()
            if dType == "FILE":
                additional_columns = {"업데이트 주기", "제공형태", "URL"}
            elif dType == "LINKED":
                temp_data["바로가기 링크"] = board.select_one("div.btn-util > a")['href']
                additional_columns = {"바로가기 횟수", "바로가기 링크"}
            
            selected_columns = common_columns.union(additional_columns) & table_data.keys()
            temp_data.update({key: table_data[key] for key in selected_columns})
            
            temp_list.append(temp_data)
    
    return temp_list
    
async def get_list(dType, df):
    logger.info(f"{dType} 수집을 시작합니다")
    base_url = return_search_url(dType)
    soup = await parse(base_url)
    page_count = get_page_count(soup)
    
    async def fetch_page_data(page):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                if page == 1:
                    url = base_url
                else:
                    url = update_url_page(base_url, page)
                soup = await parse(url)
                return await get_page_data(dType, soup)
            except Exception as exc:
                if attempt < max_retries - 1:
                    logger.warning(f'Page {page} 수집 중 오류 발생. 재시도 중... (시도 {attempt + 1}/{max_retries})')
                    await asyncio.sleep(5)  # 재시도 전 잠시 대기
                else:
                    logger.error(f'Page {page} 수집 실패: {exc}')
                    return None

    tasks = [fetch_page_data(i) for i in range(1, page_count + 1)]
    for future in tqdm_asyncio.as_completed(tasks, total=page_count, desc=f"Collecting {dType} data"):
        try:
            result = await future
            if result is not None:
                page_df = pd.DataFrame(result)
                df = pd.concat([df, page_df], ignore_index=True)
        except Exception as exc:
            logger.error(f'예상치 못한 오류 발생: {exc}')
            
    org = REQUEST_PARAMS['org']
    output_dir = os.path.join('', 'data')
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime('%y%m%d')
    filename = f"{org}_{dType}_공공데이터포털_크롤링_{today}.xlsx"
    file_path = os.path.join(output_dir, filename)
    save_to_excel(df, file_path)
    return df

def save_to_excel(df, filepath):
    df.to_excel(filepath, index=True)
    logger.info(f"Data saved to {filepath}")

async def main():
    # Load sub_organizations list
    sub_orgs_path = os.path.join("data", "sub_organizations.json")
    
    # Check if file exists
    if not os.path.exists(sub_orgs_path):
        logger.error(f"'{sub_orgs_path}' 파일을 찾을 수 없습니다.")
        return
    
    with open(sub_orgs_path, "r", encoding="utf-8") as file:
        sub_orgs = json.load(file)

    # If no organizations are found
    if not sub_orgs:
        logger.warning("기관 목록이 비어 있습니다.")
        return

    # Loop through each organization
    for org in sub_orgs:
        logger.info(f"📌 현재 기관: {org}")

        # Update config settings dynamically
        REQUEST_PARAMS["org"] = org

        # Initialize dataframes
        dataframes = {}

        # Loop through each data type (FILE, API, LINKED)
        for data_type, columns in DATA_TYPES.items():
            df = pd.DataFrame(columns=columns)
            dataframes[data_type] = await get_list(data_type, df)

        # Log completion
        logger.info(f"✅ 기관 '{org}' 데이터 크롤링 완료.")

    return dataframes

if __name__ == "__main__":
    asyncio.run(main())