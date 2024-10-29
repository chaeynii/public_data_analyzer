# src/data_handlers.py

import pandas as pd
import logging
import re
from utils import parse
import config

# 로그 설정
logging.basicConfig(
    level=logging.INFO,  # 로그 레벨 설정
    format='%(asctime)s - %(levelname)s - %(message)s',  # 로그 포맷 설정
    handlers=[
        logging.FileHandler('data_crawler.log', encoding='utf-8'),  # 로그를 UTF-8 인코딩으로 파일에 기록
        logging.StreamHandler()  # 콘솔에도 로그를 출력
    ]
)

def get_info_withURL(temp_data, dType, info_url):
    # strip + 2칸이상 공백 제거
    nonl = lambda x:" ".join(x.split())

    def tel_no_format(telno: str) -> str:
        # 전화번호 하이픈 없을 경우 추가
        if telno and not re.findall(r"\d{2,3}-\d{4}-\d{4}", telno):
            return "-".join(re.search(r"^(02.{0}|01.{1}|[0-9]{3})([0-9]+)([0-9]{4})", telno).groups())
        return telno

    soup = parse(info_url)
    tmp = soup.select_one("#contents")
    board = tmp.select_one("div.data-search-view")

    # 설명
    description = board.select_one(".cont").text.strip()
    temp_data["설명"] = description

    table_data = {}
    # data table
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
                # 관리부서 전화번호 페이지 구조 예외
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
    # 선택된 컬럼만 필터링하여 업데이트
    selected_columns = common_columns.union(additional_columns) & table_data.keys()
    temp_data.update({key: table_data[key] for key in selected_columns})
    
    return temp_data

def get_result_list(soup, dType, df):
    result_list = soup.select("div.result-list")
    for result in result_list:
        li_list = result.find_all("li")

        temp_list = []  # 각 행의 데이터를 담을 리스트

        for li in li_list: # 리스트의 각 행을 순회
            dt = li.find("dl").find("dt")
            title = dt.find("span", class_ = "title").text.strip() #제목, 공백제거
            info_url = dt.find("a")["href"] #상세링크
            tagset = ','.join(span.text.strip() for span in dt.find_all("span", class_= "tagset")) #확장자 / 데이터포맷
            div_info_list = li.find("div", class_ = "info-data").find_all("p")
            info_dict = {}
            for info in div_info_list:
                tit = info.find("span", class_ = "tit").text.strip()
                # tit이 제공기관/키워드일 경우 예외처리
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

            # 각 행의 데이터를 리스트에 추가  
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
            
            # 로그 출력
            logging.info(f"Data collected: Type={dType}, Title={title}, URL={config.BASE_URL + info_url}")

    df = pd.concat([df, pd.DataFrame(temp_list)], ignore_index=True)  # 리스트를 데이터프레임에 추가
    return df


def save_to_excel(df, file_path):
    """DataFrame을 엑셀 파일로 저장"""
    df.to_excel(file_path, index=False)
