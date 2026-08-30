# ==============================================================================
# GIA PHẢ ĐIỆN TỬ DÒNG HỌ TỪ XUÂN LỘC - CHUẨN ĐỊNH DANH HỢP NHẤT
# PHIÊN BẢN APP21 TÍCH HỢP TỐI ƯU TOÀN DIỆN CHO ĐIỆN THOẠI (MOBILE-FIRST)
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
import re
import os
from PIL import Image
from graphviz import Digraph
from pathlib import Path


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
            keyword_list = ["phạp tự", "không có con", "tảo vong", "tảo một", "chết sớm"]
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

            cursor.execute("SELECT COUNT(*) FROM GiaPha")
            count = cursor.fetchone()[0]
     
            if count == 0:
                raw_data = [


                    # ==========================================================
                    # ĐỜI THỨ 1 & 2: THỦY TỔ VÀ CÁC CỤ ĐỨNG ĐẦU CỬA
                    # ==========================================================
                    ("000.01.0.001", None, "Từ Dương Đốc", "Huy Cán", "Bà Trần Thị Niêm", "", "", "3/12 AL", "Thầy thuốc y dược tế sinh. Con đầu ông Từ Trí Sức (đời 6 Đại tôn), cùng mẹ lên làng Hoa Cử lập nghiệp.", "", ""),
                    ("100.02.0.001", "000.01.0.001", "Từ Hữu Trí", "", "Bà Đào Thị Điểm", "", "", "28/5 AL", "Đứng đầu cửa Giáp. Làm chức Tri điền.", "", ""),
                    ("200.02.0.002", "000.01.0.001", "Từ Hữu Mưu", "", "Bà Trần Thị Dinh, Bà Trần Thị Đài", "", "", "", "Đứng đầu cửa Ất. Làm nghề tri điện kiêm tổng trưởng.", "", ""),
                    ("000.02.1.003", "000.01.0.001", "Từ Thị Hằng", "", "Lấy chồng", "", "", "", "Lấy chồng", "", ""),

                    # ==========================================================
                    # ĐỜI THỨ 3: CÁC CỤ ĐỨNG ĐẦU CHI
                    # ==========================================================
                    ("110.03.0.001", "100.02.0.001", "Từ Hữu Liện", "", "Bà Trần Thị Tần", "", "", "11/12 AL", "Con đầu cụ Trí. Làm chức Huyện Thừa.", "", ""),
                    ("120.03.0.002", "100.02.0.001", "Từ Hữu Dực", "", "Bà Ngô Thị Nữ Tắc", "", "", "", "Con thứ 2 cụ Trí.", "", ""),
                    ("130.03.0.003", "100.02.0.001", "Từ Hữu Lạng", "", "Bà Trần Thị Yêm", "", "", "", "Con thứ 3 cụ Trí. Tri điện nội chức.", "", ""),
                    ("100.03.0.004", "100.02.0.001", "Nguyễn Bá Hoan", "", "", "", "", "Mất 01/8 AL", "", "Con nuôi", ""),
                    ("240.03.0.005", "200.02.0.002", "Từ Hữu Màn", "", "Bà Trần Thị Lụ", "", "", "", "Con đầu cụ Mưu. Thầy thuốc y dược tế sinh.", "", ""),
                    ("250.03.0.006", "200.02.0.002", "Từ Hữu Hùng", "", "Bà Trần Thị Bích", "", "", "", "Con thứ 2 cụ Mưu. Tri hộ kiêm chính đạo nghĩa Nam.", "", ""),
                    ("260.03.0.007", "200.02.0.002", "Từ Hữu Lân", "", "Bà Trần Thị... (Hiệu Tiệp Ảnh)", "", "", "", "Con thứ 3 cụ Mưu. Ưu binh đội trưởng.", "", ""),
                    ("270.03.0.008", "200.02.0.002", "Từ Hữu Lạc", "", "Bà Hồ Thị Hiệu, Bà Hà Thị Hiệu Từ", "", "", "", "Con thứ 4 cụ Mưu. Ban cai đội phó cơ chưởng ngọc hầu.", "", ""),

                    # ==========================================================
                    # ĐỜI THỨ 4: PHÂN RẼ VÀO CÁC PHÁI
                    # ==========================================================
                    ("111.04.0.001", "110.03.0.001", "Từ Hữu Di", "", "Bà Ngô Thị Tố (Hiệu Trang Nhạ)", "", "", "", "Con cụ Liện. Thợ rèn.", "", ""),
                    ("122.04.0.002", "120.03.0.002", "Từ Hữu Kỵ", "", "Bà Ngô Thị Lân", "", "", "", "Con đầu cụ Dực. Thầy thuốc.", "", ""),
                    ("123.04.0.003", "120.03.0.002", "Từ Hữu Tương", "", "Bà Đào Thị Đính", "", "", "", "Con thứ 2 cụ Dực. Ưu binh đội trưởng.", "", ""),
                    ("120.04.0.004", "120.03.0.002", "Từ Hữu Tạc", "", "Bà Nguyễn Thị Trân", "", "", "", "Con thứ 3 cụ Dực. Thợ rèn.", "Phạp tự", ""),
                    ("124.04.0.005", "120.03.0.002", "Từ Hữu Tỉnh", "Cố Phùng", "Bà Trần Thị Phi", "1812", "1885", "13/4 AL", "Con thứ 4 cụ Dực. Đại phú, thọ 74 tuổi. Vợ là Bà Trần Thị Phi (Bà Cố Phùng), (1814-1882, giổ 30/11)", "", ""),
                    ("120.04.0.006", "120.03.0.002", "Từ Hữu Ẩm", "", "Bà Trương Thị Tư, Bà Nguyễn Thị Chiên", "", "", "", "Con thứ 5 cụ Dực.", "", ""),
                    ("120.04.0.007", "120.03.0.002", "Từ Hữu Lộc", "", "", "", "", "", "Con thứ 5 cụ Dực.", "Tảo vong", ""),
                    ("120.04.0.008", "120.03.0.002", "Từ Hữu Phú", "", "", "", "", "", "Con thứ 5 cụ Dực.", "Tảo vong", ""),
                    ("135.04.0.009", "130.03.0.003", "Từ Hữu Tình", "", "Bà Ngô Thị Phụng", "", "", "", "Con cụ Lạng. Thí trúng nhị trường.", "", ""),
                    ("130.04.0.010", "130.03.0.003", "Từ Hữu Tính", "", "", "", "", "", "Con cụ Lạng.", "Chết sớm", ""),
                    ("246.04.0.011", "240.03.0.005", "Từ Hữu Hiển", "", "Bà Ngô Thị... (Hiệu Thao Chuyết)", "", "", "", "Con đầu cụ Màn. Làm nghề ruộng.", "", ""),
                    ("240.04.0.012", "240.03.0.005", "Từ Hữu Kiến", "", "", "", "", "", "Con cụ Màn", "Chết sớm", ""),             
                    ("240.04.1.013", "240.03.0.005", "Từ Thị Dục", "", "", "", "", "", "Con cụ Màn", "Chết sớm", ""),   
                    ("240.04.0.014", "240.03.0.005", "Từ Hữu Thông", "", "", "", "", "", "Con cụ Màn", "Tảo một", ""),
                    ("240.04.0.015", "240.03.0.005", "Từ Hữu Minh", "", "", "", "", "", "Con cụ Màn", "Tảo vong", ""), 
                    ("257.04.0.016", "250.03.0.006", "Từ Hữu Linh", "", "Bà Trần Thị Dương", "", "", "", "Con cụ Hùng.", "", ""),
                    ("258.04.0.017", "250.03.0.006", "Từ Hữu Cảo", "", "Bà Trần Thị Phổ", "", "", "", "Con thứ 2 cụ Hùng.", "", ""),
                    ("269.04.0.018", "260.03.0.007", "Từ Hữu Niên", "", "Bà Trần Thị Quỵ", "", "", "", "Con cụ Lân. Lý trưởng.", "", ""),
                    ("260.04.0.019", "260.03.0.007", "Từ Hữu Điền", "", "Bà Đặng Thị Thành", "", "", "", "Khâm sai đội lệ.", "Không có con", ""),
                    ("260.04.0.020", "260.03.0.007", "Từ Hữu Trung", "", "", "", "", "", "Con cụ Lân.", "Tảo vong", ""),
                    ("270.04.0.021", "270.03.0.008", "Từ Hữu Thận", "", "Bà Nguyễn Thị Thề", "", "", "", "Con cụ Lạc.", "", ""),
                    ("270.04.0.022", "270.03.0.008", "Từ Hữu Thung", "", "", "", "", "", "Con cụ Lạc.", "Tảo vong", ""),
                    ("270.04.1.023", "270.03.0.008", "Từ Thị Thuyết", "", "", "", "", "", "Con cụ Lạc.", "Tảo vong", ""),


                    # ==========================================================
                    # ĐỜI THỨ 5
                    # ==========================================================
                    ("111.05.0.001", "111.04.0.001", "Từ Hữu Loan", "", "Bà cả Thái Thị Thiều, Bà thứ Ngô Thị Thi", "", "", "", "Con cụ Di. Sinh hạ: Từ Hữu Thư, Từ Hữu Thuyên (chết sớm), Từ Thị Thuế (chết sớm), Từ Thị Bức (chết sớm), Từ Thị Hiến (tảo vong), Từ Thị Đỏ (tảo vong).", "", ""),
                    ("111.05.0.002", "111.04.0.001", "Từ Hữu Kiệu", "", "Bà cả Trần Thị Sum, Bà thứ Nguyễn Thị Trung", "", "", "", "Con thứ 2 cụ Di. Sinh hạ: Từ Hữu Ngạnh, Từ Thị Sam.", "", ""),               
                    ("111.05.0.003", "111.04.0.001", "Từ Hữu Phượng", "", "Bà Trần Thị Bỉnh", "", "", "", "Con thứ 3 cụ Di. Sinh hạ: Từ Hữu Khánh, Từ Hữu Xướng (chết), Từ Hữu Sam, Từ Hữu Thậm (chết), Từ Hữu Cội, Từ Hữu Đỏ (tảo vong).", "", ""),
                    ("111.05.0.004", "111.04.0.001", "Từ Hữu Điều", "", "Bà Nguyễn Thị Thiều", "", "", "", "Con thứ 4 cụ Di. Sinh hạ: Từ Thị Kiệm.", "Phạp tự", ""),
                    ("122.05.0.005", "122.04.0.002", "Từ Hữu Tiển", "", "Bà Nguyễn Thị Kỷ", "", "", "", "Con cụ Kỵ. Sinh hạ: Từ Hữu Toát, Từ Thị Tôi (tảo vong).", "", ""),
                    ("122.05.0.006", "122.04.0.002", "Từ Hữu Thạch", "", "", "", "", "", "Con cụ Kỵ.", "Chết sớm", ""),      
                    ("122.05.0.007", "122.04.0.002", "Từ Hữu Ngọc", "", "", "", "", "", "Con cụ Kỵ.", "Chết sớm", ""),       
                    ("122.05.0.008", "122.04.0.002", "Từ Hữu Ngà", "", "Bà Ngô Thị Quỳ", "", "", "", "Con thứ 2 cụ Kỵ. Sinh hạ: Từ Hữu Giá (tảo một).", "", ""),             
                    ("122.05.0.009", "122.04.0.002", "Từ Hữu Lầu", "", "Bà Trần Thị Đị", "", "", "", "Con cụ Kỵ. Sinh hạ: Từ Hữu Mận, Từ Hữu Yêm (tảo một), Từ Hữu Bạo (tảo một).", "", ""),
                    ("122.05.0.010", "122.04.0.002", "Từ Hữu Ngân", "", "", "", "", "", "Con cụ Kỵ.", "Chết sớm", ""),
                    ("122.05.0.011", "122.04.0.002", "Từ Chi Cảnh", "", "", "", "", "", "Con cụ Kỵ.", "Chết sớm", ""),
                    ("123.05.0.012", "123.04.0.003", "Từ Hữu Nghị", "", "Bà cả Đào Thị..., Bà thứ Nguyễn Thị Chói", "", "", "", "Con đầu cụ Tương. Sinh hạ: Từ Thị Thái (tảo một), Từ Hữu Rượng (chết sớm), Từ Thị (lấy chồng họ Nguyễn Nhim giữa làng), Từ Thị (lấy chồng họ Trần Kép giữa làng).", "Phạp tự", ""),
                    ("123.05.0.013", "123.04.0.003", "Từ Hữu Vọ", "", "Bà cả Nguyễn Thị Sắc, Bà thứ Phan Thị Thụ", "", "", "", "Con thứ 2 cụ Tương. Sinh hạ: Từ Thị Chiêm (tảo vong), Từ Dái Chiêm (tảo vong).", "Phạp tự", ""),
                    ("123.05.0.014", "123.04.0.003", "Từ Hữu Toàn", "", "Bà Trần Thị Chẹc", "", "", "", "Con thứ 3 cụ Tương. Sinh hạ: Từ Hữu Vẹn, Từ Hữu Vẹ, Từ Hữu Cu, Từ Thị Chích (tảo vong).", "", ""),
                    ("120.05.1.015", "120.04.0.004", "Từ Thị Tân", "", "", "", "", "", "Con cụ Tạc.", "tảo vong", ""),
                    ("120.05.1.016", "120.04.0.004", "Từ Thị Lụ", "", "", "", "", "", "Con cụ Tạc.", "tảo vong", ""),
                    ("124.05.0.017", "124.04.0.005", "Từ Hữu Bường", "", "", "", "", "", "Con cụ Tỉnh.", "Chết sớm", ""),
                    ("124.05.1.018", "124.04.0.005", "Từ Thị Bẹn", "", "Trần Song", "", "", "", "Con cụ Tỉnh. Lấy ông Trần Song trong làng", "", ""),
                    ("124.05.1.019", "124.04.0.005", "Từ Thị Phấn", "", "Trần Ích", "", "", "", "Con cụ Tỉnh. Lấy Trần Ích trong làng", "", ""),
                    ("124.05.0.020", "124.04.0.005", "Từ Hữu Chấn", "Ông Cố Thoan", "Bà Nguyễn Thị Thuyết", "1847", "1913", "05/03", "Con cụ Tỉnh. Vợ là Bà Nguyễn Thị Thuyết (người họ Nguyễn Văn Hương), (1853-1919, giổ 12/01). Sinh hạ: Từ Thị Mận (lấy ông Nguyễn Thoan ở Điền xá), Từ Thị Hân (lấy ông Nguyễn Liêm giữa làng), Từ Thị Phú (lấy ông Nguyễn Thâm giữa làng), Từ Thị Cầm (lấy ông Nguyễn Bá Mủm giữa làng), Từ Thị Đích (lấy ông Trần Thọ Bành Hương), Từ Thị Túc (lấy ông Trần Định trửa làng), Từ Hữu Đức (tảo một), Từ Hữu Đìch (tảo một), Từ Thị Toa - Thị Đỏ (tảo một).", "Phạp tự", ""),
                    ("124.05.0.021", "124.04.0.005", "Từ Hữu Nhin", "Cố Điệng", "Bà Nguyễn Thị Xuy", "1861", "1907", "17/09", "Con cụ Tỉnh. Vợ là Bà Nguyễn Thị Xuy (con cố Xưng),(1862-1942, giổ 13/08). Sinh hạ: Từ Thị Tuần (lấy ông Bang Mỹ ở Yên Vinh - Trạo Nha), Từ Thị Hợi (lấy ông Thái Mạo ở Xuân Mai), Từ Thị Thao (lấy ông Trần Lê Cớt giữa làng), Từ Hữu Chính, Từ Thị Năm (lấy ông Trần Lạc ở Yên Đồng), Từ Hữu Giáo, Từ Hữu Thí.", "", ""),       
                    ("120.05.0.022", "120.04.0.006", "Từ Hữu Hưng", "", "", "", "", "", "Con cụ Ẩm.", "Tảo một", ""),
                    ("120.05.1.023", "120.04.0.006", "Từ Thị Chiêm", "", "", "", "", "", "Con cụ Ẩm.", "Tảo vong", ""),
                    ("120.05.1.024", "120.04.0.006", "Từ Thị Diền", "", "", "", "", "", "Con cụ Ẩm.", "Tảo vong", ""),
                    ("135.05.0.025", "135.04.0.009", "Từ Hữu Hồng", "", "Bà Trần Thị Côi", "", "", "", "Con cụ Tình. Thí trúng nhị trường - chức vụ tự xã. Sinh hạ: Từ Hữu Thống, Từ Hữu Thính, Từ Thị Thuý (chết sớm).", "", ""),
                    ("135.05.0.026", "135.04.0.009", "Từ Hữu Bằng", "", "Bà cả Trần Thị Nhuận, Bà thứ Nguyễn Thị Chỉ", "", "", "", "Con thứ 2 cụ Tình. Làm nghề dạy học, kiêm thư ký làng xã. Sinh hạ: Từ Thị Điển (lấy chồng về Khô Nội), Từ Thị... (lấy ông Trần Lại trong làng), Từ Thị... (lấy ông Lượng Nhạc Trảo Nha), Từ Thị Lạp (lấy ông Trần Bách trong làng), Từ Hữu Bối (ông Phụ), Từ Hữu Triết, Từ Thị Bổn (lấy người Đại Lộc), Từ Thị Cháu (chết).", "", ""),
                    ("135.05.0.027", "135.04.0.009", "Từ Hữu Lập", "", "Bà chính Trần Thị Tự, bà thứ Bùi Thị Liên", "", "", "", "Con thứ 3 cụ Tình. Làm nghề thầy thuốc kiêm xã hộ giám tri. Sinh hạ: Từ Hữu Quán, Từ Hữu Thường (chết sớm), Từ Hữu Cự (chết sớm), Từ Hữu Kính (chết sớm), Từ Hữu Ngoạn (hán tự thông minh, chết sớm), Từ Hữu Xán (ông Cố Hạo), Từ Hữu Đỏ (tảo vong).", "", ""),
                    ("135.05.0.028", "135.04.0.009", "Từ Hữu Cống", "", "", "", "", "", "Con cụ Tình", "Chết sớm", ""),   
                    ("246.05.0.029", "246.04.0.011", "Từ Hữu Khảng", "", "Bà cả Nguyễn Thị Sự, Bà thứ Trần Thị Thượng", "", "", "", "Con cụ Hiển. Sinh hạ: Từ Hữu Đỏ (tảo vong); 6 con gái gồm: Đỏ, Hảo, Đỏ, Đỏ, Chẹch, Thông (đều tảo vong).", "Phạp tự", ""),     
                    ("246.05.0.030", "246.04.0.011", "Từ Hữu Khái", "Cả, Kỳ", "Bà Nguyễn Thị Yến", "", "", "", "Con thứ 2 cụ Hiển. Sinh hạ: Từ Hữu Hoè, Từ Hữu Trấn, Từ Hữu Ất, Từ Hữu Dự, Từ Thị, Từ Hữu Đỏ, Từ Hữu Vinh, Từ Hữu Bổng; 3 con gái gồm: Thị Đỏ, Đỏ, Đỏ (đều tảo vong).", "", ""),           
                    ("246.05.1.031", "246.04.0.011", "Từ Thị Hân", "", "", "", "", "", "Con cụ Hiển.", "Chết sớm", ""),
                    ("257.05.0.032", "257.04.0.016", "Từ Hữu Kiệt", "", "", "", "", "", "Con cụ Linh.", "Phạp tự", ""),
                    ("257.05.0.033", "257.04.0.016", "Từ Hữu Quýnh", "", "Bà Nguyễn Thị Cưu", "", "", "", "Con thứ 2 cụ Linh. Sinh hạ: Từ Hữu Thạc, Từ Hữu Đỏ (tảo vong).", "", ""),
                    ("257.05.1.034", "257.04.0.016", "Từ Thị Thước", "", "", "", "", "", "Con cụ Linh", "Chết sớm", ""),                  
                    ("257.05.0.035", "257.04.0.016", "Từ Hữu Cu", "", "", "", "", "", "Con cụ Linh", "Tảo vong", ""),
                    ("257.05.1.036", "257.04.0.016", "Từ Thị Hinh", "", "", "", "", "", "Con cụ Linh", "Tảo vong", ""),
                    ("257.05.1.037", "257.04.0.016", "Từ Thị Ky", "", "", "", "", "", "Con cụ Linh", "Tảo một", ""), 
                    ("258.05.0.038", "258.04.0.017", "Từ Hữu Trinh", "", "Bà Trần Thị Thầu", "", "", "", "Con đầu cụ Cảo. Sinh hạ: Từ Hữu Cuộc, Từ Hữu Ức (tảo một), Từ Hữu Tùy, Từ Hữu Khôi (tảo vong), Từ Thị Liên (tảo vong), Từ Thị Cẩm (tảo vong).", "", ""),               
                    ("258.05.0.039", "258.04.0.017", "Từ Hữu Triền", "", "", "", "", "", "Con cụ Cảo.", "Chết sớm", ""),
                    ("258.05.0.040", "258.04.0.017", "Từ Hữu Liên", "", "", "", "", "", "Con cụ Cảo.", "Chết sớm", ""),           
                    ("258.05.0.041", "258.04.0.017", "Từ Hữu Tranh", "", "Bà cả Trần Thị Khoá, bà thứ Trần Thị Tiết", "", "", "", "Con thứ 2 cụ Cảo. Sinh hạ: Từ Hữu Do, Từ Thị Tốn.", "", ""),
                    ("258.05.0.042", "258.04.0.017", "Từ Hữu Phối", "", "", "", "", "", "Con cụ Cảo.", "Chết sớm", ""),
                    ("258.05.0.043", "258.04.0.017", "Từ Hữu Đoàn", "", "", "", "", "", "Con cụ Cảo.", "Tảo vong", ""),
                    ("258.05.0.044", "258.04.0.017", "Từ Hữu Trừng", "", "Bà Ngô Thị Sung", "", "", "", "Con cụ Cảo. Sinh hạ: Từ Hữu Xuyến (tảo một), Từ Hữu Luyến (tảo một), Từ Hữu Son (tảo một); 7 con gái gồm: Xuân, Biện, Đỏ, Sáu, Thất, Phiến, Ú (đều chết).", "", ""),
                    ("258.05.0.045", "258.04.0.017", "Từ Hữu Điều", "", "Bà Ngô Thị Lùc", "", "", "", "Con cụ Cảo. Sinh hạ: Từ Hữu Chuyền, Từ Hữu Chuân, Từ Hữu Đích (tảo một), Từ Hữu Nhận (tảo một).", "", ""),
                    ("258.05.0.046", "258.04.0.017", "Từ Hữu Kiên", "", "Bà cả Lê Thị Hương, bà thứ Trương Thị Yến", "", "", "", "Con cụ Cảo. Làm phó tổng và dạy học Hán văn. Sinh hạ: Từ Hữu Huân, Từ Hữu Giảng, Từ Hữu Điển, Từ Hữu Dái (tảo một); 4 con gái gồm: Dản, Bẹn, Chẹc, Lục (đều tảo vong).", "", ""),
                    ("258.05.0.047", "258.04.0.017", "Từ Hữu Cồng", "", "Bà cả Trần Thị Thú, Bà thứ Trần Thị Bình", "", "", "", "Con cụ Cảo. Sinh hạ: Từ Hữu Bồng; 5 con trai gồm: Cốc, Bành, Phùng, Đích, Kiêm; 3 con gái gồm: Chẹc, Đốc, Kép (đều chết sớm).", "", ""),
                    ("269.05.0.048", "269.04.0.018", "Từ Hữu Bộ", "", "", "", "", "", "Con cụ Niên", "Tảo vong", ""),
                    ("270.05.0.049", "270.04.0.021", "Từ Hữu Dinh", "", "Bà: Không biết rõ", "", "", "", "Con cụ Thận. Làm lý trưởng kiêm chức tri xã, nghỉ việc đi học tổng Cổ Giác. Sinh hạ: 2 con trai (1 con trai chết, 1 con trai theo mẹ về họ ngoại làm ở đâu tung tích không rõ).", "di cư, không rõ", ""),
                    ("270.05.1.050", "270.04.0.021", "Từ Thị Trù", "", "", "", "", "", "Con cụ Thận.", "Tảo vong", ""),

                    # ==========================================================
                    # ĐỜI 6
                    # ==========================================================
                    # ------------------------------------
                    # CHI 1
                    # ------------------------------------    
                    ("111.06.0.001", "111.05.0.001", "Từ Hữu Thư", "", "Bà Ngô Thị Kim", "", "", "", "Con cụ Loan. Lý trưởng. Sinh hạ: Từ Hữu Phiệt, Từ Thị (lấy cố Trần Cớt trong làng), Từ Thị (lấy ông Trần Chước trong làng), Từ Hữu Vinh (tảo một), Từ Hữu Vượng (tảo một), Từ Hữu Thuận (tảo một), Từ Hữu Đốc (tảo một).", "", ""),                  
                    ("111.06.0.002", "111.05.0.001", "Từ Hữu Thuyên", "", "", "", "", "", "Con cụ Loan.", "Chết sớm", ""),
                    ("111.06.1.003", "111.05.0.001", "Từ Thị Thuế", "", "", "", "", "", "Con cụ Loan.", "Chết sớm", ""),                    
                    ("111.06.1.004", "111.05.0.001", "Từ Thị Bức", "", "", "", "", "", "Con cụ Loan.", "Chết sớm", ""),
                    ("111.06.1.005", "111.05.0.001", "Từ Thị Hiến", "", "", "", "", "", "Con cụ Loan.", "Chết sớm", ""),                 
                    ("111.06.0.006", "111.05.0.002", "Từ Hữu Ngạnh", "", "Bà Thái Thị Mạnh", "", "", "", "Con cụ Kiệu. Sinh hạ: Từ Hữu Lâm, Từ Hữu Tâm, Từ Hữu Lam (tảo một), Từ Hữu Liêm (tảo một).", "", ""),
                    ("111.06.1.007", "111.05.0.002", "Từ Thị Sam", "", "Không rõ", "", "", "", "Con cụ Kiệu.", "", ""),
                    ("111.06.0.008", "111.05.0.003", "Từ Hữu Khánh", "", "Bà Trần Thị Câu", "", "", "", "Con cụ Phượng. Sinh hạ: Từ Hữu Sáng, Từ Thị (lấy cố Hiến xã Thạch Liên), Từ Thị Chẹc (tảo một), Từ Thị (lấy chồng về Yên Đồng), Từ Thị Năm (tảo một), Từ Hữu Xích.", "", ""),
                    ("111.06.0.009", "111.05.0.003", "Từ Hữu Xướng", "", "", "", "", "", "Con cụ Phượng.", "Chết sớm", ""),
                    ("111.06.0.010", "111.05.0.003", "Từ Hữu Sum", "", "Bà Trần Thị Cơ", "", "", "", "Con cụ Phượng. Sinh hạ: Từ Hữu Toại, Từ Thị (lấy cố Sị trong làng), Từ Hữu Nghi, Từ Thị (lấy ông cựu Thuyên trong làng), Từ Thị (lấy ông Trần Yểu trong làng), Từ Thị Sáu (lấy ông Cửu Tường trong làng), Từ Thị (lấy ông Trung Hiếu trong làng), Từ Hữu Luận.", "", ""),  
                    ("111.06.0.011", "111.05.0.003", "Từ Hữu Thậm", "", "", "", "", "", "Con cụ Phượng.", "Chết sớm", ""),
                    ("111.06.0.012", "111.05.0.003", "Từ Hữu Cội", "", "Bà Trần Thị Dênh", "", "", "", "Con cụ Phượng. Sinh hạ: Từ Thị Dị (lấy ông Trần Đinh trong làng), Từ Hựu Lệ, Từ Thị (lấy ông Đặng Cầu quanh làng), Từ Thị (lấy ông Trần Thảng trong làng), Từ Hữu Nghĩa, Từ Hữu Khí (chết sớm), Từ Hữu Trề (chết sớm), Từ Thị Tám (lấy ông Trần Hoàn trong làng), Từ Hữu Lộc (tảo vong).", "", ""),
                    ("111.06.1.013", "111.05.0.004", "Từ Thị Kiệm", "", "Không rõ", "", "", "", "Con cụ Điều.", "", ""),

                    # ------------------------------------
                    # CHI 2
                    # ------------------------------------ 
                    ("122.06.0.014", "122.05.0.005", "Từ Hữu Toát", "", "Bà Trần Thị Náu", "", "", "", "Con cụ Tiển. Sinh hạ: Từ Hữu Duyệt, Từ Thị Em (lấy ông Trần Thế trong làng), Từ Hữu Hợi, Từ Hữu Điếm (tảo vong), Từ Thị Đỏ (tảo vong).", "", ""),
                    ("122.06.1.015", "122.05.0.005", "Từ Thị Tôi", "", "", "", "", "", "Con cụ Tiển", "Tảo vong", ""),
                    ("122.06.0.016", "122.05.0.008", "Từ Hữu Giá", "", "", "", "", "", "Con cụ Ngà.", "Tảo một", ""),
                    ("122.06.0.017", "122.05.0.009", "Từ Hữu Mận", "", "Bà Lê Thị Út", "", "", "", "Con cụ Lầu. Sinh hạ: Từ Thị Mai (lấy Trần Chinh trong làng), Từ Hữu Khai, Từ Hữu Lai, Từ Hữu Đỏ (tảo vong).", "", ""),
                    ("122.06.0.018", "122.05.0.009", "Từ Hữu Yêm", "", "", "", "", "", "Con cụ Lầu.", "Tảo một", ""),
                    ("122.06.0.019", "122.05.0.009", "Từ Hữu Bạo", "", "", "", "", "", "Con cụ Lầu.", "Tảo một", ""),  
                    ("123.06.1.020", "123.05.0.012", "Từ Thị Thái", "", "", "", "", "", "Con cụ Nghị.", "Tảo một", ""),
                    ("123.06.0.021", "123.05.0.012", "Từ Hữu Rượng", "", "", "", "", "", "Con cụ Nghị.", "Chết sớm", ""),
                    ("123.06.1.022", "123.05.0.012", "Từ Thị ...", "", "Lấy họ Nguyễn Nhim", "", "", "", "Con cụ Nghị.", "", ""),
                    ("123.06.1.023", "123.05.0.012", "Từ Thị ...", "", "Lấy họ Trần Kép", "", "", "", "Con cụ Nghị.", "", ""),
                    ("123.06.1.024", "123.05.0.013", "Từ Thị Chiêm", "", "", "", "", "", "Con cụ Vọ", "Tảo vong", ""),
                    ("123.06.0.025", "123.05.0.013", "Từ Dái Chiêm", "", "", "", "", "", "Con cụ Vọ", "Chết sớm", ""),
                    ("123.06.0.026", "123.05.0.014", "Từ Hựu Vẹn", "", "Bà Trần Thị Diệp", "", "", "", "Con cụ Toàn. Sinh hạ: Từ Hữu Kiệp, Từ Hữu Điệp, Từ Thị Ba (lấy chồng về Thạch Liên), Từ Hữu Dữu (chết sớm), Từ Thị Chút (lấy ông Trần Tuần Dư Nại), Từ Thị Tỷ (lấy chồng về Tiến Lộc).", "", ""),
                    ("123.06.0.027", "123.05.0.014", "Từ Hữu Vẹ", "", "Bà Trần Thị Ba", "", "", "", "Con cụ Toàn. Sinh hạ: Từ Thị Xin (chết sớm).", "Phạp tự", ""),
                    ("123.06.0.028", "123.05.0.014", "Từ Hữu Cu", "", "", "", "", "", "Con cụ Toàn", "Chết sớm", ""),
                    ("123.06.1.029", "123.05.0.014", "Từ Thị Chích", "", "", "", "", "", "Con cụ Toàn", "Tảo vong", ""),                
                    ("124.06.1.030", "124.05.0.020", "Từ Thị Mận", "", "Nguyễn Thoan", "", "", "", "Con cụ Chấn. Lấy ông Nguyễn Thoan ở Trường Thành - Đồng Lộc", "", ""),
                    ("124.06.1.031", "124.05.0.020", "Từ Thị Hân", "", "Nguyễn Liêm", "", "", "", "Con cụ Chấn. Lấy ông Nguyễn Liêm ở giữa làng", "", ""),
                    ("124.06.1.032", "124.05.0.020", "Từ Thị Phú", "", "Nguyễn Thẩm", "", "", "", "Con cụ Chấn. Lấy ông Nguyễn Thẩm ở giữa làng", "", ""),
                    ("124.06.1.033", "124.05.0.020", "Từ Thị Cầm", "", "Nguyễn Ẩm", "", "", "", "Con cụ Chấn. Lấy ông Nguyễn Ẩm ở Triền Lối", "", ""),
                    ("124.06.1.034", "124.05.0.020", "Từ Thị Đích", "", "Trần Thọ Bành", "", "", "", "Con cụ Chấn. Lấy ông Trần Thọ Bành ở Triền Lối", "", ""),
                    ("124.06.1.035", "124.05.0.020", "Từ Thị Túc", "", "Trần Định", "", "", "", "Con cụ Chấn. Lấy ông Nguyễn Định ở giữa làng", "", ""),
                    ("124.06.0.036", "124.05.0.020", "Từ Hữu Đức", "", "", "", "", "", "Con cụ Chấn", "Tảo một", ""),
                    ("124.06.0.037", "124.05.0.020", "Từ Hữu Đìch", "", "", "", "", "", "Con cụ Chấn", "Tảo một", ""),
                    ("124.06.1.038", "124.05.0.020", "Từ Thị Toa", "", "", "", "", "", "Con cụ Chấn", "Tảo một", ""),
                    ("124.06.1.039", "124.05.0.021", "Từ Thị Tuần", "", "Bang Mỵ", "", "", "", "Con cụ Nhin. Lấy ông Bang Mỹ người ở Yên Vinh - Trảo Nha ", "", ""),
                    ("124.06.1.040", "124.05.0.021", "Từ Thị Hợi", "", "Thái Mạo", "", "", "", "Con cụ Nhin. Lấy ông Thái Mạo(Hạ) ở Xuân Mai", "", ""),
                    ("124.06.1.041", "124.05.0.021", "Từ Thị Thao", "", "Trần Lê Cớt", "", "", "", "Con cụ Nhin. Lấy ông Trần Lê Cớt giữa làng", "", ""),
                    ("124.06.0.042", "124.05.0.021", "Từ Hữu Chính", "", "Bà Nguyễn Thị Sương", "1891", "1940", "21/5", "Con cụ Nhin. Làm lý trưởng, thầy thuốc, địa lý, phù thuỷ đạo sỹ. Vợ là Bà Nguyễn Thị Sương (1898-1964, giổ 07/12). Sinh hạ: Từ Quang Diệu, Từ Hữu Bút (liệt sỹ), Từ Thị Tam (lấy ông Khởi trong làng), Từ Thị Hảo (lấy ông Trần Ninh trong làng), Từ Hữu Son, Từ Thị Tám (lấy ông Nguyễn Long trong làng), Từ Thị Chín (lấy ông Nhân trong làng); 3 con gái gồm: Thị Tứ, Thị Chút, Thị Mười (đều tảo vong).", "", ""),
                    ("124.06.1.043", "124.05.0.021", "Từ Thị Năm", "", "Trần Lạc", "", "", "", "Con cụ Nhin. Lấy ông Trần Lạc ở Yên Đồng (Con cháu là Trần Vựng)", "", ""),
                    ("124.06.0.044", "124.05.0.021", "Từ Hữu Giáo", "", "Bà Thái Thị Thới", "", "", "", "Con cụ Nhin. Sinh hạ: Từ Thị Chắt (lấy chồng người họ Trần Quang), Từ Thị Con (lấy chồng người Điền Xá Đồng Lộc), Từ Hữu Huấn (chết sớm), Từ Hữu Chuột, Từ Hữu Xưng (chết lúc 15 tuổi).", "", ""),
                    ("124.06.0.045", "124.05.0.021", "Từ Hữu Thí", "", "Bà Trần Thị Ba", "", "", "", "Con cụ Nhin. Sinh hạ: Từ Hữu Nuôi (chết sớm), Từ Hữu Thiện, Từ Thị Tỷ (lấy chồng người Đức Thọ), Từ Thị Quyền (lấy chồng người Thạch Ngọc).", "", ""),

                    # ------------------------------------
                    # CHI 3
                    # ------------------------------------                     
                    ("135.06.0.046", "135.05.0.025", "Từ Hữu Thống", "", "Bà Trần Thị Cầu", "", "", "", "Con cụ Hồng. Sinh hạ: Từ Thị Đích, Thị Dy (chết sớm).", "Phạp tự", ""),
                    ("135.06.0.047", "135.05.0.025", "Từ Hữu Thính", "", "Bà Ngô Thị Điện, Bà thứ Trương Thị Thiện", "", "", "", "Con cụ Hồng. Làm phó lý trưởng. Sinh hạ: Từ Thị (lấy cố Đốc Phiếm trong làng), Từ Hữu Mục, Từ Hữu Khoa, Từ Thị Đích (chết sớm).", "", ""),
                    ("135.06.1.048", "135.05.0.025", "Từ Thị Thúy", "", "", "", "", "", "Con cụ Hồng.", "Chết sớm", ""),
                    ("135.06.1.049", "135.05.0.026", "Từ Thị Điển", "", "Không rõ", "", "", "", "Con cụ Bằng. Lấy chồng về Khô Nội", "", ""),
                    ("135.06.1.050", "135.05.0.026", "Từ Thị ...", "", "Trần Lại", "", "", "", "Con cụ Bằng. Lấy ông Trần Lại trong làng", "", ""),
                    ("135.06.1.051", "135.05.0.026", "Từ Thị ...", "", "Lượng Nhạc", "", "", "", "Con cụ Bằng. Lấy Ông Lượng Nhạc Trảo Nha", "", ""),
                    ("135.06.1.052", "135.05.0.026", "Từ Thị Lạp", "", "Trần Bách", "", "", "", "Con cụ Bằng. Lấy ông Trần Bách trong làng", "", ""),
                    ("135.06.0.053", "135.05.0.026", "Từ Hữu Bối", "Ông Phụ", "Bà Nguyễn Thị Chút", "", "", "", "Con cụ Bằng. Sinh hạ: Từ Hữu Nuôi (chết sớm), Từ Thị Cháu (chết sớm), Từ Hữu Mậu.", "", ""),
                    ("135.06.0.054", "135.05.0.026", "Từ Hữu Triết", "", "Bà lấy chồng khác", "", "", "", "Con cụ Bằng. Sinh hạ: Từ Hữu Cháu (chết sớm), Từ Hữu Cước (chết sớm), Từ Hữu Quằt (chết sớm), Từ Thị Quỳ (lấy chồng về Trường Lộc).", "", ""),
                    ("135.06.1.055", "135.05.0.026", "Từ Thị Bổn", "", "Không rõ", "", "", "", "Con cụ Bằng. Lấy người Đại lộc", "", ""),
                    ("135.06.0.056", "135.05.0.027", "Từ Hữu Quán", "", "Bà Trần Thị Tuy", "", "", "", "Con cụ Lập. Sinh hạ: Từ Thị Khoách (lấy chồng họ Nguyễn Nhin), Từ Thị Hai (lấy ông Nguyễn Điểm giữa làng), Từ Thị Chự (lấy người họ Nguyễn Thế Kê Mòi), Từ Thị Em Nậy (lấy ông Trần Tuệ giữa làng), Từ Thị Em Con (lấy ông Trần Bệ giữa làng), Từ Hữu Trù, Từ Thị Chút (lấy ông Trần Bản giữa làng), Từ Thị Tám (lấy ông Trần Dê giữa làng).", "", ""),
                    ("135.06.0.057", "135.05.0.027", "Từ Hữu Thường", "", "", "", "", "", "Con cụ Lập", "Chết sớm", ""),
                    ("135.06.0.058", "135.05.0.027", "Từ Hữu Cự", "", "", "", "", "", "Con cụ Lập", "Chết sớm", ""),
                    ("135.06.0.059", "135.05.0.027", "Từ Hữu Kính", "", "", "", "", "", "Con cụ Lập", "Chết sớm", ""),
                    ("135.06.0.060", "135.05.0.027", "Từ Hữu Ngoạn", "", "Không có vợ", "", "", "", "Con ông Từ Hữu Lập. Hán tự thông minh.", "Không có con", ""),
                    ("135.06.0.061", "135.05.0.027", "Từ Hữu Xán", "", "Bà Nguyễn Thị Tửu", "", "", "", "Con cụ Lập. Sinh hạ: Từ Thị Bẹn (đã lấy chồng, chết sớm), Từ Thị Em (lấy chồng về Yên Đồng), Từ Thị Tam (chết đuối), Từ Thị Tứ (chết sớm), Từ Hữu Năm, Từ Hữu Lục, Từ Thị Bảy (chết sớm), Từ Hữu Tám.", "", ""),

                    # ------------------------------------
                    # CHI 4
                    # ------------------------------------        
                    ("246.06.0.062", "246.05.0.030", "Từ Hữu Hoè", "", "Bà Trần Thị Cát", "", "", "", "Con cụ Khái. Sinh hạ: Từ Hữu Đỏ, Từ Hữu Đốc, Từ Hữu Lường (đều chết sớm).", "", ""),
                    ("246.06.0.063", "246.05.0.030", "Từ Hữu Trấn", "", "Bà Trần Thị Tình", "", "", "", "Con cụ Khái. Ông trước làm quyền suất đội – Sắc phong phó Đô đốc. Sinh hạ: Từ Hữu Bạt, Từ Hữu Nhiếp, Từ Thị Đị (lấy ông Trần Hoàng trong làng).", "", ""),
                    ("246.06.0.064", "246.05.0.030", "Từ Hữu Át", "", "Bà Trần Thị Thưởng", "", "", "", "Con cụ Khái. Sinh hạ: Từ Hữu Xỉ, Từ Hữu Dị, Từ Thị Em (lấy ông Trần Vịnh giữa làng), Từ Thị Dị (tảo vong), Từ Thị Đỏ (tảo vong).", "", ""),
                    ("246.06.0.065", "246.05.0.030", "Từ Hữu Dự", "", "Bà Nguyễn Thị Tông, Bà thứ Nguyễn Thị Sáu", "", "", "", "Con cụ Kỳ.", "Không có con", ""),
                    ("246.06.0.066", "246.05.0.030", "Từ Hữu Vinh", "", "", "", "", "", "Con cụ Khái", "Chết sớm", ""),
                    ("246.06.0.067", "246.05.0.030", "Từ Hữu Bồng", "", "", "", "", "", "Con cụ Khái", "Chết sớm", ""),

                    # ------------------------------------
                    # CHI 5
                    # ------------------------------------                           
                    ("257.06.0.068", "257.05.0.033", "Từ Hữu Thạc", "", "Bà Nguyễn Thị Thẩm", "", "", "", "Con cụ Quýnh. Sinh hạ: Từ Thị Đạc (tảo vong), Từ Thị Đô (tảo một). Ông bà này cuối thế kỷ 18, khoảng triều đại Thành Thái di cư ra Hoàng Mai, Nghệ An ở. Tông tích không rõ.", "di cư, không rõ", ""),
                    ("258.06.0.069", "258.05.0.038", "Từ Hữu Cuộc", "", "Bà Trần Thị Khanh", "", "", "", "Con cụ Trinh. Sinh hạ: Từ Thị Tấn (tảo vong), Từ Hữu Đỏ (tảo vong), Từ Thị Đức (tảo vong), Từ Hữu Cu.", "", ""),
                    ("258.06.0.070", "258.05.0.038", "Từ Hữu Ức", "", "", "", "", "", "Con cụ Trinh.", "Tảo một", ""),
                    ("258.06.0.071", "258.05.0.038", "Từ Hữu Tùy", "", "Bà Trần Thị Trúc", "", "", "", "Con thứ 2 cụ Trinh. Sinh hạ: Từ Hữu Hoài, Từ Thị Láng (lấy chồng người họ Nguyễn Nhin), Từ Thị Chích (tảo một), Từ Hữu Liên (tảo một).", "", ""),
                    ("258.06.0.072", "258.05.0.038", "Từ Hữu Khôi", "", "", "", "", "", "Con cụ Trinh.", "Tảo vong", ""),
                    ("258.06.1.073", "258.05.0.038", "Từ Thị Liên", "", "", "", "", "", "Con cụ Trinh.", "Tảo vong", ""),
                    ("258.06.1.074", "258.05.0.038", "Từ Thị Cẩm", "", "", "", "", "", "Con cụ Trinh.", "Tảo vong", ""),
                    ("258.06.0.075", "258.05.0.041", "Từ Hữu Do", "", "Bà Ngô Thị Dị", "", "", "", "Con cụ Tranh. Sinh hạ: Từ Hữu Nha, Từ Thị Nhạ (tảo vong), Từ Thị Nhỏ (tảo vong).", "", ""),
                    ("258.06.1.076", "258.05.0.041", "Từ Thị Tốn", "", "Không rõ", "", "", "", "Con cụ Tranh", "", ""),
                    ("258.06.0.077", "258.05.0.044", "Từ Hữu Xuyến", "", "", "", "", "", "Con cụ Trừng.", "Tảo một", ""),
                    ("258.06.0.078", "258.05.0.044", "Từ Hữu Luyến", "", "", "", "", "", "Con cụ Trừng.", "Tảo một", ""),
                    ("258.06.0.079", "258.05.0.044", "Từ Hữu Son", "", "", "", "", "", "Con cụ Trừng.", "Tảo một", ""),
                    ("258.06.0.080", "258.05.0.045", "Từ Hữu Chuyên", "", "Bà Trần Thị Nhuyến", "", "", "", "Con cụ Điều. Sinh hạ: Từ Hữu Trại, Từ Hữu Lành (tảo vong), Từ Hữu Đỏ (tảo vong), 6 gái (Vinh, Đích, Thảo, Chích, Đỏ, Đỏ) đều tảo vong.", "", ""),
                    ("258.06.0.081", "258.05.0.045", "Từ Hữu Chuân", "",  "Bà Trần Thị Biên", "", "", "", "Con thứ 2 cụ Điều. Sinh hạ: Từ Hữu Nhạc, Từ Hữu Vòng (tảo một), Từ Thị Viền (lấy chồng người họ Nguyễn Nhin).", "", ""),
                    ("258.06.0.082", "258.05.0.045", "Từ Hữu Đích", "", "", "", "", "", "Con cụ Điều", "Tảo một", ""),
                    ("258.06.0.083", "258.05.0.045", "Từ Hữu Nhận", "", "", "", "", "", "Con cụ Điều", "Tảo một", ""),
                    ("258.06.0.084", "258.05.0.046", "Từ Hữu Huân", "", "Bà Trần Thị Mạnh", "", "", "", "Con cụ Kiên. Ông trước làm lý trưởng. Sinh hạ: Từ Hữu Vi, Từ Hữu Lậu, Từ Hữu Ứng, Từ Thị... (lấy người họ Trần), Từ Hữu Tôn (mất sớm), 3 gái [Thị Lượng, Em, Đỏ] đều tảo một.", "", ""),
                    ("258.06.0.085", "258.05.0.046", "Từ Hữu Giảng", "", "Bà Trần Thị Quán", "", "", "", "Con thứ 2 cụ Kiên. Sinh hạ: Từ Hữu Dái (tảo một), Từ Hữu Lai, Từ Hữu Lưu, Từ Hữu Đỏ (tảo vong).", "", ""),
                    ("258.06.0.086", "258.05.0.046", "Từ Hữu Điển", "", "Bà Trần Thị Lương", "", "", "", "Con thứ 3 cụ Kiên. Sinh hạ: Từ Hữu Kẹo, Từ Hữu Mât (tảo vong), Từ Hữu Thái, Từ Hữu Thới (tảo một), Từ Thị Em (tảo một), Từ Thị Sáu (tảo một), 4 gái [Yêm, Đường, Đỏ, Đỏ] đều tảo một.", "", ""),
                    ("258.06.0.087", "258.05.0.046", "Từ Hữu Dái", "", "", "", "", "", "Con cụ Kiên", "Tảo một", ""),
                    ("258.06.0.088", "258.05.0.047", "Từ Hữu Bồng", "", "Bà Trần Thị Út", "", "", "", "Con cụ Kiên. Sinh hạ: Từ Hữu Tự (chết sớm), Từ Hữu Đỏ (tảo vong), Từ Hữu Đỏ (tảo vong). Ông bà này về sau di cư đi đâu không rõ.", "di cư, không rõ", ""),

                    # ==========================================================
                    # ĐỜI 7 
                    # ==========================================================

                    # ------------------------------------
                    # CHI 1
                    # ------------------------------------
                    ("111.07.0.001", "111.06.0.001", "Từ Hữu Phiệt", "", "Bà cả Trần Thị Hán, bà thứ Trần Thị Thoả", "", "", "", "Con cụ Thư. Ông trước làm lý trưởng, chết ngày 25 tháng 7 âm lịch. Sinh hạ: Từ Thị... (lấy 2 lần chồng, lần sau về Vĩnh Lộc), Từ Hữu Điệt, Từ Thị Đém (tảo một), Từ Thị Bốn, Từ Hữu Huyền, Từ Hữu Ca (tảo một), Từ Thị Bảy (lấy người họ Nguyễn Nhin), Từ Thị Bát (tảo vong), Từ Hữu Đỏ (tảo vong), Từ Hữu Đỏ (tảo vong).", "", ""),
                    ("111.07.1.002", "111.06.0.001", "Từ Thị ...", "", "Trần Cớt", "", "", "", "Con cụ Thư. Lấy cố Trần Cớt trong làng", "", ""),
                    ("111.07.1.003", "111.06.0.001", "Từ Thị ...", "", "Trần Chước", "", "", "", "Con cụ Thư. Lấy ông Trần Chước trong làng", "", ""),
                    ("111.07.0.004", "111.06.0.001", "Từ Hữu Vinh", "", "", "", "", "", "Con cụ Thư.", "Tảo một", ""),
                    ("111.07.0.005", "111.06.0.001", "Từ Hữu Vượng", "", "", "", "", "", "Con cụ Thư.", "Tảo một", ""),
                    ("111.07.0.006", "111.06.0.001", "Từ Hữu Thuận", "", "", "", "", "", "Con cụ Thư.", "Tảo một", ""),
                    ("111.07.0.007", "111.06.0.001", "Từ Hữu Đốc", "", "", "", "", "", "Con cụ Thư.", "Tảo một", ""),
                    ("111.07.0.008", "111.06.0.006", "Từ Hữu Lâm", "", "Bà Trần Thị Nhỏ", "", "", "", "Con cụ Ngạnh. Sinh hạ: Từ Thị Mức (lấy chồng họ Nguyễn Nhin), Từ Thị Ba (lấy chồng, 3 chồng), Từ Hữu Đồng, Từ Hữu Địch (tảo vong), Từ Hữu Kế, Từ Thị Chút (chết sớm), Từ Hữu Thịnh (chết sớm).", "", ""),
                    ("111.07.0.009", "111.06.0.006", "Từ Hữu Tâm", "", "Bà Thái Thị Hai", "", "", "", "Con thứ 2 cụ Ngạnh. Được cấp bằng Phó tổng dụng. Sinh hạ: Từ Hữu Điệng (chết sớm), Từ Hữu Tiệng, Từ Thị Em (chết đuối), Từ Hữu Thiện (tảo một).", "", ""),
                    ("111.07.0.010", "111.06.0.006", "Từ Hữu Lam", "", "", "", "", "", "Con cụ Ngạnh", "Tảo một", ""),
                    ("111.07.0.011", "111.06.0.006", "Từ Hữu Liêm", "", "", "", "", "", "Con cụ Ngạnh", "Tảo một", ""),
                    ("111.07.0.012", "111.06.0.008", "Từ Hữu Sáng", "", "Bà Trần Thị Bộ", "", "", "", "Con đầu cụ Khánh. Sinh hạ: Từ Hữu Nghiệp (tảo một), Từ Hữu Xuân (tảo vong), Từ Hữu Vên (tảo vong), Từ Thị Út (tảo một), Từ Thị Xin (tảo một), Từ Thị Mức (lấy chồng không có con, chết).", "", ""),
                    ("111.07.1.013", "111.06.0.008", "Từ Thị...", "", "cố Hiến", "", "", "", "Con cụ Khánh. Lấy cố Hiến  xã Thạch Liên.", "", ""),
                    ("111.07.1.014", "111.06.0.008", "Từ Thị Chẹc", "", "", "", "", "", "Con cụ Khánh", "Tảo một", ""),
                    ("111.07.1.015", "111.06.0.008", "Từ Thị...", "", "Không rõ", "", "", "", "Con cụ Khánh. Lấy chồng về Yên đồng.", "", ""),
                    ("111.07.1.016", "111.06.0.008", "Từ Thị Năm", "", "", "", "", "", "Con cụ Khánh", "Tảo một", ""),
                    ("111.07.0.017", "111.06.0.008", "Từ Hữu Xích", "", "Bà cả Trần Thị Phương, bà thứ Nguyễn Thị Thiu", "", "", "", "Con cụ Khánh. Sinh hạ: 3 trai [Nghiêm, Linh, Tấn] đều tảo vong, Từ Thị Tuất (lấy người miền Nam, Từ Thị Thảo lấy người Sơn Lộc).", "Phạp tự", ""),
                    ("111.07.0.018", "111.06.0.010", "Từ Hữu Toại", "", "Bà cả Trần Thị Khai, bà thứ Nguyễn Thị Kiềm", "", "", "", "Con cụ Sum. Ông trước làm lý trưởng lên chánh tổng. Sinh hạ: Từ Hữu Hào, Từ Thị Em nậy (lấy ông Thực Dư ở Đại Lộc), Từ Thị Em Con (lấy ông Nguyễn Khiêm), Từ Hữu Bốn, Từ Hữu Niêm (chết sớm).", "", ""),
                    ("111.07.1.019", "111.06.0.010", "Từ Thị ...", "", "cố Sị", "", "", "", "Con cụ Sum. Lấy cố Sị trong làng", "", ""),
                    ("111.07.0.020", "111.06.0.010", "Từ Hữu Nghị", "", "Bà Lê Thị Hai", "", "", "", "Con thứ 2 cụ Sum. Sinh hạ: Từ Hữu Nghi (chết lúc khoảng 20 tuổi), Từ Thị Em (lấy ông Trần Hải trong làng), Từ Hữu Lợi (tảo một), Từ Hữu Lộc.", "", ""),
                    ("111.07.1.021", "111.06.0.010", "Từ Thị ...", "", "cựu Thuyên", "", "", "", "Con cụ Sum. Lấy ông cựu Thuyên trong làng", "", ""),
                    ("111.07.1.022", "111.06.0.010", "Từ Thị ...", "", "Trần Yểu", "", "", "", "Con cụ Sum. Lấy ông Trần Yểu trong làng", "", ""),
                    ("111.07.1.023", "111.06.0.010", "Từ Thị Sáu", "", "Cửu Tường", "", "", "", "Con cụ Sum. Lấy ông Cửu Tường trong làng", "", ""),
                    ("111.07.1.024", "111.06.0.010", "Từ Thị ...", "", "Trung Hiếu", "", "", "", "Con cụ Sum. Lấy ông Trung Hiếu trong làng", "", ""),
                    ("111.07.0.025", "111.06.0.010", "Từ Hữu Luận", "", "Bà Trần Thị, bà thứ Trần Thị Kép", "", "", "", "Con thứ 3 cụ Sum. Sinh hạ: Từ Thị Ngọ (lấy ông Trần Phúc trong làng), Từ Hữu Trợ, Từ Hữu Trự, Từ Hữu Ngự (tảo một), Từ Hữu Sáu, Từ Thị Tựu (lấy anh Nhàn xã Vĩnh Lộc), Từ Hữu Kế, Từ Thị Đỏ (tảo vong), Từ Hữu Chín (tảo một).", "", ""),
                    ("111.07.1.026", "111.06.0.012", "Từ Thị Dị", "", "Trần Đinh", "", "", "", "Con cụ Cội. Lấy ông Trần Đinh trong làng", "", ""),
                    ("111.07.0.027", "111.06.0.012", "Từ Hữu Lệ", "", "Bà Trần Thị Cầy (út)", "", "", "", "Con đầu cụ Cội. Sinh hạ: Từ Hữu Số, Từ Hữu Nhuyến, Từ Hữu Tam (mất sớm).", "", ""),
                    ("111.07.1.028", "111.06.0.012", "Từ Thị ...", "", "Đặng Cầu", "", "", "", "Con cụ Cội. Lấy ông Đặng Cầu trong làng", "", ""),
                    ("111.07.1.029", "111.06.0.012", "Từ Thị ...", "", "Trần Thảng", "", "", "", "Con cụ Cội. Lấy ông Trần Thảng trong làng", "", ""),
                    ("111.07.0.030", "111.06.0.012", "Từ Hữu Nghĩa", "", "Bà Ngô Thị Ứng", "", "", "", "Con thứ 2 cụ Cội. Sinh hạ: Từ Hữu Nhường, Từ Thị Em (lấy ông Quỳ trong làng), Từ Hữu Thường, Từ Thị Chút (lấy ông Tình trong làng), Từ Hữu Tường, Từ Hữu Âu, Từ Hữu Dái (tảo một).", "", ""),
                    ("111.07.0.031", "111.06.0.012", "Từ Hữu Khí", "", "", "", "", "", "Con cụ Cội.", "Chết sớm", ""),
                    ("111.07.0.032", "111.06.0.012", "Từ Hữu Trề", "", "", "", "", "", "Con cụ Cội.", "Chết sớm", ""),
                    ("111.07.1.033", "111.06.0.012", "Từ Thị Tám", "", "Đặng Cầu", "", "", "", "Con cụ Cội. Lấy ông Trần Hoàn trong làng", "", ""),
                    ("111.07.0.034", "111.06.0.012", "Từ Hữu Lộc", "", "", "", "", "", "Con cụ Cội.", "Tảo vong", ""),

                    # ------------------------------------
                    # CHI 2
                    # ------------------------------------ 
                    ("122.07.0.035", "122.06.0.014", "Từ Hữu Duyệt", "", "Bà Trần Thị Nhụ", "", "", "", "Con cụ Toát. Sinh hạ: Từ Hữu Tựu, Từ Thị Tưu (lấy ông Trần Diệm trong làng), Từ Thị Chút (lấy ông Trần Ngọt trong làng), Từ Thị Chút Em (lấy ông Nguyễn Hy ở Yên Đồng), Từ Hữu Nựu.", "", ""),
                    ("122.07.1.036", "122.06.0.014", "Từ Thị Em", "", "Trần Thế", "", "", "", "Con cụ Toát. Lấy ông Trần Thế trong làng", "", ""),
                    ("122.07.0.037", "122.06.0.014", "Từ Hữu Hợi", "", "Bà Nguyễn Thị Đình", "", "", "", "Con thứ 2 cụ Toát. Sinh hạ: Từ Hữu Cảnh, Từ Hữu Quý (liệt sỹ), Từ Thị Tỷ (lấy ông Phan Đàn Xóm Mới), Từ Hữu Tư, Từ Thị Ngụ (lấy chồng về Đức Lâm, Đức Thọ), Từ Thị Lùc (lấy chồng về Kỳ Anh).", "", ""),
                    ("122.07.0.038", "122.06.0.014", "Từ Hữu Điếm", "", "", "", "", "", "Con cụ Toát", "Tảo vong", ""),
                    ("122.07.1.039", "122.06.0.017", "Từ Thị Mai", "", "Trần Chinh", "", "", "", "Con cụ Mận. Lấy Trần Chinh trong làng", "", ""),
                    ("122.07.0.040", "122.06.0.017", "Từ Hữu Khai (Đoài)", "", "Bà Nguyễn Thị Chắt", "", "", "", "Con cụ Mận. Sinh hạ: Từ Thị Đoài (lấy ông Trần Đại trữa làng), Từ Hữu Lương, Từ Thị Đỏ (tảo một).", "", ""),
                    ("122.07.0.041", "122.06.0.017", "Từ Hữu Lai", "Như", "Bà Trần Thị Em", "", "", "", "Con thứ 2 cụ Mận. Sinh hạ: Từ Thị Xuân, Từ Thị Tâm, Từ Hữu Tương.", "", ""),
                    ("123.07.0.042", "123.06.0.026", "Từ Hữu Kiệp", "", "Bà Trần Thị Tráng", "", "", "", "Con đầu cụ Vẹn. Sinh hạ: Từ Hữu Đa (tảo một), Từ Hữu Số, Từ Hữu Yêm, Từ Hữu Niềm, Từ Thị Xuân (lấy ông Nguyễn Cầu, Trung Xá), Từ Hữu Xanh, Từ Thị Thanh (lấy ông Nguyễn Tứ (Xà) trong làng).", "", ""),
                    ("123.07.0.043", "123.06.0.026", "Từ Hữu Điệp", "", "Bà Nguyễn Thị Ba", "", "", "", "Con thứ 2 cụ Vẹn. Sinh hạ: Từ Hữu Nuôi, Từ Hữu Nuôi Em (Tiếp). ", "", ""),
                    ("123.07.1.044", "123.06.0.026", "Từ Thị Ba", "", "Không rõ", "", "", "", "Con cụ Vẹn. Lấy chồng về Thạch Liên", "", ""),         
                    ("123.07.0.045", "123.06.0.026", "Từ Hữu Dữu", "", "", "", "", "", "Con cụ Vẹn", "Chết sớm", ""),
                    ("123.07.1.046", "123.06.0.026", "Từ Thị Chút", "", "Trần Tuần", "", "", "", "Con cụ Vẹn. Lấy ông Trần Tuần dư nại", "", ""),
                    ("123.07.1.047", "123.06.0.026", "Từ Thị Tỷ", "", "Ông Long", "", "", "", "Con cụ Vẹn. Lấy chồng về Tiến Lộc", "", ""),
                    ("123.07.1.048", "123.06.0.027", "Từ Thị Xin", "", "", "", "", "", "Con cụ Vẹ", "Chết sớm", ""),
                    ("124.07.0.049", "124.06.0.042", "Từ Quang Diệu", "", "Bà Trần Thị Thái", "1920", "1992", "01/05 AL", "Con đầu cụ Chính. Cán bộ xã, huyện, tỉnh liên khu 4; Huân, Huy chương kháng chiến hạng Nhất. Vợ là Bà Trần Thị Thái (1934-2012, giỗ 15/01). Sinh hạ: Từ Hữu Chắt (Chết sớm), Từ Thị Đào (tảo vong), Từ Thị Lý (Chết sớm), Từ Hữu Hạnh (tảo vong), Từ Quang Viện, Từ Quang Xá, Từ Kim Khánh, Từ Quang Thuỳ, Từ Thị Đỏ (tảo vong).", "", ""),
                    ("124.07.0.050", "124.06.0.042", "Từ Quang Bút", "", "Không có vợ", "", "", "", "Con cụ Chính. Liệt sĩ chống Pháp", "Không có con", ""),
                    ("124.07.1.051", "124.06.0.042", "Từ Thị Tam", "", "Trần Khới", "", "", "", "Con cụ Chính. Lấy ông Trần Khới trong làng (Con cháu hiện nay là Trần Khởi", "", ""),
                    ("124.07.1.052", "124.06.0.042", "Từ Thị Tứ", "", "", "", "", "", "Con cụ Chính", "Tảo vong", ""),
                    ("124.07.1.053", "124.06.0.042", "Từ Thị Chút", "", "", "", "", "", "Con cụ Chính", "Tảo vong", ""),             
                    ("124.07.1.054", "124.06.0.042", "Từ Thị Hảo", "", "Trần Ninh", "", "", "", "Con cụ Chính. Lấy ông Trần Ninh trong làng (Con cháu hiện nay là Trần Đình Sâm", "", ""),             
                    ("124.07.0.055", "124.06.0.042", "Từ Quang Son", "Phú", "Bà Trần Thị Tỷ", "", "", "", "Con thứ 3 cụ Chính. Ông làm cán bộ hợp tác xã. Sinh hạ: Từ Hữu Phú, Từ Thị Ngư (lấy ông Thái Kỳ xóm mới), Từ Thị Nhung (lấy chồng), Từ Hữu Huy, Từ Thị Quy (lấy anh Trần Hải (Xứ) trong làng), Từ Hữu Quý.", "", ""),
                    ("124.07.1.056", "124.06.0.042", "Từ Thị Tám", "", "Nguyễn Long", "", "", "", "Con cụ Chính. Lấy ông Nguyễn Long trong làng(Con cháu hiện nay là Nguyễn Thị Thanh", "", ""),
                    ("124.07.1.057", "124.06.0.042", "Từ Thị Chín", "", "Ông Nhân", "", "", "", "Con cụ Chính. Lấy ông Nhân trong làng(Con cháu hiện nay là Chắt Nhân", "", ""),
                    ("124.07.1.058", "124.06.0.042", "Từ Thị Mười", "", "", "", "", "", "Con cụ Chính", "Tảo vong", ""),
                    ("124.07.1.059", "124.06.0.044", "Từ Thị Chắt", "", "Trần Minh", "", "", "", "Con ông Giáo. Lấy ông Trần Minh ở Quang Lộc", "", ""),
                    ("124.07.1.060", "124.06.0.044", "Từ Thị Con", "", "Nguyễn Thủy", "", "", "", "Con ông Giáo. Lấy ông Nguyễn Thủy ở Điền Xá - Đồng Lộc", "", ""),                  
                    ("124.07.0.061", "124.06.0.044", "Từ Hữu Huấn", "", "", "", "", "", "Con ông Giáo.", "Chết sớm", ""),
                    ("124.07.0.062", "124.06.0.044", "Từ Hữu Chuột", "", "Bà Trần Thị Tỷ", "", "", "", "Con ông Giáo. Sinh hạ: Từ Hữu Khang, Từ Thị Thái, Từ Hữu Bình, Từ Thị Đỏ (tảo vong).", "", ""),
                    ("124.07.0.063", "124.06.0.044", "Từ Hữu Xưng", "", "", "", "", "", "Con ông Giáo. Chết lúc 15 tuổi ", "Chết sớm", ""),
                    ("124.07.0.064", "124.06.0.045", "Từ Hữu Nuôi", "", "", "", "", "", "Con cụ Thí", "Chết sớm", ""),
                    ("124.07.0.065", "124.06.0.045", "Từ Hữu Thiện", "", "Bà cả Trần Thị Xuân, Bà thứ Nguyễn Thị Quế", "", "", "", "Con cụ Thí. Ông trước làm nghề dạy học, giáo viên cấp 1. Vợ cả (Bà Hòa Thượng Xuân)sinh hạ: Từ Hữu Giáp (mất sớm). Vợ thứ sinh hạ: Từ Hữu Cường, Từ Hữu Thành (tảo vong), Từ Hữu Mạnh (đi làm con nuôi).", "", ""),
                    ("124.07.1.066", "124.06.0.045", "Từ Thị Tỷ", "Liên", "ông Trần Văn Sinh", "", "", "", "Con cụ Thí. Lấy ông Trần Văn Sinh người Đức Thọ", "", ""),
                    ("124.07.1.067", "124.06.0.045", "Từ Thị Quyền", "", "ông Nguyễn Hữu Tuế", "", "", "", "Con cụ Thí. Lấy ông Tuế người Thạch Ngọc", "", ""),

                    # ------------------------------------
                    # CHI 3
                    # ------------------------------------      
                    ("135.07.1.068", "135.06.0.046", "Từ Thị Đích", "", "Không rõ", "", "", "", "Con cụ Thống. Lấy chồng về Đồng Lộc.", "", ""),
                    ("135.07.1.069", "135.06.0.046", "Từ Thị Di", "", "", "", "", "", "Con cụ Thống.", "Chết sớm", ""),
                    ("135.07.1.070", "135.06.0.047", "Từ Thị ...", "", "Trần Phiếm", "", "", "", "on cụ Thính. Lấy ông Trần Phiếm trong làng", "", ""),
                    ("135.07.0.071", "135.06.0.047", "Từ Hữu Mục", "", "Bà Trần Thị Dản", "", "", "", "Con cụ Thính. Sinh hạ: Từ Thị Thộ (mất do thiên lôi), Từ Hữu Thự.", "", ""),
                    ("135.07.0.072", "135.06.0.047", "Từ Hữu Khoa", "", "Không có vợ", "", "", "", "Con cụ Thính. Sống già nhưng không có vợ con.", "Không có con", ""),
                    ("135.07.0.073", "135.06.0.053", "Từ Hữu Nuôi", "", "", "", "", "", "Con ông Bối(ông Phụ)", "Chết sớm", ""),
                    ("135.07.1.074", "135.06.0.053", "Từ Thị Cháu", "", "", "", "", "", "Con ông Bối(ông Phụ)", "Chết sớm", ""),
                    ("135.07.0.075", "135.06.0.053", "Từ Hữu Mậu", "", "Hai vợ đều bỏ", "", "", "", "Con ông Bối (ông Phụ). Sinh hạ: Từ Thị Xanh (lấy chồng Miền Nam), Từ Thị Dần (không chồng con), Từ Thị Tam (mất sớm), Từ Thị Tứ (không chồng con).", "", ""),
                    ("135.07.0.076", "135.06.0.054", "Từ Hữu Cháu", "", "", "", "", "", "Con ông Triết", "Chết sớm", ""),
                    ("135.07.0.077", "135.06.0.054", "Từ Hữu Cước", "", "", "", "", "", "Con ông Triết", "Chết sớm", ""),
                    ("135.07.0.078", "135.06.0.054", "Từ Hữu Quằt", "", "", "", "", "", "Con ông Triết", "Chết sớm", ""),
                    ("135.07.1.079", "135.06.0.054", "Từ Thị Quỳ", "", "Không rõ", "", "", "", "Con ông Triết. Lấy chồng về Trường Lộc", "", ""),
                    ("135.07.1.080", "135.06.0.056", "Từ Thị Khoách", "", "Nguyễn Thiềng", "", "", "", "Con cụ Quán. Lấy ông Nguyễn Thiềng giữa làng", "", ""),
                    ("135.07.1.081", "135.06.0.056", "Từ Thị Hai", "", "Nguyễn Điểm", "", "", "", "Con cụ Quán. Lấy ông Nguyễn Điểm giữa làng", "", ""),
                    ("135.07.1.082", "135.06.0.056", "Từ Thị Chự", "", "Nguyễn Thế", "", "", "", "Con cụ Quán. Lấy ông Nguyễn Thế ở Kẻ Mòi", "", ""),
                    ("135.07.1.083", "135.06.0.056", "Từ Thị Em Nậy", "", "Trần Tuệ", "", "", "", "Con cụ Quán. Lấy ông Trần Tuệ giữa làng", "", ""),
                    ("135.07.1.084", "135.06.0.056", "Từ Thị Em Con", "", "Trần Bệ", "", "", "", "Con cụ Quán. Lấy ông Trần Bệ giữa làng", "", ""),            
                    ("135.07.0.085", "135.06.0.056", "Từ Hữu Trù", "", "Bà Nguyễn Thị Ngoéc", "", "", "", "Con cụ Quán. Vợ là Bà Nguyễn Thị Ngoéc (người Tiền Lối, Quang Lộc). Sinh hạ: Từ Hữu Trì, Từ Hữu Thái, Từ Thị Chiu (lấy chồng về Đại Lộc), Từ Thị Kẹm (chết sớm), Từ Hữu Ô (chết sớm), Từ Hữu Mạ (chết sớm).", "", ""),
                    ("135.07.1.086", "135.06.0.056", "Từ Thị Chút", "", "Trần Bản", "", "", "", "Con cụ Quán. Lấy ông Trần Bản giữa làng", "", ""),
                    ("135.07.1.087", "135.06.0.056", "Từ Thị Tám", "", "Trần Dê", "", "", "", "Con cụ Quán. Lấy ông Trần Dê giữa làng", "", ""),
                    ("135.07.1.088", "135.06.0.061", "Từ Thị Bẹn", "", "Không rõ", "", "", "", "Con ông Xán. Đã lấy chồng chết sớm", "", ""),
                    ("135.07.1.089", "135.06.0.061", "Từ Thị Em", "", "ông Bút", "", "", "", "Con ông Xán. Lấy ông Bút ở Yên Đồng", "", ""),
                    ("135.07.1.090", "135.06.0.061", "Từ Thị Tam", "", "", "", "", "", "Con ông Xán. Chết đuối", "Chết sớm", ""),
                    ("135.07.1.091", "135.06.0.061", "Từ Thị Tứ", "", "", "", "", "", "Con ông Xán.", "Chết sớm", ""),          
                    ("135.07.0.092", "135.06.0.061", "Từ Hữu Năm", "Từ Hoa Việt", "Bà Nguyễn Thị Lợi", "", "", "", "Con ông Xán. Vợ là Bà Nguyễn Thị Lợi (người Quốc Oai, Bình Đà, Hà Đông). Bộ đội chống Pháp, kỹ sư điện, Huy chương chống Pháp, Huân chương chống Mỹ (Gia đình ở Hà Nội). Sinh hạ: Từ Thị Lan, Từ Hữu Nam (Từ Hoa Nam - bộ đội), Từ Thị Hải Anh.", "", ""),
                    ("135.07.0.093", "135.06.0.061", "Từ Hữu Lục", "Quang, Thuận, Bút", "Bà Trần Thị Tỷ", "", "1988", "2/6 AL", "Con ông Xán. Ông mất ngày 2/6/1988 AL. Vợ là Bà Trần Thị Tỷ (mất 28/10 AL 2003). Sinh hạ: Từ Thị Hạnh (chết sớm), Từ Thị Phúc (chết sớm), Từ Thị Thu Hà (lấy anh Nguyễn Tâm [Chung], trong làng), Từ Thị Nhung (chết đuối), Từ Hữu Hoà (Đại tá Quân đội, sống ở Hà Nội), Từ Thị Hiệp (lấy chồng về Sơn Lộc [chết sớm]), Từ Hữu Huấn (ở Hà Nội).", "", ""), 
                    ("135.07.1.094", "135.06.0.061", "Từ Thị Bảy", "", "", "", "", "", "Con ông Xán.", "Chết sớm", ""),
                    ("135.07.0.095", "135.06.0.061", "Từ Hữu Tám", "Sơn", "Bà Nguyễn Thị Quý", "", "", "", "Con ông Xán. Vợ là Bà Nguyễn Thị Quý (người Thuận Lộc). Vợ chồng làm công nhân ở Nông trường Việt Trung, Quảng Bình. Sinh hạ: Từ Thị Thái, Từ Thị Bình, Từ Thị Minh, Từ Thị Thìn, Từ Hữu Sang (chết sớm), Từ Hữu Trọng.", "", ""),

                    # ------------------------------------
                    # CHI 4
                    # ------------------------------------     
                    ("246.07.0.096", "246.06.0.062", "Từ Hữu Đốc", "", "", "", "", "", "Con ông Hòe", "Chết sớm", ""),
                    ("246.07.0.097", "246.06.0.062", "Từ Hữu Lường", "", "", "", "", "", "Con ông Hòe", "Chết sớm", ""),
                    ("246.07.0.098", "246.06.0.063", "Từ Hữu Bạt", "", "Bà cả Trần Thị Dinh, Bà thứ Ngô Thị Bốn", "", "", "", "Con ông Trấn. Ông trước làm Hương thợ làng. Sinh hạ: Từ Hữu Mộc (đi Lào chết), Từ Hữu Phương (chết sớm), Từ Hữu Cương, Từ Thị Ngọ (lấy ông Trần Thản trong làng).", "", ""),
                    ("246.07.0.099", "246.06.0.063", "Từ Hữu Nhiếp", "", "Bà Trần Thị Thào", "", "", "14/4", "Con thứ 2 cụ Trấn. Vợ là Bà Trần Thị Thào (thọ 91 tuổi, mất 21/2 AL). Ông trước làm sải chùa, cán bộ phong trào 1930. Sống thọ 73 tuổi. Sinh hạ: Từ Thị Chắn (tảo vong), Từ Thị Chắt (lấy ông Trần Dương, Yên Đồng), Từ Hữu Tượng, Từ Hữu Hình (Hảo - Liệt sĩ), Từ Hữu Chất.", "", ""),
                    ("246.07.1.100", "246.06.0.063", "Từ Thị Đị", "", "Trần Hùng", "", "", "", "Con ông Trấn. Lấy ông Trần Hùng giữa làng", "", ""),
                    ("246.07.0.101", "246.06.0.064", "Từ Hữu Xỉ", "", "Bà cả Ngô Thị Em, bà thứ Đặng Thị Tư", "", "", "", "Con ông Át. Sinh hạ: Từ Hữu Tuất (tảo một), Từ Thị Yên (lấy ông Nguyễn Liêu trong làng), Từ Hữu Dần, Từ Hữu Thìn.", "", ""),
                    ("246.07.0.102", "246.06.0.064", "Từ Hữu Dỵ", "", "Nguyễn Thị Thường", "", "", "", "Con thứ 2 ông Át. Vợ là Nguyễn Thị Thường (Vợ cải giá tha phu). Sinh hạ: Từ Hữu Bạng, Từ Hữu Hộ, Từ Hữu Khánh.", "", ""),
                    ("246.07.1.103", "246.06.0.064", "Từ Thị Em", "", "Trần Vịnh", "", "", "", "Con ông Át. Lấy ông Trần Vịnh giữa làng", "", ""),
                    ("246.07.1.104", "246.06.0.064", "Từ Thị Dị", "", "", "", "", "", "Con ông Át", "Tảo vong", ""),
                    # ------------------------------------
                    # CHI 5
                    # ------------------------------------          
                    ("258.07.1.105", "258.06.0.069", "Từ Thị Tấn", "", "", "", "", "", "Con ông Cuộc.", "Tảo vong", ""),
                    ("258.07.1.106", "258.06.0.069", "Từ Thị Đức", "", "", "", "", "", "Con ông Cuộc.", "Tảo vong", ""),                   
                    ("258.07.0.107", "258.06.0.069", "Từ Hữu Cu", "", "Bà Nguyễn Thị Út", "", "", "", "Con ông Cuộc.", "Không có con", ""),
                    ("258.07.0.108", "258.06.0.071", "Từ Hữu Hoài", "", "Bà Nguyễn Thị Túc", "", "", "", "Con ông Tuỳ. Sinh hạ: Từ Thị Hiểu (lấy ông Trần Chiểu trong làng), Từ Hữu Điểu, Từ Hữu Tiếu (Phán), Từ Thị Đỏ (tảo vong).", "", ""),
                    ("258.07.1.109", "258.06.0.071", "Từ Thị ...", "", "ông Láng", "", "", "", "Con ông Tuỳ. Lấy ông Láng giữa làng", "", ""),
                    ("258.07.1.110", "258.06.0.071", "Từ Thị Chích", "", "", "", "", "", "Con ông Tuỳ", "Tảo một", ""),
                    ("258.07.0.111", "258.06.0.071", "Từ Hữu Liên", "", "", "", "", "", "Con ông Tuỳ", "Tảo một", ""),
                    ("258.07.0.112", "258.06.0.075", "Từ Hữu Nha", "", "Bà Nguyễn Thị Thật", "", "", "", "Con ông Do. Nghề nghiệp: làm nghề da, thợ mộc, thợ may. Sinh hạ: Từ Thị Dệ (lấy ông Nguyễn Văn Thống, Dư Nại), Từ Thị Hoà (lấy ông Hành ở Mỹ Lộc), Từ Thị Dục (lấy ông Thế Nhiên, Thượng Xuân), Từ Thị Phúc (lấy ông Trần Á trong làng), Từ Thị Tỷ (lấy Nguyễn Hành, Dư Nại), Từ Hữu Tung (tảo vong).", "", ""),
                    ("258.07.1.113", "258.06.0.075", "Từ Thị Nhạ", "", "", "", "", "", "Con ông Do.", "Tảo vong", ""),
                    ("258.07.1.114", "258.06.0.075", "Từ Thị Nhỏ", "", "", "", "", "", "Con ông Do.", "Tảo vong", ""),
                    ("258.07.0.115", "258.06.0.080", "Từ Hữu Trại", "", "Vợ đi lấy chồng khác", "", "", "", "Con ông Chuyên. Sinh hạ: Từ Thị Sào (lấy chồng về Kẻ Mòi).", "Phạp tự", ""),
                    ("258.07.0.116", "258.06.0.080", "Từ Hữu Lành", "", "", "", "", "", "Con ông Chuyên.", "Tảo vong", ""),
                    ("258.07.0.117", "258.06.0.081", "Từ Hữu Nhạc", "",  "Bà cả Đặng Thị Kiều, bà thứ Thái Thị Hanh", "", "", "", "Con ông Chuân. Nghề nghiệp: Dạy Hán, thầy thuốc, địa lý. Sinh hạ: Từ Thị Em (lấy ông Phan Liêu, Xóm Mới), Từ Hữu Đề.", "", ""),
                    ("258.07.0.118", "258.06.0.081", "Từ Hữu Vòng", "", "", "", "", "", "Con ông Chuân", "Tảo một", ""),
                    ("258.07.1.119", "258.06.0.081", "Từ Thị Mặc", "", "Nguyễn Viền", "", "", "", "Con ông Chuân. Lấy ông Nguyễn Viền giữa làng", "", ""),
                    ("258.07.0.120", "258.06.0.084", "Từ Hữu Vi", "", "Bà Trần Thị Thao", "", "", "", "Con đầu ông Huân. Nghề nghiệp: Thợ mộc. Sinh hạ: Từ Hữu Dạ (tảo một), Từ Hữu Túc, Từ Thị Đạn (lấy ông Trần Bá (Phố) trong làng).", "", ""),
                    ("258.07.0.121", "258.06.0.084", "Từ Hữu Lậu", "", "Bà Trần Thị Tân, bà thứ Lê Thị Năm", "", "", "", "Con ông Huân. Sinh hạ: Từ Hữu Vân, Từ Hữu Đằng, Từ Hữu Bầng (Liệt sĩ), Từ Hữu Nhuệ.", "", ""),
                    ("258.07.0.122", "258.06.0.084", "Từ Hữu Ứng", "", "Bà Trần Thị Năm", "", "", "", "Con thứ 3 ông Huân. Được sắc phong Chánh bát phẩm, Đội trưởng. Sinh hạ: Từ Hữu Sàn, Từ Thị Em (lấy ông Trần Tá trong làng), Từ Hữu Hiệt, Từ Thị Tử (lấy ông Nguyễn Xà trong làng), Từ Hữu Sàng.", "", ""),
                    ("258.07.1.123", "258.06.0.084", "Từ Thị ...", "", "Mục Lung", "", "", "", "Con ông Huân. Lấy ông Mục Lung ", "", ""),
                    ("258.07.0.124", "258.06.0.084", "Từ Hữu Tôn", "", "", "", "", "", "Con ông Huân", "Chết sớm", ""),
                    ("258.07.0.125", "258.06.0.085", "Từ Hữu Dái", "", "", "", "", "", "Con ông Giảng", "Tảo một", ""),
                    ("258.07.0.126", "258.06.0.085", "Từ Hữu Lai", "", "Bà Trần Thị...", "", "", "", "Con ông Giảng. Sinh hạ: Từ Hữu Trà, Từ Thị Trừ (lấy chồng về Thạch Tiến), Từ Thị Thứ (lấy Trần Vụ trong làng), Từ Hữu Bậc (Liệt sĩ).", "", ""),
                    ("258.07.0.127", "258.06.0.085", "Từ Hữu Lưu", "", "Bà Nguyễn Thị Thời", "", "", "", "Con thứ 2 ông Giảng. Sinh hạ: Từ Thị Bẹn (lấy ông Trần Dung trong làng), Từ Hữu Tưu (Khoái), Từ Thị Em (lấy ông Phan Âu, Thượng Xuân), Từ Thị... (lấy ông Trần Phu trong làng).", "", ""),
                    ("258.07.0.128", "258.06.0.086", "Từ Hữu Kẹo", "", "Vợ lấy chồng khác", "", "", "", "Con ông Điển.", "Phạp tự", ""),
                    ("258.07.0.129", "258.06.0.086", "Từ Hữu Mật", "", "", "", "", "", "Con ông Điển.", "Tảo vong", ""),
                    ("258.07.0.130", "258.06.0.086", "Từ Hữu Thái", "", "", "", "", "", "Con ông Điển.", "Chết sớm", ""),
                    ("258.07.0.131", "258.06.0.086", "Từ Hữu Thới", "", "", "", "", "", "Con ông Điển.", "Tảo một", ""),
                    ("258.07.0.132", "258.06.0.088", "Từ Hữu Tự", "", "", "", "", "", "Con ông Bồng", "Chết sớm", ""),

                    # ==========================================================
                    # ĐỜI 8 
                    # ==========================================================

                    # ------------------------------------
                    # CHI 1
                    # ------------------------------------                    
                    ("111.08.1.001", "111.07.0.001", "Từ Thị...", "", "Cửu Bẹn", "", "", "", "Con ông Phiệt. Lấy 2 chồng, chồng đầu là ông Điệng; sau lấy ông Cửu Bẹn ở Vĩnh Lộc", "", ""),
                    ("111.08.0.002", "111.07.0.001", "Từ Hữu Điệt", "", "Bà Nguyễn Thị Bốn", "", "", "", "Con ông Phiệt. Sinh hạ: Từ Hữu Vện.", "", ""),
                    ("111.08.1.003", "111.07.0.001", "Từ Thị Đém", "", "", "", "", "", "Con ông Phiệt", "Tảo vong", ""),
                    ("111.08.0.004", "111.07.0.001", "Từ Hữu Việt", "", "Vợ lấy chồng khác", "", "", "", "Con ông Phiệt.", "Phạp tự", ""),
                    ("111.08.0.005", "111.07.0.001", "Từ Hữu Huyền", "Năm", "Bà Nguyễn Thị Vạn", "", "", "", "Con ông Phiệt. Sinh hạ: Từ Hữu Cháu, Từ Hữu Thụ, Từ Hữu Phù (Tửu), Từ Thị Tứ (lấy ông Nguyễn Chung trong làng), Từ Hữu Dấu, Từ Thị Lục (lấy ông Trần Hoàn trong làng).", "", ""),
                    ("111.08.0.006", "111.07.0.001", "Từ Hữu Ca", "", "", "", "", "", "Con ông Phiệt", "Tảo một", ""),
                    ("111.08.1.007", "111.07.0.001", "Từ Thị Bảy", "", "Ba Điêm", "", "", "", "Con ông Phiệt. Lấy ông Ba Điêm trong làng", "Tảo một", ""),
                    ("111.08.1.008", "111.07.0.001", "Từ Thị Bát", "", "", "", "", "", "Con ông Phiệt", "Tảo vong", ""),
                    ("111.08.1.009", "111.07.0.008", "Từ Thị Mực", "", "Cu Láng", "", "", "", "Con ông Lâm. Lấy ông Cu Láng trong làng", "", ""),
                    ("111.08.1.010", "111.07.0.008", "Từ Thị Ba", "", "Không rõ", "", "", "", "Con ông Lâm. Lấy 3 chồng", "", ""),
                    ("111.08.0.011", "111.07.0.008", "Từ Hữu Đồng", "Hường", "Bà Trần Thị Con", "", "", "", "Con đầu ông Lâm. Sinh hạ: Từ Hữu Hường (Liệt sĩ), Từ Hữu Hồng, Từ Hữu Bàng, Từ Thị Thị (lấy về Thượng Lội, Quang Lộc), Từ Hữu Bính, Từ Thị Minh (lấy anh Trần Lục (Cứ) trong làng), Từ Hữu Lương.", "", ""),
                    ("111.08.0.012", "111.07.0.008", "Từ Hữu Địch", "", "", "", "", "", "Con ông Lâm", "Tảo vong", ""),
                    ("111.08.0.013", "111.07.0.008", "Từ Hữu Kế", "Huệ", "Bà Trần Thị Hạ", "", "", "", "Con thứ 2 ông Lâm. Sinh hạ: Từ Thị Huệ, Từ Thị Hoà, Từ Hữu Huy, Từ Thị Hiệu (lấy Nguyễn Minh Thạc, Thượng Xuân), Từ Hữu Hiếu, Từ Thị Hương, Từ Hữu Hoa, Từ Hữu Hoè, Từ Hữu Huề.", "", ""),
                    ("111.08.1.014", "111.07.0.008", "Từ Thị Chút", "", "", "", "", "", "Con ông Lâm", "Chết sớm", ""),
                    ("111.08.0.015", "111.07.0.008", "Từ Hữu Thịnh", "", "", "", "", "", "Con ông Lâm", "Chết sớm", ""),
                    ("111.08.0.016", "111.07.0.009", "Từ Hữu Điệng", "", "", "", "", "", "Con ông Tâm", "Chết sớm", ""),
                    ("111.08.0.017", "111.07.0.009", "Từ Hữu Tiệng", "", "Bà Nguyễn Thị Bình", "", "", "", "Con ông Tâm. Sinh hạ: Từ Thị Chắt (lấy ông Ca trong làng), Từ Hữu Lai, Từ Hữu Phối (Không vợ), Từ Thị Hợp (Không chồng).", "", ""),
                    ("111.08.1.018", "111.07.0.009", "Từ Thị Em", "", "", "", "", "", "Con ông Tâm. Chết đuối", "Chết sớm", ""),
                    ("111.08.0.019", "111.07.0.009", "Từ Hữu Thiện", "", "", "", "", "", "Con ông Tâm", "Tảo một", ""),
                    ("111.08.0.020", "111.07.0.012", "Từ Hữu Nghiệp", "", "", "", "", "", "Con ông Sáng", "Tảo một", ""),
                    ("111.08.0.021", "111.07.0.012", "Từ Hữu Xuân", "", "", "", "", "", "Con ông Sáng", "Tảo vong", ""),
                    ("111.08.0.022", "111.07.0.012", "Từ Hữu Vên", "", "", "", "", "", "Con ông Sáng", "Tảo vong", ""),
                    ("111.08.1.023", "111.07.0.012", "Từ Thị Út", "", "", "", "", "", "Con ông Sáng", "Tảo một", ""),
                    ("111.08.1.024", "111.07.0.012", "Từ Thị Xin", "", "", "", "", "", "Con ông Sáng", "Tảo một", ""),
                    ("111.08.1.025", "111.07.0.012", "Từ Thị Mức", "", "Không rõ", "", "", "", "Con ông Sáng. Lấy chồng không có con (chết)", "", ""), 
                    ("111.08.1.026", "111.07.0.017", "Từ Thị Tuất", "", "Không rõ", "", "", "", "Con ông Xích. Lấy chồng người miền Nam", "", ""),
                    ("111.08.0.027", "111.07.0.018", "Từ Hữu Hào", "", "Bà Trần Thị...", "", "", "", "Con ông Toại. Sinh hạ: Từ Hữu Lượng, Từ Thị Em (lấy ông Trần Thường trong làng), Từ Thị Tựu (lấy ông Nguyễn Ngơi, Thượng Xuân), Từ Hữu Dự (tảo vong), Từ Thị Thương (tảo một).", "", ""),
                    ("111.08.1.028", "111.07.0.018", "Từ Thị Em Nậy", "", "Thực Dư", "", "", "", "Con ông Toại. Lấy ông Thực Dư ở Đại lộc", "", ""),
                    ("111.08.1.029", "111.07.0.018", "Từ Thị Em Con", "", "Nguyễn Khiêm", "", "", "", "Con ông Toại. Lấy ông Nguyễn Khiêm", "", ""),
                    ("111.08.0.030", "111.07.0.018", "Từ Hữu Bốn", "", "", "", "", "", "Con ông Toại", "Chết sớm", ""),
                    ("111.08.0.031", "111.07.0.018", "Từ Hữu Niêm", "", "", "", "", "", "Con ông Toại", "Chết sớm", ""),
                    ("111.08.0.032", "111.07.0.020", "Từ Hữu Nghi", "", "", "", "", "", "Con ông Nghị. Chết lúc khoảng 20 tuổi, Không có vợ con.", "Chết sớm", ""),
                    ("111.08.1.033", "111.07.0.020", "Từ Thị Em", "", "", "", "", "", "Con ông Nghị. Lấy ông Trần Hải trong làng", "", ""),
                    ("111.08.0.034", "111.07.0.020", "Từ Hữu Lợi", "", "", "", "", "", "Con ông Nghị", "Tảo một", ""),
                    ("111.08.0.035", "111.07.0.020", "Từ Hữu Lộc", "", "", "", "", "", "Con ông Nghị", "Chết sớm", ""),
                    ("111.08.1.036", "111.07.0.025", "Từ Thị Xin ", "", "Trần Phúc", "", "", "", "Con ông Luận. Lấy ông Trần Phúc trong làng", "", ""),                   
                    ("111.08.0.037", "111.07.0.025", "Từ Hữu Trợ", "", "Bà Trần Thị Đửu", "", "", "", "Con ông Luận. Sinh hạ: Từ Hữu Khương (Liệt sĩ), Từ Thị Thương (lấy Nguyễn Cược trong làng), Từ Hữu Sâm (Ở Hà Nội).", "", ""),
                    ("111.08.0.038", "111.07.0.025", "Từ Hữu Thú", "Trự", "Bà Trần Thị", "", "", "", "Con ông Luận. Sinh hạ: Từ Thị Tuyết (lấy Trần Hoàn [Hoàn Con] trong làng), Từ Hữu Hợp, Từ Thị Bình.", "", ""),
                    ("111.08.0.039", "111.07.0.025", "Từ Hữu Ngự", "", "", "", "", "", "Con ông Luận", "Tảo một", ""),
                    ("111.08.0.040", "111.07.0.025", "Từ Hữu Sáu", "", "Bà Trần Thị Quế", "", "", "", "Con thứ 3 ông Luận. Đại tá Quân đội. Vợ là Bà Trần Thị Quế ở Đức Thuỷ, Đức Thọ. Sinh hạ: Từ Thị Thuỷ, Từ Thị Hà, Từ Thị Hải, Từ Hữu Đạt.", "", ""),
                    ("111.08.1.041", "111.07.0.025", "Từ Thị Tựu", "", "ông Nhàn", "", "", "", "Con ông Luận. Lấy ông Nhàn xã Vịnh lộc", "", ""),   
                    ("111.08.0.042", "111.07.0.025", "Từ Hữu Kế", "", "Bà Phạm Thị Man", "", "", "", "Con thứ 4 ông Luận. Bộ đội chuyển sang công nhân nhà nước, nghỉ việc. Sinh hạ: Từ Hữu Hùng, Từ Thị Dũng, Từ Thị Hoà, Từ Hữu Côi.", "", ""),
                    ("111.08.0.043", "111.07.0.025", "Từ Hữu Chín ", "", "", "", "", "", "Con ông Luận", "Tảo một", ""),            
                    ("111.08.0.044", "111.07.0.027", "Từ Hữu Số", "", "Bà Trần Thị Khuyển", "", "", "", "Con ông Lệ. Ông chết, bà đi lấy chồng khác. Sinh hạ: Từ Thị Hương (lấy chồng về Đức Thọ).", "Phạp tự", ""),
                    ("111.08.0.045", "111.07.0.027", "Từ Hữu Nhuyến", "Thanh", "Bà Nguyễn Thị Hồng", "", "", "", "Con thứ 2 ông Lệ. Cán bộ xã, huyện, tỉnh (đã nghỉ hưu). Vợ là Bà Nguyễn Thị Hồng ở Nghi Xuân. Sinh hạ: Từ Ngọc Lương, Từ Hữu Long, Từ Thị Lam, Từ Thị Lê, Từ Hữu Lĩnh, Từ Thị Lộc.", "", ""),
                    ("111.08.0.046", "111.07.0.027", "Từ Hữu Tam", "", "", "", "", "", "Con ông Lệ", "Chết sớm", ""),
                    ("111.08.0.047", "111.07.0.030", "Từ Hữu Nhường", "Hiền", "Bà Nguyễn Thị Liêm", "", "", "", "Con đầu ông Nghĩa. Vợ là Bà Nguyễn Thị Liêm ở Quang Lộc. Sinh hạ: Từ Thị Hiền (lấy anh Nguyễn Bảo con ông Nguyễn Toàn), Từ Hữu Thảo (chết sớm), Từ Hữu Cát, Từ Hữu Nhung, Từ Thị Sâm (lấy anh Nguyễn Tú [Chiên]), Từ Thị Liệu (lấy anh Trần Bình con ông Trực), Từ Thị Đào (lấy anh Trần Đình Trọng trong làng), Từ Hữu Xuân.", "", ""),
                    ("111.08.1.048", "111.07.0.030", "Từ Thị Em", "", "", "", "", "", "Con ông Nghĩa. Lấy ông Quỳ (Thành) trong làng", "", ""),
                    ("111.08.0.049", "111.07.0.030", "Từ Hữu Thường", "", "Bà Lê Thị Thanh", "", "", "", "Con trai thứ 2 ông Nghĩa. Công nhân lâm nghiệp (đã nghỉ việc). Vợ là Bà Lê Thị Thanh ở Trung Lộc. Sinh hạ: Từ Hữu Bình, Từ Hữu Minh, Từ Thị Hoà.", "", ""),
                    ("111.08.1.050", "111.07.0.030", "Từ Thị Chút", "", "", "", "", "", "Con ông Nghĩa. Lấy ông Tình trong làng ", "", ""),
                    ("111.08.0.051", "111.07.0.030", "Từ Hữu Tường", "", "Bà Trần Thị Thảo", "", "", "", "Con thứ 3 ông Nghĩa. Công nhân xí nghiệp gang thép Thái Nguyên (đã nghỉ việc). Sinh hạ: Từ Thị Thái, Từ Thị Hoà, Từ Hữu Hùng.", "", ""),
                    ("111.08.0.052", "111.07.0.030", "Từ Hữu Âu", "", "Bà Bùi Thị Cảnh", "", "", "", "Con thứ 4 ông Nghĩa. Vợ là Bà Bùi Thị Cảnh ở Đại Lộc. Sinh hạ: Từ Thị Thuỷ, Từ Thị Lan, Từ Hữu Hoài, Từ Thị Hồng, Từ Hữu Quang, Từ Hữu Quý.", "", ""),
                    ("111.08.0.053", "111.07.0.030", "Từ Hữu Dái", "", "", "", "", "", "Con ông Nghĩa", "Tảo một", ""),

                    # ------------------------------------
                    # CHI 2
                    # ------------------------------------

                    ("122.08.0.067", "122.07.0.035", "Từ Hữu Tựu", "", "Bà Trần Thị Chút", "", "", "", "Con ông Duyệt. Sinh hạ: Từ Thị ... (tảo một), Từ Hữu Tuyến", "", ""),
                    ("122.08.0.068", "122.07.0.035", "Từ Hữu Nựu", "", "Bà Ngô Thị Bảy", "", "", "", "Con thứ 2 ông Duyệt. Sinh hạ: Từ Hữu Cừ, Từ Thị Tỷ (tảo một).", "", ""),
                    ("122.08.1.069", "122.07.0.035", "Từ Thị Tưu", "", "Trần Diệm", "", "", "", "Con đông Duyệt. Lấy ông Trần Diệm trong làng", "", ""),
                    ("122.08.1.070", "122.07.0.035", "Từ Thị Chút", "", "Trần Ngọt", "", "", "", "Con ông Duyệt. Lấy ông Trần Ngọt trong làng", "", ""),
                    ("122.08.1.071", "122.07.0.035", "Từ Thị Chút Em", "", "Nguyễn Hy", "", "", "", "Con ông Duyệt. Lấy ông Nguyễn Hy ở Yên Đồng", "", ""),
                    ("122.08.0.072", "122.07.0.037", "Từ Xuân Cảnh", "", "Bà Trần Thị Nuôi, bà thứ Nguyễn Thị Lan", "", "", "", "Con đầu ông Hợi. Sinh hạ: Từ Thị Chắt (lấy chồng về Sơn Lộc), Từ Thị Xanh (lấy Trần Hạnh [Thành] trong làng), Từ Hữu Anh (tảo một), Từ Hữu Hồng (tảo một), Từ Thị Hường (tảo một), Từ Thị Hạnh, Từ Thị Hiền, Từ Hữu Hoàn, Từ Thị Hằng.", "", ""),
                    ("122.08.0.073", "122.07.0.037", "Từ Hữu Quý", "", "", "", "", "", "Con thứ 2 ông Hợi. Liệt sỹ chống Mỹ.", "Không có con", ""),
                    ("122.08.1.074", "122.07.0.037", "Từ Thị Tỷ", "", "Phan Đàn", "", "", "", "Con ông Hợi. Lấy ông Phan Đàn Xóm Mới", "", ""),
                    ("122.08.0.075", "122.07.0.037", "Từ Hữu Tư", "", "Bà Nguyễn Thị Tứ", "", "", "", "Con thứ 3 ông Hợi. Công nhân nhà nước. Sinh hạ: Từ Thị Liên, Từ Hữu Thành.", "", ""),
                    ("122.08.1.076", "122.07.0.037", "Từ Thị Ngụ", "", "Không rõ", "", "", "", "Con ông Hợi. Lấy chồng về Đức Lâm, Đức Thọ", "", ""),
                    ("122.08.1.077", "122.07.0.037", "Từ Thị Lục", "", "Không rõ", "", "", "", "Con ông Hợi. Lấy chồng về Kỳ Anh", "", ""),
                    ("122.08.1.078", "122.07.0.040", "Từ Thị Đoài", "", "Trần Đại", "", "", "", "Con ông Khai. Lấy ông Trần Đại trữa làng ", "", ""),
                    ("122.08.0.079", "122.07.0.040", "Từ Hữu Lương", "", "Bà Phan Thị Minh", "", "", "", "Con ông Khai (Đoài). Vợ là Bà Phan Thị Minh người Thượng Xuân. Sinh hạ: Từ Hữu Trung, Từ Hữu Thông, Từ Hữu Tiến, Từ Huấn Triển (tảo một), Từ Hữu Trường, Từ Thị Tình (Tảo một), Từ Hữu Thân.", "", ""),
                    ("122.08.1.080", "122.07.0.041", "Từ Thị Xuân", "", "Không rõ", "", "", "", "Con ông Lai (Như). Lấy chồng người ở Sơn Lộc", "", ""),
                    ("122.08.1.081", "122.07.0.041", "Từ Thị Tâm", "", "Ông Tịnh", "", "", "", "Con ông Lai (Như)", "", ""),
                    ("122.08.0.082", "122.07.0.041", "Từ Hữu Tương", "", "Bà Nguyên", "", "", "", "Con ông Lai (Như). Vợ là Bà Nguyên người ở Sơn Lộc Sinh hạ: Từ Thị Hằng, Từ Hữu Đạt.", "", ""),
                    ("123.08.0.083", "123.07.0.042", "Từ Hữu Đa", "", "", "", "", "", "Con ông Kiệp", "Tảo một", ""),
                    ("123.08.0.084", "123.07.0.042", "Từ Hữu Số", "", "Bà Trần Thị Lan", "", "", "", "Con ông Kiệp. Cán bộ quân sự về hưu. Sinh hạ: Từ Thị Hương (lấy chồng), Từ Hữu Quyền, Từ Thị Tâm, Từ Hữu Thắng, Từ Trần Đông - con nuôi.", "", ""),
                    ("123.08.0.085", "123.07.0.042", "Từ Hữu Yêm", "", "Bà Đinh Thị Ngọ", "", "", "", "Con ông Kiệp. Công nhân nhà nước. Sinh hạ: Từ Hữu Hải (chết sớm), Từ Hữu Hoàn, Từ Hữu Ngọc, Từ Thị Hằng.", "", ""),
                    ("123.08.0.086", "123.07.0.042", "Từ Hữu Niềm", "", "Bà Trần Thị Lý", "", "", "", "Con ông Kiệp. Cán bộ Quân đội nghỉ hưu. Vợ là Bà Trần Thị Lý ở Yên Đồng. Sinh hạ: Từ Thị Hoà, Từ Hữu Hùng, Từ Thị Nguyệt, Từ Thị Ngọc, Từ Thị Trâm, Từ Thị Quế.", "", ""),
                    ("123.08.1.087", "123.07.0.042", "Từ Thị Xuân", "", "Nguyễn Cầu", "", "", "", "Con ông Kiệp. Lấy ông Nguyễn Cầu, Trung Xá", "", ""),
                    ("123.08.0.088", "123.07.0.042", "Từ Hữu Xanh", "", "Bà Trần Thị Châu", "", "", "", "Con ông Kiệp. Sinh hạ: Từ Hữu Thuận, Từ Hữu Lợi, Từ Hữu Hải, Từ Hữu Bằng.", "", ""),
                    ("123.08.1.089", "123.07.0.042", "Từ Thị Thanh", "", "Nguyễn Tứ", "", "", "", "Con ông Kiệp. Lấy ông Nguyễn Tứ (Xà) trong làng", "", ""),
                    ("123.08.0.090", "123.07.0.043", "Từ Hữu Nuôi", "Nam", "Bà Trần Thị Phương", "", "", "", "Con ông Điệp. Vợ là Bà Trần Thị Phương ở Khánh Lộc. Sinh hạ: Từ Hữu Dũng.", "", ""),
                    ("123.08.0.091", "123.07.0.043", "Từ Hữu Em", "Tiếp", "Bà Nguyễn Thị Sâm", "", "", "", "Con thứ 2 ông Điệp. Vợ là Bà Nguyễn Thị Sâm ở Khánh Lộc. Sinh hạ: Từ Hữu Phú, Từ Hữu Khánh, Từ Hữu Chương.", "", ""),
                    ("124.08.0.092", "124.07.0.049", "Từ Hữu Chắt", "", "", "", "", "", "Con ông Quang Diệu", "Chết sớm", ""),
                    ("124.08.1.093", "124.07.0.049", "Từ Thị Đào", "", "", "", "", "", "Con ông Quang Diệu", "Tảo vong", ""),
                    ("124.08.1.094", "124.07.0.049", "Từ Thị Lý", "", "", "", "", "", "Con ông Quang Diệu", "Chết sớm", ""),
                    ("124.08.0.095", "124.07.0.049", "Từ Hữu Hạnh", "", "", "", "", "", "Con ông Quang Diệu", "Tảo vong", ""),                    
                    ("124.08.0.096", "124.07.0.049", "Từ Quang Viện", "", "Bà Lưu Thị Nhung", "1962", "", "", "Con ông Quang Diệu. Công nhân nhà nước ở Đắc Lắc. Vợ là Bà Lưu Thị Nhung ở Nam Đàn (1962). Sinh hạ: Từ Thị Hiền, Từ Minh Khoa.", "", ""),
                    ("124.08.0.097", "124.07.0.049", "Từ Quang Xá", "", "Bà Nguyễn Thị Hoa", "1965", "", "", "Con ông Quang Diệu. Vợ là Bà Nguyễn Thị Hoa ở Đại Lộc, 1971-2017, giỗ 15/12 AL. Sinh hạ: Từ Ngọc Mơ (Gái).", "", ""),
                    ("124.08.0.098", "124.07.0.049", "Từ Quang Khánh", "", "Bà Thái Thị Nguyệt", "", "1967", "", "Con ông Quang Diệu. Vợ là Bà Thái Thị Nguyệt (Sinh năm 1972). Sinh hạ: Từ Thị Trang, Từ Thị Ngân, Từ Thị Thắm (mất lúc 5 tuổi), Từ Quang Nam.", "", ""),
                    ("124.08.0.099", "124.07.0.049", "Từ Quang Thuỳ", "", "Bà Nguyễn Thị Hường", "1970", "", "", "Con ông Quang Diệu. Thượng tá, Cán bộ Quân đội. Vợ là Nguyễn Thị Hường ở Thịnh Lộc, sinh năm 1989. Sinh hạ: Từ Anh Thư, Từ Anh Thơ, Từ Minh Hiếu.", "", ""),
                    ("124.08.0.100", "124.07.0.055", "Từ Hữu Phú", "", "Bà Lê Thị Cúc", "", "2020", "", "Con đầu ông Son. Cán bộ Quân đội nghỉ hưu. Vợ là Bà Lê Thị Cúc ở Hương Khê. Sinh hạ: Từ Hải Thành, Từ Thị Hương Xuân, Từ Thị Minh Trang.", "", ""),
                    ("124.08.1.101", "124.07.0.055", "Từ Thị Ngư", "", "Thái Kỳ", "", "", "", "Con ông Son. Lấy ông Thái Kỳ xóm mới", "", ""),
                    ("124.08.1.102", "124.07.0.055", "Từ Thị Nhung", "", "Không rõ", "", "", "", "Con ông Son. Lấy về Yên Lộc, sau đó chồng nghiện rượu nên bỏ vào Lâm Đồng làm ăn", "", ""),
                    ("124.08.0.103", "124.07.0.055", "Từ Hữu Huy", "", "Bà Trần Thị Tâm", "1966", "", "", "Con thứ 2 ông Son. Vợ là Bà Trần Thị Tâm ở Yên Đồng. Sinh hạ: Từ Hữu Hoàng, Từ Quang Hiệp, Từ Thị Phương.", "", ""),
                    ("124.08.1.104", "124.07.0.055", "Từ Thị Quy", "", "Trần Hải", "1970", "", "", "Con ông Son. Lấy anh Trần Hải (Xứ) trong làng", "", ""),
                    ("124.08.0.105", "124.07.0.055", "Từ Hữu Quý", "", "Bà Nguyễn Thị Mùi", "1972", "", "", "Con thứ 3 ông Son. Vợ là Bà Nguyễn Thị Mùi ở Thượng Xuân. Sinh hạ: Từ Nhật Lương, Từ Nam Thắng.", "", ""),
                    ("124.08.0.106", "124.07.0.062", "Từ Hữu Khang", "", "Bà Trần Thị Thị", "", "", "", "Con đầu ông Chuột. Vợ là Bà Trần Thị Thị ở giữa làng). Sinh hạ: Từ Thị Hiền, Từ Thị Hoà.", "Phạp tự", ""),
                    ("124.08.0.107", "124.07.0.062", "Từ Thị Thái", "", "Không lấy chồng", "", "", "", "Con ông Chuột. Không lấy chồng", "", ""),
                    ("124.08.0.108", "124.07.0.062", "Từ Hữu Bình", "", "Bà Trần Thị Xuân", "", "", "", "Con ông Chuột. Vợ là Bà Trần Thị Xuân ở giữa làng. Sinh hạ: Từ Hữu Sâm, Từ Thị Phượng, Từ Hữu Bảo.", "", ""),
                    ("124.08.0.109", "124.07.0.065", "Từ Hữu Giáp", "", "", "", "", "", "Con ông Thiện.", "Chết sớm", ""),
                    ("124.08.0.110", "124.07.0.065", "Từ Hữu Cường", "", "Bà Nguyễn Thị Thuận", "", "", "", "Con ông Thiện. Vợ là Bà Nguyễn Thị Thuận ở Đại Lộc. Sinh hạ: Từ Hữu Đức.", "", ""),
                    ("124.08.0.111", "124.07.0.065", "Từ Hữu Thành", "", "", "", "", "", "Con ông Thiện.", "Chết sớm", ""),
                    ("124.08.0.112", "124.07.0.065", "Từ Hữu Mạnh", "", "Bà Trần Thị Lý", "", "", "", "Con ông Thiện. Vợ là Bà Trần Thị Lý ở Thạch Ngọc. Sinh hạ: Từ Thị Khánh Huyền, Từ Thị Khánh Minh, Từ Hữu Duy.", "", ""),

                    # ------------------------------------
                    # CHI 3
                    # ------------------------------------
                    ("135.08.1.113", "135.07.0.071", "Từ Thị Thộ", "", "", "", "", "", "Con ông Mục", "Chết sớm", ""),
                    ("135.08.0.114", "135.07.0.071", "Từ Hữu Thự", "", "Bà Trần Thị Em", "", "", "", "Con ông Mục. Sinh hạ: Từ Hữu Hoà, Từ Hữu Bình, Từ Hữu Hạnh, Từ Thị Bính (lấy chồng Quang Lộc), Từ Thị Tý (lấy chồng Tùng Lộc), Từ Thị Vân (lấy chồng Diễn Châu, Nghệ An).", "", ""),
                    ("135.08.1.115", "135.07.0.075", "Từ Thị Xanh", "", "Không rõ", "", "", "", "Con ông Mậu. Lấy chồng người miền Nam", "", ""),
                    ("135.08.1.116", "135.07.0.075", "Từ Thị Dần", "", "Không lấy chồng", "", "", "", "Con ông Mậu. Không lấy chồng", "Chết sớm", ""),
                    ("135.08.1.117", "135.07.0.075", "Từ Thị Tam", "", "", "", "", "", "Con ông Mậu", "Chết sớm", ""),
                    ("135.08.1.118", "135.07.0.075", "Từ Thị Tứ", "", "Không lấy chồng", "", "", "", "Con ông Mậu. Không lấy chồng", "", ""),
                    ("135.08.0.119", "135.07.0.085", "Từ Hữu Trì", "Đệ", "Bà cả Trần Thị Đị, Bà hai Đào Thị Bàn", "", "", "", "Con ông Trù. Sinh hạ: Từ Thị Hoa (lấy chồng Hương Khê), Từ Thị Lan, Từ Thị Bình (con bà hai).", "Phạp tự", ""),
                    ("135.08.0.120", "135.07.0.085", "Từ Hữu Thái", "Thỉnh", "Bà Đào Thị Nhân", "", "", "", "Con thứ 2 ông Trù. Sinh hạ: Từ Hữu Tân, Từ Hữu Thân, Từ Thị Ái, Từ Hữu Hùng, Từ Thị Dũng, Từ Hữu Hoà.", "", ""),
                    ("135.08.1.121", "135.07.0.085", "Từ Thị Chin", "", "", "", "", "", "Con ông Trù. Lấy chồng về Đại lộc", "", ""),
                    ("135.08.1.122", "135.07.0.085", "Từ Thị Kẹm", "", "", "", "", "", "Con ông Trù", "Chết sớm", ""),
                    ("135.08.0.123", "135.07.0.085", "Từ Hữu Ô", "", "", "", "", "", "Con ông Trù", "Chết sớm", ""),
                    ("135.08.0.124", "135.07.0.085", "Từ Hữu Mạ", "", "", "", "", "", "Con ông Trù", "Chết sớm", ""),
                    ("135.08.1.125", "135.07.0.092", "Từ Thị Lan", "", "Không rõ", "", "", "", "Con ông Việt", "", ""),
                    ("135.08.0.126", "135.07.0.092", "Từ Hữu Nam", "Từ Hoa Nam", "Bà cả Trương Thị Thảo, Bà hai Nguyễn Thanh Chung", "", "", "", "Con ông Việt. Sinh hạ: Từ Hoàng Hải, Từ Mai Ly, Từ Mai Linh (con bà hai).", "", ""),
                    ("135.08.1.127", "135.07.0.092", "Từ Thị Hải Anh", "", "Không rõ", "", "", "", "Con ông Việt", "", ""),
                    ("135.08.1.128", "135.07.0.093", "Từ Thị Hạnh", "", "", "", "", "", "Con ông Lục", "Chết sớm", ""),
                    ("135.08.1.129", "135.07.0.093", "Từ Thị Phúc", "", "", "", "", "", "Con ông Lục", "Chết sớm", ""),
                    ("135.08.1.130", "135.07.0.093", "Từ Thị Thu Hà", "", "Nguyễn Tâm", "", "", "", "Con ông Lục. Lấy anh Nguyễn Tâm (Chung), trong làng", "", ""),
                    ("135.08.1.131", "135.07.0.093", "Từ Thị Nhung", "", "", "", "", "", "Con ông Lục. Chết đuối", "Chết sớm", ""),
                    ("135.08.0.132", "135.07.0.093", "Từ Hữu Hoà", "", "Bà Lê Thị Kim Hiền", "", "", "", "Con ông Lục (Quang, Thuận, Bút). Đại tá Quân đội nghỉ hưu tại Hà Nội. Sinh hạ: Từ Thanh Huyền (1993), Từ Tiến Dũng (1999).", "", ""),
                    ("135.08.1.133", "135.07.0.093", "Từ Thị Hiệp", "", "Không rõ", "", "", "", "Con ông Lục. Lấy chồng về Sơn Lộc (Chết sớm)", "", ""),
                    ("135.08.0.134", "135.07.0.093", "Từ Hữu Huấn", "", "Bà Nguyễn Thị Hà Hạnh", "", "", "", "Con ông Lục. ở Hà Nội. Sinh hạ: Từ Phương Thảo, Từ Phương Hiếu, Từ Nguyên Anh.", "", ""),
                    ("135.08.1.135", "135.07.0.095", "Từ Thị Thái", "", "Không rõ", "", "", "", "Con ông Tám", "", ""),
                    ("135.08.1.136", "135.07.0.095", "Từ Thị Bình", "", "Không rõ", "", "", "", "Con ông Tám", "", ""),
                    ("135.08.1.137", "135.07.0.095", "Từ Thị Minh", "", "Không rõ", "", "", "", "Con ông Tám", "", ""),
                    ("135.08.1.138", "135.07.0.095", "Từ Thị Thìn", "", "Không rõ", "", "", "", "Con ông Tám", "", ""),
                    ("135.08.0.139", "135.07.0.095", "Từ Hữu Sang", "", "Bà Phan Thị Hương", "", "", "", "Con ông Tám. Chết sớm. Sinh hạ: Từ Hữu Phương (Quảng Bình).", "", ""),
                    ("135.08.0.140", "135.07.0.095", "Từ Hữu Trọng", "", "Bà Đinh Thị Thu Hải", "", "", "", "Con ông Tám. Sinh hạ: Từ Hải Đăng (Quảng Bình).", "", ""),

                    # ------------------------------------
                    # CHI 4
                    # ------------------------------------                
                    ("246.08.0.141", "246.07.0.098", "Từ Hữu Mộc", "", "", "", "", "", "Con ông Bạt. Đi Lào chết", "Chết sớm", ""),
                    ("246.08.0.142", "246.07.0.098", "Từ Hữu Phương", "", "", "", "", "", "Con ông Bạt", "Chết sớm", ""),
                    ("246.08.0.143", "246.07.0.098", "Từ Hữu Cương", "", "Bà Trần Thị Tần", "", "", "", "Con ông Bạt. Ông làm cán bộ Đảng và chính quyền xã HTX. Sinh hạ: Từ Thị Xuân (Lấy anh Thanh (Thống) ở Dư nại, Từ Hữu Hạ, Từ Thị Thu (Lấy anh Trần Cần Trong xã, Từ Hữu Đông.", "", ""),
                    ("246.08.1.144", "246.07.0.098", "Từ Thị Ngọ", "", "Trần Thản", "", "", "", "Con ông Bạt. Lấy ông Trần Thản trong làng", "", ""),
                    ("246.08.1.145", "246.07.0.099", "Từ Thị Chắn", "", "", "", "", "", "Con ông Nhiếp", "Tảo vong", ""),
                    ("246.08.1.146", "246.07.0.099", "Từ Thị Chắt", "", "Trần Dương", "", "", "", "Con ông Nhiếp. Lấy ông Trần Dương, Yên Đồng", "", ""),
                    ("246.08.0.147", "246.07.0.099", "Từ Hữu Tượng", "", "Bà Trần Thị Mảy", "", "", "", "Con ông Nhiếp. Sinh hạ: Từ Thị Dược, Từ Thị Tâm (lấy chồng về Yên Đồng), Từ Hữu Tam (liệt sĩ), Từ Thị Tứ, Từ Hữu Nam, Từ Hữu Lục, Từ Hữu Thị (chết sớm), Từ Hữu Thành, Từ Hữu Lập (chết sớm), Từ Thị Minh.", "", ""),
                    ("246.08.0.148", "246.07.0.099", "Từ Hữu Hình", "Hảo", "", "", "", "", "Con thứ 2 ông Nhiếp. Ông là cán bộ quân sự chống Pháp - Liệt sĩ, được truy tặng 3 huân chương.", "Không có con", ""),
                    ("246.08.0.149", "246.07.0.099", "Từ Hữu Chất", "", "Bà Ngô Thị Bính", "", "", "", "Con ông Nhiếp. Ông trước làm cán bộ thương nghiệp Huyện, Tỉnh nghỉ hưu. Sinh hạ: Từ Mạnh Mậu, Từ Thị Kiểu (Lấy chồng về Sơn Lộc), Từ Thị Thu (Lấy Trần Choan trong làng), Từ Quốc Lệ, Từ Quốc Đạt, Từ Thị Đỏ (Tảo vong).", "", ""),
                    ("246.08.0.150", "246.07.0.101", "Từ Hữu Tuất", "", "", "", "", "", "Con ông Xỉ", "Tảo một", ""),
                    ("246.08.1.151", "246.07.0.101", "Từ Thị Yên", "", "Nguyễn Liêu", "", "", "", "Con ông Xỉ. Lấy ông Nguyễn Liêu trong làng", "Tảo một", ""),
                    ("246.08.0.152", "246.07.0.101", "Từ Hữu Dần", "", "", "", "", "", "Con ông Xỉ", "Chết sớm", ""),
                    ("246.08.0.153", "246.07.0.101", "Từ Hữu Thìn", "", "", "", "", "", "Con ông Xỉ", "Chết sớm", ""),                    
                    ("246.08.0.154", "246.07.0.102", "Từ Quang Bạng", "", "Bà Trần Thị Thảng", "", "", "", "Con đầu ông Dị. Sinh hạ: Từ Thị Hạnh (Lấy chồng về Quang Lộc), Từ Hữu Phúc.", "", ""),
                    ("246.08.0.155", "246.07.0.102", "Từ Quang Hộ", "Lý", "Bà Trần Thị Khuyển", "", "", "", "Con thứ 2 ông Dị. Sinh hạ: Từ Hải Lý, Từ Thị Tình (chết), Từ Thị Công, Từ Thị Ty, Từ Hữu Sơn, Từ Hữu Lam.", "", ""),
                    ("246.08.0.156", "246.07.0.102", "Từ Hữu Châu ", "Khánh", "Bà cả Nguyễn Thị Xuân, thứ: Nguyễn Thị Liên", "", "", "", "Con thứ 3 ông Dị. Sinh hạ: Từ Thị Mỹ cán bộ ở Gia Lai(lấy chồng), Từ Thị Hoà (lấy chồng về Quang Lộc), Từ Thị Tâm giáo viên ở Gia Lai(lấy chồng), Từ Thị Sâm, Từ Hữu Thắng, Từ Thị Lộc, Từ Hữu Lợi.", "", ""),


                    # ------------------------------------
                    # CHI 5
                    # ------------------------------------
                    ("258.08.1.157", "258.07.0.108", "Từ Thị Hiểu", "", "Trần Chiểu", "", "", "", "Con ông Hoài. Lấy ông Trần Chiểu trong làng", "", ""),
                    ("258.08.0.158", "258.07.0.108", "Từ Hữu Điểu", "Trung", "Bà Trần Thị Hai", "", "", "", "Con ông Hoài. Sinh hạ: Từ Thị Cháu (lấy chồng người Quang Lộc), Từ Hữu Loan, Từ Hữu Ba, Từ Thị Tỷ (lấy anh Trần Thành(Phu) trong làng), Từ Thị Xuân (lấy chồng về Nghi Xuân).", "", ""),
                    ("258.08.0.159", "258.07.0.108", "Từ Hữu Tiếu", "Phán", "Bà Nguyễn Thị Con", "", "", "", "Con ông Hoài. Ông trước làm cán bộ đảng uỷ và uỷ ban xã. Sinh hạ: Từ Hữu Phán, Từ Hữu Đán (mất sớm), Từ Thị Hoà (lấy chồng về Thuận Lộc), Từ Thị Chất (lấy chồng về Thạch Đài, Thạch Hà), Từ Hữu Tường (Liệt sỹ), Từ Hữu Lục, Từ Hữu Lương.", "", ""),
                    ("258.08.1.160", "258.07.0.112", "Từ Thị Dệ", "", "Nguyễn Văn Thống", "", "", "", "Con ông Nha. Lấy ông Nguyễn Văn Thống ở Dư Nại", "", ""),
                    ("258.08.1.161", "258.07.0.112", "Từ Thị Hòa", "", "ông Hành", "", "", "", "Con ông Nha. Lấy người Mỹ Lộc", "", ""),
                    ("258.08.1.162", "258.07.0.112", "Từ Thị Dục", "", "Thế Nhiên", "", "", "", "Con ông Nha. Lấy ông Thế Nhiên ở Thượng Xuân", "", ""),
                    ("258.08.1.163", "258.07.0.112", "Từ Thị Phúc", "", "Trần Á", "", "", "", "Con ông Nha. Lấy ông Trần Á trong làng", "", ""),
                    ("258.08.1.164", "258.07.0.112", "Từ Thị Tỷ", "", "Nguyễn Hành", "", "", "", "Con ông Nha. Lấy Nguyễn Hành ở Dư Nại", "", ""),
                    ("258.08.0.165", "258.07.0.112", "Từ Hữu Tung", "", "", "", "", "", "Con ông Nha", "Tảo vong", ""),
                    ("258.08.1.166", "258.07.0.115", "Từ Thị Sào", "", "Không rõ", "", "", "", "Con ông Trại. Lấy chồng về Kẻ Mòi", "", ""),
                    ("258.08.1.167", "258.07.0.117", "Từ Thị Em", "", "", "", "", "", "Con ông Nhạc. Lấy ông Phan Liêu Xóm Mới", "", ""),
                    ("258.08.0.168", "258.07.0.117", "Từ Hữu Đề", "", "", "", "", "", "Con ông Nhạc. Ông làm Hội trưởng hội Đông y tỉnh Nghệ Tĩnh. Sinh hạ: Từ Hữu Đàn, Từ Hữu Liêm, Từ Hữu Thanh.", "", ""),
                    ("258.08.0.169", "258.07.0.120", "Từ Hữu Dạ", "", "", "", "", "", "Con ông Vi", "Tảo một", ""),
                    ("258.08.0.170", "258.07.0.120", "Từ Hữu Túc", "Thân", "Bà Nguyễn Thị Hai", "", "", "", "Con ông Vi đời thứ 7. Ông trước làm nghề thợ mộc. Sinh hạ: Từ Thị Thìn (lấy chồng về Trung Lộc), Từ Thị Kiêm (lấy ông Trần Đạt trong làng), Từ Thị Yêm (tảo một), Từ Thị Chế (tảo một), Từ Hữu Đỏ (tảo một), Từ Hữu Tuý, Từ Thị Tuyết (lấy ông Trần Tùng trong làng), Từ Thị Bình (lấy chồng về Nghi Xuân).", "", ""),
                    ("258.08.1.171", "258.07.0.120", "Từ Thị Đạn", "", "Trần Bá", "", "", "", "Con ông Vi. Lấy ông Trần Bá trong làng", "", ""),
                    ("258.08.0.172", "258.07.0.121", "Từ Hữu Vân", "Bính", "Bà Trần Thị Đém", "", "", "", "Con ông Lậu. Sinh hạ: Từ Thị Bính (lấy chồng về Quang Lộc), Từ Thị Tam (lấy Trần Ngoạt trong làng), Từ Thị Lục (lấy chồng về Hương Sơn), Từ Thị Liên (ở Đắk Lắk, không lấy chồng ), Từ Thị Xuân (lấy chồng về Thạch Hà), Từ Hữu Hậu.", "", ""),
                    ("258.08.0.173", "258.07.0.121", "Từ Hữu Đằng", "", "", "", "", "", "Con ông Lậu. Ông làm công nhân ở Nghĩa Đàn - Nghệ An. Sinh hạ: Từ Hợp, Từ Hoà, Từ Hoa, Từ Lý, Từ Long, Từ Thành, Từ Bình.", "", ""),
                    ("258.08.0.174", "258.07.0.121", "Từ Hữu Bầng", "", "", "", "", "", "Con ông Lậu. Liệt sỹ chống Pháp.", "Không có con", ""),
                    ("258.08.0.175", "258.07.0.121", "Từ Hữu Nhuệ", "", "", "", "", "", "Con ông Lậu. Công nhân ở Nghĩa Đàn, Nghệ An. Sinh hạ: Từ Hữu Thanh, Từ Hữu Bình.", "", ""),
                    ("258.08.0.176", "258.07.0.122", "Từ Hữu Sàn", "", "Bà Trần Thị Chút", "", "", "", "Con ông Ứng. Sinh hạ: Từ Hữu Lý, Từ Hữu Hộ (Liệt sỹ), Từ Hữu Minh.", "", ""),
                    ("258.08.1.177", "258.07.0.122", "Từ Thị Em", "", "Trần Tá", "", "", "", "Con ông Ứng. Lấy ông Trần Tá trong làng", "", ""),
                    ("258.08.0.178", "258.07.0.122", "Từ Hữu Hiệt", "", "Bà Trần Thị Ngụ", "", "", "", "Con ông Ứng. Làm Trưởng ban, y dược thú y xã, được tặng thưởng Huân chương. Sinh hạ: Từ Thị Xuân (tảo một), Từ Thị Đào (lấy chồng về Thạch Đinh), Từ Thị Huệ (lấy chồng về Thạch Tượng), Từ Thị Lan (lấy chồng về Đức Lâm, Đức Thọ), Từ Hữu Toàn, Từ Hữu Tiến, Từ Hữu Dũng.", "", ""),
                    ("258.08.1.179", "258.07.0.122", "Từ Thị Tỷ", "", "Nguyễn Xà", "", "", "", "Con ông Ứng. Lấy ông Nguyễn Xà trong làng", "", ""),
                    ("258.08.0.180", "258.07.0.122", "Từ Hữu Sàng", "Nhu", "Bà Nguyễn Thị Tỷ", "", "", "", "Con thứ 3 ông Ứng đời thứ 7. Ông trước đi bộ đội chống Pháp, được tặng thưởng 2 Huân chương. Sinh hạ: Từ Thị Nhu (lấy chồng về Đại Lộc), Từ Hữu Giáp, Từ Thị Huệ, Từ Hữu Huề.", "", ""),
                    ("258.08.0.181", "258.07.0.126", "Từ Hữu Trà", "", "Bà Trần Thị Nuôi", "", "", "", "Con ông Lai. Ông trước làm cán bộ Hợp tác xã nhiều nhiệm kỳ. Sinh hạ: Từ Hữu Triển (Liệt sỹ), Từ Hữu Đại, Từ Thị Thanh (lấy Trần Hùng (Xương) trong làng).", "", ""),
                    ("258.08.1.182", "258.07.0.126", "Từ Thị Trừ", "", "Không rõ", "", "", "", "Con ông Lai. Lấy chồng về Thạch Tiến", "", ""),
                    ("258.08.1.183", "258.07.0.126", "Từ Thị Thứ", "", "Trần Vụ", "", "", "", "Con ông Lai. Lấy Trần Vụ trong làng ", "", ""),
                    ("258.08.0.184", "258.07.0.126", "Từ Hữu Bậc", "", "", "", "", "", "Con ông Lai. Liệt sỹ", "Không có con", ""),
                    ("258.08.1.185", "258.07.0.127", "Từ Thị Bẹn", "", "Trần Dung", "", "", "", "Con ông Lưu. Lấy ông Trần Dung trong làng ", "", ""),
                    ("258.08.0.186", "258.07.0.127", "Từ Hữu Tưu", "Khoái", "Bà Trần Thị Luận", "", "", "", "Con ông Lưu. Sinh hạ: Từ Hữu Nậy (Từ Trần – 47 tuổi), Từ Hữu Em (Hoài), Từ Thị Tỷ (lấy Trần Tịnh trong làng), Từ Thị Tứ (lấy chồng về Thanh Hoá), Từ Hữu Năm (chết sớm), Từ Thị Sáu (lấy Trần Tam (cứ) trong làng), Từ Hữu Chất, Từ Hữu Tạo, Từ Hữu Bình, Từ Hữu Chín.", "", ""),
                    ("258.08.1.187", "258.07.0.127", "Từ Thị ...", "", "Trần Phu", "", "", "", "Con ông Lưu. Lấy ông Trần Phu trong làng", "", ""),
                    ("258.08.1.188", "258.07.0.127", "Từ Thị Em", "", "Phan Âu", "", "", "", "Con ông Lưu. Lấy ông Phan Âu ở Thượng Xuân", "", ""),
                    
                    # ==========================================================
                    # ĐỜI 9 
                    # ==========================================================

                    # ------------------------------------
                    # CHI 1
                    # ------------------------------------
                    ("111.09.0.001", "111.08.0.002", "Từ Hữu Vện", "Hà", "Bà Trần Thị Nghĩa", "", "", "", "Con ông Điệt. Ông làm nghề thợ mộc. Sinh hạ: Từ Hữu Đắc, Từ Hữu Bật, Từ Hữu Phú, Từ Hữu Tư [mất sớm], Từ Hữu Ngụ, Từ Thị Xuân [chồng Thạch Sơn, Thạch Hà].", "", ""),
                    ("111.09.0.002", "111.08.0.005", "Từ Hữu Cháu", "", "Bà: lấy chồng khác", "", "", "", "Con ông Huyền. Sinh hạ: Từ Hữu Tân.", "", ""),
                    ("111.09.0.003", "111.08.0.005", "Từ Hữu Thụ", "Dụng", "Bà Trần Thị Đởm", "", "", "", "Con thứ 2 ông Huyền. Sinh hạ: Từ Thị Hoà [lấy chồng trong làng], Từ Thị Dũng [lấy ông Trần Đại trong làng], Từ Thị Bình, Từ Hữu Đính, Từ Thị Minh, Từ Hữu Bính.", "", ""),
                    ("111.09.0.004", "111.08.0.005", "Từ Hữu Phù", "Tửu", "Bà Trần Thị Em", "", "", "", "Con thứ 3 ông Huyền. Ông trước làm cán bộ xã và HTX nhiều nhiệm kỳ. Sinh hạ: Từ Thị Hương [lấy chồng về Xóm Mới], Từ Hữu Đạt, Từ Thị Xuân [lấy anh Trần Tám(Cân)trong làng].", "", ""),
                    ("111.09.1.005", "111.08.0.005", "Từ Thị Tứ", "", "Nguyễn Chung", "", "", "", "Con ông Huyền. Lấy ông Nguyễn Chung trong làng", "", ""),
                    ("111.09.0.006", "111.08.0.005", "Từ Hữu Dấu", "", "Bà Nguyễn Thị Hoa", "", "", "", "Con thứ 4 ông Huyền. Sinh hạ: Từ Hữu Huề, Từ Hữu Huê, Từ Hữu Hoà, Từ Thị Phương.", "", ""),
                    ("111.09.1.007", "111.08.0.005", "Từ Thị Lục", "", "Trần Hoàn", "", "", "", "Con ông Huyền. Lấy ông Trần Hoàn trong làng", "", ""),
                    ("111.09.0.008", "111.08.0.011", "Từ Hữu Hường", "", "", "", "", "", "Con ông Đồng. Ông là liệt sỹ, vợ về lấy chồng khác.", "Không có con", ""),
                    ("111.09.0.009", "111.08.0.011", "Từ Hữu Hồng", "", "Bà Trần Thị Minh", "", "", "", "Con thứ 2 ông Đồng. Lấy Bà Trần Thị Minh ở Thạch Hà. Sinh hạ: Từ Hữu Quân, Từ Thị Thanh [chết đuối], Từ Thị Lý, Từ Hữu Mạo.", "", ""),
                    ("111.09.0.010", "111.08.0.011", "Từ Hữu Bàng", "", "Bà Nguyễn Thị Chắt", "", "", "", "Con thứ 3 ông Đồng. Sinh hạ: Từ Thị Hoa, Từ Hữu Lan, Từ Thị Phương.", "", ""),
                    ("111.09.1.011", "111.08.0.011", "Từ Thị Thị", "", "Không rõ", "", "", "", "Con ông Đồng. lấy về Thượng Lội, Quang Lộc", "", ""),
                    ("111.09.0.012", "111.08.0.011", "Từ Hữu Bính", "", "Bà Nguyễn Thị Hường", "", "", "", "Con thứ 4 ông Đồng. Lấy Bà Nguyễn Thị Hường ở Hương Khê. Sinh hạ: Từ Thị Nga, Từ Hữu Sửu.", "", ""),
                    ("111.09.1.013", "111.08.0.011", "Từ Thị Minh", "", "Trần Lục", "", "", "", "Con ông Đồng. lấy anh Trần Lục (Cứ) trong làng", "", ""),
                    ("111.09.0.014", "111.08.0.011", "Từ Hữu Lương", "", "Bà Trần Thị Bính", "", "", "", "Con thứ 5 ông Đồng. Sinh hạ: Từ Hữu Hải, Từ Hữu Hiệp, Từ Thị Thuỷ.", "", ""),
                    ("111.09.1.015", "111.08.0.013", "Từ Thị Huệ", "", "Không rõ", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.1.016", "111.08.0.013", "Từ Thị Hòa", "", "Không rõ", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.0.017", "111.08.0.013", "Từ Hữu Huy", "", "Bà Trần Thị Châu", "", "", "", "Con ông Kế. Sinh hạ: Từ Thị Thanh, Từ Hữu Danh, Từ Hữu Nhân, Từ Hữu Nghĩa.", "", ""),
                    ("111.09.1.018", "111.08.0.013", "Từ Thị Hiệu", "", "Nguyễn Minh Thạc", "", "", "", "Con ông Kế. Lấy Nguyễn Minh Thạc Thượng Xuân", "", ""),
                    ("111.09.0.019", "111.08.0.013", "Từ Hữu Hiếu", "", "Nguyễn Thị ...", "", "", "", "Con ông Kế. Sinh hạ: Từ Thị Hoài [con bà Vân], đang cập nhật.", "", ""),
                    ("111.09.1.020", "111.08.0.013", "Từ Thị Hương", "", "Không rõ", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.0.021", "111.08.0.013", "Từ Hữu Hoa", "", "", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.0.022", "111.08.0.013", "Từ Hữu Hoè", "", "", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.0.023", "111.08.0.013", "Từ Hữu Huề", "", "đang cập nhật", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.1.024", "111.08.0.017", "Từ Thị Chắt", "", "Lương Văn Ca", "", "", "", "Con ông Tiệng. Lấy Lương Văn Ca trong làng", "", ""), 
                    ("111.09.0.025", "111.08.0.017", "Từ Hữu Lai", "", "Bà Trần Thị Thanh", "", "", "", "Con ông Tiệng. Sinh hạ: Từ Hữu Cháu, Từ Thị Lý, Từ Hữu Quy, Từ Hữu Định, Từ Hữu Luật, Từ Thị Luận, Từ Hữu Duẩn.", "", ""),
                    ("111.09.0.026", "111.08.0.017", "Từ Hữu Phối", "", "Không lấy vợ", "", "", "", "Con ông Tiệng. Sống đến già, không lấy vợ.", "Không có con", ""),
                    ("111.09.1.027", "111.08.0.017", "Từ Thị Hợp", "", "Không lấy chồng", "", "", "", "Con ông Tiệng. Sống đến già, không lấy chồng.", "Không có con", ""), 
                    ("111.09.0.028", "111.08.0.027", "Từ Hữu Lượng", "Nghiệm", "Bà Nguyễn Thị Ngóec ", "", "", "", "Con ông Hào. Lấy Bà Nguyễn Thị Ngóec ở Đại Lộc. Sinh hạ: Từ Hữu Cháu [tảo vong], Từ Thị Nghiệm, Từ Hữu Sơn, Từ Hữu Thân, Từ Hữu Thìn [liệt sỹ], Từ Hữu Hải, Từ Thị Hà, Từ Hữu Nga.", "", ""),
                    ("111.09.1.029", "111.08.0.027", "Từ Thị Em", "", "Trần Thường", "", "", "", "Con ông Hào. Lấy ông Trần Thường trong làng", "", ""),
                    ("111.09.1.030", "111.08.0.027", "Từ Thị Tựu", "", "Nguyễn Ngơi", "", "", "", "Con ông Hào. Lấy ông Nguyễn Ngơi Thượng xuân", "", ""),
                    ("111.09.0.031", "111.08.0.027", "Từ Hữu Dự", "", "", "", "", "", "Con ông Hào", "Tảo vong", ""),
                    ("111.09.0.032", "111.08.0.027", "Từ Thị Thương", "", "", "", "", "", "Con ông Hào", "Tảo một", ""),
                    ("111.09.0.033", "111.08.0.037", "Từ Hữu Khương", "", "", "", "", "", "Con ông Trợ. Liệt sỹ", "Không có con", ""),
                    ("111.09.1.034", "111.08.0.037", "Từ Thị Thương", "", "Nguyễn Cược", "", "", "", "Con ông Trợ. Lấy Nguyễn Cược trong làng", "", ""),
                    ("111.09.0.035", "111.08.0.037", "Từ Hữu Sâm", "", "Bà Lê Thị Hằng", "", "", "", "Con ông Trợ. Kỹ sư, cán bộ nhà nước. ở Hà Nội. Sinh hạ 3 người con gái: Từ Minh Nguyệt, Từ Nguyệt Nga, Từ Lê Nguyệt Ánh.", "", ""),
                    ("111.09.1.036", "111.08.0.038", "Từ Thị Tuyết", "", "Trần Hoàn", "", "", "", "Con ông Thú. Lấy Trần Hoàn (Hoàn Con) trong làng", "", ""),
                    ("111.09.0.037", "111.08.0.038", "Từ Hữu Hợp", "", "Bà Đào Thị Liên", "", "", "", "Con ông Thú. Lấy Bà Đào Thị Liên ở Quang Lộc. Sinh hạ: Từ Thị Hường, Từ Hữu Định, Từ Hữu Tuấn.", "", ""),
                    ("111.09.1.038", "111.08.0.038", "Từ Thị Bình", "", "Trần Hoàn", "", "", "", "Con ông Thú. Lấy Trần Hoàn (Hoàn Con) trong làng", "", ""),
                    ("111.09.1.039", "111.08.0.040", "Từ Thị Thủy", "", "Không rõ", "", "", "", "Con ông Sáu. Đang cập nhật.", "", ""),
                    ("111.09.1.040", "111.08.0.040", "Từ Thị Hà", "", "Không rõ", "", "", "", "Con ông Sáu. Đang cập nhật.", "", ""),
                    ("111.09.1.041", "111.08.0.040", "Từ Thị Hải", "", "Không rõ", "", "", "", "Con ông Sáu. Đang cập nhật.", "", ""),
                    ("111.09.0.042", "111.08.0.040", "Từ Hữu Đạt", "", "Bà Nguyễn Thị Huệ", "", "", "", "Con ông Sáu. Sinh hạ: Từ Hải Minh, Từ Ngân Khánh.", "", ""),
                    ("111.09.0.043", "111.08.0.042", "Từ Hữu Hùng", "", "đang cập nhật", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.1.044", "111.08.0.042", "Từ Thị Dũng", "", "đang cập nhật", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.1.045", "111.08.0.042", "Từ Thị Hòa", "", "đang cập nhật", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.0.046", "111.08.0.042", "Từ Hữu Côi", "", "đang cập nhật", "", "", "", "Con ông Kế. Đang cập nhật.", "", ""),
                    ("111.09.0.047", "111.08.0.045", "Từ Ngọc Lương", "", "Bà Nguyễn Thị Huệ", "", "", "", "Con thứ nhất ông Thanh. Trung tướng, Phó Giáo sư, Tiến sỹ. Vợ là Bà Nguyễn Thị Huệ làm Công nhân Nhà máy Cộc Sợi, nghỉ hưu tại TP.HCM. Ông bà có công lao to lớn, đóng góp nhiều công sức và tài lực xây dựng dòng họ. Sinh hạ: Từ Ngọc Nhân, Từ Ngọc Vỵ.", "", ""),
                    ("111.09.0.048", "111.08.0.045", "Từ Ngọc Long", "", "Bà Nguyễn Thị Hoa", "", "", "", "Con thứ 2 ông Thanh. Sinh hạ: Từ Thị Mai, Từ Thị Huyền.", "", ""),
                    ("111.09.1.049", "111.08.0.045", "Từ Thị Lam", "", "Đang cập nhật", "", "", "", "Con ông Thanh. Đang cập nhật", "", ""),
                    ("111.09.1.050", "111.08.0.045", "Từ Thị Lê", "", "Đang cập nhật", "", "", "", "Con ông Thanh. Đang cập nhật", "", ""),
                    ("111.09.0.051", "111.08.0.045", "Từ Ngọc Lĩnh", "", "Bà Trần Thị Sâm", "", "", "", "Con trai thứ 3 ông Thanh. Sinh hạ: Từ Ngọc Ý [đang cập nhật].", "", ""),
                    ("111.09.1.052", "111.08.0.045", "Từ Thị Lộc", "", "Đang cập nhật", "", "", "", "Con ông Thanh. Đang cập nhật", "", ""),
                    ("111.09.1.053", "111.08.0.047", "Từ Thị Hiền", "", "Nguyễn Bảo", "", "", "", "Con ông Hiền. Lấy anh Nguyễn Bảo con ông Nguyễn Toàn trong làng", "", ""),
                    ("111.09.0.054", "111.08.0.047", "Từ Hữu Thảo", "", "", "", "", "", "Con ông Hiền.", "Chết sớm", ""),
                    ("111.09.0.055", "111.08.0.047", "Từ Hữu Cát", "", "Bà Nguyễn Thị Tứ", "", "", "", "Con ông Hiền. Sinh hạ: Từ Thị Mai, Từ Hữu Thuận, Từ Thị Hà, Từ Hữu Thoả.", "", ""),
                    ("111.09.0.056", "111.08.0.047", "Từ Hữu Nhung", "", "Bà Nguyễn Thị Tạo", "", "", "", "Con ông Hiền. Sinh hạ: Từ Hữu Hoàn, Từ Hữu Hải.", "", ""),
                    ("111.09.1.057", "111.08.0.047", "Từ Thị Sâm", "", "Nguyễn Tú", "", "", "", "Con ông Hiền. Lấy anh Nguyễn Tú (Chiên)", "", ""),
                    ("111.09.1.058", "111.08.0.047", "Từ Thị Liệu", "", "Trần Bình", "", "", "", "Con ông Hiền. Lấy anh Trần Bình con ông Trự", "", ""),
                    ("111.09.1.059", "111.08.0.047", "Từ Thị Đào", "", "Trần Đình Trọng", "", "", "", "Con ông Hiền. Lấy anh Trần Đình Trọng trong làng", "", ""),
                    ("111.09.0.060", "111.08.0.047", "Từ Ngọc Xuân", "", "đang cập nhật", "", "", "", "Con ông Hiền. Đang cập nhật.", "", ""),
                    ("111.09.0.061", "111.08.0.049", "Từ Hữu Bình", "", "Bà Trần Thị Sen", "", "", "", "Con ông Thường. Sinh hạ: Từ Hữu Linh, Từ Thị Tâm.", "", ""),
                    ("111.09.0.062", "111.08.0.049", "Từ Hữu Minh", "", "đang cập nhật", "", "", "", "Con ông Thường. Đang cập nhật.", "", ""),
                    ("111.09.1.063", "111.08.0.049", "Từ Thị Hòa", "", "đang cập nhật", "", "", "", "Con ông Thường. Đang cập nhật.", "", ""),
                    ("111.09.1.064", "111.08.0.051", "Từ Thị Thái", "", "đang cập nhật", "", "", "", "Con ông Tường. Đang cập nhật.", "", ""),
                    ("111.09.1.065", "111.08.0.051", "Từ Thị Hòa", "", "đang cập nhật", "", "", "", "Con ông Tường. Đang cập nhật.", "", ""),
                    ("111.09.0.066", "111.08.0.051", "Từ Hữu Hùng", "", "đang cập nhật", "", "", "", "Con ông Tường. Đang cập nhật.", "", ""),
                    ("111.09.1.067", "111.08.0.052", "Từ Thị Thủy", "", "đang cập nhật", "", "", "", "Con ông Âu. Đang cập nhật.", "", ""),
                    ("111.09.1.068", "111.08.0.052", "Từ Thị Lan", "", "đang cập nhật", "", "", "", "Con ông Âu. Đang cập nhật.", "", ""),
                    ("111.09.0.069", "111.08.0.052", "Từ Hữu Hoài", "", "đang cập nhật", "", "", "", "Con ông Âu. Đang cập nhật.", "", ""),
                    ("111.09.1.070", "111.08.0.052", "Từ Thị Hồng", "", "đang cập nhật", "", "", "", "Con ông Âu. Đang cập nhật.", "", ""),
                    ("111.09.0.071", "111.08.0.052", "Từ Hữu Quang", "", "đang cập nhật", "", "", "", "Con ông Âu. Đang cập nhật.", "", ""),
                    ("111.09.0.072", "111.08.0.052", "Từ Hữu Quý", "", "đang cập nhật", "", "", "", "Con ông Âu. Đang cập nhật.", "", ""),

                    # ------------------------------------
                    # CHI 2
                    # ------------------------------------
                    ("122.09.0.001", "122.08.0.067", "Từ Hữu Tuyến", "", "Bà Nguyễn Thị Lan", "", "", "", "Con đầu ông Tựu. Công nhân Lâm trường Hương Sơn. Sinh hạ: Từ Thị Hoà, Từ Hữu Thoả, Từ Hữu Thành, Từ Hữu Tuyền, Từ Thị Mỏ, Từ Thị Mậu.", "", ""),
                    ("122.09.0.002", "122.08.0.068", "Từ Hữu Cừ", "", "Bà Nguyễn Thị Cháu", "", "", "", "Con ông Nựu. Vợ là Bà Nguyễn Thị Cháu ở Thượng Xuân. Sinh hạ: 1. Từ Hữu Hùng, 2. Từ Thị Dũng, 3. Từ Hữu Kiên (chết sớm), 4. Từ Hữu Cường, 5. Từ Thị Phú (lấy chồng về Mỹ Lộc), 6. Từ Thị Hựu, 7. Từ Thị Hạnh, 8. Từ Hữu Phúc, 9. Từ Hữu Vừng.", "", ""),
                    ("122.09.0.003", "122.08.0.068", "Từ Thị Tỷ", "", "", "", "", "", "Con ông Nựu.", "Tảo một", ""),         
                    ("122.09.1.004", "122.08.0.072", "Từ Thị Chắt", "", "Không rõ", "", "", "", "Con ông Cảnh. Lấy chồng về Sơn Lộc", "", ""),
                    ("122.09.1.005", "122.08.0.072", "Từ Thị Xanh", "", "Trần Hạnh", "", "", "", "Con ông Cảnh. Lấy Trần Hạnh (Thành) trong làng", "", ""),
                    ("122.09.0.006", "122.08.0.072", "Từ Hữu Anh", "", "", "", "", "", "Con ông Cảnh.", "Tảo một", ""),
                    ("122.09.0.007", "122.08.0.072", "Từ Hữu Hồng", "", "", "", "", "", "Con ông Cảnh.", "Tảo một", ""),
                    ("122.09.1.008", "122.08.0.072", "Từ Thị Hường", "", "", "", "", "", "Con ông Cảnh.", "Tảo một", ""),
                    ("122.09.1.009", "122.08.0.072", "Từ Thị Hạnh", "", "Không rõ", "", "", "", "Con ông Cảnh. Đang cập nhật", "", ""),
                    ("122.09.1.010", "122.08.0.072", "Từ Thị Hiền", "", "Không rõ", "", "", "", "Con ông Cảnh. Đang cập nhật", "", ""),
                    ("122.09.0.011", "122.08.0.072", "Từ Hữu Hoàn", "", "đang cập nhật", "", "", "", "Con ông Cảnh. Đang cập nhật.", "", ""),
                    ("122.09.1.012", "122.08.0.072", "Từ Thị Hằng", "", "Không rõ", "", "", "", "Con ông Cảnh. Đang cập nhật", "", ""),
                    ("122.09.1.013", "122.08.0.075", "Từ Thị Liên", "", "đang cập nhật", "", "", "", "Con ông Tư. Đang cập nhật.", "", ""),
                    ("122.09.0.014", "122.08.0.075", "Từ Hữu Thành", "", "đang cập nhật", "", "", "", "Con ông Tư. Đang cập nhật.", "", ""),
                    ("122.09.0.015", "122.08.0.079", "Từ Hữu Trung", "", "Lê Thị Vân", "", "", "", "Con đầu ông Lương. Vợ là Lê Thị Vân Lê Thị Vân ở  xã Thạch Sơn, Thạch Hà. Sinh hạ: Từ Thị Bích Loan (lấy chồng về tỉnh Lâm Đồng), Từ Ngọc Luân, Từ Ngọc Lễ", "", ""),
                    ("122.09.0.016", "122.08.0.079", "Từ Hữu Thông", "", "Trần Thị Hạnh", "", "", "", "Con ông Lương. Vợ là Trần Thị Hạnh (Thành) ở giữa làng. Sinh hạ: Từ Hữu Huy, Từ Hữu Ngọc.", "", ""),
                    ("122.09.0.017", "122.08.0.079", "Từ Hữu Tiến", "", "Trần Thị Hà", "", "", "", "Con ông Lương. Vợ là Trần Thị Hà ở Đắc Lắc. Sinh hạ: Từ Hữu Thỏa, Từ Thị Ly, Từ Thị Linh", "", ""),
                    ("122.09.0.018", "122.08.0.079", "Từ Hữu Triển", "", "", "", "", "", "Con ông Lương", "Tảo một", ""),                    
                    ("122.09.0.019", "122.08.0.079", "Từ Hữu Trường", "", "Lữ Thị Kim Khuê", "", "", "", "Con ông Lương. Vợ là Lữ Thị Kim Khuê ở Đắc Lắc. Sinh hạ: Từ Ngọc Anh Thư, Từ Vĩnh Cường", "", ""),
                    ("122.09.1.020", "122.08.0.079", "Từ Thị T́ình", "", "", "", "", "", "Con ông Lương.", "Tảo một", ""),
                    ("122.09.0.021", "122.08.0.079", "Từ Hữu Thân", "", "Nguyễn Thị Kiều", "", "", "", "Con ông Lương. Vợ là Nguyễn Thị Kiều ở Đồng Nai.Sinh hạ: Từ Thị Ngọc Trân, Từ Thị Ngọc Châu", "", ""),                    
                    ("122.09.1.022", "122.08.0.082", "Từ Thị Hằng", "", "Nguyễn Hữu Tuấn", "", "", "", "Con ông Tương. Chồng là Nguyễn Hữu Tuấn con ông Nhuận ở Thượng Lộc.", "", ""),
                    ("122.09.0.023", "122.08.0.082", "Từ Hữu Đạt", "", "đang cập nhật", "", "", "", "Con ông Tương. Đang cập nhật.", "", ""), 
                    ("123.09.0.024", "123.08.0.084", "Từ Hữu Quyết", "", "đang cập nhật", "", "", "", "Con ông Số.", "", ""),
                    ("123.09.1.025", "123.08.0.084", "Từ Thị Tâm", "", "đang cập nhật", "", "", "", "Con ông Số.", "", ""),
                    ("123.09.0.026", "123.08.0.084", "Từ Hữu Thắng", "", "đang cập nhật", "", "", "", "Con ông Số.", "", ""),
                    ("123.09.0.027", "123.08.0.084", "Trần Từ Nông", "Đông", "đang cập nhật", "", "", "", "Con nuôi ông Số.", "Con nuôi", ""),                    
                    ("123.09.0.028", "123.08.0.085", "Từ Hữu Hải", "", "", "", "", "", "Con ông Yêm.", "Chết sớm", ""),
                    ("123.09.0.029", "123.08.0.085", "Từ Hữu Hoàn", "", "đang cập nhật", "", "", "", "Con ông Yêm. Đang cập nhật.", "", ""),
                    ("123.09.0.030", "123.08.0.085", "Từ Hữu Ngọc", "", "đang cập nhật", "", "", "", "Con ông Yêm. Đang cập nhật", "", ""),
                    ("123.09.1.031", "123.08.0.085", "Từ Thị Hằng", "", "đang cập nhật", "", "", "", "Con ông Yêm. Đang cập nhật", "", ""),
                    ("123.09.1.032", "123.08.0.086", "Từ Thị Hòa", "", "đang cập nhật", "", "", "", "Con ông Niềm. Đang cập nhật.", "", ""),
                    ("123.09.0.033", "123.08.0.086", "Từ Hữu Hùng", "", "đang cập nhật", "", "", "", "Con ông Niềm. Đang cập nhật.", "", ""),
                    ("123.09.1.034", "123.08.0.086", "Từ Thị Nguyệt", "", "đang cập nhật", "", "", "", "Con ông Niềm. Đang cập nhật.", "", ""),
                    ("123.09.1.035", "123.08.0.086", "Từ Thị Ngọc", "", "đang cập nhật", "", "", "", "Con ông Niềm. Đang cập nhật.", "", ""),
                    ("123.09.1.036", "123.08.0.086", "Từ Thị Trâm", "", "đang cập nhật", "", "", "", "Con ông Niềm. Đang cập nhật.", "", ""),
                    ("123.09.0.037", "123.08.0.088", "Từ Hữu Thuận", "", "đang cập nhật", "", "", "", "Con ông Xanh. Đang cập nhật.", "", ""),
                    ("123.09.0.038", "123.08.0.088", "Từ Hữu Lợi", "", "đang cập nhật", "", "", "", "Con ông Xanh. Đang cập nhật.", "", ""),
                    ("123.09.0.039", "123.08.0.088", "Từ Hữu Hải", "", "đang cập nhật", "", "", "", "Con ông Xanh. Đang cập nhật.", "", ""),
                    ("123.09.0.040", "123.08.0.088", "Từ Hữu Bằng", "", "đang cập nhật", "", "", "", "Con ông Xanh. Đang cập nhật.", "", ""),
                    ("123.09.0.041", "123.08.0.090", "Từ Hữu Dũng", "", "đang cập nhật", "", "", "", "Con ông Nuôi. Đang cập nhật.", "", ""),
                    ("123.09.0.042", "123.08.0.091", "Từ Hữu Phú", "", "đang cập nhật", "", "", "", "Con ông Em. Đang cập nhật.", "", ""),
                    ("123.09.0.043", "123.08.0.091", "Từ Hữu Khánh", "", "đang cập nhật", "", "", "", "Con ông Em. Đang cập nhật.", "", ""),
                    ("123.09.0.044", "123.08.0.091", "Từ Hữu Chương", "", "đang cập nhật", "", "", "", "Con ông Em. Đang cập nhật.", "", ""),
                    ("124.09.1.045", "124.08.0.096", "Từ Thị Hiền", "", "Hồ Ngọc Điểu", "", "", "", "Con ông Viện. Đang cập nhật.", "", ""),
                    ("124.09.0.046", "124.08.0.096", "Từ Minh Khoa", "", "Lê Thị Thảo Duyên", "", "", "", "Con ông Viện. Vợ là Lê Thị Thảo Duyên sống ở Đắc Lắc, quê gốc ở Quảng Nam.", "", ""),
                    ("124.09.1.047", "124.08.0.097", "Từ Ngọc Mơ ", "", "đang cập nhật", "", "", "", "Con ông Xá. Đang cập nhật.", "", ""),
                    ("124.09.1.048", "124.08.0.098", "Từ Thị Trang", "", "Trần Hoàng Sáng", "", "", "", "Con ông Khánh. Chồng là Trần Hoàng Sáng ở Đức Thọ.", "", ""),
                    ("124.09.1.049", "124.08.0.098", "Từ Thị Ngân", "", "Nguyễn Văn Hiệp", "", "", "", "Con ông Khánh. Chồng là Nguyễn Văn Hiệp ở Nghệ An.", "", ""),
                    ("124.09.1.050", "124.08.0.098", "Từ Thị Thắm", "", "", "", "", "", "Con ông Khánh. Mất lúc 5 tuổi.", "Chết sớm", ""),
                    ("124.09.0.051", "124.08.0.098", "Từ Quang Nam", "", "đang cập nhật", "", "", "", "Con ông Khánh. Đang cập nhật.", "", ""),
                    ("124.09.1.052", "124.08.0.099", "Từ Anh Thư", "", "đang cập nhật", "", "", "", "Con ông Thùy. Đang cập nhật.", "", ""),
                    ("124.09.1.053", "124.08.0.099", "Từ Anh Thơ", "", "đang cập nhật", "", "", "", "Con ông Thùy. Đang cập nhật.", "", ""),
                    ("124.09.0.054", "124.08.0.099", "Từ Minh Hiếu", "", "đang cập nhật", "", "", "", "Con ông Thùy. Đang cập nhật.", "", ""),
                    ("124.09.0.055", "124.08.0.100", "Từ Hải Thành", "", "Nguyễn Thị Thùy", "", "", "", "Con ông Phú. Vợ là Nguyễn Thị Thùy ở Lào Cai. Sinh hạ: Từ Nguyễn Gia Hân, Từ Mỹ Duyên, Từ Hải Đăng", "", ""),
                    ("124.09.1.056", "124.08.0.100", "Từ Thị Hương Xuân", "", "Lê Thành Phương", "", "", "", "Con ông Phú. Chồng là Lê Thành Phương ở Thị Trấn Hương Khê.", "", ""),
                    ("124.09.1.057", "124.08.0.100", "Từ Thị Minh Trang", "", "Lưu Doãn Ánh", "", "", "", "Con ông Phú. Chồng là Lưu Doãn Ánh ở Nam Trực - Nam Định.", "", ""),
                    ("124.09.1.058", "124.08.0.103", "Từ Thị Phương", "", "Nguyễn Anh Sơn", "", "", "", "Con ông Huy. Chồng là Nguyễn Anh Sơn ở Quang Lộc.", "", ""),
                    ("124.09.0.059", "124.08.0.103", "Từ Hữu Hoàng", "", "Trần Thị Loan", "", "", "", "Con ông Huy. Vợ là Trần Thị Loan con Ông Phúc ở giữa làng. Sinh hạ: Từ Ngọc Huyền", "", ""),
                    ("124.09.0.060", "124.08.0.103", "Từ Quang Hiệp", "", "đang cập nhật", "", "", "", "Con ông Huy. Đang cập nhật.", "", ""),
                    ("124.09.0.061", "124.08.0.105", "Từ Nhật Lương", "", "đang cập nhật", "", "", "", "Con ông Quý. Đang cập nhật.", "", ""),
                    ("124.09.0.062", "124.08.0.105", "Từ Nam Thắng", "", "đang cập nhật", "", "", "", "Con ông Quý. Đang cập nhật.", "", ""),
                    ("124.09.1.063", "124.08.0.106", "Từ Thị Hiền", "", "đang cập nhật", "", "", "", "Con ông Khang. Đang cập nhật.", "", ""),
                    ("124.09.1.064", "124.08.0.106", "Từ Thị Hòa", "", "đang cập nhật", "", "", "", "Con ông Khang. Đang cập nhật.", "", ""),
                    ("124.09.0.065", "124.08.0.108", "Từ Hữu Sâm", "", "Nguyễn Thị Hồng", "", "", "", "Con ông Bình. Vợ là Nguyễn Thị Hồng ở giữa làng.", "", ""),
                    ("124.09.1.066", "124.08.0.108", "Từ Thị Phượng", "", "Trần Văn Cường", "", "", "", "Con ông Bình. Chồng là Trần Văn Cường ở Cửa Lò.", "", ""),
                    ("124.09.0.067", "124.08.0.108", "Từ Hữu Bảo", "", "đang cập nhật", "", "", "", "Con ông Bình. Đang cập nhật.", "", ""),
                    ("124.09.0.068", "124.08.0.110", "Từ Hữu Đức", "", "đang cập nhật", "", "", "", "Con ông Cường. Đang cập nhật.", "", ""),
                    ("124.09.0.069", "124.08.0.112", "Từ Hữu Duy", "", "đang cập nhật", "", "", "", "Con ông Mạnh. Đang cập nhật.", "", ""),                    
  
                    # ------------------------------------
                    # CHI 3
                    # ------------------------------------
                    ("135.09.0.001", "135.08.0.114", "Từ Hữu Hoà", "", "Bà Thái Thị Hãn", "", "", "", "Con ông Từ Hữu Thự. Vợ là Bà Thái Thị Hãn người ở Kỳ Anh. Sinh hạ: Từ Hữu Dũng, Từ Hữu Trung.", "", ""), 
                    ("135.09.0.002", "135.08.0.114", "Từ Hữu Bình", "", "Bà Võ Thị Tứ", "", "", "", "Con ông Từ Hữu Thự. Vợ là Bà Võ Thị Tứ người ở Song Lộc. Sinh hạ: Từ Thị Anh, Từ Thị Mỹ, Từ Hữu Việt, Từ Hữu Đức.", "", ""),
                    ("135.09.0.003", "135.08.0.114", "Từ Hữu Hạnh", "", "Bà Nguyễn Thị Mai", "", "", "", "Con ông Từ Hữu Thự. Vợ là Bà Nguyễn Thị Mai người ở Nam Định. Sinh hạ: Từ Thị Hà, Từ Hữu Phúc.", "", ""),
                    ("135.09.1.004", "135.08.0.114", "Từ Thị Bính", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thự. Lấy chồng Quang Lộc", "", ""),
                    ("135.09.1.005", "135.08.0.114", "Từ Thị Tý", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thự. Lấy chồng Tùng Lộc", "", ""),
                    ("135.09.1.006", "135.08.0.114", "Từ Thị Vân", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thự. Lấy chồng Diễn Châu, Nghệ An", "", ""),
                    ("135.09.1.007", "135.08.0.119", "Từ Thị Hoa", "", "Không rõ", "", "", "", "Con ông Từ Hữu Trì. Đang cập nhật.", "", ""),
                    ("135.09.1.008", "135.08.0.119", "Từ Thị Lan", "", "Không rõ", "", "", "", "Con ông Từ Hữu Trì. Đang cập nhật.", "", ""),
                    ("135.09.1.009", "135.08.0.119", "Từ Thị Bình", "", "Không rõ", "", "", "", "Con ông Từ Hữu Trì. Con bà hai. Đang cập nhật.", "", ""),
                    ("135.09.0.010", "135.08.0.120", "Từ Hữu Tân", "", "Bà Nguyễn Thị Canh", "", "", "", "Con ông Từ Hữu Thái. Sinh hạ: Từ Thị Nhung, Từ Hữu Tài, Từ Hữu Chiến.", "", ""),
                    ("135.09.0.011", "135.08.0.120", "Từ Hữu Thân", "", "Bà Trần Thị Thành", "", "", "", "Con ông Từ Hữu Thái. Sinh hạ: Từ Hữu Trung, Từ Hữu Thông.", "", ""),
                    ("135.09.1.012", "135.08.0.120", "Từ Thị Ái", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thái. Đang cập nhật.", "", ""),
                    ("135.09.0.013", "135.08.0.120", "Từ Hữu Hùng", "", "Bà Thái Thị Dung", "", "", "", "Con ông Từ Hữu Thái. Sinh hạ: Từ Hữu Quốc, Từ Hữu Khánh.", "", ""),
                    ("135.09.1.014", "135.08.0.120", "Từ Thị Dũng", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thái. Đang cập nhật.", "", ""),
                    ("135.09.0.015", "135.08.0.120", "Từ Hữu Hoà", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Thái. Đang cập nhật.", "", ""),
                    ("135.09.0.016", "135.08.0.126", "Từ Hoàng Hải", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Nam. Đang cập nhật.", "", ""),
                    ("135.09.1.017", "135.08.0.126", "Từ Mai Ly", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Nam. Đang cập nhật.", "", ""),
                    ("135.09.1.018", "135.08.0.126", "Từ Mai Linh", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Nam. Con bà hai. Đang cập nhật.", "", ""),
                    ("135.09.0.019", "135.08.0.132", "Từ Thanh Huyền", "", "đang cập nhật", "1993", "", "", "Con ông Từ Hữu Hoà. Đang cập nhật.", "", ""),
                    ("135.09.0.020", "135.08.0.132", "Từ Tiến Dũng", "", "đang cập nhật", "1999", "", "", "Con ông Từ Hữu Hoà. Đang cập nhật.", "", ""),
                    ("135.09.1.021", "135.08.0.134", "Từ Phương Thảo", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Huấn. Đang cập nhật.", "", ""),
                    ("135.09.1.022", "135.08.0.134", "Từ Phương Hiếu", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Huấn. Đang cập nhật.", "", ""),
                    ("135.09.1.023", "135.08.0.134", "Từ Nguyên Anh", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Huấn. Đang cập nhật.", "", ""),
                    ("135.09.0.024", "135.08.0.139", "Từ Hữu Phương", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Sang. Đang cập nhật.", "", ""),
                    ("135.09.0.025", "135.08.0.140", "Từ Hải Đăng", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Trọng. Đang cập nhật.", "", ""),

                    # ------------------------------------
                    # CHI 4
                    # ------------------------------------
                    ("246.09.1.001", "246.08.0.143", "Từ Thị Xuân", "", "Không rõ", "", "", "", "Con ông Từ Hữu Cương. Lấy chồng về Dư Nại.", "", ""),
                    ("246.09.0.002", "246.08.0.143", "Từ Hữu Hạ", "", "Bà Trần Thị Mai", "", "", "", "Con ông Từ Hữu Cương. Sinh hạ: Từ Hữu Thông, Từ Hữu Minh.", "", ""),
                    ("246.09.1.003", "246.08.0.143", "Từ Thị Thu", "", "Trần Cần", "", "", "", "Con ông Từ Hữu Cương. Lấy anh Trần Cần trong xã", "", ""),
                    ("246.09.0.004", "246.08.0.143", "Từ Hữu Đông", "", "Bà Trần Thị Phú", "", "", "", "Con ông Từ Hữu Cương. Sinh hạ: Từ Thị Hà, Từ Hữu Hưng.", "", ""),                       
                    ("246.09.1.005", "246.08.0.147", "Từ Thị Dược", "", "Không rõ", "", "", "", "Con ông Từ Hữu Tượng. Đang cập nhật", "", ""),
                    ("246.09.1.006", "246.08.0.147", "Từ Thị Tâm", "", "Không rõ", "", "", "", "Con ông Từ Hữu Tượng. Lấy chồng về Yên Đồng", "", ""),
                    ("246.09.0.007", "246.08.0.147", "Từ Hữu Tam", "", "", "", "", "", "Con ông Từ Hữu Tượng. Liệt sĩ", "Không có con", ""),
                    ("246.09.1.008", "246.08.0.147", "Từ Thị Tứ", "", "Không rõ", "", "", "", "Con ông Từ Hữu Tượng. Đang cập nhật", "", ""),
                    ("246.09.0.009", "246.08.0.147", "Từ Hữu Nam", "", "Bà Trần Thị Vinh", "", "", "", "Con ông Từ Hữu Tượng. Sinh hạ: Từ Thị Nga, Từ Hữu Vũ.", "", ""),
                    ("246.09.0.010", "246.08.0.147", "Từ Hữu Lục", "", "Bà Trần Thị Hiền", "", "", "", "Con ông Từ Hữu Tượng. Vợ là Bà Trần Thị Hiền con ông Năm giữa làng. Sinh hạ: Từ Thị Thắm, Từ Thị Thuỳ.", "", ""),
                    ("246.09.0.011", "246.08.0.147", "Từ Hữu Thị", "", "", "", "", "", "Con ông Từ Hữu Tượng", "Chết sớm", ""),
                    ("246.09.0.012", "246.08.0.147", "Từ Hữu Thành", "", "Bà Lê Thị Nhị", "", "", "", "Con ông Từ Hữu Tượng. Vợ là Bà Lê Thị Nhị ở Quảng Bình. Sinh hạ: Từ Hữu Bình, Từ Hữu Ngọc, Từ Hữu Tuấn.", "", ""),
                    ("246.09.0.013", "246.08.0.147", "Từ Hữu Lập", "", "", "", "", "", "Con ông Từ Hữu Tượng. Tử sỹ", "Chết sớm", ""),
                    ("246.09.1.014", "246.08.0.147", "Từ Thị Minh", "", "Không rõ", "", "", "", "Con ông Từ Hữu Tượng. Đang cập nhật", "", ""),
                    ("246.09.0.015", "246.08.0.149", "Từ Mạnh Mậu", "", "Bà Nguyễn Thị Lai", "", "", "", "Con ông Từ Hữu Chất. Kỹ sư, cán bộ nhà nước. Vợ là Bà Nguyễn Thị Lai người ở Trường Lộc. Sinh hạ: Từ Mạnh Hùng, Từ Thị Việt Hà.", "", ""),
                    ("246.09.1.016", "246.08.0.149", "Từ Thị Kiểu", "", "Thân Văn Yên", "", "", "", "Con ông Từ Hữu Chất. Lấy chồng về Sơn Lộc", "", ""),
                    ("246.09.1.017", "246.08.0.149", "Từ Thị Thu", "", "Trần Choan", "", "", "", "Con ông Từ Hữu Chất. Lấy Trần Choan trong làng", "", ""),
                    ("246.09.0.018", "246.08.0.149", "Từ Quốc Lệ", "", "Bà Trần Thị Hằng", "", "", "", "Con ông Từ Hữu Chất. Đại tá Quân đội. Sinh hạ: Từ Huy Trung, Từ Thị Huyền Nga, Từ Quốc Việt.", "", ""),
                    ("246.09.0.019", "246.08.0.149", "Từ Quốc Đạt", "", "Bà Trần Thị Xuân", "", "", "", "Con ông Từ Hữu Chất. Sinh hạ: Từ Thị Sâm, Từ Hữu Nhung.", "", ""),

                    ("246.09.1.020", "246.08.0.154", "Từ Thị Hạnh", "", "Thân Viết Tiến", "", "", "", "Con ông Từ Hữu Bạng. Lấy chồng về Quang Lộc", "", ""),

                    ("246.09.0.021", "246.08.0.154", "Từ Hữu Phúc", "", "Bà Trần Thị Nuôi", "", "", "", "Con ông Từ Hữu Bạng. Sinh hạ: Từ Thị Đức, Từ Hữu Lành, Từ Thị Hiền, Từ Thị Thảo, Từ Hữu Quang.", "", ""),
                    ("246.09.0.022", "246.08.0.155", "Từ Hữu Lý", "", "Bà Lê Thị Truyền", "", "", "", "Con ông Từ Hữu Hộ. Sinh hạ: Từ Hữu Pháp, Từ Hữu Luân, Từ Thị Hồng Quyên.", "", ""),
                    ("246.09.1.023", "246.08.0.155", "Từ Thị Tình", "", "", "", "", "", "Con ông Từ Hữu Hộ.", "Chết sớm", ""),
                    ("246.09.1.024", "246.08.0.155", "Từ Thị Công", "", "Không lấy chồng", "", "", "", "Con ông Từ Hữu Hộ. Không lấy chồng", "", ""),
                    ("246.09.1.025", "246.08.0.155", "Từ Thị Ty", "", "Không lấy chồng", "", "", "", "Con ông Từ Hữu Hộ. Không lấy chồng", "", ""),
                    ("246.09.0.026", "246.08.0.155", "Từ Hữu Sơn", "", "Bà Trần Thị Thuỷ", "", "", "", "Con ông Từ Hữu Hộ. Vợ là Bà Trần Thị Thuỷ, Con ông Bốn giữa làng. Sinh hạ: Từ Nam Long, Từ Quốc Vương.", "", ""),
                    ("246.09.0.027", "246.08.0.155", "Từ Hữu Lam", "", "Nguyễn Thị Hà", "", "", "", "Con ông Từ Hữu Hộ. Sinh hạ: Từ Hữu Việt.", "", ""),                 
                    ("246.09.1.028", "246.08.0.156", "Từ Thị Mỹ", "", "Nguyễn Tiến Phẳng", "", "", "", "Con ông Từ Hữu Khánh, Con Bà Xuân. Làm cán bộ ở Gia Lai", "", ""),
                    ("246.09.1.029", "246.08.0.156", "Từ Thị Hòa", "", "Đặng Lệ", "", "", "", "Con ông Từ Hữu Khánh. Lấy chồng về Quang Lộc", "", ""),
                    ("246.09.1.030", "246.08.0.156", "Từ Thị Tâm", "", "Không rõ", "", "", "", "Con ông Từ Hữu Khánh. Làm giáo viên ở Gia Lai", "", ""),
                    ("246.09.0.031", "246.08.0.156", "Từ Hữu Cát", "", "", "", "", "", "Con ông Từ Hữu Khánh", "Chết sớm", ""),
                    ("246.09.1.032", "246.08.0.156", "Từ Thị Sâm", "", "Không rõ", "", "", "", "Con ông Từ Hữu Khánh, con Bà Liên. Đang cập nhật", "", ""),
                    ("246.09.0.033", "246.08.0.156", "Từ Hữu Thắng", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Khánh. Đang cập nhật.", "", ""),
                    ("246.09.1.034", "246.08.0.156", "Từ Thị Lộc", "", "Không rõ", "", "", "", "Con ông Từ Hữu Khánh. Đang cập nhật", "", ""),
                    ("246.09.0.035", "246.08.0.156", "Từ Hữu Lợi", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Khánh. Đang cập nhật.", "", ""),
                    ("246.09.0.036", "246.08.0.156", "Từ Hữu Bảo", "", "", "", "", "", "Con ông Từ Hữu Khánh", "Chết sớm", ""),
                    ("246.09.0.037", "246.08.0.156", "Từ Hữu Quyền", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Khánh. Đang cập nhật.", "", ""),

                    # ------------------------------------
                    # CHI 5
                    # ------------------------------------
                    ("258.09.1.001", "258.08.0.158", "Từ Thị Cháu", "", "Không rõ", "", "", "", "Con ông Từ Hữu Điểu. Lấy hồng người Quang Lộc", "", ""),
                    ("258.09.0.002", "258.08.0.158", "Từ Hữu Loan", "", "Bà Đặng Thị Thức", "", "", "", "Con ông Từ Hữu Điểu (Trung). Vợ là Bà Đặng Thị Thức người ở Quang Lộc. Sinh hạ: Từ Hữu Sơn, Từ Thị Hà, Từ Hữu Hải, Từ Hữu Hùng, Từ Hữu Tuấn.", "", ""),
                    ("258.09.0.003", "258.08.0.158", "Từ Hữu Ba", "", "Bà Trần Thị Xuân", "", "", "", "Con ông Từ Hữu Điểu. Cán bộ Nhà nước. Sinh hạ: Từ Hữu Long, Từ Thu Mai.", "", ""),
                    ("258.09.1.004", "258.08.0.158", "Từ Thị Tỷ", "", "Trần Thành", "", "", "", "Con ông Từ Hữu Điểu. Lấy anh Trần Thành (Phu) trong làng", "", ""),
                    ("258.09.1.005", "258.08.0.158", "Từ Thị Xuân", "", "Không rõ", "", "", "", "Con ông Từ Hữu Điểu. Lấy chồng về Nghi Xuân", "", ""),
                    ("258.09.0.006", "258.08.0.159", "Từ Hữu Phán", "", "Bà Phan Thị Lộc", "", "", "", "Con ông Từ Hữu Tiếu (Phán). Ông là Chánh án Tòa án huyện Can Lộc. Sinh hạ: Từ Thị Nga (lấy chồng về Trường Lộc), Từ Thị Ngân, Từ Hữu Anh (chết sớm), Từ Hữu Hùng.", "", ""),
                    ("258.09.0.007", "258.08.0.159", "Từ Hữu Đán", "", "Bà Trần Thị Thảo", "", "", "", "Con ông Từ Hữu Tiếu", "Chết sớm", ""),
                    ("258.09.1.008", "258.08.0.159", "Từ Thị Hòa", "", "Không rõ", "", "", "", "Con ông Từ Hữu Tiếu. Lấy chồng về Thuận Lộc", "", ""),
                    ("258.09.1.009", "258.08.0.159", "Từ Thị Chất", "", "Không rõ", "", "", "", "Con ông Từ Hữu Tiếu. Lấy chồng về Thạch Đài, Thạch Hà", "", ""),
                    ("258.09.0.010", "258.08.0.159", "Từ Hữu Tường", "", "Bà Trần Thị Thảo", "", "", "", "Con ông Từ Hữu Tiếu. Liệt sỹ", "Chưa có con", ""),
                    ("258.09.0.011", "258.08.0.159", "Từ Hữu Lục", "", "Bà Trần Thị Thảo", "", "", "", "Con ông Từ Hữu Tiếu. Sinh hạ: Từ Thị Nhung, Từ Thị Thuỷ, Từ Thị Lâm.", "", ""),
                    ("258.09.0.012", "258.08.0.159", "Từ Hữu Lương", "", "Bà Trần Thị Tài", "", "", "", "Con ông Từ Hữu Tiếu. Sinh hạ: Từ Thị Hiền, Từ Thị Hữu, Từ Hữu Đạt, Từ Hữu Phương.", "", ""),
                    ("258.09.0.013", "258.08.0.168", "Từ Hữu Đàn", "", "Bà Trần Thị Liên", "", "", "", "Con ông Từ Hữu Đề. Sinh hạ: Từ Hữu Minh, Từ Thị Anh.", "", ""),
                    ("258.09.0.014", "258.08.0.168", "Từ Hữu Liêm", "", "Bà Lê Thị Hồng", "", "", "", "Con ông Từ Hữu Đề. Sinh hạ: Từ Thị Tâm, Từ Thị Như.", "", ""),
                    ("258.09.0.015", "258.08.0.168", "Từ Hữu Thanh", "", "Bà Phan Thị Quế", "", "", "", "Con ông Từ Hữu Đề. Sinh hạ: Từ Hữu Quỳnh, Từ Thị Oanh.", "", ""),
                    ("258.09.1.016", "258.08.0.170", "Từ Thị Thìn", "", "Không rõ", "", "", "", "Con ông Từ Hữu Túc. Lấy chồng về Trung Lộc", "", ""),
                    ("258.09.1.017", "258.08.0.170", "Từ Thị Kiêm", "", "Trần Đạt", "", "", "", "Con ông Từ Hữu Túc. Lấy ông Trần Đạt trong làng", "", ""),
                    ("258.09.1.018", "258.08.0.170", "Từ Thị Yêm", "", "", "", "", "", "Con ông Từ Hữu Túc", "Tảo một", ""),
                    ("258.09.1.019", "258.08.0.170", "Từ Thị Chế", "", "", "", "", "", "Con ông Từ Hữu Túc", "Tảo một", ""),
                    ("258.09.0.020", "258.08.0.170", "Từ Hữu Tuý", "", "Bà Trần Thị Hương", "", "", "", "Con ông Từ Hữu Túc (Thân). Vợ là Bà Trần Thị Hương người Hương Sơn. Sinh hạ: Từ Ngọc Anh, Từ Ngọc Dũng, Từ Ngọc Cường, Từ Ngọc Quyền, Từ Thị Hoa.", "", ""),
                    ("258.09.1.021", "258.08.0.170", "Từ Thị Tuyết", "", "Trần Tùng", "", "", "", "Con ông Từ Hữu Túc. Lấy ông Trần Tùng trong làng", "", ""),
                    ("258.09.1.022", "258.08.0.170", "Từ Thị Bình", "", "Không rõ", "", "", "", "Con ông Từ Hữu Túc. Lấy chồng về Nghi Xuân ", "", ""),
                    ("258.09.1.023", "258.08.0.172", "Từ Thị Bính", "", "Không rõ", "", "", "", "Con ông Từ Hữu Vân. Lấy chồng về Quang lộc", "", ""),
                    ("258.09.1.024", "258.08.0.172", "Từ Thị Tam", "", "Trần Ngoạt", "", "", "", "Con ông Từ Hữu Vân. Lấy Trần Ngoạt trong làng ", "", ""),
                    ("258.09.1.025", "258.08.0.172", "Từ Thị Lục", "", "Không rõ", "", "", "", "Con ông Từ Hữu Vân. Lấy chồng về Hương Sơn", "", ""),
                    ("258.09.1.026", "258.08.0.172", "Từ Thị Liên", "", "Không lấy chồng", "", "", "", "Con ông Từ Hữu Vân. Ở Đắc Lắc", "", ""),
                    ("258.09.1.027", "258.08.0.172", "Từ Thị Xuân", "", "Không rõ", "", "", "", "Con ông Từ Hữu Vân. Lấy chồng về Thạch Hà", "", ""),
                    ("258.09.0.028", "258.08.0.172", "Từ Hữu Hậu", "", "Bà Hoàng Thị Chung", "", "", "", "Con ông Từ Hữu Vân. Vợ là Bà Hoàng Thị Chung người ở Sơn Lộc. Sinh hạ: Từ Hữu Thành, Từ Thị Thanh, Từ Thị Thắm, Từ Hữu Thiết.", "", ""),
                    ("258.09.0.029", "258.08.0.173", "Từ Hợp", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.030", "258.08.0.173", "Từ Hòa", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.031", "258.08.0.173", "Từ Hoa", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.032", "258.08.0.173", "Từ Lý", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.033", "258.08.0.173", "Từ Long", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.034", "258.08.0.173", "Từ Thành", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.035", "258.08.0.173", "Từ Bình", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Đằng. Đang cập nhật.", "", ""),
                    ("258.09.0.036", "258.08.0.175", "Từ Hữu Thanh", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Nhuệ. Đang cập nhật.", "", ""),
                    ("258.09.0.037", "258.08.0.175", "Từ Hữu Bình", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Nhuệ. Đang cập nhật.", "", ""),
                    ("258.09.0.038", "258.08.0.176", "Từ Hữu Lý", "", "Bà Đào Thị Lan", "", "", "", "Con ông Từ Hữu Sàn. Vợ là Bà Đào Thị Lan người ở Đức Thọ. Sinh hạ: Từ Thị Liễu, Từ Thị Lâm, Từ Hữu Luân, Từ Hữu Luật.", "", ""),
                    ("258.09.0.039", "258.08.0.176", "Từ Hữu Hộ", "", "", "", "", "", "Con ông Từ Hữu Sàn. Liệt sỹ", "Không có con", ""),                
                    ("258.09.0.040", "258.08.0.176", "Từ Hữu Minh", "", "Bà Nguyễn Thị Nựu", "", "", "", "Con ông Từ Hữu Sàn. Sinh hạ: Từ Thị Bình, Từ Hữu Thanh, Từ Thị Xanh, Từ Hữu Tuấn.", "", ""),
                    ("258.09.1.041", "258.08.0.178", "Từ Thị Xuân", "", "", "", "", "", "Con ông Từ Hữu Hiệt", "Tảo một", ""),
                    ("258.09.1.042", "258.08.0.178", "Từ Thị Đào", "", "Không rõ", "", "", "", "Con ông Từ Hữu Hiệt. Lấy chồng về Thạch Đỉnh", "", ""),
                    ("258.09.1.043", "258.08.0.178", "Từ Thị Huệ", "", "Không rõ", "", "", "", "Con ông Từ Hữu Hiệt. Lấy chồng về Thạch Tượng", "", ""),
                    ("258.09.1.044", "258.08.0.178", "Từ Thị Lan", "", "Không rõ", "", "", "", "Con ông Từ Hữu Hiệt. Lấy chồng về Đức Lâm, Đức Thọ", "", ""),
                    ("258.09.0.045", "258.08.0.178", "Từ Hữu Toàn", "", "Bà Trần Thị Vân", "", "", "", "Con ông Từ Hữu Hiệt. Vợ là Bà Trần Thị Vân người ở Đại Lộc. Sinh hạ: Từ Hữu Nam, Từ Hữu Đông.", "", ""),
                    ("258.09.0.046", "258.08.0.178", "Từ Hữu Tiến", "", "Bà Trần Thị Hoa", "", "", "", "Con ông Từ Hữu Hiệt. Sinh hạ: Từ Thị Hằng, Từ Hữu Tuấn, Từ Hữu Hải.", "", ""),
                    ("258.09.0.047", "258.08.0.178", "Từ Hữu Dũng", "", "Bà Trần Thị Hạnh", "", "", "", "Con ông Từ Hữu Hiệt. Sinh hạ: Từ Thị Nga, Từ Hữu Anh, Từ Hữu Sơn.", "", ""),
                    ("258.09.1.048", "258.08.0.180", "Từ Thị Nhu", "", "ông Minh", "", "", "", "Con ông Từ Hữu Sàng (Nhu). Lấy chồng về Đại Lộc ", "", ""),
                    ("258.09.0.049", "258.08.0.180", "Từ Hữu Giáp", "", "Bà Trần Thị Luận", "", "", "", "Con ông Từ Hữu Sàng (Nhu). Sinh hạ: Từ Hữu Quý, Từ Thị Huyền, Từ Hữu Quyền, Từ Hữu Lợi.", "", ""),
                    ("258.09.1.050", "258.08.0.180", "Từ Thị Huệ", "", "Ông Bình", "", "", "", "Con ông Từ Hữu Sàng (Nhu). Lấy chồng về Trung Lộc", "", ""),
                    ("258.09.0.051", "258.08.0.180", "Từ Hữu Huề", "", "Bà Trần Thị Nga", "", "", "", "Con ông Từ Hữu Sàng (Nhu). Sinh hạ: Từ Thị Hạnh, Từ Thị Linh, Từ Hữu Khoa.", "", ""),
                    ("258.09.0.052", "258.08.0.181", "Từ Hữu Triển", "", "", "", "", "", "Con ông Từ Hữu Trà. Liệt sỹ", "Chưa có con", ""),                     
                    ("258.09.0.053", "258.08.0.181", "Từ Hữu Đại", "", "Bà Trần Thị Hương", "", "", "", "Con ông Từ Hữu Trà. Sinh hạ: Từ Hữu Thắng, Từ Hữu Đông, Từ Hữu Trường, Từ Thị Hà, Từ Hữu Đồng.", "", ""),
                    ("258.09.1.054", "258.08.0.181", "Từ Thị Thanh", "", "Trần Hùng", "", "", "", "Con ông Từ Hữu Trà. Lấy Trần Hùng (Xương) trong làng", "", ""),     
                    ("258.09.0.055", "258.08.0.186", "Từ Hữu Nậy", "", "Không lấy vợ", "", "", "", "Con ông Từ Hữu Tưu (Khoái). Mất lúc 47 Tuổi", "Không có con", ""),
                    ("258.09.0.056", "258.08.0.186", "Từ Hữu Em", "Hoài", "Bà Trần Thị Đợt", "", "", "", "Con ông Từ Hữu Tưu. Vợ là Bà Trần Thị Đợt người ở Thanh Hoá. Sinh hạ: Từ Hữu Sơn, Từ Thị Thuỷ, Từ Hữu Hùng.", "", ""),
                    ("258.09.1.057", "258.08.0.186", "Từ Thị Tỷ", "", "", "", "", "", "Con ông Từ Hữu Tưu. Lấy Trần Tịnh trong làng", "", ""),
                    ("258.09.1.058", "258.08.0.186", "Từ Thị Tứ", "", "", "", "", "", "Con ông Từ Hữu Tưu. Lấy chồng về Thanh Hoá", "", ""),
                    ("258.09.0.059", "258.08.0.186", "Từ Hữu Năm", "", "", "", "", "", "Con ông Từ Hữu Tưu", "Chết sớm", ""),
                    ("258.09.1.060", "258.08.0.186", "Từ Thị Sáu", "", "Trần Tam", "", "", "", "Con ông Từ Hữu Tưu. Lấy Trần Tam (Cứ) trong làng ", "", ""),
                    ("258.09.0.061", "258.08.0.186", "Từ Hữu Chất", "", "Bà cả: Trần Thị Vân, bà thứ: Trần Thị Huê", "", "", "", "Con ông Từ Hữu Tưu (Khoái). Sinh hạ: Từ Hữu Phú, Từ Hữu Dũng, Từ Thị Anh, Từ Hữu Văn.", "", ""),
                    ("258.09.0.062", "258.08.0.186", "Từ Hữu Tạo", "", "Bà Trần Thị Lợi", "", "", "", "Con ông Từ Hữu Tưu (Khoái). Sinh hạ: Từ Thị Xuân, Từ Hữu Hạnh, Từ Thị Hà.", "", ""),
                    ("258.09.0.063", "258.08.0.186", "Từ Hữu Bình", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Tưu (Khoái). Đang cập nhật.", "", ""),
                    ("258.09.0.064", "258.08.0.186", "Từ Hữu Chín", "", "đang cập nhật", "", "", "", "Con ông Từ Hữu Tưu (Khoái). Đang cập nhật.", "", ""),


                    # ==========================================================
                    # ĐỜI 10 
                    # ==========================================================

                    # ------------------------------------
                    # CHI 1
                    # ------------------------------------
                    ("111.10.0.001", "111.09.0.001", "Từ Hữu Đắc", "", "Bà Nguyễn Thị Luân", "", "", "", "Con ông Vện. Vợ là Bà Nguyễn Thị Luân. Sinh hạ: Từ Hữu Thuận, Từ Thị Tình, Từ Thị Bình, Từ Thị Luận, Từ Hữu Hòa.", "", ""),
                    ("111.10.0.002", "111.09.0.001", "Từ Hữu Bật", "", "Bà Đặng Thị Đào", "", "", "", "Con ông Vện (Hà). Vợ là Bà Đặng Thị Đào người Hương Khê. Sinh hạ: Từ Hữu Nhâm, Từ Hữu Tý.", "", ""),
                    ("111.10.0.003", "111.09.0.001", "Từ Hữu Phú", "", "Bà Trần Thị Nho", "", "", "", "Con ông Vện (Hà). Vợ là Bà Trần Thị Nho. Sinh hạ: Từ Thị Long, Từ Thị Thuỷ, Từ Thị Vân, Từ Hữu Quốc, Từ Hữu Kỳ.", "", ""),
                    ("111.10.0.004", "111.09.0.001", "Từ Hữu Tư", "", "", "", "", "", "Con ông Vện (Hà) .", "Chết sớm", ""),
                    ("111.10.0.005", "111.09.0.001", "Từ Hữu Ngụ", "", "Bà Trần Thị Hồng", "", "", "", "Con ông Vện (Hà). Vợ là Bà Trần Thị Hồng. Sinh hạ: Từ Thị Quảng, Từ Thị Quyền, Từ Hữu Quý, Từ Hữu Báu.", "", ""),
                    ("111.10.1.006", "111.09.0.001", "Từ Thị Xuân", "", "Không rõ", "", "", "", "Con ông Vện (Hà). Chồng người Thạch Sơn, Thạch Hà.", "", ""),
                    ("111.10.0.007", "111.09.0.002", "Từ Hữu Tân", "Hải", "Bà Trần Thị An", "", "", "", "Con ông Từ Hữu Cháu. Vợ là Bà Trần Thị An. Sinh hạ: Từ Thị Hải, Từ Thị Dương, Từ Thị Liễu, Từ Thị Lan, Từ Thị Hạnh, Từ Thị Cúc.", "", ""),
                    ("111.10.1.008", "111.09.0.003", "Từ Thị Hoà", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thụ (Dụng). Lấy chồng trong làng.", "", ""),
                    ("111.10.1.009", "111.09.0.003", "Từ Thị Dũng", "", "Ông Trần Đại", "", "", "", "Con ông Từ Hữu Thụ (Dụng). Lấy ông Trần Đại trong làng.", "", ""),
                    ("111.10.1.010", "111.09.0.003", "Từ Thị Bình", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thụ (Dụng).", "", ""),
                    ("111.10.0.011", "111.09.0.003", "Từ Hữu Đính", "", "Bà Trần Thị Hằng", "", "", "", "Con ông Từ Hữu Thụ (Dụng). Vợ là Bà Trần Thị Hằng. Sinh hạ: Từ Hữu Ý.", "", ""),
                    ("111.10.1.012", "111.09.0.003", "Từ Thị Minh", "", "Không rõ", "", "", "", "Con ông Từ Hữu Thụ (Dụng).", "", ""),
                    ("111.10.0.013", "111.09.0.003", "Từ Hữu Bính", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thụ (Dụng). Đang cập nhật.", "", ""),
                    
                    ("111.10.1.014", "111.09.0.004", "Từ Thị Hương", "", "Không rõ", "", "", "", "Con ông Từ Hữu Phù (Tửu). Lấy chồng về Xóm Mới.", "", ""),
                    ("111.10.0.015", "111.09.0.004", "Từ Quang Đạt", "", "Bà Trần Thị Bính", "", "", "", "Con ông Từ Hữu Phù (Tửu). Vợ là Bà Trần Thị Bính. Sinh hạ: Từ Thị Thảo, Từ Thị Hiền, Từ Hữu Trung.", "", ""),
                    ("111.10.1.016", "111.09.0.004", "Từ Thị Xuân", "", "Trần Tám", "", "", "", "Con ông Từ Hữu Phù (Tửu). Lấy anh Trần Tám (Cân) trong làng.", "", ""),
                    
                    ("111.10.0.017", "111.09.0.006", "Từ Hữu Huề", "", "Bà Trần Thị Quế", "", "", "", "Con ông Từ Hữu Dấu. Vợ là Bà Trần Thị Quế. Sinh hạ: Từ Hữu Tuấn, Từ Hữu Anh.", "", ""),
                    ("111.10.0.018", "111.09.0.006", "Từ Hữu Huê", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Dấu. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.019", "111.09.0.006", "Từ Hữu Hoà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Dấu. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.020", "111.09.0.006", "Từ Thị Phương", "", "Không rõ", "", "", "", "Con ông Từ Hữu Dấu.", "", ""),

                    ("111.10.0.021", "111.09.0.009", "Từ Hữu Quân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hồng. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.022", "111.09.0.009", "Từ Thị Thanh", "", "", "", "", "", "Con ông Từ Hữu Hồng. Mất do chết đuối.", "Chết sớm", ""),
                    ("111.10.1.023", "111.09.0.009", "Từ Thị Lý", "", "Không rõ", "", "", "", "Con ông Từ Hữu Hồng.", "", ""),
                    ("111.10.0.024", "111.09.0.009", "Từ Hữu Mạo", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hồng. Đang cập nhật thông tin vợ con.", "", ""),

                    ("111.10.1.025", "111.09.0.010", "Từ Thị Hoa", "", "Không rõ", "", "", "", "Con ông Từ Hữu Bàng.", "", ""),
                    ("111.10.0.026", "111.09.0.010", "Từ Hữu Lan", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bàng. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.027", "111.09.0.010", "Từ Thị Phương", "", "Không rõ", "", "", "", "Con ông Từ Hữu Bàng.", "", ""),

                    ("111.10.1.028", "111.09.0.012", "Từ Thị Nga", "", "Không rõ", "", "", "", "Con ông Từ Hữu Bính.", "", ""),
                    ("111.10.0.029", "111.09.0.012", "Từ Hữu Sửu", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bính. Đang cập nhật thông tin vợ con.", "", ""),

                    ("111.10.0.030", "111.09.0.014", "Từ Hữu Hải", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lương. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.031", "111.09.0.014", "Từ Hữu Hiệp", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lương. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.032", "111.09.0.014", "Từ Thị Thuỷ", "", "Không rõ", "", "", "", "Con ông Từ Hữu Lương.", "", ""),

                    ("111.10.1.033", "111.09.0.017", "Từ Thị Thanh", "", "Không rõ", "", "", "", "Con ông Từ Hữu Huy.", "", ""),
                    ("111.10.0.034", "111.09.0.017", "Từ Hữu Danh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Huy. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.035", "111.09.0.017", "Từ Hữu Nhân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Huy. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.036", "111.09.0.017", "Từ Hữu Nghĩa", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Huy. Đang cập nhật thông tin vợ con.", "", ""),

                    ("111.10.1.037", "111.09.0.019", "Từ Thị Hoài", "", "Không rõ", "", "", "", "Con ông Từ Hữu Hiếu (vợ cả Nguyễn Thị Vân).", "", ""),



                    ("111.10.0.060", "111.09.0.025", "Từ Hữu Cháu", "", "Bà Lương", "", "", "", "Con ông Từ Hữu Lai. Sinh hạ: Từ Thị Hồng Nhung, Từ Hữu Khánh.", "", ""),
                    ("111.10.1.061", "111.09.0.025", "Từ Thị Lý", "", "Ông Quế", "", "", "", "Con ông Từ Hữu Lai. Chồng là Ông Quế ở trong xã.", "", ""),
                    ("111.10.0.062", "111.09.0.025", "Từ Hữu Quy", "", "Bà Hiền", "", "", "", "Con ông Từ Hữu Lai. Sinh hạ: Từ Thị Hồng Ngọc, Từ Quang Chung.", "", ""),
                    ("111.10.0.063", "111.09.0.025", "Từ Hữu Định", "", "Trần Thị Bính", "", "", "", "Con ông Từ Hữu Lai. Sinh hạ: Từ Hữu Thắng, Từ Thị Thắm, Từ Hữu Quyết Tiến, Từ Thị Linh.", "", ""),
                    ("111.10.0.064", "111.09.0.025", "Từ Hữu Luật", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lai. Sinh hạ: Từ Thị Ngọc Linh, Từ Thị Ngọc Hà.", "", ""),
                    ("111.10.1.065", "111.09.0.025", "Từ Thị Luận", "", "Nguyễn Doãn Tuấn", "", "", "", "Con ông Từ Hữu Lai. Chồng là Nguyễn Doãn Tuấn.", "", ""),
                    ("111.10.0.066", "111.09.0.025", "Từ Hữu Duẫn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lai. Sinh hạ: Từ Hữu Phong, Từ Hữu Việt Anh, Từ Hữu... (đang cập nhật).", "", ""),

                    ("111.10.0.067", "111.09.0.028", "Từ Hữu Cháu", "", "", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm)..", "Tảo vong", ""),
                    ("111.10.1.068", "111.09.0.028", "Từ Thị Nghiệm", "", "Không rõ", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm).", "", ""),
                    ("111.10.0.069", "111.09.0.028", "Từ Hữu Sơn", "", "Bà Trần Thị Liên", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm). Sinh hạ: Từ Hữu Trường, Từ Thị Vân, Từ Hữu Lý, Từ Hữu Tài, Từ Hữu Giang.", "", ""),
                    ("111.10.0.070", "111.09.0.028", "Từ Hữu Thân", "", "Bà Trần Thị Diên", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm). Sinh hạ: Từ Hữu Bản, Từ Hữu Mạnh, Từ Thị Cần.", "", ""),
                    ("111.10.0.071", "111.09.0.028", "Từ Hữu Thìn", "", "Không rõ", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm). Liệt sỹ.", "", ""),
                    ("111.10.0.072", "111.09.0.028", "Từ Hữu Hải", "", "Bà Trần Thị Hường", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm). Sinh hạ: Từ Hữu Thuận.", "", ""),
                    ("111.10.1.073", "111.09.0.028", "Từ Thị Hà", "", "Không rõ", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm).", "", ""),
                    ("111.10.0.074", "111.09.0.028", "Từ Hữu Nga", "", "Bà Trần Thị Cúc", "", "", "", "Con ông Từ Hữu Lượng (Nghiệm). Sinh hạ: Từ Hữu Anh, Từ Hữu Hoàng.", "", ""),

                    ("111.10.1.075", "111.09.0.035", "Từ Minh Nguyệt", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Sâm.", "", ""),
                    ("111.10.1.076", "111.09.0.035", "Từ Nguyệt Nga", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Sâm.", "", ""),
                    ("111.10.1.077", "111.09.0.035", "Từ Lê Nguyệt Ánh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Sâm.", "", ""),

                    ("111.10.1.078", "111.09.0.037", "Từ Thị Hường", "", "Không rõ", "", "", "", "Con ông Từ Hữu Hợp.", "", ""),
                    ("111.10.0.079", "111.09.0.037", "Từ Hữu Định", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hợp. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.080", "111.09.0.037", "Từ Hữu Tuấn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hợp. Đang cập nhật thông tin vợ con.", "", ""),

                    ("111.10.0.081", "111.09.0.042", "Từ Hải Minh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đạt. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.082", "111.09.0.042", "Từ Ngân Khánh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đạt.", "", ""),



                    ("111.10.0.093", "111.09.0.047", "Từ Ngọc Nhân", "", "Đang cập nhật", "", "", "", "Con ông Từ Ngọc Lương. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.094", "111.09.0.047", "Từ Ngọc Vỵ", "", "Đang cập nhật", "", "", "", "Con ông Từ Ngọc Lương. Đang cập nhật thông tin vợ con.", "", ""),

                    ("111.10.1.095", "111.09.0.048", "Từ Thị Mai", "", "Đang cập nhật", "", "", "", "Con ông Từ Ngọc Long.", "", ""),
                    ("111.10.1.096", "111.09.0.048", "Từ Thị Huyền", "", "Đang cập nhật", "", "", "", "Con ông Từ Ngọc Long.", "", ""),

                    ("111.10.0.097", "111.09.0.051", "Từ Ngọc Ý", "", "Đang cập nhật", "", "", "", "Con ông Từ Ngọc Lĩnh. Đang cập nhật thông tin vợ con.", "", ""),


                    ("111.10.1.101", "111.09.0.055", "Từ Thị Mai", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cát.", "", ""),
                    ("111.10.0.102", "111.09.0.055", "Từ Hữu Thuận", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cát. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.103", "111.09.0.055", "Từ Thị Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cát.", "", ""),
                    ("111.10.0.104", "111.09.0.055", "Từ Hữu Thoả", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cát. Đang cập nhật thông tin vợ con.", "", ""),

                    ("111.10.0.105", "111.09.0.056", "Từ Hữu Hoàn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Nhung. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.0.106", "111.09.0.056", "Từ Hữu Hải", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Nhung. Đang cập nhật thông tin vợ con.", "", ""),



                    ("111.10.0.111", "111.09.0.061", "Từ Hữu Linh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bình. Đang cập nhật thông tin vợ con.", "", ""),
                    ("111.10.1.112", "111.09.0.061", "Từ Thị Tâm", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bình.", "", ""),

        
                    
                    # ------------------------------------
                    # CHI 2
                    # ------------------------------------
                    ("122.10.1.001", "122.09.0.001", "Từ Thị Hoà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuyến.", "", ""),
                    ("122.10.0.002", "122.09.0.001", "Từ Hữu Thoả", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuyến. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.0.003", "122.09.0.001", "Từ Hữu Thành", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuyến. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.0.004", "122.09.0.001", "Từ Hữu Tuyền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuyến. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.1.005", "122.09.0.001", "Từ Thị Mỏ", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuyến.", "", ""),
                    ("122.10.1.006", "122.09.0.001", "Từ Thị Mậu", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuyến.", "", ""),

                    ("122.10.0.007", "122.09.0.002", "Từ Hữu Hùng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.1.008", "122.09.0.002", "Từ Thị Dũng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ.", "", ""),
                    ("122.10.0.009", "122.09.0.002", "Từ Hữu Kiên", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ. Chết sớm.", "", ""),
                    ("122.10.0.010", "122.09.0.002", "Từ Hữu Cường", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.1.011", "122.09.0.002", "Từ Thị Phú", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ. Lấy chồng về Mỹ Lộc.", "", ""),
                    ("122.10.1.012", "122.09.0.002", "Từ Thị Hựu", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ.", "", ""),
                    ("122.10.1.013", "122.09.0.002", "Từ Thị Hạnh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ.", "", ""),
                    ("122.10.0.014", "122.09.0.002", "Từ Hữu Phúc", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.0.015", "122.09.0.002", "Từ Hữu Vừng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Cừ. Đang cập nhật thông tin vợ con.", "", ""),


                    ("122.10.1.030", "122.09.0.015", "Từ Thị Bích Loan", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Trung. Lấy chồng về tỉnh Lâm Đồng.", "", ""),
                    ("122.10.0.031", "122.09.0.015", "Từ Ngọc Luân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Trung. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.0.032", "122.09.0.015", "Từ Ngọc Lễ", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Trung. Đang cập nhật thông tin vợ con.", "", ""),

                    ("122.10.0.033", "122.09.0.016", "Từ Hữu Huy", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thông. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.0.034", "122.09.0.016", "Từ Hữu Ngọc", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thông. Đang cập nhật thông tin vợ con.", "", ""),

                    ("122.10.0.035", "122.09.0.017", "Từ Hữu Thỏa", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tiến. Đang cập nhật thông tin vợ con.", "", ""),
                    ("122.10.1.036", "122.09.0.017", "Từ Thị Ly", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tiến.", "", ""),
                    ("122.10.1.037", "122.09.0.017", "Từ Thị Linh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tiến.", "", ""),

                    ("122.10.1.038", "122.09.0.019", "Từ Ngọc Anh Thư", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Trường.", "", ""),
                    ("122.10.0.039", "122.09.0.019", "Từ Vĩnh Cường", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Trường. Đang cập nhật thông tin vợ con.", "", ""),

                    ("122.10.1.040", "122.09.0.021", "Từ Thị Ngọc Trân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thân.", "", ""),
                    ("122.10.1.041", "122.09.0.021", "Từ Thị Ngọc Châu", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thân.", "", ""),

                    

      
                    ("124.10.1.071", "124.09.0.055", "Từ Nguyễn Gia Hân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hải Thành.", "", ""),
                    ("124.10.1.072", "124.09.0.055", "Từ Mỹ Duyên", "", "Đang cập nhật", "", "", "", "Con ông Từ Hải Thành.", "", ""),
                    ("124.10.0.073", "124.09.0.055", "Từ Hải Đăng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hải Thành. Đang cập nhật thông tin vợ con.", "", ""),

                    ("124.10.1.074", "124.09.0.059", "Từ Ngọc Huyền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hoàng.", "", ""),


                    # ------------------------------------
                    # CHI 3
                    # ------------------------------------
                    ("135.10.0.001", "135.09.0.001", "Từ Hữu Dũng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hoà. Đang cập nhật thông tin vợ con.", "", ""),
                    ("135.10.0.002", "135.09.0.001", "Từ Hữu Trung", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hoà. Đang cập nhật thông tin vợ con.", "", ""),

                    ("135.10.1.003", "135.09.0.002", "Từ Thị Anh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bình.", "", ""),
                    ("135.10.1.004", "135.09.0.002", "Từ Thị Mỹ", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bình.", "", ""),
                    ("135.10.0.005", "135.09.0.002", "Từ Hữu Việt", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bình. Đang cập nhật thông tin vợ con.", "", ""),
                    ("135.10.0.006", "135.09.0.002", "Từ Hữu Đức", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Bình. Đang cập nhật thông tin vợ con.", "", ""),

                    ("135.10.1.007", "135.09.0.003", "Từ Thị Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hạnh.", "", ""),
                    ("135.10.0.008", "135.09.0.003", "Từ Hữu Phúc", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hạnh. Đang cập nhật thông tin vợ con.", "", ""),

                    ("135.10.1.009", "135.09.0.010", "Từ Thị Nhung", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tân.", "", ""),
                    ("135.10.0.010", "135.09.0.010", "Từ Hữu Tài", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tân. Đang cập nhật thông tin vợ con.", "", ""),
                    ("135.10.0.011", "135.09.0.010", "Từ Hữu Chiến", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tân. Đang cập nhật thông tin vợ con.", "", ""),

                    ("135.10.0.012", "135.09.0.011", "Từ Hữu Trung", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thân. Đang cập nhật thông tin vợ con.", "", ""),
                    ("135.10.0.013", "135.09.0.011", "Từ Hữu Thông", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thân. Đang cập nhật thông tin vợ con.", "", ""),

                    ("135.10.0.014", "135.09.0.013", "Từ Hữu Quốc", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hùng. Đang cập nhật thông tin vợ con.", "", ""),
                    ("135.10.0.015", "135.09.0.013", "Từ Hữu Khánh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hùng. Đang cập nhật thông tin vợ con.", "", ""),


                    # ------------------------------------
                    # CHI 4
                    # ------------------------------------              
                    ("246.10.0.001", "246.09.0.002", "Từ Hữu Thông", "", "Đặng Thị Thuyết", "", "", "", "Con ông Từ Hữu Hạ. Vợ là Đặng Thị Thuyết. Sinh hạ: Từ Hữu Thuận, Từ Huy Hoàng.", "", ""),
                    ("246.10.0.002", "246.09.0.002", "Từ Hữu Minh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hạ. Đang cập nhật thông tin vợ con.", "", ""),

                    ("246.10.1.003", "246.09.0.004", "Từ Thị Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đông.", "", ""),
                    ("246.10.0.004", "246.09.0.004", "Từ Hữu Hưng", "", "Trần Thị Đào", "", "", "", "Con ông Từ Hữu Đông. Vợ là Trần Thị Đào. Sinh hạ: Từ Hải Đăng", "", ""),

                    ("246.10.1.005", "246.09.0.009", "Từ Thị Nga", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Nam.", "", ""),
                    ("246.10.0.006", "246.09.0.009", "Từ Hữu Vũ", "", "Lê Thị Hương", "", "", "", "Con ông Từ Hữu Nam. Vợ là Lê Thị Hương. Sinh hạ: Từ Quốc Anh.", "", ""),

                    ("246.10.1.007", "246.09.0.010", "Từ Thị Thắm", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lục.", "", ""),
                    ("246.10.1.008", "246.09.0.010", "Từ Thị Thuỳ", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lục.", "", ""),

                    ("246.10.0.009", "246.09.0.012", "Từ Hữu Bình", "", "Trần Thị Thanh Huyền", "", "", "", "Con ông Từ Hữu Thành. Vợ là Trần Thị Thanh Huyền.", "", ""),
                    ("246.10.0.010", "246.09.0.012", "Từ Hữu Ngọc", "", "Nguyễn Thị Mỹ Linh", "", "", "", "Con ông Từ Hữu Thành. Vợ là Nguyễn Thị Mỹ Linh. Sinh hạ: Từ Hữu Hiếu.", "", ""),
                    ("246.10.0.011", "246.09.0.012", "Từ Hữu Tuấn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thành. Đang cập nhật.", "", ""),

                    ("246.10.0.012", "246.09.0.015", "Từ Mạnh Hùng", "", "Thái Thị Minh Thu", "", "", "", "Con ông Từ Mạnh Mậu. Vợ là Thái Thị Minh Thu Sinh hạ: Từ Thái Đức Anh, Từ Gia Bảo.", "", ""),
                    ("246.10.1.013", "246.09.0.015", "Từ Thị Việt Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Mạnh Mậu.", "", ""),

                    ("246.10.0.014", "246.09.0.018", "Từ Huy Trung", "", "Đang cập nhật", "", "", "", "Con ông Từ Quốc Lệ. Sinh hạ: Từ Quốc Bảo.", "", ""),
                    ("246.10.1.015", "246.09.0.018", "Từ Thị Huyền Nga", "", "Đang cập nhật", "", "", "", "Con ông Từ Quốc Lệ.", "", ""),
                    ("246.10.0.016", "246.09.0.018", "Từ Quốc Việt", "", "Đang cập nhật", "", "", "", "Con ông Từ Quốc Lệ. Sinh hạ: Từ Quốc Sơn, Từ Quốc Hải.", "", ""),
                    ("246.10.1.017", "246.09.0.019", "Từ Thị Sâm", "", "Đang cập nhật", "", "", "", "Con ông Từ Quốc Đạt.", "", ""),
                    ("246.10.0.018", "246.09.0.019", "Từ Hữu Nhung", "", "Phạm Thị Hoài An", "", "", "", "Con ông Từ Quốc Đạt. Sinh hạ: Từ Quốc Tuấn, Từ Nam Phong, Từ Minh Khang, Từ Minh Huy.", "", ""),

                    ("246.10.1.019", "246.09.0.021", "Từ Thị Đức", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phúc.", "", ""),
                    ("246.10.0.020", "246.09.0.021", "Từ Hữu Lành", "", "Nguyễn Thị Lan", "", "", "", "Con ông Từ Hữu Phúc. Vợ là Nguyễn Thị Lan. Sinh hạ: Từ Nguyễn Duy Phước, Từ Duy Khải.", "", ""),
                    ("246.10.1.021", "246.09.0.021", "Từ Thị Hiền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phúc.", "", ""),
                    ("246.10.1.022", "246.09.0.021", "Từ Thị Thảo", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phúc.", "", ""),
                    ("246.10.0.023", "246.09.0.021", "Từ Hữu Quang", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phúc. Đang cập nhật thông tin vợ con.", "", ""),
                    
                    ("246.10.0.024", "246.09.0.022", "Từ Hữu Pháp", "", "Trần Thị Ngọc", "", "", "", "Con ông Từ Hữu Lý. Vợ là Trần Thị Ngọc. Sinh hạ: Từ Nhật Nam, Từ Nhật Đức", "", ""),
                    ("246.10.0.025", "246.09.0.022", "Từ Hữu Luân", "", "Đặng Thị Phương Thủy", "", "", "", "Con ông Từ Hữu Lý. Vợ là Đặng Thị Phương Thủy. Sinh hạ: Từ Hữu Bắc", "", ""),
                    ("246.10.1.026", "246.09.0.022", "Từ Thị Hồng Quyên", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lý.", "", ""),

                    ("246.10.0.027", "246.09.0.026", "Từ Nam Long", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Sơn. Đang cập nhật thông tin vợ con.", "", ""),
                    ("246.10.0.028", "246.09.0.026", "Từ Quốc Vương", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Sơn. Đang cập nhật thông tin vợ con.", "", ""),

                    ("246.10.0.029", "246.09.0.027", "Từ Hữu Việt", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lam. Đang cập nhật thông tin vợ con.", "", ""),

                    
                    # ------------------------------------
                    # CHI 5
                    # ------------------------------------            
                    ("258.10.0.001", "258.09.0.002", "Từ Hữu Sơn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Loan. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.002", "258.09.0.002", "Từ Thị Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Loan.", "", ""),
                    ("258.10.0.003", "258.09.0.002", "Từ Hữu Hải", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Loan. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.004", "258.09.0.002", "Từ Hữu Hùng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Loan. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.005", "258.09.0.002", "Từ Hữu Tuấn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Loan. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.006", "258.09.0.003", "Từ Hữu Long", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Ba. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.007", "258.09.0.003", "Từ Thu Mai", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Ba.", "", ""),

                    ("258.10.1.008", "258.09.0.006", "Từ Thị Nga", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phán. Lấy chồng về Trường Lộc.", "", ""),
                    ("258.10.1.009", "258.09.0.006", "Từ Thị Ngân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phán.", "", ""),
                    ("258.10.0.010", "258.09.0.006", "Từ Hữu Anh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phán. Chết sớm.", "", ""),
                    ("258.10.0.011", "258.09.0.006", "Từ Hữu Hùng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Phán. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.1.012", "258.09.0.011", "Từ Thị Nhung", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lục.", "", ""),
                    ("258.10.1.013", "258.09.0.011", "Từ Thị Thuỷ", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lục.", "", ""),
                    ("258.10.1.014", "258.09.0.011", "Từ Thị Lâm", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lục.", "", ""),

                    ("258.10.1.015", "258.09.0.012", "Từ Thị Hiền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lương.", "", ""),
                    ("258.10.1.016", "258.09.0.012", "Từ Thị Hữu", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lương.", "", ""),
                    ("258.10.0.017", "258.09.0.012", "Từ Hữu Đạt", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lương. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.018", "258.09.0.012", "Từ Hữu Phương", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lương. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.019", "258.09.0.013", "Từ Hữu Minh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đàn. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.020", "258.09.0.013", "Từ Thị Anh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đàn.", "", ""),

                    ("258.10.1.021", "258.09.0.014", "Từ Thị Tâm", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Liêm.", "", ""),
                    ("258.10.1.022", "258.09.0.014", "Từ Thị Như", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Liêm.", "", ""),

                    ("258.10.0.023", "258.09.0.015", "Từ Hữu Quỳnh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thanh. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.024", "258.09.0.015", "Từ Thị Oanh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Thanh.", "", ""),

                    ("258.10.0.025", "258.09.0.020", "Từ Ngọc Anh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuý. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.026", "258.09.0.020", "Từ Ngọc Dũng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuý. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.027", "258.09.0.020", "Từ Ngọc Cường", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuý. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.028", "258.09.0.020", "Từ Ngọc Quyền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuý. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.029", "258.09.0.020", "Từ Thị Hoa", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tuý.", "", ""),

                    ("258.10.0.030", "258.09.0.028", "Từ Hữu Thành", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hậu. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.031", "258.09.0.028", "Từ Thị Thanh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hậu.", "", ""),
                    ("258.10.1.032", "258.09.0.028", "Từ Thị Thắm", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hậu.", "", ""),
                    ("258.10.0.033", "258.09.0.028", "Từ Hữu Thiết", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Hậu. Đang cập nhật thông tin vợ con.", "", ""),


                    ("258.10.1.064", "258.09.0.038", "Từ Thị Liễu", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lý.", "", ""),
                    ("258.10.1.065", "258.09.0.038", "Từ Thị Lâm", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lý.", "", ""),
                    ("258.10.0.066", "258.09.0.038", "Từ Hữu Luân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lý. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.067", "258.09.0.038", "Từ Hữu Luật", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Lý. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.1.068", "258.09.0.040", "Từ Thị Bình", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Minh.", "", ""),
                    ("258.10.0.069", "258.09.0.040", "Từ Hữu Thanh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Minh. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.070", "258.09.0.040", "Từ Thị Xanh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Minh.", "", ""),
                    ("258.10.0.071", "258.09.0.040", "Từ Hữu Tuấn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Minh. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.072", "258.09.0.045", "Từ Hữu Nam", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Toàn. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.073", "258.09.0.045", "Từ Hữu Đông", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Toàn. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.1.074", "258.09.0.046", "Từ Thị Hằng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tiến.", "", ""),
                    ("258.10.0.075", "258.09.0.046", "Từ Hữu Tuấn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tiến. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.076", "258.09.0.046", "Từ Hữu Hải", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tiến. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.1.077", "258.09.0.047", "Từ Thị Nga", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Dũng.", "", ""),
                    ("258.10.0.078", "258.09.0.047", "Từ Hữu Anh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Dũng. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.079", "258.09.0.047", "Từ Hữu Sơn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Dũng. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.080", "258.09.0.049", "Từ Hữu Quý", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Giáp. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.081", "258.09.0.049", "Từ Thị Huyền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Giáp.", "", ""),
                    ("258.10.0.082", "258.09.0.049", "Từ Hữu Quyền", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Giáp. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.083", "258.09.0.049", "Từ Hữu Lợi", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Giáp. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.1.084", "258.09.0.051", "Từ Thị Hạnh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Huề.", "", ""),
                    ("258.10.1.085", "258.09.0.051", "Từ Thị Linh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Huề.", "", ""),
                    ("258.10.0.086", "258.09.0.051", "Từ Hữu Khoa", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Huề. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.087", "258.09.0.053", "Từ Hữu Thắng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đại. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.088", "258.09.0.053", "Từ Hữu Đông", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đại. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.089", "258.09.0.053", "Từ Hữu Trường", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đại. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.090", "258.09.0.053", "Từ Thị Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đại.", "", ""),
                    ("258.10.0.091", "258.09.0.053", "Từ Hữu Đồng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Đại. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.092", "258.09.0.056", "Từ Hữu Sơn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Em. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.093", "258.09.0.056", "Từ Thị Thuỷ", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Em.", "", ""),
                    ("258.10.0.094", "258.09.0.056", "Từ Hữu Hùng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Em. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.0.095", "258.09.0.061", "Từ Hữu Phú", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Chất. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.0.096", "258.09.0.061", "Từ Hữu Dũng", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Chất. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.097", "258.09.0.061", "Từ Thị Anh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Chất.", "", ""),
                    ("258.10.0.098", "258.09.0.061", "Từ Hữu Văn", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Chất. Đang cập nhật thông tin vợ con.", "", ""),

                    ("258.10.1.099", "258.09.0.062", "Từ Thị Xuân", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tạo.", "", ""),
                    ("258.10.0.100", "258.09.0.062", "Từ Hữu Hạnh", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tạo. Đang cập nhật thông tin vợ con.", "", ""),
                    ("258.10.1.101", "258.09.0.062", "Từ Thị Hà", "", "Đang cập nhật", "", "", "", "Con ông Từ Hữu Tạo.", "", ""),

                ]


                # 🔍 DÁN ĐOẠN KIỂM TRA VÀO ĐÂY:
                for index, record in enumerate(raw_data):
                    if len(record) != 16:
                        print(f"⚠️ Phát hiện lỗi ở record thứ {index + 1} (ID: {record[0]} - {record[2]}): Có {len(record)} phần tử (Yêu cầu đúng 11).")



                
                insert_query = """
                INSERT INTO GiaPha (
                    ID, ChaID, HoTen, TenTu, VoChong, NamSinh, NamMat, NgayGio, 
                    ChucDanh_GhiChu, TinhTrang, HinhAnh
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.executemany(insert_query, raw_data)
                conn.commit()

    #=====================================================================
    # [PHÂN LÔ B2]: Hàm con tải dữ liệu từ SQLite sang DataFrame DataFrame
    #=====================================================================
    @classmethod
    def load_data(cls):
        cls.init_database()
        with sqlite3.connect(cls.DB_FILE) as conn:
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


# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [PHÂN LÔ C] - KHU VỰC BẢN VẼ HÌNH HỌC GRAPHVIZ (TÍCH HỢP ZOOM & PAN DI ĐỘNG)
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

class KyThuatBanVeGiaPha:

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
        
        con_nuoi_tag = ""
        if "con nuôi" in tinh_trang.lower() or member_id == "100.03.0.004":
            con_nuoi_tag = "\n(Con nuôi)"
        
        if doi_num == 1:
            hien_tu = f" (Tự: {ten_tu})" if ten_tu else " (Tự: Huy Cán)"
            return f"Từ Dương Đốc {doi_khoanh}\n(Thủy Tổ{hien_tu}){di_cu_tag}{con_nuoi_tag}"
        elif doi_num == 2:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            if member_id == "000.02.1.003":
                return f"{ten_rut_gon} {doi_khoanh}\n(Lấy chồng)"
            return f"{ten_rut_gon} {doi_khoanh}\n(Đứng đầu Cửa {cua}){di_cu_tag}{con_nuoi_tag}"
        elif doi_num == 3:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            if member_id == "100.03.0.004" or "con nuôi" in tinh_trang.lower():
                return f"{ten_rut_gon} {doi_khoanh}\n(Con nuôi)"
            ten_chi = chi.split("(")[0].strip() if "(" in chi else chi
            return f"{ten_rut_gon} {doi_khoanh}\n({ten_chi}){di_cu_tag}{con_nuoi_tag}"
        else:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            return f"{ten_rut_gon} {doi_khoanh}{di_cu_tag}{con_nuoi_tag}"

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
            children = children.sort_values(by="STT")

        for _, child in children.iterrows():
            c_id = str(child['ID'])
            c_label = cls.tao_nhan_ton_kinh(child.to_dict())
            gioi_tinh = str(child.get('GioiTinh', 'Nam'))
            c_doi_num = int(child['DoiThu'])
            
            c_fill = "#FFF0F5" if gioi_tinh == "Nữ" else QuanTriTaiNguyen.COLOR_PALETTE.get(c_doi_num, "#E8F5E9")
            c_shape = "box" if gioi_tinh == "Nữ" else "box"
            
            dot.node(c_id, c_label, fillcolor=c_fill, color="#2E7D32", shape=c_shape, style="filled,rounded", penwidth="1.2")
            dot.edge(str(focus_id), c_id, color="#2E7D32", penwidth="1.5")
        return dot


    #=====================================================================
    # [PHÂN LÔ C5]: Hàm con vẽ sơ đồ toàn cảnh / Trục dọc theo ID
    #=====================================================================
    @classmethod
    def draw_family_tree(cls, df_data, cua_loc="Tất cả", chi_loc="Tất cả", phai_loc="Tất cả", che_do_xem="1. Chỉ Đinh Nam (Gọn: Tên ⑦)", target_id=""):
        dot = Digraph(comment='Gia Phả Toàn Cảnh', node_attr={'style': 'filled,rounded', 'fontname': 'Arial', 'fontsize': '10', 'margin': '0.04,0.04', 'width': '0', 'height': '0'})
        dot.attr(rankdir='TB', splines='polyline', ordering='out')
        
        df_approved = df_data[df_data["TrangThai"] == "Đã duyệt"].copy()
        
        if "RecordIndex" in df_approved.columns:
            df_approved = df_approved.sort_values(by="RecordIndex")
            
        clean_target_id = str(target_id).strip()
        if clean_target_id:
            valid_ids = set()
            # 1. Truy ngược toàn bộ tổ tiên lên trên (Thủy tổ -> Ông -> Cha) tạo thành hàng dọc
            curr = clean_target_id
            visited = set()
            while curr and curr != "0" and curr not in visited:
                visited.add(curr)
                valid_ids.add(curr)
                p_row = df_approved[df_approved["ID"] == curr]
                if p_row.empty:
                    break
                curr = str(p_row.iloc[0].get("ChaMe_ID", ""))
                
            # 2. Quét toàn bộ con cháu tỏa ra bên dưới từ ID mục tiêu
            queue = [clean_target_id]
            descendant_visited = set()
            while queue:
                c_curr = queue.pop(0)
                if c_curr in descendant_visited:
                    continue
                descendant_visited.add(c_curr)
                valid_ids.add(c_curr)
                
                children = df_approved[df_approved["ChaMe_ID"] == c_curr]
                for _, ch in children.iterrows():
                    queue.append(str(ch["ID"]))
                    
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
                    if node_id == "000.02.1.003":
                        label = f"{ho_ten} {doi_khoanh}\n(Lấy chồng)"
                    else:
                        label = f"{ho_ten} {doi_khoanh}\n(Đứng đầu Cửa {cua}){di_cu_tag}{con_nuoi_tag}"
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
                la_mat_som = any(kw in tinh_trang_lower for kw in ["chết sớm", "tảo vong", "tảo một"])
                
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
                la_mat_som = any(kw in tinh_trang_lower for kw in ["chết sớm", "tảo vong", "tảo một"])
                
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

            if is_target:
                fill, shape, color, pen_width = "#FFE082", "box", "#C62828", "2.5"
            elif node_id == "000.02.1.003" or gioi_tinh == "Nữ":
                fill, shape, color, pen_width = "#FFF0F5", "box", "#D81B60", "1.2"
            else:
                fill, shape, color, pen_width = QuanTriTaiNguyen.COLOR_PALETTE.get(doi_num, "#FFFFFF"), "box", "#455A64", "1.2"
            
            dot.node(node_id, label, fillcolor=fill, shape=shape, color=color, penwidth=pen_width)

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
    # [PHÂN LÔ D1]: Hàm con nén và lưu trữ ảnh tải lên
    #=====================================================================
    @staticmethod
    def xu_ly_va_nen_anh(uploaded_file, save_path):
        try:
            img = Image.open(uploaded_file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            img.save(save_path, "JPEG", quality=85)
            return True
        except:
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
    #=====================================================================
    @staticmethod
    def thiet_lap_giao_dien():
        st.set_page_config(page_title="Gia phả điện tử dòng Họ Từ Xuân Lộc", page_icon="📜", layout="wide")
        st.markdown("""
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
            <style>
                .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem; }
                .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; margin-bottom: 5px; }
                .hd-zoom { font-size: 0.85rem; color: #546E7A; margin-bottom: 8px; }
                [data-testid="stDataFrame"] div[data-baseweb="table"] td {
                    white-space: normal !important;
                    word-wrap: break-word !important;
                    height: auto !important;
                }
                .desktop-view { display: block; }
                .mobile-view { display: none; }
                
                @media (max-width: 768px) {
                    .desktop-view { display: none !important; }
                    .mobile-view { display: block !important; }
                    .hide-on-mobile { display: none !important; }
                    h1.mobile-view { font-size: 1.15rem !important; font-weight: bold; white-space: nowrap; margin-bottom: -22px !important; }
                    h2.mobile-view { font-size: 1.15rem !important; margin-top: -5px !important; margin-bottom: 0px !important; }
                }
            </style>
        """, unsafe_allow_html=True)

    #=====================================================================
    # [PHÂN LÔ E2]: Hàm con render màn hình Trực Hệ
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
            
            hop_le_path = QuanTriHinhAnh.lay_anh_chuan_xac(curr_person['ID'], curr_person['HoTen'])
            if hop_le_path and (Path(__file__).resolve().parent / hop_le_path).exists():
                st.image(str(Path(__file__).resolve().parent / hop_le_path), width=180, caption=f"Chân dung: {curr_person['HoTen']}")

            st.markdown(f"### 👤 Cụ: **{curr_person['HoTen']}{ten_tu_txt} {QuanTriTaiNguyen.get_circled_doi(curr_person['DoiThu'], curr_person['TinhTrang'])}**")
            st.write(f"- **Mã định danh:** `{curr_person['ID']}`")
            st.write(f"- **Thuộc:** {curr_person['Cua']} — {curr_person['Chi']} {('— ' + curr_person['Phai']) if curr_person['Phai'] else ''}")
            
            if curr_person['VoChong']:
                st.write(f"- **{'Bà' if curr_person.get('GioiTinh') == 'Nam' else 'Chồng'}:** {curr_person['VoChong']}")
            if curr_person['NgayGio']: st.write(f"- **Ngày giỗ:** {curr_person['NgayGio']}")
            if curr_person['NamSinh'] or curr_person['NamMat']: st.write(f"- **Năm sinh/mất:** {curr_person['NamSinh']} - {curr_person['NamMat']}")
            if curr_person['GhiChu']: st.write(f"- **Ghi chú:** {curr_person['GhiChu']}")
            if curr_person['TinhTrang']: st.write(f"- **Tình trạng:** {curr_person['TinhTrang']}")

            st.markdown("---")

            raw_children = df[(df["ChaMe_ID"] == str(st.session_state.focus_id)) & (df["TrangThai"] == "Đã duyệt")]
            
            # Lọc bỏ nữ giới và các trường hợp có chấm tròn tuyệt tôn / chết sớm / phạp tự / tảo vong...
            filtered_children = []
            keyword_list = ["phạp tự", "không có con", "tảo vong", "tảo một", "chết sớm"]
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

    #=====================================================================
    # [PHÂN LÔ E3]: Hàm con render màn hình Toàn Cảnh
    #=====================================================================
    @staticmethod
    def render_toancanh(df):
        st.subheader("Sơ Đồ Phả Hệ Toàn Cảnh")
        col1, col2, col3, col4 = st.columns(4)
        with col1: che_do_xem = st.selectbox("1. Chế độ hiển thị:", ["1. Chỉ Đinh Nam (Gọn: Tên ⑦)", "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)", "3. Chỉ Đinh Nam (Đủ vợ và chồng)", "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)"])
        with col2: cua_chon = st.selectbox("2. Lọc theo Cửa:", ["Tất cả"] + sorted([c for c in df['Cua'].unique() if c and c != "Gốc"]))
        with col3:
            df_tc = df[df['Cua'] == cua_chon] if cua_chon != "Tất cả" else df
            danh_sach_chi = QuanTriTaiNguyen.lay_danh_sach_chi_chuan(df_tc)
            chi_chon = st.selectbox("3. Lọc theo Chi:", ["Tất cả"] + danh_sach_chi)
        with col4:
            df_pc = df[df['Chi'] == chi_chon] if chi_chon != "Tất cả" else df
            sorted_phai = QuanTriTaiNguyen.sap_xep_danh_sach_phai(df_pc['Phai'].unique())
            phai_chon = st.selectbox("4. Lọc theo Phái:", ["Tất cả"] + sorted_phai)

        st.markdown("<div class='hd-zoom hide-on-mobile'>💡 <b>Trên điện thoại:</b> Dùng 2 ngón tay kéo dãn để zoom to, hoặc bấm nút <b>(+)</b> để nhìn rõ từng đời.</div>", unsafe_allow_html=True)
        try:
            tree_graph = KyThuatBanVeGiaPha.draw_family_tree(df, cua_chon, chi_chon, phai_chon, che_do_xem)
            KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(tree_graph, chieu_cao=680)
        except Exception as e:
            st.error(f"Lỗi hiển thị: {e}")

    #=====================================================================
    # [PHÂN LÔ E4]: Hàm con render màn hình Tra Cứu
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
            
        st.dataframe(df_app[["STT", "ID", "ChaMe_ID", "HoTen", "TenTu", "VoChong", "NamSinh", "NamMat", "NgayGio", "GhiChu", "TinhTrang", "HinhAnh"]], use_container_width=True, hide_index=True)



    
        

    #=====================================================================
    # [PHÂN LÔ E5]: Hàm con render màn hình Thêm Thành Viên
    #=====================================================================
    @staticmethod
    def render_themthanhvien(df):
        st.subheader("Gửi đề xuất thêm thành viên mới")
        with st.form("form_add_member"):
            c1, c2 = st.columns(2)
            with c1:
                new_id = st.text_input("Mã định danh [9 số, ví dụ: 123.04.0.011] (*):")
                ho_ten = st.text_input("Họ và Tên (*):")
                ten_tu = st.text_input("Tên tự / Tên hiệu:")
            with c2:
                df_parents = df[(df["TrangThai"] == "Đã duyệt") & (df["GioiTinh"] == "Nam")][["ID", "HoTen", "DoiThu"]]
                parent_dict = {row['ID']: f"{row['ID']} - {row['HoTen']} (Đời {row['DoiThu']})" for _, row in df_parents.iterrows()}
                parent_dict[""] = "Không rõ / Gốc khởi đầu"
                cha_id = st.selectbox("Mã định danh của Cha (ChaID):", options=list(parent_dict.keys()), format_func=lambda x: parent_dict[x])
                vo_chong = st.text_input("Vợ / Chồng:")

            c3, c4 = st.columns(2)
            with c3:
                nam_sinh = st.text_input("Năm sinh:")
                nam_mat = st.text_input("Năm mất:")
            with c4:
                ngay_gio = st.text_input("Ngày giỗ Âm lịch (ví dụ: 15/07 AL):")
                tinh_trang = st.selectbox("Tình trạng:", ["", "Phạp tự", "Không có con", "Tảo vong", "Tảo một", "Chết sớm", "Con nuôi", "di cư, không rõ"])

            ghi_chu = st.text_area("Chức danh / Ghi chú lịch sử:")
            uploaded_file = st.file_uploader("Hình ảnh chân dung:", type=["jpg", "jpeg", "png"])
            btn_submit = st.form_submit_button("📤 Gửi đề xuất ghi vào SQL")
            
            if btn_submit:
                hinh_anh_path = ""
                if uploaded_file is not None:
                    os.makedirs("images", exist_ok=True)
                    file_path = Path(__file__).resolve().parent / "images" / f"{ho_ten.strip()}.jpg"
                    if QuanTriHinhAnh.xu_ly_va_nen_anh(uploaded_file, file_path):
                        hinh_anh_path = f"images/{ho_ten.strip()}.jpg"

                success, messages = KhoDuLieuSQL.insert_member(
                    new_id=new_id, ho_ten=ho_ten, ten_tu=ten_tu, cha_id=cha_id,
                    vo_chong=vo_chong, nam_sinh=nam_sinh, nam_mat=nam_mat, ngay_gio=ngay_gio,
                    ghi_chu=ghi_chu, tinh_trang=tinh_trang, hinh_anh=hinh_anh_path
                )
                if success: st.success(messages[0])
                else: 
                    for err in messages: st.error(err)

    #=====================================================================
    # [PHÂN LÔ E6]: Hàm con render màn hình Xuất Báo Cáo & In Ấn
    #=====================================================================
    @staticmethod
    def render_xuatbaocao(df):
        st.subheader("🖨️ Trung tâm Xuất Báo cáo & In ấn Phả Hệ")
        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
        
        export_df = df_app[["STT", "ID", "ChaMe_ID", "HoTen", "TenTu", "VoChong", "NamSinh", "NamMat", "NgayGio", "GhiChu", "TinhTrang", "HinhAnh"]].rename(columns={
            "ID": "Mã Định Danh", "ChaMe_ID": "Mã Cha/Mẹ", "HoTen": "Họ và Tên", "TenTu": "Tên Tự", 
            "VoChong": "Vợ/Chồng", "NamSinh": "Năm Sinh", "NamMat": "Năm Mất", "NgayGio": "Ngày Giỗ", 
            "GhiChu": "Ghi Chú", "TinhTrang": "Tình Trạng", "HinhAnh": "Hình Ảnh"
        })
        
        tab1, tab2 = st.tabs(["📥 Xuất dữ liệu (CSV)", "📄 In ấn báo cáo"])
        with tab1:
            st.download_button("📥 Tải xuống tệp CSV", export_df.to_csv(index=False).encode('utf-8-sig'), "GiaPha_HoTu.csv", "text/csv")
        with tab2:
            if st.button("🖨️ Mở cửa sổ In ấn / Xuất PDF"):
                html_report = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>@page {{ size: A4 landscape; margin: 10mm; }} body {{ font-family: 'Times New Roman'; }} table {{ width: 100%; border-collapse: collapse; }} th, td {{ border: 1px solid #333; padding: 5px; font-size: 10px; }} th {{ background: #f2f2f2; }}</style></head><body>
                <h1 style="text-align:center;">DÒNG HỌ TỪ XUÂN LỘC - PHẢ HỆ ĐỊNH DANH</h1>
                <table><thead><tr><th>STT</th><th>Mã Định Danh</th><th>Mã Cha/Mẹ</th><th>Họ Tên</th><th>Tên Tự</th><th>Vợ/Chồng</th><th>Năm Sinh</th><th>Năm Mất</th><th>Ngày Giỗ</th><th>Ghi Chú</th><th>Tình Trạng</th><th>Hình Ảnh</th></tr></thead><tbody>"""
                for _, r in export_df.iterrows():
                    html_report += f"<tr><td>{r['STT']}</td><td>{r['Mã Định Danh']}</td><td>{r['Mã Cha/Mẹ']}</td><td><b>{r['Họ và Tên']}</b></td><td>{r['Tên Tự']}</td><td>{r['Vợ/Chồng']}</td><td>{r['Năm Sinh']}</td><td>{r['Năm Mất']}</td><td>{r['Ngày Giỗ']}</td><td>{r['Ghi Chú']}</td><td>{r['Tình Trạng']}</td><td>{r['Hình Ảnh']}</td></tr>"
                html_report += "</tbody></table><script>window.print();</script></body></html>"
                components.html(html_report, height=600, scrolling=True)

    #=====================================================================
    # [PHÂN LÔ E7]: Hàm con render màn hình Quản Trị Hệ Thống
    #=====================================================================
    @staticmethod
    def render_quantri(df):
        st.subheader("Bảng Quản Trị Hệ Thống")
        mat_khau = st.sidebar.text_input("Mật khẩu Quản trị:", type="password")
        if mat_khau == "admin123":
            st.success("Xác thực Quản trị viên thành công!")
            chon_id = st.selectbox("Chọn Mã định danh thành viên cần xóa:", df["ID"].tolist())
            if st.button("❌ Xóa khỏi CSDL"):
                KhoDuLieuSQL.delete_member(chon_id)
                st.error(f"Đã xóa thành viên mã {chon_id}!")
                st.rerun()
        else:
            st.warning("Nhập mật khẩu quản trị (Mặc định: admin123).")


    #=====================================================================
    # [PHÂN LÔ E8]: Hàm con điều phối đầu não giao diện với menu chuẩn xác mới (Tối ưu Mobile Title)
    #=====================================================================
    @classmethod
    def render_app(cls):
        cls.thiet_lap_giao_dien()
        df = KhoDuLieuSQL.load_data()

        st.markdown('<h1 class="desktop-view" style="font-weight: bold; margin-bottom: 0px;">📜 Gia phả điện tử dòng Họ Từ Xuân Lộc</h1>', unsafe_allow_html=True)
        st.markdown('<h1 class="mobile-view" style="font-size: 1.15rem; font-weight: bold; white-space: nowrap; margin-bottom: 0px;">📜 Gia phả Họ Từ Xuân Lộc</h1>', unsafe_allow_html=True)
        
        st.markdown("""
            <div class="hide-on-mobile">
                <p style="color: #546E7A; margin-top: 5px; margin-bottom: 15px;">Hệ thống quản lý phả hệ chuẩn mực — Cơ sở dữ liệu SQLite tối ưu đa thiết bị</p>
            </div>
        """, unsafe_allow_html=True)

        if "focus_id" not in st.session_state:
            st.session_state.focus_id = "000.01.0.001"

        # Cập nhật menu theo đúng thứ tự ông chủ yêu cầu
        menu = st.sidebar.radio("CHỌN CHỨC NĂNG:", [
            "🎯 Trực Hệ", 
            "🌳 Toàn Cảnh", 
            "🆔 Lọc theo ID", 
            "🔍 Tra Cứu", 
            "✍ Thêm Thành Viên", 
            "🖨 Xuất Báo Cáo", 
            "🛡 Quản Trị Hệ Thống"
        ])
        
        if menu == "🎯 Trực Hệ": 
            cls.render_tructhe(df)
        elif menu == "🌳 Toàn Cảnh": 
            cls.render_toancanh(df)
        elif menu == "🆔 Lọc theo ID": 
            cls.render_loc_theo_id(df) # Màn hình chuyên biệt vẽ trục dọc và tỏa nhánh theo ID
        elif menu == "🔍 Tra Cứu": 
            cls.render_tracuu(df)
        elif menu == "✍ Thêm Thành Viên": 
            cls.render_themthanhvien(df)
        elif menu == "🖨 Xuất Báo Cáo": 
            cls.render_xuatbaocao(df)
        elif menu == "🛡 Quản Trị Hệ Thống": 
            cls.render_quantri(df)


 
    #=====================================================================
    # [PHÂN LÔ E9]: Màn hình chuyên biệt Lọc theo ID hoặc Tên (Sạch ký tự tuyệt đối)
    #=====================================================================
    @staticmethod
    def render_loc_theo_id(df):
        st.subheader("🆔 Sơ Đồ Trục Cội Nguồn & Tỏa Nhánh Theo ID / Tên")
        
        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
        
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            nhap_lieu = st.text_input("Nhập Họ và tên hoặc Mã định danh:", value="Từ Quang Diệu", placeholder="Ví dụ: Từ Quang Diệu, 124070049 hoặc 124.07.0.049")
        with c2:
            che_do_xem = st.selectbox("Chế độ hiển thị nhãn:", [
                "1. Chỉ Đinh Nam (Gọn: Tên ⑦)", 
                "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)", 
                "3. Chỉ Đinh Nam (Đủ vợ và chồng)", 
                "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)"
            ], index=1, key="che_do_xem_id")

        target_id = ""
        nhap_lieu_clean = nhap_lieu.strip()

        if nhap_lieu_clean:
            # 🟢 CHUẨN HÓA ĐẦU VÀO: Bỏ toàn bộ dấu chấm để hỗ trợ cả dạng 123040567 lẫn 123.04.0.567
            nhap_lieu_khong_cham = nhap_lieu_clean.replace(".", "")
            
            # Tạo một cột tạm trong DataFrame chứa ID đã bỏ dấu chấm để so sánh linh hoạt
            df_app['ID_KhongCham'] = df_app['ID'].str.replace(".", "", regex=False)
            
            matched_by_id = df_app[df_app["ID_KhongCham"] == nhap_lieu_khong_cham]
            
            if not matched_by_id.empty:
                # Lấy ID chuẩn chính xác trong cơ sở dữ liệu của bản ghi tìm thấy
                target_id = str(matched_by_id.iloc[0]['ID'])
                st.success(f"✅ Đã tìm thấy mã định danh: **{target_id}** — {matched_by_id.iloc[0]['HoTen']}")
            else:
                def chuan_hoa_dau(txt):
                    return str(txt).strip().lower().replace("oà", "òa").replace("uỳ", "uỳ").replace("úy", "uý")

                nhap_lieu_chuan = chuan_hoa_dau(nhap_lieu_clean)
                df_app['HoTen_Chuan'] = df_app['HoTen'].apply(chuan_hoa_dau)
                
                matched_by_name = df_app[df_app['HoTen_Chuan'] == nhap_lieu_chuan]
                
                if len(matched_by_name) == 1:
                    target_id = str(matched_by_name.iloc[0]["ID"])
                    st.success(f"✅ Đã tìm thấy: **{matched_by_name.iloc[0]['HoTen']}** (ID: `{target_id}`, {matched_by_name.iloc[0]['Chi']}, Đời {matched_by_name.iloc[0]['DoiThu']})")
                elif len(matched_by_name) > 1:
                    options_dict = {}
                    for _, row in matched_by_name.iterrows():
                        label_opt = f"{row['HoTen']} (ID: {row['ID']} — {row.get('Chi', 'Gốc/Khác')}, Đời {row['DoiThu']})"
                        options_dict[label_opt] = row['ID']
                    
                    with c3:
                        selected_label = st.selectbox("⚠️ Phát hiện trùng tên! Chọn đúng người:", options=list(options_dict.keys()))
                    target_id = options_dict[selected_label]
                else:
                    st.warning(f"❌ Không tìm thấy thành viên nào khớp với từ khóa: '{nhap_lieu_clean}'")

        st.info("📍 **Nguyên lý:** Hệ thống vẽ **một hàng dọc liên tục từ Cụ Thủy Tổ qua các đời Cha, Ông** trực tiếp đi đến ID này, đồng thời **tỏa rộng toàn bộ các nhánh con cháu** bên dưới để ông chủ quan sát rõ ràng chi tiết.")

        if target_id:
            try:
                tree_graph = KyThuatBanVeGiaPha.draw_family_tree(df, target_id=target_id, che_do_xem=che_do_xem)
                KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(tree_graph, chieu_cao=750)
            except Exception as e:
                st.error(f"Lỗi hiển thị sơ đồ: {e}")


# ==============================================================================
# ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
# [ĐIỀU PHỐI ĐẦU NÃO] - KHỞI CHẠY CHƯƠNG TRÌNH
# ==============================================================================

if __name__ == "__main__":
    SoChiHuyGiaoDien.render_app()
