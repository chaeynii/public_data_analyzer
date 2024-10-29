# src/crawler.py

import os
import pandas as pd
import logging
import re
from datetime import datetime
from utils import parse, return_search_url, get_page_count
import config

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_info_withURL(temp_data, dType, info_url):
    nonl = lambda x:" ".join(x.split())
    
    def tel_no_format(telno: str) -> str:
        if telno and not re.findall(r"\d{2,3}-\d{4}-\d{4}", telno):
            return "-".join(re.search(r"^(02.{0}|01.{1}|[0-9]{3})([0-9]+)([0-9]{4})", telno).groups())
        return telno

    soup = parse(info_url)
    tmp = soup.select_one("#contents")
    board = tmp.select_one("div.data-search-view")
    description = board.select_one(".cont").text.strip()
    temp_data["설명"] = description

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
    if (dType == "FILE"):
        additional_columns = {"업데이트 주기", "제공형태", "URL"}
    elif (dType == "LINKED"):
        temp_data["바로가기 링크"] = board.select_one("div.btn-util > a")['href']
        additional_columns = {"바로가기 횟수", "바로가기 링크"}

    selected_columns = common_columns.union(additional_columns) & table_data.keys()
    temp_data.update({key: table_data[key] for key in selected_columns})
    return temp_data

def get_result_list(soup, dType, df):
    result_list = soup.select("div.result-list")
    for result in result_list:
        li_list = result.find_all("li")
        temp_list = []
        for li in li_list:
            dt = li.find("dl").find("dt")
            title = dt.find("span", class_ = "title").text.strip()
            info_url = dt.find("a")["href"]
            tagset = ','.join(span.text.strip() for span in dt.find_all("span", class_= "tagset"))
            div_info_list = li.find("div", class_ = "info-data").find_all("p")
            info_dict = {}
            for info in div_info_list:
                tit = info.find("span", class_ = "tit").text.strip()
                if (tit == "제공기관"):
                    if (dType == "LINKED"):
                        data = info.find("span", class_ = "data").text.strip()
                    else:
                        data = info.find("span", class_ = "data").find("span", class_ = "esHighlight").text.strip()
                elif(tit == "키워드"):
                    data = list(info.children)[-1].strip()
                else:
                    data = info.find("span", class_ = "data").text.strip()
                info_dict[tit] = data

            temp_data = {"데이터명": title,
                         "상세링크": info_url,
                         "제공기관": info_dict.get("제공기관", ""),
                         "수정일": info_dict.get("수정일", ""),
                         "조회수": info_dict.get("조회수", ""),
                         "키워드": info_dict.get("키워드", "")}
            if (dType == "API"):
                temp_data["데이터포맷"] = tagset
                temp_data["활용신청"] = info_dict.get("활용신청", "")
            else:
                temp_data["확장자"] = tagset
            if (dType == "FILE"):
                temp_data["주기성 데이터"] = info_dict.get("주기성 데이터", "")
                temp_data["다운로드"] = info_dict.get("다운로드", "")
            temp_data = get_info_withURL(temp_data, dType, config.BASE_URL+info_url)
            temp_list.append(temp_data)
            logging.info(f"Data collected: Type={dType}, Title={title}, URL={config.BASE_URL + info_url}")
        df = pd.concat([df, pd.DataFrame(temp_list)], ignore_index=True)
    return df

def get_list(dType, df):
    print(f"{dType} 수집을 시작합니다")
    search_url = return_search_url(dType)
    page_count = get_page_count(parse(search_url))
    for i in range(1, page_count + 1):
        print(f"page: {i}")
        new_url = return_search_url(dType, currentPage=i)
        soup = parse(new_url)
        df = get_result_list(soup, dType, df)
    
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
    """메인 함수"""
    col_FILE = ["데이터명", "설명", "확장자", "제공기관", "조회수", "다운로드", "키워드", "업데이트 주기", "수정일", "등록일", "주기성 데이터", "제공형태", "URL", "상세링크"]
    col_API = ["데이터명", "설명", "데이터포맷", "제공기관", "조회수", "활용신청", "키워드", "수정일", "등록일", "상세링크"]
    col_LINKED = ["데이터명", "설명", "확장자", "제공기관", "조회수", "키워드", "수정일", "등록일", "바로가기 횟수", "바로가기 링크", "상세링크"]

    df_FILE = pd.DataFrame(columns=col_FILE)
    df_API = pd.DataFrame(columns=col_API)
    df_LINKED = pd.DataFrame(columns=col_LINKED)

    df_FILE = get_list("FILE", df_FILE)
    df_API = get_list("API", df_API)
    df_LINKED = get_list("LINKED", df_LINKED)

if __name__ == "__main__":
    main()
