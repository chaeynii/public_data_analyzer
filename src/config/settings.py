from config.common_imports import *
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "").strip()
SEARCH_URL = os.getenv("BASE_URL", "").strip() + "/tcs/dss/selectDataSetList.do?"
ORG_NAME = os.getenv("ORG_NAME", "")

REQUEST_PARAMS = {
    'dType': '',
    'sort': 'updtDt',
    'org': ORG_NAME,
    'currentPage': 1,
    'perPage': 40,
}

# 공통 컬럼
DATA_TYPES = ["FILE", "API"]
COLUMNS = [
    # "제공기관", 
    "구분", "데이터명", "설명", "데이터포맷/확장자",
    "조회수", "다운로드/활용신청", "키워드", "분류체계",
    "업데이트 주기", "수정일", "등록일",
    "주기성 데이터", "제공형태",
    #    "바로가기 횟수", "바로가기 링크",
    "URL", "상세링크", "제공기관유형"]