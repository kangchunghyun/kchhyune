import os
import json
import datetime
import pandas as pd
import concurrent.futures
from util.config import deep_get, extract_field_from_list, extract_nested_list, get_first_match

def parse_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        root = data.get("fileAnalysisResults", [])[0]
        return {
            # 분석 타겟 관련 필드 추가
            "sha256": root.get("sha256",None),
            "filename": root.get("fileName",None),
            "mimetype": root.get("mimeType",None),
            "extension": root.get("detectedExtension",None),
            "filesize": (root.get("size") or 0),

            # 분석 엔진 관련 필드 추가
            "slepversion": root.get("version",None),
            "summaryresult": root.get("summaryResult",None),
            "summaryexploitname": root.get("summaryExploitName",None),
            "set0time": get_first_match(root.get("analyserInfos", []), "analyserName", "EngineSet 0", "elapsedTime"),
            "set1time": get_first_match(root.get("analyserInfos", []), "analyserName", "EngineSet 1", "elapsedTime"),
            "events": [[event.get("Name",None)] for event in root.get("events", [])],
            "severity": [[item.get("Severity",None)] for item in root.get("events", [])],
            "slename": [[item.get("SLEName",None)] for item in root.get("events", [])],
            "sleversion": [[item.get("SLEVersion",None)] for item in root.get("events", [])],
            "shortmsgko": [[item.get("ShortMsg",{}).get("lang=ko",None)] for item in root.get("events", [])],
            "shortmsgen": [[item.get("ShortMsg",{}).get("lang=en",None)] for item in root.get("events", [])],
            "longmsgko": [[item.get("LongMsg",{}).get("lang=ko",None)] for item in root.get("events", [])],
            "longmsgen": [[item.get("LongMsg",{}).get("lang=en",None)] for item in root.get("events", [])],

            # cdr 관련 필드 추가
            "cdrversion": deep_get(root, ["cdrResult", "cdrMarsReport", "version", "cdrVersion"]),
            "cdrdetectedfiletype": deep_get(root, ["cdrResult", "cdrMarsReport", "fileInfo", "extensionType"]),
            "cdrresult": deep_get(root, ["cdrResult", "cdrMarsReport", "statusInfo", "status"]),
            "cdrstatus": deep_get(root, ["cdrResult", "cdrMarsReport", "statusInfo", "message"]),
            "cdrdetailmessage": deep_get(root, ["cdrResult", "cdrMarsReport", "statusInfo", "detailMessage"]),
            "cdrpolicy": deep_get(root, ["cdrResult", "cdrMarsReport", "policy", "policies"]),
            "cdrpolicydetail": deep_get(root, ["cdrResult", "cdrMarsReport", "policy", "details"]),
            "cdrtime": deep_get(root, ["cdrResult", "cdrMarsReport", "statusInfo", "elapsedTime"]),
            
            "cdrcategory": [extract_field_from_list(deep_get(root, ["cdrResult", "cdrMarsReport", "reportItems"]) or [], "category")],
            "cdraction": [extract_field_from_list(deep_get(root, ["cdrResult", "cdrMarsReport", "reportItems"]) or [], "action")],
            #"cdrcontent": [extract_field_from_list(item.get("detailEntries", []), "content") for item in deep_get(root, ["cdrResult", "cdrMarsReport", "reportItems"], []) or []],
            "cdrmode": [extract_field_from_list(item.get("detailEntries", []), "mode") for item in deep_get(root, ["cdrResult", "cdrMarsReport", "reportItems"], [])or []]
        }
        
    except Exception as e:
        print(f"[ERROR] {filepath} 처리 실패: {e}")
        return None

def analysis_parser_parallel_pd(src_dir, dest_dir):
    if not os.path.exists(src_dir):
        print(f"[ERROR] {src_dir} 경로가 없습니다.")
        return
        #raise FileNotFoundError(f"{src_dir} 경로가 없습니다.")
    if not os.path.exists(dest_dir):
        print(f"[INFO] {dest_dir} 경로가 없습니다. 생성합니다.")
        os.makedirs(dest_dir)
        return
        #raise FileNotFoundError(f"{src_dir} 경로가 없습니다.")

    json_files = [
        os.path.join(src_dir, f) for f in os.listdir(src_dir)
        if f.endswith('.json')
    ]

    # 병렬 처리 시작
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(executor.map(parse_json_file, json_files))

    # 유효한 결과만 필터링
    valid_results = [r for r in results if r is not None]

    # pandas DataFrame으로 저장
    df = pd.DataFrame(valid_results)
    csv_path = os.path.join(
        dest_dir,
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_SecuLetter_Sample_Data.csv"
    )
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"[INFO] CSV 저장 완료: {csv_path}")

