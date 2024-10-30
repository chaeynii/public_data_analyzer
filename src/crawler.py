# src/crawler.py

import os
import pandas as pd
import logging
import re
from datetime import datetime
from utils import parse, return_search_url, update_url_page, get_page_count
import config
from concurrent.futures import ThreadPoolExecutor, as_completed

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_page_data(dType, soup):
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

            detail_soup = parse(config.BASE_URL + info_url)
            board = detail_soup.select_one("#contents").select_one("div.data-search-view")
            temp_data["설명"] = board.select_one(".cont").text.strip()
            
            table_data = {}
            for data_table_row in board.select("div.file-meta-table-pc > table > tr"):
                cols = data_table_row.find_all(["th", "td"])
                for th, td in zip(cols[::2], cols[1::2]):
                    if th.name != "th" or td.name != "td":
                        msg = f"data table error. {info_url}\nth: {th}\ntd: {td}"
                        logging.error(msg)
                        break
                    key = nonl(th.text)
                    value = nonl(td.text)
                    if key == "관리부서 전화번호" and not value:
                        telno = re.search(r"telNo.+\"([\d.]+)\"", td.select_one("script").text).groups()[0]
                        value = tel_no_format(telno)
                    table_data[key] = value
                    logging.debug("{}: [{}]".format(key, value))
            
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
            logging.info(f"Data collected: Type={dType}, Title={title}, URL={config.BASE_URL + info_url}")
    
    return temp_list
    
def get_list(dType, df):
    print(f"{dType} 수집을 시작합니다")
    base_url = return_search_url(dType)
    page_count = get_page_count(parse(base_url))
    
    def fetch_page_data(page):
        if page == 1:
            url = base_url
        else:
            url = update_url_page(base_url, page)
        soup = parse(url)
        return get_page_data(dType, soup)

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_page = {executor.submit(fetch_page_data, i): i for i in range(1, page_count + 1)}
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                page_df = pd.DataFrame(future.result())
                df = pd.concat([df, page_df], ignore_index=True)
                print(f"Completed page: {page}")
            except Exception as exc:
                print(f'Page {page} generated an exception: {exc}')
            
    org = config.REQUEST_PARAMS['org']
    output_dir = os.path.join('', 'data')
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime('%y%m%d')
    filename = f"{org}_{dType}_공공데이터포털_크롤링_{today}.xlsx"
    file_path = os.path.join(output_dir, filename)
    save_to_excel(df, file_path)
    return df

def save_to_excel(df, filepath):
    df.to_excel(filepath, index=False)
    print(f"Data saved to {filepath}")

def main():
    data_types = {
        "FILE": ["데이터명", "설명", "확장자", "제공기관", "조회수", "다운로드", "키워드", "업데이트 주기", "수정일", "등록일", "주기성 데이터", "제공형태", "URL", "상세링크"],
        "API": ["데이터명", "설명", "데이터포맷", "제공기관", "조회수", "활용신청", "키워드", "수정일", "등록일", "상세링크"],
        "LINKED": ["데이터명", "설명", "확장자", "제공기관", "조회수", "키워드", "수정일", "등록일", "바로가기 횟수", "바로가기 링크", "상세링크"]
    }

    dataframes = {}

    for data_type, columns in data_types.items():
        df = pd.DataFrame(columns=columns)
        dataframes[data_type] = get_list(data_type, df)

    return dataframes

if __name__ == "__main__":
    main()
