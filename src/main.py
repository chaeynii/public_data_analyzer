from crawler import crawl_data
from analyzer import analyze_data
import config

def main():
    # 크롤링 실행
    crawled_data = crawl_data(config.REQUEST_PARAMS['org'])
    
    # 분석 실행
    analyze_data(crawled_data, config.REQUEST_PARAMS['org'])

if __name__ == "__main__":
    main()
