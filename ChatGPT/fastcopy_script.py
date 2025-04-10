
import os
import time
import shutil
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# 설정
base_dir = "C:/example/source"
upload1 = "C:/example/destination"
dirCount = 100         # upload 디렉토리 내 참고 파일 수 (초과 시 대기)
chunk_size = 1000      # 한 번에 복사할 파일 개수
max_workers = 4        # 병렬 복사 스레드 수

copied_files = set()   # 복사 완료된 파일 경로 기록 (재복사 방지)

# --------------------------
# 디렉토리 탐색 함수
# --------------------------
def subDirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

# --------------------------
# 제너레이터: 모든 파일 하나씩 반환
# --------------------------
def yield_all_files(base_dir):
    for file in Path(base_dir).glob("*.*"):
        if file.is_file():
            yield file
    for sub in subDirs(base_dir):
        subDir = os.path.join(base_dir, sub)
        for file in Path(subDir).glob("*.*"):
            if file.is_file():
                yield file

# --------------------------
# Chunk로 나누는 헬퍼 함수
# --------------------------
def chunked_iterable(iterable, chunk_size):
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

# --------------------------
# FastCopy 스타일 복사 함수
# --------------------------
def fastcopy_style(src_path, dst_dir):
    dst_file = os.path.join(dst_dir, os.path.basename(src_path))

    # 재복사 방지
    if str(src_path) in copied_files:
        print(f"⏩ SKIP (이미 복사됨): {src_path}")
        return

    # 디렉토리 용량 확인
    while len(os.listdir(dst_dir)) >= dirCount:
        print("📦 디렉토리 포화 상태. 5초 대기 중...")
        time.sleep(5)

    # 복사 시도
    try:
        with open(src_path, 'rb') as fsrc, open(dst_file, 'wb') as fdst:
            shutil.copyfileobj(fsrc, fdst, length=16 * 1024 * 1024)

        copied_files.add(str(src_path))
        print(f"✅ Copied: {src_path} → {dst_file}")

    except Exception as e:
        print(f"❌ 복사 실패: {src_path} | 오류: {e}")

# --------------------------
# 복사 수행
# --------------------------
print("🚀 복사 시작!")
for file_chunk in chunked_iterable(yield_all_files(base_dir), chunk_size):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for file in tqdm(file_chunk, desc="📦 복사 중", unit="file"):
            executor.submit(fastcopy_style, str(file), upload1)

print("🎉 복사 완료!")
