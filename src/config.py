# src/config.py

import json
import os

BASE_URL = "https://www.data.go.kr"
REQUEST_PARAMS = {
    'dType': '',
    'keyword': '',
    'operator': '',
    'detailKeyword': '',
    'publicDataPk': '',
    'recmSe': '',
    'detailText': '',
    'relatedKeyword': '',
    'commaNotInData': '',
    'commaAndData': '',
    'commaOrData': '',
    'must_not': '',
    'tabId': '',
    'dataSetCoreTf': '',
    'coreDataNm': '',
    'sort': 'updtDt',
    'relRadio': '',
    'orgFullName': '',
    'orgFilter': '',
    'org': '',
    'orgSearch': '',
    'currentPage': 1,
    'perPage': 10,
    'brm': '',
    'instt': '',
    'svcType': '',
    'kwrdArray': '',
    'extsn': '',
    'coreDataNmArray': '',
    'pblonsipScopeCode': ''
}

# JSON 파일 경로
INPUT_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'input.json')

# 기관 이름 로드
def load_agency_name():
    with open(INPUT_FILE_PATH, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data.get("agency_name", "")

# 기관 이름을 가져와 REQUEST_PARAMS에 설정
ORG_NAME = load_agency_name()
REQUEST_PARAMS['org'] = ORG_NAME
REQUEST_PARAMS['orgFullName'] = ORG_NAME
REQUEST_PARAMS['orgFilter'] = ORG_NAME