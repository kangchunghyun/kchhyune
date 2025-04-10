import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import os
import asyncio
import threading
from email import message_from_file
from email.policy import default
from aiosmtplib import SMTP, SMTPException

CHUNK_SIZE = 30
CHUNK_DELAY = 2

class EmailSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Chunked EML 발송기 Ultimate v4.0")
        self.root.geometry("800x700")
        self.stop_requested = False
        self.sent_set = set()
        self.success_count = 0
        self.fail_count = 0
        self.total_count = 0

        self._build_widgets()

    def _build_widgets(self):
        row = 0

        def label(text):
            return tk.Label(self.root, text=text)

        label("🏠 EML 루트 디렉토리").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.dir_entry = tk.Entry(self.root, width=50)
        self.dir_entry.grid(row=row, column=1, padx=5)
        tk.Button(self.root, text="찾기", command=self.browse_folder).grid(row=row, column=2, padx=5)
        row += 1

        label("🔁 반복 횟수").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.repeat_entry = tk.Entry(self.root)
        self.repeat_entry.insert(0, "1")
        self.repeat_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        label("⏱️ 간격 (초)").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.interval_entry = tk.Entry(self.root)
        self.interval_entry.insert(0, "0.2")
        self.interval_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        label("🌐 SMTP 호스트").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.smtp_host_entry = tk.Entry(self.root, width=40)
        self.smtp_host_entry.insert(0, "test.seculetter.net")
        self.smtp_host_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        label("📮 SMTP 포트").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.smtp_port_entry = tk.Entry(self.root, width=10)
        self.smtp_port_entry.insert(0, "25")
        self.smtp_port_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        self.no_login_var = tk.BooleanVar()
        self.no_login_var.set(False)
        self.no_login_check = tk.Checkbutton(
            self.root,
            text="로그인 없이 발송",
            variable=self.no_login_var,
            command=self.toggle_login_fields
        )
        self.no_login_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10)
        row += 1

        self.skip_cert_check_var = tk.BooleanVar()
        self.skip_cert_check = tk.Checkbutton(
            self.root,
            text="🔓 SSL 인증서 검증 생략 (자체 인증서용)",
            variable=self.skip_cert_check_var
        )
        self.skip_cert_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10)
        row += 1

        label("📧 SMTP 유저").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.smtp_user_entry = tk.Entry(self.root, width=40)
        self.smtp_user_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        label("🔐 SMTP 비밀번호").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.smtp_pass_entry = tk.Entry(self.root, show='*', width=40)
        self.smtp_pass_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        label("📩 고정 수신자 이메일").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.recipient_entry = tk.Entry(self.root, width=40)
        self.recipient_entry.grid(row=row, column=1, sticky="w", padx=5)
        row += 1

        self.send_button = tk.Button(self.root, text="🚀 발송 시작!", command=self.start_sending)
        self.send_button.grid(row=row, column=0, pady=20)

        self.stop_button = tk.Button(self.root, text="🛑 정지", command=self.stop_sending, state=tk.DISABLED)
        self.stop_button.grid(row=row, column=1, pady=20)
        row += 1

        self.progress = ttk.Progressbar(self.root, length=600, mode='determinate')
        self.progress.grid(row=row, column=0, columnspan=3, padx=10, pady=10)
        row += 1

        self.status_label = tk.Label(self.root, text="✅ 성공: 0  ❌ 실패: 0")
        self.status_label.grid(row=row, column=0, columnspan=3, padx=10)
        row += 1

        self.log_text = scrolledtext.ScrolledText(self.root, width=95, height=20)
        self.log_text.grid(row=row, column=0, columnspan=3, padx=10, pady=10)

    def toggle_login_fields(self):
        state = tk.DISABLED if self.no_login_var.get() else tk.NORMAL
        self.smtp_user_entry.config(state=state)
        self.smtp_pass_entry.config(state=state)

    def browse_folder(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def log(self, message):
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)

    def update_status(self):
        self.status_label.config(text=f"✅ 성공: {self.success_count}  ❌ 실패: {self.fail_count}")
        if self.total_count > 0:
            progress_percent = (self.success_count + self.fail_count) / self.total_count * 100
            self.progress['value'] = progress_percent
            self.root.update_idletasks()


    def start_sending(self):
        # 🔄 상태 초기화
        self.sent_set.clear()             # ✅ 이미 발송된 파일 초기화
        self.success_count = 0
        self.fail_count = 0
        self.total_count = 0
        self.progress['value'] = 0
        self.update_status()              # ✅ 카운트 UI 갱신

        self.send_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.run_async_loop).start()


    def stop_sending(self):
        self.stop_requested = True
        self.log("🛑 사용자 중지 요청!")

    def run_async_loop(self):
        asyncio.run(self.send_emails_async())
        self.send_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    async def send_emails_async(self):
        self.success_count = 0
        self.fail_count = 0

        root_dir = self.dir_entry.get()
        repeat_count = int(self.repeat_entry.get())
        interval = float(self.interval_entry.get())
        smtp_user = self.smtp_user_entry.get()
        smtp_pass = self.smtp_pass_entry.get()
        smtp_host = self.smtp_host_entry.get()
        smtp_port = int(self.smtp_port_entry.get())
        use_login = not self.no_login_var.get()
        fixed_recipient = self.recipient_entry.get()

        eml_files = self.find_eml_files(root_dir)
        if not eml_files:
            self.log("❌ EML 파일이 없습니다!")
            return

        self.total_count = len(eml_files) * repeat_count
        self.progress['value'] = 0
        self.update_status()

        for round_num in range(repeat_count):
            if self.stop_requested:
                self.log("🛑 중단됨 - 반복 시작 전")
                return

            self.log(f"🔁 반복 {round_num + 1}/{repeat_count} 시작")

            for chunk_start in range(0, len(eml_files), CHUNK_SIZE):
                if self.stop_requested:
                    self.log("🛑 중단됨 - Chunk 시작 전")
                    return

                chunk = eml_files[chunk_start:chunk_start + CHUNK_SIZE]
                tasks = [
                    self.send_eml_file_async(eml_path, smtp_user, smtp_pass, smtp_host, smtp_port, use_login, fixed_recipient, interval * idx)
                    for idx, eml_path in enumerate(chunk)
                    if eml_path not in self.sent_set
                ]
                await asyncio.gather(*tasks)
                await asyncio.sleep(CHUNK_DELAY)

        self.log("🏁 전체 발송 완료!")

    async def send_eml_file_async(self, eml_path, smtp_user, smtp_pass, smtp_host, smtp_port, use_login, recipient, delay):
        if self.stop_requested:
            return

        await asyncio.sleep(delay)

        try:
            with open(eml_path, 'r', encoding='utf-8') as f:
                msg = message_from_file(f, policy=default)

            msg.replace_header('To', recipient)
            for header in ('Cc', 'Bcc'):
                if header in msg:
                    del msg[header]

            validate_certs = not self.skip_cert_check_var.get()

            smtp = SMTP(hostname=smtp_host, port=smtp_port, start_tls=True, validate_certs=False)
            await smtp.connect()

            if use_login and smtp_user and smtp_pass:
                await smtp.login(smtp_user, smtp_pass)

            await smtp.send_message(msg)
            await smtp.quit()

            self.success_count += 1
            self.sent_set.add(eml_path)
            self.log(f"✅ 발송됨: {os.path.basename(eml_path)}")
        except Exception as e:
            self.fail_count += 1
            self.log(f"❌ 실패: {os.path.basename(eml_path)} → {e}")
        finally:
            self.update_status()

    def find_eml_files(self, root_dir):
        eml_files = []
        for subdir, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith('.eml'):
                    eml_files.append(os.path.join(subdir, file))
        return eml_files

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailSenderGUI(root)
    root.mainloop()
