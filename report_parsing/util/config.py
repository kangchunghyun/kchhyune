# DB 접속 정보
config = {
    "DB_HOST": "",
    "DB_USER": "",
    "DB_PASSWORD": "",
    "DB_NAME": "postgres",
    "DB_PORT": 5432,
}

# 헬퍼 함수
def deep_get(dct, keys, default=None):
    for key in keys:
        if isinstance(dct, dict):
            dct = dct.get(key, default)
        else:
            return default
    return dct

def extract_field_from_list(data_list, field):
    if not isinstance(data_list, list):
        return []
    return [item.get(field) for item in data_list if isinstance(item, dict)]

def get_first_match(items, key, value, target):
    for item in items:
        if item.get(key) == value:
            return item.get(target)
    return None

def extract_nested_list(data_list, outer_field, inner_field):
    """
    리스트 안 딕셔너리에서 내부 리스트(outer_field)를 꺼내어 inner_field 추출
    """
    results = []
    for item in data_list:
        if isinstance(item, dict):
            for entry in item.get(outer_field, []):
                if isinstance(entry, dict):
                    results.append(entry.get(inner_field))
    return results

def extract_field_from_list(data_list, field):
    return [item.get(field) for item in data_list if isinstance(item, dict)]