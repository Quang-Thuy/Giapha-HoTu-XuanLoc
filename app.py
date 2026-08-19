# ==============================================================================
# GIA PHẢ ĐIỆN TỬ DÒNG HỌ TỪ XUÂN LỘC
# SỞ CHỈ HUY TỔNG - KIẾN TRÚC PHÁO ĐÀI ĐA TẦNG
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
from data.db_manager import KhoDuLieuSQL
from core.graph_engine import KyThuatBanVeGiaPha
from core.validators import DataValidator
from utils.helpers import QuanTriTaiNguyen

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
        st.caption("Hệ thống quản lý phả hệ chuẩn mực — Cấu trúc Tôn Tộc & Phân Nhánh")

        if "focus_id" not in st.session_state:
            st.session_state.focus_id = 133 if 133 in df["ID"].values else 1

        # MENU ĐIỀU HƯỚNG GỌN GÀNG TỐI ƯU CHO ĐIỆN THOẠI
        menu = st.sidebar.radio("CHỌN CHỨC NĂNG:", [
            "🏛️ 1. Phả Hệ Đại Tôn",
            "🌿 2. Họ Từ Xuân Lộc",
            "📜 3. Kho Tư Liệu Cổ",
            "🕯️ 4. Văn Tế & Nghi Lễ",
            "✍️ Thêm Thành Viên",
            "🖨️ Xuất & In Ấn",
            "🛡️ Quản Trị Hệ Thống"
        ])

        # --- MỤC 1: PHẢ HỆ ĐẠI TÔN ---
        if menu == "🏛️ 1. Phả Hệ Đại Tôn":
            st.subheader("🏛️ Phả Hệ Đại Tôn (Gốc tích dòng họ)")
            st.markdown("Phần ghi chép lịch sử cội nguồn, bản sơ đồ Đại Tôn nguyên bản đến đời thứ 8 và quá trình di cư của các bậc tiền bối.")
            
            with st.expander("📖 Lược sử Đại Tôn & Bản thảo gốc"):
                st.write("""
                * **Thủy Tổ:** Cụ Tôn sư dòng họ, lưu giữ tại nhà thờ Đại Tôn.
                * **Sơ đồ nguyên bản:** Thể hiện rõ các nhánh trưởng, nhánh thứ từ đời thứ 1 đến đời thứ 8 (như tư liệu bản thảo viết tay cổ).
                * **Quá trình di cư:** Chi 2 Ất thuộc Đại Tôn di cư lên vùng đất mới, hình thành nên chi phái tại Xuân Lộc ngày nay.
                """)
            
            with st.expander("🔍 Tra cứu thông tin gốc Thủy Tổ (Đời 1 - Đời 3)"):
                df_dai_ton = df[df["DoiThu"] <= 3].copy()
                st.dataframe(df_dai_ton[["ID", "HoTen", "TenTu", "DoiThu", "Chi_Nhanh", "VoChong", "GhiChu"]], use_container_width=True, hide_index=True)

        # --- MỤC 2: HỌ TỪ XUÂN LỘC (3 TAB TƯƠNG TÁC) ---
        elif menu == "🌿 2. Họ Từ Xuân Lộc":
            st.subheader("🌿 Phả hệ Họ Từ Xuân Lộc (Hệ thống tương tác)")
            
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🎯 Cây Trực Hệ", "🌳 Cây Toàn Cảnh", "🔍 Tra Cứu Danh Bạ"])
            
            # 1. Cây Trực Hệ
            with sub_tab1:
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
                    if curr_person['GhiChu']:
                        st.write(f"- **Ghi chú:** {curr_person['GhiChu']}")

                    st.markdown("---")
                    children = df[(df["ChaMe_ID"] == st.session_state.focus_id) & (df["TrangThai"] == "Đã duyệt")]
                    if not children.empty:
                        st.markdown(f"**👉 Chọn con cháu đời kế tiếp:**")
                        for _, ch in children.iterrows():
                            if st.button(f"Mở: {QuanTriTaiNguyen.lay_ten_chinh(ch['HoTen'])} {QuanTriTaiNguyen.get_circled_doi(ch['DoiThu'])}", key=f"t1_child_{ch['ID']}"):
                                st.session_state.focus_id = ch['ID']
                                st.rerun()
                    else:
                        st.warning("Nhánh này hiện chưa cập nhật con cháu.")
                        
                    st.markdown("---")
                    if int(curr_person.get("ChaMe_ID", 0)) != 0:
                        if st.button("⬅️ Quay lại đời trước (Cha)"):
                            st.session_state.focus_id = int(curr_person["ChaMe_ID"])
                            st.rerun()
                    if st.button("🔄 Về gốc Cụ Thủy Tổ ①"):
                        st.session_state.focus_id = 1
                        st.rerun()

            # 2. Cây Toàn Cảnh
            with sub_tab2:
                col1, col2, col3 = st.columns(3)
                with col1:
                    che_do_xem = st.selectbox("1. Chế độ:", ["1. Chỉ Đinh Nam (Gọn: Tên ⑦)", "2. Chỉ Đinh Nam (Chi tiết)", "3. Cả Nam & Nữ"])
                with col2:
                    cua_chon = st.selectbox("2. Lọc Cửa:", ["Tất cả", "Giáp", "Ất"])
                with col3:
                    chi_chon = st.selectbox("3. Lọc Chi:", ["Tất cả"] + sorted([c for c in df['Chi'].unique() if c]))

                try:
                    tree_graph = KyThuatBanVeGiaPha.draw_family_tree(df, cua_chon, chi_chon, che_do_xem)
                    KyThuatBanVeGiaPha.hien_thi_so_do_tuong_tac(tree_graph, chieu_cao=680)
                except Exception as e:
                    st.error(f"Lỗi hiển thị: {e}")

            # 3. Tra Cứu Danh Bạ
            with sub_tab3:
                st.markdown("### Tra cứu danh bộ gia tộc chi tiết")
                df_approved = df[df["TrangThai"] == "Đã duyệt"].copy()
                c1, c2, c3 = st.columns(3)
                with c1:
                    tim_ten = st.text_input("Tìm tên:")
                with c2:
                    loc_cua = st.selectbox("Lọc Cửa:", ["Tất cả", "Giáp", "Ất"])
                with c3:
                    loc_chi = st.selectbox("Lọc Chi:", ["Tất cả"] + sorted([c for c in df_approved['Chi'].unique() if c]))
                    
                if tim_ten:
                    df_approved = df_approved[df_approved["HoTen"].str.contains(tim_ten, case=False, na=False) | df_approved["TenTu"].str.contains(tim_ten, case=False, na=False)]
                if loc_cua != "Tất cả":
                    df_approved = df_approved[df_approved["Cua"] == loc_cua]
                if loc_chi != "Tất cả":
                    df_approved = df_approved[df_approved["Chi"] == loc_chi]
                    
                st.dataframe(df_approved[["ID", "HoTen", "TenTu", "GioiTinh", "DoiThu", "Chi_Nhanh", "VoChong", "NgayGio", "GhiChu"]], use_container_width=True, hide_index=True)

        # --- MỤC 3: KHO TƯ LIỆU CỔ ---
        elif menu == "📜 3. Kho Tư Liệu Cổ":
            st.subheader("📜 Kho Tư Liệu Bút Tích & Sắc Phong Cổ")
            st.markdown("Lưu trữ ảnh chụp/scan bản thảo viết tay cổ để con cháu đời sau đối chiếu nguyên bản.")
            
            with st.expander("📄 Giới thiệu về Kho tư liệu gốc dòng họ"):
                st.write("Kho lưu trữ này bảo tồn các văn bản Hán Nôm cổ, gia phả giấy dòng họ và các tư liệu lịch sử quan trọng qua các thời kỳ.")

            with st.expander("📜 Tư liệu 01: Bản thảo phả hệ gốc (Chữ Hán)"):
                st.image("https://via.placeholder.com/600x350.png?text=Anh+Chup+Gia+Pha+Goc", caption="Bản thảo lưu giữ tại nhà thờ họ")
                st.markdown("**Bản dịch nghĩa:** Ghi chép về nguồn gốc di cư của cụ Thủy Tổ và sơ đồ phân nhánh tộc phái.")

        # --- MỤC 4: VĂN TẾ & NGHI LỄ ---
        elif menu == "🕯️ 4. Văn Tế & Nghi Lễ":
            st.subheader("🕯️ Văn Tế & Nghi Lễ Gia Tộc Cổ")
            st.markdown("Lưu truyền các bài văn cúng tế tổ tiên, văn khấn ngày giỗ họ và nghi thức truyền thống.")
            
            with st.expander("🏮 Lịch Giỗ Tổ & Chạp Mả hằng năm"):
                st.markdown("""
                * **Giỗ Tổ chính:** Ngày 25 tháng 7 Âm lịch (tưởng niệm cụ Hữu Phiệt và các bậc tiền bối).
                * **Lễ Chạp mả:** Tháng Chạp hằng năm tại cồn Nhẳm và cồn Chùa Lạch.
                """)

            with st.expander("📜 Xem và sao chép Văn khấn Giỗ Họ"):
                st.text_area(
                    "Nội dung văn khấn:",
                    value="Nam mô A Di Đà Phật! (3 lần)\n\n"
                          "Kính lạy tổ tiên dòng họ Từ Xuân Lộc...\n"
                          "Hôm nay là ngày... tháng... năm...\n"
                          "Con cháu toàn tộc thành tâm dâng hương hoa lễ vật...",
                    height=180
                )

            with st.expander("📋 Hướng dẫn nghi thức cúng tế chuẩn mực"):
                st.write("Trình bày thứ tự dâng hương của tộc trưởng, đại diện các chi phái và con cháu phương xa hướng về cội nguồn.")

        # --- THÊM THÀNH VIÊN ---
        elif menu == "✍️ Thêm Thành Viên":
            st.subheader("✍️ Gửi đề xuất thêm thành viên mới vào CSDL")
            with st.form("form_add_member"):
                c1, c2 = st.columns(2)
                with c1:
                    ho_ten = st.text_input("Họ và Tên (*):")
                    ten_tu = st.text_input("Tên tự / Tên hiệu:")
                    gioi_tinh = st.selectbox("Giới tính:", ["Nam", "Nữ"])
                    doi_thu = st.number_input("Đời thứ:", min_value=1, max_value=25, value=8)
                    cua = st.selectbox("Thuộc Cửa:", ["Giáp", "Ất", "Khác"])
                    chi = st.selectbox("Thuộc Chi:", ["Chi 1 Giáp (Cụ Liệu)", "Chi 2 Giáp (Cụ Dực)", "Chi 3 Giáp (Cụ Lạng)", "Chi 4 Ất (Cụ Màn)", "Chi 5 Ất (Cụ Hùng)", "Chi 6 Ất (Cụ Lân)", "Chi 7 Ất (Cụ Lạc)", "Khác"])
                with c2:
                    df_parents = df[df["TrangThai"] == "Đã duyệt"][["ID", "HoTen", "DoiThu", "Chi"]]
                    parent_dict = {row['ID']: f"{row['ID']} - {row['HoTen']} ({QuanTriTaiNguyen.get_circled_doi(row['DoiThu'])})" for _, row in df_parents.iterrows()}
                    parent_dict[0] = "0 - Cụ Thủy Tổ / Không rõ"
                    cha_me_id = st.selectbox("Thuộc con của ai (ChaID)?:", options=list(parent_dict.keys()), format_func=lambda x: parent_dict[x])
                    vo_chong = st.text_input("Bà / Chồng:")
                    nam_sinh = st.text_input("Năm sinh:")
                    nam_mat = st.text_input("Năm mất:")
                    ngay_gio = st.text_input("Ngày giỗ Âm lịch (ví dụ: 25/07 AL):")

                ghi_chu = st.text_area("Chức danh / Ghi chú lịch sử:")
                btn_submit = st.form_submit_button("📤 Gửi đề xuất")
                
                if btn_submit:
                    success, messages = DataValidator.insert_member(
                        ho_ten=ho_ten.strip(), ten_tu=ten_tu.strip(), gioi_tinh=gioi_tinh,
                        doi_thu=doi_thu, cua=cua, chi=chi, cha_id=cha_me_id,
                        vo_chong=vo_chong.strip(), nam_sinh=nam_sinh.strip(), nam_mat=nam_mat.strip(),
                        ngay_gio=ngay_gio.strip(), ghi_chu=ghi_chu.strip(), hinh_anh=""
                    )
                    if success: st.success(messages[0])
                    else:
                        for err in messages: st.error(err)

        # --- XUẤT & IN ẤN ---
        elif menu == "🖨️ Xuất & In Ấn":
            st.subheader("🖨️ Trung tâm Xuất Báo cáo & In ấn Phả Hệ")
            df_approved = df[df["TrangThai"] == "Đã duyệt"].copy()
            export_df = df_approved[["ID", "ChaMe_ID", "HoTen", "TenTu", "GioiTinh", "DoiThu", "Chi_Nhanh", "VoChong", "NamSinh", "NamMat", "NgayGio", "GhiChu"]].rename(columns={
                "ChaMe_ID": "Mã Cha/Mẹ", "HoTen": "Họ và Tên", "TenTu": "Tên Tự/Hiệu",
                "GioiTinh": "Giới Tính", "DoiThu": "Đời Thứ", "Chi_Nhanh": "Chi/Nhánh",
                "VoChong": "Vợ/Chồng", "NamSinh": "Năm Sinh", "NamMat": "Năm Mất",
                "NgayGio": "Ngày Giỗ Âm Lịch", "GhiChu": "Ghi Chú/Chức Danh"
            })
            tab1, tab2 = st.tabs(["📥 Xuất dữ liệu (CSV)", "📄 Xem trước & In ấn"])
            with tab1:
                csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Tải xuống tệp CSV (Excel)", data=csv_data, file_name="GiaPha_DongHoTuXuAnLoc.csv", mime="text/csv")
            with tab2:
                if st.button("🖨️ Mở cửa sổ In ấn / Xuất PDF"):
                    html_report = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Gia phả</title><style>body{{font-family:'Times New Roman';margin:20px;}}h1,h2{{text-align:center;text-transform:uppercase;margin:5px 0;}}table{{width:100%;border-collapse:collapse;margin-top:10px;}}th,td{{border:1px solid #333;padding:8px;font-size:13px;}}th{{background:#f2f2f2;text-align:center;}}.center{{text-align:center;}}@media print{{body{{margin:0;}}</style></head><body><h1>Dòng Họ Từ Xuân Lộc</h1><h2>PHẢ HỆ TOÀN TẬP GIA TỘC</h2><div style="text-align:center;font-style:italic;margin-bottom:20px;">(Tài liệu lưu giữ nội bộ)</div><table><thead><tr><th>STT</th><th>Họ và Tên</th><th>Tên Tự</th><th>Đời</th><th>Chi / Nhánh</th><th>Hôn phối</th><th>Ngày Giỗ</th><th>Ghi chú</th></tr></thead><tbody>"""
                    for idx, row in export_df.iterrows():
                        html_report += f"""<tr><td class="center">{idx + 1}</td><td><b>{row['Họ và Tên']}</b></td><td>{row['Tên Tự/Hiệu']}</td><td class="center">Đời {row['Đời Thứ']}</td><td>{row['Chi/Nhánh']}</td><td>{row['Vợ/Chồng']}</td><td class="center">{row['Ngày Giỗ Âm Lịch']}</td><td>{row['Ghi Chú/Chức Danh']}</td></tr>"""
                    html_report += """</tbody></table><script>window.print();</script></body></html>"""
                    components.html(html_report, height=600, scrolling=True)

        # --- QUẢN TRỊ ---
        elif menu == "🛡️ Quản Trị Hệ Thống":
            st.subheader("🛡️ Bảng phê duyệt dành cho Ban Liên Lạc Dòng Họ")
            mat_khau = st.sidebar.text_input("Mật khẩu Quản trị:", type="password")
            if mat_khau == "admin123":
                st.success("Xác thực thành công!")
                df_pending = df[df["TrangThai"] == "Chờ duyệt"].copy()
                if df_pending.empty: st.info("Hiện không có đề xuất nào chờ duyệt.")
                else:
                    chon_id = st.selectbox("Chọn ID thành viên:", df_pending["ID"])
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Phê duyệt"):
                            KhoDuLieuSQL.approve_member(chon_id)
                            st.success(f"Đã duyệt ID {chon_id}!")
                            st.rerun()
                    with col_b:
                        if st.button("❌ Xóa bỏ"):
                            KhoDuLieuSQL.delete_member(chon_id)
                            st.error(f"Đã xóa ID {chon_id}!")
                            st.rerun()
            else:
                st.warning("Nhập mật khẩu quản trị (Mặc định: admin123).")

if __name__ == "__main__":
    SoChiHuyGiaoDien.render_app()
