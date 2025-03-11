from config.common_imports import *
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "").strip()
ORG_NAME = os.getenv("ORG_NAME", "")

REQUEST_PARAMS = {
    'dType': '',
    'sort': 'updtDt',
    'org': ORG_NAME,
    'currentPage': 1,
    'perPage': 40,
}

# 데이터 타입별 컬럼 설정
DATA_TYPES = {
    "FILE": ["데이터명", "설명", "확장자", "제공기관", "조회수", "다운로드", "키워드", "업데이트 주기", "수정일", "등록일", "주기성 데이터", "제공형태", "URL", "상세링크", "분류체계"],
    "API": ["데이터명", "설명", "데이터포맷", "제공기관", "조회수", "활용신청", "키워드", "수정일", "등록일", "상세링크", "분류체계"],
    "LINKED": ["데이터명", "설명", "확장자", "제공기관", "조회수", "키워드", "수정일", "등록일", "바로가기 횟수", "바로가기 링크", "상세링크", "분류체계"]
}