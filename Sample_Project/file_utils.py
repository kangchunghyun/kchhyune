# file_utils.py
from pathlib import Path
import shutil
import config
import csv
from db_utils import insert_fileinfo_record
from tkinter import scrolledtext, Toplevel, filedialog, messagebox

# 신규 파일 복사 함수(미완성)
def copy_file_from_dirs(file, search_dirs, dest_dir):
    """
    search_dirs 리스트에서 file을 찾은 후,
    찾으면 해당 파일을 dest_dir로 복사하고 True 반환.
    없으면 False 반환.
    """
    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            prefix = line[:3]
            candidate = Path(search_dirs) / prefix / line
            print(f"Checking: {candidate}")
            if candidate.exists():
                shutil.copy2(candidate, Path(dest_dir) / line)
                return True
    # 파일이 존재하지 않으면 False 반환 
        return False
    
# ------------------------- 파일 선택 함수 -------------------------
def select_filename_list():
    filename = filedialog.askopenfilename(filetypes=[("Text/CSV Files", "*.csv;*.txt")])
    config.filename_list_path.set(filename)

# ------------------------- DB 업데이트 함수  -------------------------
def run_csv_insertion(progress_var, button, batch_size):
    progress_var.set(0)
    config.progress_bar.update_idletasks()

    config.status_var.set("DB 업데이트 중...")

    filepath = config.filename_list_path.get()
    tag_input = config.tags.get().split(',')  # 쉼표로 분리
    
    if not config.conn:
        config.status_var.set("경고 - DB에 연결되어 있지 않습니다.")
        return
    
    if not filepath:
        config.status_var.set("경고 - CSV 파일 경로가 없습니다.")
        return
    
    button.config(state="disabled")

    inserted = 0
    failed = 0

    try:
        with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
            reader = list(csv.DictReader(csvfile))
            row_count = len(reader)

            if row_count == 0:
                messagebox.showerror("오류", "CSV 파일이 비어 있습니다.")
                config.status_var.set("CSV 파일이 비어 있습니다.")
                return
            
            for batch_start in range(0, row_count, batch_size):
                batch = reader[batch_start:batch_start + batch_size]
                batch_failed = False
                
                for row in batch:
                    if insert_fileinfo_record(row, tag_input):
                        inserted += 1
                        
                    else:
                        failed += 1
                        batch_failed = True

                if batch_failed:
                    config.conn.rollback()

                else: 
                    config.conn.commit()


                progress = ((batch_start + len(batch)) / row_count) * 100
                progress_var.set(progress)
                config.progress_bar.update_idletasks()

        config.status_var.set(f"삽입 완료: {inserted}건, 실패: {failed}건")
        progress_var.set(100)

    except Exception as e:
        print("오류", f"파일 열기 실패 또는 DB 오류: {e}")
        #messagebox.showerror("오류", f"파일 열기 실패 또는 DB 오류: {e}")
        config.status_var.set(f"오류: {e}")

    finally:
        button.config(state="normal")