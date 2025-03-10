from config.common_imports import *

REQUEST_PARAMS = {
    'dType': '',
    'sort': 'updtDt',
    'org': os.getenv("ORG_NAME", ""),
    'currentPage': 1,
    'perPage': 10,
}