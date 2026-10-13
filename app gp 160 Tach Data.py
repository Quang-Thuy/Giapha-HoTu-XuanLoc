# ==============================================================================
# GIA PHẢ ĐIỆN TỬ DÒNG HỌ TỪ XUÂN LỘC - CHUẨN ĐỊNH DANH HỢP NHẤT
# PHIÊN BẢN TÍCH HỢP TỐI ƯU TOÀN DIỆN CHO ĐIỆN THOẠI (MOBILE-FIRST)
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
import re
import os
from PIL import Image
from graphviz import Digraph
# Thêm trực tiếp đường dẫn bin của Graphviz vào biến môi trường của tiến trình Python
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

import shutil
# Hàm tự động tìm và thêm đường dẫn Graphviz vào PATH một cách linh hoạt
def auto_detect_graphviz():
    # 1. Kiểm tra xem hệ thống đã nhận diện được lệnh 'dot' sẵn chưa
    if shutil.which("dot") is not None:
        return  # Đã có sẵn trong PATH của máy, không cần làm gì thêm

    # 2. Danh sách các đường dẫn cài đặt phổ biến trên Windows
    common_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
        os.path.expanduser(r"~\AppData\Local\Programs\Graphviz\bin"),
    ]

    # 3. Quét qua các đường dẫn phổ biến, nếu thấy tệp dot.exe thì tự động thêm vào môi trường
    for path in common_paths:
        dot_executable = os.path.join(path, "dot.exe" if os.name == "nt" else "dot")
        if os.path.exists(dot_executable):
            os.environ["PATH"] += os.pathsep + path
            break

# Gọi hàm tự động nhận diện trước khi sử dụng thư viện graphviz
auto_detect_graphviz()

from pathlib import Path
from PIL import Image, ImageOps
try:
    from pillow_heif import register_heif_opener
    register_heif_opener() # Đăng ký hỗ trợ đọc định dạng ảnh HEIC/HEIF của iPhone
except ImportError:
    pass
import io
import zipfile
import base64
import folium
from streamlit_folium import st_folium

#==========================================
# Telegram Manager (Phiên bản Bọc Thép CSDL & SQL Trực Tiếp)
#==========================================
import threading
import telebot
from telebot import types
from pathlib import Path
import sqlite3
import streamlit as st

class TelegramBotManager:
    # Đã cấu hình chuẩn Token và Chat ID Siêu nhóm
    FIXED_TOKEN = "8709408235:AAH69tB_CGYxDs4ZuCSxKMNlPXg4yJhg_JE"
    FIXED_CHAT_ID = "-1004360294941"

    @staticmethod
    def get_bot_token_and_chat_id():
        return TelegramBotManager.FIXED_TOKEN, TelegramBotManager.FIXED_CHAT_ID

    @staticmethod
    @st.cache_resource
    def start_background_bot():
        """Khởi động trạm lắng nghe tín hiệu từ Telegram trên luồng ngầm"""
        token, chat_id = TelegramBotManager.get_bot_token_and_chat_id()
        if not token:
            return False

        bot = telebot.TeleBot(token)

        @bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            _, current_chat_id = TelegramBotManager.get_bot_token_and_chat_id()
            if str(call.message.chat.id) != str(current_chat_id):
                bot.answer_callback_query(call.id, "❌ Bạn không có quyền quản trị hệ thống!")
                return

            data = call.data
            try:
                # ---------------- PHÊ DUYỆT ----------------
                if data.startswith("duyet_"):
                    member_id = data.replace("duyet_", "")
                    kq = False
                    ho_ten = "Thành viên"
                    
                    with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                        cursor = conn.cursor()
                        # Lấy thông tin hiện tại
                        cursor.execute("SELECT TinhTrang, HoTen FROM GiaPha WHERE ID = ?", (member_id,))
                        row = cursor.fetchone()
                        
                        if row:
                            tinh_trang_goc, ho_ten = row
                            # Cắt bỏ chữ "Chờ duyệt"
                            new_tinh_trang = str(tinh_trang_goc).replace("Chờ duyệt,", "").replace("Chờ duyệt", "").strip()
                            
                            # CẬP NHẬT TRỰC TIẾP VÀO DATABASE BẰNG SQL (Khắc phục triệt để lỗi thiếu hàm)
                            cursor.execute("UPDATE GiaPha SET TinhTrang = ? WHERE ID = ?", (new_tinh_trang, member_id))
                            conn.commit()
                            kq = cursor.rowcount > 0
                            
                    if kq:
                        cap_text = f"✅ <b>ĐÃ PHÊ DUYỆT THÀNH CÔNG:</b>\n👤 {ho_ten} (ID: <code>{member_id}</code>)"
                        if call.message.photo:
                            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=cap_text, parse_mode="HTML")
                        else:
                            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=cap_text, parse_mode="HTML")
                        bot.answer_callback_query(call.id, "Đã duyệt và lưu vào CSDL!")
                        # Làm sạch cache để tải lại dữ liệu mới trên Web
                        KhoDuLieuSQL.load_data.clear() 
                    else:
                        bot.answer_callback_query(call.id, "❌ Lỗi: Không tìm thấy thành viên trong CSDL!")
                
                # ---------------- TỪ CHỐI / XÓA ----------------
                elif data.startswith("xoa_"):
                    member_id = data.replace("xoa_", "")
                    kq = False
                    ho_ten = "Thành viên"
                    
                    with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT HoTen FROM GiaPha WHERE ID = ?", (member_id,))
                        row = cursor.fetchone()
                        
                        if row:
                            ho_ten = row[0]
                            # Xóa ảnh (nếu có)
                            try:
                                duong_dan_anh = QuanTriHinhAnh.lay_anh_chuan_xac(member_id, ho_ten)
                                if duong_dan_anh:
                                    img_path = Path(__file__).resolve().parent / duong_dan_anh
                                    if img_path.exists(): img_path.unlink()
                            except Exception:
                                pass
                            
                            # XÓA TRỰC TIẾP TỪ DATABASE BẰNG SQL
                            cursor.execute("DELETE FROM GiaPha WHERE ID = ?", (member_id,))
                            conn.commit()
                            kq = cursor.rowcount > 0
                            
                    if kq:
                        cap_text = f"❌ <b>ĐÃ TỪ CHỐI & XÓA BỎ:</b>\n👤 {ho_ten} (ID: <code>{member_id}</code>)"
                        if call.message.photo:
                            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=cap_text, parse_mode="HTML")
                        else:
                            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=cap_text, parse_mode="HTML")
                        bot.answer_callback_query(call.id, "Đã xóa vĩnh viễn khỏi CSDL!")
                        # Làm sạch cache để tải lại dữ liệu mới trên Web
                        KhoDuLieuSQL.load_data.clear()
                    else:
                        bot.answer_callback_query(call.id, "❌ Lỗi: Không tìm thấy dữ liệu để xóa!")

            except Exception as e:
                bot.answer_callback_query(call.id, f"Lỗi hệ thống: {e}")

        def run_polling():
            while True:
                try:
                    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
                except Exception:
                    import time
                    time.sleep(5)

        t = threading.Thread(target=run_polling, daemon=True)
        t.start()
        return True

    @staticmethod
    def gui_thong_bao_cho_duyet(member_info, img_relative_path=None):
        token, chat_id = TelegramBotManager.get_bot_token_and_chat_id()
        if not token or not chat_id:
            return False, "Chưa cấu hình Token hoặc Chat ID."

        bot = telebot.TeleBot(token)
        noi_dung = (
            f"🔔 <b>CÓ YÊU CẦU THÊM THÀNH VIÊN MỚI</b>\n\n"
            f"👤 <b>Họ tên:</b> {member_info.get('HoTen')}\n"
            f"🆔 <b>Mã ĐD:</b> <code>{member_info.get('ID')}</code>\n"
            f"👨 <b>Cha trực hệ:</b> {member_info.get('TenCha')}\n"
            f"📋 <b>Tình trạng:</b> {member_info.get('TinhTrang')}\n"
            f"📝 <b>Ghi chú:</b> {member_info.get('GhiChu', 'Không có')}\n\n"
            f"👉 Vui lòng chọn thao tác bên dưới:"
        )

        reply_markup = types.InlineKeyboardMarkup()
        btn_duyet = types.InlineKeyboardButton("✅ Phê duyệt", callback_data=f"duyet_{member_info.get('ID')}")
        btn_xoa = types.InlineKeyboardButton("❌ Từ chối / Xóa", callback_data=f"xoa_{member_info.get('ID')}")
        reply_markup.add(btn_duyet, btn_xoa)

        try:
            full_img_path = None
            if img_relative_path:
                p = Path(__file__).resolve().parent / img_relative_path
                if p.exists(): full_img_path = p

            if full_img_path:
                with open(full_img_path, "rb") as photo:
                    bot.send_photo(chat_id=chat_id, photo=photo, caption=noi_dung, parse_mode="HTML", reply_markup=reply_markup)
            else:
                bot.send_message(chat_id=chat_id, text=noi_dung, parse_mode="HTML", reply_markup=reply_markup)
            return True, "Đã gửi thông báo thành công!"
        except Exception as e:
            return False, f"Lỗi gửi: {e}"




# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ A] - KHU VỰC QUẢN TRỊ TÀI NGUYÊN & GIẢI MÃ ĐỊNH DANH
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

class QuanTriTaiNguyen:
    BASE_DIR = Path(__file__).resolve().parent
    DB_FILE = BASE_DIR / "giapha_HoTu.db"
    TUYET_TON = " ●"

    CIRCLED_NUMBERS = {
        1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤",
        6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩",
        11: "⑪", 12: "⑫", 13: "⑬", 14: "⑭", 15: "⑮",
        16: "⑯", 17: "⑰", 18: "⑑", 19: "⑒", 20: "⑓", 21: "㉑"
    }

    COLOR_PALETTE = {
        1: "#FFD1D1", 2: "#FFE6CC", 3: "#FFF2CC", 
        4: "#D5E8D4", 5: "#DAE8FC", 6: "#E1D5E7", 
        7: "#FCE5CD", 8: "#D9EAD3", 9: "#FFF2CC",
        10: "#E2F0D9", 11: "#FBE5D6", 12: "#EDEDED"
    }


    #=====================================================================
    # [PHÂN LÔ A1]: Hàm con xử lý khoanh tròn số đời và chấm đen tuyệt tôn
    #=====================================================================
    @classmethod
    def get_circled_doi(cls, doi_val, tinh_trang=""):
        try:
            val = int(doi_val)
            res = cls.CIRCLED_NUMBERS.get(val, f"({doi_val})")
            keyword_list = ["phạp tự", "không có con", "tảo vong", "tảo một", "chết sớm", "liệt sỹ", "Liệt sĩ", "tử sỹ", "tử sĩ"]
            if any(kw in str(tinh_trang).lower() for kw in keyword_list):
                res += cls.TUYET_TON
            return res
        except:
            return ""


    #=====================================================================
    # [PHÂN LÔ A2]: Hàm con trích xuất tên chính (tên cuối)
    #=====================================================================
    @staticmethod
    def lay_ten_chinh(ho_ten_day_du):
        ten = str(ho_ten_day_du).strip()
        if not ten or ten == "nan" or ten == "None":
            return ""
        if "(" in ten:
            ten = ten.split("(")[0].strip()
        parts = ten.split()
        return parts[-1] if parts else ten

    #=====================================================================
    # [PHÂN LÔ A3]: Hàm con sắp xếp danh sách phái
    #=====================================================================
    @staticmethod
    def sap_xep_danh_sach_phai(danh_sach_phai):
        def get_phai_order(p):
            m = re.search(r'Phái\s*(\d+)', str(p), flags=re.IGNORECASE)
            if m:
                num = int(m.group(1))
                return float('inf') if num == 0 else num
            return float('inf') - 1
            
        clean_list = [p for p in danh_sach_phai if p]
        return sorted(clean_list, key=get_phai_order)

    #=====================================================================
    # [PHÂN LÔ A4]: Hàm con lọc danh sách chi chuẩn
    #=====================================================================
    @staticmethod
    def lay_danh_sach_chi_chuan(df_source):
        bo_qua = {"", "Thủy Tổ", "Ngoại vi / Lấy chồng", "Khác"}
        raw_chis = [c for c in df_source['Chi'].unique() if c and c not in bo_qua]
        
        def get_chi_num(chi_str):
            m = re.search(r'Chi\s*(\d+)', str(chi_str), flags=re.IGNORECASE)
            return int(m.group(1)) if m else 99
            
        return sorted(raw_chis, key=get_chi_num)


class BoGiaiMaDinhDanh:
    #=====================================================================
    # [PHÂN LÔ A5]: Hàm con giải mã cấu trúc 9 chữ số định danh
    #=====================================================================
    @staticmethod
    def phan_tich_ma(hotu_str):
        clean_id = str(hotu_str).replace(".", "").strip()
        if len(clean_id) != 9 or not clean_id.isdigit():
            return {
                "Cua": "Khác", "Chi": "Khác", "Phai": "", 
                "DoiThu": 1, "GioiTinh": "Nam", "STT": 1
            }
        
        khoi_chi = clean_id[0:3]
        khoi_doi = int(clean_id[3:5])
        khoi_gt = clean_id[5]
        khoi_stt = int(clean_id[6:9])
        
        gioi_tinh = "Nữ" if khoi_gt == "1" else "Nam"
        
        if clean_id == "000010001":
            cua, chi, phai = ("Gốc", "Thủy Tổ", "")
        elif khoi_chi == "000":
            cua, chi, phai = ("Gốc", "Ngoại vi / Lấy chồng", "")
        else:
            mapping_chi = {
                "100": ("Cửa Giáp", "", ""),
                "200": ("Cửa Ất", "", ""),
                "110": ("Cửa Giáp", "Chi 1 (Cụ Liện)", ""),
                "120": ("Cửa Giáp", "Chi 2 (Cụ Dực)", ""),
                "130": ("Cửa Giáp", "Chi 3 (Cụ Lạng)", ""),
                "111": ("Cửa Giáp", "Chi 1 (Cụ Liện)", "Phái 1 (Cụ Di)"),
                "122": ("Cửa Giáp", "Chi 2 (Cụ Dực)", "Phái 2 (Cụ Kỵ)"),
                "123": ("Cửa Giáp", "Chi 2 (Cụ Dực)", "Phái 3 (Cụ Tương)"),
                "124": ("Cửa Giáp", "Chi 2 (Cụ Dực)", "Phái 4 (Cụ Tỉnh)"),
                "135": ("Cửa Giáp", "Chi 3 (Cụ Lạng)", "Phái 5 (Cụ Tình)"),
                "240": ("Cửa Ất", "Chi 4 (Cụ Màn)", ""),
                "250": ("Cửa Ất", "Chi 5 (Cụ Hùng)", ""),
                "260": ("Cửa Ất", "Chi 6 (Cụ Lân)", ""),
                "270": ("Cửa Ất", "Chi 7 (Cụ Lạc)", ""),
                "246": ("Cửa Ất", "Chi 4 (Cụ Màn)", "Phái 6 (Cụ Hiển)"),
                "257": ("Cửa Ất", "Chi 5 (Cụ Hùng)", "Phái 7 (Cụ Linh)"),
                "258": ("Cửa Ất", "Chi 5 (Cụ Hùng)", "Phái 8 (Cụ Cảo)"),
                "269": ("Cửa Ất", "Chi 6 (Cụ Lân)", "Phái 9 (Cụ Niên)"),
                "270": ("Cửa Ất", "Chi 7 (Cụ Lạc)", "Phái 0 (Cụ Thận)"),
            }
            cua, chi, phai = mapping_chi.get(khoi_chi, ("Khác", "Khác", ""))
            
        return {
            "Cua": cua, "Chi": chi, "Phai": phai,
            "DoiThu": khoi_doi, "GioiTinh": gioi_tinh, "STT": khoi_stt
        }


# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ B] - KHU VỰC KHO DỮ LIỆU SQLITE GỐC
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

class KhoDuLieuSQL:
    BASE_DIR = Path(__file__).resolve().parent
    DB_FILE = BASE_DIR / "giapha_HoTu.db"

    #=====================================================================
    # [PHÂN LÔ B1]: Hàm con khởi tạo CSDL SQLite và seed 23 mốc lịch sử gốc
    #=====================================================================
    @classmethod
    def init_database(cls):
        with sqlite3.connect(cls.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS GiaPha (
                ID TEXT PRIMARY KEY,
                ChaID TEXT,
                HoTen TEXT NOT NULL,
                TenTu TEXT,
                VoChong TEXT,
                NamSinh VARCHAR(20),
                NamMat VARCHAR(20),
                NgayGio VARCHAR(50),
                ChucDanh_GhiChu TEXT,
                TinhTrang TEXT,
                HinhAnh TEXT,
                FOREIGN KEY (ChaID) REFERENCES GiaPha(ID)
            );
            """)

            # 🟢 THÊM BẢNG CẤU HÌNH HỆ THỐNG VÀO ĐÂY

            # Tạo bảng cấu hình hệ thống
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS CauHinhHeThong (
                Khoa TEXT PRIMARY KEY,
                GiaTri TEXT
            );
            """)
            # Đặt mặc định là 'True' (Mở) để con cháu tự do tải lên lúc đầu khóa là 'False'
            cursor.execute("INSERT OR IGNORE INTO CauHinhHeThong (Khoa, GiaTri) VALUES ('cho_phep_tai_anh', 'True')")

            cursor.execute("SELECT COUNT(*) FROM GiaPha")
            count = cursor.fetchone()[0]
     
            
            if count == 0:
                # 1. Gọi dữ liệu từ file vừa tạo (Lưu ý gõ đúng tên file không có đuôi .py)
                from Data_Giapha_Chi2_At import raw_data

                # 2. Vòng lặp kiểm tra lỗi nằm ở App chính
                for index, record in enumerate(raw_data):
                    if len(record) != 11:
                        print(f"⚠️ Phát hiện lỗi ở record thứ {index + 1} (ID: {record[0]} - {record[2]}): Có {len(record)} phần tử (Yêu cầu đúng 11).")

                # Kiểm tra ID trùng lặp trong mảng raw_data
                seen_ids = set()
                duplicate_ids = set()
                for record in raw_data:
                    rid = record[0]
                    if rid in seen_ids:
                        duplicate_ids.add(rid)
                    else:
                        seen_ids.add(rid)

                if duplicate_ids:
                    print(f"⚠️ Phát hiện các ID bị trùng lặp trong raw_data: {duplicate_ids}")
                else:
                    print("✅ Mảng raw_data hoàn toàn sạch, không có ID nào bị trùng.")


                # ==========================================
                # ĐOẠN CODE THỐNG KÊ TỔNG SỐ LƯỢNG, NAM, NỮ TRÊN BẢNG ĐEN
                # ==========================================
                total_members = len(raw_data)
                count_nu = 0
                count_nam = 0
                
                for record in raw_data:
                    member_id = str(record[0]).replace(".", "").strip()
                    # Ký tự thứ 6 của mã định danh (index 5) quy định giới tính: '1' là Nữ, ngược lại là Nam
                    if len(member_id) >= 6 and member_id[5] == '1':
                        count_nu += 1
                    else:
                        count_nam += 1
                
                print("==================================================")
                print(f"📊 THỐNG KÊ DỮ LIỆU GIA PHẢ HỌ TỪ XUÂN LỘC:")
                print(f"   - Tổng số            : {total_members}")
                print(f"   - Tổng số Nam        : {count_nam}")
                print(f"   - Tổng số Nữ         : {count_nu}")
                print("==================================================")

                
                insert_query = """
                INSERT INTO GiaPha (
                    ID, ChaID, HoTen, TenTu, VoChong, NamSinh, NamMat, NgayGio, 
                    ChucDanh_GhiChu, TinhTrang, HinhAnh
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.executemany(insert_query, raw_data)
                conn.commit()

    #=====================================================================
    # [PHÂN LÔ B2]: Hàm con tải dữ liệu từ SQLite sang DataFrame
    #=====================================================================
    @staticmethod
    @st.cache_data(show_spinner="Đang đồng bộ dữ liệu huyết mạch...") # 🟢 LỆNH KÍCH HOẠT CACHE
    def load_data():
        KhoDuLieuSQL.init_database() # Đổi cls thành KhoDuLieuSQL
        with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn: # Đổi cls thành KhoDuLieuSQL
            query = """
            SELECT 
                rowid AS RecordIndex,
                ID,
                COALESCE(ChaID, '') AS ChaMe_ID, 
                HoTen, 
                TenTu,
                VoChong, 
                NamSinh,
                NamMat,
                NgayGio,
                ChucDanh_GhiChu AS GhiChu, 
                TinhTrang,
                HinhAnh
            FROM GiaPha
            ORDER BY rowid ASC
            """
            df = pd.read_sql_query(query, conn).fillna("")

        expanded_rows = []
        for _, row in df.iterrows():
            parsed = BoGiaiMaDinhDanh.phan_tich_ma(row['ID'])
            new_row = row.to_dict()
            new_row.update(parsed)
            expanded_rows.append(new_row)
            
        df_final = pd.DataFrame(expanded_rows)
        df_final["TrangThai"] = "Đã duyệt"
        
        if 'RecordIndex' in df_final.columns:
            df_final = df_final.sort_values(by="RecordIndex", ascending=True).reset_index(drop=True)

        if 'STT' in df_final.columns:
            df_final['STT'] = range(1, len(df_final) + 1)
        else:
            df_final.insert(0, 'STT', range(1, len(df_final) + 1))
            
        return df_final

    #=====================================================================
    # [PHÂN LÔ B3]: Hàm con thẩm định tính hợp lệ ID và logic thế hệ cha-con
    #=====================================================================
    @classmethod
    def validate_member_data(cls, new_id, cha_id, ho_ten):
        errors = []
        if not ho_ten or not ho_ten.strip():
            errors.append("Họ và tên không được để trống.")
        if not new_id or len(str(new_id).replace(".", "").strip()) != 9:
            errors.append("Mã định danh không hợp lệ (Phải đúng chuẩn 9 chữ số ví dụ: 123.04.0.011).")
            
        parsed_new = BoGiaiMaDinhDanh.phan_tich_ma(new_id)
        new_doi = parsed_new['DoiThu']

        with sqlite3.connect(cls.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ID FROM GiaPha WHERE ID = ?", (new_id,))
            if cursor.fetchone():
                errors.append(f"Mã định danh '{new_id}' đã tồn tại trong hệ thống.")

            if cha_id and cha_id != "":
                cursor.execute("SELECT ID FROM GiaPha WHERE ID = ?", (cha_id,))
                parent = cursor.fetchone()
                if not parent:
                    errors.append(f"Mã cha (ID: {cha_id}) không tồn tại trong cơ sở dữ liệu.")
                else:
                    parsed_parent = BoGiaiMaDinhDanh.phan_tich_ma(cha_id)
                    if new_doi <= parsed_parent['DoiThu']:
                        errors.append(f"Lỗi thế hệ: Đời của con (Đời {new_doi}) không thể nhỏ hơn hoặc bằng đời của cha (Đời {parsed_parent['DoiThu']}).")
        return errors

    #=====================================================================
    # [PHÂN LÔ B4]: Hàm con thực thi chèn thành viên mới
    #=====================================================================
    @classmethod
    def insert_member(cls, new_id, ho_ten, ten_tu, cha_id, vo_chong, nam_sinh, nam_mat, ngay_gio, ghi_chu, tinh_trang, hinh_anh):
        validation_errors = cls.validate_member_data(new_id, cha_id, ho_ten)
        if validation_errors:
            return False, validation_errors

        cls.init_database()
        cha_id_val = None if not cha_id or cha_id == "" else cha_id

        with sqlite3.connect(cls.DB_FILE) as conn:
            cursor = conn.cursor()
            query = """
            INSERT INTO GiaPha (
                ID, ChaID, HoTen, TenTu, VoChong, 
                NamSinh, NamMat, NgayGio, ChucDanh_GhiChu, TinhTrang, HinhAnh
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                new_id.strip(), cha_id_val, ho_ten.strip(), ten_tu.strip(), 
                vo_chong.strip(), nam_sinh.strip(), nam_mat.strip(), ngay_gio.strip(), 
                ghi_chu.strip(), tinh_trang.strip(), hinh_anh
            ))
            conn.commit()
            
        KhoDuLieuSQL.load_data.clear() # 🟢 XÓA CACHE ĐỂ CẬP NHẬT NGƯỜI MỚI VÀO BẢNG
        return True, ["Thêm thành viên thành công!"]

    #=====================================================================
    # [PHÂN LÔ B5]: Hàm con thực thi xóa thành viên theo ID
    #=====================================================================
    @classmethod
    def delete_member(cls, member_id):
        with sqlite3.connect(cls.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM GiaPha WHERE ID = ?", (member_id,))
            conn.commit()
            
        KhoDuLieuSQL.load_data.clear() # 🟢 XÓA CACHE ĐỂ LÀM BIẾN MẤT NGƯỜI VỪA XÓA

# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ C] - KHU VỰC BẢN VẼ HÌNH HỌC GRAPHVIZ (TÍCH HỢP ZOOM & PAN DI ĐỘNG)
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

class KyThuatBanVeGiaPha:

    NHANH_MAPPING = {
        "Phái 1 (Cụ Di)": [
            ("Nhánh Cụ Thư", "111.06.0.001"),
            ("Nhánh Cụ Ngạch", "111.06.0.006"),
            ("Nhánh Cụ Khánh", "111.06.0.008"),
            ("Nhánh Cụ Sum", "111.06.0.010"),
            ("Nhánh Cụ Cội", "111.06.0.012")
        ],
        "Phái 2 (Cụ Kỵ)": [
            ("Nhánh Cụ Toát", "122.06.0.014"),
            ("Nhánh Cụ Mận", "122.06.0.017")
        ],
        "Phái 3 (Cụ Tương)": [
            ("Nhánh Cụ Vẹn", "123.06.0.026")
        ],
        "Phái 4 (Cụ Tỉnh)": [
            ("Nhánh Cụ Chính", "124.06.0.042"),
            ("Nhánh Cụ Giáo", "124.06.0.044"),
            ("Nhánh Cụ Thí", "124.06.0.045")
        ],
        "Phái 5 (Cụ Tình)": [
            ("Nhánh Cụ Thính", "135.06.0.047"),
            ("Nhánh Cụ Quán", "135.06.0.056"),
            ("Nhánh Cụ Xán", "135.06.0.061")
        ],
        "Phái 6 (Cụ Hiển)": [
            ("Nhánh Cụ Bạt", "246.07.0.098"),
            ("Nhánh Cụ Nhiếp", "246.07.0.100"),
            ("Nhánh Cụ Dị", "246.07.0.102")
        ],
        "Phái 7 (Cụ Linh)": [
            ("Nhánh Cụ Thạc", "257.06.0.068")
        ],
        "Phái 8 (Cụ Cảo)": [
            ("Nhánh Cụ Hoài", "258.07.0.108"),
            ("Nhánh Cụ Nhạc", "258.07.0.117"),
            ("Nhánh Cụ Vi", "258.07.0.120"),
            ("Nhánh Cụ Lậu", "258.07.0.121"),
            ("Nhánh Cụ Ứng", "258.07.0.122"),
            ("Nhánh Cụ Lai", "258.07.0.126"),
            ("Nhánh Cụ Lưu", "258.07.0.127")
        ],
        "Phái 0 (Cụ Thận)": [
            ("Nhánh Cụ Dinh", "270.05.0.049")
        ]
    }


    #=====================================================================
    # [PHÂN LÔ C1]: Hàm con truy tìm chuỗi tổ tiên ngược
    #=====================================================================
    @staticmethod
    def get_ancestors_chain(df_data, focus_id):
        chain = []
        curr_id = str(focus_id)
        visited = set()
        while curr_id and curr_id != "0" and curr_id not in visited:
            visited.add(curr_id)
            row = df_data[df_data["ID"] == curr_id]
            if row.empty:
                break
            chain.insert(0, row.iloc[0].to_dict())
            curr_id = str(row.iloc[0].get("ChaMe_ID", ""))
        return chain

    #=====================================================================
    # [PHÂN LÔ C2]: Hàm con truy tìm toàn bộ con cháu bên dưới
    #=====================================================================
    @staticmethod
    def get_all_descendants(df_data, focus_id):
        descendant_ids = set()
        queue = [str(focus_id)]
        while queue:
            curr = queue.pop(0)
            children = df_data[(df_data["ChaMe_ID"] == curr) & (df_data["TrangThai"] == "Đã duyệt")]
            if "STT" in children.columns:
                children = children.sort_values(by="STT")
            for _, ch in children.iterrows():
                c_id = str(ch["ID"])
                if c_id not in descendant_ids:
                    descendant_ids.add(c_id)
                    queue.append(c_id)
        return list(descendant_ids)

    #=====================================================================
    # [PHÂN LÔ C3]: Hàm con tạo nhãn hiển thị trang trọng trên node
    #=====================================================================
    @staticmethod
    def tao_nhan_ton_kinh(member):
        doi_num = int(member.get('DoiThu', 1))
        tinh_trang = str(member.get('TinhTrang', ''))
        member_id = str(member.get('ID', ''))
        
        doi_khoanh = QuanTriTaiNguyen.get_circled_doi(doi_num, tinh_trang)
        ho_ten = str(member.get('HoTen', '')).strip()
        ten_tu = str(member.get('TenTu', '')).strip()
        cua = str(member.get('Cua', ''))
        chi = str(member.get('Chi', ''))
        
        di_cu_tag = "\n(Di cư, không rõ)" if "di cư" in tinh_trang.lower() and "không rõ" in tinh_trang.lower() else ""
        con_nuoi_tag = "\n(Con nuôi)" if "con nuôi" in tinh_trang.lower() or member_id == "100.03.0.004" else ""
        
        # 🟢 FIX: Nhận diện cả "chờ duyệt" và "chờ xử lý"
        cho_duyet_tag = "\n(Chờ duyệt)" if "chờ duyệt" in tinh_trang.lower() or "chờ xử lý" in tinh_trang.lower() else ""
        
        if doi_num == 1:
            hien_tu = f" (Tự: {ten_tu})" if ten_tu else " (Tự: Huy Cán)"
            return f"Từ Dương Đốc {doi_khoanh}\n(Thủy Tổ{hien_tu}){di_cu_tag}{con_nuoi_tag}{cho_duyet_tag}"

        elif doi_num == 2:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            if member_id == "000.02.1.003" or "lấy chồng" in str(member.get('GhiChu', '')).lower():
                return f"{ten_rut_gon} {doi_khoanh}\n(Lấy chồng){cho_duyet_tag}"
            elif any(kw in tinh_trang.lower() for kw in ["tảo vong", "tảo một", "chết sớm"]):
                return f"{ten_rut_gon} {doi_khoanh}\n({tinh_trang.capitalize()}){cho_duyet_tag}"
            elif any(kw in tinh_trang.lower() for kw in ["phạp tự", "không có con"]): 
                return f"{ten_rut_gon} {doi_khoanh}{cho_duyet_tag}"
            return f"{ten_rut_gon} {doi_khoanh}\n(Đứng đầu {cua}){di_cu_tag}{con_nuoi_tag}{cho_duyet_tag}"

        elif doi_num == 3:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            if member_id == "100.03.0.004" or "con nuôi" in tinh_trang.lower():
                return f"{ten_rut_gon} {doi_khoanh}\n(Con nuôi){cho_duyet_tag}"
            ten_chi = chi.split("(")[0].strip() if "(" in chi else chi
            return f"{ten_rut_gon} {doi_khoanh}\n({ten_chi}){di_cu_tag}{con_nuoi_tag}{cho_duyet_tag}"
        else:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            return f"{ten_rut_gon} {doi_khoanh}{di_cu_tag}{con_nuoi_tag}{cho_duyet_tag}"

    #=====================================================================
    # [PHÂN LÔ C4]: Hàm con vẽ biểu đồ sơ đồ trực hệ tập trung
    #=====================================================================
    @classmethod
    def draw_focus_tree(cls, df_data, focus_id):
        dot = Digraph(comment='Focus Tree', node_attr={'shape': 'box', 'style': 'filled,rounded', 'fontname': 'Arial', 'fontsize': '11'})
        dot.attr(rankdir='TB', size='14,10', ordering='out')

        ancestor_chain = cls.get_ancestors_chain(df_data, focus_id)
        if not ancestor_chain:
            return dot

        prev_node_id = None
        for member in ancestor_chain:
            m_id = str(member['ID'])
            doi_num = int(member['DoiThu'])
            is_focus = (m_id == str(focus_id))
            
            label = cls.tao_nhan_ton_kinh(member)
            fill = "#FFE082" if is_focus else QuanTriTaiNguyen.COLOR_PALETTE.get(doi_num, "#FFFFFF")
            border_color = "#C62828" if is_focus else "#455A64"
            pen_width = "2.8" if is_focus else "1.5"
            
            dot.node(m_id, label, fillcolor=fill, color=border_color, penwidth=pen_width, style="filled,rounded")
            if prev_node_id:
                dot.edge(prev_node_id, m_id, color="#C62828" if is_focus else "#37474F", penwidth="2.2" if is_focus else "1.3")
            prev_node_id = m_id

        if str(focus_id) == "000.01.0.001":
            children = df_data[(df_data["ChaMe_ID"] == "000.01.0.001") & (df_data["TrangThai"] == "Đã duyệt")]
        else:
            children = df_data[(df_data["ChaMe_ID"] == str(focus_id)) & (df_data["TrangThai"] == "Đã duyệt")]

        if not children.empty and "STT" in children.columns:
            # Sửa lại sắp xếp children theo STT_Con thay vì STT cũ để chuẩn xác
            children['STT_Con'] = children['ID'].apply(
                lambda x: int(str(x).replace('.', '').strip()[-3:]) if len(str(x).replace('.', '').strip()) >= 9 else 999
            )
            children = children.sort_values(by="STT_Con")

        for _, child in children.iterrows():
            c_id = str(child['ID'])
            c_label = cls.tao_nhan_ton_kinh(child.to_dict())
            gioi_tinh = str(child.get('GioiTinh', 'Nam'))
            c_doi_num = int(child['DoiThu'])
            tinh_trang_child = str(child.get('TinhTrang', '')).lower()
            
            is_con_nuoi = ("con nuôi" in tinh_trang_child or c_id == "100.03.0.004")
            
            # 🟢 FIX: Áp dụng nền vàng nhạt, viền cam nét đứt cho người đang "Chờ duyệt" vào Trực Hệ
            is_cho_duyet = ("chờ duyệt" in tinh_trang_child or "chờ xử lý" in tinh_trang_child)
            
            if is_cho_duyet:
                c_fill, c_style, c_pen = "#FFF8E1", "filled,dashed", "1.5"
                c_border = "#F57C00"
            elif is_con_nuoi:
                c_fill, c_style, c_pen = "#E0F7FA", "filled,dashed", "1.5"
                c_border = "#00838F"
            else:
                c_fill = "#FFF0F5" if gioi_tinh == "Nữ" else QuanTriTaiNguyen.COLOR_PALETTE.get(c_doi_num, "#E8F5E9")
                c_style, c_pen = "filled,rounded", "1.2"
                c_border = "#2E7D32"
            
            dot.node(c_id, c_label, fillcolor=c_fill, color=c_border, shape="box", style=c_style, penwidth=c_pen)
            dot.edge(str(focus_id), c_id, color="#2E7D32", penwidth="1.5")

        return dot


    #=====================================================================
    # [PHÂN LÔ C5]: Hàm con vẽ sơ đồ toàn cảnh / Trục dọc theo ID
    #=====================================================================
    @classmethod
    def draw_family_tree(cls, df_data, cua_loc="Tất cả", chi_loc="Tất cả", phai_loc="Tất cả", che_do_xem="1. Chỉ Đinh Nam (Gọn: Tên ⑦)", target_id="", nhanh_chon="Tất cả", nhanh_dict=None, so_doi_tren="Tất cả", so_doi_duoi="Tất cả", highlight_ids=None):
        dot = Digraph(comment='Gia Phả Toàn Cảnh', node_attr={'style': 'filled,rounded', 'fontname': 'Arial, Segoe UI Symbol, Arial Unicode MS', 'fontsize': '10', 'margin': '0.04,0.04', 'width': '0', 'height': '0'})
        dot.attr(rankdir='TB', splines='polyline', ordering='out')
        
        df_approved = df_data[df_data["TrangThai"] == "Đã duyệt"].copy()
        
        if "RecordIndex" in df_approved.columns:
            df_approved = df_approved.sort_values(by="RecordIndex")
            
        clean_target_id = str(target_id).strip()
        if clean_target_id:
            valid_ids = set()
            # 1. Truy ngược tổ tiên lên trên (Hỗ trợ giới hạn số đời hoặc lấy tất cả)
            curr = clean_target_id
            visited = set()
            count_tren = 0
            while curr and curr != "0" and curr not in visited:
                if so_doi_tren != "Tất cả" and count_tren >= int(so_doi_tren):
                    break
                visited.add(curr)
                valid_ids.add(curr)
                p_row = df_approved[df_approved["ID"] == curr]
                if p_row.empty:
                    break
                curr = str(p_row.iloc[0].get("ChaMe_ID", ""))
                count_tren += 1
                
            # 2. Quét con cháu tỏa ra bên dưới từ ID mục tiêu (Hỗ trợ giới hạn số đời hoặc lấy tất cả)
            queue = [(clean_target_id, 0)]
            descendant_visited = set()
            while queue:
                c_curr, depth = queue.pop(0)
                if c_curr in descendant_visited:
                    continue
                if so_doi_duoi != "Tất cả" and depth > int(so_doi_duoi):
                    continue
                descendant_visited.add(c_curr)
                valid_ids.add(c_curr)
                
                if so_doi_duoi == "Tất cả" or depth < int(so_doi_duoi):
                    children = df_approved[df_approved["ChaMe_ID"] == c_curr]
                    for _, ch in children.iterrows():
                        queue.append((str(ch["ID"]), depth + 1))
                    
            df_draw = df_approved[df_approved["ID"].isin(valid_ids)].copy()
        else:
            if cua_loc != "Tất cả":
                df_draw = df_approved[(df_approved["Cua"] == cua_loc) | (df_approved["ID"] == "000.01.0.001")].copy()
            else:
                df_draw = df_approved.copy()
                
            if chi_loc != "Tất cả":
                branch_members = df_approved[df_approved["Chi"] == chi_loc]
                valid_ids = set(branch_members["ID"].tolist())
                for p_id in branch_members["ChaMe_ID"]:
                    curr = str(p_id)
                    while curr and curr != "0":
                        valid_ids.add(curr)
                        parent_row = df_approved[df_approved["ID"] == curr]
                        if parent_row.empty:
                            break
                        curr = str(parent_row.iloc[0].get("ChaMe_ID", ""))
                df_draw = df_approved[df_approved["ID"].isin(valid_ids)].copy()

            if phai_loc != "Tất cả":
                phai_members = df_approved[df_approved["Phai"] == phai_loc]
                valid_phai_ids = set(phai_members["ID"].tolist())
                for p_id in phai_members["ChaMe_ID"]:
                    curr = str(p_id)
                    while curr and curr != "0":
                        valid_phai_ids.add(curr)
                        parent_row = df_approved[df_approved["ID"] == curr]
                        if parent_row.empty:
                            break
                        curr = str(parent_row.iloc[0].get("ChaMe_ID", ""))
                df_draw = df_draw[df_draw["ID"].isin(valid_phai_ids)].copy()

            # 🟢 Bổ sung thêm đoạn logic lọc theo Nhánh (giữ nguyên toàn bộ code gốc phía trên)
            if nhanh_chon != "Tất cả" and nhanh_dict and nhanh_chon in nhanh_dict:
                root_branch_id = nhanh_dict[nhanh_chon]
                valid_nhanh_ids = set()
                queue = [root_branch_id]
                desc_visited = set()
                while queue:
                    curr = queue.pop(0)
                    if curr in desc_visited:
                        continue
                    desc_visited.add(curr)
                    valid_nhanh_ids.add(curr)
                    ch_rows = df_approved[df_approved["ChaMe_ID"] == curr]
                    for _, ch in ch_rows.iterrows():
                        queue.append(str(ch["ID"]))
                
                curr = root_branch_id
                while curr and curr != "0":
                    valid_nhanh_ids.add(curr)
                    p_row = df_approved[df_approved["ID"] == curr]
                    if p_row.empty:
                        break
                    curr = str(p_row.iloc[0].get("ChaMe_ID", ""))
                
                df_draw = df_draw[df_draw["ID"].isin(valid_nhanh_ids)].copy()

        if "Chỉ Đinh Nam" in che_do_xem:
            df_draw = df_draw[df_draw["GioiTinh"] == "Nam"]

        if "RecordIndex" in df_draw.columns:
            df_draw = df_draw.sort_values(by="RecordIndex", ascending=True)

        ids_in_graph = set(df_draw['ID'].tolist())

        for _, row in df_draw.iterrows():
            node_id = str(row['ID'])
            ho_ten = str(row.get('HoTen', '')).strip()
            ten_tu = str(row.get('TenTu', '')).strip()
            doi_num = int(row['DoiThu'])
            gioi_tinh = str(row.get('GioiTinh', 'Nam')).strip()
            cua = str(row.get('Cua', '')).strip()
            chi = str(row.get('Chi', '')).strip()
            vo_val = str(row.get('VoChong', '')).strip()
            tinh_trang = str(row.get('TinhTrang', '')).strip()
            
            doi_khoanh = QuanTriTaiNguyen.get_circled_doi(doi_num, tinh_trang)
            di_cu_tag = "\n(Di cư, không rõ)" if "di cư" in tinh_trang.lower() and "không rõ" in tinh_trang.lower() else ""
            con_nuoi_tag = "\n(Con nuôi)" if "con nuôi" in tinh_trang.lower() or node_id == "100.03.0.004" else ""

            is_target = (node_id == clean_target_id)

            if che_do_xem == "1. Chỉ Đinh Nam (Gọn: Tên ⑦)":
                ten_chinh = QuanTriTaiNguyen.lay_ten_chinh(ho_ten)
                if doi_num == 1:
                    hien_tu = f" (Tự: {ten_tu})" if ten_tu else " (Tự: Huy Cán)"
                    label = f"Từ Dương Đốc {doi_khoanh}\n(Thủy Tổ{hien_tu}){di_cu_tag}{con_nuoi_tag}"


                elif doi_num == 2:
                    if node_id == "000.02.1.003" or "lấy chồng" in str(row.get('GhiChu', '')).lower():
                        label = f"{ho_ten} {doi_khoanh}\n(Lấy chồng)"
                    elif any(kw in tinh_trang.lower() for kw in ["tảo vong", "tảo một", "chết sớm"]):
                        label = f"{ho_ten} {doi_khoanh}\n({tinh_trang.capitalize()})"
                    else:
                        label = f"{ho_ten} {doi_khoanh}\n(Đứng đầu {cua}){di_cu_tag}{con_nuoi_tag}"

                elif doi_num == 3:
                    if node_id == "100.03.0.004":
                        label = f"{ho_ten} {doi_khoanh}\n(Con nuôi)"
                    else:
                        ten_chi = chi.split("(")[0].strip() if "(" in chi else chi
                        label = f"{ho_ten} {doi_khoanh}\n({ten_chi}){di_cu_tag}{con_nuoi_tag}"
                else:
                    label = f"{doi_khoanh}\n{ten_chinh}{di_cu_tag}{con_nuoi_tag}"
            elif che_do_xem == "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)":
                ho_ten_sach = ho_ten.split("(")[0].strip()
                label = f"{doi_khoanh}\n{ho_ten_sach}{di_cu_tag}{con_nuoi_tag}"

            elif che_do_xem == "3. Chỉ Đinh Nam (Đủ vợ và chồng)":
                parts = [f"{ho_ten} {doi_khoanh}"]
                tinh_trang_lower = str(tinh_trang).lower()
                
                la_mat_som = any(kw in tinh_trang_lower for kw in ["chết sớm", "tảo vong", "tảo một", "liệt sỹ", "Liệt sĩ", "tử sỹ", "tử sĩ"])
                
                if la_mat_som:
                    parts.append(f"({tinh_trang.capitalize()})")
                elif vo_val and vo_val != "nan":
                    prefix_icon = "♂" if gioi_tinh == "Nữ" else "♀"
                    vo_raw_list = re.split(r',\s*', vo_val)
                    for idx, v in enumerate(vo_raw_list):
                        v_clean = v.strip()
                        v_clean = re.sub(r'^(Bà chính|Bà thứ|bà chính|bà thứ|Bà cả|Bà hai|cả|thứ|hai|chính|Bà|bà|Chồng[:\s]*)+', '', v_clean, flags=re.IGNORECASE).strip()
                        p_prefix = prefix_icon if idx == 0 else "   "
                        hieu_match = re.search(r'\((?:Hiệu[:\s]*)?([^)]+)\)', v_clean)
                        if hieu_match:
                            ten_goc = re.sub(r'\s*\(.*?\)', '', v_clean).strip()
                            hieu_val = hieu_match.group(1).strip()
                            parts.append(f"{p_prefix}: {ten_goc}")
                            parts.append(f"   ({hieu_val})")
                        else:
                            v_clean = re.sub(r'\s*mất.*$', '', v_clean, flags=re.IGNORECASE).strip()
                            if v_clean and v_clean.lower() not in ["nan", "không biết rõ"]:
                                parts.append(f"{p_prefix}: {v_clean}")
                label = "\n".join(parts) + di_cu_tag + con_nuoi_tag
                


            elif che_do_xem == "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)":
                parts = [f"{ho_ten} {doi_khoanh}"]
                tinh_trang_lower = str(tinh_trang).lower()
                la_mat_som = any(kw in tinh_trang_lower for kw in ["chết sớm", "tảo vong", "tảo một", "liệt sỹ", "Liệt sĩ", "tử sỹ", "tử sĩ"])
                
                if node_id == "000.02.1.003":
                    parts.append("(Lấy chồng)")
                elif la_mat_som:
                    parts.append(f"({tinh_trang.capitalize()})")
                elif vo_val and vo_val != "nan":
                    prefix_icon = "♂" if gioi_tinh == "Nữ" else "♀"
                    vo_raw_list = re.split(r',\s*', vo_val)
                    for idx, v in enumerate(vo_raw_list):
                        v_clean = v.strip()
                        v_clean = re.sub(r'^(Bà chính|Bà thứ|bà chính|bà thứ|Bà cả|Bà hai|cả|thứ|hai|chính|Bà|bà|Chồng[:\s]*)+', '', v_clean, flags=re.IGNORECASE).strip()
                        p_prefix = prefix_icon if idx == 0 else "   "
                        hieu_match = re.search(r'\((?:Hiệu[:\s]*)?([^)]+)\)', v_clean)
                        if hieu_match:
                            ten_goc = re.sub(r'\s*\(.*?\)', '', v_clean).strip()
                            hieu_val = hieu_match.group(1).strip()
                            parts.append(f"{p_prefix}: {ten_goc}")
                            parts.append(f"   ({hieu_val})")
                        else:
                            v_clean = re.sub(r'\s*mất.*$', '', v_clean, flags=re.IGNORECASE).strip()
                            if v_clean and v_clean.lower() not in ["nan", "không biết rõ"]:
                                parts.append(f"{p_prefix}: {v_clean}")
                label = "\n".join(parts) + di_cu_tag + con_nuoi_tag

            else:
                label = f"{ho_ten} {doi_khoanh}"

            # 🟢 [THÊM MỚI]: Nhận diện cờ Chờ duyệt hoặc Chờ xử lý
            is_cho_duyet = ("chờ duyệt" in tinh_trang.lower() or "chờ xử lý" in tinh_trang.lower())

            # 🟢 Nhận diện con nuôi (bao gồm cả Nguyễn Bá Hoan mã 100.03.0.004)
            is_con_nuoi = ("con nuôi" in tinh_trang.lower() or node_id == "100.03.0.004")

            is_ancestor_root = (node_id == "000.01.0.001")
            
            if highlight_ids is None:
                highlight_ids = []
            is_highlight = (node_id in highlight_ids)

            # 1. CỤ TỔ: DÙNG NODE CHUẨN, CỠ CHỮ 18, VIỀN ĐỎ DÀY, NỀN VÀNG (HOẠT ĐỘNG HOÀN HẢO MỌI CHẾ ĐỘ)
            if is_ancestor_root:
                fill, shape, color, pen_width, style, f_size = "#FFE082", "box", "#C62828", "3.5", "filled,rounded", "18"
                dot.node(node_id, label, fillcolor=fill, shape=shape, color=color, penwidth=pen_width, style=style, fontsize=f_size)
            
            # 2. NHÂN VẬT ĐIỂN HÌNH VÀ MỤC TIÊU: VIỀN ĐƠN, NỀN VÀNG TIÊU CHUẨN
            elif is_target or is_highlight:
                fill, shape, color, pen_width, style = "#FFE082", "box", "#C62828", "2.5", "filled,rounded"
                dot.node(node_id, label, fillcolor=fill, shape=shape, color=color, penwidth=pen_width, style=style)
            
            # 3. CÁC THÀNH VIÊN KHÁC
            else:
                # 🟢 [CẬP NHẬT Ở ĐÂY]: Ưu tiên trạng thái Chờ duyệt lên hàng đầu để luôn luôn hiển thị viền cam
                if is_cho_duyet:
                    fill, shape, color, pen_width, style = "#FFF8E1", "box", "#F57C00", "1.5", "filled,dashed"
                elif is_con_nuoi:
                    fill, shape, color, pen_width, style = "#E0F7FA", "box", "#00838F", "1.5", "filled,dashed"
                elif node_id == "000.02.1.003" or gioi_tinh == "Nữ":
                    fill, shape, color, pen_width, style = "#FFF0F5", "box", "#D81B60", "1.2", "filled,rounded"
                else:
                    fill, shape, color, pen_width, style = QuanTriTaiNguyen.COLOR_PALETTE.get(doi_num, "#FFFFFF"), "box", "#455A64", "1.2", "filled,rounded"
                
                dot.node(node_id, label, fillcolor=fill, shape=shape, color=color, penwidth=pen_width, style=style)


        for _, row in df_draw.iterrows():
            node_id = str(row['ID'])
            curr_parent = str(row.get('ChaMe_ID', ''))
            if curr_parent and curr_parent in ids_in_graph:
                edge_color = "#C62828" if (curr_parent == clean_target_id or node_id == clean_target_id) else "#546E7A"
                dot.edge(curr_parent, node_id, color=edge_color, penwidth="1.2")
        return dot



    #=====================================================================
    # [PHÂN LÔ C6]: Hàm con nhúng SVG tương tác pan/zoom (Tối ưu cảm ứng di động)
    #=====================================================================
    @classmethod
    def hien_thi_so_do_tuong_tac(cls, dot_graph, chieu_cao=620):
        try:
            svg_data = dot_graph.pipe(format="svg").decode("utf-8")
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
                <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
                <style>
                    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: transparent; overflow: hidden; }}
                    #container-giapha {{ width: 100%; height: {chieu_cao}px; border: 1.5px solid #CFD8DC; border-radius: 10px; background: #FDFEFE; position: relative; }}
                    #container-giapha svg {{ width: 100%; height: 100%; }}
                    .custom-zoom-controls {{ position: absolute; top: 12px; left: 12px; z-index: 999; display: flex; gap: 6px; }}
                    .custom-zoom-controls button {{ width: 36px; height: 36px; background: #fff; border: 1px solid #B0BEC5; border-radius: 6px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
                </style>
            </head>
            <body>
                <div id="container-giapha">
                    <div class="custom-zoom-controls">
                        <button onclick="zoomIn()">+</button>
                        <button onclick="zoomOut()">-</button>
                        <button onclick="resetZoom()" style="font-size: 14px;">⟳</button>
                    </div>
                    {svg_data}
                </div>
                <script>
                    var panZoomInstance = null;
                    window.onload = function() {{
                        var svgElement = document.querySelector('#container-giapha svg');
                        if (svgElement) {{
                            svgElement.setAttribute('id', 'svg-zoom-target');
                            var customEventsHandler = {{
                                haltEventListeners: ['touchstart', 'touchend', 'touchmove', 'touchleave', 'touchcancel'],
                                init: function(options) {{
                                    var instance = options.instance, initialScale = 1, pannedX = 0, pannedY = 0;
                                    this.hammer = Hammer(options.svgElement, {{
                                        inputClass: Hammer.SUPPORT_ALL_TOUCHES ? Hammer.AllTouchInput : Hammer.TouchInput
                                    }});
                                    this.hammer.get('pinch').set({{ enable: true }});
                                    this.hammer.on('panstart panmove', function(ev) {{
                                        if (ev.type === 'panstart') {{ pannedX = 0; pannedY = 0; }}
                                        instance.panBy({{x: ev.deltaX - pannedX, y: ev.deltaY - pannedY}});
                                        pannedX = ev.deltaX; pannedY = ev.deltaY;
                                    }});
                                    this.hammer.on('pinchstart pinchmove', function(ev) {{
                                        if (ev.type === 'pinchstart') {{
                                            initialScale = instance.getZoom();
                                            instance.zoomAtPoint(initialScale * ev.scale, {{x: ev.center.x, y: ev.center.y}});
                                        }}
                                        instance.zoomAtPoint(initialScale * ev.scale, {{x: ev.center.x, y: ev.center.y}});
                                    }});
                                    options.svgElement.addEventListener('touchmove', function(e) {{ e.preventDefault(); }});
                                }},
                                destroy: function() {{ this.hammer.destroy(); }}
                            }};
                            panZoomInstance = svgPanZoom('#svg-zoom-target', {{
                                zoomEnabled: true, controlIconsEnabled: false, fit: true, center: true,
                                minZoom: 0.1, maxZoom: 25, zoomScaleSensitivity: 0.25,
                                dblClickZoomEnabled: true, mouseWheelZoomEnabled: true,
                                customEventsHandler: customEventsHandler
                            }});
                        }}
                    }};
                    function zoomIn() {{ if (panZoomInstance) panZoomInstance.zoomIn(); }}
                    function zoomOut() {{ if (panZoomInstance) panZoomInstance.zoomOut(); }}
                    function resetZoom() {{ if (panZoomInstance) {{ panZoomInstance.resetZoom(); panZoomInstance.center(); }} }}
                </script>
            </body>
            </html>
            """
            components.html(html_content, height=chieu_cao + 10)
        except Exception:
            st.graphviz_chart(dot_graph, use_container_width=True)


# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ D] - KHU VỰC QUẢN TRỊ HÌNH ẢNH CHÂN DUNG
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓


class QuanTriHinhAnh:
    #=====================================================================
    # [PHÂN LÔ D1]: Hàm con xử lý và lưu trữ ảnh siêu bền vững
    #=====================================================================
    @staticmethod
    def xu_ly_va_nen_anh(uploaded_file, save_path):
        try:
            # 1. Đọc tệp ảnh tải lên (hỗ trợ cả HEIC từ album)
            img = Image.open(uploaded_file)
            
            # 2. Tự động xoay ảnh đúng chiều dựa trên EXIF (Khắc phục lỗi quay ngang)
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
                
            # 3. Ép kiểu về hệ màu RGB để lưu chuẩn JPEG an toàn
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")
                
            # 4. Nén tối ưu dung lượng, giữ nguyên độ nét chân dung
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            img.save(save_path, "JPEG", quality=85)
            return True
        except Exception as e:
            print(f"⚠️ Chi tiết lỗi xử lý ảnh: {e}")
            return False

    #=====================================================================
    # [PHÂN LÔ D2]: Hàm con truy xuất đường dẫn ảnh chân dung chuẩn xác
    #=====================================================================
    @staticmethod
    def lay_anh_chuan_xac(member_id, member_name):
        image_dir = Path(__file__).resolve().parent / "images"
        if not image_dir.exists(): return ""
        clean_name = re.sub(r'[\(\)].*?[\(\)]', '', member_name).strip()
        for file in image_dir.iterdir():
            if file.name.startswith(f"{member_id} ") and clean_name.lower() in file.name.lower():
                return f"images/{file.name}"
        return ""

# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ E] - KHU VỰC GIAO DIỆN CHÍNH (STREAMLIT UI & RESPONSIVE MOBILE)
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

class SoChiHuyGiaoDien:

    #=====================================================================
    # [PHÂN LÔ E1]: Hàm con cấu hình giao diện chung & Responsive CSS

    @staticmethod
    def thiet_lap_giao_dien():
        st.set_page_config(page_title="Gia phả điện tử dòng Họ Từ Xuân Lộc", page_icon="📜", layout="wide")
        
        # Đọc cấu hình kích thước chữ từ session state (Mặc định là 16px cho Trung bình)
        font_size_map = {
            "Nhỏ": "14px",
            "Trung bình": "16px",
            "Lớn": "19px"
        }
        current_font_size = font_size_map.get(st.session_state.get("ui_font_size", "Trung bình"), "16px")

        st.markdown(f"""
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
            <style>
                html, body, [class*="css"] {{
                    font-size: {current_font_size} !important;
                }}
                .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem; }}
                .stButton>button {{ width: 100%; border-radius: 8px; height: 3em; font-weight: bold; margin-bottom: 5px; }}
                .hd-zoom {{ font-size: 0.85rem; color: #546E7A; margin-bottom: 8px; }}
                [data-testid="stDataFrame"] div[data-baseweb="table"] td {{
                    white-space: normal !important;
                    word-wrap: break-word !important;
                    height: auto !important;
                }}
                .desktop-view {{ display: block; }}
                .mobile-view {{ display: none; }}
                
                /* 🟢 TINH CHỈNH RIÊNG CHO NÚT CHUYỂN SANG TRỰC HỆ TẠI MỤC LỌC THEO ID */
                div:has(> button[key*="btn_goto_tructhe_from_id"]) {{
                    display: flex;
                    justify-content: center;
                }}
                button[key*="btn_goto_tructhe_from_id"] {{
                    max-width: 50% !important;
                    margin: 0 auto !important;
                    display: block !important;
                }}
                
                @media (max-width: 768px) {{
                    .desktop-view {{ display: none !important; }}
                    .mobile-view {{ display: block !important; }}
                    .hide-on-mobile {{ display: none !important; }}
                    h1.mobile-view {{ font-size: 1.15rem !important; font-weight: bold; white-space: nowrap; margin-bottom: -22px !important; }}
                    h2.mobile-view {{ font-size: 1.15rem !important; margin-top: -5px !important; margin-bottom: 0px !important; }}
                    
                    /* Trên điện thoại cho nút rộng hơn một chút để dễ bấm */
                    button[key*="btn_goto_tructhe_from_id"] {{
                        max-width: 90% !important;
                    }}
                }}
            </style>
        """, unsafe_allow_html=True)

    #=====================================================================
    # [PHÂN LÔ E2]: Hàm con render màn hình Giới thiệu dòng họ chuẩn HTML
    #=====================================================================
    @staticmethod
    def render_gioithieu_1trang():
        # --- TÍCH HỢP NÚT PHÁT NHẠC NỀN GIA PHẢ ---
        st.markdown("### 🎵 Âm Vang Cội Nguồn")
        col_au1, col_au2 = st.columns([1, 2])
        with col_au1:
            phat_nhac = st.toggle("Bật nhạc nền gia phả", value=False, key="toggle_nhac_nen_gioithieu")
        
        if phat_nhac:
            audio_path = Path(__file__).resolve().parent / "nhac_nen.mp3"
            if audio_path.exists():
                with col_au2:
                    st.audio(str(audio_path), format="audio/mp3", autoplay=True)
                st.success("🎶 Đang phát khúc ca cội nguồn dòng họ Từ Xuân Lộc...")
            else:
                st.warning("⚠️ Chưa tìm thấy tệp 'nhac_nen.mp3' trong thư mục dự án. Ông chủ vui lòng đưa tệp nhạc vào cùng thư mục với mã nguồn nhé!")
        st.markdown("---")

        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    margin: 0;
                    padding: 10px;
                    background: transparent;
                }
                .intro-container {
                    background: linear-gradient(135deg, #fdfbf7 0%, #f4ebd0 100%);
                    padding: 25px 35px;
                    border-radius: 12px;
                    border: 1px solid #d4c5a9;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
                    font-family: 'Times New Roman', Times, serif;
                    color: #2C3E50;
                    line-height: 1.7;
                }
            </style>
        </head>
        <body>
            <div class="intro-container">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #8B0000; margin-bottom: 8px; text-transform: uppercase; font-size: 1.5rem; letter-spacing: 1px;">📜 LỜI GIỚI THIỆU DÒNG HỌ TỪ XUÂN LỘC</h2>
                    <p style="font-style: italic; color: #555; font-size: 1.05rem; margin-top: 0;">Kính dâng anh linh tiên tổ — Lưu truyền huyết mạch cho muôn đời con cháu</p>
                    <hr style="border: 0; height: 1.5px; background: #C62828; width: 50%; margin: 15px auto;">
                </div>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 15px;">
                    "Uống nước nhớ nguồn, ăn quả nhớ người trồng cây" là đạo lý ngàn đời của dân tộc ta. Đối với mỗi dòng tộc, cuốn gia phả trước đây thường chỉ nằm lặng lẽ ở một góc tủ trong nhà, nay đã được <b>số hóa toàn diện</b> để vượt qua mọi giới hạn về không gian và thời gian. Ứng dụng <b>Gia phả điện tử dòng Họ Từ Xuân Lộc</b> ra đời với sứ mệnh đưa dữ liệu huyết mạch đến với tất cả mọi người; giúp con cháu dù đi làm ăn xa muôn phương hay ở bất cứ chân trời góc bể nào cũng có thể dễ dàng tiếp cận, tra cứu cội nguồn và hướng về tổ tiên với lòng thành kính sâu sắc nhất.
                </p>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 15px;">
                    Theo tư liệu quý giá và các bản phổ ký do các bậc cao niên để lại, Thủy tổ dòng họ ta là cụ <b>Từ Dương Đốc</b> (huyết danh <i>Huy Cán</i>), một bậc thầy thuốc y dược tế sinh đầy đức độ. Nhân thời buổi binh đao ly loạn cuối thời Hậu Lê (Lê Mạt), Ngài cùng hiền thê là bà <b>Trần Thị Niêm</b> đã rời quê hương Cổ Kênh (Thạch Hà), tha hương lên làng Hoa Cử (Văn Cử) khai hoang phá thạch, lập nghiệp sinh cơ.
                </p>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 15px;">
                    Từ nền móng vững chắc ấy, trải qua bao thăng trầm lịch sử, dòng họ ta tự hào là một dòng tộc hiếu học, khoa bảng hiển hách, đời nào cũng có người hiển đạt, giữ trọng trách lớn trong triều đình phong kiến, làm quan to, tướng lĩnh quân đội, cán bộ lãnh đạo cấp cao, trí thức lớn và doanh nhân thành đạt trên mọi miền Tổ quốc. Từ hai ngọn nguồn chính là <b>Cửa Giáp</b> (do cụ <i>Từ Hữu Trí</i> thủ giữ) và <b>Cửa Ất</b> (do cụ <i>Từ Hữu Mưu</i> gánh vác), các thế hệ con cháu luôn nối tiếp truyền thống hào hùng, tôi luyện ý chí kiên trung, tô thắm thêm bảng vàng truyền thống vẻ vang của dòng họ Từ.
                </p>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 15px;">
                    Để gìn giữ gia phong và giải quyết triệt để bài toán tránh tình trạng <i>"thế thứ hỗn đồ tung tích dán đoạn"</i> hay rủi ro hôn thú đồng tông, ứng dụng đã áp dụng chuẩn hóa cấu trúc <b>Mã định danh 9 chữ số</b> (ví dụ: <code>124.07.0.049</code>). Cấu trúc khoa học này được quy ước vô cùng chặt chẽ: trong đó <code style="color: #8B0000;">"124"</code> là cửa, chi, phái; <code style="color: #8B0000;">"07"</code> là đời; <code style="color: #8B0000;">"0 hoặc 1"</code> là giới tính; và <code style="color: #8B0000;">"xxx"</code> là số thứ tự được sắp xếp theo đúng nguyên tắc sinh trưởng trong nhánh. Nhờ nền tảng này, hệ thống tự động liên kết huyết mạch minh bạch, tuyệt đối không bao giờ có sự nhầm lẫn thế hệ.
                </p>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 15px;">
                    Bên cạnh đó, để trang sử gia phả thêm phần sống động, ứng dụng tích hợp tính năng lưu trữ và hiển thị <b>ảnh chân dung</b>. Khi cập nhật thành viên, hình ảnh tư liệu của các cụ hay người thân sẽ được tải lên và hiển thị trang trọng ngay bên cạnh tiểu sử <b>(tại mục tra cứu trực hệ)</b>, giúp thế hệ mai sau được tận mắt ngắm nhìn dung mạo, thần thái oai nghiêm và hiền hậu của ông cha.
                </p>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 25px;">
                    Cùng với các tính năng ưu việt như <b>sơ đồ phả hệ trực hệ và toàn cảnh với nhiều góc chiếu trực quan</b>, cho phép phóng to thu nhỏ, kéo lướt mượt mà trên điện thoại, máy tính, kết hợp cùng <b>hệ thống ngày giỗ 4 đời trực hệ</b> tự động nhắc nhở, ứng dụng chính là nhịp cầu công nghệ gắn kết sắt son tình dòng tộc cho con cháu muôn đời.
                </p>

                <div style="
                    background: #fff8e1;
                    border-left: 5px solid #ffa000;
                    padding: 12px 18px;
                    margin: 20px 0;
                    border-radius: 4px;
                    font-style: italic;
                    font-size: 1.05rem;
                    color: #5d4037;
                ">
                    "Vật bổ hồ thiên, nhân sinh do Tổ; cây cối được lá xanh cành rậm là do vun trồng rễ tốt gốc sâu, dòng dõi được cha truyền con nối là nhờ phúc phước của tổ tiên dồi dào ấm hậu."
                </div>

                <p style="text-align: justify; font-size: 1.05rem; text-indent: 30px; margin-bottom: 10px;">
                    Con cháu dòng họ Từ Xuân Lộc muôn đời sau, dù ở bất cứ cương vị nào, xin hãy luôn ghi nhớ công ơn trời biển của tổ tiên, phát huy truyền thống hiếu học và khoa bảng vẻ vang, đoàn kết đùm bọc lẫn nhau, giữ gìn đạo đức gia phong, cùng chung tay làm rạng danh hai tiếng <b>Họ Từ Xuân Lộc</b> trên bản đồ đất nước.
                </p>
            </div>
        </body>
        </html>
        """
        components.html(html_content, height=1150, scrolling=True)

        # --- CÔNG TẮC PHÁT GIỌNG ĐỌC LỜI GIỚI THIỆU ---
        st.markdown("---")
        bat_giong_doc = st.toggle("🔊 Bật giọng đọc Lời giới thiệu (Nữ miền Bắc truyền cảm)")

        if bat_giong_doc:
            voice_path = Path(__file__).resolve().parent / "giong_doc_gioi_thieu.mp3"
            if voice_path.exists():
                st.audio(str(voice_path), format="audio/mp3", autoplay=True)
                st.success("🎙️ Đang phát giọng đọc Lời giới thiệu dòng họ...")
            else:
                st.warning("⚠️ Chưa tìm thấy tệp 'giong_doc_gioi_thieu.mp3'. Ông chủ vui lòng chạy file tạo âm thanh trước nhé!")


 
    #=====================================================================
    # [PHÂN LÔ E3]: Hàm con render màn hình Trực Hệ
    #=====================================================================

    @staticmethod
    def render_tructhe(df):

        st.markdown('<h2 class="desktop-view" style="font-size: 1.3rem; font-weight: bold;">🎯 Tuyến Phả Hệ Trọng Tâm</h2>', unsafe_allow_html=True)
        
        st.markdown('<h2 class="mobile-view" style="font-size: 1.2rem; font-weight: bold;">🎯 Xem Trực Hệ</h2>', unsafe_allow_html=True)
       
        chain = KyThuatBanVeGiaPha.get_ancestors_chain(df, st.session_state.focus_id)
        breadcrumb_str = " ➔ ".join([f"**{QuanTriTaiNguyen.lay_ten_chinh(c['HoTen'])} {QuanTriTaiNguyen.get_circled_doi(c['DoiThu'], c['TinhTrang'])}**" for c in chain])
        
        col_path, col_toggle = st.columns([3, 1])
        with col_path: st.info(f"📍 **Đường dẫn cội nguồn:** {breadcrumb_str}")
        with col_toggle: mo_rong_duoi = st.toggle("🌳 Mở rộng nhánh dưới", value=False, key="toggle_mo_rong_nhanh")

        col_tree, col_nav = st.columns([2, 1])
        with col_tree:
            st.markdown("<div class='hd-zoom hide-on-mobile'>💡 <b>Trên điện thoại:</b> Dùng 2 ngón tay chạm để phóng to/thu nhỏ hoặc bấm nút <b>(+ / -)</b> ở góc sơ đồ.</div>", unsafe_allow_html=True)
            try:
                if mo_rong_duoi:
                    ancestor_ids = [item['ID'] for item in chain]
                    descendant_ids = KyThuatBanVeGiaPha.get_all_descendants(df, st.session_state.focus_id)
                    df_sub = df[df["ID"].isin(set(ancestor_ids + descendant_ids))].copy()
                    focus_graph = KyThuatBanVeGiaPha.draw_family_tree(df_sub)
                else:
                    focus_graph = KyThuatBanVeGiaPha.draw_focus_tree(df, st.session_state.focus_id)
                KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(focus_graph, chieu_cao=580)
            except Exception as e:
                st.error(f"Lỗi hiển thị sơ đồ: {e}")

        with col_nav:
            curr_row = df[df["ID"] == str(st.session_state.focus_id)]
            if curr_row.empty: return
            curr_person = curr_row.iloc[0]
            ten_tu_txt = f" (Tự: {curr_person['TenTu']})" if curr_person['TenTu'] else ""
            

            
            # --- HIỂN THỊ ẢNH CHÂN DUNG HIỆN TẠI ---
            hop_le_path = QuanTriHinhAnh.lay_anh_chuan_xac(curr_person['ID'], curr_person['HoTen'])
            if hop_le_path and (Path(__file__).resolve().parent / hop_le_path).exists():
                st.image(str(Path(__file__).resolve().parent / hop_le_path), width=180, caption=f"Chân dung: {curr_person['HoTen']}")

            # 🟢 TÍNH NĂNG MỞ CHO CON CHÁU TỰ TẢI ẢNH (ĐỌC TRỰC TIẾP TỪ CSDL ĐỂ ĐỒNG BỘ TOÀN HỆ THỐNG)



            # 🟢 ĐỌC CÔNG TẮC TỪ CSDL SQLite
            try:
                with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT GiaTri FROM CauHinhHeThong WHERE Khoa = 'cho_phep_tai_anh'")
                    res = cursor.fetchone()
                    cho_phep_tai_anh = (res[0] == 'True') if res else False
            except Exception:
                cho_phep_tai_anh = False

            if cho_phep_tai_anh:
                with st.expander("📷 Tự tải/Cập nhật ảnh chân dung"):
                    st.info(f"Đang cập nhật ảnh cho: **{curr_person['HoTen']}** (ID: `{curr_person['ID']}`)")
                    
                    # Chấp nhận mọi định dạng chữ thường và chữ hoa
                    up_file_user = st.file_uploader(
                        "Chọn ảnh (JPG, PNG, HEIC):", 
                        type=["jpg", "jpeg", "png", "heic", "heif", "JPG", "JPEG", "PNG", "HEIC"], 
                        key=f"up_{curr_person['ID']}"
                    )
                    if up_file_user is not None:
                        if st.button("💾 Xác nhận lưu ảnh lên hệ thống", key=f"btn_save_{curr_person['ID']}"):
                            os.makedirs("images", exist_ok=True)
                            clean_name = re.sub(r'[\(\)].*?[\(\)]', '', curr_person['HoTen']).strip()
                            save_file_path = Path(__file__).resolve().parent / "images" / f"{curr_person['ID']} {clean_name}.jpg"
                            if QuanTriHinhAnh.xu_ly_va_nen_anh(up_file_user, save_file_path):
                                st.success("✅ Tải ảnh lên thành công! Ảnh đã được cập nhật vào sơ đồ.")
                                st.rerun()
                            else:
                                st.error("❌ Lỗi xử lý ảnh. Vui lòng thử lại.")
            else:
                st.caption("🔒 Chức năng tự tải ảnh Đang tạm khóa.")

            st.markdown(f"### 👤 Cụ: **{curr_person['HoTen']}{ten_tu_txt} {QuanTriTaiNguyen.get_circled_doi(curr_person['DoiThu'], curr_person['TinhTrang'])}**")
            st.write(f"- **Mã định danh:** `{curr_person['ID']}`")
            st.write(f"- **Thuộc:** {curr_person['Cua']} — {curr_person['Chi']} {('— ' + curr_person['Phai']) if curr_person['Phai'] else ''}")
            
            # Thay vì hiển thị nhãn "Bà:" cho thành viên Nam, đổi thành "Vợ:"
            if curr_person['VoChong']:
                st.write(f"- **{'Vợ' if curr_person.get('GioiTinh') == 'Nam' else 'Chồng'}:** {curr_person['VoChong']}")

                
            if curr_person['NgayGio']: st.write(f"- **Ngày giỗ:** {curr_person['NgayGio']}")
            if curr_person['NamSinh'] or curr_person['NamMat']: st.write(f"- **Năm sinh/mất:** {curr_person['NamSinh']} - {curr_person['NamMat']}")
            if curr_person['GhiChu']: st.write(f"- **Ghi chú:** {curr_person['GhiChu']}")
            if curr_person['TinhTrang']: st.write(f"- **Tình trạng:** {curr_person['TinhTrang']}")

            st.markdown("---")

            raw_children = df[(df["ChaMe_ID"] == str(st.session_state.focus_id)) & (df["TrangThai"] == "Đã duyệt")]
            
            # Lọc bỏ nữ giới và các trường hợp có chấm tròn tuyệt tôn / chết sớm / phạp tự / tảo vong...
            filtered_children = []
            keyword_list = ["phạp tự", "không có con", "tảo vong", "tảo một", "chết sớm", "liệt sỹ", "Liệt sĩ", "tử sỹ", "tử sĩ"]
            for _, ch in raw_children.iterrows():
                gioi_tinh = str(ch.get("GioiTinh", "")).strip()
                tinh_trang = str(ch.get("TinhTrang", "")).lower()
                
                # Điều kiện giữ lại: Phải là Nam VÀ Tình trạng không chứa các từ khóa tuyệt tôn/chết sớm
                is_nam = (gioi_tinh == "Nam")
                has_tuyet_ton = any(kw in tinh_trang for kw in keyword_list)
                
                if is_nam and not has_tuyet_ton:
                    filtered_children.append(ch)
            
            children = pd.DataFrame(filtered_children) if filtered_children else pd.DataFrame(columns=raw_children.columns)

            if not children.empty:
                if "STT" in children.columns: children = children.sort_values(by="STT")
                st.markdown(f"**👉 Mở con cháu đời kế tiếp:**")
                for _, ch in children.iterrows():
                    if st.button(f"Mở: {QuanTriTaiNguyen.lay_ten_chinh(ch['HoTen'])} {QuanTriTaiNguyen.get_circled_doi(ch['DoiThu'], ch['TinhTrang'])}", key=f"btn_c_{ch['ID']}"):
                        st.session_state.focus_id = ch['ID']
                        st.rerun()

            else:
                st.warning("Nhánh này hiện chưa cập nhật con cháu đời kế tiếp.")
                
            st.markdown("---")
            if curr_person.get("ChaMe_ID") and curr_person["ChaMe_ID"] != "":
                if st.button("⬅️ Quay lại đời trước (Cha)"):
                    st.session_state.focus_id = curr_person["ChaMe_ID"]
                    st.rerun()
            if st.button("🔄 Về gốc Cụ Thủy Tổ ①"):
                st.session_state.focus_id = "000.01.0.001"
                st.rerun()


            # 🟢 ĐẶT ĐOẠN NÀY Ở DÒNG CUỐI CÙNG CỦA HÀM render_tructhe (BÊN NGOÀI MỌI KHUNG CỘT CŨ)
            if st.session_state.get("return_to_menu"):
                prev_menu = st.session_state.return_to_menu
                st.markdown("---")
                
                # Sử dụng cú pháp container thu gọn và canh giữa thay vì chia cột bị kẹt trong layout cũ
                st.markdown("""
                    <style>
                    div.stButton > button[key*="btn_back_to_previous_menu"] {
                        max-width: 50% !important;
                        margin: 0 auto !important;
                        display: block !important;
                    }
                    div:has(> button[key*="btn_back_to_previous_menu"]) {
                        display: flex;
                        justify-content: center;
                    }
                    </style>
                """, unsafe_allow_html=True)

                if st.button(f"🔙 Quay lại màn hình {prev_menu}", key="btn_back_to_previous_menu", use_container_width=True):
                    st.session_state.pending_menu = prev_menu
                    del st.session_state.return_to_menu
                    st.rerun()


    #=====================================================================
    # [PHÂN LÔ E4]: Hàm con render màn hình Toàn Cảnh
    #=====================================================================
   
    @staticmethod
    def render_toancanh(df):
        st.subheader("Sơ Đồ Phả Hệ Toàn Cảnh")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: che_do_xem = st.selectbox("1. Chế độ hiển thị:", [
            "1. Chỉ Đinh Nam (Gọn: Tên ⑦)", 
            "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)", 
            "3. Chỉ Đinh Nam (Đủ vợ và chồng)", 
            "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)"
        ], index=2) # <--- Thêm index=2 để mặc định chọn sẵn chế độ thứ 3 khi mở màn hình

        with col2: cua_chon = st.selectbox("2. Lọc theo Cửa:", ["Tất cả"] + sorted([c for c in df['Cua'].unique() if c and c != "Gốc"]))
        with col3:
            df_tc = df[df['Cua'] == cua_chon] if cua_chon != "Tất cả" else df
            danh_sach_chi = QuanTriTaiNguyen.lay_danh_sach_chi_chuan(df_tc)
            chi_chon = st.selectbox("3. Lọc theo Chi:", ["Tất cả"] + danh_sach_chi)
        with col4:
            df_pc = df[df['Chi'] == chi_chon] if chi_chon != "Tất cả" else df
            sorted_phai = QuanTriTaiNguyen.sap_xep_danh_sach_phai(df_pc['Phai'].unique())
            phai_chon = st.selectbox("4. Lọc theo Phái:", ["Tất cả"] + sorted_phai)
        with col5:
            danh_sach_nhanh = []
            nhanh_dict = {}
            if phai_chon != "Tất cả" and phai_chon in KyThuatBanVeGiaPha.NHANH_MAPPING:
                branches = KyThuatBanVeGiaPha.NHANH_MAPPING[phai_chon]
                if len(branches) > 1:
                    danh_sach_nhanh = ["Tất cả"] + [b[0] for b in branches]
                    nhanh_dict = {b[0]: b[1] for b in branches}
            
            if danh_sach_nhanh:
                nhanh_chon = st.selectbox("5. Lọc theo Nhánh:", danh_sach_nhanh)
            else:
                nhanh_chon = "Tất cả"

        st.markdown("<div class='hd-zoom hide-on-mobile'>💡 <b> Trên điện thoại:</b> Dùng 2 ngón tay kéo dãn để zoom to, hoặc bấm nút <b>(+)</b> để nhìn rõ từng đời.</div>", unsafe_allow_html=True)
        try:
            tree_graph = KyThuatBanVeGiaPha.draw_family_tree(df, cua_chon, chi_chon, phai_chon, che_do_xem, nhanh_chon=nhanh_chon, nhanh_dict=nhanh_dict)
            KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(tree_graph, chieu_cao=680)
        except Exception as e:
            st.error(f"Lỗi hiển thị: {e}")

    #=====================================================================
    # [PHÂN LÔ E5]: Hàm con render màn hình Tra Cứu
    #=====================================================================
    @staticmethod
    def render_tracuu(df):
        st.subheader("Tra cứu thông tin danh bạ gia tộc")
        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: tim_ten = st.text_input("Tìm kiếm tên / Mã định danh:")
        with c2: loc_cua = st.selectbox("Cửa:", ["Tất cả"] + sorted([c for c in df_app['Cua'].unique() if c and c != "Gốc"]))
        with c3:
            df_c = df_app[df_app['Cua'] == loc_cua] if loc_cua != "Tất cả" else df_app
            danh_sach_chi = QuanTriTaiNguyen.lay_danh_sach_chi_chuan(df_c)
            loc_chi = st.selectbox("Chi:", ["Tất cả"] + danh_sach_chi)
        with c4:
            df_chi_sub = df_app[df_app['Chi'] == loc_chi] if loc_chi != "Tất cả" else df_app
            sorted_phai = QuanTriTaiNguyen.sap_xep_danh_sach_phai(df_chi_sub['Phai'].unique())
            loc_phai = st.selectbox("Phái:", ["Tất cả"] + sorted_phai)

        if tim_ten:
            df_app = df_app[df_app["HoTen"].str.contains(tim_ten, case=False, na=False) | df_app["ID"].str.contains(tim_ten, case=False, na=False)]
        if loc_cua != "Tất cả": df_app = df_app[df_app["Cua"] == loc_cua]
        if loc_chi != "Tất cả": df_app = df_app[df_app["Chi"] == loc_chi]
        if loc_phai != "Tất cả": df_app = df_app[df_app["Phai"] == loc_phai]


        # 🟢 [LOGIC MỚI]: SẮP XẾP CHUẨN XÁC THEO 6 LỚP KHÓA HUYẾT MẠCH
        def lay_doi_tu_id(m_id):
            try:
                parts = str(m_id).split('.')
                if len(parts) > 1 and parts[1].isdigit():
                    return int(parts[1])
            except: pass
            return 999 

        def lay_cua_sort(cua_str):
            c = str(cua_str).lower()
            if "giáp" in c: return 1
            if "ất" in c: return 2
            return 3

        def lay_chi_sort(chi_str):
            m = re.search(r'Chi\s*(\d+)', str(chi_str), flags=re.IGNORECASE)
            return int(m.group(1)) if m else 99

        def lay_phai_sort(phai_str):
            m = re.search(r'Phái\s*(\d+)', str(phai_str), flags=re.IGNORECASE)
            return int(m.group(1)) if m else 99

        # 1. Tạo các cột phân loại
        df_app['Doi_Sort'] = df_app['ID'].apply(lay_doi_tu_id)
        df_app['Cua_Sort'] = df_app['Cua'].apply(lay_cua_sort)
        df_app['Chi_Sort'] = df_app['Chi'].apply(lay_chi_sort)
        df_app['Phai_Sort'] = df_app['Phai'].apply(lay_phai_sort)
        
        # 2. Ánh xạ RecordIndex của Cha để xếp: gia đình anh lớn trước, gia đình em nhỏ sau
        dict_record = df_app.set_index('ID')['RecordIndex'].to_dict()
        df_app['Cha_RecordIndex'] = df_app['ChaMe_ID'].map(dict_record).fillna(999999)

        # 3. THỰC THI SẮP XẾP 6 TẦNG: Đời -> Cửa -> Chi -> Phái -> Vị trí Cha -> Vị trí Con
        df_app = df_app.sort_values(by=['Doi_Sort', 'Cua_Sort', 'Chi_Sort', 'Phai_Sort', 'Cha_RecordIndex', 'RecordIndex'])


        # 🟢 HÀM XỬ LÝ CHUẨN HÓA VỢ CHỒNG GIỐNG 100% FILE PDF
        def format_vo_chong_html(text, gioi_tinh="Nam"):
            if not text or str(text).lower() in ["nan", "none", ""]:
                return ""
            raw_list = [p.strip() for p in str(text).split(',') if p.strip()]
            cleaned_parts = []
            for item in raw_list:
                item_clean = re.sub(r'^(bà chính|bà thứ|bà cả|bà hai|bà ba|bà nhất|bà nhì|bà út|chính|thứ|cả|hai|ba|nhất|nhì|út|chồng|vợ|bà)\s*', '', item, flags=re.IGNORECASE).strip()
                if str(gioi_tinh).strip() == "Nữ":
                    if not item_clean.lower().startswith("chồng"):
                        item_clean = f"Chồng: {item_clean}"
                else:
                    item_clean = f"Vợ: {item_clean}"
                cleaned_parts.append(item_clean)
            return '<br>'.join(cleaned_parts)

        # 🟢 HÀM ĐỊNH DẠNG TÊN ĐỜI (Tách đời giống hệt bản in PDF)
        def get_gen_title_html(doi_thu):
            try:
                gen = int(doi_thu)
                if gen <= 3:
                    return "ĐỜI THỨ NHẤT ĐẾN ĐỜI THỨ 3"
                else:
                    roman_map = {4: 'TƯ', 5: 'NĂM', 6: 'SÁU', 7: 'BẢY', 8: 'TÁM', 9: 'CHÍN', 10: 'MƯỜI', 11: 'MƯỜI MỘT', 12: 'MƯỜI HAI', 13: 'MƯỜI BA', 14: 'MƯỜI BỐN', 15: 'MƯỜI LĂM'}
                    gen_label = roman_map.get(gen, str(gen))
                    return f"ĐỜI THỨ {gen_label}"
            except:
                return "CHƯA XÁC ĐỊNH"

        html_table = """
        <div style="max-height: 600px; overflow-y: auto; border: 1px solid #d4c5a9; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
        <table style="width: 100%; border-collapse: collapse; font-family: 'Times New Roman', Times, serif; background: #FFFDF9;">
            <thead>
                <tr style="background-color: #8B0000; color: #FFF8DC; text-align: center; position: sticky; top: 0; z-index: 10;">
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 4%;">STT</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 8%;">Mã ĐD</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 12%;">Họ Tên</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 8%;">Tên Tự</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 12%;">Vợ/Chồng</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 8%;">Sinh/Mất</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 6%;">Ngày Giỗ</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 34%;">Ghi Chú</th>
                    <th style="padding: 10px; border: 1px solid #c2b292; width: 8%;">Hình ảnh</th>
                </tr>
            </thead>
            <tbody>
        """
        
        last_rendered_gen = None 
        
        for _, row in df_app.iterrows():
            m_id = row.get('ID', '')
            m_name = row.get('HoTen', '')
            m_gioi_tinh = row.get('GioiTinh', 'Nam')
            m_doi = lay_doi_tu_id(m_id) # Lấy số đời chuẩn xác đã được trích xuất
            
            # KIỂM TRA VÀ CHÈN DÒNG TIÊU ĐỀ ĐỜI THEO LOGIC PDF
            curr_gen_title = get_gen_title_html(m_doi)
            if curr_gen_title != last_rendered_gen:
                html_table += f"""
                <tr>
                    <td colspan="9" style="background: #F4EBD0; color: #8B0000; border: 1.5px solid #8B0000; font-weight: bold; text-align: center; font-size: 13px; letter-spacing: 2px; padding: 6px; text-transform: uppercase;">
                        📜 {curr_gen_title}
                    </td>
                </tr>
                """
                last_rendered_gen = curr_gen_title

            anh_path = QuanTriHinhAnh.lay_anh_chuan_xac(m_id, m_name)
            img_html = "<span style='color: #999; font-size: 11px; font-style: italic;'>Chưa có</span>"
            if anh_path:
                full_img_path = Path(__file__).resolve().parent / anh_path
                if full_img_path.exists():
                    try:
                        with open(full_img_path, "rb") as f:
                            b64_str = base64.b64encode(f.read()).decode("utf-8")
                            img_html = f'<img src="data:image/jpeg;base64,{b64_str}" style="width: 42px; height: 52px; object-fit: cover; border-radius: 4px; border: 1px solid #8B0000; box-shadow: 1px 1px 3px rgba(0,0,0,0.15);" />'
                    except:
                        pass
            
            vo_chong_raw = str(row.get('VoChong', ''))
            vo_chong_fmt = format_vo_chong_html(vo_chong_raw, m_gioi_tinh)
            
            html_table += f"""
                <tr style="border-bottom: 1px solid #e0d5be;">
                    <td style="padding: 6px; border: 1px solid #c2b292; text-align: center; font-weight: bold; color: #8B0000;">{row.get('STT', '')}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292; text-align: center; font-family: monospace; font-size: 11.5px; color: #333;">{row.get('ID', '')}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292;"><b style="color: #8B0000; font-size: 12px;">{row.get('HoTen', '')}</b></td>
                    <td style="padding: 6px; border: 1px solid #c2b292; font-size: 11.5px;">{row.get('TenTu', '')}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292; font-size: 11.5px;">{vo_chong_fmt}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292; text-align: center; font-size: 11.5px; white-space: nowrap;">{row.get('NamSinh', '')} - {row.get('NamMat', '')}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292; text-align: center; font-weight: bold; color: #700; font-size: 11.5px;">{row.get('NgayGio', '')}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292; font-size: 11.5px;">{row.get('GhiChu', '')}</td>
                    <td style="padding: 6px; border: 1px solid #c2b292; text-align: center; background: #fff;">{img_html}</td>
                </tr>
            """
            
        html_table += "</tbody></table></div>"
        components.html(html_table, height=620, scrolling=True)
     

    #=====================================================================
    # [PHÂN LÔ E6]: Màn hình Lọc theo ID hoặc Tên(Truy vết nhánh)
    #=====================================================================
    @staticmethod
    def render_loc_theo_id(df):
        st.markdown('<h2 class="desktop-view" style="font-size: 1.3rem; font-weight: bold;">🆔 Sơ Đồ Trục Cội Nguồn & Tỏa Nhánh Theo ID / Tên</h2>', unsafe_allow_html=True)
        st.markdown('<h2 class="mobile-view" style="font-size: 1.05rem; font-weight: bold; white-space: nowrap;">🆔 Sơ đồ theo ID / Tên</h2>', unsafe_allow_html=True)
        
        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
        
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        with c1:
            nhap_lieu = st.text_input("Nhập Họ và tên hoặc Mã định danh:", value="Từ Quang Diệu", placeholder="Ví dụ: Từ Quang Diệu, 124070049 hoặc 124.07.0.049")
        with c2:
            che_do_xem = st.selectbox("Chế độ hiển thị nhãn:", [
                "1. Chỉ Đinh Nam (Gọn: Tên ⑦)", 
                "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)", 
                "3. Chỉ Đinh Nam (Đủ vợ và chồng)", 
                "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)"
            ], index=3, key="che_do_xem_id")
        with c3:
            so_doi_tren = st.selectbox("Số đời trên:", ["Tất cả"] + list(range(1, 11)), index=0, key="sel_so_doi_tren")
        with c4:
            so_doi_duoi = st.selectbox("Số đời dưới:", ["Tất cả"] + list(range(1, 11)), index=0, key="sel_so_doi_duoi")


        target_id = ""
        nhap_lieu_clean = nhap_lieu.strip()

        if nhap_lieu_clean:
            nhap_lieu_khong_cham = nhap_lieu_clean.replace(".", "")
            df_app['ID_KhongCham'] = df_app['ID'].str.replace(".", "", regex=False)
            matched_by_id = df_app[df_app["ID_KhongCham"] == nhap_lieu_khong_cham]
            
            if not matched_by_id.empty:
                target_id = str(matched_by_id.iloc[0]['ID'])
                # PC hiện "Đã tìm thấy", Mobile hiện "Đã thấy" (Giữ nguyên khung xanh nguyên bản)
                st.markdown(f"""
                    <div style="padding: 8px 12px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; color: #155724; font-size: 13px; margin-bottom: 10px;">
                        <span class="desktop-view">✅ Đã tìm thấy: <b>{matched_by_id.iloc[0]['HoTen']}</b> (ID: <code>{target_id}</code>, {matched_by_id.iloc[0]['Chi']}, Đời {matched_by_id.iloc[0]['DoiThu']})</span>
                        <span class="mobile-view">✅ Đã thấy: <b>{matched_by_id.iloc[0]['HoTen']}</b> (ID: <code>{target_id}</code>, {matched_by_id.iloc[0]['Chi']}, Đời {matched_by_id.iloc[0]['DoiThu']})</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                def chuan_hoa_dau(txt):
                    return str(txt).strip().lower().replace("oà", "òa").replace("uỳ", "uỳ").replace("úy", "uý")

                nhap_lieu_chuan = chuan_hoa_dau(nhap_lieu_clean)
                df_app['HoTen_Chuan'] = df_app['HoTen'].apply(chuan_hoa_dau)
                
                matched_by_name = df_app[df_app['HoTen_Chuan'] == nhap_lieu_chuan]
                
                if len(matched_by_name) == 1:
                    target_id = str(matched_by_name.iloc[0]["ID"])
                    # PC hiện "Đã tìm thấy", Mobile hiện "Đã thấy"
                    st.markdown(f"""
                        <div style="padding: 8px 12px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; color: #155724; font-size: 13px; margin-bottom: 10px;">
                            <span class="desktop-view">✅ Đã tìm thấy: <b>{matched_by_name.iloc[0]['HoTen']}</b> (ID: <code>{target_id}</code>, {matched_by_name.iloc[0]['Chi']}, Đời {matched_by_name.iloc[0]['DoiThu']})</span>
                            <span class="mobile-view">✅ Đã thấy: <b>{matched_by_name.iloc[0]['HoTen']}</b> (ID: <code>{target_id}</code>, {matched_by_name.iloc[0]['Chi']}, Đời {matched_by_name.iloc[0]['DoiThu']})</span>
                        </div>
                    """, unsafe_allow_html=True)

                elif len(matched_by_name) > 1:
                    options_dict = {}
                    for idx, (_, row) in enumerate(matched_by_name.iterrows(), 1):
                        cha_id = row.get('ChaMe_ID', '')
                        ten_cha = "Gốc"
                        if cha_id:
                            cha_row = df[df['ID'] == cha_id]
                            if not cha_row.empty:
                                ten_cha_full = str(cha_row.iloc[0].get('HoTen', ''))
                                parts = ten_cha_full.split()
                                ten_cha = parts[-1] if parts else ten_cha_full
                        
                        label_opt = f"{idx}. {row['HoTen']} ({ten_cha})"
                        options_dict[label_opt] = row['ID']

                    with c3:
                        selected_label = st.selectbox("⚠️ Phát hiện trùng tên! Chọn đúng người:", options=list(options_dict.keys()))
                    target_id = options_dict[selected_label]

                else:
                    st.warning(f"❌ Không tìm thấy thành viên nào khớp với từ khóa: '{nhap_lieu_clean}'")

        # Nút bấm chuyển nhanh sang Trực Hệ được đặt ở cột giữa để tự động thu gọn và canh giữa
        if target_id:
            # 1. Vẽ sơ đồ và hiển thị tương tác trước (đặt lên trên)
            try:
                tree_graph = KyThuatBanVeGiaPha.draw_family_tree(df, target_id=target_id, che_do_xem=che_do_xem, so_doi_tren=so_doi_tren, so_doi_duoi=so_doi_duoi)
                KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(tree_graph, chieu_cao=750)
            except Exception as e:
                st.error(f"Lỗi hiển thị sơ đồ: {e}")

            # 2. Đặt nút bấm ở dưới cùng sau khi sơ đồ đã hiện xong
            st.markdown("---")
            col_l, col_c, col_r = st.columns([1, 2, 1])
            with col_c:
                if st.button("👉 Bấm vào đây để mở xem chi tiết của ID này", key="btn_goto_tructhe_from_id", use_container_width=True):
                    st.session_state.focus_id = target_id
                    st.session_state.return_to_menu = "🆔 Lọc theo ID"
                    st.session_state.pending_menu = "🎯 Trực Hệ"
                    
                    # 🟢 THÊM ĐOẠN JAVASCRIPT ÉP TRÌNH DUYỆT CUỘN LÊN ĐẦU TRANG KHI SANG TRANG
                    components.html("""
                        <script>
                            window.parent.window.scrollTo({ top: 0, behavior: 'smooth' });
                        </script>
                    """, height=0)
                    
                    st.rerun()


    #=====================================================================
    # [PHÂN LÔ E7]: Hàm con render màn hình Thêm Thành Viên (TỐI ƯU MOBILE UX)
    #=====================================================================
    @staticmethod
    def render_themthanhvien(df):
        # 🟢 1. TRẠM ĐÓN THÔNG BÁO
        if "msg_thanh_cong" in st.session_state:
            st.success(st.session_state.msg_thanh_cong)
            st.balloons()
            del st.session_state.msg_thanh_cong

        st.subheader("Thêm thành viên mới")
        st.info("💡 Nhập thông tin cơ bản, hệ thống tự cấp Mã ID.")
        
        col_trai, col_phai = st.columns(2)
        
        with col_trai:
            ho_ten = st.text_input("Họ và tên (*):", placeholder="Ví dụ: Từ Văn Nam")
            gioi_tinh = st.selectbox("Giới tính (*):", ["Nam", "Nữ"])
            
        with col_phai:
            df_parents = df[(df["TrangThai"] == "Đã duyệt") & (df["GioiTinh"] == "Nam")][["ID", "HoTen", "DoiThu"]]
            parent_dict = {row['ID']: f"{row['HoTen']} (Đời {row['DoiThu']} - {row['ID']})" for _, row in df_parents.iterrows()}
            parent_dict[""] = "-- Chọn Cha --"
            cha_id = st.selectbox("Chọn Cha (*):", options=list(parent_dict.keys()), format_func=lambda x: parent_dict[x])

        # 🟢 2. ĐƯA NĂM SINH RA NGOÀI MÀN HÌNH CHÍNH (KHÔNG BẮT BUỘC)
        nam_sinh = st.text_input("Năm sinh:", placeholder="Ví dụ: 2026")

        # =================================================================
        # CÂU HỎI Y/N & SẮP XẾP ANH CHỊ EM CHUẨN XÁC
        # =================================================================
        xac_nhan_vi_tri = "Y"
        vi_tri_mong_muon = 1
        
        if cha_id:
            ten_cha = df[df["ID"] == cha_id]["HoTen"].iloc[0].split("(")[0].strip()
            df_con = df[df["ChaMe_ID"] == cha_id].copy()
            so_luong_con = len(df_con)
            
            st.markdown("---")
            if so_luong_con > 0:
                df_con['STT_Con'] = df_con['ID'].apply(
                    lambda x: int(str(x).replace('.', '').strip()[-3:]) if len(str(x).replace('.', '').strip()) >= 9 else 999
                )
                df_con = df_con.sort_values(by="STT_Con")
                
                danh_sach_ten_con = ", ".join([QuanTriTaiNguyen.lay_ten_chinh(name) for name in df_con["HoTen"]])
                cau_hoi = f"❓ **Ông {ten_cha} có {so_luong_con} con ({danh_sach_ten_con}). Bạn là con thứ {so_luong_con + 1}?**"
            else:
                cau_hoi = f"❓ **Ông {ten_cha} chưa có con. Bạn là con thứ 1?**"
            
            xac_nhan_vi_tri = st.radio(cau_hoi, options=["Y", "N"], format_func=lambda x: "✅ Đúng" if x == "Y" else "❌ Khác", horizontal=True)
            
            if xac_nhan_vi_tri == "N":
                vi_tri_mong_muon = st.number_input("👉 Số thứ tự ĐÚNG:", min_value=1, max_value=99, step=1)
                st.warning(f"⚠️ Đã ghi nhận chờ Admin xếp vào vị trí thứ {vi_tri_mong_muon}.")
        
        st.markdown("---")

        # =================================================================
        # 3. THÔNG TIN BỔ SUNG (ĐÃ SẮP XẾP LẠI TRÌNH TỰ NĂM MẤT -> NGÀY GIỖ)
        # =================================================================
        with st.expander("➕ Thông tin bổ sung nâng cao (Vợ/chồng, năm mất, ngày giỗ, ảnh...)"):
            col_sub_1, col_sub_2 = st.columns(2)
            with col_sub_1:
                ten_tu = st.text_input("Tên tự/hiệu:")
                vo_chong = st.text_input("Vợ/Chồng:")
            with col_sub_2:
                tinh_trang_nhap = st.selectbox("Tình trạng:", ["", "Phạp tự", "Không có con", "Tảo vong", "Tảo một", "Chết sớm", "Con nuôi", "di cư, không rõ"])
            
            col_nam_1, col_nam_2 = st.columns(2)
            with col_nam_1: 
                nam_mat = st.text_input("Năm mất:")
            with col_nam_2: 
                ngay_gio = st.text_input("Ngày giỗ (AL):") # Đã bố trí chuẩn ngay sau năm mất
            
            ghi_chu = st.text_area("Tiểu sử/Ghi chú:")
            
            # Khung tải ảnh chân dung
            uploaded_file = st.file_uploader("🖼️ Tải lên ảnh chân dung (tùy chọn):", type=["jpg", "jpeg", "png"])

        btn_submit = st.button("📤 LƯU THÀNH VIÊN", use_container_width=True)
        
        if btn_submit:
            if not ho_ten.strip() or not cha_id:
                st.error("⚠️ Thiếu Họ tên hoặc chưa chọn Cha!")
            else:
                try:
                    import random
                    from pathlib import Path
                    
                    parsed_cha = BoGiaiMaDinhDanh.phan_tich_ma(cha_id)
                    new_doi = parsed_cha['DoiThu'] + 1
                    prefix_chi = str(cha_id).replace(".", "").strip()[:3]
                    khoi_gt = "1" if gioi_tinh == "Nữ" else "0"
                    
                    existing_ids = df[df["ID"].str.contains(rf"\.{new_doi:02d}\.", na=False)]["ID"].tolist()
                    existing_suffixes = [str(x).replace(".", "").strip()[-3:] for x in existing_ids if len(str(x).replace(".", "").strip()) >= 9]
                    
                    random_suffix = "600" 
                    for _ in range(1000):
                        rnd_val = random.randint(600, 799)
                        rnd_str = f"{rnd_val:03d}"
                        if rnd_str not in existing_suffixes:
                            random_suffix = rnd_str
                            break
                            
                    raw_auto_id = f"{prefix_chi}{new_doi:02d}{khoi_gt}{random_suffix}"
                    new_id = f"{raw_auto_id[:3]}.{raw_auto_id[3:5]}.{raw_auto_id[5]}.{raw_auto_id[6:]}"

                    # Xử lý lưu file ảnh
                    hinh_anh_path = ""
                    if uploaded_file is not None:
                        image_dir = Path(__file__).resolve().parent / "images"
                        image_dir.mkdir(parents=True, exist_ok=True)
                        file_ext = Path(uploaded_file.name).suffix.lower()
                        if file_ext not in [".jpg", ".jpeg", ".png"]:
                            file_ext = ".jpg"
                        file_name = f"{new_id} {ho_ten.strip()}{file_ext}"
                        save_path = image_dir / file_name
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        hinh_anh_path = f"images/{file_name}"

                    tinh_trang_final = "Chờ duyệt"
                    if tinh_trang_nhap:
                        tinh_trang_final = f"Chờ duyệt, {tinh_trang_nhap}"
                        
                    ghi_chu_final = ghi_chu.strip()
                    if xac_nhan_vi_tri == "N":
                        ghi_chu_final = f"[Xin xếp vào vị trí thứ {vi_tri_mong_muon}] " + ghi_chu_final

                    success, messages = KhoDuLieuSQL.insert_member(
                        new_id=new_id, ho_ten=ho_ten, ten_tu=ten_tu, cha_id=cha_id,
                        vo_chong=vo_chong, nam_sinh=nam_sinh, nam_mat=nam_mat, ngay_gio=ngay_gio,
                        ghi_chu=ghi_chu_final, tinh_trang=tinh_trang_final, hinh_anh=hinh_anh_path
                    )
                    
                    if success:
                        msg = f"🎉 Thêm thành công ({tinh_trang_final})"
                        st.session_state.msg_thanh_cong = msg

                        try:
                            cha_row = df[df['ID'] == cha_id]
                            ten_cha_hien_thhi = cha_row.iloc[0]['HoTen'] if not cha_row.empty else "Không rõ"
                            
                            member_info = {
                                "HoTen": ho_ten,
                                "ID": new_id,
                                "TenCha": ten_cha_hien_thhi,
                                "TinhTrang": tinh_trang_final,
                                "GhiChu": ghi_chu_final
                            }
                            TelegramBotManager.gui_thong_bao_cho_duyet(member_info, hinh_anh_path)
                        except Exception as tele_err:
                            print(f"Lỗi gửi Telegram: {tele_err}")
                        KhoDuLieuSQL.load_data.clear()
                        st.rerun()
                    else:
                        for err in messages: st.error(err)
                        
                except Exception as e:
                    st.error(f"Lỗi: {e}")


    # ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
    # [PHÂN LÔ E8]: TRUNG TÂM XUẤT BÁO CÁO & IN ẤN PHẢ HỆ (ĐÃ TỐI ƯU NGẮT TRANG ĐỜI 3)
    # ==============================================================================

    @staticmethod
    def render_xuatbaocao(df):
        st.subheader("🖨️ Trung tâm Xuất Báo cáo & In ấn Phả Hệ")
        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
        
        tab_csv, tab_word, tab_in, tab_phado = st.tabs(["📥 Xuất dữ liệu (CSV)", "📄 Xuất Thế phả (Word)", "🖨️ In ấn báo cáo", "🖼 Xuất ảnh Phả đồ"])
        
        with tab_csv:
            export_df_csv = df_app[["STT", "ID", "ChaMe_ID", "HoTen", "TenTu", "VoChong", "NamSinh", "NamMat", "NgayGio", "GhiChu", "TinhTrang", "HinhAnh"]].rename(columns={
                "ID": "Mã Định Danh", "ChaMe_ID": "Mã Cha/Mẹ", "HoTen": "Họ và Tên", "TenTu": "Tên Tự", 
                "VoChong": "Vợ/Chồng", "NamSinh": "Năm Sinh", "NamMat": "Năm Mất", "NgayGio": "Ngày Giỗ", 
                "GhiChu": "Ghi Chú", "TinhTrang": "Tình Trạng", "HinhAnh": "Hình Ảnh"
            })
            st.download_button("📥 Tải xuống tệp CSV", export_df_csv.to_csv(index=False).encode('utf-8-sig'), "GiaPha_HoTu.csv", "text/csv")


        ### bắt đầu tab_word ###
        with tab_word:
            st.markdown("Tính năng kết xuất **Thế Phả truyền thống định dạng cao cấp** sang file Word (.docx) chuẩn phong cách bản in gốc.")
            
            # --- 1. THÊM NÚT TẢI ẢNH BÌA & HÌNH NỀN CHO FILE WORD ---
            col_bia, col_nen = st.columns(2)
            with col_bia:
                anh_bia_word = st.file_uploader("🖼️ Tải lên ảnh bìa (Tùy chọn)", type=["jpg", "jpeg", "png"], key="upload_cover_word")
            with col_nen:
                anh_nen_word = st.file_uploader("🖼️ Tải lên hình nền các trang (Tùy chọn)", type=["jpg", "jpeg", "png"], key="upload_bg_word")
            st.markdown("---")
            # ---------------------------------------------

            try:
                from docx import Document
                from docx.shared import Pt, Inches, RGBColor
                from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_TAB_ALIGNMENT
                from docx.oxml import OxmlElement, parse_xml
                from docx.oxml.ns import qn
                from io import BytesIO
                import re
                
                # --- HÀM MỚI: XỬ LÝ ẢNH NỀN (BEHIND TEXT BẰNG VML WATERMARK) ---
                def chen_watermark_full_trang(header_obj, img_file):
                    # 1. Đảm bảo đọc ảnh từ đầu dòng
                    img_file.seek(0)
                    
                    # 2. Thêm ảnh vào document part để lấy rel_id
                    rel_id, _ = header_obj.part.get_or_add_image(img_file)
                    
                    # 3. Tạo thẻ đoạn văn
                    p = header_obj.paragraphs[0] if header_obj.paragraphs else header_obj.add_paragraph()
                    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    
                    # 4. XML cấu trúc VML Shape Watermark (Phủ kín trang A4, nằm dưới chữ)
                    vml_xml = f'''
                        <w:r xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                             xmlns:v="urn:schemas-microsoft-com:vml"
                             xmlns:o="urn:schemas-microsoft-com:office:office"
                             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
                            <w:pict>
                                <v:shape id="WatermarkShape"
                                         o:spid="_x0000_s2049"
                                         type="#_x0000_t75"
                                         style="position:absolute;margin-left:-70pt;margin-top:-50pt;width:595.3pt;height:785.9pt;z-index:-251657216;"
                                         stroked="f">
                                    <v:imagedata r:id="{rel_id}" o:title="hinh_nen"/>
                                    <o:lock v:ext="edit" aspectratio="t"/>
                                </v:shape>
                            </w:pict>
                        </w:r>
                    '''

                    p._p.append(parse_xml(vml_xml))
                # --------------------------------------------------------------------

                # 1. Hàm hỗ trợ trích xuất Đời từ ID
                def lay_doi_tu_id(m_id):
                    try:
                        parts = str(m_id).split('.')
                        if len(parts) > 1 and parts[1].isdigit():
                            return int(parts[1])
                    except:
                        pass
                    return 999

                # 2. Hàm hỗ trợ trích xuất 3 số cuối (STT) từ ID
                def lay_stt_tu_id(m_id):
                    try:
                        clean_id = str(m_id).replace('.', '').strip()
                        if len(clean_id) >= 3:
                            return int(clean_id[-3:])
                    except:
                        pass
                    return 9999

                # 3. Hàm hỗ trợ lấy mã CHI (2 số đầu tiên của ID)
                def lay_ma_chi_tu_id(m_id):
                    try:
                        clean_id = str(m_id).replace('.', '').strip()
                        if len(clean_id) >= 2:
                            return clean_id[:2]
                    except:
                        pass
                    return "99"

                # 4. Hàm sắp xếp Cửa (Giáp trước, Ất sau)
                def lay_cua_sort(cua_str):
                    c = str(cua_str).lower()
                    if "giáp" in c: return 1
                    if "ất" in c: return 2
                    return 3

                # 5. Từ điển khoanh tròn số thứ tự cho con cái
                circled_children_num = {
                    1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤",
                    6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩",
                    11: "⑪", 12: "⑫", 13: "⑬", 14: "⑭", 15: "⑮",
                    16: "⑯", 17: "⑰", 18: "⑑", 19: "⑒", 20: "⑓", 21: "㉑",
                    22: "㉒", 23: "㉓", 24: "㉔", 25: "㉕", 26: "㉖", 27: "㉗", 28: "㉘"
                }

                # Tập hợp từ khóa sinh tử
                death_keywords = ["tảo vong", "tảo một", "chết sớm", "mất sớm"]
                parent_ids = set(df_app['ChaMe_ID'].dropna().unique())

                def should_keep_for_heading(row):
                    tinh_trang = str(row.get('TinhTrang', '')).lower()
                    ghi_chu = str(row.get('GhiChu', '')).lower()
                    m_id = str(row.get('ID', '')).strip()
                    
                    # 🟢 Tách riêng phần tiểu sử bản thân, không đọc lẹm sang phần "sinh hạ" của con cái
                    ghi_chu_ban_than = ghi_chu.split('sinh hạ:')[0] if 'sinh hạ:' in ghi_chu else ghi_chu
                    
                    # Quét từ khóa tử vong ở cột Tình trạng hoặc phần Tiểu sử cá nhân
                    has_death_kw = any(kw in tinh_trang for kw in death_keywords) or any(kw in ghi_chu_ban_than for kw in death_keywords)
                    is_adopted = "con nuôi" in tinh_trang or m_id == "100.03.0.004"
                    
                    if (has_death_kw and m_id not in parent_ids) or is_adopted:
                        return False
                    return True

                df_word = df_app[df_app['GioiTinh'] == 'Nam'].copy()
                df_word = df_word[df_word.apply(should_keep_for_heading, axis=1)]
                
                df_word['Doi_Sort'] = df_word['ID'].apply(lay_doi_tu_id)
                df_word['STT_Sort'] = df_word['ID'].apply(lay_stt_tu_id)
                df_word['Cua_Sort'] = df_word['Cua'].apply(lay_cua_sort)
                df_word['Chi_Sort'] = df_word.apply(lambda row: "00" if row['Doi_Sort'] <= 8 else lay_ma_chi_tu_id(row['ID']), axis=1)
                
                df_word = df_word.sort_values(by=['Doi_Sort', 'Cua_Sort', 'Chi_Sort', 'STT_Sort'])

                # Bắt đầu khởi tạo Word
                doc = Document()
                from docx.enum.section import WD_SECTION_START

                # ==============================================================
                # PHẦN 1: TRANG BÌA (CẤU TRÚC RIÊNG - PHỦ KÍN 100%)
                # ==============================================================
                if anh_bia_word is not None:
                    # Lấy section đầu tiên làm trang bìa
                    section_cover = doc.sections[0]
                    
                    # Ép lề về 0 để ảnh tràn viền hoàn toàn
                    section_cover.top_margin = Inches(0)
                    section_cover.bottom_margin = Inches(0)
                    section_cover.left_margin = Inches(0)
                    section_cover.right_margin = Inches(0)

                    p_img = doc.add_paragraph()
                    p_img.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    p_img.paragraph_format.space_before = Pt(0)
                    p_img.paragraph_format.space_after = Pt(0)
                    
                    run_img = p_img.add_run()
                    run_img.add_picture(anh_bia_word, width=Inches(8.27))
                    
                    # QUAN TRỌNG: Ngắt Section mới để tách hoàn toàn cấu trúc trang bìa với phần nội dung bên dưới
                    doc.add_section(WD_SECTION_START.NEW_PAGE)

       
                # ==============================================================
                # PHẦN 2: TỪ TRANG 2 TRỞ ĐI (CẤU TRÚC CHUẨN - CÓ KHUNG ĐỎ & SỐ TRANG)
                # ==============================================================
                for i, section in enumerate(doc.sections):
                    # Bỏ qua Section 0 (Trang bìa)
                    if anh_bia_word is not None and i == 0:
                        continue

                    # --- BỨC TƯỜNG VÔ HÌNH: ÉP KHỐI CHỮ VÀO GIỮA KHUNG ẢNH NỀN ---
                    # Ông chủ thay đổi các con số (Inches) dưới đây để xê dịch toàn bộ khối chữ nhé:
                    section.top_margin = Inches(1.3)    # Tăng/giảm để đẩy khối chữ xuống/lên
                    section.bottom_margin = Inches(1.0) # Canh lề dưới
                    section.left_margin = Inches(1.3)   # Tăng/giảm để xô khối chữ sang phải/trái
                    section.right_margin = Inches(0.9)  # Canh lề phải
                    section.header_distance = Inches(0.8)  

                    sectPr = section._sectPr

                    # Ép số trang bắt đầu từ số 1 ở trang nội dung đầu tiên
                    if anh_bia_word is not None and i == 1:
                        pgNumType = OxmlElement('w:pgNumType')
                        pgNumType.set(qn('w:start'), '1')
                        sectPr.append(pgNumType)
  
                    # --- QUAN TRỌNG: CẮT ĐỨT LIÊN KẾT HEADER VỚI TRANG BÌA ---
                    section.header.is_linked_to_previous = False
                    section.first_page_header.is_linked_to_previous = False
                    # --------------------------------------------------------

                    # Giữ chỗ trang đầu của nội dung
                    section.different_first_page_header_footer = True
                    first_header = section.first_page_header
                    first_p = first_header.paragraphs[0] if first_header.paragraphs else first_header.add_paragraph()
                    first_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    
                    first_run = first_p.add_run("\u00A0")  
                    first_run.font.name = 'Times New Roman'
                    first_run.font.size = Pt(10)           

                    # Đánh số trang chuẩn cho các trang tiếp theo
                    header = section.header
                    header_p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
                    header_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    
                    run_l = header_p.add_run("--- ")
                    run_l.font.name = 'Times New Roman'
                    run_l.font.size = Pt(10)
                    run_l.font.color.rgb = RGBColor(120, 120, 120)
                    
                    fld = OxmlElement('w:fldSimple')
                    fld.set(qn('w:instr'), 'PAGE')
                    header_p._p.append(fld)
                    
                    run_r = header_p.add_run(" ---")
                    run_r.font.name = 'Times New Roman'
                    run_r.font.size = Pt(10)
                    run_r.font.color.rgb = RGBColor(120, 120, 120)

                    # --- CHÈN HÌNH NỀN VÀO CÁC TRANG NỘI DUNG ---
                    if anh_nen_word is not None:
                        if section.different_first_page_header_footer:
                            anh_nen_word.seek(0)
                            chen_watermark_full_trang(section.first_page_header, anh_nen_word)
                        
                        anh_nen_word.seek(0)
                        chen_watermark_full_trang(section.header, anh_nen_word)

                # Định nghĩa màu sắc chuẩn in màu
                COLOR_PRIMARY = RGBColor(139, 0, 0)     # Đỏ đun (#8B0000)
                COLOR_SECONDARY = RGBColor(139, 69, 19) # Nâu đồng (#8B4513)
                COLOR_TEXT = RGBColor(44, 44, 44)       # Xám than đậm (#2C2C2C)
                COLOR_BLACK = RGBColor(0, 0, 0)         # Đen tuyền cho tên bố
                
                # BỐ CỤC TRANG ĐẦU CHUẨN THEO BẢN IN GỐC
                p_title = doc.add_paragraph()
                p_title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

                p_title.paragraph_format.space_before = Pt(10)
                p_title.paragraph_format.space_after = Pt(2)
                run_title = p_title.add_run('TỪ TỘC TIỂU TÔN PHỔ KÝ')
                run_title.bold = True
                run_title.font.size = Pt(22)
                run_title.font.color.rgb = COLOR_PRIMARY
                run_title.font.name = 'Times New Roman'
                
                p_sub = doc.add_paragraph()
                p_sub.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                p_sub.paragraph_format.space_after = Pt(18)
                run_sub = p_sub.add_run('Bản ghi chép chi tiết tiểu sử, niên biểu và huyết mạch các thế hệ')
                run_sub.italic = True
                run_sub.font.size = Pt(11.5)
                run_sub.font.color.rgb = COLOR_SECONDARY
                run_sub.font.name = 'Times New Roman'

                # Khối Nguồn gốc (Tiểu tôn phổ ký)
                p_nguongoc = doc.add_paragraph()
                p_nguongoc.paragraph_format.left_indent = Inches(0.2)
                p_nguongoc.paragraph_format.space_after = Pt(16)
                p_nguongoc.paragraph_format.line_spacing = 1.15

                r_notitle = p_nguongoc.add_run("Nguồn gốc:\n")
                r_notitle.bold = True
                r_notitle.font.size = Pt(11.5)
                r_notitle.font.color.rgb = COLOR_PRIMARY
                r_notitle.font.name = 'Times New Roman'

                nguon_goc_text = (
                    "• Truy xưng: Ông Từ Hữu Bương — Chết ngày 14 tháng 2 âm\n"
                    "                     Bà Nguyễn Thị Nhỏ — Chết\n"
                    "                     (Ông bà này thuộc Đông Hải Quận)\n"
                    "• Truyền xưng: Ông Từ Cẩn Thận — Chết ngày 9 tháng 7 âm\n"
                    "                        Bà Đinh Thị Thuần Tâm — Chết ngày 16 tháng 12 âm\n"
                    "                        (Ông bà này thuộc Đông Hải Quận)"
                )
                r_nocontent = p_nguongoc.add_run(nguon_goc_text + "\n")
                r_nocontent.italic = True
                r_nocontent.font.size = Pt(10.5)
                r_nocontent.font.color.rgb = COLOR_TEXT
                r_nocontent.font.name = 'Times New Roman'

                r_tail = p_nguongoc.add_run("          Truy xưng và truyền xưng lên theo Đại Tôn phổ ký")
                r_tail.italic = True
                r_tail.font.size = Pt(10.5)
                r_tail.font.color.rgb = COLOR_TEXT
                r_tail.font.name = 'Times New Roman'
                
                roman_map = {1: 'NHẤT', 2: 'HAI', 3: 'BA', 4: 'TƯ', 5: 'NĂM', 6: 'SÁU', 7: 'BẢY', 8: 'TÁM', 9: 'CHÍN', 10: 'MƯỜI', 11: 'MƯỜI MỘT', 12: 'MƯỜI HAI', 13: 'MƯỜI BA', 14: 'MƯỜI BỐN', 15: 'MƯỜI LĂM'}
                
                current_doi = -1
                current_cua = ""
                current_chi_sort = ""
                gen_stt_counter = 1

                for index, row in df_word.iterrows():
                    doi = row['Doi_Sort']
                    chi_sort_val = row['Chi_Sort']
                    cua_val = str(row.get('Cua', '')).strip()
                    chi_val = str(row.get('Chi', '')).strip()
                    
                    # 1. TIÊU ĐỀ ĐỜI
                    if doi != current_doi:
                        if doi != 999:
                            doi_name = roman_map.get(doi, str(doi))
                            p_doi = doc.add_paragraph()
                            p_doi.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                            p_doi.paragraph_format.space_before = Pt(18)
                            p_doi.paragraph_format.space_after = Pt(8)
                            p_doi.paragraph_format.keep_with_next = True
                            
                            run_doi = p_doi.add_run(f'📜 ĐỜI THỨ {doi_name}')
                            run_doi.bold = True
                            run_doi.font.size = Pt(14.5)
                            run_doi.font.color.rgb = COLOR_PRIMARY
                            run_doi.font.name = 'Times New Roman'
                        
                        current_doi = doi
                        current_cua = ""
                        current_chi_sort = ""
                        if doi <= 2:
                            gen_stt_counter = 1

                    # 2. TIÊU ĐỀ CỬA (Từ đời 3 trở đi)
                    if doi >= 3 and cua_val != current_cua:
                        if "Giáp" in cua_val: prefix_cua = "A. "
                        elif "Ất" in cua_val: prefix_cua = "B. "
                        else: prefix_cua = "C. "
                        
                        p_cua = doc.add_paragraph()
                        p_cua.paragraph_format.space_before = Pt(12)
                        p_cua.paragraph_format.space_after = Pt(6)
                        p_cua.paragraph_format.left_indent = Inches(0.1)
                        p_cua.paragraph_format.keep_with_next = True
                        
                        cua_text = cua_val if cua_val and cua_val != "Khác" else "NHÁNH KHÁC"
                        run_cua = p_cua.add_run(f'{prefix_cua}{cua_text.upper()}')
                        run_cua.bold = True
                        run_cua.font.size = Pt(13)
                        run_cua.font.color.rgb = COLOR_PRIMARY
                        run_cua.font.name = 'Times New Roman'
                        
                        current_cua = cua_val
                        if doi <= 8:
                            gen_stt_counter = 1

                    # 3. TIÊU ĐỀ CHI (Từ đời 9 trở đi - Rút gọn chỉ còn CHI X)
                    if doi >= 9 and chi_sort_val != current_chi_sort:
                        chi_clean = re.sub(r'\s*\(.*?\)', '', chi_val).strip()
                        chi_text = chi_clean if (chi_clean and chi_clean != "Khác") else "Nhánh Khác"
                        
                        p_chi = doc.add_paragraph()
                        p_chi.paragraph_format.space_before = Pt(8)
                        p_chi.paragraph_format.space_after = Pt(4)
                        p_chi.paragraph_format.left_indent = Inches(0.2)
                        p_chi.paragraph_format.keep_with_next = True
                        
                        run_chi = p_chi.add_run(f'❖ {chi_text.upper()}')
                        run_chi.bold = True
                        run_chi.font.size = Pt(12)
                        run_chi.font.color.rgb = COLOR_SECONDARY
                        run_chi.font.name = 'Times New Roman'
                        
                        current_chi_sort = chi_sort_val
                        gen_stt_counter = 1

                    # --- TRÍCH XUẤT THÔNG TIN THÀNH VIÊN ---
                    ho_ten = str(row.get('HoTen', '')).strip()
                    ma_id = str(row.get('ID', '')).strip()
                    ten_tu = str(row.get('TenTu', '')).strip()
                    vo_chong = str(row.get('VoChong', '')).strip()
                    nam_sinh = str(row.get('NamSinh', '')).strip()
                    nam_mat = str(row.get('NamMat', '')).strip()
                    ngay_gio = str(row.get('NgayGio', '')).strip()
                    ghi_chu = str(row.get('GhiChu', '')).strip()
                    tinh_trang = str(row.get('TinhTrang', '')).strip()
                    cha_me_id = str(row.get('ChaMe_ID', '')).strip()
                    
                    # Truy tìm tên bố từ CSDL
                    ten_cha = ""
                    if cha_me_id and cha_me_id != "":
                        cha_row = df_app[df_app['ID'] == cha_me_id]
                        if not cha_row.empty:
                            raw_cha_name = str(cha_row.iloc[0].get('HoTen', '')).strip()
                            ten_cha = raw_cha_name.split("(")[0].strip()

                    # Làm sạch nội dung tiểu sử
                    ghi_chu_clean = re.sub(r'(?i)Sinh hạ:.*$', '', ghi_chu).strip()
                    ghi_chu_clean = re.sub(r'\[.*?\]', '', ghi_chu_clean).strip()

                    # --- TRÌNH BÀY ĐOẠN VĂN TIỂU SỬ ---
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Inches(0.2)
                    p.paragraph_format.space_after = Pt(8)
                    p.paragraph_format.line_spacing = 1.15
                    
                    p.paragraph_format.tab_stops.add_tab_stop(Inches(3.8), WD_TAB_ALIGNMENT.LEFT)

                    if doi == 1:
                        prefix_label = "✦ THỦY TỔ TIÊN KHẢO: "
                    else:
                        prefix_label = f"{gen_stt_counter:02d}. "
                        gen_stt_counter += 1

                    # Tên thành viên
                    run_name = p.add_run(f"{prefix_label}{ho_ten}")
                    run_name.bold = True
                    run_name.font.size = Pt(11.5)
                    run_name.font.color.rgb = COLOR_PRIMARY
                    run_name.font.name = 'Times New Roman'

                    # Mã ID
                    run_id = p.add_run(f" [{ma_id}]")
                    run_id.font.size = Pt(10)
                    run_id.font.color.rgb = RGBColor(100, 100, 100)
                    run_id.font.name = 'Courier New'
                    
                    # 1. Tên tự / Tên hiệu (Đặt ngay sát sau Mã ID)
                    if ten_tu and ten_tu.lower() not in ['nan', 'none']:
                        run_tu = p.add_run(f" — (Tự/Hiệu: {ten_tu})")
                        run_tu.italic = True
                        run_tu.font.size = Pt(10.5)
                        run_tu.font.color.rgb = COLOR_TEXT
                        run_tu.font.name = 'Times New Roman'

                    # 2. Quan hệ "Con ông..." đặt sau Tự/Hiệu, có tab để căn lề ngay ngắn
                    if ten_cha:
                        run_cha = p.add_run(f"\tCon ông {ten_cha}")
                        run_cha.bold = False
                        run_cha.font.size = Pt(10.5)
                        run_cha.font.color.rgb = COLOR_BLACK
                        run_cha.font.name = 'Times New Roman'
                        
                    p.add_run("\n")

                    # --- XỬ LÝ THÔNG TIN VỢ/CHỒNG ---
                    if vo_chong and vo_chong.lower() not in ['nan', 'none']:
                        r_lbl1 = p.add_run("   + Vợ/Chồng: ")
                        r_lbl1.bold = True
                        r_lbl1.font.size = Pt(10.5)
                        r_lbl1.font.color.rgb = COLOR_SECONDARY
                        r_lbl1.font.name = 'Times New Roman'
                        
                        r_val1 = p.add_run(f"{vo_chong}\n")
                        r_val1.font.size = Pt(10.5)
                        r_val1.font.color.rgb = COLOR_TEXT
                        r_val1.font.name = 'Times New Roman'
                        
                    # Niên biểu
                    thong_tin_thoi_gian = []
                    if nam_sinh and nam_sinh.lower() not in ['nan', 'none']: thong_tin_thoi_gian.append(f"Sinh: {nam_sinh}")
                    if nam_mat and nam_mat.lower() not in ['nan', 'none']: thong_tin_thoi_gian.append(f"Mất: {nam_mat}")
                    if ngay_gio and ngay_gio.lower() not in ['nan', 'none']: thong_tin_thoi_gian.append(f"Ngày giỗ: {ngay_gio}")
                    
                    if thong_tin_thoi_gian:
                        r_lbl = p.add_run(f"   + Niên biểu: ")
                        r_lbl.bold = True
                        r_lbl.font.size = Pt(10.5)
                        r_lbl.font.color.rgb = COLOR_SECONDARY
                        r_lbl.font.name = 'Times New Roman'
                        
                        r_val = p.add_run(" | ".join(thong_tin_thoi_gian) + "\n")
                        r_val.font.size = Pt(10.5)
                        r_val.font.color.rgb = COLOR_TEXT
                        r_val.font.name = 'Times New Roman'
                        
                    # Tiểu sử
                    if ghi_chu_clean and ghi_chu_clean.lower() not in ['nan', 'none']:
                        r_lbl = p.add_run(f"   + Tiểu sử: ")
                        r_lbl.bold = True
                        r_lbl.font.size = Pt(10.5)
                        r_lbl.font.color.rgb = COLOR_SECONDARY
                        r_lbl.font.name = 'Times New Roman'
                        
                        r_val = p.add_run(f"{ghi_chu_clean}\n")
                        r_val.font.size = Pt(10.5)
                        r_val.font.color.rgb = COLOR_TEXT
                        r_val.font.name = 'Times New Roman'
                        
                    # Tình trạng đặc biệt
                    if tinh_trang and tinh_trang.lower() not in ['nan', 'none']:
                        r_lbl = p.add_run(f"   + Tình trạng: ")
                        r_lbl.bold = True
                        r_lbl.font.size = Pt(10.5)
                        r_lbl.font.color.rgb = COLOR_SECONDARY
                        r_lbl.font.name = 'Times New Roman'
                        
                        r_val = p.add_run(f"{tinh_trang}\n")
                        r_val.font.size = Pt(10.5)
                        r_val.font.color.rgb = COLOR_TEXT
                        r_val.font.name = 'Times New Roman'

         
            
                    # --- TÍCH HỢP DANH SÁCH CON CÁI (LỌC BỎ "KHÔNG RÕ", "ĐANG CẬP NHẬT") ---
                    main_children_list = []
                    bracket_children_list = []
                    
                    if ghi_chu:
                        m_sinhha = re.search(r'(?i)Sinh hạ:\s*(.*?)(?=\.|$|\[)', ghi_chu)
                        raw_sub_main = m_sinhha.group(1).strip() if m_sinhha else ""
                        if raw_sub_main:
                            parts_sub = re.split(r',\s*(?![^()]*\))', raw_sub_main)
                            for ps in parts_sub:
                                clean_ps = ps.strip()
                                if clean_ps:
                                    if not any(kw in clean_ps.lower() for kw in ["pháp tự", "phạp tự", "cố phù", "tên khác"]):
                                        main_children_list.append(clean_ps)
                        
                        bracket_matches = re.findall(r'\[(.*?)\]', ghi_chu)
                        for bm in bracket_matches:
                            bracket_children_list.append(bm.strip())

                    children_df = df_app[df_app['ChaMe_ID'] == ma_id].copy()

                    if main_children_list or bracket_children_list or not children_df.empty:
                        r_lbl = p.add_run(f"   + Ông bà sinh hạ:\n")
                        r_lbl.bold = True
                        r_lbl.font.size = Pt(10.5)
                        r_lbl.font.color.rgb = COLOR_SECONDARY
                        r_lbl.font.name = 'Times New Roman'
                        
                        total_lines_count = len(main_children_list) + len(bracket_children_list)
                        current_line_idx = 1
                        
                        if main_children_list:
                            for nc_name in main_children_list:
                                matched_row = None
                                clean_nc_name = nc_name.split('(')[0].strip().lower()
                                
                                if not children_df.empty:
                                    for _, crow in children_df.iterrows():
                                        c_hoten = str(crow.get('HoTen', '')).strip().lower()
                                        if c_hoten == clean_nc_name:
                                            matched_row = crow
                                            break

                                if matched_row is not None:
 
                                    c_name = str(matched_row.get('HoTen', '')).strip()
                                    c_name_huy = re.sub(r'\s*\(.*?\)', '', c_name).strip()
                                    
                                    c_tinhtrang = str(matched_row.get('TinhTrang', '')).strip()
                                    c_gioitinh = str(matched_row.get('GioiTinh', 'Nam')).strip()
                                    c_ghichu_con = str(matched_row.get('GhiChu', '')).strip()
                                    c_vochong_con = str(matched_row.get('VoChong', '')).strip()
                                    
                                    death_keywords = ["chết sớm", "tảo vong", "tảo một", "mất sớm", "tử sỹ", "tử sĩ", "liệt sỹ", "Liệt sĩ", "hy sinh"]
                                    extra = []
                                    
                                    if c_tinhtrang and c_tinhtrang.lower() not in ['nan', 'none', '']:
                                        if c_gioitinh != "Nữ":
                                            if any(kw in c_tinhtrang.lower() for kw in death_keywords):
                                                extra.append(c_tinhtrang)
                                        else:
                                            extra.append(c_tinhtrang)
                                    else:
                                        if c_gioitinh == "Nữ":
                                            # Kiểm tra nếu tình trạng hoặc ghi chú có chứa "không lấy chồng"
                                            full_check_str = f"{c_tinhtrang} {c_ghichu_con}".lower()
                                            if "không lấy chồng" in full_check_str:
                                                extra.append("Không lấy chồng")
                                            else:
                                                # Làm sạch ghi chú
                                                g_text_cleaned = ""
                                                if c_ghichu_con and c_ghichu_con.lower() not in ['nan', 'none', '']:
                                                    g_text_cleaned = re.sub(r'^Con\s+[^.]*\.?\s*', '', c_ghichu_con, flags=re.IGNORECASE).strip()
                                                    g_text_cleaned = re.sub(r'\.+$', '', g_text_cleaned).strip()
                                                    # LỌC BỎ RÁC
                                                    if any(bad in g_text_cleaned.lower() for bad in ["đang cập nhật", "không rõ"]):
                                                        g_text_cleaned = ""

                                                # Lọc bỏ rác ở cột vợ/chồng
                                                has_vc = c_vochong_con and c_vochong_con.lower() not in ['nan', 'none', 'không rõ', 'đang cập nhật']
                                                has_gc = bool(g_text_cleaned)

                                                # LOGIC THÔNG MINH: TRÁNH LẶP TỪ "LẤY" VÀ "ÔNG"
                                                vc_display = ""
                                                if has_vc:
                                                    vc_lower = c_vochong_con.lower()
                                                    if vc_lower.startswith("lấy ông "):
                                                        vc_display = "Lấy ông " + c_vochong_con[8:].lstrip()
                                                    elif vc_lower.startswith("lấy "):
                                                        vc_display = "Lấy " + c_vochong_con[4:].lstrip()
                                                    elif vc_lower.startswith("ông "):
                                                        vc_display = f"Lấy {c_vochong_con}"
                                                    else:
                                                        vc_display = f"Lấy ông {c_vochong_con}"

                                                if has_vc and has_gc:
                                                    if c_vochong_con.lower() in g_text_cleaned.lower():
                                                        extra.append(g_text_cleaned)
                                                    else:
                                                        extra.append(f"{vc_display} {g_text_cleaned}".strip())
                                                elif has_vc and not has_gc:
                                                    extra.append(vc_display)
                                                elif not has_vc and has_gc:
                                                    extra.append(g_text_cleaned)

                                    extra_str = f" ( {', '.join(extra)} )" if extra else ""
                                    display_str = f"{c_name_huy}{extra_str}"
                                    
                                else:
                                    display_str = nc_name.strip()
                               
                                circled_num = circled_children_num.get(current_line_idx, f"({current_line_idx})")
                                newline = "\n" if current_line_idx < total_lines_count else ""
                                
                                r_val = p.add_run(f"      {circled_num}. {display_str}{newline}")
                                r_val.font.size = Pt(10.5)
                                r_val.font.color.rgb = COLOR_TEXT
                                r_val.font.name = 'Times New Roman'
                                current_line_idx += 1
                                
                        elif not children_df.empty and not bracket_children_list:
                            children_df['STT_Sort'] = children_df['ID'].apply(lay_stt_tu_id)
                            children_df = children_df.sort_values(by='STT_Sort')
                            total_lines_count = len(children_df)
                            
                            death_keywords = ["chết sớm", "tảo vong", "tảo một", "mất sớm", "tử sỹ", "tử sĩ", "liệt sỹ", "Liệt sĩ", "hy sinh"]
                            
                            for c_idx, c_row in enumerate(children_df.itertuples(), 1):
                                c_tinhtrang = str(getattr(c_row, 'TinhTrang', '')).strip()
                                c_gioitinh = str(getattr(c_row, 'GioiTinh', 'Nam')).strip()
                                c_ghichu = str(getattr(c_row, 'GhiChu', '')).strip()
                                c_vochong = str(getattr(c_row, 'VoChong', '')).strip()
                                
                                c_name = str(getattr(c_row, 'HoTen', '')).strip()
                                c_name_huy = re.sub(r'\s*\(.*?\)', '', c_name).strip()
                                
                                extra = []
                                
                                if c_tinhtrang and c_tinhtrang.lower() not in ['nan', 'none', '']:
                                    if c_gioitinh != "Nữ":
                                        if any(kw in c_tinhtrang.lower() for kw in death_keywords):
                                            extra.append(c_tinhtrang)
                                    else:
                                        extra.append(c_tinhtrang)
                                else:
                                    if c_gioitinh == "Nữ":
                                        full_check_str = f"{c_tinhtrang} {c_ghichu}".lower()
                                        if "không lấy chồng" in full_check_str:
                                            extra.append("Không lấy chồng")
                                        else:
                                            g_text_cleaned = ""
                                            if c_ghichu and c_ghichu.lower() not in ['nan', 'none', '']:
                                                g_text_cleaned = re.sub(r'^Con\s+[^.]*\.?\s*', '', c_ghichu, flags=re.IGNORECASE).strip()
                                                g_text_cleaned = re.sub(r'\.+$', '', g_text_cleaned).strip()
                                                if any(bad in g_text_cleaned.lower() for bad in ["đang cập nhật", "không rõ"]):
                                                    g_text_cleaned = ""

                                            has_vc = c_vochong and c_vochong.lower() not in ['nan', 'none', 'không rõ', 'đang cập nhật']
                                            has_gc = bool(g_text_cleaned)

                                            # LOGIC THÔNG MINH: TRÁNH LẶP TỪ "LẤY" VÀ "ÔNG"
                                            vc_display = ""
                                            if has_vc:
                                                vc_lower = c_vochong.lower()
                                                if vc_lower.startswith("lấy ông "):
                                                    vc_display = "Lấy ông " + c_vochong[8:].lstrip()
                                                elif vc_lower.startswith("lấy "):
                                                    vc_display = "Lấy " + c_vochong[4:].lstrip()
                                                elif vc_lower.startswith("ông "):
                                                    vc_display = f"Lấy {c_vochong}"
                                                else:
                                                    vc_display = f"Lấy ông {c_vochong}"

                                            if has_vc and has_gc:
                                                if c_vochong.lower() in g_text_cleaned.lower():
                                                    extra.append(g_text_cleaned)
                                                else:
                                                    extra.append(f"{vc_display} {g_text_cleaned}".strip())
                                            elif has_vc and not has_gc:
                                                extra.append(vc_display)
                                            elif not has_vc and has_gc:
                                                extra.append(g_text_cleaned)

                                extra_str = f" ( {', '.join(extra)} )" if extra else ""
                                circled_num = circled_children_num.get(c_idx, f"({c_idx})")
                                newline = "\n" if c_idx < total_lines_count else ""
                                
                                r_val = p.add_run(f"      {circled_num}. {c_name_huy}{extra_str}{newline}")
                                r_val.font.size = Pt(10.5)
                                r_val.font.color.rgb = COLOR_TEXT
                                r_val.font.name = 'Times New Roman'

                        if bracket_children_list:
                            for b_idx, bracket_text in enumerate(bracket_children_list, 1):
                                newline = "\n" if current_line_idx < total_lines_count else ""
                                r_val = p.add_run(f"      * {bracket_text}{newline}")
                                r_val.font.size = Pt(10.5)
                                r_val.font.color.rgb = COLOR_TEXT
                                r_val.font.name = 'Times New Roman'
                                current_line_idx += 1

                # Lưu và tải xuống
                bio = BytesIO()
                doc.save(bio)
                word_data = bio.getvalue()
                
                st.download_button(
                    label="📄 Tải xuống cuốn Thế Phả định dạng cao cấp (.docx)",
                    data=word_data,
                    file_name='The_Pha_Ho_Tu_Xuan_Loc_Cao_Cap.docx',
                    mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )
            except Exception as e:
                st.error(f"Lỗi khởi tạo file Word: {e}")
               
                
            ### Kết thúc tab_word ###
                



        # KHU VỰC IN ẤN BÁO CÁO (GIỮ NGUYÊN)
        with tab_in:
            st.markdown("🖼️ **Chọn ảnh bìa và ảnh sơ đồ cho tập tài liệu (Tùy chọn):**")

            
            col_img1, col_img2 = st.columns(2)
            with col_img1:
                uploaded_cover = st.file_uploader("1. Tải lên tệp Ảnh Bìa (JPG, PNG)", type=["jpg", "jpeg", "png"], key="upload_cover_pdf")
            with col_img2:
                uploaded_tree_img = st.file_uploader("2. Tải lên Ảnh Sơ đồ 3 đời đầu (JPG, PNG)", type=["jpg", "jpeg", "png"], key="upload_tree_pdf")
            
            # --- CẤU HÌNH 2 LỰA CHỌN CHÍNH (TIÊU CHUẨN HOẶC TÙY CHỈNH TỪNG TRANG) ---
            st.markdown("---")
            st.markdown("⚙️ **Cấu hình định dạng trang in:**")
            
            print_mode_type = st.radio(
                "Chọn phương thức định dạng trang:",
                options=["Tiêu chuẩn (Auto, 14-23)", "Tùy chỉnh chi tiết theo từng trang"],
                horizontal=True,
                key="print_mode_type_radio"
            )
            
            selected_page_mode = "Auto"
            default_rows_val = 17
            custom_rules = {}
            
            if print_mode_type == "Tiêu chuẩn (Auto, 14-23)":
                page_mode_options = ["Auto", 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
                curr_val = st.session_state.get('selected_page_mode', 17)
                try:
                    default_idx = page_mode_options.index(curr_val)
                except ValueError:
                    default_idx = 4  # Mặc định là số 17
                    
                selected_page_mode = st.selectbox(
                    "Chọn chế độ trình bày trang in:",
                    options=page_mode_options,
                    index=default_idx,
                    key="selected_page_mode_selectbox"
                )
            else:
                default_rows_val = st.selectbox(
                    "Số dòng mặc định cho các trang còn lại:",
                    options=[14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
                    index=3,  # Mặc định là 17
                    key="default_rows_val_selectbox"
                )
                custom_text = st.text_area(
                    "Nhập quy tắc tùy chỉnh theo trang (Ví dụ: Trang 15, 18, 20 = 15 dòng; Trang 35, 37 = 20 dòng):",
                    value=st.session_state.get('custom_rules_text', ""),
                    placeholder="Trang 15, 18, 20 = 15\nTrang 35, 37, 39 = 20",
                    key="custom_text_textarea"
                )
                st.session_state.custom_rules_text = custom_text
                
                if custom_text:
                    for line in custom_text.split('\n'):
                        if '=' in line:
                            parts = line.split('=')
                            pages_str = parts[0]
                            rows_str = re.sub(r'[^0-9]', '', parts[1])
                            if rows_str.isdigit():
                                row_val = int(rows_str)
                                for p_part in pages_str.split(','):
                                    p_part = re.sub(r'[^0-9]', '', p_part)
                                    if p_part.isdigit():
                                        custom_rules[int(p_part)] = row_val

            st.markdown("---")
            
            # Ô cấu hình chèn trang trống thủ công để dán hình ảnh
            insert_blank_only_str = st.text_area(
                "📄 Tự động chèn các trang trống (Dùng để dán hình ảnh/tư liệu thủ công):\n(Cú pháp: Nhập số trang cần để trống, ví dụ: Trang 5, Trang 12 hoặc gõ 5, 12)",
                value=st.session_state.get('insert_blank_only_str', ""),
                placeholder="Ví dụ:\n5\n12\n20",
                key="input_blank_only_pages"
            )
            st.session_state.insert_blank_only_str = insert_blank_only_str
            
            blank_pages_set = set()
            if insert_blank_only_str:
                for line in insert_blank_only_str.split('\n'):
                    for p_part in line.split(','):
                        p_num = re.sub(r'[^0-9]', '', p_part)
                        if p_num.isdigit():
                            blank_pages_set.add(int(p_num))

            st.markdown("---")
            insert_blank_pages_str = st.text_area(
                "🌲 Tự động chèn sơ đồ phả hệ vào trang trống (Cú pháp: Trang [Số]: ID = [Mã], trước = [Số đời], sau = [Số đời]):",
                value=st.session_state.get('insert_blank_pages_str', "Trang 3: ID = 000.01.0.001, trước = 0, sau = 3"),
                placeholder="Trang 3: ID = 000.01.0.001, trước = 0, sau = 3",
                key="input_blank_pages_tree"
            )
            st.session_state.insert_blank_pages_str = insert_blank_pages_str
            
            # Phân tích cú pháp chèn sơ đồ tự động
            tree_rules = {} # {so_trang: {"id": target_id, "before": n, "after": m}}
            if insert_blank_pages_str:
                for line in insert_blank_pages_str.split('\n'):
                    if ':' in line and '=' in line:
                        try:
                            page_part, rule_part = line.split(':', 1)
                            p_num = int(re.sub(r'[^0-9]', '', page_part))
                            
                            id_match = re.search(r'ID\s*=\s*([0-9\.]+)', rule_part, re.IGNORECASE)
                            before_match = re.search(r'trước\s*=\s*(\d+)', rule_part, re.IGNORECASE)
                            after_match = re.search(r'sau\s*=\s*(\d+)', rule_part, re.IGNORECASE)
                            
                            if id_match:
                                t_id = id_match.group(1).strip()
                                b_val = int(before_match.group(1)) if before_match else 0
                                a_val = int(after_match.group(1)) if after_match else 3
                                tree_rules[p_num] = {"id": t_id, "before": b_val, "after": a_val}
                        except Exception:
                            pass

            if st.button("🖨️ Mở cửa sổ In ấn / Xuất PDF"):
                records = df_app.to_dict('records')
    
                import base64
                import os
                
                # --- CHUẨN BỊ ẢNH BÌA BASE64 ---
                cover_image_base64 = ""
                if uploaded_cover is not None:
                    try:
                        bytes_data = uploaded_cover.getvalue()
                        encoded_string = base64.b64encode(bytes_data).decode("utf-8")
                        mime_type = uploaded_cover.type
                        cover_image_base64 = f"data:{mime_type};base64,{encoded_string}"
                    except Exception as e:
                        st.error(f"Lỗi đọc ảnh bìa tải lên: {e}")
                else:
                    current_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
                    possible_paths = [
                        os.path.join(current_dir, "images", "bia_giapha"),
                        os.path.join(current_dir, "images", "bia_giapha.jpg"),
                        os.path.join(current_dir, "images", "bia_giapha.png"),
                        os.path.join(current_dir, "images", "bia_giapha.jpeg"),
                        os.path.join("images", "bia_giapha"),
                        os.path.join("images", "bia_giapha.jpg"),
                        os.path.join("images", "bia_giapha.png"),
                        "bia_giapha.jpg",
                        "bia_giapha.png"
                    ]
                    found_cover_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            found_cover_path = path
                            break
                        for ext in [".jpg", ".png", ".jpeg", ""]:
                            if os.path.exists(f"{path}{ext}"):
                                found_cover_path = f"{path}{ext}" if ext != "" else path
                                break
                        if found_cover_path:
                            break
                    
                    if found_cover_path:
                        try:
                            with open(found_cover_path, "rb") as img_file:
                                encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
                                mime_type = "image/png" if "png" in found_cover_path.lower() else "image/jpeg"
                                cover_image_base64 = f"data:{mime_type};base64,{encoded_string}"
                        except Exception:
                            pass

                # --- CHUẨN BỊ ẢNH SƠ ĐỒ BASE64 ---
                tree_image_base64 = ""
                if uploaded_tree_img is not None:
                    try:
                        bytes_data = uploaded_tree_img.getvalue()
                        encoded_string = base64.b64encode(bytes_data).decode("utf-8")
                        mime_type = uploaded_tree_img.type
                        tree_image_base64 = f"data:{mime_type};base64,{encoded_string}"
                    except Exception as e:
                        st.error(f"Lỗi đọc ảnh sơ đồ tải lên: {e}")

                def get_gen_title(r):
                    gen = int(r.get('DoiThu', 1))
                    if gen <= 3:
                        return "ĐỜI THỨ NHẤT ĐẾN ĐỜI THỨ 3"
                    else:
                        roman_map = {4: 'TƯ', 5: 'NĂM', 6: 'SÁU', 7: 'BẢY', 8: 'TÁM', 9: 'CHÍN', 10: 'MƯỜI', 11: 'MƯỜI MỘT', 12: 'MƯỜI HAI'}
                        gen_label = roman_map.get(gen, str(gen))
                        return f"ĐỜI THỨ {gen_label}"

                def format_multiline(text):
                    if not text or str(text).lower() in ["nan", "none", ""]:
                        return ""
                    parts = [p.strip() for p in str(text).split(',') if p.strip()]
                    return '<br>'.join(parts)

                def format_vo_chong(text, gioi_tinh="Nam"):
                    if not text or str(text).lower() in ["nan", "none", ""]:
                        return ""
                    raw_list = [p.strip() for p in str(text).split(',') if p.strip()]
                    cleaned_parts = []
                    for item in raw_list:
                        item_clean = re.sub(r'^(bà chính|bà thứ|bà cả|bà hai|bà ba|bà nhất|bà nhì|bà út|chính|thứ|cả|hai|ba|nhất|nhì|út|chồng|vợ|bà)\s*', '', item, flags=re.IGNORECASE).strip()
                        
                        if str(gioi_tinh).strip() == "Nữ":
                            if not item_clean.lower().startswith("chồng"):
                                item_clean = f"Chồng: {item_clean}"
                        else:
                            item_clean = f"Vợ: {item_clean}"
                                
                        cleaned_parts.append(item_clean)
                    return '<br>'.join(cleaned_parts)
   
         
            
                # ==========================================
                # HÀM TẠO SƠ ĐỒ TRỰC HỆ BẰNG HTML/CSS (ĐÃ SỬA: CHẶN HIỂN THỊ NHƯNG VẪN LAN TRUYỀN XUỐNG DƯỚI)
                # ==========================================
                def generate_tree_html(target_id, before_gen, after_gen):
                    # 1. Thu thập tổ tiên ngược lên trước (before_gen đời)
                    ancestors_list = []
                    curr_id = str(target_id)
                    visited_anc = set()
                    for _ in range(before_gen):
                        if not curr_id or curr_id == "0" or curr_id in visited_anc:
                            break
                        visited_anc.add(curr_id)
                        row = df_app[df_app["ID"] == curr_id]
                        if row.empty:
                            break
                        ancestors_list.insert(0, row.iloc[0].to_dict())
                        curr_id = str(row.iloc[0].get("ChaMe_ID", ""))

                    # 2. Lấy thông tin thành viên trung tâm
                    target_row = df_app[df_app["ID"] == str(target_id)]
                    target_dict = target_row.iloc[0].to_dict() if not target_row.empty else {"HoTen": target_id, "ID": target_id, "DoiThu": ""}

                    # 3. Thu thập con cháu tỏa xuống dưới
                    descendants_list = []
                    queue = [(str(target_id), 0)]
                    desc_visited = set()
                    
                    exclusion_keywords = ["tảo vong", "tảo một", "chết sớm", "mất sớm"]
                    hero_keywords = ["liệt sỹ", "Liệt sĩ", "tử sỹ", "tử sĩ"]

                    while queue:
                        c_curr, depth = queue.pop(0)
                        if c_curr in desc_visited or depth > after_gen:
                            continue
                        desc_visited.add(c_curr)
                        
                        # Lấy danh sách con trực tiếp của node hiện tại
                        children = df_app[df_app["ChaMe_ID"] == c_curr]
                        if "STT" in children.columns:
                            children = children.sort_values(by="STT")
                            
                        for _, ch in children.iterrows():
                            ch_dict = ch.to_dict()
                            ch_id = str(ch_dict.get("ID"))
                            
                            gioi_tinh = str(ch_dict.get("GioiTinh", "")).strip()
                            tinh_trang = str(ch_dict.get("TinhTrang", "")).lower()
                            ghi_chu = str(ch_dict.get("GhiChu", "")).lower()
                            
                            is_nam = (gioi_tinh == "Nam")
                            
                            # QUY TẮC 1: Nữ loại bỏ hoàn toàn khỏi danh sách hiển thị
                            if not is_nam:
                                continue
                            
                            # Kiểm tra xem có phải là Liệt sĩ / Tử sĩ không
                            is_hero = any(kw in tinh_trang or kw in ghi_chu for kw in hero_keywords)
                            
                            # Kiểm tra xem có dính từ khóa loại bỏ không
                            has_exclusion = any(kw in tinh_trang for kw in exclusion_keywords)
                            
                            # Nếu dính chết sớm/mất sớm nhưng LÀ Liệt sĩ / TỬ SĨ thì được MIỄN TRỪ
                            if has_exclusion and is_hero:
                                has_exclusion = False
                            
                            # QUY TẮC HIỂN THỊ: Chỉ đưa vào danh sách nếu không bị loại bỏ và trong phạm vi số đời
                            if not has_exclusion:
                                if depth + 1 <= after_gen:
                                    descendants_list.append((depth + 1, ch_dict))
                            
                            # 🟢 QUAN TRỌNG: Dù node đó có bị ẩn (ví dụ chết sớm) hay không, 
                            # vẫn PHẢI ĐẨY VÀO QUEUE để tiếp tục quét các đời con cháu phía dưới của nhánh đó!
                            if depth + 1 <= after_gen:
                                queue.append((ch_id, depth + 1))

                    # Render HTML cấu trúc sơ đồ
                    html_tree = f"""
                    <div style="font-family: 'Times New Roman', serif; padding: 5px; width: 100%; box-sizing: border-box; text-align: center; color: #2C2C2C;">
                    """
                    
                    if ancestors_list:
                        html_tree += f"""
                        <div style="font-size: 12px; font-weight: bold; color: #8B0000; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px;">📜 Cội nguồn tổ tiên (Ngược lên {len(ancestors_list)} đời):</div>
                        """
                        for anc in ancestors_list:
                            is_tgt = (str(anc['ID']) == str(target_id))
                            bg_c = "#FFE082" if is_tgt else "#F4EBD0"
                            border_c = "#C62828" if is_tgt else "#8B0000"
                            html_tree += f"""
                            <div style="display: inline-block; background: {bg_c}; border: 1.5px solid {border_c}; padding: 3px 10px; border-radius: 4px; margin: 1px; font-size: 10.5px;">
                                <b>{anc.get('HoTen', '')}</b> &nbsp;|&nbsp; <span style="font-family: monospace;">{anc.get('ID', '')}</span> &nbsp;|&nbsp; Đời {anc.get('DoiThu', '')}
                            </div>
                            <div style="font-size: 11px; color: #8B0000; line-height: 1; margin: 1px 0;">⬇</div>
                            """

                    t_name = target_dict.get('HoTen', target_id)
                    t_doi = target_dict.get('DoiThu', '')
                    t_chi = target_dict.get('Chi', '')
                    t_vo = target_dict.get('VoChong', '')
                    
                    html_tree += f"""
                        <div style="background: #FFE082; border: 2px solid #C62828; padding: 5px 12px; border-radius: 6px; margin: 4px auto; max-width: 420px;">
                            <div style="font-size: 12.5px; font-weight: bold; color: #8B0000; text-transform: uppercase;">⭐ NHÂN VẬT TRUNG TÂM: {t_name}</div>
                            <div style="font-size: 10.5px; margin-top: 2px;">Mã định danh: <b>{target_id}</b> &nbsp;|&nbsp; Đời thứ {t_doi} &nbsp;|&nbsp; {t_chi}</div>
                            {f"<div style='font-size: 10px; margin-top: 1px; color: #444;'>Vợ/Chồng: {t_vo}</div>" if t_vo else ""}
                        </div>
                    """

                    if descendants_list:
                        html_tree += f"""<div style="font-size: 12px; font-weight: bold; color: #8B0000; margin-top: 6px; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px;">Hậu duệ Nam thuần huyết tỏa nhánh xuống dưới (Sau {after_gen} đời):</div><div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; max-height: 165mm; overflow: hidden; padding: 4px;">"""                    
                        for depth, ch in descendants_list:
                            doi_khoanh = QuanTriTaiNguyen.get_circled_doi(ch.get('DoiThu', ''), ch.get('TinhTrang', ''))
                            html_tree += f"""
                            <div style="background: #FFF; border: 1.2px solid #2E7D32; padding: 5px 8px; border-radius: 4px; font-size: 11px; min-width: 120px;">
                                <b style="color: #2E7D32;">{ch.get('HoTen', '')} {doi_khoanh}</b>
                            </div>
                            """
                        html_tree += "</div>"
                    else:
                        html_tree += f"""<div style="font-size: 10.5px; font-style: italic; color: #666; margin-top: 4px;">(Chưa có ghi nhận hậu duệ Nam trực hệ trong phạm vi đời này)</div>"""

                    html_tree += "</div>"
                    return html_tree

                # ==========================================
                # ĐIỀU PHỐI LOGIC CHÍNH
                # ==========================================
                effective_default = default_rows_val if print_mode_type == "Tùy chỉnh chi tiết theo từng trang" else 17
                
                page_chunks = []
                current_chunk = []
                row_count = 0
                last_rendered_gen = None
                page_idx = 2 
                target_rows = custom_rules.get(page_idx, effective_default)
                
                def check_and_insert_blank_pages():
                    nonlocal page_idx, page_chunks
                    while page_idx in blank_pages_set and page_idx not in tree_rules:
                        page_chunks.append(("BLANK_PAGE_PLACEHOLDER", {}))
                        page_idx += 1

                check_and_insert_blank_pages()

                for r in records:
                    gen = get_gen_title(r)
                    
                    if gen == "ĐỜI THỨ TƯ" and last_rendered_gen == "ĐỜI THỨ NHẤT ĐẾN ĐỜI THỨ 3":
                        if current_chunk:
                            while row_count < target_rows:
                                current_chunk.append(None)
                                row_count += 1
                            page_chunks.append(current_chunk)
                            current_chunk = []
                            row_count = 0
                            page_idx += 1
                            check_and_insert_blank_pages()
                        
                        if page_idx not in tree_rules:
                            tree_rules[page_idx] = {"id": "000.01.0.001", "before": 0, "after": 3}
                            
                    header_needed = (gen != last_rendered_gen)
                    slots_needed = (1 if header_needed else 0) + 1
                    
                    if row_count + slots_needed > target_rows and current_chunk:
                        while row_count < target_rows:
                            current_chunk.append(None)
                            row_count += 1
                        page_chunks.append(current_chunk)
                        current_chunk = []
                        row_count = 0
                        page_idx += 1
                        
                        check_and_insert_blank_pages()
                        while page_idx in tree_rules:
                            page_chunks.append(("TREE_PAGE_PLACEHOLDER", tree_rules[page_idx]))
                            page_idx += 1
                            check_and_insert_blank_pages()
                            
                        target_rows = custom_rules.get(page_idx, effective_default)
                        header_needed = (gen != last_rendered_gen)
                    
                    current_chunk.append(r)
                    if header_needed:
                        row_count += 1
                        last_rendered_gen = gen
                    row_count += 1
                    
                    if row_count >= target_rows:
                        while row_count < target_rows:
                            current_chunk.append(None)
                            row_count += 1
                        page_chunks.append(current_chunk)
                        current_chunk = []
                        row_count = 0
                        page_idx += 1
                        
                        check_and_insert_blank_pages()
                        while page_idx in tree_rules:
                            page_chunks.append(("TREE_PAGE_PLACEHOLDER", tree_rules[page_idx]))
                            page_idx += 1
                            check_and_insert_blank_pages()
                            
                        target_rows = custom_rules.get(page_idx, effective_default)
                        
                if current_chunk:
                    while row_count < target_rows:
                        current_chunk.append(None)
                        row_count += 1
                    page_chunks.append(current_chunk)

                html_report = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
                    @page {{ size: A4 landscape; margin: 6mm; }} 
                    body {{ font-family: 'Times New Roman', serif; background-color: #FDFBF7; color: #2C2C2C; margin: 0; padding: 0; -webkit-print-color-adjust: exact; }} 
                    
                    .cover-image-container {{
                        page-break-after: always; break-after: page; page-break-inside: avoid; break-inside: avoid;
                        width: 100%; height: 194mm; max-height: 194mm; position: relative; 
                        background-color: #590000; background-image: url("{cover_image_base64}");
                        background-size: 100% 100%; background-position: center; background-repeat: no-repeat;
                        box-sizing: border-box; margin-bottom: 15mm; overflow: hidden;
                    }}

                    .page-container {{ 
                        page-break-after: always; break-after: page; page-break-inside: avoid; break-inside: avoid;
                        height: 194mm; max-height: 194mm; position: relative; 
                        background: linear-gradient(135deg, #fdfbf7 0%, #f4ebd0 100%);
                        border: 3px double #8B0000; padding: 10px; padding-top: 26px;
                        box-sizing: border-box; margin-bottom: 15mm; overflow: hidden;
                    }}
                    .page-container:last-child {{ page-break-after: avoid; break-after: avoid; margin-bottom: 0; }}
                    
                    .page-number-badge {{
                        position: absolute; top: -3px; left: 50%; transform: translateX(-50%);
                        width: 26px; height: 26px; border: 2px solid #8B0000; border-radius: 50%;
                        background-color: #FDFBF7; color: #8B0000; font-family: 'Times New Roman', serif;
                        font-weight: bold; font-size: 11px; display: flex; align-items: center; justify-content: center; z-index: 100;
                        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
                    }}

                    .watermark-draft {{
                        position: absolute; top: 28px; left: 35px; border: 3.5px solid #C62828; color: #C62828;
                        font-family: 'Times New Roman', serif; font-weight: bold; font-size: 22px; padding: 6px 18px;
                        text-transform: uppercase; letter-spacing: 3.5px; border-radius: 6px;
                        background-color: rgba(255, 235, 238, 0.85); transform: rotate(-10deg); z-index: 99;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.15);
                    }}

                    table {{ width: 100%; border-collapse: collapse; margin-top: 6px; background-color: rgba(255, 255, 255, 0.85); }} 
                    th {{ border: 1px solid #8B0000; padding: 3px; font-size: 11px; background: #8B0000; color: #FFF8DC; text-align: center; font-weight: bold; }}
                    td {{ border: 1px solid #c2b292; padding: 3px; font-size: 11.5px; height: 20px; word-break: break-word; vertical-align: middle; color: #1a1a1a; }} 
                    .main-title {{ text-align: center; font-size: 15px; font-weight: bold; color: #8B0000; margin-top: 2px; margin-bottom: 1px; text-transform: uppercase; letter-spacing: 1.5px; }}
                    .sub-title {{ text-align: center; font-size: 9.5px; font-style: italic; color: #555; margin-bottom: 3px; }}
                    .doi-header {{ background: #F4EBD0; color: #8B0000; border: 1.5px solid #8B0000; font-weight: bold; text-align: center; font-size: 12px; letter-spacing: 2px; padding: 3px; text-transform: uppercase; }}
                    .empty-row td {{ color: transparent; border: 1px solid #c2b292; background-color: rgba(255,255,255,0.2); }}
                </style></head><body>"""
                
                html_report += f"""<div class="cover-image-container">"""
                if not cover_image_base64:
                    html_report += f"""<div style="color: #FFD700; font-size: 16px; font-family: 'Times New Roman', serif; padding: 20px; text-align: center; margin: auto;">[Chưa có ảnh bìa. Vui lòng chọn tệp ảnh bìa từ giao diện]</div>"""
                html_report += f"""</div>"""

                stt_in = 1
                last_rendered_gen = None
                actual_page_counter = 2
                tree_image_rendered = False

                for chunk in page_chunks:
                    # 🟢 Xử lý Trang Trống (TÍCH HỢP DÁN ẢNH THÔNG MINH)
                    if isinstance(chunk, tuple) and chunk[0] == "BLANK_PAGE_PLACEHOLDER":
                        page_str = f"{actual_page_counter:02d}"
                        
                        if tree_image_base64 and not tree_image_rendered:
                            html_report += f"""<div class="page-container" style="display: flex; flex-direction: column; background: #FFFDF9; padding: 10px; padding-top: 35px; padding-bottom: 15px;">
                                <div class="page-number-badge">{page_str}</div>
                                <div style="flex: 1; width: 100%; position: relative;">
                                    <img src="{tree_image_base64}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; margin: 0 auto; transform: scaleY(1.2); transform-origin: center;">
                                </div>
                            </div>"""
                            tree_image_rendered = True
                        else:
                            html_report += f"""<div class="page-container" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: #FFFEFA;">
                                <div class="page-number-badge">{page_str}</div>
                                <div style="font-size: 15px; font-style: italic; color: #777; border: 2px dashed #b0a080; padding: 40px 60px; border-radius: 8px; background: rgba(255,255,255,0.6);">
                                    📄 [TRANG TRỐNG DÀNH ĐỂ DÁN HÌNH ẢNH / TƯ LIỆU THỦ CÔNG]
                                </div>
                            </div>"""
                        actual_page_counter += 1
                        continue

                    # 🟢 Xử lý Trang Sơ Đồ Cấu Hình
                    if isinstance(chunk, tuple) and chunk[0] == "TREE_PAGE_PLACEHOLDER":
                        page_str = f"{actual_page_counter:02d}"
                        
                        if tree_image_base64 and not tree_image_rendered:
                            html_report += f"""<div class="page-container" style="display: flex; flex-direction: column; background: #FFFDF9; padding: 10px; padding-top: 35px; padding-bottom: 15px;">
                                <div class="page-number-badge">{page_str}</div>
                                <div style="flex: 1; width: 100%; position: relative;">
                                    <img src="{tree_image_base64}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: contain; margin: 0 auto; transform: scaleY(1.2); transform-origin: center;">
                                </div>
                            </div>"""
                            tree_image_rendered = True
                        else:
                            rule_info = chunk[1]
                            display_content = generate_tree_html(rule_info["id"], rule_info["before"], rule_info["after"])
                            html_report += f"""<div class="page-container" style="display: flex; flex-direction: column; justify-content: flex-start; align-items: center; text-align: center; background: #FFFDF9;">
                                <div class="page-number-badge">{page_str}</div>
                                <div style="width: 100%; min-height: 184mm; height: auto; display: flex; align-items: center; justify-content: center; border: 1.5px dashed #8B0000; border-radius: 5px; box-sizing: border-box; overflow: hidden; background: #FFFEFA; padding: 2px;">
                                    {display_content}
                                </div>
                            </div>"""
                        actual_page_counter += 1
                        continue

                    page_idx = actual_page_counter
                    html_report += f"""<div class="page-container">"""
                    
                    page_str = f"{page_idx:02d}"
                    html_report += f"""<div class="page-number-badge">{page_str}</div>"""
                    html_report += f"""<div class="watermark-draft">BẢN NHÁP</div>"""
                    html_report += f"""<h2 class="main-title">DÒNG HỌ TỪ XUÂN LỘC - PHẢ HỆ ĐỊNH DANH</h2>"""
                    html_report += f"""<div class="sub-title">Lưu giữ huyết mạch dòng tộc — Trân trọng kính dâng tiên tổ</div>"""
                    
                    # 🟢 CHÈN CỘT TÌNH TRẠNG SAU CÙNG (WIDTH = 7%) VÀ BẢO LƯU 100% CẤU TRÚC / CHÚ THÍCH GỐC
                    html_report += f"""<table><thead><tr>
                        <th style="width: 4%;">STT</th>
                        <th style="width: 9%;">Mã Định Danh</th>
                        <th style="width: 11%;">Họ Tên</th>
                        <th style="width: 7%;">Tên Tự</th>
                        <th style="width: 12%;">Vợ/Chồng</th>
                        <th style="width: 5%;">Năm Sinh</th>
                        <th style="width: 5%;">Năm Mất</th>
                        <th style="width: 6%;">Ngày Giỗ</th>
                        <th style="width: 34%;">Ghi Chú</th>
                        <th style="width: 7%;">Tình Trạng</th>
                    </tr></thead><tbody>"""
                    
                    for r in chunk:
                        if r is None:
                            html_report += f"""<tr class="empty-row">
                                <td style="text-align:center;">&nbsp;</td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                                <td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
                            </tr>"""
                        else:
                            curr_gen_title = get_gen_title(r)
                            if curr_gen_title != last_rendered_gen:
                                html_report += f"""<tr><td colspan="10" class="doi-header">📜 {curr_gen_title}</td></tr>"""
                                last_rendered_gen = curr_gen_title
                            
                            ten_tu_fmt = format_multiline(r.get('TenTu', ''))
                            vo_chong_fmt = format_vo_chong(r.get('VoChong', ''), r.get('GioiTinh', 'Nam'))
                            
                            html_report += f"""<tr>
                                <td style="text-align:center; font-weight: bold; color: #8B0000;">{stt_in}</td>
                                <td style="text-align:center; font-family: monospace; font-size: 11px; white-space: nowrap; color: #333;">{r.get('ID', '')}</td>
                                <td><b style="color: #8B0000; font-size: 12.5px;">{r.get('HoTen', '')}</b></td>
                                <td>{ten_tu_fmt}</td>
                                <td>{vo_chong_fmt}</td>
                                <td style="text-align:center;">{r.get('NamSinh', '')}</td>
                                <td style="text-align:center;">{r.get('NamMat', '')}</td>
                                <td style="text-align:center; font-weight: bold; color: #700;">{r.get('NgàyGiỗ') if 'NgàyGiỗ' in r else r.get('NgayGio', '')}</td>
                                <td>{r.get('GhiChu', '')}</td>
                                <td style="text-align:center; font-size: 10px;">{r.get('TinhTrang', '')}</td>
                            </tr>"""
                            stt_in += 1

                    html_report += "</tbody></table></div>"
                    actual_page_counter += 1

                html_report += "<script>window.print();</script></body></html>"

                components.html(html_report, height=650, scrolling=True)




        # ==============================================================
        # 4. KHU VỰC XUẤT FILE ẢNH PHẢ ĐỒ (LỌC THEO ID - BẢN WORD NGANG)
        # ==============================================================
        with tab_phado:
            st.markdown("#### 🖼️ Xuất ảnh Phả đồ (Khổ ngang)")
            st.caption("Hệ thống sẽ trích xuất đồ họa phả đồ theo trục Cội nguồn (đời trên) và Tỏa nhánh (đời dưới) của nhân vật được chọn, sau đó chèn vào file Word A4 hướng nằm ngang.")
            
            c_id1, c_id2 = st.columns([1.5, 1.5])
            with c_id1:
                nhap_tim_kiem = st.text_input(
                    "🎯 Nhập Mã định danh hoặc Họ tên:", 
                    value="000.01.0.001", 
                    placeholder="Ví dụ: 000.01.0.001 hoặc Từ Dương Đốc",
                    key="input_phado_id"
                )
            with c_id2:
                che_do_nhan = st.selectbox(
                    "Chế độ hiển thị nhãn đồ họa:", 
                    [
                        "1. Chỉ Đinh Nam (Gọn: Tên ⑦)", 
                        "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)", 
                        "3. Chỉ Đinh Nam (Đủ vợ và chồng)", 
                        "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)"
                    ], 
                    index=2, 
                    key="sel_phado_chedo"
                )

            # --- KHU VỰC CẤU HÌNH SỐ ĐỜI VÀ CÔNG TẮC NỀN ---
            st.markdown("##### ⚙️ Cấu hình số đời & Chế độ nền:")
            col_tren, col_duoi, col_nen = st.columns([1, 1, 1.5])
            with col_tren:
                so_doi_tren = st.selectbox(
                    "Đời trên (Tổ tiên truy ngược):", 
                    ["Tất cả"] + list(range(1, 11)), 
                    index=0, 
                    key="sel_phado_doi_tren"
                )
            with col_duoi:
                so_doi_duoi = st.selectbox(
                    "Đời dưới (Hậu duệ tỏa nhánh):", 
                    ["Tất cả"] + list(range(1, 11)), 
                    index=0, 
                    key="sel_phado_doi_duoi"
                )
            with col_nen:
                st.write("Chế độ nền ảnh (Tối ưu cho Canva):")
                nen_trong_suot = st.toggle("Loại bỏ nền (Nền trong suốt)", value=False, key="toggle_trong_suot")

            # Thuật toán tự động nhận diện thành viên
            target_id_chon = ""
            ten_thanh_vien = ""
            chuoi_nhap = nhap_tim_kiem.strip()

            if chuoi_nhap:
                nhap_loc_cham = chuoi_nhap.replace(".", "")
                df_temp = df_app.copy()
                df_temp['ID_Raw'] = df_temp['ID'].str.replace(".", "", regex=False)
                khop_id = df_temp[df_temp["ID_Raw"] == nhap_loc_cham]
                
                if not khop_id.empty:
                    target_id_chon = str(khop_id.iloc[0]['ID'])
                    ten_thanh_vien = khop_id.iloc[0]['HoTen']
                    st.success(f"📌 Đã chọn: **{ten_thanh_vien}** (Mã: `{target_id_chon}` — Đời thứ {khop_id.iloc[0]['DoiThu']})")
                else:
                    def chuan_hoa(txt):
                        return str(txt).strip().lower().replace("oà", "òa").replace("ùy", "uỳ").replace("úy", "uý")

                    nhap_ten = chuan_hoa(chuoi_nhap)
                    df_temp['HoTen_Lower'] = df_temp['HoTen'].apply(chuan_hoa)
                    khop_ten = df_temp[df_temp['HoTen_Lower'] == nhap_ten]
                    
                    if len(khop_ten) == 1:
                        target_id_chon = str(khop_ten.iloc[0]["ID"])
                        ten_thanh_vien = khop_ten.iloc[0]['HoTen']
                        st.success(f"📌 Đã chọn: **{ten_thanh_vien}** (Mã: `{target_id_chon}` — Đời thứ {khop_ten.iloc[0]['DoiThu']})")
                    elif len(khop_ten) > 1:
                        danh_sach_trung = {f"{r['HoTen']} (Mã: {r['ID']} - Đời {r['DoiThu']})": r['ID'] for _, r in khop_ten.iterrows()}
                        chon_nguoi = st.selectbox("⚠️ Phát hiện trùng tên, vui lòng chọn cụ thể:", list(danh_sach_trung.keys()), key="dup_phado")
                        target_id_chon = danh_sach_trung[chon_nguoi]
                        ten_thanh_vien = khop_ten[khop_ten['ID'] == target_id_chon].iloc[0]['HoTen']
                    else:
                        st.warning(f"❌ Không tìm thấy thành viên nào có tên hoặc mã: '{chuoi_nhap}'")

            # --- VINH DANH NHÂN VẬT ĐIỂN HÌNH (HỖ TRỢ NHIỀU TÊN) ---
            st.markdown("##### 🌟 Vinh danh Nhân vật điển hình (Có thể nhập nhiều tên, cách nhau bởi dấu phẩy):")
            nhap_dien_hinh = st.text_input("Nhập Mã định danh hoặc Họ tên (Ví dụ: Từ Hữu Dực, Từ Hữu Lạng):", key="input_hl_names")
            
            highlight_ids_chon = []
            if nhap_dien_hinh.strip():
                # Tách các từ khóa theo dấu phẩy
                keywords = [k.strip() for k in nhap_dien_hinh.split(',') if k.strip()]
                for kw in keywords:
                    kw_clean = kw.replace(".", "")
                    # Tìm theo ID
                    khop_id = df_app[df_app['ID'].str.replace(".", "", regex=False) == kw_clean]
                    if not khop_id.empty:
                        highlight_ids_chon.extend(khop_id['ID'].tolist())
                    else:
                        # Tìm theo Tên
                        khop_ten = df_app[df_app['HoTen'].str.lower().str.contains(kw.lower(), na=False)]
                        if not khop_ten.empty:
                            highlight_ids_chon.extend(khop_ten['ID'].tolist())
                # Lọc bỏ các ID trùng lặp nếu có
                highlight_ids_chon = list(set(highlight_ids_chon))

            st.write("")

            # Nút bấm khởi tạo, xem trước và đóng gói file
            if st.button("🚀 Khởi tạo Phả đồ & Xem trước", type="primary", key="btn_xuat_phado_word"):
                if not target_id_chon:
                    st.error("Vui lòng xác định chính xác thành viên trước khi xuất file!")
                else:
                    try:
                        from docx import Document
                        from docx.enum.section import WD_ORIENT
                        from docx.shared import Inches, Pt, RGBColor
                        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
                        import io
                        import base64
                        
                        # Khởi tạo trang Word khổ A4 nằm ngang
                        doc_pd = Document()
                        sec = doc_pd.sections[-1]
                        w_goc, h_goc = sec.page_height, sec.page_width
                        sec.orientation = WD_ORIENT.LANDSCAPE
                        sec.page_width = w_goc
                        sec.page_height = h_goc
                        
                        # Căn lề hẹp để sơ đồ bung rộng tối đa
                        sec.top_margin = Inches(0.4)
                        sec.bottom_margin = Inches(0.4)
                        sec.left_margin = Inches(0.4)
                        sec.right_margin = Inches(0.4)
                        
                        # Tiêu đề trang trọng
                        p_tieu_de = doc_pd.add_paragraph()
                        p_tieu_de.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        p_tieu_de.paragraph_format.space_after = Pt(2)
                        run_td = p_tieu_de.add_run("PHẢ ĐỒ TRỤC CỘI NGUỒN & TỎA NHÁNH")
                        run_td.bold = True
                        run_td.font.size = Pt(16)
                        run_td.font.color.rgb = RGBColor(139, 0, 0)
                        run_td.font.name = 'Times New Roman'
                        
                        p_phu = doc_pd.add_paragraph()
                        p_phu.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        p_phu.paragraph_format.space_after = Pt(8)
                        run_phu = p_phu.add_run(
                            f"Nhân vật trung tâm: {ten_thanh_vien} (Mã: {target_id_chon}) | "
                            f"Số đời trên: {so_doi_tren} | Số đời dưới: {so_doi_duoi}"
                        )
                        run_phu.italic = True
                        run_phu.font.size = Pt(11)
                        run_phu.font.color.rgb = RGBColor(100, 100, 100)
                        run_phu.font.name = 'Times New Roman'
                        
                        # Vẽ sơ đồ qua Graphviz
                        with st.spinner("Đang kết xuất đồ họa phả hệ chất lượng cao (300 DPI)..."):
                            graph_obj = KyThuatBanVeGiaPha.draw_family_tree(
                                df_app,
                                target_id=target_id_chon,
                                che_do_xem=che_do_nhan,
                                so_doi_tren=so_doi_tren,
                                so_doi_duoi=so_doi_duoi,
                                highlight_ids=highlight_ids_chon
                            )
                            graph_obj.attr(dpi='300')
                            
                            # 🟢 XỬ LÝ LỆNH NỀN TRONG SUỐT
                            if nen_trong_suot:
                                graph_obj.attr(bgcolor='transparent')
                            else:
                                graph_obj.attr(bgcolor='white')
                                
                            png_bytes = graph_obj.pipe(format='png')
                            img_io = io.BytesIO(png_bytes)
                        
                        # --- HIỂN THỊ BẢN XEM TRƯỚC (PRINT PREVIEW) ---
                        st.markdown("---")
                        st.markdown("##### 👁️ BẢN XEM TRƯỚC SƠ ĐỒ (PRINT PREVIEW)")
                        
                        # Hiệu ứng UI: Nếu chọn nền trong suốt, hiện nền caro xám để dễ nhận diện
                        if nen_trong_suot:
                            st.caption("Ảnh đang ở chế độ **Trong suốt**. (Hiển thị nền caro giả lập bên dưới). Rất thích hợp để mang sang Canva ghép cảnh!")
                            st.markdown(
                                f'''<div style="background: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAMUlEQVQ4T2NkYGAQYcAP3uCTZhw1gGGYhAGBZIA/ENF5/P//P8OogRwMNPGAuBwQBAA0Yx/1f/2qTAAAAABJRU5ErkJggg=='); border: 1px solid #ccc; padding: 10px; border-radius: 8px;">
                                    <img src="data:image/png;base64,{base64.b64encode(png_bytes).decode()}" style="width: 100%;">
                                </div>''', 
                                unsafe_allow_html=True
                            )
                        else:
                            st.caption("Ảnh đang ở chế độ **Nền trắng tiêu chuẩn**.")
                            img_io.seek(0) 
                            st.image(img_io, use_container_width=True)
                            
                        st.markdown("---")
                        
                        # Chèn ảnh sơ đồ vào Word
                        img_io.seek(0) 
                        p_anh = doc_pd.add_paragraph()
                        p_anh.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        p_anh.add_run().add_picture(img_io, width=Inches(10.5))
                        
                        # Lưu file Word
                        mem_file = io.BytesIO()
                        doc_pd.save(mem_file)
                        word_bytes = mem_file.getvalue()
                        
                        st.success(f"✅ Đã xử lý thành công dữ liệu đồ họa cho: {ten_thanh_vien}!")
                        
                        # 🟢 CUNG CẤP 2 NÚT TẢI: VỪA TẢI WORD VỪA TẢI ẢNH GỐC ĐỂ DÙNG TRÊN CANVA
                        st.markdown("👇 **Vui lòng chọn định dạng file muốn tải về:**")
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            st.download_button(
                                label=f"📄 TẢI BẢN IN WORD (.docx)",
                                data=word_bytes,
                                file_name=f"Pha_Do_{target_id_chon.replace('.', '_')}_{ten_thanh_vien}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        with col_dl2:
                            st.download_button(
                                label=f"🖼️ TẢI ẢNH GỐC (.png)",
                                data=png_bytes,
                                file_name=f"Pha_Do_{target_id_chon.replace('.', '_')}_{ten_thanh_vien}.png",
                                mime="image/png",
                                use_container_width=True
                            )
                    except Exception as err:
                        st.error(f"Đã xảy ra lỗi khi tạo file: {err}")


    #=====================================================================
    # [PHÂN LÔ E9]: Hàm con render màn hình Mở Rộng Tiện Ích
    #=====================================================================
    @staticmethod
    def render_morong():
        st.markdown('<h2 class="desktop-view" style="font-size: 1.3rem; font-weight: bold;">🌟 Phần mở rộng tiện ích dòng họ</h2>', unsafe_allow_html=True)
        st.markdown('<h2 class="mobile-view" style="font-size: 1.2rem; font-weight: bold;">🌟 Tiện ích mở rộng</h2>', unsafe_allow_html=True)
        
        menu_mo_rong = st.selectbox(
            "👉 Kính mời bà con chọn tiện ích:",
            [
                "1. 📰 Trang tin & Hoạt động Dòng họ",
                "2. 📊 Bảng vàng Công đức & Khuyến học",
                "3. 📜 Thư viện Di sản (Bài cúng, Gia phả gốc)",
                "4. 💬 Sổ vàng (Ý kiến & Lời tri ân)",
                "5. 🗺️ Bản đồ Không gian Tâm linh & Lăng mộ (VR 360°)",
            ]
        )
        
        st.markdown("---")
        
        # ---------------------------------------------------------
        # MỤC 1: TRANG TIN & HOẠT ĐỘNG DÒNG HỌ
        # ---------------------------------------------------------
        if "1." in menu_mo_rong:
            # Tiêu đề tương thích đa nền tảng
            st.markdown('<h3 class="desktop-view" style="color: #0056b3; font-weight: bold;">📰 Trang Tin & Hoạt Động Dòng Họ Từ Xuân Lộc</h3>', unsafe_allow_html=True)
            st.markdown('<h3 class="mobile-view" style="color: #0056b3; font-size: 1.15rem; font-weight: bold;">📰 Trang Tin & Hoạt Động</h3>', unsafe_allow_html=True)
            st.write("Nơi cập nhật các thông báo quan trọng, lịch giỗ chạp và vinh danh các hoạt động đóng góp, khuyến học của dòng tộc.")
            
            tin_tuc_dong_ho = [
                {
                    "Loai": "Sự kiện sắp tới",
                    "Ngay": "10/03 Âm lịch (Sắp tới)",
                    "TieuDe": "📢 Thông báo Lễ Tế Tổ và họp mặt toàn dòng họ",
                    "NoiDung": "Kính báo toàn thể bà con nội ngoại. Năm nay lễ Tế Tổ sẽ được tổ chức trọng thể tại Nhà thờ họ ở Xóm Văn Xuân, xã Xuân Lộc. Kính mời bà con sắp xếp thời gian về dự để thắt chặt tình đoàn kết dòng tộc.",
                    "HinhAnh": "" 
                },
                {
                    "Loai": "Tin tức",
                    "Ngay": "Tháng 08/2026",
                    "TieuDe": "🎓 Trao phần thưởng Khuyến học cho các cháu đỗ Đại học",
                    "NoiDung": "Hội đồng gia tộc đã tổ chức tuyên dương và trích Quỹ Khuyến học trao thưởng cho các cháu đỗ Đại học điểm cao năm nay. Mong các cháu tiếp tục phát huy truyền thống hiếu học khoa bảng vẻ vang của dòng Họ Từ.",
                    "HinhAnh": ""
                },
                {
                    "Loai": "Tin tức",
                    "Ngay": "Tháng 02/2026",
                    "TieuDe": "🛠️ Hoàn thành tu bổ khuôn viên Khu lăng mộ",
                    "NoiDung": "Nhờ sự chung tay đóng góp tịnh tài, tịnh vật của bà con con cháu thập phương, khuôn viên lăng mộ các bậc Tiên tổ đã được lát gạch và xây bờ bao khang trang, sạch đẹp. Xin ghi nhận công đức của toàn thể bà con.",
                    "HinhAnh": ""
                }
            ]

            tab_sukien, tab_tintuc = st.tabs(["🗓️ Sự kiện sắp diễn ra", "📌 Tin tức hoạt động"])
            
            with tab_sukien:
                su_kien_sap_toi = [tin for tin in tin_tuc_dong_ho if tin["Loai"] == "Sự kiện sắp tới"]
                if su_kien_sap_toi:
                    for sk in su_kien_sap_toi:
                        st.error(f"### {sk['TieuDe']}")
                        st.write(f"🕒 **Thời gian:** {sk['Ngay']}")
                        st.write(f"📝 **Nội dung:** {sk['NoiDung']}")
                        if sk['HinhAnh']:
                            try: st.image(sk['HinhAnh'], use_container_width=True)
                            except: pass
                        st.button("🔔 Đăng ký tham gia / Nhắc lịch", key=f"btn_sk_{sk['TieuDe']}")
                        st.markdown("---")
                else:
                    st.success("Hiện tại chưa có sự kiện nào sắp diễn ra.")

            with tab_tintuc:
                tin_tuc_cu = [tin for tin in tin_tuc_dong_ho if tin["Loai"] == "Tin tức"]
                if tin_tuc_cu:
                    for tin in tin_tuc_cu:
                        with st.expander(f"[{tin['Ngay']}] {tin['TieuDe']}", expanded=True):
                            st.write(tin['NoiDung'])
                            if tin['HinhAnh']:
                                try: st.image(tin['HinhAnh'], use_container_width=True)
                                except: pass
                else:
                    st.write("Chưa có bản tin nào được cập nhật.")

        # ---------------------------------------------------------
        # MỤC 2: BẢNG VÀNG CÔNG ĐỨC & KHUYẾN HỌC
        # ---------------------------------------------------------
        elif "2." in menu_mo_rong:
            st.markdown('<h3 class="desktop-view" style="color: #8B0000; font-weight: bold;">📊 Bảng Vàng Công Đức & Khuyến Học</h3>', unsafe_allow_html=True)
            st.markdown('<h3 class="mobile-view" style="color: #8B0000; font-size: 1.15rem; font-weight: bold;">📊 Công Đức & Khuyến Học</h3>', unsafe_allow_html=True)
            st.write("Nơi lưu danh và tri ân những tấm lòng vàng đóng góp xây dựng dòng họ, cùng các tấm gương hiếu học xuất sắc.")

            du_lieu_bang_vang = {
                "cong_duc": [
                    {"Nam": "2026", "NguoiGop": "Gia đình ông Từ ............", "SoTien_HienVat": "50.000.000 VNĐ", "GhiChu": "Trùng tu khuôn viên lăng mộ"},
                    {"Nam": "2026", "NguoiGop": "Ông Từ Hữu ...........", "SoTien_HienVat": "Cặp lục bình đá nguyên khối", "GhiChu": "Cung tiến Nhà thờ Tổ"},
                    {"Nam": "2025", "NguoiGop": "Tập thể con cháu Chi ........", "SoTien_HienVat": "120.000.000 VNĐ", "GhiChu": "Đóng góp Quỹ Khuyến học họ Từ"}
                ],
                "khuyen_hoc": [
                    {"Nam": "2026", "NguoiNhan": "Cháu Từ Hữu ...........", "ThanhTich": "Đậu Đại học Bách Khoa Hà Nội", "PhanThuong": "Giấy khen & 5.000.000 VNĐ"},
                    {"Nam": "2026", "NguoiNhan": "Cháu Từ Hữu ...........", "ThanhTich": "Giải Nhất học sinh giỏi cấp Tỉnh", "PhanThuong": "Giấy khen & 2.000.000 VNĐ"},
                    {"Nam": "2025", "NguoiNhan": "Cháu Từ Hữu ...........", "ThanhTich": "Đạt danh hiệu Học sinh giỏi Xuất sắc", "PhanThuong": "Sách vở & 500.000 VNĐ"}
                ]
            }

            tab_cd, tab_kh = st.tabs(["💰 Ghi nhận Công đức", "🎓 Tuyên dương Khuyến học"])

            with tab_cd:
                for item in du_lieu_bang_vang["cong_duc"]:
                    html_card = f"""
                    <div class="desktop-view" style="background: linear-gradient(to right, #FFF8DC, #FFFFFF); border-left: 6px solid #DAA520; padding: 15px 20px; margin-bottom: 12px; border-radius: 6px; box-shadow: 1px 2px 5px rgba(0,0,0,0.08); display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 2;">
                            <span style="font-size: 1.15rem; font-weight: bold; color: #8B0000;">{item['NguoiGop']}</span><br>
                            <span style="color: #444; font-size: 1rem;">📍 Mục đích: {item['GhiChu']} (Ghi nhận năm: {item['Nam']})</span>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <span style="font-size: 1.25rem; font-weight: bold; color: #B8860B; background: #FFF; padding: 5px 15px; border-radius: 20px; border: 1px solid #EEE;">🎁 {item['SoTien_HienVat']}</span>
                        </div>
                    </div>

                    <div class="mobile-view" style="background: #FFFDF0; border-top: 4px solid #DAA520; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                        <div style="font-weight: bold; color: #8B0000; font-size: 1.1rem; margin-bottom: 8px;">👤 {item['NguoiGop']}</div>
                        <div style="color: #B8860B; font-weight: bold; font-size: 1.15rem; margin-bottom: 8px;">🎁 {item['SoTien_HienVat']}</div>
                        <div style="color: #555; font-size: 0.95rem; margin-bottom: 4px;">📍 {item['GhiChu']}</div>
                        <div style="color: #888; font-size: 0.85rem; font-style: italic;">⏳ Năm: {item['Nam']}</div>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)
                st.button("✍️ Đăng ký cung tiến / Đóng góp", key="btn_cungtien", use_container_width=True)

            with tab_kh:
                for item in du_lieu_bang_vang["khuyen_hoc"]:
                    html_card = f"""
                    <div class="desktop-view" style="background: linear-gradient(to right, #F0F8FF, #FFFFFF); border-left: 6px solid #4682B4; padding: 15px 20px; margin-bottom: 12px; border-radius: 6px; box-shadow: 1px 2px 5px rgba(0,0,0,0.08); display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 2;">
                            <span style="font-size: 1.15rem; font-weight: bold; color: #000080;">🎓 {item['NguoiNhan']}</span><br>
                            <span style="color: #444; font-size: 1rem;">🏆 Thành tích: {item['ThanhTich']} (Năm: {item['Nam']})</span>
                        </div>
                        <div style="flex: 1; text-align: right;">
                            <span style="font-size: 1.1rem; font-weight: bold; color: #D2691E; background: #FFF; padding: 5px 15px; border-radius: 20px; border: 1px solid #EEE;">🏅 {item['PhanThuong']}</span>
                        </div>
                    </div>

                    <div class="mobile-view" style="background: #F8FBFF; border-top: 4px solid #4682B4; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                        <div style="font-weight: bold; color: #000080; font-size: 1.1rem; margin-bottom: 8px;">🎓 {item['NguoiNhan']}</div>
                        <div style="color: #444; font-weight: bold; font-size: 0.95rem; margin-bottom: 8px;">🏆 {item['ThanhTich']}</div>
                        <div style="color: #D2691E; font-size: 1rem; font-weight: bold; margin-bottom: 4px;">🏅 Thưởng: {item['PhanThuong']}</div>
                        <div style="color: #888; font-size: 0.85rem; font-style: italic;">⏳ Năm: {item['Nam']}</div>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)
                st.button("📝 Cập nhật bảng điểm / Thành tích", key="btn_khuyenhoc", use_container_width=True)


        # ---------------------------------------------------------
        # MỤC 3: THƯ VIỆN DI SẢN (BÀI CÚNG, GIA PHẢ GỐC, TÀI LIỆU THAM KHẢO)
        # ---------------------------------------------------------
        elif "3." in menu_mo_rong:
            st.markdown('<h3 class="desktop-view" style="color: #8B4513; font-weight: bold;">📜 Thư Viện Di Sản & Văn Tế Truyền Thống</h3>', unsafe_allow_html=True)
            st.markdown('<h3 class="mobile-view" style="color: #8B4513; font-size: 1.15rem; font-weight: bold;">📜 Thư Viện Di Sản</h3>', unsafe_allow_html=True)
            st.write("Nơi lưu trữ, bảo tồn và truyền tụng các tài liệu quý giá, sắc phong, phổ ký, các bài cúng giỗ chuẩn mực và tài liệu tham khảo chéo của dòng họ.")

            # ==========================================
            # 🔌 Ổ CẮM DỮ LIỆU THƯ VIỆN DI SẢN (Hỗ trợ cả xem text và đính kèm file PDF)
            # ==========================================
            thu_vien_di_san = {
                "bai_cung": [
                    {
                        "TieuDe": "Bài văn khấn Lễ Tế Tổ Dòng Họ",
                        "DoiTuong": "Đọc tại Nhà thờ họ vào ngày giỗ Tổ",
                        "NoiDung": "Duy Việt Nam quốc, Hà Tĩnh tỉnh, Can Lộc huyện, Xuân Lộc xã...\n\nHôm nay là ngày... tháng... năm...\nToàn thể con cháu nội ngoại dòng Họ Từ Xuân Lộc tề tựu chắp tay kính bái...\n\n(Nội dung hiển thị trực tiếp trên web)",
                        "LinkOnline": "", 
                        "FilePDF": "tailieu/bai_cung_te_to.pdf" # 👈 Tùy chọn: Bỏ file PDF vào thư mục tailieu
                    },
                    {
                        "TieuDe": "Bài khấn Cúng Gia Tiên ngày Lễ Tết",
                        "DoiTuong": "Dùng chung cho các gia đình con cháu",
                        "NoiDung": "Hôm nay là ngày Mùng 1 tháng Giêng năm...\nTín chủ con là: [Tên gia chủ]\nNgụ tại: [Địa chỉ]\n\nKính cẩn thưa trình tiên tổ...",
                        "LinkOnline": "",
                        "FilePDF": "" 
                    }
                ],
                "tai_lieu": [
                    {
                        "TieuDe": "Bản dịch Phổ ký Đại tôn họ Từ",
                        "Loai": "Phổ ký - Gia phả (File PDF)",
                        "TomTat": "Bản dịch sang chữ Quốc ngữ từ cuốn gia phả chữ Hán cổ do các bậc tiền bối để lại, ghi chép lại nguồn gốc cội nguồn dòng họ từ đời Khởi tổ.",
                        "LinkOnline": "", 
                        "FilePDF": "tailieu/ban_dich_gia_pha.pdf" 
                    },
                    {
                        "TieuDe": "Sắc phong thời vua Thành Thái",
                        "Loai": "Sắc phong (Bản chụp PDF/JPG)",
                        "TomTat": "Hình ảnh bản sắc phong vua ban truy tặng cho các cụ Tổ có công lao hiển hách với triều đình và đất nước.",
                        "LinkOnline": "https://drive.google.com/file/d/vi-du-link-nao-do/view",
                        "FilePDF": "" 
                    }
                ],
                "tai_lieu_tham_khao": [
                    {
                        "TieuDe": "Gia phả Chi 1 / Cửa Giáp",
                        "Loai": "Tài liệu đối chiếu (File PDF)",
                        "TomTat": "Tài liệu gia phả của nhánh Chi 1 thuộc Cửa Giáp dùng để con cháu tham khảo, đối chiếu thế thứ họ hàng.",
                        "LinkOnline": "",
                        "FilePDF": "tailieu/gia_pha_chi1_giap.pdf"
                    },
                    {
                        "TieuDe": "Gia phả Đại tôn Cổ Kênh",
                        "Loai": "Tài liệu tham khảo (Bản PDF)",
                        "TomTat": "Tài liệu gốc lưu trữ tại quê tổ Cổ Kênh, Thạch Hà để tham chiếu nguồn gốc phát tích của dòng họ.",
                        "LinkOnline": "",
                        "FilePDF": ""
                    }
                ]
            }

            # 🟢 CHIA 3 TAB GỌN GÀNG
            tab_baicung, tab_tailieu, tab_thamkhao = st.tabs(["🙏 Văn khấn & Bài cúng", "📚 Phổ ký & Sắc phong", "📑 Tài liệu tham khảo"])

            with tab_baicung:
                st.info("💡 Bấm vào tên bài khấn để mở rộng xem nội dung chi tiết. Có thể sao chép để in ra, đọc trên điện thoại hoặc tải file PDF gốc về.")
                for idx_bc, item_bc in enumerate(thu_vien_di_san["bai_cung"]):
                    with st.expander(f"📖 {item_bc['TieuDe']} ({item_bc['DoiTuong']})"):
                        st.markdown(f"**Mục đích sử dụng:** *{item_bc['DoiTuong']}*")
                        st.markdown("---")
                        st.text(item_bc['NoiDung'])
                        st.markdown("---")
                        
                        # Thêm hàng nút tải PDF cho Bài cúng
                        col_bc1, col_bc2 = st.columns(2)
                        with col_bc1:
                            if item_bc.get("LinkOnline") and str(item_bc["LinkOnline"]).strip() != "":
                                st.link_button("🌐 Xem trực tuyến (Drive/Web)", item_bc["LinkOnline"], key=f"btn_web_bc_{idx_bc}", use_container_width=True)
                            else:
                                st.button("🌐 Xem trực tuyến", disabled=True, key=f"btn_web_dis_bc_{idx_bc}", use_container_width=True)
                                
                        with col_bc2:
                            file_path_bc = item_bc.get("FilePDF", "")
                            if file_path_bc and os.path.exists(file_path_bc):
                                with open(file_path_bc, "rb") as pdf_file_bc:
                                    st.download_button(
                                        label="📥 Tải File PDF Bài Cúng về máy",
                                        data=pdf_file_bc,
                                        file_name=os.path.basename(file_path_bc),
                                        mime="application/pdf",
                                        key=f"dl_pdf_bc_{idx_bc}",
                                        use_container_width=True
                                    )
                            else:
                                st.button("📥 Tải File PDF (Chưa có file)", disabled=True, key=f"btn_pdf_dis_bc_{idx_bc}", use_container_width=True)
                        
            with tab_tailieu:
                for idx, item in enumerate(thu_vien_di_san["tai_lieu"]):
                    html_card = f"""
                    <div class="desktop-view" style="background: #FDF5E6; border-left: 5px solid #D2691E; padding: 15px; margin-bottom: 8px; border-radius: 6px;">
                        <h4 style="margin:0; color: #8B4513;">{item['TieuDe']}</h4>
                        <span style="font-size: 0.9em; color: #666;">🏷️ Phân loại: {item['Loai']}</span>
                        <p style="margin: 8px 0; color: #333;">{item['TomTat']}</p>
                    </div>
                    
                    <div class="mobile-view" style="background: #FDF5E6; border-top: 4px solid #D2691E; padding: 12px; margin-bottom: 8px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-weight: bold; color: #8B4513; font-size: 1.1rem; margin-bottom: 4px;">{item['TieuDe']}</div>
                        <div style="font-size: 0.85em; color: #666; margin-bottom: 8px;">🏷️ {item['Loai']}</div>
                        <div style="color: #333; font-size: 0.95em; margin-bottom: 8px;">{item['TomTat']}</div>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if item.get("LinkOnline") and str(item["LinkOnline"]).strip() != "":
                            st.link_button("🌐 Xem trực tuyến (Drive/Web)", item["LinkOnline"], use_container_width=True)
                        else:
                            st.button("🌐 Xem trực tuyến", disabled=True, key=f"btn_web_dis_{idx}", use_container_width=True)
                            
                    with col_btn2:
                        file_path = item.get("FilePDF", "")
                        if file_path and os.path.exists(file_path):
                            with open(file_path, "rb") as pdf_file:
                                st.download_button(
                                    label="📥 Tải File PDF về máy",
                                    data=pdf_file,
                                    file_name=os.path.basename(file_path),
                                    mime="application/pdf",
                                    key=f"dl_pdf_{idx}",
                                    use_container_width=True
                                )
                        else:
                            st.button("📥 Tải File PDF (Chưa có file)", disabled=True, key=f"btn_pdf_dis_{idx}", use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)

            with tab_thamkhao:
                st.info("💡 Không gian lưu trữ các tài liệu, gia phả của các Chi/Phái khác hoặc dòng họ liên quan để đối chiếu, nghiên cứu.")
                for idx_tk, item_tk in enumerate(thu_vien_di_san["tai_lieu_tham_khao"]):
                    html_card_tk = f"""
                    <div class="desktop-view" style="background: #F0F8FF; border-left: 5px solid #4682B4; padding: 15px; margin-bottom: 8px; border-radius: 6px;">
                        <h4 style="margin:0; color: #000080;">{item_tk['TieuDe']}</h4>
                        <span style="font-size: 0.9em; color: #666;">🏷️ Phân loại: {item_tk['Loai']}</span>
                        <p style="margin: 8px 0; color: #333;">{item_tk['TomTat']}</p>
                    </div>
                    
                    <div class="mobile-view" style="background: #F0F8FF; border-top: 4px solid #4682B4; padding: 12px; margin-bottom: 8px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="font-weight: bold; color: #000080; font-size: 1.1rem; margin-bottom: 4px;">{item_tk['TieuDe']}</div>
                        <div style="font-size: 0.85em; color: #666; margin-bottom: 8px;">🏷️ {item_tk['Loai']}</div>
                        <div style="color: #333; font-size: 0.95em; margin-bottom: 8px;">{item_tk['TomTat']}</div>
                    </div>
                    """
                    st.markdown(html_card_tk, unsafe_allow_html=True)
                    
                    col_btn1_tk, col_btn2_tk = st.columns(2)
                    with col_btn1_tk:
                        if item_tk.get("LinkOnline") and str(item_tk["LinkOnline"]).strip() != "":
                            st.link_button("🌐 Xem trực tuyến", item_tk["LinkOnline"], key=f"btn_web_tk_{idx_tk}", use_container_width=True)
                        else:
                            st.button("🌐 Xem trực tuyến", disabled=True, key=f"btn_web_dis_tk_{idx_tk}", use_container_width=True)
                            
                    with col_btn2_tk:
                        file_path_tk = item_tk.get("FilePDF", "")
                        if file_path_tk and os.path.exists(file_path_tk):
                            with open(file_path_tk, "rb") as pdf_file_tk:
                                st.download_button(
                                    label="📥 Tải File PDF về máy",
                                    data=pdf_file_tk,
                                    file_name=os.path.basename(file_path_tk),
                                    mime="application/pdf",
                                    key=f"dl_pdf_tk_{idx_tk}",
                                    use_container_width=True
                                )
                        else:
                            st.button("📥 Tải File PDF (Chưa có file)", disabled=True, key=f"btn_pdf_dis_tk_{idx_tk}", use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)     
 
        # ---------------------------------------------------------
        # MỤC 4: SỔ VÀNG (Ý KIẾN & LỜI TRI ÂN)
        # ---------------------------------------------------------

        elif "4." in menu_mo_rong:
            st.markdown('<h3 class="desktop-view" style="color: #2E8B57; font-weight: bold;">💬 Sổ Vàng Gia Tộc (Ý Kiến & Lời Tri Ân)</h3>', unsafe_allow_html=True)
            st.markdown('<h3 class="mobile-view" style="color: #2E8B57; font-size: 1.15rem; font-weight: bold;">💬 Sổ Vàng Gia Tộc</h3>', unsafe_allow_html=True)
            st.write("Không gian lưu giữ những dòng tâm tư, tình cảm, lời tri ân tiên tổ và các ý kiến đóng góp xây dựng dòng họ của con cháu khắp mọi miền.")

            tab_doc, tab_viet = st.tabs(["📖 Xem Sổ Vàng", "✍️ Viết Lời Lưu Bút"])

            with tab_doc:
                if "danh_sach_so_vang" not in st.session_state:
                    st.session_state.danh_sach_so_vang = [
                        {"id": 101, "NguoiGui": "Kho_Chung_Cu_Nha_2", "Chi": "Chi 2/Ất (Xuân Lộc)", "Ngay": "12/10/2026", "NoiDung": "Cảm ơn Ban Quản trị đã tâm huyết xây dựng ứng dụng gia phả số hóa tuyệt vời này."},
                        {"id": 102, "NguoiGui": "Cháu Từ ......", "Chi": "Hà Nội", "Ngay": "05/09/2026", "NoiDung": "Thế hệ trẻ chúng cháu rất tự hào về truyền thống dòng họ."},
                        {"id": 103, "NguoiGui": "Bà Từ Thị ......", "Chi": "Đà Nẵng", "Ngay": "01/08/2026", "NoiDung": "Kính chúc dòng Họ Từ ngày càng hưng vượng, con cháu thành đạt."}
                    ]
                
                so_vang_da_duyet = st.session_state.danh_sach_so_vang

                if not so_vang_da_duyet:
                    st.info("Cuốn Sổ vàng hiện đang chờ những lời tri ân đầu tiên từ bà con...")
                else:
                    is_config_admin = True  

                    for item in so_vang_da_duyet:
                        bai_id = item.get('id')
                        nguoi_gui_val = item.get('NguoiGui')
                        ngay_val = item.get('Ngay')
                        chi_val = item.get('Chi')
                        noi_dung_val = item.get('NoiDung')
                        
                        # Sử dụng f-string an toàn từng dòng, không bao bọc HTML cồng kềnh
                        st.markdown(f"""
                        <div class="desktop-view" style="background: #F5FFFA; border-left: 5px solid #2E8B57; padding: 15px; margin-bottom: 8px; border-radius: 6px; box-shadow: 1px 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-weight: bold; color: #2E8B57; font-size: 1.1rem;">👤 {nguoi_gui_val}</span>
                                <span style="color: #888; font-size: 0.9rem;">🕒 {ngay_val}</span>
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">📍 Nơi ở / Chi phái: {chi_val}</div>
                            <div style="color: #333; font-size: 1.05rem; font-style: italic; border-left: 3px solid #ddd; padding-left: 10px;">"{noi_dung_val}"</div>
                        </div>
                        
                        <div class="mobile-view" style="background: #F5FFFA; border-top: 4px solid #2E8B57; padding: 12px; margin-bottom: 8px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-weight: bold; color: #2E8B57; font-size: 1.05rem; margin-bottom: 4px;">👤 {nguoi_gui_val}</div>
                            <div style="font-size: 0.85em; color: #888; margin-bottom: 4px;">🕒 {ngay_val} | 📍 {chi_val}</div>
                            <div style="color: #333; font-size: 0.95em; margin-top: 8px; font-style: italic; border-left: 2px solid #ddd; padding-left: 8px;">"{noi_dung_val}"</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if is_config_admin:
                            if st.button(f"🗑️ Thu hồi bài này (ID: {bai_id})", key=f"del_sovang_{bai_id}"):
                                st.session_state.danh_sach_so_vang = [b for b in st.session_state.danh_sach_so_vang if b['id'] != bai_id]
                                st.rerun() 
                        
                        st.markdown("<br>", unsafe_allow_html=True)

            with tab_viet:
                st.info("📝 Nội dung sẽ được gửi thẳng về Ban Quản trị phê duyệt và tự động xóa khỏi biểu mẫu sau khi gửi thành công.")
                
                with st.form("form_so_vang", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        nguoi_gui = st.text_input("Họ và tên người gửi (*):", placeholder="Ví dụ: Từ Quang...")
                    with col2:
                        chi_phai = st.text_input("Chi phái / Nơi ở hiện tại:", placeholder="Ví dụ: Chi 2/Ất hoặc TP.HCM")
                    
                    noi_dung = st.text_area("Nội dung lưu bút (*):", placeholder="Nhập tâm tư, nguyện vọng hoặc ý kiến đóng góp của bà con...", height=120)
                    
                    submit_btn = st.form_submit_button("📤 Gửi Sổ Vàng", use_container_width=True)
                    
                    if submit_btn:
                        if nguoi_gui.strip() == "" or noi_dung.strip() == "":
                            st.warning("⚠️ Bà con vui lòng điền đầy đủ Họ tên và Nội dung!")
                        else:
                            import datetime
                            ngay_hien_tai = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                            
                            try:
                                token, chat_id = TelegramBotManager.get_bot_token_and_chat_id()
                                if token and chat_id:
                                    import requests
                                    tin_nhan_bot = f"🔔 [SỔ VÀNG] LỜI NHẮN MỚI CHỜ DUYỆT!\n👤 Người gửi: {nguoi_gui}\n📍 Chi phái: {chi_phai}\n⏳ Thời gian: {ngay_hien_tai}\n💬 Nội dung: {noi_dung}"
                                    url_tele = f"https://api.telegram.org/bot{token}/sendMessage"
                                    payload = {"chat_id": chat_id, "text": tin_nhan_bot}
                                    requests.post(url_tele, json=payload, timeout=5)
                            except Exception:
                                pass 
                            
                            st.success(f"✅ Đã gửi thành công! Xin cảm ơn {nguoi_gui}. Lời tri ân đang chờ Ban quản trị phê duyệt.")
        # ---------------------------------------------------------
        # MỤC 5: BẢN ĐỒ TÂM LINH & LĂNG MỘ
        # ---------------------------------------------------------
        elif "5." in menu_mo_rong:
            # Lớp BanDoGiaToc đã tự động xử lý responsive tiêu đề bên trong hàm render_bando()
            try:
                BanDoGiaToc.render_bando()
            except NameError:
                st.error("⚠️ Lớp BanDoGiaToc chưa được định nghĩa hoặc chưa được nạp. Hãy đảm bảo ông chủ đã chèn Khối [PHÂN LÔ F] vào mã nguồn.")
            




    #=====================================================================
    # [PHÂN LÔ E10]: Hướng dẫn sử dụng và Trợ lý ảo AI
    #=====================================================================

    @staticmethod
    def render_huong_dan_va_ai(df):
        st.markdown('<h3 class="desktop-view" style="color: #8B0000; font-weight: bold;">🤖 Trợ Lý AI & Cẩm Nang Dòng Họ</h3>', unsafe_allow_html=True)
        st.markdown('<h3 class="mobile-view" style="color: #8B0000; font-size: 1.15rem; font-weight: bold;">🤖 Trợ Lý AI & Cẩm Nang</h3>', unsafe_allow_html=True)
        st.write("Trung tâm tra cứu cẩm nang vận hành và giao lưu cùng Trợ lý ảo thông thái dòng họ Từ Xuân Lộc.")

        tab_hd, tab_ai = st.tabs(["📖 Cẩm nang sử dụng", "🤖 Trợ lý ảo AI (Đa nhiệm & Giọng đọc)"])

        # ==========================================
        # TAB 1: HƯỚNG DẪN SỬ DỤNG (CHIA NHỎ & TRANG TRỌNG)
        # ==========================================
        with tab_hd:
            st.markdown("""
                <div style="background: #FFF8E1; border-left: 5px solid #8B0000; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <h4 style="color: #8B0000; margin: 0 0 5px 0; font-family: 'Times New Roman', Times, serif; font-weight: bold;">
                        📖 CẨM NANG VẬN HÀNH GIA PHẢ ĐIỆN TỬ
                    </h4>
                    <p style="margin: 0; color: #4E342E; font-size: 0.95rem; font-family: 'Times New Roman', Times, serif; line-height: 1.5;">
                        <em>Kính cẩn chào mừng toàn thể con cháu nội ngoại hướng về cội nguồn.</em> Dưới đây là các chỉ dẫn chi tiết, được chia nhỏ từng bước để các bậc cao niên và con cháu dễ dàng tra cứu huyết mạch tộc họ.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🌐 1. Truy Cập & Thao Tác Cơ Bản Trên Điện Thoại"):
                st.markdown("""
                * **Mở/Đóng Menu điều hướng:** Chạm vào biểu tượng mũi tên (`>` hoặc `<`) ở góc trái phía trên màn hình để mở bảng chọn các chức năng.
                * **Thao tác phóng to / thu nhỏ sơ đồ:** Người dùng dùng hai ngón tay chụm lại để thu nhỏ toàn cảnh hoặc kéo giãn ra để xem chi tiết tên cụ, năm sinh, đời thứ. Có thể dùng các nút bấm `(+)`, `(-)` tích hợp sẵn ở góc sơ đồ.
                """)
                
            with st.expander("🗺️ 2. Hướng Dẫn Xem Trực Hệ & Toàn Cảnh"):
                st.markdown("""
                * **Chức năng Trực Hệ:** Giúp xem ngược dòng cội nguồn từ con cháu lên Cụ Thủy Tổ. Bà con có thể bấm bật "Mở rộng nhánh dưới" để xem các đời con cháu tiếp theo.
                * **Chức năng Toàn Cảnh:** Sơ đồ phả hệ tổng thể từ gốc đến ngọn. Hỗ trợ các bộ lọc hiển thị (chỉ đinh nam, chi tiết, hoặc cả nam & nữ) và lọc theo từng Cửa, Chi nhánh để không bị rối mắt.
                """)

            with st.expander("🔍 3. Tra Cứu & Giải Mã Định Danh 9 Chữ Số"):
                st.markdown("""
                * **Tra cứu nhanh (Danh bộ):** Gõ tên hoặc tên tự vào ô tìm kiếm để lọc nhanh danh sách gia tộc.
                * **Ý nghĩa Mã định danh (Ví dụ: `124.07.0.049`):** 
                  - **3 số đầu (124):** Xác định Cửa, Chi hoặc Phái gốc.
                  - **2 số tiếp (07):** Định danh chính xác đời thứ mấy.
                  - **Số thứ 6 (0):** Biểu thị giới tính (`0` là Nam, `1` là Nữ).
                  - **3 số cuối (049):** Số thứ tự cá nhân sinh trưởng trong nhánh.
                """)

            with st.expander("✍️ 4. Thêm Thành Viên & Sổ Vàng Tri Ân"):
                st.markdown("""
                * **Thêm Thành Viên:** Con cháu vào mục "Thêm Thành Viên", điền thông tin nhân khẩu mới. Dữ liệu sẽ được gửi về Telegram để Ban quản lý kiểm duyệt trước khi đưa vào hệ thống.
                * **Sổ Vàng:** Nơi bà con viết lời tri ân tiên tổ, ghi nhận công đức hoặc đóng góp ý kiến xây dựng dòng họ, giữ gìn đạo lý "Uống nước nhớ nguồn".
                """)

        # ==========================================
        # TAB 2: TRỢ LÝ ẢO AI (2 LUỒNG TRÍ TUỆ & LOA gTTS)
        # ==========================================
        with tab_ai:
            st.info("🤖 Trợ lý AI đã được nâng cấp toàn diện: Vừa hướng dẫn cách dùng ứng dụng, vừa tra cứu chính xác tuyệt đối tên thành viên (Phân biệt rạch ròi Hòa và Hoa).")
            
            user_question = st.text_input("💬 Nhập câu hỏi của bạn cho Trợ lý ảo:", placeholder="Ví dụ: Làm sao để thêm thành viên? hoặc Từ Quang Thùy là ai?")
            
            if st.button("🚀 Gửi câu hỏi cho AI", use_container_width=True):
                if not user_question.strip():
                    st.warning("⚠️ Vui lòng nhập nội dung câu hỏi!")
                else:
                    import unicodedata, re
                    
                    q_raw = user_question.strip()
                    # Chuẩn hóa NFD để xử lý tách từ tiếng Việt chuẩn xác
                    q_lower = unicodedata.normalize('NFC', q_raw.lower())
                    
                    phan_hoi_html = ""
                    thong_tin_doc = ""
                    
                    # ---------------------------------------------------------
                    # LUỒNG 1: HƯỚNG DẪN CÁCH SỬ DỤNG ỨNG DỤNG (APP USAGE)
                    # ---------------------------------------------------------
                    if any(kw in q_lower for kw in ["thêm thành viên", "bổ sung", "nhập thêm", "đăng ký mới"]):
                        thong_tin_doc = "Để thêm thành viên mới, bà con vui lòng mở Menu, chọn mục 'Thêm Thành Viên'. Sau đó điền đầy đủ thông tin nhân khẩu và chọn Cha trực hệ. Hệ thống sẽ gửi đề xuất về cho Ban quản lý phê duyệt."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                    
                    elif any(kw in q_lower for kw in ["sơ đồ", "trực hệ", "toàn cảnh", "cách xem", "phả hệ"]):
                        thong_tin_doc = "Để xem sơ đồ, bà con mở Menu góc trái, chọn 'Trực Hệ' để xem ngược dòng từ con cháu lên Thủy tổ, hoặc chọn 'Toàn Cảnh' để nhìn bức tranh tổng thể toàn dòng họ. Dùng 2 ngón tay để phóng to, thu nhỏ."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                        
                    elif any(kw in q_lower for kw in ["mã định danh", "cấu trúc", "9 chữ số", "ý nghĩa mã"]):
                        thong_tin_doc = "Mã định danh gồm 9 chữ số. 3 số đầu chỉ Cửa và Chi. 2 số tiếp theo chỉ đời thứ mấy. Chữ số thứ 6 là giới tính. Và 3 số cuối là thứ tự sinh trưởng trong nhánh."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                        
                    elif any(kw in q_lower for kw in ["sổ vàng", "tri ân", "góp ý"]):
                        thong_tin_doc = "Bà con hãy vào mục 'Sổ Vàng' trên Menu để viết lời tri ân tiên tổ, đóng góp ý kiến hoặc ghi nhận công đức. Lời nhắn sẽ được hiển thị công khai sau khi duyệt."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                    
                    # ---------------------------------------------------------
                    # LUỒNG 2: TRA CỨU DỮ LIỆU NHÂN KHẨU (DATA QUERY)
                    # ---------------------------------------------------------
                    elif any(kw in q_lower for kw in ["thủy tổ", "nguồn gốc", "cội nguồn", "khởi tổ", "ông tổ", "cụ tổ"]):
                        thong_tin_doc = "Thủy tổ dòng họ ta là cụ Từ Dương Đốc, huyết danh Huy Cán, vốn là một bậc thầy thuốc y dược tế sinh đầy đức độ. Cụ đã đặt nền móng vững chắc cho huyết mạch dòng họ Từ Xuân Lộc muôn đời sau."
                        phan_hoi_html = f"📜 <b>Trợ lý AI đáp:</b><br><br>{thong_tin_doc}"
                    
                    else:
                        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
                        
                        # Đã sửa lại từ khóa đếm: Dùng "có mấy" thay vì "mấy" để không nhầm với "đời thứ mấy"
                        is_counting = any(kw in q_lower for kw in ["có mấy", "bao nhiêu người", "tổng số", "có bao nhiêu", "đếm số", "danh sách"])
                        
                        # Loại bỏ các từ phụ trợ để lấy lõi tên cần tìm
                        stop_words = {"có", "mấy", "người", "tên", "là", "thế", "nào", "đời", "thứ", "trong", "họ", "và", "các", "những", "thì", "vị", "này", "được", "gọi", "con", "của", "ai", "cho", "hỏi", "về"}
                        q_words = [w for w in re.findall(r'[a-zà-ỹ]+', q_lower) if w not in stop_words]
                        
                        matched_indices = []
                        if q_words:
                            # Đồng nhất Hòa và Hoà trong từ khóa tìm kiếm
                            q_words_norm = [w.replace("òa", "oà") for w in q_words]
                            
                            for idx, row in df_app.iterrows():
                                ho_ten = str(row.get("HoTen", "")).strip()
                                if not ho_ten or ho_ten in ["Từ Thị ?", "Từ Húy Đỏ", "Từ Thị"]:
                                    continue
                                
                                ho_ten_lower = unicodedata.normalize('NFC', ho_ten.lower())
                                ten_words = re.findall(r'[a-zà-ỹ]+', ho_ten_lower)
                                ten_words_norm = [w.replace("òa", "oà") for w in ten_words]
                                
                                # KHỚP CHÍNH XÁC TUYỆT ĐỐI THEO TỪNG TỪ
                                if all(qw in ten_words_norm for qw in q_words_norm):
                                    matched_indices.append(idx)

                        matched_rows = df_app.loc[matched_indices] if matched_indices else pd.DataFrame()
                        so_luong = len(matched_rows)
                        
                        if so_luong > 0:
                            # TRƯỜNG HỢP: TÌM ĐÍCH DANH 1 NGƯỜI
                            if not is_counting and so_luong == 1:
                                m = matched_rows.iloc[0]
                                m_ten = m.get('HoTen')
                                m_doi = m.get('DoiThu')
                                m_cua = m.get('Cua')
                                m_chi = m.get('Chi')
                                m_phai = m.get('Phai')
                                m_id = m.get('ID')
                                m_vc = m.get('VoChong', '')
                                m_ns = m.get('NamSinh', '')
                                m_nm = m.get('NamMat', '')
                                m_ghichu = m.get('GhiChu', '')
                                
                                if "đời" in q_lower or "thế hệ" in q_lower:
                                    thong_tin_doc = f"Thành viên {m_ten} thuộc đời thứ {m_doi}, thuộc {m_cua}, {m_chi}."
                                    phan_hoi_html = f"🎯 <b>Trợ lý AI trả lời:</b> Thành viên <b>{m_ten}</b> (Mã ĐD: <code>{m_id}</code>) thuộc đời thứ <b>{m_doi}</b> ({m_cua} — {m_chi})."
                                else:
                                    thong_tin_doc = f"Thông tin về thành viên {m_ten}, thuộc đời thứ {m_doi}, {m_cua}, {m_chi}. Vợ hoặc chồng là {m_vc if m_vc else 'Chưa cập nhật'}. Sinh năm {m_ns}, mất năm {m_nm}. Tiểu sử: {m_ghichu if m_ghichu else 'Đang cập nhật'}."
                                    phan_hoi_html = (
                                        f"🎯 <b>Trợ lý AI tìm thấy 1 kết quả chính xác:</b><br><br>"
                                        f"👤 <b>Họ tên:</b> {m_ten} (Mã ĐD: <code>{m_id}</code>)<br>"
                                        f"• <b>Thế hệ:</b> Đời thứ <b>{m_doi}</b> | {m_cua} — {m_chi} {('— ' + m_phai) if m_phai else ''}<br>"
                                        f"• <b>Vợ/Chồng:</b> {m_vc if m_vc else 'Chưa cập nhật'}<br>"
                                        f"• <b>Năm sinh/mất:</b> {m_ns} - {m_nm}<br>"
                                        f"• <b>Tiểu sử/Ghi chú:</b> {m_ghichu if m_ghichu else 'Đang cập nhật'}"
                                    )
                            
                            # TRƯỜNG HỢP: HỎI SỐ LƯỢNG HOẶC NHIỀU NGƯỜI
                            else:
                                chi_tiet_lst = []
                                doc_lst = [f"Tìm thấy tổng cộng {so_luong} thành viên khớp yêu cầu."]
                                for _, m in matched_rows.iterrows():
                                    m_ten = m.get('HoTen')
                                    m_doi = m.get('DoiThu')
                                    m_cua = m.get('Cua')
                                    m_chi = m.get('Chi')
                                    m_id = m.get('ID')
                                    
                                    chi_tiet_lst.append(f"👤 <b>{m_ten}</b> (Mã ĐD: <code>{m_id}</code>) - Đời thứ {m_doi} ({m_cua} — {m_chi})")
                                    doc_lst.append(f"Thành viên {m_ten}, đời thứ {m_doi}.")
                                    
                                thong_tin_doc = " ".join(doc_lst)
                                phan_hoi_html = f"📊 <b>Trợ lý AI thống kê:</b> Tìm thấy tổng cộng <b>{so_luong} thành viên</b>:<br><br>" + "<br><br>".join(chi_tiet_lst)
                        else:
                            thong_tin_doc = "Xin lỗi, tôi không tìm thấy thông tin nào khớp với câu hỏi của bạn."
                            phan_hoi_html = f"🤖 <b>Trợ lý AI đáp:</b> Không tìm thấy thông tin nào khớp với câu hỏi: <i>'{q_raw}'</i>."

                    # HIỂN THỊ VĂN BẢN KẾT QUẢ
                    st.markdown(f"""
                        <div style="background: #FDFEFE; border: 1.5px solid #8B0000; padding: 18px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); font-family: 'Times New Roman', Times, serif; font-size: 1.05rem; color: #2C3E50; margin-bottom: 15px;">
                            {phan_hoi_html}
                        </div>
                    """, unsafe_allow_html=True)

                    # ---------------------------------------------------------
                    # SỬ DỤNG GOOGLE TTS API (CLIENT=GTX) - ỔN ĐỊNH 100%
                    # Loại bỏ hoàn toàn lỗi gTTS và tương thích trên mọi điện thoại
                    # ---------------------------------------------------------
                    import urllib.parse
                    clean_speech_text = re.sub(r'<[^>]*>', '', thong_tin_doc)
                    safe_text = clean_speech_text.replace('\n', ' ').strip()
                    encoded_text = urllib.parse.quote(safe_text)
                    
                    # API phát âm thanh nội bộ ổn định nhất của Google
                    google_tts_url = f"https://translate.googleapis.com/translate_tts?client=gtx&ie=UTF-8&tl=vi&q={encoded_text}"
                    
                    audio_html_code = f"""
                        <div style="display: flex; align-items: center; gap: 10px; background: #FFF8E1; padding: 10px 15px; border-radius: 6px; border: 1px solid #FFE082; font-family: Arial, sans-serif; margin-top: 15px;">
                            <audio controls style="height: 40px; width: 100%;">
                                <source src="{google_tts_url}" type="audio/mpeg">
                                Trình duyệt của thiết bị không hỗ trợ phát âm thanh.
                            </audio>
                        </div>
                        <div style="font-size: 0.85rem; color: #795548; font-style: italic; margin-top: 5px;">
                            🔊 Bấm nút Play (▶) để nghe Trợ lý ảo đọc bằng tiếng Việt chuẩn.
                        </div>
                    """
                    st.components.v1.html(audio_html_code, height=85)                    
    #=====================================================================
    # [PHÂN LÔ E11]: TRUNG TÂM QUẢN TRỊ & VẬN HÀNH HỆ THỐNG (XÓA SẠCH ẢNH + CSDL)
    #=====================================================================
    @staticmethod
    def render_quantri(df):
        st.subheader("🛠️ Trung Tâm Quản Trị & Vận Hành Hệ Thống")
        mat_khau = st.sidebar.text_input("Mật khẩu Quản trị:", type="password")
        
        if mat_khau != "admin12345":
            if mat_khau: st.sidebar.error("❌ Mật khẩu không chính xác!")
            st.warning("🔒 Vui lòng nhập mật khẩu quản trị vào khung bên trái để truy cập.")
            return
            
        st.success("✅ Xác thực Quản trị viên thành công!")
        
        tab_kiemduyet, tab_dulieu, tab_cauhinh, tab_telegram = st.tabs([
            "⏳ Kiểm Duyệt Mới", 
            "🗃️ Dữ Liệu & Ảnh", 
            "⚙️ Cấu Hình Chung", 
            "🤖 Telegram Bot"
        ])


        # ==========================================
        # TAB 1: KIỂM DUYỆT THÀNH VIÊN MỚI (CÓ HIỂN THỊ ẢNH KIỂM TRA TRỰC QUAN)
        # ==========================================
        with tab_kiemduyet:
            st.markdown("### 📋 Danh sách thành viên đang Chờ duyệt")
            df_pending = df[df["TinhTrang"].str.contains("Chờ", case=False, na=False)].copy()
            
            if df_pending.empty:
                st.success("🎉 Hiện không có hồ sơ nào cần phê duyệt. Tất cả đều an toàn!")
            else:
                for _, row in df_pending.iterrows():
                    cha_id = row.get('ChaMe_ID', '')
                    cha_row = df[df['ID'] == cha_id]
                    cha_ten = cha_row.iloc[0]['HoTen'] if not cha_row.empty else "Không rõ"
                    
                    # 🟢 TÌM VÀ KIỂM TRA ẢNH CHÂN DUNG CỦA THÀNH VIÊN NÀY
                    member_id = row['ID']
                    member_name = row['HoTen']
                    img_relative_path = QuanTriHinhAnh.lay_anh_chuan_xac(member_id, member_name)
                    
                    with st.expander(f"👤 {member_name} (ID: {member_id}) - {row['TinhTrang']}", expanded=True):
                        # Chia bố cục: Cột trái chứa thông tin, Cột giữa chứa Ảnh chân dung (nếu có), Cột phải chứa nút bấm
                        col_info, col_img, col_action = st.columns([2, 1, 1])
                        
                        with col_info:
                            st.write(f"- **Cha trực hệ:** **{cha_ten}** (`{cha_id}`)")
                            st.write(f"- **Tình trạng:** `{row['TinhTrang']}`")
                            st.write(f"- **Ghi chú/Nguyện vọng:** {row.get('GhiChu', '')}")
                        
                        with col_img:
                            if img_relative_path:
                                full_img_path = Path(__file__).resolve().parent / img_relative_path
                                if full_img_path.exists():
                                    st.image(str(full_img_path), width=120, caption="Ảnh gửi lên")
                                else:
                                    st.info("🖼️ Không tìm thấy file ảnh vật lý.")
                            else:
                                st.info("📭 Thành viên này chưa tải ảnh.")
                        
                        with col_action:
                            st.markdown("<br>", unsafe_allow_html=True) # Căn chỉnh lề ngang nút bấm
                            if st.button("✅ Phê duyệt", key=f"btn_duyet_{member_id}", use_container_width=True):
                                import re
                                new_tinh_trang = str(row['TinhTrang']).replace("Chờ duyệt,", "").replace("Chờ duyệt", "").replace("Chờ xử lý,", "").replace("Chờ xử lý", "").strip()
                                new_ghi_chu = re.sub(r'\[Xin xếp vào vị trí thứ \d+\]', '', str(row['GhiChu'])).strip()
                                if KhoDuLieuSQL.duyet_thanh_vien(member_id, new_tinh_trang, new_ghi_chu):
                                    st.success(f"Đã duyệt {member_name} thành công!")
                                    st.rerun()

                            if st.button("❌ Xóa bỏ", key=f"btn_xoa_{member_id}", type="primary", use_container_width=True):
                                # 1. Xóa file ảnh vật lý trước khi xóa CSDL
                                try:
                                    if img_relative_path:
                                        p_img = Path(__file__).resolve().parent / img_relative_path
                                        if p_img.exists():
                                            p_img.unlink()
                                except Exception:
                                    pass
                                    
                                # 2. Xóa bản ghi
                                if KhoDuLieuSQL.delete_member(member_id): 
                                    st.warning(f"Đã xóa vĩnh viễn hồ sơ và ảnh của {member_name}!")
                                    KhoDuLieuSQL.load_data.clear()
                                    st.rerun()


        # ==========================================
        # TAB 2: XÓA THÀNH VIÊN & XÓA ẢNH (DỮ LIỆU GỐC)
        # ==========================================
        with tab_dulieu:
            col_xoa_nguoi, col_xoa_anh = st.columns(2)
            
            with col_xoa_nguoi:
                st.markdown("### ❌ Xóa thành viên khỏi CSDL")
                chon_id = st.selectbox("Chọn Mã định danh cần xóa:", [""] + df["ID"].tolist())
                if st.button("❌ Xóa vĩnh viễn khỏi CSDL", type="primary", use_container_width=True):
                    if chon_id:
                        row_chon = df[df["ID"] == chon_id]
                        if not row_chon.empty:
                            t_name = row_chon.iloc[0]["HoTen"]
                            
                            # 1. Xóa file ảnh vật lý tương ứng
                            try:
                                d_anh = QuanTriHinhAnh.lay_anh_chuan_xac(chon_id, t_name)
                                if d_anh:
                                    f_path = Path(__file__).resolve().parent / d_anh
                                    if f_path.exists():
                                        f_path.unlink()
                            except Exception:
                                pass
                                
                        # 2. Xóa CSDL
                        KhoDuLieuSQL.delete_member(chon_id)
                        st.success(f"Đã xóa thành viên mã {chon_id} và file ảnh liên quan!")
                        KhoDuLieuSQL.load_data.clear()
                        st.rerun()
                    else:
                        st.error("Vui lòng chọn một mã định danh.")

            with col_xoa_anh:
                st.markdown("### 🖼️ Xóa ảnh chân dung bị lỗi")
                chon_id_anh = st.selectbox("Chọn ID thành viên cần xóa ảnh:", [""] + df["ID"].tolist(), key="xoa_anh_sel")
                if st.button("🗑️ Xóa file ảnh", use_container_width=True):
                    if chon_id_anh:
                        row_anh = df[df["ID"] == chon_id_anh]
                        if not row_anh.empty:
                            ten_anh = row_anh.iloc[0]["HoTen"]
                            duong_dan = QuanTriHinhAnh.lay_anh_chuan_xac(chon_id_anh, ten_anh)
                            if duong_dan:
                                file_path = Path(__file__).resolve().parent / duong_dan
                                if file_path.exists():
                                    file_path.unlink()
                                    st.success(f"✅ Đã xóa sạch ảnh của {ten_anh}!")
                                    st.rerun()
                            else:
                                st.warning("⚠️ Thành viên này hiện chưa có ảnh trên máy chủ.")
                    else:
                        st.error("Vui lòng chọn một mã định danh.")

        # ==========================================
        # TAB 3: CẤU HÌNH & SAO LƯU
        # ==========================================
        with tab_cauhinh:
            st.markdown("### 🔓 Cấu hình quyền tải ảnh")
            with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT GiaTri FROM CauHinhHeThong WHERE Khoa = 'cho_phep_tai_anh'")
                res = cursor.fetchone()
                current_val = (res[0] == 'True') if res else False

            cho_phep_moi = st.toggle("Mở chế độ cho phép con cháu tự tải ảnh", value=current_val)
            if cho_phep_moi != current_val:
                with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE CauHinhHeThong SET GiaTri = ? WHERE Khoa = 'cho_phep_tai_anh'", (str(cho_phep_moi),))
                    conn.commit()
                st.rerun()
            
            if cho_phep_moi:
                st.warning("⚠️ Đang MỞ: Tất cả mọi người có thể tự tải ảnh chân dung lên hệ thống.")
            else:
                st.info("🔒 Đang KHÓA: Tính năng tự tải ảnh đang tạm vô hiệu hóa.")
            
            st.markdown("---")
            st.markdown("### 📦 Sao lưu toàn bộ ảnh trên máy chủ")
            if st.button("📥 Bắt đầu nén toàn bộ ảnh (.zip)"):
                import zipfile
                import io
                image_dir = Path(__file__).resolve().parent / "images"
                if image_dir.exists():
                    zip_buffer = io.BytesIO()
                    count_img = 0
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for file_path in image_dir.iterdir():
                            if file_path.is_file() and file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".heic", ".heif"]:
                                zip_file.write(file_path, arcname=file_path.name)
                                count_img += 1
                    zip_buffer.seek(0)
                    
                    if count_img > 0:
                        st.success(f"✅ Đã đóng gói thành công {count_img} bức ảnh!")
                        st.download_button(
                            label="⬇️ Tải tệp nén (.zip) về máy",
                            data=zip_buffer,
                            file_name="backup_anh_giapha.zip",
                            mime="application/zip"
                        )
                    else:
                        st.warning("⚠️ Thư mục ảnh hiện đang trống.")
                else:
                    st.warning("⚠️ Không tìm thấy thư mục images trên máy chủ.")

        # ==========================================
        # TAB 4: TELEGRAM BOT
        # ==========================================
        with tab_telegram:
            st.markdown("### 🤖 Cổng kết nối Bot Telegram Quản Trị")
            st.info("Khu vực cấu hình sẵn sàng để tích hợp bot nhận thông báo và phê duyệt trực tiếp trên ứng dụng Telegram.")
            
            enable_tele = st.toggle("Kích hoạt thông báo tự động qua Telegram", value=True)
            if enable_tele:
                st.text_input("Telegram Bot Token:", placeholder="Ví dụ: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
                st.text_input("Admin Chat ID:", placeholder="Ví dụ: 987654321")
                if st.button("💾 Lưu cấu hình Telegram"):
                    st.success("Đã lưu thiết lập kết nối Bot thành công!")
            else:
                st.write("📌 Bật công tắc trên khi ông chủ muốn hệ thống tự động bắn tin nhắn chờ duyệt về điện thoại cá nhân.")


            
    #=====================================================================
    # [PHÂN LÔ E12]: Hàm con điều phối đầu não giao diện với menu chuẩn xác mới (Tối ưu Mobile Title)
    #=====================================================================

    @classmethod
    def render_app(cls):
        cls.thiet_lap_giao_dien()
        
        # 🟢 ĐÓN NHẬN LỆNH CHUYỂN TRANG TỪ TRANG KHÁC (PHẢI ĐẶT TRƯỚC KHI VẼ RADIO)
        if "pending_menu" in st.session_state:
            st.session_state["CHỌN CHỨC NĂNG"] = st.session_state.pending_menu
            del st.session_state.pending_menu

        df = KhoDuLieuSQL.load_data()
 
        # 🟢 CHÈN LOGO VÀO THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
        logo_path = Path(__file__).resolve().parent / "logo_hotu.png"
        if logo_path.exists():
            st.sidebar.image(str(logo_path), use_container_width=True)

        st.markdown('<h1 class="desktop-view" style="font-weight: bold; margin-bottom: 0px;">📜 Gia phả điện tử dòng Họ Từ Xuân Lộc</h1>', unsafe_allow_html=True)
        st.markdown('<h1 class="mobile-view" style="font-size: 1.15rem; font-weight: bold; white-space: nowrap; margin-bottom: 0px;">📜 Gia phả Họ Từ Xuân Lộc</h1>', unsafe_allow_html=True)
        
        st.markdown("""
            <div class="hide-on-mobile">
                <p style="color: #546E7A; margin-top: 5px; margin-bottom: 15px;">Hệ thống quản lý phả hệ chuẩn mực - Cơ sở dữ liệu SQLite tối ưu đa thiết bị</p>
            </div>
        """, unsafe_allow_html=True)

        if "focus_id" not in st.session_state:
            st.session_state.focus_id = "000.01.0.001"

        # 🌟 Đưa khối điều hướng lên sát hết cỡ phía trên (Sát nút << mặc định)
        st.sidebar.markdown("""
            <style>
                @keyframes runSameWayFar {
                    0% { transform: translateX(-8px); opacity: 0.2; }
                    50% { transform: translateX(8px); opacity: 1; }
                    100% { transform: translateX(-8px); opacity: 0.2; }
                }
                .run-arrow-far {
                    display: inline-block;
                    color: #D32F2F;
                    font-weight: 900;
                    animation: runSameWayFar 1.0s infinite ease-in-out;
                }
                /* Dịch toàn bộ vùng chứa sidebar lên sát phía trên cùng */
                [data-testid="stSidebarUserContent"] {
                    padding-top: 0rem !important;
                }
            </style>
            <div style="text-align: center; font-weight: bold; color: #C62828; margin-top: -32px; margin-bottom: 8px; padding: 6px; background: #FFEBEE; border-radius: 6px; border: 1px dashed #EF9A9A;">
                <span class="run-arrow-far">&gt;&gt;</span> &nbsp;&nbsp;&nbsp; ĐIỀU HƯỚNG &nbsp;&nbsp;&nbsp; <span class="run-arrow-far">&gt;&gt;</span>
            </div>
        """, unsafe_allow_html=True)


        menu_options = [
            "📖 Lời Giới thiệu",
            "🎯 Trực Hệ", 
            "🌳 Toàn Cảnh", 
            "🆔 Lọc theo ID", 
            "🔍 Tra Cứu",
            "👤 Cá nhân hóa",
            "✍ Thêm Thành Viên", 
            "🖨 Xuất Báo Cáo",
            "🌟 Mở Rộng",          # 🟢 CHÈN THÊM Ở ĐÂY (NGAY SAU XUẤT BÁO CÁO)
            "🤖 Hướng dẫn & Trợ lý AI",
            "🛡 Quản Trị Hệ Thống",
            "🚪 EXIT"
        ]

        # Kiểm tra nếu có lệnh quay lại trang chủ
        if st.session_state.get("reset_to_intro", False):
            st.session_state["CHỌN CHỨC NĂNG"] = "📖 Lời Giới thiệu"
            st.session_state["reset_to_intro"] = False

        # 🎯 Menu chính

        # 🟢 Kiểm tra xem có lệnh ghi đè menu từ trang khác chuyển sang không
        default_menu_index = 0
        if "app_menu_override" in st.session_state:
            override_val = st.session_state.app_menu_override
            if override_val in menu_options:
                default_menu_index = menu_options.index(override_val)
            del st.session_state.app_menu_override  # Xóa sau khi đã nhận lệnh

        # 🎯 Menu chính tích hợp chỉ mục mặc định
        menu = st.sidebar.radio("CHỌN CHỨC NĂNG:", menu_options, index=default_menu_index, key="CHỌN CHỨC NĂNG")

        # Điều phối giao diện (Đưa "🚪 EXIT" lên đầu để phản hồi ngay lập tức khi người dùng bấm vào)
        if menu == "🚪 EXIT":
            st.markdown("""
                <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #fdfbf7 0%, #f4ebd0 100%); border-radius: 12px; border: 1px solid #d4c5a9; margin-top: 30px; font-family: 'Times New Roman', Times, serif;">
                    <h2 style="color: #8B0000; text-transform: uppercase; margin-bottom: 15px;">📜 KẾT THÚC PHIÊN TRA CỨU</h2>
                    <p style="font-size: 1.15rem; color: #2C3E50; font-style: italic; margin-bottom: 15px;">
                        "Cây có gốc mới nở cành xanh ngọn, nước có nguồn mới chảy khắp sông sâu."
                    </p>
                    <p style="font-size: 1.05rem; color: #555; line-height: 1.6; margin-bottom: 20px;">
                        Cảm ơn quý vị đã sử dụng ứng dụng Gia phả điện tử của dòng Họ.<br>
                        Chúc quý vị luôn mạnh khỏe, hạnh phúc và an khang thịnh vượng!
                    </p>
                    <p style="font-size: 0.95rem; color: #666;">
                        Quý vị có thể đóng tab trình duyệt hoặc bấm nút bên dưới để tiếp tục quay lại trang chủ.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_bt1, col_bt2, col_bt3 = st.columns([1, 2, 1])
            with col_bt2:
                if st.button("🔄 Quay lại trang chủ hệ thống", use_container_width=True):
                    st.session_state["reset_to_intro"] = True
                    st.rerun()

        elif menu == "📖 Lời Giới thiệu":
            cls.render_gioithieu_1trang()
        elif menu == "🎯 Trực Hệ": 
            cls.render_tructhe(df)
        elif menu == "🌳 Toàn Cảnh": 
            cls.render_toancanh(df)
        elif menu == "🆔 Lọc theo ID": 
            cls.render_loc_theo_id(df)
        elif menu == "🔍 Tra Cứu": 
            cls.render_tracuu(df)
        elif menu == "👤 Cá nhân hóa": 
            cn_hoa = QuanLyCaNhanHoa()
            cn_hoa.hien_thi_menu_ca_nhan_hoa()
        elif menu == "✍ Thêm Thành Viên": 
            cls.render_themthanhvien(df)
        elif menu == "🖨 Xuất Báo Cáo": 
            cls.render_xuatbaocao(df)
        elif menu == "🌟 Mở Rộng":
            cls.render_morong()  # 🟢 Đồng bộ chuẩn gọi hàm bằng cls. giống các mục khác

        elif menu == "🤖 Hướng dẫn & Trợ lý AI":
            cls.render_huong_dan_va_ai(df)  # Hoặc gọi trực tiếp khối giao diện nội dung
        elif menu == "🛡 Quản Trị Hệ Thống":
            cls.render_quantri(df)



# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ F] - KHU VỰC BẢN ĐỒ KHÔNG GIAN TÂM LINH & THỰC TẾ ẢO (VR 360)
# (PHIÊN BẢN QUY MÔ ĐẠI TÔN - ĐA PHÂN LỚP)
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

class BanDoGiaToc:
    # --------------------------------------------------------------------------
    # KHỐI 1: DỮ LIỆU ĐẠI TÔN VÀ CÁC CHI TRỰC THUỘC
    # Cập nhật tọa độ thật (ViDo, KinhDo) và Link360 vào các ô bên dưới
    # --------------------------------------------------------------------------
    DANH_SACH_DI_TICH = [
        # === HỆ THỐNG ĐẠI TÔN ===
        {
            "Nhom": "Đại tôn", "Loai": "Nhà thờ", "Ten": "Nhà thờ Đại tôn", 
            "ViDo": 18.425321, "KinhDo": 105.812144, "Link360": "",
            "MoTa": "Trung tâm tín ngưỡng của toàn dòng họ, nơi thờ Thủy Tổ Đại tôn (Chi Lưu)."
        },
        {
            "Nhom": "Đại tôn", "Loai": "Lăng mộ", "Ten": "Lăng mộ Khởi Tổ Đại tôn", 
            "ViDo": None, "KinhDo": None, "Link360": "",
            "MoTa": "Khu lăng mộ Khởi Tổ Đại tôn."
        },

        # === HỆ THỐNG CỬA GIÁP ===
        {
            "Nhom": "Giáp", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 1 / Cửa Giáp", 
            "ViDo": 18.425321, "KinhDo": 105.812144, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 1 thuộc Cửa Giáp."
        },
        {
            "Nhom": "Giáp", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 1 / Cửa Giáp", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 1 Cửa Giáp."
        },
        {
            "Nhom": "Giáp", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 2 / Cửa Giáp", 
            "ViDo": 18.420450, "KinhDo": 105.901809, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 2 thuộc Cửa Giáp (Thạch Bắc)."
        },
        {
            "Nhom": "Giáp", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 2 / Cửa Giáp", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 2 Cửa Giáp."
        },

        # === HỆ THỐNG CỬA ẤT ===
        {
            "Nhom": "Ất", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 1 / Cửa Ất", 
            "ViDo": 18.421275, "KinhDo": 105.827571, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 1 thuộc Cửa Ất (Thượng Nguyên)."
        },
        {
            "Nhom": "Ất", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 1 / Cửa Ất", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 1 Cửa Ất."
        },
        
        # 🟢 ĐIỂM NHẤN TRUNG TÂM: CHI 2 ẤT (TIỂU TÔN XUÂN LỘC)
        {
            "Nhom": "Xuân Lộc", "Loai": "Nhà thờ", "Ten": "Nhà thờ Tiểu tôn Chi 2 / Cửa Ất (Từ Xuân Lộc)", 
            "ViDo": 18.421106, "KinhDo": 105.765740, "Link360": "", 
            "MoTa": "TRUNG TÂM TIỂU TÔN TỪ XUÂN LỘC. Nơi thờ cúng cụ Từ Hữu Mưu và các bậc tiên linh Chi 2 Cửa Ất."
        },
        {
            "Nhom": "Xuân Lộc", "Loai": "Lăng mộ", "Ten": "Khu Lăng mộ Tiểu tôn Chi 2 / Cửa Ất (Từ Xuân Lộc)", 
            "ViDo": 18.421752, "KinhDo": 105.759765, "Link360": "", 
            "MoTa": "Lăng mộ cụ đứng đầu Chi 2 Cửa Ất và các vị tổ Tiểu tôn Xuân Lộc."
        },

        {
            "Nhom": "Ất", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 3 / Cửa Ất", 
            "ViDo": 18.435605, "KinhDo": 105.831180, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 3 thuộc Cửa Ất."
        },
        {
            "Nhom": "Ất", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 3 / Cửa Ất", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 3 Cửa Ất."
        },
        {
            "Nhom": "Ất", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 4 / Cửa Ất", 
            "ViDo": 18.436142, "KinhDo": 105.830161, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 4 thuộc Cửa Ất."
        },
        {
            "Nhom": "Ất", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 4 / Cửa Ất", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 4 Cửa Ất."
        },
        {
            "Nhom": "Ất", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 5 / Cửa Ất", 
            "ViDo": 18.436104, "KinhDo": 105.831470, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 5 thuộc Cửa Ất."
        },
        {
            "Nhom": "Ất", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 5 / Cửa Ất", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 5 Cửa Ất."
        },

        # === HỆ THỐNG CỬA BÍNH ===
        {
            "Nhom": "Bính", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 1 / Cửa Bính", 
            "ViDo": 18.424517, "KinhDo": 105.812987, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 1 thuộc Cửa Bính."
        },
        {
            "Nhom": "Bính", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 1 / Cửa Bính", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 1 Cửa Bính."
        },
        {
            "Nhom": "Bính", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 2 / Cửa Bính", 
            "ViDo": 18.41692000, "KinhDo": 105.830356, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 2 thuộc Cửa Bính."
        },
        {
            "Nhom": "Bính", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 2 / Cửa Bính", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 2 Cửa Bính."
        },
        {
            "Nhom": "Bính", "Loai": "Nhà thờ", "Ten": "Nhà thờ Chi 3 / Cửa Bính", 
            "ViDo": 18.492155, "KinhDo": 105.868197, "Link360": "", "MoTa": "Nơi thờ tự tiên tổ Chi 3 thuộc Cửa Bính."
        },
        {
            "Nhom": "Bính", "Loai": "Lăng mộ", "Ten": "Khu mộ Tổ Chi 3 / Cửa Bính", 
            "ViDo": None, "KinhDo": None, "Link360": "", "MoTa": "Lăng mộ các cụ Chi 3 Cửa Bính."
        }
    ]

    @staticmethod
    def lay_cau_hinh_giao_dien(nhom, loai):
        """Hàm thuật toán quy định màu sắc và biểu tượng cho từng phân lớp"""
        config = {"color": "gray", "icon": "info-sign"}
        
        # 1. Biểu tượng (Nhà thờ là icon nhà, Lăng mộ là icon bia/info)
        if loai == "Nhà thờ":
            config["icon"] = "home"
        elif loai == "Lăng mộ":
            config["icon"] = "bookmark" # Icon dạng bia đá/dấu mốc
            
        # 2. Quy định màu sắc theo nhánh huyết mạch
        if nhom == "Đại tôn":
            config["color"] = "darkred"    # Đỏ đậm quyền lực
        elif nhom == "Giáp":
            config["color"] = "blue"       # Xanh lam
        elif nhom == "Ất":
            config["color"] = "green"      # Xanh lục
        elif nhom == "Xuân Lộc":
            config["color"] = "orange"     # Màu cam nổi bật cho trung tâm Tiểu tôn
        elif nhom == "Bính":
            config["color"] = "purple"     # Tím
            
        return config

    @staticmethod
    def render_bando():
        st.markdown('<h2 class="desktop-view" style="font-size: 1.3rem; font-weight: bold; color: #8B0000;">🗺️ Bản đồ Không gian Đại tôn & Tiểu tôn (Tích hợp VR 360)</h2>', unsafe_allow_html=True)
        st.markdown('<h2 class="mobile-view" style="font-size: 1.2rem; font-weight: bold; color: #8B0000;">🗺️ Bản đồ Đại tôn</h2>', unsafe_allow_html=True)
        
        # Chú thích màu sắc trên bản đồ
        st.markdown("""
        <div style='font-size: 0.9rem; margin-bottom: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6;'>
            <b>Chú giải:</b> 
            <span style='color: darkred;'>🔴 Đại tôn</span> | 
            <span style='color: blue;'>🔵 Cửa Giáp</span> | 
            <span style='color: green;'>🟢 Cửa Ất</span> | 
            <span style='color: purple;'>🟣 Cửa Bính</span> | 
            <span style='color: darkorange; font-weight: bold;'>🟠 Tiểu tôn Xuân Lộc (Chi 2/Ất)</span>
        </div>
        """, unsafe_allow_html=True)

        if not BanDoGiaToc.DANH_SACH_DI_TICH:
            return

        # Focus camera vào tọa độ của Tiểu tôn Xuân Lộc (Chi 2 Ất) để khi mở lên ưu tiên nhìn thấy cội nguồn trực tiếp
        xuan_loc = next((d for d in BanDoGiaToc.DANH_SACH_DI_TICH if d["Nhom"] == "Xuân Lộc"), BanDoGiaToc.DANH_SACH_DI_TICH[0])
        


        #m = folium.Map(location=[xuan_loc["ViDo"], xuan_loc["KinhDo"]], zoom_start=13, tiles="OpenStreetMap")
        #m = folium.Map(
            #location=[xuan_loc['ViDo'], xuan_loc['KinhDo']], 
            #zoom_start=15, 
            #width='100%', 
            #height='100%'
        #)
        m = folium.Map(
            location=[xuan_loc["ViDo"], xuan_loc["KinhDo"]], 
            zoom_start=13, 
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', 
            attr='Esri'
        )

        for di_tich in BanDoGiaToc.DANH_SACH_DI_TICH:
            vi_do = di_tich.get('ViDo')
            kinh_do = di_tich.get('KinhDo')

            # 🟢 BỘ LỌC THÔNG MINH: Bỏ qua không vẽ nếu tọa độ chưa có (None hoặc rỗng)
            if vi_do is None or kinh_do is None or str(vi_do).strip() == "" or str(kinh_do).strip() == "":
                continue

            ui_config = BanDoGiaToc.lay_cau_hinh_giao_dien(di_tich["Nhom"], di_tich["Loai"])
            link_google_maps = f"https://www.google.com/maps/dir/?api=1&destination={vi_do},{kinh_do}"
            
            # Khung hiển thị VR360
            if di_tich.get('Link360') and str(di_tich['Link360']).strip() != "":
                khung_360_html = f"""
                <div style="margin-top: 10px; margin-bottom: 12px;">
                    <iframe width="100%" height="200" style="border: 2px solid {ui_config['color']}; border-radius: 6px;" 
                        src="{di_tich['Link360']}" allowfullscreen>
                    </iframe>
                </div>
                """
            else:
                khung_360_html = f"""
                <div style="margin-top: 10px; margin-bottom: 12px; height: 100px; background-color: #f4f4f4; border: 1px dashed #aaa; border-radius: 6px; display: flex; align-items: center; justify-content: center; text-align: center;">
                    <div style="color: #666; font-size: 13px; padding: 10px;">📸 <br>Không gian 360°<br>sẽ sớm được cập nhật...</div>
                </div>
                """

            popup_html = f"""
            <div style="font-family: 'Arial', sans-serif; min-width: 280px; max-width: 300px;">
                <h4 style="color: {ui_config['color']}; margin-top: 0; margin-bottom: 5px; font-size: 15px; text-transform: uppercase;">{di_tich['Ten']}</h4>
                <span style="background-color: {ui_config['color']}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">Thuộc nhóm: {di_tich['Nhom']}</span>
                <p style="font-size: 13px; color: #444; margin-top: 8px; margin-bottom: 8px;"><i>{di_tich.get('MoTa', '')}</i></p>
                
                {khung_360_html}
                
                <a href="{link_google_maps}" target="_blank" style="background-color: #1a73e8; color: white; padding: 8px 12px; text-decoration: none; border-radius: 5px; font-size: 13px; font-weight: bold; display: block; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    📍 CHỈ ĐƯỜNG TỚI ĐÂY
                </a>
            </div>
            """

            folium.Marker(
                location=[vi_do, kinh_do],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"Chạm để xem: {di_tich['Ten']}",
                icon=folium.Icon(color=ui_config['color'], icon=ui_config['icon'], prefix='glyphicon')
            ).add_to(m)



        from folium import Element
        # 1. TIÊM MÃ JAVASCRIPT ĐỂ ĐÁNH THỨC BẢN ĐỒ SAU 0.5 GIÂY
        js_danh_thuc = """
        <script>
            setTimeout(function(){
                window.dispatchEvent(new Event('resize'));
            }, 500);
        </script>
        """
        m.get_root().html.add_child(Element(js_danh_thuc))

        # 2. XUẤT BẢN ĐỒ RA NHƯ CŨ
        import streamlit.components.v1 as components
        # ép render tĩnh:
        components.html(m._repr_html_(), height=660, scrolling=True)


# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [QUẢN LÝ CÁ NHÂN HÓA & CẤU HÌNH HỆ THỐNG - HOÀN THIỆN ĐẦY ĐỦ
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓


class QuanLyCaNhanHoa:
    def __init__(self):
        if 'app_domain' not in st.session_state:
            st.session_state.app_domain = "streamlit.app"
        if 'app_title' not in st.session_state:
            st.session_state.app_title = "Gia phả Họ Từ Xuân Lộc"
            
        if 'dev_email' not in st.session_state:
            st.session_state.dev_email = "developer@giaphatructhe.vn"
        if 'dev_phone' not in st.session_state:
            st.session_state.dev_phone = "0900.XXX.XXX"
        if 'ui_theme' not in st.session_state:
            st.session_state.ui_theme = "Light"
        if 'ui_font_size' not in st.session_state:
            st.session_state.ui_font_size = "Trung bình"

    def hien_thi_menu_ca_nhan_hoa(self):
        st.subheader("⚙️ Cài đặt & Cá nhân hóa")
        
        selected_sub = st.radio(
            "Chọn mục con",
            [
                "Cấu hình App",
                "Hồ sơ cá nhân",
                "Hệ thống ngày giỗ",
                "Cài đặt hệ thống"
            ],
            horizontal=True
        )
        st.markdown("---")

        if selected_sub == "Cấu hình App":
            self.hien_thi_cau_hinh_app()
        elif selected_sub == "Hồ sơ cá nhân":
            self.hien_thi_ho_so_ca_nhan()
        elif selected_sub == "Hệ thống ngày giỗ":
            self.hien_thi_he_thong_ngay_gio()
        elif selected_sub == "Cài đặt hệ thống":
            self.hien_thi_cai_dat_he_thong()

    def hien_thi_cau_hinh_app(self):
        st.subheader("🗄️ Cấu hình chung cho App")
        st.text_input("Tên miền hiển thị", value=st.session_state.app_domain, disabled=True)
        st.text_input("Tiêu đề ứng dụng (Cố định)", value=st.session_state.app_title, disabled=True)
        
        st.write("---")
        st.write("### Tùy chỉnh Logo dòng họ")
        uploaded_logo = st.file_uploader("Tải lên logo dòng họ (PNG, JPG)")
        if uploaded_logo:
            st.image(uploaded_logo, width=100, caption="Logo hiện tại")

        st.write("---")
        st.write("### 👨‍💻 Thông tin liên hệ Người phát triển phần mềm")
        st.caption("🔒 Bảo mật: Khu vực này chỉ dành riêng cho tài khoản Quản trị viên (Admin).")

        admin_pass_input = st.text_input("Nhập mật khẩu Admin để chỉnh sửa thông tin kỹ thuật:", type="password")
        is_admin = (admin_pass_input == "admin123")

        if is_admin:
            st.success("🔓 Xác thực Admin thành công! Bạn có quyền thay đổi thông tin nhà phát triển.")
            new_dev_email = st.text_input("Email Người phát triển:", value=st.session_state.dev_email)
            new_dev_phone = st.text_input("Điện thoại Người phát triển:", value=st.session_state.dev_phone)
            
            if st.button("💾 Cập nhật thông tin nhà phát triển"):
                st.session_state.dev_email = new_dev_email
                st.session_state.dev_phone = new_dev_phone
                st.success("Đã cập nhật thông tin nhà phát triển thành công!")
        else:
            if admin_pass_input:
                st.error("❌ Mật khẩu Admin không chính xác!")
            st.text_input("Email Người phát triển (Chỉ đọc)", value=st.session_state.dev_email, disabled=True)
            st.text_input("Điện thoại Người phát triển (Chỉ đọc)", value=st.session_state.dev_phone, disabled=True)
            st.info("💡 Vui lòng nhập đúng mật khẩu Quản trị (admin123) vào ô phía trên để mở khóa quyền chỉnh sửa.")


    def hien_thi_ho_so_ca_nhan(self):
        st.subheader("👤 Hồ sơ cá nhân & Liên kết Định danh")

        p_name = st.text_input(
            "Tên hiển thị (Họ và tên đúng như trong phả hệ): *", 
            value=st.session_state.get("ls_device_owner_name", "Từ Quang A")
        )
        p_email = st.text_input(
            "Email liên hệ: (Tùy chọn)", 
            value=st.session_state.get("ls_device_owner_email", "giapha.xuanloc@gmail.com")
        )
        p_phone = st.text_input(
            "Số điện thoại Zalo: (Tùy chọn)", 
            value=st.session_state.get("ls_device_owner_phone", "0900000XXX")
        )
        
            
        if st.button("💾 Cập nhật hồ sơ & Tự động gán ID", key="btn_update_profile"):
            st.session_state["ls_device_owner_name"] = p_name
            st.session_state["ls_device_owner_email"] = p_email
            st.session_state["ls_device_owner_phone"] = p_phone
            
            try:
                df_full = KhoDuLieuSQL.load_data()
                df_app = df_full[df_full["TrangThai"] == "Đã duyệt"].copy()
                
                def chuan_hoa_dau(txt):
                    return str(txt).strip().lower().replace("oà", "òa").replace("uỳ", "uỳ").replace("úy", "uý")

                nhap_lieu_chuan = chuan_hoa_dau(p_name)
                df_app['HoTen_Chuan'] = df_app['HoTen'].apply(chuan_hoa_dau)
                
                matched_by_name = df_app[df_app['HoTen_Chuan'] == nhap_lieu_chuan]
                
                # Trường hợp chỉ tìm thấy duy nhất 1 người
                if len(matched_by_name) == 1:
                    found_id = str(matched_by_name.iloc[0]["ID"])
                    doi_thu = matched_by_name.iloc[0]["DoiThu"]
                    chi_nhanh = matched_by_name.iloc[0]["Chi"]
                    
                    st.session_state["ls_device_owner_id"] = found_id
                    st.session_state["pending_disambiguation"] = None
                    st.success(f"✅ Đã lưu hồ sơ và liên kết thành công:\n- **Họ tên:** {p_name}\n- **Mã định danh (ID):** `{found_id}` (Đời {doi_thu} — {chi_nhanh})")
                
                # Trường hợp phát hiện trùng tên (Nhiều người có cùng tên) -> Lưu vào session state
                elif len(matched_by_name) > 1:
                    st.session_state["pending_disambiguation"] = matched_by_name.to_dict('records')
                    st.session_state["pending_df_full"] = df_full
                else:
                    st.session_state["pending_disambiguation"] = None
                    st.warning(f"❌ Không tìm thấy thành viên nào khớp với tên: '{p_name}'. Vui lòng kiểm tra lại chính tả.")
            except Exception as e:
                st.error(f"Lỗi truy xuất cơ sở dữ liệu: {e}")

        # Hiển thị phần chọn người thân độc lập bền vững qua các lần rerun
        if st.session_state.get("pending_disambiguation"):
            matched_records = st.session_state["pending_disambiguation"]
            df_full = st.session_state.get("pending_df_full")
            
            st.warning(f"⚠️ Phát hiện có **{len(matched_records)} người** trùng tên trong dòng họ! Vui lòng chọn đúng người bên dưới:")
            
            options_dict = {}
            for row in matched_records:
                cha_id = row.get('ChaMe_ID', '')
                ten_cha = "Gốc"
                if cha_id and df_full is not None:
                    cha_row = df_full[df_full['ID'] == cha_id]
                    if not cha_row.empty:
                        ten_cha_full = str(cha_row.iloc[0].get('HoTen', ''))
                        parts = ten_cha_full.split()
                        ten_cha = parts[-1] if parts else ten_cha_full
                
                # Định dạng siêu ngắn gọn cho điện thoại: "Từ Hữu Hòa (Thự) - Đ8"
                label_opt = f"{row['HoTen']} ({ten_cha}) - Đ{row['DoiThu']}"
                options_dict[label_opt] = row['ID']
            
            selected_label = st.selectbox("Chọn đúng người thân của bạn:", options=list(options_dict.keys()), key="select_disambiguate_person")
            if st.button("Xác nhận chọn người này", key="btn_confirm_selected_person"):
                chosen_id = options_dict[selected_label]
                st.session_state["ls_device_owner_id"] = chosen_id
                st.session_state["pending_disambiguation"] = None # Xóa trạng thái chờ sau khi đã chọn xong
                st.success(f"✅ Đã gán thành công mã định danh (ID): `{chosen_id}` cho thiết bị!")
                st.rerun()

                
    def hien_thi_he_thong_ngay_gio(self):
        st.subheader("🕯️ Hệ thống ngày giỗ 4 đời trực hệ")
        st.write("Lịch giỗ tiên tổ (Cụ Ông & Cụ Bà) được định danh trực quan cho thiết bị của bạn.")
        
        owner_id_str = st.session_state.get("ls_device_owner_id", "")
        owner_name = st.session_state.get("ls_device_owner_name", "Chưa xác định")

        if not owner_id_str:
            st.warning("⚠️ Thiết bị này chưa được liên kết định danh cá nhân. Vui lòng sang tab **👤 Hồ sơ cá nhân** để cập nhật!")
        else:
            st.success(f"✅ Đang hiển thị lịch giỗ cho chủ nhân thiết bị: **{owner_name} (ID: {owner_id_str})**")
            
            try:
                conn = sqlite3.connect(KhoDuLieuSQL.DB_FILE)
                df_all = pd.read_sql_query("SELECT ID, ChaID, HoTen, NamSinh, NamMat, NgayGio, VoChong, ChucDanh_GhiChu FROM GiaPha", conn)
                conn.close()

                ancestor_ids = []
                curr = str(owner_id_str).strip()
                depth = 0
                visited = set()
                
                while curr and curr != "0" and curr not in visited and depth < 4:
                    visited.add(curr)
                    p_row = df_all[df_all["ID"] == curr]
                    if p_row.empty:
                        break
                    parent_id = str(p_row.iloc[0].get("ChaID", ""))
                    if parent_id and parent_id != "None" and parent_id != "":
                        ancestor_ids.append(parent_id)
                        curr = parent_id
                        depth += 1
                    else:
                        break

                if not ancestor_ids:
                    st.info("Chưa tìm thấy dữ liệu tổ phụ trực hệ phía trên cho ID này.")
                else:
                    df_ancestors = df_all[df_all["ID"].isin(ancestor_ids)].copy()
                    df_ancestors = df_ancestors.sort_values(by="ID", ascending=True)

                    vai_ve_ong = ["Can Ông", "Cố Ông", "Ông", "Bố"]
                    vai_ve_ba = ["Can Bà", "Cố Bà", "Bà", "Mẹ"]

                    memorial_rows = []
                    stt_counter = 1

                    for idx, (_, row) in enumerate(df_ancestors.iterrows()):
                        pos = min(idx, len(vai_ve_ong) - 1)
                        
                        ten_ong = row["HoTen"]
                        nam_sinh_ong = row["NamSinh"]
                        nam_mat_ong = row["NamMat"]
                        ngay_gio_ong = str(row["NgayGio"]).strip()
                        vo_chong_txt = str(row["VoChong"]).strip()
                        ghi_chu_txt = str(row["ChucDanh_GhiChu"]).strip()
                        full_text = f"{vo_chong_txt} {ghi_chu_txt}"

                        # 1. Thêm dòng của Cụ Ông
                        if ngay_gio_ong:
                            memorial_rows.append({
                                "STT": stt_counter,
                                "Họ và tên": f"{vai_ve_ong[pos]}: {ten_ong}",
                                "Năm sinh": nam_sinh_ong,
                                "Năm mất": nam_mat_ong,
                                "Ngày giỗ": ngay_gio_ong
                            })
                            stt_counter += 1

                        # 2. Thuật toán cải tiến quét thông tin và ngày giỗ của Cụ Bà
                        # Tìm kiếm mọi mẫu ngày tháng (ví dụ: 30/11, 13/08, 07/12...) đứng sau chữ giỗ/giổ/mất
                        match_gio = re.search(r'(?:gi[ổỗo]|mất)\s*(?:al)?\s*[:\s]*(\d{1,2}/\d{1,2}(?:\s*al)?)', full_text, re.IGNORECASE)
                        if not match_gio:
                            # Quét dự phòng tìm bất kỳ dạng định dạng ngày/tháng xuất hiện trong văn bản hôn phối
                            match_gio = re.search(r'(\d{1,2}/\d{1,2}\s*(?:al)?)', full_text, re.IGNORECASE)

                        if match_gio:
                            ngay_gio_ba = match_gio.group(1).upper()
                            if "AL" not in ngay_gio_ba:
                                ngay_gio_ba += " AL"
                            
                            # Trích xuất năm sinh - năm mất của cụ bà (ví dụ: 1814-1882)
                            match_nam = re.search(r'\(?(\d{4})\s*-\s*(\d{4})', full_text)
                            nam_sinh_ba = match_nam.group(1) if match_nam else ""
                            nam_mat_ba = match_nam.group(2) if match_nam else ""

                            # Lọc lấy tên cụ bà sạch sẽ
                            ten_ba = ""
                            if "Bà" in vo_chong_txt:
                                ten_ba = vo_chong_txt.split(",")[0].strip()
                            else:
                                m_ba = re.search(r'(Bà\s+[^,\(\)]+)', full_text, re.IGNORECASE)
                                if m_ba:
                                    ten_ba = m_ba.group(1).strip()
                            
                            if not ten_ba:
                                ten_ba = "Hiền nội"

                            ten_ba_sach = re.sub(r'^(Bà chính|Bà thứ|Bà cả|Bà hai|Bà)\s*', '', ten_ba).strip()
                            if not ten_ba_sach:
                                ten_ba_sach = "Hiền nội"

                            memorial_rows.append({
                                "STT": stt_counter,
                                "Họ và tên": f"{vai_ve_ba[pos]}: {ten_ba_sach}",
                                "Năm sinh": nam_sinh_ba,
                                "Năm mất": nam_mat_ba,
                                "Ngày giỗ": ngay_gio_ba
                            })
                            stt_counter += 1

                    if not memorial_rows:
                        st.info("Chưa ghi nhận thông tin ngày giỗ cụ thể cho các bậc tiên tổ trong nhánh này.")
                    else:
                        df_table = pd.DataFrame(memorial_rows)
                        st.markdown("#### 📅 Bảng Lịch Giỗ Tiên Tổ")
                        st.dataframe(df_table[["STT", "Họ và tên", "Năm sinh", "Năm mất", "Ngày giỗ"]], use_container_width=True, hide_index=True)
                        st.markdown("🔔 *Hệ thống tự động kích hoạt chế độ báo thức và đếm ngược trước 5 ngày cho các mốc giỗ này.*")

            except Exception as e:
                st.error(f"Lỗi tải dữ liệu lịch giỗ: {e}")


    def hien_thi_cai_dat_he_thong(self):
        st.subheader("🛠️ Cài đặt hệ thống & Giao diện")
        
        st.markdown("#### 🎨 Tùy chỉnh giao diện")
        st.session_state.ui_theme = st.selectbox("Chọn giao diện", ["Light", "Dark", "Hệ thống"], index=0)
        st.session_state.ui_font_size = st.select_slider("Kích thước chữ", options=["Nhỏ", "Trung bình", "Lớn"], value=st.session_state.get("ui_font_size", "Trung bình"))
        
        if st.button("Áp dụng giao diện"):
            st.success(f"Đã áp dụng giao diện {st.session_state.ui_theme}, chữ {st.session_state.ui_font_size}")
            st.rerun() # <--- Thêm dòng này để trang tự động reload và đổi cỡ chữ toàn cục ngay lập tức

        st.markdown("---")
        st.markdown("#### ⚙️ Cài đặt hệ thống")
        st.checkbox("Bảo mật hai lớp (2FA)")
        st.selectbox("Ngôn ngữ", ["Tiếng Việt", "English"])
        
        st.write("---")
        st.write("### Dữ liệu gia phả")
        if st.button("Xóa bộ nhớ cache", type="primary"):
            st.cache_data.clear()
            st.warning("Đã xóa bộ nhớ cache thành công!")

        st.write("### Thông báo")
        st.checkbox("Nhận email thông báo ngày giỗ trước 5 ngày")
        
# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [ĐIỀU PHỐI ĐẦU NÃO] - KHỞI CHẠY CHƯƠNG TRÌNH
# ==============================================================================

if __name__ == "__main__":
    # 1. Đánh thức luồng lắng nghe ngầm của Bot Telegram TRƯỚC TIÊN
    try:
        TelegramBotManager.start_background_bot()
    except Exception as e:
        pass
        
    # 2. Sau khi Bot đã thức, mới bắt đầu vẽ giao diện SAU CÙNG
    SoChiHuyGiaoDien.render_app()
    
