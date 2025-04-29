# gui_main.py
import tkinter as tk
from tkinter import filedialog, ttk
from db_utils import connect_to_db, copy_file_from_db
from file_utils import  run_csv_insertion 
import config


# ------------------------- 기본 설정 -------------------------
root = tk.Tk()
root.title("FileInfo DB GUI")
#root.geometry("600x600")
root.resizable(False, False)

config.progress_var = tk.DoubleVar(value=0)
config.status_var = tk.StringVar(value="💤 대기 중입니다...")

config.file_path_var = tk.StringVar()
config.destination_path = tk.StringVar()
config.filename_list_path = tk.StringVar()
config.tags = tk.StringVar()
config.filename_entry = tk.StringVar()
config.filename_list = tk.StringVar()
config.cur = tk.StringVar()
config.copy_tag_mode = tk.StringVar(value="or")

# ------------------------- 노트북 탭 구성 -------------------------
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

tab_db = ttk.Frame(notebook)
tab_update = ttk.Frame(notebook)
tab_search = ttk.Frame(notebook)

notebook.add(tab_db, text="DB 접속")
notebook.add(tab_update, text="DB 업데이트")
notebook.add(tab_search, text="파일 가져오기")

# ------------------------- DB 접속 탭 -------------------------
db_frame = tk.LabelFrame(tab_db, text="[DB 접속 정보]", padx=10, pady=10)
db_frame.pack(padx=10, pady=10, fill="x")

tk.Label(db_frame, text="DB IP:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
host_entry = tk.Entry(db_frame, width=30)
host_entry.grid(row=0, column=1)

tk.Label(db_frame, text="사용자:").grid(row=1, column=0, padx=10, sticky="e")
user_entry = tk.Entry(db_frame, width=30)
user_entry.grid(row=1, column=1)

tk.Label(db_frame, text="비밀번호:").grid(row=2, column=0, padx=10, sticky="e")
password_entry = tk.Entry(db_frame, width=30, show="*")
password_entry.grid(row=2, column=1)

tk.Button(db_frame, text="Connect", command=lambda: connect_to_db(host_entry, user_entry, password_entry)).grid(row=3, column=1, padx=5, pady=10, sticky="w")

# ------------------------- DB 업데이트 탭 -------------------------
input_frame = tk.LabelFrame(tab_update, text="[DB 업데이트]")
input_frame.pack(fill="x", padx=10, pady=10, ipady=5)

# 파일 경로 입력
tk.Label(input_frame, text="파일 경로:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
tk.Entry(input_frame, textvariable=config.filename_list_path, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="w")
tk.Button(input_frame, text="찾기", 
          command=lambda: config.filename_list_path.set(
                filedialog.askopenfilename(
                    filetypes=[("Text/CSV Files", "*.csv;*.txt")]
                    )
                )
        ).grid(row=0, column=2, padx=5, pady=5)

# 태그 입력
tk.Label(input_frame, text="태그 입력:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
tk.Entry(input_frame, textvariable=config.tags, width=30).grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="w")

# 버튼 라인
insert_btn = tk.Button(input_frame, text="입력", width=20, command=lambda: run_csv_insertion(config.progress_var, insert_btn, config.batch_size))
insert_btn.grid(row=2, column=1, padx=5, pady=10, sticky="w")

# ------------------------- 파일 가져오기 탭 -------------------------
def toggle_entry():
    # 입력 필드 레이블 업데이트
    copy_label.config(text=f"{copy_radio_mode.get()}: ")

    if copy_radio_mode.get() == "List":
        copy_input_entry.config(state="normal")
        config.filename_entry.set("")
        open_button.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        tag_mode_frame.grid_remove()  # Tag 검색 모드 숨기기
    else:
        copy_input_entry.config(state="normal")
        config.tags.set("")
        open_button.grid_remove()
        tag_mode_frame.grid()  # Tag 검색 모드 보이기

copy_radio_mode = tk.StringVar(value="List")  # "List" 또는 "Tag"
config.copy_tag_mode = tk.StringVar(value="or")     # "and" 또는 "or"

search_frame = tk.LabelFrame(tab_search, text="[파일 가져오기]")
search_frame.pack(fill="x", padx=10, pady=10, ipady=5)

# 복사 위치 입력
tk.Label(search_frame, text="Dst:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
tk.Entry(search_frame, textvariable=config.destination_path, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="w")
tk.Button(search_frame, text="찾기",
          command=lambda: config.destination_path.set(filedialog.askdirectory())
          ).grid(row=0, column=2, padx=5, pady=5)

# 복사 대상 모드 선택 (Src / Tag)
mode_select_frame = tk.Frame(search_frame)
mode_select_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
tk.Radiobutton(mode_select_frame, text="List", value="List", variable=copy_radio_mode, command=toggle_entry).pack(side="left", padx=10)
tk.Radiobutton(mode_select_frame, text="Tag", value="Tag", variable=copy_radio_mode, command=toggle_entry).pack(side="left", padx=10)

# 복사 대상 입력 필드 + 레이블
copy_label = tk.Label(search_frame, text="List:")
copy_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")

copy_input_entry = tk.Entry(search_frame, textvariable=config.filename_entry, width=40)
copy_input_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# 열기 버튼 (초기에는 보이게)
open_button = tk.Button(search_frame, text="열기",
                        command=lambda: config.filename_entry.set(
                            filedialog.askopenfilename(filetypes=[("Text/CSV Files", "*.csv;*.txt")])
                        ))
open_button.grid(row=2, column=2, padx=5, pady=5, sticky="w")

# TAG 검색 모드 (AND / OR)
tag_mode_frame = tk.Frame(search_frame)
tag_mode_frame.grid(row=3, column=0, columnspan=3, pady=(5, 0))

# [초기에 숨기기] - List 선택이 기본이니까
if copy_radio_mode.get() == "List":
    tag_mode_frame.grid_remove()

tk.Label(tag_mode_frame, text="[검색 모드]").pack(side="left", padx=5)
tk.Radiobutton(tag_mode_frame, text="AND", value="and", variable=config.copy_tag_mode).pack(side="left", padx=5)
tk.Radiobutton(tag_mode_frame, text="OR", value="or", variable=config.copy_tag_mode).pack(side="left", padx=5)

# 파일 복사 버튼 (강조)
file_copy_btn = tk.Button(search_frame, text="파일 복사", font=("맑은 고딕", 12, "bold"),
    bg="#4CAF50", fg="white", padx=20, pady=5,
    command=lambda: copy_file_from_db(
        *(("file", copy_input_entry.get(), config.destination_path.get(), "OR") if copy_radio_mode.get() == "List"
          else ("tag", copy_input_entry.get(), config.destination_path.get(), config.copy_tag_mode.get().upper()))
    )
)

file_copy_btn.grid(row=4, column=1, padx=3, pady=10, sticky="w")

# ------------------------- 상태바 -------------------------
status_frame = ttk.Frame(root)
status_frame.pack(fill="x", padx=10, pady=10, ipady=5)

status_label = tk.Label(status_frame, textvariable=config.status_var, anchor="w", relief="sunken")
status_label.grid(row=4, column=0, columnspan=3, sticky="we", padx=5, pady=(0, 5))

progress_bar = ttk.Progressbar(status_frame, variable=config.progress_var, maximum=100)
progress_bar.grid(row=3, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="we")
config.progress_bar = progress_bar

root.mainloop()