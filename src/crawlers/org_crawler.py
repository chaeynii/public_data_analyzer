from config.common_imports import *
import config.settings
from config.logging_config import setup_logging

SetList_URL = config.settings.BASE_URL + "/tcs/dss/selectDataSetList.do"
ORG_NAME = config.settings.ORG_NAME

logger = setup_logging("org_crawler.log")

def org_crawler():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 크롬드라이브 실행 여부
    driver = webdriver.Chrome(service=service, options=options)

    # 산하기관 리스트 저장
    sub_organizations = []

    try:
        # 1. url 접속
        driver.get(SetList_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "orgBtn")))
        logger.info("1. SetList_URL 접속 성공")

        # 2. Click "제공기관별 검색" button
        org_btn = driver.find_element(By.ID, "orgBtn")
        org_btn.click()
        logger.info("2. Clicked organization search button")

        # 3. Enter organization name in search input
        search_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "orgNm")))
        search_input.send_keys(ORG_NAME)
        logger.info(f"3. Entered organization name: {ORG_NAME}")

        # 4. Click the search button
        search_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".form-wrap .button.blue")))
        search_button.click()
        logger.info("4. Clicked search button.")

        # 5. 해당 기관 찾기
        tree_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#jstreeDiv li[role='treeitem'] > a.jstree-anchor"))
        )

        parent_li = None
        for item in tree_items:
            if ORG_NAME in item.text:
                logger.info(f"----- Found organization: {item.text}")

                # Find the <li role="treeitem"> that wraps this <a>
                parent_li = item.find_element(By.XPATH, "./parent::li[@role='treeitem']")

                # 해당 a 태그의 id 값 저장
                parent_li_id = parent_li.get_attribute("id")
                if not parent_li_id:
                    parent_li_id = "generated-" + str(hash(item.text))  # Generate a unique ID
                    driver.execute_script("arguments[0].setAttribute('id', arguments[1]);", parent_li, parent_li_id)

                logger.info(f"----- Found parent `<li>` with ID: {parent_li_id}")
                break

        if parent_li is None:
            logger.error(f"XXXXX Organization '{ORG_NAME}' not found in the tree.")
            return

        # 6. 산하기관이 있을 경우 저장
        try:
            sub_org_group = parent_li.find_element(By.CSS_SELECTOR, "ul[role='group']")
            sub_orgs = sub_org_group.find_elements(By.CSS_SELECTOR, "li[role='treeitem'] > a.jstree-anchor")

            logger.info(f"----- Collecting direct sub-organizations under '{ORG_NAME}':")
            for sub in sub_orgs:
                sub_name = sub.get_attribute("textContent").strip()
                sub_organizations.append(sub_name)

            # Save to JSON
            with open("logs/sub_organizations.json", "w", encoding="utf-8") as file:
                json.dump(sub_organizations, file, ensure_ascii=False, indent=4)

        except:
            logger.error(f"XXXXX No sub-organizations found under '{ORG_NAME}'.")
            print(f"XXXXX No sub-organizations found under '{ORG_NAME}'.")

    finally:
        driver.quit()

    return sub_organizations

async def main():
    return org_crawler()

if __name__ == "__main__":
    sub_orgs = asyncio.run(main())
    logger.info(f"Sub-Organizations Extracted: {sub_orgs}")
    print(f"Sub-Organizations Extracted: {sub_orgs}")