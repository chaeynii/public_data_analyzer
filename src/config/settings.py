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
    'perPage': 10,
}