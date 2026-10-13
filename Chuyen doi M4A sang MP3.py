import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import subprocess

# Thiết lập giao diện mặc định
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AudioConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Phần Mềm Chuyển Đổi M4A sang MP3")
        self.geometry("500x250")
        
        self.filepath = ""
        
        # Tiêu đề
        self.label = ctk.CTkLabel(self, text="Chọn file M4A cần chuyển đổi", font=("Arial", 16, "bold"))
        self.label.pack(pady=20)
        
        # Nút chọn file
        self.btn_select = ctk.CTkButton(self, text="Chọn File", command=self.select_file)
        self.btn_select.pack(pady=10)
        
        # Nút chuyển đổi
        self.btn_convert = ctk.CTkButton(self, text="Chuyển sang MP3", command=self.start_conversion, state="disabled")
        self.btn_convert.pack(pady=10)
        
        # Nhãn thông báo trạng thái
        self.status_label = ctk.CTkLabel(self, text="", font=("Arial", 13))
        self.status_label.pack(pady=10)

    def select_file(self):
        self.filepath = filedialog.askopenfilename(filetypes=[("M4A Files", "*.m4a")])
        if self.filepath:
            filename = os.path.basename(self.filepath)
            self.label.configure(text=f"Đã chọn: {filename}")
            self.btn_convert.configure(state="normal")
            self.status_label.configure(text="")

    def start_conversion(self):
        self.btn_convert.configure(state="disabled")
        self.btn_select.configure(state="disabled")
        self.status_label.configure(text="Đang xử lý âm thanh... Vui lòng đợi!", text_color="#f39c12")
        
        # Chạy luồng (Thread) riêng để giao diện không bị treo
        threading.Thread(target=self.process_audio, daemon=True).start()

    def process_audio(self):
        try:
            # Xác định đường dẫn file MP3 đầu ra
            output_path = os.path.splitext(self.filepath)[0] + ".mp3"
            
            # ĐÃ SỬA CHUẨN XÁC TỌA ĐỘ: Trỏ thẳng vào file ffmpeg.exe bên ngoài
           
            ffmpeg_path = r"C:\Program Files\ffmpeg\ffmpeg.exe"
            
            # Ra lệnh ép chất lượng âm thanh cao nhất
            command = [ffmpeg_path, "-y", "-i", self.filepath, "-q:a", "0", output_path]
            
            # creationflags=0x08000000 giúp ẩn cửa sổ đen khi chạy ngầm
            result = subprocess.run(command, capture_output=True, text=True, creationflags=0x08000000)
            
            if result.returncode == 0:
                filename = os.path.basename(output_path)
                self.status_label.configure(text=f"Thành công! Đã lưu: {filename}", text_color="#2ecc71")
            else:
                self.status_label.configure(text="Lỗi: FFmpeg gặp sự cố khi chuyển!", text_color="#e74c3c")
                
        except Exception as e:
            # Bắt lỗi chính xác và in ra
            self.status_label.configure(text=f"Lỗi: {str(e)[:40]}...", text_color="#e74c3c")
        finally:
            self.btn_convert.configure(state="normal")
            self.btn_select.configure(state="normal")

if __name__ == "__main__":
    app = AudioConverterApp()
    app.mainloop()
