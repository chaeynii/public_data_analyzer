# 공공데이터 포털 데이터 수집 및 분석

## 프로젝트 개요

공공데이터 포털(data.go.kr)에서 특정 기관의 데이터셋을 자동으로 수집하고 분석하는 도구

파일 데이터, API, 연계 데이터 등 다양한 유형의 공공데이터를 효율적으로 크롤링하여 엑셀 파일로 저장함

## 주요 기능

- 기관명 기반 데이터 검색 및 수집
- 파일 데이터, API, 연계 데이터 유형별 크롤링
- 데이터 상세 정보 자동 추출
- 수집된 데이터의 엑셀 파일 저장
- 멀티프로세싱을 통한 고속 데이터 수집 (선택적)

## 시스템 요구사항

- Python 3.7+
- pandas
- requests
- BeautifulSoup4

## 설치 방법

1. 저장소 클론

    `git clone https://github.com/your-username/public-data-crawler.git`

2. 프로젝트 디렉토리로 이동

    `cd public-data-crawler`

3. 필요한 패키지 설치

    `pip install -r requirements.txt`


## 사용 방법

1. .env 환경변수 파일 생성

```
BASE_URL = "https://www.data.go.kr"
ORG_NAME = ""
```

2. 다음 명령어를 실행하여 크롤링을 시작

    `python src/main.py`


3. 수집된 데이터는 `data` 폴더 내에 엑셀 파일로 저장됨

## 프로젝트 구조
```
public_data_crawler/
├── src/
│ ├── config.py
│ ├── crawler.py
│ ├── data_handlers.py
│ └── utils.py
├── data/
├── input.json
├── requirements.txt
└── README.md
```

## 주의사항

- 공공데이터 포털의 이용 정책을 준수하여 사용해주세요.
- 대량의 데이터를 수집할 경우 서버에 부하를 줄 수 있습니다.

## 연락처
관리자 : chaeyni.w@gmail.com

프로젝트 링크 [https://github.com/chaeynii/public-data-crawler]
