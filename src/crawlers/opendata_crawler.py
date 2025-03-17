from config.common_imports import *
from config.logging_config import setup_logging
from config.settings import BASE_URL, DATA_TYPES, REQUEST_PARAMS

logger = setup_logging("crawler.log")

async def get_page_data(dType, soup):
    result_list = soup.select("div.result-list")
    temp_list = []
    for result in result_list:
        li_list = result.find_all("li")
        for li in li_list:
        # p.tag-area 태그 확인 및 category, provider_type 설정
            tag_area = li.find("p", class_="tag-area")
            category = None
            provider_type = None
            if tag_area:
                labels = tag_area.find_all('span', class_='labelset')
                category = labels[0].text.strip() if len(labels) > 0 else None
                provider_type = labels[1].text.strip() if len(labels) > 1 else None
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
                "키워드": info_dict.get("키워드", ""),
                "분류체계": category,   
                "제공기관유형": provider_type
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

            detail_soup = await url_utils.parse(BASE_URL + info_url)
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

async def get_data_list(dType, df):
    logger.info(f"{dType} 수집을 시작합니다")
    SEARCH_URL = url_utils.return_search_url(dType)
    
    soup = await url_utils.parse(SEARCH_URL)
    page_count = html_utils.get_page_count(soup)
    
    async def fetch_page_data(page):
        max_retries = 10
        for attempt in range(max_retries):
            try:
                if page == 1:
                    url = SEARCH_URL
                else:
                    url = url_utils.update_url_page(SEARCH_URL, page)
                soup = await url_utils.parse(url)
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
    file_utils.save_to_excel(df, os.path.join(output_dir, f"{org}_{dType}_공공데이터포털_크롤링_{datetime.now().strftime('%y%m%d')}.xlsx"))
    return df

async def main():
    # 기관 목록 JSON 파일 로드
    sub_orgs_path = os.path.join("data", "sub_organizations.json")
    sub_orgs = file_utils.load_json(sub_orgs_path)
    if not sub_orgs:
        return

    # 기관별 크롤링 실행
    dataframes = {}
    for org in sub_orgs:
        logger.info(f"📌 현재 기관: {org}")

        # 동적으로 요청 파라미터 업데이트
        REQUEST_PARAMS["org"] = org

        # 데이터 타입별 데이터프레임 초기화
        for data_type, columns in DATA_TYPES.items():
            df = pd.DataFrame(columns=columns)
            dataframes[data_type] = await get_data_list(data_type, df)

        logger.info(f"✅ 기관 '{org}' 데이터 크롤링 완료.")

    return dataframes

if __name__ == "__main__":
    asyncio.run(main())