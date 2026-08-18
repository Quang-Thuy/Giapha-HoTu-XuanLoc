import streamlit as st
import pandas as pd
from graphviz import Digraph
from pathlib import Path

# ==============================================================================
# 1. CẤU HÌNH DỮ LIỆU ĐỘC LẬP
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "giapha_data.csv"

# Bảng số đời khoanh tròn Unicode từ Đời 1 đến Đời 25
CIRCLED_NUMBERS = {
    1: "①", 2: "②", 3: "③", 4: "④", 5: "⑤",
    6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨", 10: "⑩",
    11: "⑪", 12: "⑫", 13: "⑬", 14: "⑭", 15: "⑮",
    16: "⑯", 17: "⑰", 18: "⑱", 19: "⑲", 20: "⑳", 21: "㉑"
}

def get_circled_doi(doi_val):
    try:
        d = int(doi_val)
        return CIRCLED_NUMBERS.get(d, f"({d})")
    except:
        return ""

def lay_ten_chinh(ho_ten_day_du):
    """Tách lấy duy nhất Tên gọi chính (bỏ họ Từ và tên đệm)"""
    ten = str(ho_ten_day_du).strip()
    if not ten or ten == "nan":
        return ""
    if "(" in ten:
        ten = ten.split("(")[0].strip()
    parts = ten.split()
    return parts[-1] if parts else ten

# ==============================================================================
# 2. KHỞI TẠO CƠ SỞ DỮ LIỆU CHUẨN XÁC TỪ TRANG 2 ĐẾN TRANG 15
# ==============================================================================
def init_database():
    raw_data = [
        # --- ĐỜI 1 ---
        {"ID": 1, "HoTen": "Từ Dương Đốc (Tự Vời Cán)", "GioiTinh": "Nam", "DoiThu": 1, "Cua": "Gốc", "Chi": "Thủy Tổ", "ChaMe_ID": 0, "VoChong": "Bà Trần Thị Niêm", "GhiChu": "Chi 2 Ất thuộc Đại Tôn di cư lên ở đây", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        
        # --- ĐỜI 2 ---
        {"ID": 2, "HoTen": "Từ Hữu Trí", "GioiTinh": "Nam", "DoiThu": 2, "Cua": "Giáp", "Chi": "Gốc Giáp", "ChaMe_ID": 1, "VoChong": "Bà Đào Thị Điểm", "GhiChu": "Đứng đầu cửa Giáp. Làm chức Tri điền. Mộ cồn Nhẳm (Có 12 con: 9 trai 3 gái chết sớm)", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 3, "HoTen": "Từ Hữu Mưu", "GioiTinh": "Nam", "DoiThu": 2, "Cua": "Ất", "Chi": "Gốc Ất", "ChaMe_ID": 1, "VoChong": "Bà chính Trần Thị Đinh, Bà thứ Trần Thị Đài", "GhiChu": "Đứng đầu cửa Ất. Chức Nghĩa Nam. Mộ cồn Chùa Lạch", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        
        # --- ĐỜI 3 - CỬA GIÁP ---
        {"ID": 4, "HoTen": "Từ Hữu Liệu", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 2, "VoChong": "Bà Trần Thị Tần", "GhiChu": "Trước làm chức Huyện Thừa", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 5, "HoTen": "Từ Hữu Dực", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 2, "VoChong": "Bà Ngô Thị Nự Tắc", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 6, "HoTen": "Từ Hữu Lạng", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 2, "VoChong": "Bà Trần Thị Côn", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        
        # --- ĐỜI 3 - CỬA ẤT ---
        {"ID": 7, "HoTen": "Từ Hữu Màn", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 3, "VoChong": "Bà Trần Thị Lụ", "GhiChu": "Trước làm thầy thuốc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 8, "HoTen": "Từ Hữu Hùng", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 3, "VoChong": "Bà Trần Thị Bính", "GhiChu": "Trước làm Tri bộ và Xã Trưởng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 9, "HoTen": "Từ Hữu Lân", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Ất", "Chi": "Nhánh Cụ Lân (Ất)", "ChaMe_ID": 3, "VoChong": "Bà Trần Thị Ảnh", "GhiChu": "Trước đi lính đóng Đội Trưởng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 10, "HoTen": "Từ Hữu Lạc", "GioiTinh": "Nam", "DoiThu": 3, "Cua": "Ất", "Chi": "Chi 3 Ất (Cụ Lạc)", "ChaMe_ID": 3, "VoChong": "Bà Hỗ Thị Thuần Thục", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 4 - GIÁP ---
        {"ID": 11, "HoTen": "Từ Hữu Di", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 4, "VoChong": "Bà Ngô Thị Tố", "GhiChu": "Trước làm nghề thợ rèn", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 12, "HoTen": "Từ Hữu Kỵ", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 5, "VoChong": "Bà Ngô Thị Lân", "GhiChu": "Trước làm Thầy thuốc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 13, "HoTen": "Từ Hữu Tương", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 5, "VoChong": "Bà Đào Thị Nanh", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 14, "HoTen": "Từ Hữu Tạc", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 5, "VoChong": "Bà Nguyễn Thị Trân", "GhiChu": "Trước làm nghề thợ rèn", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 15, "HoTen": "Từ Hữu Tỉnh", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 5, "VoChong": "Bà Trần Thị Phi", "GhiChu": "Giàu đại phú - Sắc ân Tứ thọ dân", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 16, "HoTen": "Từ Hữu Ẩm", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 5, "VoChong": "Bà Đào Thị Tư, Thứ thất Nguyễn Thị Chiêu", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 17, "HoTen": "Từ Hữu Tình", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 6, "VoChong": "Bà Ngô Thị Phụng", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 4 - ẤT ---
        {"ID": 18, "HoTen": "Từ Hữu Hiển", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 7, "VoChong": "Bà Ngô Thị ...", "GhiChu": "Hưởng thọ gần 100 tuổi", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 19, "HoTen": "Từ Hữu Kiều (mất sớm)", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 7, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 20, "HoTen": "Con gái cụ Màn", "GioiTinh": "Nữ", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 7, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 21, "HoTen": "Từ Hữu Linh", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 8, "VoChong": "Bà Trần Thị Dương", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 22, "HoTen": "Từ Hữu Cảo", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 8, "VoChong": "Bà Trần Thị Phổ", "GhiChu": "Hưởng thọ gần 100 tuổi", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 23, "HoTen": "Con gái cụ Hùng", "GioiTinh": "Nữ", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 8, "VoChong": "", "GhiChu": "Không rõ tên", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 24, "HoTen": "Từ Hữu Niên", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Nhánh Cụ Lân (Ất)", "ChaMe_ID": 9, "VoChong": "Bà Trần Thị Quy", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 25, "HoTen": "Từ Hữu Điền (Điều)", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Nhánh Cụ Lân (Ất)", "ChaMe_ID": 9, "VoChong": "Bà Đặng Thị Thành", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 26, "HoTen": "Con gái cụ Lân", "GioiTinh": "Nữ", "DoiThu": 4, "Cua": "Ất", "Chi": "Nhánh Cụ Lân (Ất)", "ChaMe_ID": 9, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 27, "HoTen": "Từ Hữu Thận", "GioiTinh": "Nam", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 3 Ất (Cụ Lạc)", "ChaMe_ID": 10, "VoChong": "Bà Nguyễn Thị Thế", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 28, "HoTen": "Con gái cụ Lạc", "GioiTinh": "Nữ", "DoiThu": 4, "Cua": "Ất", "Chi": "Chi 3 Ất (Cụ Lạc)", "ChaMe_ID": 10, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 5 - GIÁP ---
        {"ID": 29, "HoTen": "Từ Hữu Loan", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 11, "VoChong": "Bà chính Thái Thị Thiều, Thứ thất Ngô Thị Thi", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 30, "HoTen": "Từ Hữu Kiều", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 11, "VoChong": "Bà chính Trần Thị Sum, Bà thứ Nguyễn Thị Trung", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 31, "HoTen": "Từ Hữu Phượng", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 11, "VoChong": "Bà Trần Thị Binh", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 32, "HoTen": "Từ Hữu Điều", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 11, "VoChong": "Bà Nguyễn Thị Thiều", "GhiChu": "Phạp tự (không có con nối dõi)", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 33, "HoTen": "Con gái cụ Di", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 11, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        
        {"ID": 34, "HoTen": "Từ Hữu Tiển", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 12, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 35, "HoTen": "Từ Hữu Ngà", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 12, "VoChong": "Bà Trần Thị Náo", "GhiChu": "Phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 36, "HoTen": "Từ Hữu Lầu", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 12, "VoChong": "Bà Trần Thị Đị", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 37, "HoTen": "Con gái cụ Kỵ", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 12, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 38, "HoTen": "Từ Hữu Nghị", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 13, "VoChong": "Bà Trần Thị Chói", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 39, "HoTen": "Từ Hữu Vọ", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 13, "VoChong": "Bà Nguyễn Thị Sắc", "GhiChu": "Phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 40, "HoTen": "Từ Hữu Toàn", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 13, "VoChong": "Bà Trần Thị Chẹch", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 41, "HoTen": "Con gái cụ Tương", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 13, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 42, "HoTen": "Từ Hữu Bường (mất sớm)", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 15, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 43, "HoTen": "Từ Thị Bẹn", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 15, "VoChong": "Ông Trần Song (giữa làng)", "GhiChu": "Gả ông Trần Song giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 44, "HoTen": "Từ Hữu Chấn", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 15, "VoChong": "Bà Nguyễn Thị Thuyết", "GhiChu": "Mộ táng cồn Hỷ giữa ruộng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 45, "HoTen": "Từ Thị Phấn", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 15, "VoChong": "Trần Ích (giữa làng)", "GhiChu": "Gả Trần Ích giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 46, "HoTen": "Từ Hữu Nhin", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 15, "VoChong": "Bà Nguyễn Thị Xuy", "GhiChu": "Mộ táng Cồn Trù ghé dăm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 47, "HoTen": "Từ Hữu Hưng (mất sớm)", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 16, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 48, "HoTen": "Từ Thị Diễn", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 16, "VoChong": "Người họ Trần (giữa làng)", "GhiChu": "Gả người họ Trần giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 49, "HoTen": "Từ Thị Mày", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 16, "VoChong": "Người họ Trần (Yên Đồng)", "GhiChu": "Gả về Yên Đồng người họ Trần", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 50, "HoTen": "Từ Hữu Hồng", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 17, "VoChong": "", "GhiChu": "Thi trúng Nhị trường", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 51, "HoTen": "Từ Hữu Bằng", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 17, "VoChong": "Bà chính Trần Thị Nhuần, Bà thứ Nguyễn Thị Kỳ Thỉ", "GhiChu": "Trước thông hán, dạy học", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 52, "HoTen": "Từ Hữu Lập", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 17, "VoChong": "Bà chính Trần Thị ..., Bà thứ Cố Hậu", "GhiChu": "Làm thầy thuốc bắc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 53, "HoTen": "Con gái cụ Tình", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 17, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 5 - ẤT ---
        {"ID": 54, "HoTen": "Từ Hữu Khảng", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 18, "VoChong": "Bà Trần Thị Thương", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 55, "HoTen": "Từ Hữu Kỳ", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 18, "VoChong": "Bà Nguyễn Thị An", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 56, "HoTen": "Con gái cụ Hiển", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 18, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 57, "HoTen": "Từ Hữu Tiệt", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 21, "VoChong": "Không rõ", "GhiChu": "Ông bà này phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 58, "HoTen": "Từ Hữu Quýnh", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 21, "VoChong": "Bà Nguyễn Thị Ưu", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 59, "HoTen": "Từ Hữu ... (con cụ Linh)", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 21, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 60, "HoTen": "Con gái cụ Linh", "GioiTinh": "Nữ", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 21, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 61, "HoTen": "Từ Hữu Trình", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 22, "VoChong": "Bà Trần Thị Thập", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 62, "HoTen": "Từ Hữu Tranh", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 22, "VoChong": "Bà Trần Thị Khóa", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 63, "HoTen": "Từ Hữu Trừng", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 22, "VoChong": "Bà Ngô Thị Duyên", "GhiChu": "Phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 64, "HoTen": "Từ Hữu Điêu", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 22, "VoChong": "Bà Ngô Thị Khản", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 65, "HoTen": "Từ Hữu Kiên", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 22, "VoChong": "", "GhiChu": "Trước làm Phó Tổng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 66, "HoTen": "Từ Hữu Cồng", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 22, "VoChong": "Bà Trần Thị Tú", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 67, "HoTen": "Từ Hữu Dinh", "GioiTinh": "Nam", "DoiThu": 5, "Cua": "Ất", "Chi": "Chi 3 Ất (Cụ Lạc)", "ChaMe_ID": 27, "VoChong": "Không rõ", "GhiChu": "Di cư dạy hán, có 2 con trai (1 mất, 1 theo mẹ về quê ngoại)", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 6 - CON CỤ LOAN, KIỆU, PHƯỢNG (CHI 1 GIÁP) ---
        {"ID": 68, "HoTen": "Từ Hữu Thư", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 29, "VoChong": "Bà Ngô Thị Kim", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 69, "HoTen": "Con gái cụ Loan", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 29, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 70, "HoTen": "Từ Hữu Ngạnh", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 30, "VoChong": "Bà Thái Thị Mạnh", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 71, "HoTen": "Con gái cụ Kiệu", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 30, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 72, "HoTen": "Từ Hữu Khánh", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 31, "VoChong": "Bà Nguyễn Thị Lụ", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 73, "HoTen": "Từ Hữu Sum", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 31, "VoChong": "Bà Trần Thị Cơ", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 74, "HoTen": "Từ Hữu Cội", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 31, "VoChong": "Bà Trần Thị Dinh", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 75, "HoTen": "Từ Thị ... (con cụ Phượng)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 31, "VoChong": "Nguyễn Trương Khoa (Yên Đồng)", "GhiChu": "Gả Nguyễn Trương Khoa người Yên Đồng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 6 - CON CỤ TIỂN, LẦU, TOÀN (CHI 2 GIÁP) ---
        {"ID": 76, "HoTen": "Từ Hữu Toát", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 34, "VoChong": "Bà Trần Thị Náo", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 77, "HoTen": "Con gái cụ Tiển", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 34, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 78, "HoTen": "Từ Hữu Mận", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 36, "VoChong": "Bà Lê Thị ...", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 79, "HoTen": "Con gái cụ Lầu", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 36, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 80, "HoTen": "Từ Thị Huân", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 38, "VoChong": "Người họ Nguyễn", "GhiChu": "Gả người họ Nguyễn", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 81, "HoTen": "Từ Thị ... (con cụ Nghị)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 38, "VoChong": "Người họ Trần", "GhiChu": "Gả người họ Trần", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 82, "HoTen": "Từ Hữu Vẹn", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 40, "VoChong": "Bà Trần Thị Diệp", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 83, "HoTen": "Từ Hữu Vẹ", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 40, "VoChong": "Bà Trần Thị La", "GhiChu": "Phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 84, "HoTen": "Từ Hữu Cu (mất sớm)", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 40, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 6 - CON CỤ CHẤN & CỤ NHIN (CHI 2 GIÁP) ---
        {"ID": 85, "HoTen": "Từ Thị Mân", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "Khoan Trưởng (Đồng Lộc)", "GhiChu": "Gả ông Khoan Trưởng thành Đồng Lộc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 86, "HoTen": "Từ Thị Hân", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "Nguyễn Liêm (giữa làng)", "GhiChu": "Gả Nguyễn Liêm giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 87, "HoTen": "Từ Thị Cầm", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "Nguyễn Ẩm (Triền Lối)", "GhiChu": "Gả Nguyễn Ẩm người Triền Lối", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 88, "HoTen": "Từ Thị Phú", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "Nguyễn Thẩm (giữa làng)", "GhiChu": "Gả Nguyễn Thẩm giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 89, "HoTen": "Từ Thị Đích", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "Trần Bành (Triền Lối)", "GhiChu": "Gả Trần Bành người Triền Lối", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 90, "HoTen": "Từ Hữu Đức (mất sớm)", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 91, "HoTen": "Từ Thị Túc (mất sớm)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "", "GhiChu": "Gả giữa làng - chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 92, "HoTen": "Từ Hữu Đích (mất sớm)", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 44, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 93, "HoTen": "Từ Thị Tuần", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Bang Mỵ (Trạo Nha)", "GhiChu": "Gả Bang Mỵ người Yên Vinh Trạo Nha", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 94, "HoTen": "Từ Thị Hợi", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Ông Mạo (Hạ Xuân Mai)", "GhiChu": "Gả ông Mạo - Hạ Xuân Mai", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 95, "HoTen": "Từ Thị Thao", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Trần Lê Cớt (giữa làng)", "GhiChu": "Gả Trần Lê Cớt giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 96, "HoTen": "Từ Hữu Chính", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Bà Nguyễn Thị Sương", "GhiChu": "Trước làm Lý trưởng - thầy thuốc nam, địa lý phù thủy", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 97, "HoTen": "Từ Thị Năm", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Trần Lạc (Yên Đồng)", "GhiChu": "Gả Trần Lạc Yên Đồng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 98, "HoTen": "Từ Hữu Giáo", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Bà Thái Thị Thới", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 99, "HoTen": "Từ Hữu Thí", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 46, "VoChong": "Bà Trần Thị Ba", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 6 - CON CỤ HỒNG, BẰNG, LẬP (CHI 3 GIÁP) ---
        {"ID": 100, "HoTen": "Từ Hữu Thống", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 50, "VoChong": "Bà Trần Thị Cân", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 101, "HoTen": "Từ Hữu Thính", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 50, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 102, "HoTen": "Từ Thị Điển", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Gả về Xã Khố Nội", "GhiChu": "Gả về Xã Khố Nội", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 103, "HoTen": "Từ Thị ... (gả Trần Lại)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Trần Lại (giữa làng)", "GhiChu": "Gả Trần Lại giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 104, "HoTen": "Từ Thị ... (gả Cố Lượng)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Cố Lượng Nhạc (Trạo Nha)", "GhiChu": "Gả Cố Lượng Nhạc Trảo Nha", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 105, "HoTen": "Từ Thị Lạp", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Trần Bách (giữa làng)", "GhiChu": "Gả Trần Bách giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 106, "HoTen": "Từ Hữu Bối", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Bà Ngô Thị Chút", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 107, "HoTen": "Từ Hữu Triết", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Lấy chồng khác", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 108, "HoTen": "Từ Thị ... (lấy đại lộc)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 51, "VoChong": "Người Đại Lộc", "GhiChu": "Lấy người Đại Lộc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 109, "HoTen": "Từ Hữu Quán", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 52, "VoChong": "Bà Trần Thị Tuy", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 110, "HoTen": "Từ Thị ... (con cụ Lập)", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 52, "VoChong": "Ông Cu Hậu (Yên Đồng)", "GhiChu": "Gả ông Cu Hậu Yên Đồng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 111, "HoTen": "Từ Hữu Xán", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 52, "VoChong": "Bà Nguyễn Thị Suất", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 6 - CỬA ẤT ---
        {"ID": 112, "HoTen": "Từ Hữu Hòe", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 55, "VoChong": "Bà Trần Thị Cát", "GhiChu": "Phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 113, "HoTen": "Từ Hữu Trấn", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 55, "VoChong": "Bà Trần Thị Tình", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 114, "HoTen": "Từ Hữu Ắt", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 55, "VoChong": "Bà Trần Thị Thưởng", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 115, "HoTen": "Từ Hữu Dự", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 55, "VoChong": "Bà Nguyễn Thị Tòng, Nguyễn Thị Sáu", "GhiChu": "Phạp tự", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 116, "HoTen": "Con gái cụ Kỳ", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 55, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 117, "HoTen": "Từ Hữu Thạch", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 58, "VoChong": "Bà Nguyễn Thị Thẩm", "GhiChu": "Di cư ra Hoàng Mai - Nghệ An ở, tông tích không rõ", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 118, "HoTen": "Con gái cụ Quýnh", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 58, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 119, "HoTen": "Từ Hữu Lục", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 61, "VoChong": "Bà Trần Thị Khanh", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 120, "HoTen": "Từ Hữu Tùy", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 61, "VoChong": "Bà Trần Thị Trúc", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 121, "HoTen": "Con gái cụ Trình", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 61, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 122, "HoTen": "Từ Hữu Do", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 62, "VoChong": "Bà Ngô Thị Đị", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 123, "HoTen": "Con gái cụ Tranh", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 62, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 124, "HoTen": "Từ Hữu Chuyên", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 64, "VoChong": "Bà Trần Thị Nguyên", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 125, "HoTen": "Từ Hữu Chuân", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 64, "VoChong": "Bà Trần Thị Quynh", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 126, "HoTen": "Con gái cụ Điêu", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 64, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 127, "HoTen": "Từ Hữu Huân", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 65, "VoChong": "Bà Trần Thị Bôi", "GhiChu": "Trước làm Lý trưởng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 128, "HoTen": "Từ Hữu Giảng", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 65, "VoChong": "Bà Trần Thị Quán", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 129, "HoTen": "Từ Hữu Điển", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 65, "VoChong": "Bà Thái Thị Lương", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 130, "HoTen": "Con gái cụ Kiên", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 65, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        {"ID": 131, "HoTen": "Từ Hữu Bồng", "GioiTinh": "Nam", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 66, "VoChong": "Bà Trần Thị Ít", "GhiChu": "Di cư đi đâu không rõ", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 132, "HoTen": "Con gái cụ Cồng", "GioiTinh": "Nữ", "DoiThu": 6, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 66, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 7 (TRANG 10 ĐẾN TRANG 15) ---
        # Con cụ Thư (68)
        {"ID": 133, "HoTen": "Từ Hữu Phiệt", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 68, "VoChong": "Bà Trần Thị Thỏa", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 134, "HoTen": "Từ Thị ... (gả Trần Cớt)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 68, "VoChong": "Trần Cớt (giữa làng)", "GhiChu": "Gả ông Trần Cớt giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 135, "HoTen": "Từ Thị ... (gả Trần Chước)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 68, "VoChong": "Trần Chước (giữa làng)", "GhiChu": "Gả ông Trần Chước giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Ngạnh (70)
        {"ID": 136, "HoTen": "Từ Hữu Lâm", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 70, "VoChong": "Bà Trần Thị Nhỏ", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 137, "HoTen": "Từ Hữu Tâm", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 70, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Khánh (72)
        {"ID": 138, "HoTen": "Từ Hữu Sáng", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 72, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 139, "HoTen": "Từ Hữu Xích", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 72, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 140, "HoTen": "Từ Thị ... (gả Thạch Liên)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 72, "VoChong": "Cố Chắt Hiến (Thạch Liên)", "GhiChu": "Gả cố Chắt Hiến Thạch Liên", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Sum (73)
        {"ID": 141, "HoTen": "Từ Hữu Toại", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 142, "HoTen": "Từ Thị ... (gả Cố Sị)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "Cố Sị (giữa làng)", "GhiChu": "Gả cố Sị giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 143, "HoTen": "Từ Hữu Nghị (Đời 7)", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 144, "HoTen": "Từ Thị ... (gả Trần Thuyên)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "Trần Thuyên (giữa làng)", "GhiChu": "Gả Trần Thuyên giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 145, "HoTen": "Từ Thị ... (gả Trần Liêu)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "Trần Liêu (giữa làng)", "GhiChu": "Gả Trần Liêu giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 146, "HoTen": "Từ Thị Hành", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "Cửu Tường (Triền Lối)", "GhiChu": "Gả Cửu Tường Triền Lối", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 147, "HoTen": "Từ Thị ... (gả Trần Yến)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "Trần Yến (Trúc Lạng)", "GhiChu": "Gả Trần Yến Trúc Lạng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 148, "HoTen": "Từ Hữu Luân", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 73, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Cội (74)
        {"ID": 149, "HoTen": "Từ Thị Lệ", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "Trần Đinh (giữa làng)", "GhiChu": "Gả Trần Đinh giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 150, "HoTen": "Từ Hữu Lê", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 151, "HoTen": "Từ Thị ... (gả Trần Thảng)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "Trần Thảng (giữa làng)", "GhiChu": "Gả Trần Thảng giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 152, "HoTen": "Từ Hữu Nghĩa", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 153, "HoTen": "Từ Thị ... (gả Thầy Cầu)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "Thầy Cầu (Triền Lối)", "GhiChu": "Gả Thầy Cầu Triền Lối", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 154, "HoTen": "Từ Hữu Khí", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 155, "HoTen": "Từ Hữu Tề", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 156, "HoTen": "Từ Thị Tám", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 74, "VoChong": "Trần Hoan (giữa làng)", "GhiChu": "Gả ông Trần Hoan giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Toát (76)
        {"ID": 157, "HoTen": "Từ Hữu Duyệt", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 76, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 158, "HoTen": "Từ Hữu Hợi", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 76, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 159, "HoTen": "Từ Thị ... (gả Trần Thế)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 76, "VoChong": "Trần Thế (giữa làng)", "GhiChu": "Gả ông Trần Thế giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Mận (78)
        {"ID": 160, "HoTen": "Từ Thị Mai", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 78, "VoChong": "Trần Chinh (giữa làng)", "GhiChu": "Gả ông Trần Chinh giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 161, "HoTen": "Từ Hữu Khai", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 78, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 162, "HoTen": "Từ Hữu Lai", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 78, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Vẹn (82)
        {"ID": 163, "HoTen": "Từ Hữu Kiệp", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 82, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 164, "HoTen": "Từ Hữu Điệp", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 82, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 165, "HoTen": "Từ Thị Ba (gả Thạch Liên)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 82, "VoChong": "", "GhiChu": "Gả về Thạch Liên", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 166, "HoTen": "Từ Thị Chút (gả Tuần Dư Nại)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 82, "VoChong": "Tuần Dư Nại", "GhiChu": "Gả ông Tuần Dư Nại", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 167, "HoTen": "Từ Hữu Đửu", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 82, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 168, "HoTen": "Từ Thị Tỷ (gả Tiến Lộc)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 82, "VoChong": "Ông Long (Tiến Lộc)", "GhiChu": "Gả về Tiến Lộc - ông Long", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Vẹ (83)
        {"ID": 169, "HoTen": "Từ Thị ... (con cụ Vẹ - mất sớm)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 83, "VoChong": "", "GhiChu": "Mất sớm (Cụ Vẹ phạp tự)", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Chính (96)
        {"ID": 170, "HoTen": "Từ Quang Diệu", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 171, "HoTen": "Từ Quang Bút", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "", "GhiChu": "Liệt sĩ", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 172, "HoTen": "Từ Thị Tam (gả Trần Khởi)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "Trần Khởi (giữa làng)", "GhiChu": "Gả ông Trần Khởi giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 173, "HoTen": "Từ Thị Tứ", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 174, "HoTen": "Từ Thị Chút (con cụ Chính)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 175, "HoTen": "Từ Thị Hảo (gả Trần Bình)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "Trần Bình (giữa làng)", "GhiChu": "Gả ông Trần Bình giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 176, "HoTen": "Từ Quang Phú (Sơn)", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 177, "HoTen": "Từ Thị Tám (gả Nguyễn Long)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "Nguyễn Long (giữa làng)", "GhiChu": "Gả ông Nguyễn Long giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 178, "HoTen": "Từ Thị Chín (gả Nhân)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "Ông Nhân (giữa làng)", "GhiChu": "Gả ông Nhân giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 179, "HoTen": "Từ Thị Mười", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 96, "VoChong": "", "GhiChu": "Tảo vong", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Giáo (98)
        {"ID": 180, "HoTen": "Từ Thị Chắt (gả Quang Lộc)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 98, "VoChong": "Trần Minh (Quang Lộc)", "GhiChu": "Gả ông Trần Minh ở Quang Lộc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 181, "HoTen": "Từ Thị Con (gả Điền Xá)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 98, "VoChong": "Nguyễn Thủy (Điền Xá)", "GhiChu": "Gả ông Nguyễn Thủy ở Điền Xá", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 182, "HoTen": "Từ Hữu Huấn", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 98, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 183, "HoTen": "Từ Hữu Chuột", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 98, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 184, "HoTen": "Từ Hữu Xưng", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 98, "VoChong": "", "GhiChu": "Chết lúc 15 tuổi", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Thí (99)
        {"ID": 185, "HoTen": "Từ Hữu Thiện", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 99, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 186, "HoTen": "Từ Hữu Nuôi", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 99, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 187, "HoTen": "Từ Thị Tỷ (gả Đức Thọ)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 99, "VoChong": "Ông Sinh (Đức Thọ)", "GhiChu": "Gả ông Sinh người Đức Thọ", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 188, "HoTen": "Từ Thị Quyền", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 2 Giáp (Cụ Dực)", "ChaMe_ID": 99, "VoChong": "Ông Tuế (Thạch Ngọc)", "GhiChu": "Gả ông Tuế người Thạch Ngọc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Thống (100)
        {"ID": 189, "HoTen": "Từ Thị ... (gả Đồng Lộc)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 100, "VoChong": "", "GhiChu": "Gả về Xã Đồng Lộc", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 190, "HoTen": "Từ Thị ... (gả Yên Đồng)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 100, "VoChong": "", "GhiChu": "Gả về Yên Đồng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Thính (101)
        {"ID": 191, "HoTen": "Từ Thị ... (gả Trần Phiếm)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 101, "VoChong": "Trần Phiếm (giữa làng)", "GhiChu": "Gả ông Trần Phiếm giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 192, "HoTen": "Từ Hữu Mục", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 101, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 193, "HoTen": "Từ Hữu Khoa", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 101, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Bối (106)
        {"ID": 194, "HoTen": "Từ Thị Mày (con cụ Bối)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 106, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 195, "HoTen": "Từ Hữu Mậu", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 106, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 196, "HoTen": "Từ Thị Cháu", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 106, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Triết (107)
        {"ID": 197, "HoTen": "Từ Thị Chày", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 107, "VoChong": "", "GhiChu": "Lấy ai ở đâu không rõ", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 198, "HoTen": "Từ Hữu Cược", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 107, "VoChong": "", "GhiChu": "Tảo vong", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 199, "HoTen": "Từ Hữu Quằt", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 107, "VoChong": "", "GhiChu": "Tảo vong", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 200, "HoTen": "Từ Hữu Cháu", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 107, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Quán (109)
        {"ID": 201, "HoTen": "Từ Thị Khoách", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Nguyễn Thiền (giữa làng)", "GhiChu": "Lấy ông Nguyễn Thiền giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 202, "HoTen": "Từ Thị Hai", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Nguyễn Điểm (giữa làng)", "GhiChu": "Lấy ông Nguyễn Điểm giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 203, "HoTen": "Từ Thị Chự", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Ông Liêu (Kỳ Mòi)", "GhiChu": "Lấy ông Liêu ở Kỳ Mòi", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 204, "HoTen": "Từ Thị Em Nậy", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Trần Tuệ (giữa làng)", "GhiChu": "Lấy ông Trần Tuệ giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 205, "HoTen": "Từ Thị Em Con", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Trần Bệ (giữa làng)", "GhiChu": "Lấy ông Trần Bệ giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 206, "HoTen": "Từ Hữu Trù", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 207, "HoTen": "Từ Thị Chút (lấy Trần Bản)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Trần Bản (giữa làng)", "GhiChu": "Lấy ông Trần Bản giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 208, "HoTen": "Từ Thị Tám (lấy Trần Dê)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 109, "VoChong": "Trần Dê (giữa làng)", "GhiChu": "Lấy người Trần Dê giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Xán (111)
        {"ID": 209, "HoTen": "Từ Thị Bẹn (chết sớm)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "Đã lấy chồng, chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 210, "HoTen": "Từ Thị Em (lấy Bút)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "Ông Bút (Yên Đồng)", "GhiChu": "Lấy ông Bút ở Yên Đồng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 211, "HoTen": "Từ Thị Tam (chết đuối)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "Chết đuối", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 212, "HoTen": "Từ Thị Tứ (chết sớm)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 213, "HoTen": "Từ Hữu Năm", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 214, "HoTen": "Từ Hữu Lục (Xán)", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 215, "HoTen": "Từ Thị Bảy", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "Tảo vong", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 216, "HoTen": "Từ Hữu Tám", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Giáp", "Chi": "Chi 3 Giáp (Cụ Lạng)", "ChaMe_ID": 111, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Trấn (113)
        {"ID": 217, "HoTen": "Từ Hữu Bạt", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 113, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 218, "HoTen": "Từ Hữu Nhiếp", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 113, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 219, "HoTen": "Từ Thị Đị (gả Trần Hoàng)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 113, "VoChong": "Trần Hoàng (giữa làng)", "GhiChu": "Gả ông Trần Hoàng giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Ắt (114)
        {"ID": 220, "HoTen": "Từ Hữu Xỷ", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 114, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 221, "HoTen": "Từ Hữu Dỵ", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 114, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 222, "HoTen": "Từ Thị Em (lấy Trần Ninh)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 1 Ất (Cụ Màn)", "ChaMe_ID": 114, "VoChong": "Trần Ninh (giữa làng)", "GhiChu": "Lấy ông Trần Ninh giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Lục (119)
        {"ID": 223, "HoTen": "Từ Hữu Đỏ", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 119, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 224, "HoTen": "Từ Thị Tần", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 119, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 225, "HoTen": "Từ Thị Đức (chết)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 119, "VoChong": "", "GhiChu": "Chết", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Tùy (120)
        {"ID": 226, "HoTen": "Từ Hữu Hoài", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 120, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 227, "HoTen": "Từ Thị ... (lấy ông Láng)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 120, "VoChong": "Ông Láng (giữa làng)", "GhiChu": "Lấy ông Láng giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Do (122)
        {"ID": 228, "HoTen": "Từ Hữu Nha", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 122, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 229, "HoTen": "Từ Thị ... (con cụ Do)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 122, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Chuyên (124)
        {"ID": 230, "HoTen": "Từ Hữu Trại", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 124, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Chuân (125)
        {"ID": 231, "HoTen": "Từ Hữu Nhạc", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 125, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 232, "HoTen": "Từ Thị Mặc", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 125, "VoChong": "Nguyễn Viễn (giữa làng)", "GhiChu": "Lấy ông Nguyễn Viễn giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Huân (127)
        {"ID": 233, "HoTen": "Từ Hữu Vi", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 127, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 234, "HoTen": "Từ Hữu Lâu (Ất)", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 127, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 235, "HoTen": "Từ Hữu Ứng", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 127, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 236, "HoTen": "Từ Thị ... (lấy Mục Lung)", "GioiTinh": "Nữ", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 127, "VoChong": "Mục Lung (giữa làng)", "GhiChu": "Lấy ông Mục Lung giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Giảng (128)
        {"ID": 237, "HoTen": "Từ Hữu Lai (Giảng)", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 128, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 238, "HoTen": "Từ Hữu Lưu", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 128, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Điển (129)
        {"ID": 239, "HoTen": "Từ Hữu Kẹo", "GioiTinh": "Nam", "DoiThu": 7, "Cua": "Ất", "Chi": "Chi 2 Ất (Cụ Hùng)", "ChaMe_ID": 129, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # --- ĐỜI 8 (TRANG 15) ---
        # Con cụ Phiệt (133)
        {"ID": 240, "HoTen": "Từ Hữu Diệt", "GioiTinh": "Nam", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 133, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 241, "HoTen": "Từ Hữu Việt", "GioiTinh": "Nam", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 133, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 242, "HoTen": "Từ Thị ... (lấy Điệng, Cửu Bẹn)", "GioiTinh": "Nữ", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 133, "VoChong": "Ông Điệng, Cửu Bẹn", "GhiChu": "Lấy ông Điệng, lấy ông Cửu Bẹn", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 243, "HoTen": "Từ Hữu Huyền (Năm)", "GioiTinh": "Nam", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 133, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 244, "HoTen": "Từ Thị ... (lấy Ba Điêm)", "GioiTinh": "Nữ", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 133, "VoChong": "Ba Điêm (giữa làng)", "GhiChu": "Lấy ông Ba Điêm giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},

        # Con cụ Lâm (136)
        {"ID": 245, "HoTen": "Từ Thị Mực", "GioiTinh": "Nữ", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 136, "VoChong": "Cu Láng (giữa làng)", "GhiChu": "Lấy ông cu Láng giữa làng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 246, "HoTen": "Từ Thị Ba (3 chồng)", "GioiTinh": "Nữ", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 136, "VoChong": "", "GhiChu": "Lấy 3 chồng", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 247, "HoTen": "Từ Hữu Đồng", "GioiTinh": "Nam", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 136, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 248, "HoTen": "Từ Hữu Kê", "GioiTinh": "Nam", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 136, "VoChong": "", "GhiChu": "", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"},
        {"ID": 249, "HoTen": "Từ Thị Chút (chết sớm)", "GioiTinh": "Nữ", "DoiThu": 8, "Cua": "Giáp", "Chi": "Chi 1 Giáp (Cụ Liệu)", "ChaMe_ID": 136, "VoChong": "", "GhiChu": "Chết sớm", "TrangThai": "Đã duyệt", "NguoiDeXuat": "Gia tộc"}
    ]
    df = pd.DataFrame(raw_data)
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

def load_data():
    if not DB_FILE.exists():
        init_database()
    return pd.read_csv(DB_FILE, encoding="utf-8-sig").fillna("")

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

# ==============================================================================
# 3. THUẬT TOÁN VẼ CÂY PHẢ HỆ THÔNG MINH
# ==============================================================================
def get_ancestors_chain(df_data, focus_id):
    chain = []
    curr_id = int(focus_id)
    while curr_id != 0:
        row = df_data[df_data["ID"] == curr_id]
        if row.empty:
            break
        chain.insert(0, row.iloc[0].to_dict())
        curr_id = int(row.iloc[0].get("ChaMe_ID", 0))
    return chain

def draw_focus_tree(df_data, focus_id):
    dot = Digraph(comment='Focus Tree', node_attr={'shape': 'box', 'style': 'filled,rounded', 'fontname': 'Arial'})
    dot.attr(rankdir='TB', size='14,9')
    
    color_map = {
        1: "#FFD1D1", 2: "#FFE6CC", 3: "#FFF2CC", 
        4: "#D5E8D4", 5: "#DAE8FC", 6: "#E1D5E7", 7: "#FCE5CD", 8: "#D9EAD3", 9: "#FFF2CC"
    }

    ancestor_chain = get_ancestors_chain(df_data, focus_id)
    
    prev_node_id = None
    for member in ancestor_chain:
        m_id = str(member['ID'])
        ten = lay_ten_chinh(member['HoTen'])
        doi_num = int(member['DoiThu']) if str(member['DoiThu']).isdigit() else 1
        doi_khoanh = get_circled_doi(doi_num)
        
        is_focus = (member['ID'] == int(focus_id))
        fill = "#FFEB3B" if is_focus else color_map.get(doi_num, "#FFFFFF")
        
        label = f"{ten} {doi_khoanh}"
        dot.node(m_id, label, fillcolor=fill, color="#D32F2F" if is_focus else "#555555", penwidth="2.5" if is_focus else "1.0")
        
        if prev_node_id:
            dot.edge(prev_node_id, m_id, color="#D32F2F" if is_focus else "#333333", penwidth="2.0" if is_focus else "1.2")
        prev_node_id = m_id

    children = df_data[(df_data["ChaMe_ID"] == int(focus_id)) & (df_data["TrangThai"] == "Đã duyệt")]
    for _, child in children.iterrows():
        c_id = str(child['ID'])
        c_ten = lay_ten_chinh(child['HoTen'])
        c_doi_num = int(child['DoiThu']) if str(child['DoiThu']).isdigit() else 8
        c_doi_khoanh = get_circled_doi(c_doi_num)
        
        c_label = f"{c_ten} {c_doi_khoanh}"
        c_fill = color_map.get(c_doi_num, "#E8F5E9")
        
        dot.node(c_id, c_label, fillcolor=c_fill, color="#4CAF50", style="filled,dashed")
        dot.edge(str(focus_id), c_id, color="#4CAF50", penwidth="1.5")
        
    return dot

def draw_family_tree(df_data, cua_loc="Tất cả", chi_loc="Tất cả", che_do_xem="1. Chỉ Đinh Nam (Gọn: Tên ⑦)"):
    dot = Digraph(comment='Gia Phả Toàn Cảnh', node_attr={'shape': 'box', 'style': 'filled,rounded', 'fontname': 'Arial'})
    dot.attr(rankdir='TB', size='16,12')
    
    df_draw = df_data[df_data["TrangThai"] == "Đã duyệt"].copy()
    
    if "Chỉ Đinh Nam" in che_do_xem:
        df_draw = df_draw[df_draw["GioiTinh"] == "Nam"]
    
    if cua_loc != "Tất cả":
        df_draw = df_draw[(df_draw["Cua"] == cua_loc) | (df_draw["ID"] == 1)]
        
    if chi_loc != "Tất cả":
        root_cua_id = 2 if "Giáp" in chi_loc else (3 if "Ất" in chi_loc else 0)
        df_draw = df_draw[(df_draw["Chi"] == chi_loc) | (df_draw["ID"] == 1) | (df_draw["ID"] == root_cua_id)]

    color_map = {
        1: "#FFD1D1", 2: "#FFE6CC", 3: "#FFF2CC", 
        4: "#D5E8D4", 5: "#DAE8FC", 6: "#E1D5E7", 7: "#FCE5CD", 8: "#FFFFFF"
    }

    for _, row in df_draw.iterrows():
        node_id = str(row['ID'])
        ho_ten = str(row.get('HoTen', ''))
        doi_num = int(row['DoiThu']) if str(row['DoiThu']).isdigit() else 8
        doi_khoanh = get_circled_doi(doi_num)
        gioi_tinh = str(row.get('GioiTinh', 'Nam'))
        
        vo_val = str(row.get('VoChong', '')).strip()
        chuc_val = str(row.get('GhiChu', '')).strip()
        
        if che_do_xem == "1. Chỉ Đinh Nam (Gọn: Tên ⑦)":
            ten_chinh = lay_ten_chinh(ho_ten)
            label = f"{ten_chinh} {doi_khoanh}"
        elif che_do_xem == "2. Chỉ Đinh Nam (Chi tiết / Như cũ)":
            node_text = [f"{ho_ten} {doi_khoanh}"]
            if chuc_val and chuc_val != "nan":
                node_text.append(f"({chuc_val})")
            label = "\n".join(node_text)
        elif che_do_xem == "3. Cả Nam & Nữ (Đầy đủ cả Vợ & Con gái)":
            node_text = [f"{ho_ten} {doi_khoanh}"]
            if vo_val and vo_val != "nan":
                prefix = "Chồng" if gioi_tinh == "Nữ" else "Phối ngẫu"
                node_text.append(f"[{prefix}: {vo_val}]")
            if chuc_val and chuc_val != "nan":
                node_text.append(f"({chuc_val})")
            label = "\n".join(node_text)
        elif che_do_xem == "4. Cả Nam & Nữ (Ẩn Vợ, chỉ hiện Con gái)":
            node_text = [f"{ho_ten} {doi_khoanh}"]
            if gioi_tinh == "Nữ" and vo_val and vo_val != "nan":
                node_text.append(f"[Chồng: {vo_val}]")
            if chuc_val and chuc_val != "nan":
                node_text.append(f"({chuc_val})")
            label = "\n".join(node_text)
        else:
            label = f"{ho_ten} {doi_khoanh}"
        
        if gioi_tinh == "Nữ":
            fill = "#FFF0F5"
            shape = "ellipse"
        else:
            fill = color_map.get(doi_num, "#FFFFFF")
            shape = "box"
        
        dot.node(node_id, label, fillcolor=fill, shape=shape, color="#555555")
        
        parent_id = str(row.get('ChaMe_ID', 0))
        if parent_id != '0' and int(parent_id) in df_draw['ID'].values:
            dot.edge(parent_id, node_id, color="#333333")
            
    return dot

# ==============================================================================
# 4. GIAO DIỆN WEB STREAMLIT TỐI ƯU CHO DI ĐỘNG & MÁY TÍNH
# ==============================================================================
st.set_page_config(page_title="Gia Phả Họ Từ", page_icon="📜", layout="wide")

# Tối ưu CSS để hiển thị mượt mà trên Mobile
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: bold; margin-bottom: 5px; }
        h1 { font-size: 1.8rem !important; }
        h2, h3 { font-size: 1.3rem !important; }
    </style>
""", unsafe_allow_html=True)

# Tự động nạp lại DB nếu dữ liệu cũ chưa đủ 249 bản ghi chuẩn mới
if DB_FILE.exists():
    temp_df = pd.read_csv(DB_FILE, encoding="utf-8-sig")
    if len(temp_df) < 240:
        init_database()
else:
    init_database()

df = load_data()

st.title("📜 Gia Phả Điện Tử Dòng Họ Từ")
st.caption("Hệ thống quản lý phả hệ chuẩn mực — Tối ưu tra cứu trên Điện thoại & Máy tính")

if "focus_id" not in st.session_state:
    st.session_state.focus_id = 133 if 133 in df["ID"].values else 1

menu = st.sidebar.radio("CHỌN CHỨC NĂNG:", [
    "🎯 Cây Thám Hiểm Trực Hệ (Dễ xem nhất)",
    "🌳 Xem Cây Toàn Bộ / Từng Chi", 
    "🔍 Tra cứu theo Chi/Ngành", 
    "✍️ Đề xuất thành viên mới", 
    "🛡️ Quản trị & Phê duyệt"
])

# ------------------------------------------------------------------------------
# TAB 1: CÂY THÁM HIỂM TRỰC HỆ
# ------------------------------------------------------------------------------
if menu == "🎯 Cây Thám Hiểm Trực Hệ (Dễ xem nhất)":
    st.subheader("🎯 Tuyến Phả Hệ Trọng Tâm")
    
    chain = get_ancestors_chain(df, st.session_state.focus_id)
    breadcrumb_str = " ➔ ".join([f"**{lay_ten_chinh(c['HoTen'])} {get_circled_doi(c['DoiThu'])}**" for c in chain])
    st.info(f"📍 **Đường dẫn cội nguồn:** {breadcrumb_str}")

    col_tree, col_nav = st.columns([2, 1])
    
    with col_tree:
        try:
            focus_graph = draw_focus_tree(df, st.session_state.focus_id)
            st.graphviz_chart(focus_graph, use_container_width=True)
        except Exception as e:
            st.error(f"Lỗi hiển thị sơ đồ: {e}")

    with col_nav:
        curr_person = df[df["ID"] == st.session_state.focus_id].iloc[0]
        st.markdown(f"### 👤 Cụ: **{curr_person['HoTen']} {get_circled_doi(curr_person['DoiThu'])}**")
        st.write(f"- **Thuộc:** Cửa {curr_person['Cua']} — {curr_person['Chi']}")
        if curr_person['VoChong']:
            st.write(f"- **Phối ngẫu:** {curr_person['VoChong']}")
        if curr_person['GhiChu']:
            st.write(f"- **Ghi chú:** {curr_person['GhiChu']}")

        st.markdown("---")
        children = df[(df["ChaMe_ID"] == st.session_state.focus_id) & (df["TrangThai"] == "Đã duyệt")]
        
        if not children.empty:
            st.markdown(f"**👉 Bấm chọn người con (Đời {int(curr_person['DoiThu'])+1}) để mở tiếp:**")
            for _, ch in children.iterrows():
                btn_label = f"Mở nhánh: {lay_ten_chinh(ch['HoTen'])} {get_circled_doi(ch['DoiThu'])}"
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

# ------------------------------------------------------------------------------
# TAB 2: XEM CÂY TOÀN BỘ / THEO CHI
# ------------------------------------------------------------------------------
elif menu == "🌳 Xem Cây Toàn Bộ / Từng Chi":
    st.subheader("Sơ Đồ Phả Hệ Toàn Cảnh")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        che_do_xem = st.selectbox(
            "1. Chế độ hiển thị:", 
            [
                "1. Chỉ Đinh Nam (Gọn: Tên ⑦)",
                "2. Chỉ Đinh Nam (Chi tiết / Như cũ)",
                "3. Cả Nam & Nữ (Đầy đủ cả Vợ & Con gái)",
                "4. Cả Nam & Nữ (Ẩn Vợ, chỉ hiện Con gái)"
            ]
        )
    with col2:
        cua_chon = st.selectbox("2. Lọc theo Cửa:", ["Tất cả", "Giáp", "Ất"])
    with col3:
        if cua_chon == "Giáp":
            danh_sach_chi = ["Tất cả", "Chi 1 Giáp (Cụ Liệu)", "Chi 2 Giáp (Cụ Dực)", "Chi 3 Giáp (Cụ Lạng)"]
        elif cua_chon == "Ất":
            danh_sach_chi = ["Tất cả", "Chi 1 Ất (Cụ Màn)", "Chi 2 Ất (Cụ Hùng)", "Chi 3 Ất (Cụ Lạc)", "Nhánh Cụ Lân (Ất)"]
        else:
            danh_sach_chi = ["Tất cả"] + sorted([c for c in df['Chi'].unique() if c not in ['Thủy Tổ', 'Gốc Giáp', 'Gốc Ất']])
        chi_chon = st.selectbox("3. Lọc theo Chi nhánh:", danh_sach_chi)

    st.markdown("---")
    try:
        tree_graph = draw_family_tree(df, cua_chon, chi_chon, che_do_xem)
        st.graphviz_chart(tree_graph, use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi hiển thị: {e}")

# ------------------------------------------------------------------------------
# TAB 3: TRA CỨU DANH SÁCH
# ------------------------------------------------------------------------------
elif menu == "🔍 Tra cứu theo Chi/Ngành":
    st.subheader("Tra cứu thông tin danh bộ gia tộc")
    df_approved = df[df["TrangThai"] == "Đã duyệt"].copy()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tim_ten = st.text_input("Tìm kiếm theo tên:")
    with c2:
        loc_gioitinh = st.selectbox("Giới tính:", ["Tất cả", "Nam", "Nữ"])
    with c3:
        loc_cua = st.selectbox("Cửa:", ["Tất cả", "Giáp", "Ất"])
    with c4:
        loc_chi = st.selectbox("Chi:", ["Tất cả"] + sorted([c for c in df_approved['Chi'].unique() if c]))
        
    if tim_ten:
        df_approved = df_approved[df_approved["HoTen"].str.contains(tim_ten, case=False, na=False)]
    if loc_gioitinh != "Tất cả":
        df_approved = df_approved[df_approved["GioiTinh"] == loc_gioitinh]
    if loc_cua != "Tất cả":
        df_approved = df_approved[df_approved["Cua"] == loc_cua]
    if loc_chi != "Tất cả":
        df_approved = df_approved[df_approved["Chi"] == loc_chi]
        
    st.dataframe(
        df_approved[["ID", "HoTen", "GioiTinh", "DoiThu", "Cua", "Chi", "VoChong", "GhiChu"]],
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------------------------------------
# TAB 4: ĐỀ XUẤT THÀNH VIÊN MỚI
# ------------------------------------------------------------------------------
elif menu == "✍️ Đề xuất thành viên mới":
    st.subheader("Gửi đề xuất thêm thành viên mới")
    
    with st.form("form_add_member"):
        c1, c2 = st.columns(2)
        with c1:
            ho_ten = st.text_input("Họ và Tên (*):")
            gioi_tinh = st.selectbox("Giới tính:", ["Nam", "Nữ"])
            doi_thu = st.number_input("Đời thứ:", min_value=1, max_value=25, value=8)
            cua = st.selectbox("Thuộc Cửa:", ["Giáp", "Ất", "Khác"])
            chi = st.selectbox("Thuộc Chi:", [
                "Chi 1 Giáp (Cụ Liệu)", "Chi 2 Giáp (Cụ Dực)", "Chi 3 Giáp (Cụ Lạng)",
                "Chi 1 Ất (Cụ Màn)", "Chi 2 Ất (Cụ Hùng)", "Chi 3 Ất (Cụ Lạc)", "Nhánh Cụ Lân (Ất)", "Khác"
            ])
        with c2:
            df_parents = df[df["TrangThai"] == "Đã duyệt"][["ID", "HoTen", "DoiThu", "Chi"]]
            parent_dict = {row['ID']: f"{row['ID']} - {row['HoTen']} ({get_circled_doi(row['DoiThu'])})" for _, row in df_parents.iterrows()}
            parent_dict[0] = "0 - Cụ Thủy Tổ / Không rõ"
            
            cha_me_id = st.selectbox("Thuộc con của ai?:", options=list(parent_dict.keys()), format_func=lambda x: parent_dict[x])
            vo_chong = st.text_input("Vợ/Chồng (hoặc người gả cho):")
            nguoi_gui = st.text_input("Người đề xuất:", "Trưởng chi")

        ghi_chu = st.text_area("Ghi chú (chức sắc, nơi an táng, phạp tự, chết sớm):")
        btn_submit = st.form_submit_button("📤 Gửi đề xuất")
        
        if btn_submit:
            if not ho_ten.strip():
                st.error("Vui lòng nhập họ tên!")
            else:
                next_id = int(df["ID"].max()) + 1 if not df.empty else 1
                new_record = {
                    "ID": next_id,
                    "HoTen": ho_ten.strip(),
                    "GioiTinh": gioi_tinh,
                    "DoiThu": doi_thu,
                    "Cua": cua,
                    "Chi": chi,
                    "ChaMe_ID": cha_me_id,
                    "VoChong": vo_chong,
                    "GhiChu": ghi_chu,
                    "TrangThai": "Chờ duyệt",
                    "NguoiDeXuat": nguoi_gui
                }
                df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                save_data(df)
                st.success(f"Đã gửi đề xuất thêm '{ho_ten}' thành công!")

# ------------------------------------------------------------------------------
# TAB 5: QUẢN TRỊ & PHÊ DUYỆT
# ------------------------------------------------------------------------------
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
                if st.button("✅ Phê duyệt"):
                    df.loc[df["ID"] == chon_id, "TrangThai"] = "Đã duyệt"
                    save_data(df)
                    st.success(f"Đã phê duyệt ID {chon_id}!")
                    st.rerun()
            with col_b:
                if st.button("❌ Xóa bỏ"):
                    df = df[df["ID"] != chon_id]
                    save_data(df)
                    st.error(f"Đã xóa đề xuất ID {chon_id}!")
                    st.rerun()
    else:
        st.warning("Vui lòng nhập mật khẩu quản trị (Mặc định: admin123).")
