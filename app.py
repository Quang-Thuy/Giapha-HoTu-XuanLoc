# ==============================================================================
# GIA PHẢ ĐIỆN TỬ DÒNG HỌ TỪ XUÂN LỘC
# PHIÊN BẢN CHUẨN CSDL SQLITE - TỐI ƯU HÓA CỘT VỢ/CHỒNG VÀ GHI CHÚ
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
import re
from graphviz import Digraph
from pathlib import Path


# ==============================================================================
# PHÂN KHU 0: TÀI NGUYÊN & QUẢN TRỊ CƠ SỞ DỮ LIỆU SQLITE
# ==============================================================================

class QuanTriTaiNguyen:
    BASE_DIR = Path(__file__).resolve().parent
    DB_FILE = BASE_DIR / "giapha.db"

    CIRCLED_NUMBERS = {
        1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤",
        6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩",
        11: "⑪", 12: "⑫", 13: "⑬", 14: "⑭", 15: "⑮",
        16: "⑯", 17: "⑰", 18: "⑱", 19: "⑲", 20: "⑳", 21: "㉑"
    }

    COLOR_PALETTE = {
        1: "#FFD1D1", 2: "#FFE6CC", 3: "#FFF2CC", 
        4: "#D5E8D4", 5: "#DAE8FC", 6: "#E1D5E7", 
        7: "#FCE5CD", 8: "#D9EAD3", 9: "#FFF2CC",
        10: "#E2F0D9", 11: "#FBE5D6", 12: "#EDEDED"
    }

    @classmethod
    def get_circled_doi(cls, doi_val):
        try:
            return cls.CIRCLED_NUMBERS.get(int(doi_val), f"({doi_val})")
        except:
            return ""

    @staticmethod
    def lay_ten_chinh(ho_ten_day_du):
        ten = str(ho_ten_day_du).strip()
        if not ten or ten == "nan" or ten == "None":
            return ""
        if "(" in ten:
            ten = ten.split("(")[0].strip()
        parts = ten.split()
        return parts[-1] if parts else ten


class KhoDuLieuSQL:
    BASE_DIR = Path(__file__).resolve().parent
    DB_FILE = BASE_DIR / "giapha.db"

    @classmethod
    def get_connection(cls):
        return sqlite3.connect(cls.DB_FILE)

    @classmethod
    def init_database(cls):
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS GiaPha (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ChaID INTEGER,
            HoTen TEXT NOT NULL,
            TenTu TEXT,
            GioiTinh VARCHAR(10),
            DoiThu INTEGER,
            Chi_Nhanh TEXT,
            VoChong TEXT,
            NamSinh VARCHAR(20),
            NamMat VARCHAR(20),
            NgayGio VARCHAR(50),
            ChucDanh_GhiChu TEXT,
            HinhAnh TEXT,
            FOREIGN KEY (ChaID) REFERENCES GiaPha(ID)
        );
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM GiaPha")
        count = cursor.fetchone()[0]
        
        if count == 0:
            raw_data = [
                # -- ĐỜI 1 --
                (1, None, "Từ Dương Đốc", "Huy Cán", "Nam", 1, "Cửa Gốc - Thủy Tổ", "Bà Trần Thị Niêm", "", "", "", "Chi 2 Ất thuộc Đại Tôn di cư lên ở đây. Thầy thuốc y dược tế sinh.", ""),
                
                # -- ĐỜI 2 --
                (2, 1, "Từ Hữu Trí", "", "Nam", 2, "Cửa Giáp - Gốc Giáp", "Bà Đào Thị Điểm", "", "", "", "Đứng đầu cửa Giáp. Làm chức Tri điền. Mộ cồn Nhẳm (Có 12 con: 9 trai 3 gái chết sớm)", ""),
                (3, 1, "Từ Hữu Mưu", "", "Nam", 2, "Cửa Ất - Gốc Ất", "Bà chính Trần Thị Đinh, Bà thứ Trần Thị Đài", "", "", "", "Đứng đầu cửa Ất. Chức Nghĩa Nam. Mộ cồn Chùa Lạch", ""),
                
                # -- ĐỜI 3 --
                (4, 2, "Từ Hữu Liệu", "", "Nam", 3, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Trần Thị Tần", "", "", "", "Trước làm chức Huyện Thừa (Khang Hầu Huyện)", ""),
                (5, 2, "Từ Hữu Dực", "", "Nam", 3, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Ngô Thị Nự Tắc", "", "", "", "", ""),
                (6, 2, "Từ Hữu Lạng", "", "Nam", 3, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà Trần Thị Côn", "", "", "", "Tri điền nội chức, Thí tướng sĩ lạng", ""),
                (7, 3, "Từ Hữu Màn", "", "Nam", 3, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Trần Thị Lụ", "", "", "", "Trước làm thầy thuốc y dược tế sinh", ""),
                (8, 3, "Từ Hữu Hùng", "", "Nam", 3, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Bính", "", "", "", "Trước làm Tri bộ kiêm Xã Trưởng", ""),
                (9, 3, "Từ Hữu Lân", "", "Nam", 3, "Cửa Ất - Chi 6 Ất (Cụ Lân)", "Bà Trần Thị Ảnh", "", "", "", "Trước đi lính đóng Đội Trưởng", ""),
                (10, 3, "Từ Hữu Lạc", "", "Nam", 3, "Cửa Ất - Chi 7 Ất (Cụ Lạc)", "Bà Hỗ Thị Thuần Thục", "", "", "", "Chức Ban cai đội phó cơ Chưởng ngọc hầu", ""),

                # -- ĐỜI 4 --
                (11, 4, "Từ Hữu Di", "", "Nam", 4, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Ngô Thị Tố", "", "", "", "Trước làm nghề thợ rèn", ""),
                (12, 5, "Từ Hữu Kỵ", "", "Nam", 4, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Ngô Thị Lân", "", "", "", "Trước làm Thầy thuốc", ""),
                (13, 5, "Từ Hữu Tương", "", "Nam", 4, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Đào Thị Nanh", "", "", "", "Ưu binh đội trưởng", ""),
                (14, 5, "Từ Hữu Tạc", "", "Nam", 4, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Nguyễn Thị Trân", "", "", "", "Trước làm nghề thợ rèn", ""),
                (15, 5, "Từ Hữu Tỉnh", "", "Nam", 4, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Phi", "", "", "", "Giàu đại phú - Sắc ân Tứ thọ dân, thọ 86 tuổi", ""),
                (16, 5, "Từ Hữu Ẩm", "", "Nam", 4, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Đào Thị Tư, Thứ thất Nguyễn Thị Chiêu", "", "", "", "", ""),
                (17, 6, "Từ Hữu Tình", "", "Nam", 4, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà Ngô Thị Phụng", "", "", "", "", ""),
                (18, 7, "Từ Hữu Hiển", "", "Nam", 4, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Ngô Thị ...", "", "", "", "Hưởng thọ gần 100 tuổi", ""),
                (19, 7, "Từ Hữu Kiều", "", "Nam", 4, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "Chết sớm", ""),
                (20, 7, "Từ Thị Màn", "", "Nữ", 4, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "", ""),
                (21, 8, "Từ Hữu Linh", "", "Nam", 4, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Dương", "", "", "", "", ""),
                (22, 8, "Từ Hữu Cảo", "", "Nam", 4, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Phổ", "", "", "", "Hưởng thọ gần 100 tuổi", ""),
                (23, 8, "Từ Thị Hùng", "", "Nữ", 4, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Không rõ tên", ""),
                (24, 9, "Từ Hữu Niên", "", "Nam", 4, "Cửa Ất - Chi 6 Ất (Cụ Lân)", "Bà Trần Thị Quy", "", "", "", "", ""),
                (25, 9, "Từ Hữu Điền (Điều)", "", "Nam", 4, "Cửa Ất - Chi 6 Ất (Cụ Lân)", "Bà Đặng Thị Thành", "", "", "", "Khâm sai đội lệ", ""),
                (26, 9, "Từ Thị Lân", "", "Nữ", 4, "Cửa Ất - Chi 6 Ất (Cụ Lân)", "", "", "", "", "", ""),
                (27, 10, "Từ Hữu Thận", "", "Nam", 4, "Cửa Ất - Chi 7 Ất (Cụ Lạc)", "Bà Nguyễn Thị Thế", "", "", "", "", ""),
                (28, 10, "Từ Thị Lạc", "", "Nữ", 4, "Cửa Ất - Chi 7 Ất (Cụ Lạc)", "", "", "", "", "", ""),

                # -- ĐỜI 5 --
                (29, 11, "Từ Hữu Loan", "", "Nam", 5, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà chính Thái Thị Thiều, Thứ thất Ngô Thị Thi", "", "", "", "", ""),
                (30, 11, "Từ Hữu Kiều", "", "Nam", 5, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà chính Trần Thị Sum, Bà thứ Nguyễn Thị Trung", "", "", "", "", ""),
                (31, 11, "Từ Hữu Phượng", "", "Nam", 5, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Trần Thị Binh", "", "", "", "", ""),
                (32, 11, "Từ Hữu Điều", "", "Nam", 5, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Nguyễn Thị Thiều", "", "", "", "Phạp tự", ""),
                (33, 11, "Từ Thị Di", "", "Nữ", 5, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (34, 12, "Từ Hữu Tiển", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (35, 12, "Từ Hữu Ngà", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Náo", "", "", "", "Phạp tự", ""),
                (36, 12, "Từ Hữu Lầu", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Đị", "", "", "", "", ""),
                (37, 12, "Từ Thị Kỵ", "", "Nữ", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (38, 13, "Từ Hữu Nghị", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Chói", "", "", "", "", ""),
                (39, 13, "Từ Hữu Vọ", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Nguyễn Thị Sắc", "", "", "", "Phạp tự", ""),
                (40, 13, "Từ Hữu Toàn", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Chẹch", "", "", "", "", ""),
                (41, 13, "Từ Thị Tương", "", "Nữ", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (42, 15, "Từ Hữu Bường", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (43, 15, "Từ Thị Bẹn", "", "Nữ", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Ông Trần Song (giữa làng)", "", "", "", "", ""),
                (44, 15, "Từ Hữu Chấn", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Nguyễn Thị Thuyết", "", "", "", "Mộ táng cồn Hỷ giữa ruộng", ""),
                (45, 15, "Từ Thị Phấn", "", "Nữ", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Ích (giữa làng)", "", "", "", "", ""),
                (46, 15, "Từ Hữu Nhin", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Nguyễn Thị Xuy", "", "", "", "Mộ táng Cồn Trù ghé dăm", ""),
                (47, 16, "Từ Hữu Hưng", "", "Nam", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (48, 16, "Từ Thị Diễn", "", "Nữ", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Người họ Trần (giữa làng)", "", "", "", "", ""),
                (49, 16, "Từ Thị Mày", "", "Nữ", 5, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Người họ Trần (Yên Đồng)", "", "", "", "", ""),
                (50, 17, "Từ Hữu Hồng", "", "Nam", 5, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Thi trúng Nhị trường", ""),
                (51, 17, "Từ Hữu Bằng", "", "Nam", 5, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà chính Trần Thị Nhuần, Bà thứ Nguyễn Thị Kỳ Thỉ", "", "", "", "Trước thông hán, dạy học", ""),
                (52, 17, "Từ Hữu Lập", "", "Nam", 5, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà chính Trần Thị ..., Bà thứ Cố Hậu", "", "", "", "Làm thầy thuốc bắc", ""),
                (53, 17, "Từ Thị Tình", "", "Nữ", 5, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "", ""),
                (54, 18, "Từ Hữu Khảng", "", "Nam", 5, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Trần Thị Thương", "", "", "", "", ""),
                (55, 18, "Từ Hữu Kỳ", "", "Nam", 5, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Nguyễn Thị An", "", "", "", "", ""),
                (56, 18, "Từ Thị Hiển", "", "Nữ", 5, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "", ""),
                (57, 21, "Từ Hữu Tiệt", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Phạp tự", ""),
                (58, 21, "Từ Hữu Quýnh", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Nguyễn Thị Ưu", "", "", "", "", ""),
                (59, 21, "Từ Hữu Linh (con)", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (60, 21, "Từ Thị Linh", "", "Nữ", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (61, 22, "Từ Hữu Trình", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Thập", "", "", "", "", ""),
                (62, 22, "Từ Hữu Tranh", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Khóa", "", "", "", "", ""),
                (63, 22, "Từ Hữu Trừng", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Ngô Thị Duyên", "", "", "", "Phạp tự", ""),
                (64, 22, "Từ Hữu Điêu", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Ngô Thị Khản", "", "", "", "", ""),
                (65, 22, "Từ Hữu Kiên", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Trước làm Phó Tổng", ""),
                (66, 22, "Từ Hữu Cồng", "", "Nam", 5, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Tú", "", "", "", "", ""),
                (67, 27, "Từ Hữu Dinh", "", "Nam", 5, "Cửa Ất - Chi 7 Ất (Cụ Lạc)", "", "", "", "", "Làm nghề dạy chữ Hán. Sinh được 2 con trai, sau đó ông và 1 con trai mất. Còn 1 con trai theo mẹ về quê ngoại ở, đến nay chưa rõ tông tích.", ""),

                # -- ĐỜI 6 --
                (68, 29, "Từ Hữu Thư", "", "Nam", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Ngô Thị Kim", "", "", "", "", ""),
                (69, 29, "Từ Thị Loan", "", "Nữ", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (70, 30, "Từ Hữu Ngạnh", "", "Nam", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Thái Thị Mạnh", "", "", "", "", ""),
                (71, 30, "Từ Thị Kiệu", "", "Nữ", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (72, 31, "Từ Hữu Khánh", "", "Nam", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Nguyễn Thị Lụ", "", "", "", "", ""),
                (73, 31, "Từ Hữu Sum", "", "Nam", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Trần Thị Cơ", "", "", "", "", ""),
                (74, 31, "Từ Hữu Cội", "", "Nam", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Trần Thị Dinh", "", "", "", "", ""),
                (75, 31, "Từ Thị Phượng", "", "Nữ", 6, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Nguyễn Trương Khoa (Yên Đồng)", "", "", "", "", ""),
                (76, 34, "Từ Hữu Toát", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Náo", "", "", "", "", ""),
                (77, 34, "Từ Thị Tiển", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (78, 36, "Từ Hữu Mận", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Lê Thị ...", "", "", "", "", ""),
                (79, 36, "Từ Thị Lầu", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (80, 38, "Từ Thị Huân", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Người họ Nguyễn", "", "", "", "", ""),
                (81, 38, "Từ Thị Nghị", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Người họ Trần", "", "", "", "", ""),
                (82, 40, "Từ Hữu Vẹn", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Diệp", "", "", "", "", ""),
                (83, 40, "Từ Hữu Vẹ", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị La", "", "", "", "Phạp tự", ""),
                (84, 40, "Từ Hữu Cu", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (85, 44, "Từ Thị Mân", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Khoan Trưởng (Đồng Lộc)", "", "", "", "", ""),
                (86, 44, "Từ Thị Hân", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Nguyễn Liêm (giữa làng)", "", "", "", "", ""),
                (87, 44, "Từ Thị Cầm", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Nguyễn Ẩm (Triền Lối)", "", "", "", "", ""),
                (88, 44, "Từ Thị Phú", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Nguyễn Thẩm (giữa làng)", "", "", "", "", ""),
                (89, 44, "Từ Thị Đích", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Bành (Triền Lối)", "", "", "", "", ""),
                (90, 44, "Từ Hữu Đức", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (91, 44, "Từ Thị Túc", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Gả giữa làng - chết sớm", ""),
                (92, 44, "Từ Hữu Đích", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (93, 46, "Từ Thị Tuần", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bang Mỵ (Trạo Nha)", "", "", "", "", ""),
                (94, 46, "Từ Thị Hợi", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Ông Mạo (Hạ Xuân Mai)", "", "", "", "", ""),
                (95, 46, "Từ Thị Thao", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Lê Cớt (giữa làng)", "", "", "", "", ""),
                (96, 46, "Từ Hữu Chính", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Nguyễn Thị Sương", "", "", "", "Trước làm Lý trưởng - thầy thuốc nam, địa lý phù thủy", ""),
                (97, 46, "Từ Thị Năm", "", "Nữ", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Lạc (Yên Đồng)", "", "", "", "", ""),
                (98, 46, "Từ Hữu Giáo", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Thái Thị Thới", "", "", "", "", ""),
                (99, 46, "Từ Hữu Thí", "", "Nam", 6, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Bà Trần Thị Ba", "", "", "", "", ""),
                (100, 50, "Từ Hữu Thống", "", "Nam", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà Trần Thị Cân", "", "", "", "", ""),
                (101, 50, "Từ Hữu Thính", "", "Nam", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "", ""),
                (102, 51, "Từ Thị Điển", "", "Nữ", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Gả về Xã Khố Nội", "", "", "", "", ""),
                (103, 51, "Từ Thị Lại", "", "Nữ", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Lại (giữa làng)", "", "", "", "", ""),
                (104, 51, "Từ Thị Lượng", "", "Nữ", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Cố Lượng Nhạc (Trạo Nha)", "", "", "", "", ""),
                (105, 51, "Từ Thị Lạp", "", "Nữ", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Bách (giữa làng)", "", "", "", "", ""),
                (106, 51, "Từ Hữu Bối", "", "Nam", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà Ngô Thị Chút", "", "", "", "", ""),
                (107, 51, "Từ Hữu Triết", "", "Nam", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Lấy chồng khác", "", "", "", "", ""),
                (108, 51, "Từ Thị Đại Lộc", "", "Nữ", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Người Đại Lộc", "", "", "", "", ""),
                (109, 52, "Từ Hữu Quán", "", "Nam", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà Trần Thị Tuy", "", "", "", "", ""),
                (110, 52, "Từ Thị Lập", "", "Nữ", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Ông Cu Hậu (Yên Đồng)", "", "", "", "", ""),
                (111, 52, "Từ Hữu Xán", "", "Nam", 6, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Bà Nguyễn Thị Suất", "", "", "", "", ""),
                (112, 55, "Từ Hữu Hòe", "", "Nam", 6, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Trần Thị Cát", "", "", "", "Phạp tự", ""),
                (113, 55, "Từ Hữu Trấn", "", "Nam", 6, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Trần Thị Tình", "", "", "", "Quyền Suất đội – Sắc phong Phó Đô đốc", ""),
                (114, 55, "Từ Hữu Ắt", "", "Nam", 6, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Trần Thị Thưởng", "", "", "", "", ""),
                (115, 55, "Từ Hữu Dự", "", "Nam", 6, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Bà Nguyễn Thị Tòng, Nguyễn Thị Sáu", "", "", "", "Phạp tự", ""),
                (116, 55, "Từ Thị Kỳ", "", "Nữ", 6, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "", ""),
                (117, 58, "Từ Hữu Thạch", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Nguyễn Thị Thẩm", "", "", "", "Di cư ra Hoàng Mai - Nghệ An ở, tông tích không rõ", ""),
                (118, 58, "Từ Thị Quýnh", "", "Nữ", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (119, 61, "Từ Hữu Lục", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Khanh", "", "", "", "", ""),
                (120, 61, "Từ Hữu Tùy", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Trúc", "", "", "", "", ""),
                (121, 61, "Từ Thị Trình", "", "Nữ", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (122, 62, "Từ Hữu Do", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Ngô Thị Đị", "", "", "", "", ""),
                (123, 62, "Từ Thị Tranh", "", "Nữ", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (124, 64, "Từ Hữu Chuyên", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Nguyên", "", "", "", "", ""),
                (125, 64, "Từ Hữu Chuân", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Quynh", "", "", "", "", ""),
                (126, 64, "Từ Thị Điêu", "", "Nữ", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (127, 65, "Từ Hữu Huân", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Bôi", "", "", "", "Trước làm Lý trưởng", ""),
                (128, 65, "Từ Hữu Giảng", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Quán", "", "", "", "", ""),
                (129, 65, "Từ Hữu Điển", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Thái Thị Lương", "", "", "", "", ""),
                (130, 65, "Từ Thị Kiên", "", "Nữ", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (131, 66, "Từ Hữu Bồng", "", "Nam", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Bà Trần Thị Ít", "", "", "", "Di cư đi đâu không rõ", ""),
                (132, 66, "Từ Thị Cồng", "", "Nữ", 6, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),

                # -- ĐỜI 7 --
                (133, 68, "Từ Hữu Phiệt", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà cả Trần Thị Hán, Bà thứ Trần Thị Thỏa", "", "", "25/07 AL", "Làm Lý trưởng, mất 25/7 âm lịch", ""),
                (134, 68, "Từ Thị Cớt", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Cớt (giữa làng)", "", "", "", "", ""),
                (135, 68, "Từ Thị Chước", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Chước (giữa làng)", "", "", "", "", ""),
                (136, 70, "Từ Hữu Lâm", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Bà Trần Thị Nhỏ", "", "", "", "", ""),
                (137, 70, "Từ Hữu Tâm", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (138, 72, "Từ Hữu Sáng", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (139, 72, "Từ Hữu Xích", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (140, 72, "Từ Thị Hiến", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Cố Chắt Hiến (Thạch Liên)", "", "", "", "", ""),
                (141, 73, "Từ Hữu Toại", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (142, 73, "Từ Thị Sị", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Cố Sị (giữa làng)", "", "", "", "", ""),
                (143, 73, "Từ Hữu Nghị", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (144, 73, "Từ Thị Thuyên", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Thuyên (giữa làng)", "", "", "", "", ""),
                (145, 73, "Từ Thị Liêu", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Liêu (giữa làng)", "", "", "", "", ""),
                (146, 73, "Từ Thị Hành", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Cửu Tường (Triền Lối)", "", "", "", "", ""),
                (147, 73, "Từ Thị Yến", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Yến (Trúc Lạng)", "", "", "", "", ""),
                (148, 73, "Từ Hữu Luân", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (149, 74, "Từ Thị Lệ", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Đinh (giữa làng)", "", "", "", "", ""),
                (150, 74, "Từ Hữu Lê", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (151, 74, "Từ Thị Thảng", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Thảng (giữa làng)", "", "", "", "", ""),
                (152, 74, "Từ Hữu Nghĩa", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (153, 74, "Từ Thị Cầu", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Thầy Cầu (Triền Lối)", "", "", "", "", ""),
                (154, 74, "Từ Hữu Khí", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (155, 74, "Từ Hữu Tề", "", "Nam", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (156, 74, "Từ Thị Tám", "", "Nữ", 7, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Trần Hoan (giữa làng)", "", "", "", "", ""),
                (157, 76, "Từ Hữu Duyệt", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (158, 76, "Từ Hữu Hợi", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (159, 76, "Từ Thị Thế", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Thế (giữa làng)", "", "", "", "", ""),
                (160, 78, "Từ Thị Mai", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Chinh (giữa làng)", "", "", "", "", ""),
                (161, 78, "Từ Hữu Khai", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (162, 78, "Từ Hữu Lai", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (163, 82, "Từ Hữu Kiệp", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (164, 82, "Từ Hữu Điệp", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (165, 82, "Từ Thị Ba", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Thạch Liên", "", "", "", "", ""),
                (166, 82, "Từ Thị Chút", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Tuần Dư Nại", "", "", "", "", ""),
                (167, 82, "Từ Hữu Đửu", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (168, 82, "Từ Thị Tỷ", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Ông Long (Tiến Lộc)", "", "", "", "", ""),
                (169, 83, "Từ Thị Vẹ", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Mất sớm (Cụ Vẹ phạp tự)", ""),
                (170, 96, "Từ Quang Diệu", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Cán bộ Xã - Huyện - Khu 4", ""),
                (171, 96, "Từ Quang Bút", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Liệt sĩ chống Pháp", ""),
                (172, 96, "Từ Thị Tam", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Khởi (giữa làng)", "", "", "", "", ""),
                (173, 96, "Từ Thị Tứ", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (174, 96, "Từ Thị Chút", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (175, 96, "Từ Thị Hảo", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Bình (giữa làng)", "", "", "", "", ""),
                (176, 96, "Từ Quang Phú (Sơn)", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Cán bộ hợp tác xã", ""),
                (177, 96, "Từ Thị Tám", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Nguyễn Long (giữa làng)", "", "", "", "", ""),
                (178, 96, "Từ Thị Chín", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Ông Nhân (giữa làng)", "", "", "", "", ""),
                (179, 96, "Từ Thị Mười", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Tảo vong", ""),
                (180, 98, "Từ Thị Chắt", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Trần Minh (Quang Lộc)", "", "", "", "", ""),
                (181, 98, "Từ Thị Con", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Nguyễn Thủy (Điền Xá)", "", "", "", "", ""),
                (182, 98, "Từ Hữu Huấn", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (183, 98, "Từ Hữu Chuột", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "", ""),
                (184, 98, "Từ Hữu Xưng", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết lúc 15 tuổi", ""),
                (185, 99, "Từ Hữu Thiện", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Giáo viên cấp 1", ""),
                (186, 99, "Từ Hữu Nuôi", "", "Nam", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "", "", "", "", "Chết sớm", ""),
                (187, 99, "Từ Thị Tỷ", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Ông Sinh (Đức Thọ)", "", "", "", "", ""),
                (188, 99, "Từ Thị Quyền", "", "Nữ", 7, "Cửa Giáp - Chi 2 Giáp (Cụ Dực)", "Ông Tuế (Thạch Ngọc)", "", "", "", "", ""),
                (189, 100, "Từ Thị Đồng Lộc", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Đồng Lộc", "", "", "", "", ""),
                (190, 100, "Từ Thị Yên Đồng", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Yên Đồng", "", "", "", "", ""),
                (191, 101, "Từ Thị Phiếm", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Phiếm (giữa làng)", "", "", "", "", ""),
                (192, 101, "Từ Hữu Mục", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "", ""),
                (193, 101, "Từ Hữu Khoa", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Không có vợ con", ""),
                (194, 106, "Từ Thị Mày", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Chết sớm", ""),
                (195, 106, "Từ Hữu Mậu", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "", ""),
                (196, 106, "Từ Thị Cháu", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Chết sớm", ""),
                (197, 107, "Từ Thị Chày", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Lấy ai ở đâu không rõ", ""),
                (198, 107, "Từ Hữu Cược", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Tảo vong", ""),
                (199, 107, "Từ Hữu Quằt", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Tảo vong", ""),
                (200, 107, "Từ Hữu Cháu", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Chết sớm", ""),
                (201, 109, "Từ Thị Khoách", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Nguyễn Thiền (giữa làng)", "", "", "", "", ""),
                (202, 109, "Từ Thị Hai", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Nguyễn Điểm (giữa làng)", "", "", "", "", ""),
                (203, 109, "Từ Thị Chự", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Ông Liêu (Kỳ Mòi)", "", "", "", "", ""),
                (204, 109, "Từ Thị Em Nậy", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Tuệ (giữa làng)", "", "", "", "", ""),
                (205, 109, "Từ Thị Em Con", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Bệ (giữa làng)", "", "", "", "", ""),
                (206, 109, "Từ Hữu Trù", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "", ""),
                (207, 109, "Từ Thị Chút", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Bản (giữa làng)", "", "", "", "", ""),
                (208, 109, "Từ Thị Tám", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Trần Dê (giữa làng)", "", "", "", "", ""),
                (209, 111, "Từ Thị Bẹn", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Đã lấy chồng, chết sớm", ""),
                (210, 111, "Từ Thị Em", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "Ông Bút (Yên Đồng)", "", "", "", "", ""),
                (211, 111, "Từ Thị Tam", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Chết đuối", ""),
                (212, 111, "Từ Thị Tứ", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Chết sớm", ""),
                (213, 111, "Từ Hữu Năm", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Bộ đội chống Pháp, kỹ sư điện (Từ Hoa Việt)", ""),
                (214, 111, "Từ Hữu Lục (Quang)", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Mất 1988 (Quang, Thuận, Bút)", ""),
                (215, 111, "Từ Thị Bảy", "", "Nữ", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "Tảo vong", ""),
                (216, 111, "Từ Hữu Tám", "", "Nam", 7, "Cửa Giáp - Chi 3 Giáp (Cụ Lạng)", "", "", "", "", "", ""),
                (217, 113, "Từ Hữu Bạt", "", "Nam", 7, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "Hương thợ làng", ""),
                (218, 113, "Từ Hữu Nhiếp", "", "Nam", 7, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "Sãi chùa, cán bộ phong trào 1930", ""),
                (219, 113, "Từ Thị Đị", "", "Nữ", 7, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Trần Hoàng (giữa làng)", "", "", "", "", ""),
                (220, 114, "Từ Hữu Xỷ", "", "Nam", 7, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "", ""),
                (221, 114, "Từ Hữu Dỵ", "", "Nam", 7, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "", "", "", "", "", ""),
                (222, 114, "Từ Thị Em", "", "Nữ", 7, "Cửa Ất - Chi 4 Ất (Cụ Màn)", "Trần Ninh (giữa làng)", "", "", "", "", ""),
                (223, 119, "Từ Hữu Đỏ", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (224, 119, "Từ Thị Tần", "", "Nữ", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (225, 119, "Từ Thị Đức", "", "Nữ", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Chết", ""),
                (226, 120, "Từ Hữu Hoài", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (227, 120, "Từ Thị Láng", "", "Nữ", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Ông Láng (giữa làng)", "", "", "", "", ""),
                (228, 122, "Từ Hữu Nha", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Nghề da, thợ mộc, thợ may", ""),
                (229, 122, "Từ Thị Do", "", "Nữ", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (230, 124, "Từ Hữu Trại", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (231, 125, "Từ Hữu Nhạc", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Dạy Hán, thầy thuốc, địa lý", ""),
                (232, 125, "Từ Thị Mặc", "", "Nữ", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Nguyễn Viễn (giữa làng)", "", "", "", "", ""),
                (233, 127, "Từ Hữu Vi", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Thợ mộc", ""),
                (234, 127, "Từ Hữu Lâu (Ất)", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (235, 127, "Từ Hữu Ứng", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "Sắc phong Chánh bát phẩm, Đội trưởng", ""),
                (236, 127, "Từ Thị Mục Lung", "", "Nữ", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "Mục Lung (giữa làng)", "", "", "", "", ""),
                (237, 128, "Từ Hữu Lai (Giảng)", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (238, 128, "Từ Hữu Lưu", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),
                (239, 129, "Từ Hữu Kẹo", "", "Nam", 7, "Cửa Ất - Chi 5 Ất (Cụ Hùng)", "", "", "", "", "", ""),

                # -- ĐỜI 8 --
                (240, 133, "Từ Hữu Diệt", "", "Nam", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (241, 133, "Từ Hữu Việt", "", "Nam", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (242, 133, "Từ Thị Điệng", "", "Nữ", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Ông Điệng, Cửu Bẹn", "", "", "", "", ""),
                (243, 133, "Từ Hữu Huyền (Năm)", "", "Nam", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (244, 133, "Từ Thị Ba Điêm", "", "Nữ", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Ba Điêm (giữa làng)", "", "", "", "", ""),
                (245, 136, "Từ Thị Mực", "", "Nữ", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "Cu Láng (giữa làng)", "", "", "", "", ""),
                (246, 136, "Từ Thị Ba", "", "Nữ", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "Lấy 3 chồng", ""),
                (247, 136, "Từ Hữu Đồng", "", "Nam", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (248, 136, "Từ Hữu Kê", "", "Nam", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "", ""),
                (249, 136, "Từ Thị Chút", "", "Nữ", 8, "Cửa Giáp - Chi 1 Giáp (Cụ Liệu)", "", "", "", "", "Chết sớm", "")
            ]
            
            insert_query = """
            INSERT INTO GiaPha (
                ID, ChaID, HoTen, TenTu, GioiTinh, DoiThu, 
                Chi_Nhanh, VoChong, NamSinh, NamMat, NgayGio, 
                ChucDanh_GhiChu, HinhAnh
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.executemany(insert_query, raw_data)
            conn.commit()
            
        conn.close()

    @classmethod
    def load_data(cls):
        cls.init_database()
        conn = cls.get_connection()
        query = """
        SELECT 
            ID, 
            COALESCE(ChaID, 0) AS ChaMe_ID, 
            HoTen, 
            TenTu,
            GioiTinh, 
            DoiThu, 
            Chi_Nhanh, 
            VoChong, 
            NamSinh,
            NamMat,
            NgayGio,
            ChucDanh_GhiChu AS GhiChu, 
            HinhAnh
        FROM GiaPha
        """
        df = pd.read_sql_query(query, conn).fillna("")
        conn.close()
        
        def parse_cua(val):
            if "Cửa Giáp" in val or "Gốc Giáp" in val:
                return "Giáp"
            elif "Cửa Ất" in val or "Gốc Ất" in val:
                return "Ất"
            return "Gốc"

        def parse_chi(val):
            if " - " in val:
                return val.split(" - ", 1)[1].strip()
            return val

        df["Cua"] = df["Chi_Nhanh"].apply(parse_cua)
        df["Chi"] = df["Chi_Nhanh"].apply(parse_chi)
        df["TrangThai"] = "Đã duyệt"
        return df

    @classmethod
    def insert_member(cls, ho_ten, ten_tu, gioi_tinh, doi_thu, cua, chi, cha_id, vo_chong, nam_sinh, nam_mat, ngay_gio, ghi_chu, hinh_anh):
        cls.init_database()
        conn = cls.get_connection()
        cursor = conn.cursor()
        cha_id_val = None if cha_id == 0 else cha_id
        chi_nhanh_val = f"Cửa {cua} - {chi}"

        query = """
        INSERT INTO GiaPha (
            ChaID, HoTen, TenTu, GioiTinh, DoiThu, Chi_Nhanh, VoChong, 
            NamSinh, NamMat, NgayGio, ChucDanh_GhiChu, HinhAnh
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (
            cha_id_val, ho_ten, ten_tu, gioi_tinh, doi_thu, chi_nhanh_val, 
            vo_chong, nam_sinh, nam_mat, ngay_gio, ghi_chu, hinh_anh
        ))
        conn.commit()
        conn.close()

    @classmethod
    def approve_member(cls, member_id):
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE GiaPha SET TrangThai = 'Đã duyệt' WHERE ID = ?", (member_id,))
        conn.commit()
        conn.close()

    @classmethod
    def delete_member(cls, member_id):
        conn = cls.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM GiaPha WHERE ID = ?", (member_id,))
        conn.commit()
        conn.close()


# ==============================================================================
# PHÂN KHU A: BỘ LÕI BẢN VẼ & ZOOM TƯƠNG TÁC ĐA ĐIỂM
# ==============================================================================

class KyThuatBanVeGiaPha:
    @staticmethod
    def get_ancestors_chain(df_data, focus_id):
        chain = []
        try:
            curr_id = int(focus_id)
        except:
            return chain

        visited = set()
        while curr_id != 0 and curr_id not in visited:
            visited.add(curr_id)
            row = df_data[df_data["ID"] == curr_id]
            if row.empty:
                break
            chain.insert(0, row.iloc[0].to_dict())
            try:
                curr_id = int(row.iloc[0].get("ChaMe_ID", 0))
            except:
                break
        return chain

    @staticmethod
    def tao_nhan_ton_kinh(member):
        doi_num = int(member.get('DoiThu', 1))
        doi_khoanh = QuanTriTaiNguyen.get_circled_doi(doi_num)
        ho_ten = str(member.get('HoTen', '')).strip()
        ten_tu = str(member.get('TenTu', '')).strip()
        cua = str(member.get('Cua', ''))
        chi = str(member.get('Chi', ''))
        
        if doi_num == 1:
            hien_tu = f" (Tự: {ten_tu})" if ten_tu else " (Tự: Huy Cán)"
            return f"Từ Dương Đốc {doi_khoanh}\n(Thủy Tổ{hien_tu})"
        elif doi_num == 2:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            return f"{ten_rut_gon} {doi_khoanh}\n(Đứng đầu Cửa {cua})"
        elif doi_num == 3:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            ten_chi = chi.split("(")[0].strip() if "(" in chi else chi
            return f"{ten_rut_gon} {doi_khoanh}\n({ten_chi})"
        else:
            ten_rut_gon = ho_ten.split("(")[0].strip()
            return f"{ten_rut_gon} {doi_khoanh}"

    @classmethod
    def draw_focus_tree(cls, df_data, focus_id):
        dot = Digraph(
            comment='Focus Tree', 
            node_attr={'shape': 'box', 'style': 'filled,rounded', 'fontname': 'Arial', 'fontsize': '11'}
        )
        dot.attr(rankdir='TB', size='14,10')

        ancestor_chain = cls.get_ancestors_chain(df_data, focus_id)
        if not ancestor_chain:
            return dot

        prev_node_id = None
        for member in ancestor_chain:
            m_id = str(member['ID'])
            doi_num = int(member['DoiThu']) if str(member['DoiThu']).isdigit() else 1
            is_focus = (member['ID'] == int(focus_id))
            
            label = cls.tao_nhan_ton_kinh(member)
            fill = "#FFE082" if is_focus else QuanTriTaiNguyen.COLOR_PALETTE.get(doi_num, "#FFFFFF")
            border_color = "#C62828" if is_focus else "#455A64"
            pen_width = "2.8" if is_focus else "1.5"
            
            dot.node(m_id, label, fillcolor=fill, color=border_color, penwidth=pen_width)
            
            if prev_node_id:
                dot.edge(prev_node_id, m_id, color="#C62828" if is_focus else "#37474F", penwidth="2.2" if is_focus else "1.3")
            prev_node_id = m_id

        children = df_data[(df_data["ChaMe_ID"] == int(focus_id)) & (df_data["TrangThai"] == "Đã duyệt")]
        for _, child in children.iterrows():
            c_id = str(child['ID'])
            c_ten = QuanTriTaiNguyen.lay_ten_chinh(child['HoTen'])
            c_doi_num = int(child['DoiThu']) if str(child['DoiThu']).isdigit() else 8
            c_doi_khoanh = QuanTriTaiNguyen.get_circled_doi(c_doi_num)
            gioi_tinh = str(child.get('GioiTinh', 'Nam'))
            
            c_label = f"{c_ten} {c_doi_khoanh}"
            c_fill = "#FFF0F5" if gioi_tinh == "Nữ" else QuanTriTaiNguyen.COLOR_PALETTE.get(c_doi_num, "#E8F5E9")
            c_shape = "ellipse" if gioi_tinh == "Nữ" else "box"
            
            dot.node(c_id, c_label, fillcolor=c_fill, color="#2E7D32", shape=c_shape, style="filled,dashed", penwidth="1.2")
            dot.edge(str(focus_id), c_id, color="#2E7D32", penwidth="1.5")
            
        return dot

    @classmethod
    def draw_family_tree(cls, df_data, cua_loc="Tất cả", chi_loc="Tất cả", che_do_xem="1. Chỉ Đinh Nam (Gọn: Tên ⑦)"):
        dot = Digraph(
            comment='Gia Phả Toàn Cảnh', 
            node_attr={'style': 'filled,rounded', 'fontname': 'Arial', 'fontsize': '10'}
        )
        dot.attr(rankdir='TB', size='16,12', splines='polyline')
        
        df_approved = df_data[df_data["TrangThai"] == "Đã duyệt"].copy()
        
        if cua_loc != "Tất cả":
            df_draw = df_approved[(df_approved["Cua"] == cua_loc) | (df_approved["ID"] == 1)].copy()
        else:
            df_draw = df_approved.copy()
            
        if chi_loc != "Tất cả":
            branch_members = df_approved[df_approved["Chi"] == chi_loc]
            valid_ids = set(branch_members["ID"].tolist())
            for p_id in branch_members["ChaMe_ID"]:
                curr = int(p_id) if str(p_id).isdigit() else 0
                while curr != 0:
                    valid_ids.add(curr)
                    parent_row = df_approved[df_approved["ID"] == curr]
                    if parent_row.empty:
                        break
                    curr = int(parent_row.iloc[0].get("ChaMe_ID", 0)) if str(parent_row.iloc[0].get("ChaMe_ID", 0)).isdigit() else 0
            df_draw = df_approved[df_approved["ID"].isin(valid_ids)].copy()

        if "Chỉ Đinh Nam" in che_do_xem:
            df_draw = df_draw[df_draw["GioiTinh"] == "Nam"]

        ids_in_graph = set(df_draw['ID'].tolist())

        for _, row in df_draw.iterrows():
            node_id = str(row['ID'])
            ho_ten = str(row.get('HoTen', '')).strip()
            ten_tu = str(row.get('TenTu', '')).strip()
            doi_num = int(row['DoiThu']) if str(row['DoiThu']).isdigit() else 1
            doi_khoanh = QuanTriTaiNguyen.get_circled_doi(doi_num)
            gioi_tinh = str(row.get('GioiTinh', 'Nam')).strip()
            cua = str(row.get('Cua', '')).strip()
            chi = str(row.get('Chi', '')).strip()
            
            vo_val = str(row.get('VoChong', '')).strip()
            chuc_val = str(row.get('GhiChu', '')).strip()
            ngay_gio = str(row.get('NgayGio', '')).strip()
            
            if che_do_xem == "1. Chỉ Đinh Nam (Gọn: Tên ⑦)":
                if doi_num == 1:
                    hien_tu = f" (Tự: {ten_tu})" if ten_tu else " (Tự: Huy Cán)"
                    label = f"Từ Dương Đốc {doi_khoanh}\n(Thủy Tổ{hien_tu})"
                elif doi_num == 2:
                    label = f"{ho_ten} {doi_khoanh}\n(Đứng đầu Cửa {cua})"
                elif doi_num == 3:
                    ten_chi = chi.split("(")[0].strip() if "(" in chi else chi
                    label = f"{ho_ten} {doi_khoanh}\n({ten_chi})"
                else:
                    label = f"{ho_ten} {doi_khoanh}"
                
            elif che_do_xem == "2. Chỉ Đinh Nam (Chi tiết)":
                parts = [f"{ho_ten} {doi_khoanh}"]
                if ten_tu:
                    parts.append(f"[Tự: {ten_tu}]")
                if ngay_gio:
                    parts.append(f"Giỗ: {ngay_gio}")
                if chuc_val and chuc_val != "nan":
                    parts.append(f"({chuc_val})")
                label = "\n".join(parts)
                
            elif che_do_xem == "3. Cả Nam & Nữ (Đầy đủ cả Vợ & Con gái)":
                parts = [f"{ho_ten} {doi_khoanh}"]
                if vo_val and vo_val != "nan":
                    prefix = "Bà" if gioi_tinh == "Nam" else "Chồng"
                    parts.append(f"[{prefix}: {vo_val}]")
                if ngay_gio:
                    parts.append(f"Giỗ: {ngay_gio}")
                if chuc_val and chuc_val != "nan":
                    parts.append(f"({chuc_val})")
                label = "\n".join(parts)
                
            elif che_do_xem == "4. Cả Nam & Nữ (Ẩn Vợ, chỉ hiện Con gái)":
                parts = [f"{ho_ten} {doi_khoanh}"]
                if gioi_tinh == "Nữ" and vo_val and vo_val != "nan":
                    parts.append(f"[Chồng: {vo_val}]")
                if ngay_gio:
                    parts.append(f"Giỗ: {ngay_gio}")
                if chuc_val and chuc_val != "nan":
                    parts.append(f"({chuc_val})")
                label = "\n".join(parts)
            else:
                label = f"{ho_ten} {doi_khoanh}"
            
            if gioi_tinh == "Nữ":
                fill = "#FFF0F5"
                shape = "ellipse"
                color = "#D81B60"
            else:
                fill = QuanTriTaiNguyen.COLOR_PALETTE.get(doi_num, "#FFFFFF")
                shape = "box"
                color = "#455A64"
            
            dot.node(node_id, label, fillcolor=fill, shape=shape, color=color, penwidth="1.2")

        for _, row in df_draw.iterrows():
            node_id = str(row['ID'])
            curr_parent = row.get('ChaMe_ID', 0)
            
            while curr_parent != 0 and int(curr_parent) not in ids_in_graph:
                parent_row = df_approved[df_approved["ID"] == int(curr_parent)]
                if parent_row.empty:
                    break
                curr_parent = parent_row.iloc[0].get("ChaMe_ID", 0)
                
            if curr_parent != 0 and int(curr_parent) in ids_in_graph:
                dot.edge(str(curr_parent), node_id, color="#546E7A", penwidth="1.0")
                
        return dot


    @classmethod
    def hien_thi_so_do_tuong_tac(cls, dot_graph, chieu_cao=620):
        try:
            svg_data = dot_graph.pipe(format="svg").decode("utf-8")
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
                <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
                <style>
                    html, body {{
                        margin: 0; padding: 0; width: 100%; height: 100%;
                        background-color: transparent; overflow: hidden;
                    }}
                    #container-giapha {{
                        width: 100%; height: {chieu_cao}px;
                        border: 1.5px solid #CFD8DC; border-radius: 10px;
                        background: #FDFEFE; box-shadow: inset 0 0 8px rgba(0,0,0,0.03);
                        position: relative;
                        touch-action: none;
                    }}
                    /* Ép cả thẻ SVG bên trong nhận diện cảm ứng 2 ngón tay */
                    #container-giapha svg {{ 
                        width: 100%; 
                        height: 100%; 
                        touch-action: none;
                    }}
                    
                    /* Thanh công cụ zoom nằm gọn ở góc trên bên trái */
                    .custom-zoom-controls {{
                        position: absolute;
                        top: 12px;
                        left: 12px;
                        z-index: 999;
                        display: flex;
                        flex-direction: row;
                        gap: 6px;
                    }}
                    .custom-zoom-controls button {{
                        width: 36px;
                        height: 36px;
                        background-color: #ffffff;
                        color: #333333;
                        border: 1px solid #B0BEC5;
                        border-radius: 6px;
                        font-size: 18px;
                        font-weight: bold;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .custom-zoom-controls button:active {{
                        background-color: #ECEFF1;
                    }}
                </style>
            </head>
            <body>
                <div id="container-giapha">
                    <div class="custom-zoom-controls">
                        <button onclick="zoomIn()" title="Phóng to">+</button>
                        <button onclick="zoomOut()" title="Thu nhỏ">-</button>
                        <button onclick="resetZoom()" title="Đặt lại" style="font-size: 14px;">⟳</button>
                    </div>
                    {svg_data}
                </div>
                <script>
                    var panZoomInstance = null;
                    window.onload = function() {{
                        var svgElement = document.querySelector('#container-giapha svg');
                        if (svgElement) {{
                            svgElement.setAttribute('id', 'svg-zoom-target');
                            panZoomInstance = svgPanZoom('#svg-svg-zoom-target' || '#svg-zoom-target', {{
                                zoomEnabled: true,
                                controlIconsEnabled: false, // Bắt buộc tắt hoàn toàn nút mặc định
                                fit: true,
                                center: true,
                                minZoom: 0.1,
                                maxZoom: 25,
                                zoomScaleSensitivity: 0.25,
                                dblClickZoomEnabled: true,
                                mouseWheelZoomEnabled: true,
                                preventMouseEventsDefault: true
                            }});
                        }}
                    }};
                    
                    function zoomIn() {{
                        if (panZoomInstance) panZoomInstance.zoomIn();
                    }}
                    function zoomOut() {{
                        if (panZoomInstance) panZoomInstance.zoomOut();
                    }}
                    function resetZoom() {{
                        if (panZoomInstance) {{
                            panZoomInstance.resetZoom();
                            panZoomInstance.center();
                        }}
                    }}
                </script>
            </body>
            </html>
            """
            components.html(html_content, height=chieu_cao + 10)
        except Exception:
            st.graphviz_chart(dot_graph, use_container_width=True)



# ==============================================================================
# PHÂN KHU B: SỞ CHỈ HUY GIAO DIỆN & THAO TÁC
# ==============================================================================

class SoChiHuyGiaoDien:
    @staticmethod
    def thiet_lap_giao_dien():
        st.set_page_config(page_title="Gia phả điện tử dòng Họ Từ Xuân Lộc", page_icon="📜", layout="wide")
        st.markdown("""
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
            <style>
                .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
                .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; margin-bottom: 5px; }
                h1 { font-size: 1.8rem !important; }
                h2, h3 { font-size: 1.3rem !important; }
                .hd-zoom { font-size: 0.85rem; color: #546E7A; margin-bottom: 8px; }
            </style>
        """, unsafe_allow_html=True)

    @classmethod
    def render_app(cls):
        cls.thiet_lap_giao_dien()
        
        df = KhoDuLieuSQL.load_data()

        st.title("📜 Gia phả điện tử dòng Họ Từ Xuân Lộc")
        st.caption("Hệ thống quản lý phả hệ chuẩn mực — Cơ sở dữ liệu SQLite tối ưu đa thiết bị")

        if "focus_id" not in st.session_state:
            st.session_state.focus_id = 133 if 133 in df["ID"].values else 1

        menu = st.sidebar.radio("CHỌN CHỨC NĂNG:", [
            "🎯 Cây Thám Hiểm Trực Hệ (Dễ xem nhất)",
            "🌳 Xem Cây Toàn Bộ / Từng Chi", 
            "🔍 Tra cứu theo Chi/Ngành", 
            "✍️ Đề xuất thành viên mới", 
            "🛡️ Quản trị & Phê duyệt"
        ])

        # --- HỒI 1: CÂY THÁM HIỂM TRỰC HỆ ---
        if menu == "🎯 Cây Thám Hiểm Trực Hệ (Dễ xem nhất)":
            st.subheader("🎯 Tuyến Phả Hệ Trọng Tâm")
            
            chain = KyThuatBanVeGiaPha.get_ancestors_chain(df, st.session_state.focus_id)
            breadcrumb_str = " ➔ ".join([f"**{QuanTriTaiNguyen.lay_ten_chinh(c['HoTen'])} {QuanTriTaiNguyen.get_circled_doi(c['DoiThu'])}**" for c in chain])
            st.info(f"📍 **Đường dẫn cội nguồn:** {breadcrumb_str}")

            col_tree, col_nav = st.columns([2, 1])
            
            with col_tree:
                st.markdown("<div class='hd-zoom'>💡 <b>Trên điện thoại:</b> Dùng 2 ngón tay chạm để phóng to/thu nhỏ hoặc bấm nút <b>(+ / -)</b> ở góc sơ đồ.</div>", unsafe_allow_html=True)
                try:
                    focus_graph = KyThuatBanVeGiaPha.draw_focus_tree(df, st.session_state.focus_id)
                    KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(focus_graph, chieu_cao=580)
                except Exception as e:
                    st.error(f"Lỗi hiển thị sơ đồ: {e}")

            with col_nav:
                curr_person = df[df["ID"] == st.session_state.focus_id].iloc[0]
                ten_tu_txt = f" (Tự: {curr_person['TenTu']})" if curr_person['TenTu'] else ""
                st.markdown(f"### 👤 Cụ: **{curr_person['HoTen']}{ten_tu_txt} {QuanTriTaiNguyen.get_circled_doi(curr_person['DoiThu'])}**")
                st.write(f"- **Thuộc:** Cửa {curr_person['Cua']} — {curr_person['Chi']}")
                
                if curr_person['VoChong']:
                    nhan_hon_phoi = "Bà" if curr_person.get("GioiTinh") == "Nam" else "Chồng"
                    st.write(f"- **{nhan_hon_phoi}:** {curr_person['VoChong']}")
                if curr_person['NgayGio']:
                    st.write(f"- **Ngày giỗ:** {curr_person['NgayGio']}")
                if curr_person['NamSinh'] or curr_person['NamMat']:
                    st.write(f"- **Năm sinh/mất:** {curr_person['NamSinh']} - {curr_person['NamMat']}")
                if curr_person['GhiChu']:
                    st.write(f"- **Ghi chú/Chức danh:** {curr_person['GhiChu']}")

                st.markdown("---")
                children = df[(df["ChaMe_ID"] == st.session_state.focus_id) & (df["TrangThai"] == "Đã duyệt")]
                
                if not children.empty:
                    st.markdown(f"**👉 Bấm chọn người con (Đời {int(curr_person['DoiThu'])+1}) để mở tiếp:**")
                    for _, ch in children.iterrows():
                        btn_label = f"Mở nhánh: {QuanTriTaiNguyen.lay_ten_chinh(ch['HoTen'])} {QuanTriTaiNguyen.get_circled_doi(ch['DoiThu'])}"
                        if st.button(btn_label, key=f"btn_child_{ch['ID']}"):
                            st.session_state.focus_id = ch['ID']
                            st.rerun()
                else:
                    st.warning("Nhánh này hiện chưa cập nhật con cháu đời kế tiếp.")
                    
                st.markdown("---")
                if int(curr_person.get("ChaMe_ID", 0)) != 0:
                    if st.button("⬅️ Quay lại đời trước (Cha)"):
                        st.session_state.focus_id = int(curr_person["ChaMe_ID"])
                        st.rerun()
                if st.button("🔄 Về gốc Cụ Thủy Tổ ①"):
                    st.session_state.focus_id = 1
                    st.rerun()

        # --- HỒI 2: XEM CÂY TOÀN BỘ / TỪNG CHI ---
        elif menu == "🌳 Xem Cây Toàn Bộ / Từng Chi":
            st.subheader("Sơ Đồ Phả Hệ Toàn Cảnh")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                che_do_xem = st.selectbox(
                    "1. Chế độ hiển thị:", 
                    [
                        "1. Chỉ Đinh Nam (Gọn: Tên ⑦)",
                        "2. Chỉ Đinh Nam (Chi tiết)",
                        "3. Cả Nam & Nữ (Đầy đủ cả Vợ & Con gái)",
                        "4. Cả Nam & Nữ (Ẩn Vợ, chỉ hiện Con gái)"
                    ]
                )
            with col2:
                cua_chon = st.selectbox("2. Lọc theo Cửa:", ["Tất cả", "Giáp", "Ất"])
            with col3:
                if cua_chon == "Giáp":
                    danh_sach_chi = [
                        "Tất cả", 
                        "Chi 1 Giáp (Cụ Liệu)", 
                        "Chi 2 Giáp (Cụ Dực)", 
                        "Chi 3 Giáp (Cụ Lạng)"
                    ]
                elif cua_chon == "Ất":
                    danh_sach_chi = [
                        "Tất cả", 
                        "Chi 4 Ất (Cụ Màn)", 
                        "Chi 5 Ất (Cụ Hùng)", 
                        "Chi 6 Ất (Cụ Lân)", 
                        "Chi 7 Ất (Cụ Lạc)"
                    ]
                else:
                    danh_sach_chi = ["Tất cả"] + sorted([c for c in df['Chi'].unique() if c not in ['Thủy Tổ', 'Gốc Giáp', 'Gốc Ất']])
                chi_chon = st.selectbox("3. Lọc theo Chi nhánh:", danh_sach_chi)

            st.markdown("<div class='hd-zoom'>💡 <b>Trên điện thoại:</b> Dùng 2 ngón tay kéo dãn để zoom to, hoặc bấm nút <b>(+)</b> để nhìn rõ từng đời.</div>", unsafe_allow_html=True)
            try:
                tree_graph = KyThuatBanVeGiaPha.draw_family_tree(df, cua_chon, chi_chon, che_do_xem)
                KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(tree_graph, chieu_cao=680)
            except Exception as e:
                st.error(f"Lỗi hiển thị: {e}")

        # --- HỒI 3: TRA CỨU DANH SÁCH ---
        elif menu == "🔍 Tra cứu theo Chi/Ngành":
            st.subheader("Tra cứu thông tin danh bộ gia tộc (Cơ sở dữ liệu SQLite)")
            df_approved = df[df["TrangThai"] == "Đã duyệt"].copy()
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                tim_ten = st.text_input("Tìm kiếm theo tên / Tên tự:")
            with c2:
                loc_gioitinh = st.selectbox("Giới tính:", ["Tất cả", "Nam", "Nữ"])
            with c3:
                loc_cua = st.selectbox("Cửa:", ["Tất cả", "Giáp", "Ất"])
            with c4:
                loc_chi = st.selectbox("Chi:", ["Tất cả"] + sorted([c for c in df_approved['Chi'].unique() if c]))
                
            if tim_ten:
                df_approved = df_approved[
                    df_approved["HoTen"].str.contains(tim_ten, case=False, na=False) | 
                    df_approved["TenTu"].str.contains(tim_ten, case=False, na=False)
                ]
            if loc_gioitinh != "Tất cả":
                df_approved = df_approved[df_approved["GioiTinh"] == loc_gioitinh]
            if loc_cua != "Tất cả":
                df_approved = df_approved[df_approved["Cua"] == loc_cua]
            if loc_chi != "Tất cả":
                df_approved = df_approved[df_approved["Chi"] == loc_chi]
                
            st.dataframe(
                df_approved[[
                    "ID", "ChaMe_ID", "HoTen", "TenTu", "GioiTinh", "DoiThu", 
                    "Chi_Nhanh", "VoChong", "NamSinh", "NamMat", "NgayGio", 
                    "GhiChu", "HinhAnh"
                ]],
                use_container_width=True,
                hide_index=True
            )

        # --- HỒI 4: ĐỀ XUẤT THÀNH VIÊN MỚI ---
        elif menu == "✍️ Đề xuất thành viên mới":
            st.subheader("Gửi đề xuất thêm thành viên mới vào CSDL")
            
            with st.form("form_add_member"):
                c1, c2 = st.columns(2)
                with c1:
                    ho_ten = st.text_input("Họ và Tên (*):")
                    ten_tu = st.text_input("Tên tự / Tên hiệu / Tên chữ:")
                    gioi_tinh = st.selectbox("Giới tính:", ["Nam", "Nữ"])
                    doi_thu = st.number_input("Đời thứ:", min_value=1, max_value=25, value=8)
                    cua = st.selectbox("Thuộc Cửa:", ["Giáp", "Ất", "Khác"])
                    chi = st.selectbox("Thuộc Chi:", [
                        "Chi 1 Giáp (Cụ Liệu)", "Chi 2 Giáp (Cụ Dực)", "Chi 3 Giáp (Cụ Lạng)",
                        "Chi 4 Ất (Cụ Màn)", "Chi 5 Ất (Cụ Hùng)", "Chi 6 Ất (Cụ Lân)", "Chi 7 Ất (Cụ Lạc)", "Khác"
                    ])
                with c2:
                    df_parents = df[df["TrangThai"] == "Đã duyệt"][["ID", "HoTen", "DoiThu", "Chi"]]
                    parent_dict = {row['ID']: f"{row['ID']} - {row['HoTen']} ({QuanTriTaiNguyen.get_circled_doi(row['DoiThu'])})" for _, row in df_parents.iterrows()}
                    parent_dict[0] = "0 - Cụ Thủy Tổ / Không rõ"
                    
                    cha_me_id = st.selectbox("Thuộc con của ai (ChaID)?:", options=list(parent_dict.keys()), format_func=lambda x: parent_dict[x])
                    vo_chong = st.text_input("Bà / Chồng (hoặc người gả cho):")
                    nam_sinh = st.text_input("Năm sinh:")
                    nam_mat = st.text_input("Năm mất (nếu đã mất):")
                    ngay_gio = st.text_input("Ngày giỗ Âm lịch (ví dụ: 15/07 AL):")

                ghi_chu = st.text_area("Chức danh / Ghi chú lịch sử / Công trạng:")
                btn_submit = st.form_submit_button("📤 Gửi đề xuất ghi vào SQL")
                
                if btn_submit:
                    if not ho_ten.strip():
                        st.error("Vui lòng nhập họ tên!")
                    else:
                        KhoDuLieuSQL.insert_member(
                            ho_ten=ho_ten.strip(),
                            ten_tu=ten_tu.strip(),
                            gioi_tinh=gioi_tinh,
                            doi_thu=doi_thu,
                            cua=cua,
                            chi=chi,
                            cha_id=cha_me_id,
                            vo_chong=vo_chong.strip(),
                            nam_sinh=nam_sinh.strip(),
                            nam_mat=nam_mat.strip(),
                            ngay_gio=ngay_gio.strip(),
                            ghi_chu=ghi_chu.strip(),
                            hinh_anh=""
                        )
                        st.success(f"Đã gửi đề xuất thêm '{ho_ten}' vào CSDL SQL thành công!")

        # --- HỒI 5: QUẢN TRỊ & PHÊ DUYỆT ---
        elif menu == "🛡️ Quản trị & Phê duyệt":
            st.subheader("Bảng phê duyệt dành cho Ban Liên Lạc Dòng Họ")
            mat_khau = st.sidebar.text_input("Mật khẩu Quản trị:", type="password")
            
            if mat_khau == "admin123":
                st.success("Xác thực Quản trị viên thành công!")
                df_pending = df[df["TrangThai"] == "Chờ duyệt"].copy()
                
                if df_pending.empty:
                    st.info("Hiện không có đề xuất nào đang chờ duyệt.")
                else:
                    st.warning(f"Có {len(df_pending)} đề xuất cần duyệt:")
                    st.dataframe(df_pending, use_container_width=True, hide_index=True)
                    
                    chon_id = st.selectbox("Chọn ID thành viên:", df_pending["ID"])
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Phê duyệt vào CSDL"):
                            KhoDuLieuSQL.approve_member(chon_id)
                            st.success(f"Đã phê duyệt ID {chon_id} vào hệ thống!")
                            st.rerun()
                    with col_b:
                        if st.button("❌ Xóa bỏ đề xuất"):
                            KhoDuLieuSQL.delete_member(chon_id)
                            st.error(f"Đã xóa đề xuất ID {chon_id}!")
                            st.rerun()
            else:
                st.warning("Vui lòng nhập mật khẩu quản trị (Mặc định: admin123).")


# ==============================================================================
# PHÂN KHU C: ĐIỀU PHỐI ĐẦU NÃO
# ==============================================================================

if __name__ == "__main__":
    SoChiHuyGiaoDien.render_app()
