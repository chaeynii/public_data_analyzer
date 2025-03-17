from config.common_imports import *
from config.logging_config import setup_logging

logger = setup_logging("file_utils.log")

def save_to_excel(df, file_path):
    try:
        df.to_excel(file_path, index=True, engine='openpyxl')
        logger.info(f"Data saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save {file_path} : {e}")
        
def load_json(file_path):
    if not os.path.exists(file_path):
        logger.error(f"'{file_path}' 파일을 찾을 수 없습니다.")
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if not data:
                logger.warning(f"'{file_path}' 파일이 비어 있습니다.")
            return data
    except Exception as e:
        logger.error(f"JSON 파일 로드 중 오류 발생: {e}")
        return None