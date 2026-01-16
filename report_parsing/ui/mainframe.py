import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
import threading
from parser.analysis_json import analysis_parser_parallel_pd
from util.database import Database
import time
import traceback

class MainFrame(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SecuLetter - Report Generator")
        self.geometry("420x300")

        self._create_widgets()

    def long_running_task(self):
        import time
        max_value = 100
        for i in range(max_value + 1):
            time.sleep(0.1)  # Simulate a long-running task
            self.progress_var.set(i)
            self.update_idletasks()  # Update the UI
        messagebox.showinfo("Info", "Parsing completed!")

    def _create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # Main 탭
        tab_main = ttk.Frame(notebook)
        main_frame = tk.LabelFrame(tab_main, text="[DB Connect]", labelanchor="n")
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="DB Host: ").grid(row=0, column=0, sticky="w", padx=10)
        self.db_host_entry = tk.Entry(main_frame, width=30)
        self.db_host_entry.grid(row=0, column=1, padx=15)
        tk.Label(main_frame, text="User: ").grid(row=2, column=0, sticky="w", padx=10)
        self.db_user_entry = tk.Entry(main_frame, width=30)
        self.db_user_entry.grid(row=2, column=1, padx=15)
        tk.Label(main_frame, text="Password: ").grid(row=3, column=0, sticky="w", padx=10)
        self.db_password_entry = tk.Entry(main_frame, show="*", width=30)
        self.db_password_entry.grid(row=3, column=1, padx=15)
        
        tk.Button(main_frame, text="Connect", font=("맑은 고딕", 12, "bold"), bg="#4CAF50", fg="white", 
                  command=self.connect_db).grid(row=0, rowspan=3, sticky="ns", column=3)

        # Report 탭
        tab_parser = ttk.Frame(notebook)
        parser_frame = tk.LabelFrame(tab_parser, text="[Report Generator]", labelanchor="n")
        parser_frame.pack(fill="both", expand=True)

        tk.Label(parser_frame, text="Report(json) Dir: ").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.src_dir_entry = tk.Entry(parser_frame, width=20)
        self.src_dir_entry.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(parser_frame, text="Browse", command=lambda: (self.src_dir_entry.delete(0, tk.END), self.src_dir_entry.insert(0, filedialog.askdirectory()))).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(parser_frame, text="Report(csv) Dir: ").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.dest_dir_entry = tk.Entry(parser_frame, width=20)
        self.dest_dir_entry.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(parser_frame, text="Browse", command=lambda: (self.dest_dir_entry.delete(0, tk.END), self.dest_dir_entry.insert(0, filedialog.askdirectory()))).grid(row=1, column=2, padx=10, pady=10)

        parser_frame_button = tk.Frame(parser_frame)
        parser_frame_button.grid(row=2, column=0, columnspan=3, pady=10)
        tk.Button(parser_frame_button, text="Parsing", command=self._run_parser).grid(row=0, column=1, padx=10, pady=10)

        # Upsert 탭
        tab_upsert = ttk.Frame(notebook)
        upsert_frame = tk.LabelFrame(tab_upsert, text="[DB Upsert]", labelanchor="n")
        upsert_frame.pack(fill="both", expand=True)
        tk.Label(upsert_frame, text="Data =").grid(row=0, column=0, sticky="w", padx=10)
        self.upsertData_entry = tk.Entry(upsert_frame, width=30)
        self.upsertData_entry.grid(row=0, column=1, padx=15)
        tk.Button(upsert_frame, text="Browse", command=lambda: (self.upsertData_entry.delete(0, tk.END), self.upsertData_entry.insert(0, filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv;")])))).grid(row=0, column=2, padx=10, pady=10)
        tk.Button(upsert_frame, text="Upsert", font=("맑은 고딕", 12, "bold"), bg="#4CAF50", fg="white", command=self.upsert_data).grid(row=1, column=1, padx=10, pady=10)
    

        # 탭 추가
        notebook.add(tab_main, text="Main")
        notebook.add(tab_parser, text="Report")
        notebook.add(tab_upsert, text="Upsert")

    def connect_db(self):
        host = self.db_host_entry.get()
        user = self.db_user_entry.get()
        password = self.db_password_entry.get()

        db = Database(
            host=host,
            user=user,
            password=password
        )
        
        if db.test_connection():
            self.db = db
            self.db_host_entry.config(state="readonly")
            self.db_user_entry.config(state="readonly")
            self.db_password_entry.config(state="readonly")
            messagebox.showinfo("성공", "연결 성공!")
        else:
            messagebox.showerror("실패", "연결 실패!")

    def upsert_data(self):
        if not self.db:
            messagebox.showerror("Error", "DB에 연결되지 않았습니다.")
            return
        
        data = self.upsertData_entry.get()
        if not data:
            messagebox.showerror("Error", "업로드할 데이터가 없습니다.")
            return
        try:
            self.db.upsert_unified_data(data)
            messagebox.showinfo("Info", "업로드 완료!")

        except Exception as e:
            print(traceback.format_exc())
            messagebox.showerror("Error", f"업로드 실패: {e}")

    def _run_parser(self):
        messagebox.showinfo("Info", "Parsing started!")
        thread = threading.Thread(
            target=analysis_parser_parallel_pd,
            args=(self.src_dir_entry.get(), self.dest_dir_entry.get())
        )
        thread.start()

    
