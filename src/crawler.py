# src/crawler.py

import os
import pandas as pd
from datetime import datetime
from utils import parse, return_search_url, get_page_count
from data_handlers import get_result_list 
import config
from multiprocessing import Pool

def get_list(dType, df):
    print(f"{dType} 수집을 시작합니다")
    search_url = return_search_url(dType)
    # print(f"Requesting URL: {search_url}")
    page_count = get_page_count(parse(search_url))
    # print(f"Total pages: {page_count}")
    
    # 속도 개선 이전
    for i in range(1, page_count + 1):
        print(f"page: {i}")
        new_url = return_search_url(dType, currentPage=i)
        soup = parse(new_url)
        df = get_result_list(soup, dType, df)
    
    # Multiprocessing을 위한 Pool 설정
    # with Pool(processes=4) as pool:
    #     page_numbers = range(1, page_count + 1)
    #     results = pool.map(fetch_page_data, [(dType, page, df) for page in page_numbers])

    # # 결과 통합
    # all_data = [item for sublist in results for item in sublist]
    # df = pd.DataFrame(all_data)
    
    # 데이터 수집이 완료된 후 파일 저장
    org = config.REQUEST_PARAMS['org']
    
    output_dir = os.path.join('', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime('%y%m%d')
    filename = f"{org}_{dType}_공공데이터포털_크롤링_{today}.xlsx"
    file_path = os.path.join(output_dir, filename)
    
    save_to_excel(df, file_path)
    
    return df

def fetch_page_data(page_info):
    dType, page_number, df = page_info
    url = return_search_url(dType, currentPage=page_number)
    soup = parse(url)
    return get_result_list(soup, dType, df)

def save_to_excel(df, filepath):
    df.to_excel(filepath, index=True)
    print(f"Data saved to {filepath}")

def main():
    """메인 함수"""

    # 컬럼명
    col_FILE = ["데이터명", "설명", "확장자", "제공기관", "조회수", "다운로드", "키워드", "업데이트 주기", "수정일", "등록일", "주기성 데이터", "제공형태", "URL", "상세링크"]
    col_API = ["데이터명", "설명", "데이터포맷", "제공기관", "조회수", "활용신청", "키워드", "수정일", "등록일", "상세링크"]
    col_LINKED = ["데이터명", "설명", "확장자", "제공기관", "조회수", "키워드", "수정일", "등록일", "바로가기 횟수", "바로가기 링크", "상세링크"]

    # # 데이터프레임
    df_FILE = pd.DataFrame(columns=col_FILE)
    df_API = pd.DataFrame(columns=col_API)
    df_LINKED = pd.DataFrame(columns=col_LINKED)
    
    # 데이터 수집 및 저장
    df_FILE = get_list("FILE", df_FILE)
    df_API = get_list("API", df_API)
    df_LINKED = get_list("LINKED", df_LINKED)

if __name__ == "__main__":
    main()
