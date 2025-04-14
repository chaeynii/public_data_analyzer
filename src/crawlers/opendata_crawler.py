from config.common_imports import *
from config.logging_config import setup_logging
from config.settings import BASE_URL, DATA_TYPES, REQUEST_PARAMS, COLUMNS
from typing import Dict, List, Optional, Any

logger = setup_logging("crawler.log")

async def collect(dType: str, df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"{dType} 수집을 시작합니다")
    
    SEARCH_URL = url_utils.return_search_url(dType)
    soup = await url_utils.parse(SEARCH_URL)
    page_count = html_utils.get_page_count(soup)
    
    async def fetch_page_data(page) -> Optional[List[Dict[str, str]]]:
        max_retries = 10
        for attempt in range(max_retries):
            try:
                if page == 1:
                    url = SEARCH_URL
                else:
                    url = url_utils.update_url_page(SEARCH_URL, page)
                soup = await url_utils.parse(url)
                return await get_data(soup)
            except Exception as exc:
                if attempt < max_retries - 1:
                    logger.error({exc})
                    logger.warning(f'Page {page} 수집 오류({exc}) / 재시도 {attempt + 1}/{max_retries})')
                    await asyncio.sleep(5)
                else:
                    logger.error(f'Page {page} 수집 실패: {exc}')
                    return None

    async def get_data(soup: bs) -> List[Dict[str, str]]:
        result_list = soup.select("div.result-list")
        temp_list: List[Dict[str, str]] = []
        
        for result in result_list: 
            for li in result.find_all("li"):
                ### p.tag-area > 분류체계(brown) / 제공기관 유형(red)
                tag_area = li.find("p", class_="tag-area")
                category = None
                # provider_type = None
                if tag_area:
                    labels = tag_area.find_all('span', class_='labelset')
                    category = labels[0].text.strip() if len(labels) > 0 else None
                    # provider_type = labels[1].text.strip() if len(labels) > 1 else None
                
                ### dl > dt > 상세링크(a), 데이터명(span.title), 데이터유형(span.tagset)
                info_url = li.select_one("dl dt a")["href"]
                title = li.select_one("dl dt span.title").text.strip()
                tagset = ','.join(span.get_text(strip=True) for span in li.select("dl dt span.tagset"))

                ### div.info-data > 제공기관, 수정일, 조회수, 다운로드, 주기성 데이터, 키워드 등
                div_info_list = li.select("div.info-data p")
                info_dict = {
                    info.find("span", class_="tit").text.strip(): (
                        list(info.children)[-1].strip() if info.find("span", class_="tit").text.strip() == "키워드"
                        else info.find("span", class_="data").text.strip()
                    )
                    for info in div_info_list
                    if info.find("span", class_="tit")
                }

                temp_data: Dict[str, Any] = {
                    "구분" : dType,
                    "데이터명": title if title else "",
                    "상세링크": (BASE_URL+info_url) if info_url else "",
                    "분류체계": category if category else "",
                    # "제공기관": info_dict.get("제공기관", ""),
                    # "제공기관유형": provider_type if provider_type else "",
                    "조회수" : info_dict.get("조회수", ""),
                    "데이터포맷/확장자":tagset if tagset else "",
                    "다운로드/활용신청": info_dict.get("다운로드", info_dict.get("활용신청", "")),
                    "주기성 데이터" : info_dict.get("주기성 데이터", "")
                }

                ### 상세 정보 가져오기
                detail_soup = await url_utils.parse(BASE_URL + info_url)
                board = detail_soup.select_one("table.dataset-table")
                if board:
                    for data_table_row in board.find_all("tr"):
                        cols = data_table_row.find_all(["th", "td"])
                        for th, td in zip(cols[::2], cols[1::2]):
                            if th.name != "th" or td.name != "td":
                                logger.error(f"data table error. {info_url}\nth: {th}\ntd: {td}")
                                break
                            key = th.text.strip()
                            value = td.text.strip()
                            if key in COLUMNS:
                                temp_data[key] = value
                else:
                    logger.warning(f"[상세 테이블 없음] {info_url}")
                temp_list.append(temp_data)
        return temp_list
    
    tasks = [fetch_page_data(i) for i in range(1, page_count + 1)]
    for future in tqdm_asyncio.as_completed(tasks, total=page_count, desc=f"Collecting {dType} data"):
        try:
            result = await future
            if result is not None:
                page_df = pd.DataFrame(result)
                df = pd.concat([df, page_df], ignore_index=False)
        except Exception as exc:
            logger.error(f'예상치 못한 오류 발생: {exc}')
            
    return df

async def main():
    # 기관 목록 JSON 파일 로드
    sub_orgs_path = os.path.join("data", "sub_organizations.json")
    sub_orgs = file_utils.load_json(sub_orgs_path)
    if not sub_orgs:
        return

    # 기관별 크롤링 실행
    df_result = pd.DataFrame()
    for org in sub_orgs:
        logger.info(f"📌 현재 기관: {org}")

        REQUEST_PARAMS["org"] = org

        for data_type in DATA_TYPES:
            collected = await collect(data_type, pd.DataFrame(columns=COLUMNS))
            df_result = pd.concat([df_result, collected], ignore_index=True)

        # 엑셀로 저장
        output_dir = os.path.join('', 'data')
        os.makedirs(output_dir, exist_ok=True)
        file_utils.save_to_excel(df_result, os.path.join(output_dir, f"{org}_공공데이터포털_크롤링_{datetime.now().strftime('%y%m%d')}.xlsx"))
            
        logger.info(f"✅ 기관 '{org}' 데이터 크롤링 완료.")

    return df_result

if __name__ == "__main__":
    asyncio.run(main())