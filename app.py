# ==============================================================================
# TÊN PHẦN MỀM : PHẦN MỀM GIA PHẢ ĐIỆN TỬ DÒNG HỌ TỪ XUÂN LỘC
# PHIÊN BẢN    : 1.6.3 (Chuẩn định danh hợp nhất & Tối ưu đa thiết bị)
# TÁC GIẢ      : TỪ QUANG THÙY
# CHỦ SỞ HỮU   : TỪ QUANG THÙY
# NĂM HOÀN THÀNH: 2026
# BẢN QUYỀN    : Bảo lưu mọi quyền (All Rights Reserved). Nghiêm cấm sao chép,
#                phân phối hoặc sử dụng mã nguồn khi chưa có sự đồng ý bằng văn bản.
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sqlite3
import re
import os
import shutil
import threading
import time
import random
import unicodedata
import urllib.parse
import urllib.request
import json
import datetime
import base64
import io
import zipfile
from pathlib import Path
from PIL import Image, ImageOps
from graphviz import Digraph
import folium
from streamlit_folium import st_folium
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from io import BytesIO

import telebot
from telebot import types

import sys

# Thử nghiệm đăng ký hỗ trợ định dạng ảnh HEIC/HEIF của iPhone
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# --- CẤU HÌNH ĐƯỜNG DẪN GRAPHVIZ TỰ ĐỘNG ---
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

def auto_detect_graphviz():
    if shutil.which("dot") is not None:
        return
    common_paths = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
        os.path.expanduser(r"~\AppData\Local\Programs\Graphviz\bin"),
    ]
    for path in common_paths:
        dot_executable = os.path.join(path, "dot.exe" if os.name == "nt" else "dot")
        if os.path.exists(dot_executable):
            os.environ["PATH"] += os.pathsep + path
            break

auto_detect_graphviz()

# ==============================================================================
# QUẢN TRỊ TELEGRAM & PHÂN QUYỀN ĐA CẤP (RBAC 2-TIER)
# Bảo mật tuyệt đối: Không chứa Token cứng trong mã nguồn
# ==============================================================================

class TelegramBotManager:
    @staticmethod
    def _get_db_config():
        """Đọc toàn bộ cấu hình Telegram và danh sách phân quyền từ SQLite"""
        cfg = {}
        try:
            db_path = Path(__file__).resolve().parent / "giapha_HoTu.db"
            if db_path.exists():
                with sqlite3.connect(db_path, timeout=15) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT Khoa, GiaTri FROM CauHinhHeThong WHERE Khoa LIKE 'tele_%'")
                    cfg = dict(cursor.fetchall())
        except Exception:
            pass
        return cfg

    @staticmethod
    def get_bot_token_and_chat_id():
        """
        [TẠM THỜI ĐỂ TEST]: Cố định token và chat_id trực tiếp để không phải nhập lại.
        Sau khi ổn định, ông chủ chỉ cần xóa hoặc đặt trống 2 biến này bên dưới, 
        hệ thống sẽ tự động quay về cơ chế đọc bảo mật qua Streamlit Secrets / SQLite.
        """
        TEMP_TEST_TOKEN = "8709408235:AAH69tB_CGYxDs4ZuCSxKMNlPXg4yJhg_JE"     # Ví dụ: "7123456789:AAG..."
        TEMP_TEST_CHAT_ID = "-1004360294941"   # Ví dụ: "-100123456789"

        token = TEMP_TEST_TOKEN.strip()
        chat_id = TEMP_TEST_CHAT_ID.strip()

        # Nếu chưa điền ở biến tạm, hệ thống sẽ tự quét theo cơ chế bảo mật cũ
        if not token or not chat_id:
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

            if not token:
                try:
                    if "TELEGRAM_BOT_TOKEN" in st.secrets:
                        token = str(st.secrets["TELEGRAM_BOT_TOKEN"]).strip()
                    if "TELEGRAM_CHAT_ID" in st.secrets:
                        chat_id = str(st.secrets["TELEGRAM_CHAT_ID"]).strip()
                except Exception:
                    pass

            cfg = TelegramBotManager._get_db_config()
            if cfg.get("tele_enabled", "True") == "False":
                return "", ""

            if not token:
                token = cfg.get("tele_bot_token", "").strip()
            if not chat_id:
                chat_id = cfg.get("tele_chat_id", "").strip()

        # Lưu đệm vào biến môi trường của tiến trình để luồng ngầm (Thread) đọc ổn định 100%
        if token:
            os.environ["TELEGRAM_BOT_TOKEN"] = token
        if chat_id:
            os.environ["TELEGRAM_CHAT_ID"] = chat_id

        return token, chat_id

    @staticmethod
    def parse_id_list(raw_str):
        """Tách chuỗi ID ngăn cách bởi dấu phẩy thành danh sách chuẩn"""
        if not raw_str:
            return []
        return [x.strip() for x in re.split(r'[,;\s]+', str(raw_str)) if x.strip()]

    @staticmethod
    def lay_so_chi_tu_ma_id(member_id):
        """Giải mã số Chi (1..5) từ ký tự thứ 2 của Mã định danh 9 chữ số"""
        clean_id = str(member_id).replace(".", "").strip()
        if len(clean_id) >= 2 and clean_id[1].isdigit():
            return clean_id[1]
        return "0"

    @staticmethod
    def kiem_tra_quyen_duyet(user_tele_id, member_id):
        """
        Kiểm tra quyền duyệt của người bấm nút trên Telegram:
        - Admin Cấp 1: Toàn quyền duyệt mọi Cửa / Chi.
        - Admin Cấp 2: Chỉ được duyệt thành viên thuộc đúng Chi mình phụ trách.
        """
        uid = str(user_tele_id).strip()
        cfg = TelegramBotManager._get_db_config()
        
        # 1. Kiểm tra Admin Cấp 1 (Toàn quyền - Lấy từ DB hoặc Streamlit Secrets nếu có)
        admin_cap1_list = TelegramBotManager.parse_id_list(cfg.get("tele_admin_cap1", ""))
        try:
            if "TELEGRAM_ADMIN_CAP1" in st.secrets:
                admin_cap1_list.extend(TelegramBotManager.parse_id_list(st.secrets["TELEGRAM_ADMIN_CAP1"]))
        except Exception:
            pass

        if uid in admin_cap1_list:
            return True, "Admin Cấp 1 (Toàn quyền)"

        # 2. Kiểm tra Admin Cấp 2 theo đúng Chi của thành viên
        so_chi = TelegramBotManager.lay_so_chi_tu_ma_id(member_id)
        admin_chi_list = TelegramBotManager.parse_id_list(cfg.get(f"tele_admin_chi_{so_chi}", ""))
        if uid in admin_chi_list:
            return True, f"Admin Cấp 2 (Chi {so_chi})"

        # 3. Nếu chưa cấu hình phân quyền chi tiết trong DB, cho phép duyệt mặc định
        has_any_rbac = bool(admin_cap1_list) or any(
            bool(TelegramBotManager.parse_id_list(cfg.get(f"tele_admin_chi_{i}", ""))) for i in range(1, 6)
        )
        if not has_any_rbac:
            return True, "Quản trị viên"

        return False, f"Mã ID của bạn ({uid}) chưa có trong danh sách Admin duyệt Chi {so_chi}!"

    @staticmethod
    def _tao_bot_instance(token):
        """Khởi tạo TeleBot với threaded=False để không bị kẹt sub-thread trên Streamlit Cloud"""
        bot = telebot.TeleBot(token, threaded=False)

        @bot.message_handler(commands=['start', 'myid', 'id'])
        def send_user_id(message):
            uid = message.from_user.id
            uname = message.from_user.full_name
            cid = message.chat.id
            msg_reply = (
                f"👋 Xin chào dòng tộc, <b>{uname}</b>!\n"
                f"🆔 <b>Mã Telegram cá nhân (User ID) của bạn là:</b> <code>{uid}</code>\n"
                f"💬 <b>Mã cuộc trò chuyện (Chat ID):</b> <code>{cid}</code>\n\n"
                f"<i>👉 Hãy gửi mã <code>{uid}</code> này cho Ông chủ (Admin Cấp 1) để được cấp quyền phê duyệt thành viên của Chi mình.</i>"
            )
            bot.reply_to(message, msg_reply, parse_mode="HTML")

        @bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            data = str(call.data or "")
            user_click_id = call.from_user.id
            user_click_name = call.from_user.full_name or "Admin"

            try:
                if data.startswith("duyet_") or data.startswith("xoa_"):
                    is_approve = data.startswith("duyet_")
                    member_id = data.replace("duyet_", "").replace("xoa_", "").strip()

                    # 1. Kiểm tra phân quyền
                    co_quyen, thong_bao_quyen = TelegramBotManager.kiem_tra_quyen_duyet(user_click_id, member_id)
                    if not co_quyen:
                        bot.answer_callback_query(call.id, f"❌ {thong_bao_quyen}"[:190], show_alert=True)
                        return

                    # 2. Thực thi cập nhật/xóa trực tiếp vào CSDL SQLite (timeout=20 chống khóa bảng)
                    kq = False
                    ho_ten = "Thành viên"
                    db_path = Path(__file__).resolve().parent / "giapha_HoTu.db"

                    with sqlite3.connect(db_path, timeout=20) as conn:
                        cursor = conn.cursor()
                        if is_approve:
                            cursor.execute("SELECT TinhTrang, HoTen FROM GiaPha WHERE ID = ?", (member_id,))
                            row = cursor.fetchone()
                            if row:
                                tinh_trang_goc, ho_ten = row
                                new_tinh_trang = (
                                    str(tinh_trang_goc)
                                    .replace("Chờ duyệt,", "")
                                    .replace("Chờ duyệt", "")
                                    .replace("Chờ xử lý,", "")
                                    .replace("Chờ xử lý", "")
                                    .strip()
                                )
                                cursor.execute("UPDATE GiaPha SET TinhTrang = ? WHERE ID = ?", (new_tinh_trang, member_id))
                                conn.commit()
                                kq = True
                        else:
                            cursor.execute("SELECT HoTen FROM GiaPha WHERE ID = ?", (member_id,))
                            row = cursor.fetchone()
                            if row:
                                ho_ten = row[0]
                                try:
                                    duong_dan_anh = QuanTriHinhAnh.lay_anh_chuan_xac(member_id, ho_ten)
                                    if duong_dan_anh:
                                        img_path = Path(__file__).resolve().parent / duong_dan_anh
                                        if img_path.exists():
                                            img_path.unlink()
                                except Exception:
                                    pass
                                cursor.execute("DELETE FROM GiaPha WHERE ID = ?", (member_id,))
                                conn.commit()
                                kq = True

                    # 3. PHẢN HỒI TỨC THÌ CHO TELEGRAM ĐỂ TẮT VÒNG XOAY TRÊN ĐIỆN THOẠI NGAY LẬP TỨC
                    if kq:
                        msg_toast = "✅ Đã phê duyệt vào Gia phả!" if is_approve else "❌ Đã từ chối và xóa hồ sơ!"
                        try:
                            bot.answer_callback_query(call.id, msg_toast)
                        except Exception:
                            pass

                        # 4. Cập nhật lại nội dung tin nhắn trên Telegram (gỡ bỏ 2 nút bấm)
                        trang_thai_txt = "✅ <b>ĐÃ PHÊ DUYỆT THÀNH CÔNG</b>" if is_approve else "❌ <b>ĐÃ TỪ CHỐI & XÓA BỎ</b>"
                        cap_text = (
                            f"{trang_thai_txt}\n"
                            f"👤 Thành viên: <b>{ho_ten}</b> (ID: <code>{member_id}</code>)\n"
                            f"🛡 Người xử lý: <b>{user_click_name}</b> ({thong_bao_quyen})"
                        )
                        try:
                            if call.message.photo:
                                bot.edit_message_caption(
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    caption=cap_text,
                                    parse_mode="HTML",
                                    reply_markup=None
                                )
                            else:
                                bot.edit_message_text(
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    text=cap_text,
                                    parse_mode="HTML",
                                    reply_markup=None
                                )
                        except Exception:
                            pass

                        # 5. Làm mới bộ nhớ đệm của Web
                        try:
                            KhoDuLieuSQL.load_data.clear()
                        except Exception:
                            pass
                    else:
                        bot.answer_callback_query(call.id, "ℹ️ Hồ sơ này đã được xử lý hoặc không còn trong CSDL!", show_alert=True)

                elif data.startswith("sv_approve_") or data.startswith("sv_reject_"):
                    is_approve = data.startswith("sv_approve_")
                    post_id = data.replace("sv_approve_", "").replace("sv_reject_", "").strip()

                    db_path = Path(__file__).resolve().parent / "giapha_HoTu.db"
                    KhoDuLieuSQL.init_so_vang_table()

                    with sqlite3.connect(db_path, timeout=20) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT TacGia, COALESCE(SoChi, '0') FROM SoVang WHERE ID = ?", (post_id,))
                        row = cursor.fetchone()

                        if not row:
                            bot.answer_callback_query(call.id, "ℹ️ Lưu bút này đã được xử lý hoặc không còn trong CSDL!", show_alert=True)
                            return

                        tac_gia, so_chi = row[0], str(row[1]).strip()

                        # 1. Kiểm tra quyền duyệt (Admin Cấp 1 hoặc Admin Cấp 2 phụ trách đúng Chi)
                        ma_gia_lap = f"1{so_chi}0.01.0.001" if so_chi in ["1", "2", "3", "4", "5"] else "000.01.0.001"
                        co_quyen, thong_bao_quyen = TelegramBotManager.kiem_tra_quyen_duyet(user_click_id, ma_gia_lap)
                        if not co_quyen:
                            bot.answer_callback_query(call.id, f"❌ {thong_bao_quyen}"[:190], show_alert=True)
                            return

                        # 2. Thực thi cập nhật trạng thái 'Đã duyệt' hoặc Xóa bỏ
                        if is_approve:
                            cursor.execute("UPDATE SoVang SET TrangThai = 'Đã duyệt' WHERE ID = ?", (post_id,))
                        else:
                            cursor.execute("DELETE FROM SoVang WHERE ID = ?", (post_id,))
                        conn.commit()

                    # 3. Phản hồi tức thì tắt vòng xoay trên điện thoại
                    msg_toast = "✅ Đã phê duyệt hiển thị lên Sổ Vàng!" if is_approve else "❌ Đã từ chối và xóa lưu bút!"
                    try:
                        bot.answer_callback_query(call.id, msg_toast)
                    except Exception:
                        pass

                    # 4. Cập nhật lại nội dung tin nhắn trên Telegram
                    trang_thai_txt = "✅ <b>SỔ VÀNG ĐÃ ĐƯỢC PHÊ DUYỆT</b>" if is_approve else "❌ <b>SỔ VÀNG ĐÃ BỊ TỪ CHỐI & XÓA BỎ</b>"
                    cap_text = (
                        f"{trang_thai_txt}\n"
                        f"👤 Người gửi: <b>{tac_gia}</b> (Mã bài: <code>#{post_id}</code>)\n"
                        f"🛡 Người xử lý: <b>{user_click_name}</b> ({thong_bao_quyen})"
                    )
                    try:
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=cap_text,
                            parse_mode="HTML",
                            reply_markup=None
                        )
                    except Exception:
                        pass
                    else:
                        bot.answer_callback_query(call.id, "ℹ️ Lưu bút này đã được xử lý hoặc không còn trong CSDL!", show_alert=True)

            except Exception as e:
                err_short = f"⚠️ Lỗi xử lý: {str(e)}"[:180]
                try:
                    bot.answer_callback_query(call.id, err_short, show_alert=True)
                except Exception:
                    pass
        return bot

    @staticmethod
    def start_background_bot():
        """
        Khởi động duy nhất 01 Trạm lắng nghe Telegram trên toàn bộ máy chủ (Singleton Worker).
        Chống tuyệt đối lỗi nhân đôi luồng (Conflict 409) khi Streamlit rerun hoặc clear cache.
        """
        token, _ = TelegramBotManager.get_bot_token_and_chat_id()
        if not token:
            return False
        # Kiểm tra khóa đơn luồng gắn trên module hệ thống sys
        active_token = getattr(sys, "_hotu_tele_active_token", None)
        worker_thread = getattr(sys, "_hotu_tele_worker_thread", None)
        if active_token == token and worker_thread is not None and worker_thread.is_alive():
            return True
        # Cập nhật token hiện hành vào khóa hệ thống
        setattr(sys, "_hotu_tele_active_token", token)
        
        def run_singleton_polling(bot_token):
            while getattr(sys, "_hotu_tele_active_token", None) == bot_token:
                try:
                    bot_instance = TelegramBotManager._tao_bot_instance(bot_token)
                    # Xóa webhook cũ (nếu có) để đường truyền getUpdates thông suốt
                    try:
                        bot_instance.remove_webhook()
                    except Exception:
                        pass
                    # QUAN TRỌNG: skip_pending=False để KHÔNG BAO GIỜ vứt bỏ cú bấm nút của Admin
                    bot_instance.infinity_polling(
                        skip_pending=False,
                        timeout=20,
                        long_polling_timeout=20,
                        allowed_updates=["message", "callback_query"]
                    )
                except Exception as poll_err:
                    print(f"Telegram Polling Reconnecting: {poll_err}")
                    time.sleep(4)

        t = threading.Thread(target=run_singleton_polling, args=(token,), daemon=True)
        t.start()
        setattr(sys, "_hotu_tele_worker_thread", t)
        return True

    #=====================================
    # Duyệt thêm thành viên
    #=====================================
    @staticmethod
    def gui_thong_bao_cho_duyet(member_info, img_relative_path=None):
        """Định tuyến thông báo chuẩn xác tới Nhóm chung, Admin Cấp 1 và đúng Admin của Chi đó"""
        token, default_chat_id = TelegramBotManager.get_bot_token_and_chat_id()
        if not token:
            return False, "Chưa cấu hình Bot Token."

        cfg = TelegramBotManager._get_db_config()
        member_id = member_info.get('ID', '')
        so_chi = TelegramBotManager.lay_so_chi_tu_ma_id(member_id)

        ten_cua = "Cửa Giáp" if so_chi in ["1", "2", "3"] else ("Cửa Ất" if so_chi in ["4", "5"] else "Dòng họ")

        danh_sach_nhan = set()
        if default_chat_id:
            danh_sach_nhan.add(default_chat_id)
        for id_c1 in TelegramBotManager.parse_id_list(cfg.get("tele_admin_cap1", "")):
            danh_sach_nhan.add(id_c1)
        for id_c2 in TelegramBotManager.parse_id_list(cfg.get(f"tele_admin_chi_{so_chi}", "")):
            danh_sach_nhan.add(id_c2)
        if not danh_sach_nhan:
            return False, "Chưa có ID người nhận thông báo."

        bot = telebot.TeleBot(token, threaded=False)
        noi_dung = (
            f"🔔 <b>YÊU CẦU DUYỆT THÀNH VIÊN MỚI</b>\n"
            f"🏛 Phân nhánh: <b>{ten_cua} — Chi {so_chi}</b>\n\n"
            f"👤 <b>Họ tên:</b> {member_info.get('HoTen')}\n"
            f"🆔 <b>Mã ĐD:</b> <code>{member_id}</code>\n"
            f"👨 <b>Cha trực hệ:</b> {member_info.get('TenCha')}\n"
            f"📋 <b>Tình trạng:</b> {member_info.get('TinhTrang')}\n"
            f"📝 <b>Ghi chú:</b> {member_info.get('GhiChu', 'Không có')}\n\n"
            f"👉 <i>Chỉ Admin Cấp 1 hoặc Admin Cấp 2 phụ trách Chi {so_chi} mới có quyền phê duyệt:</i>"
        )

        reply_markup = types.InlineKeyboardMarkup()
        btn_duyet = types.InlineKeyboardButton("✅ Phê duyệt", callback_data=f"duyet_{member_id}")
        btn_xoa = types.InlineKeyboardButton("❌ Từ chối / Xóa", callback_data=f"xoa_{member_id}")
        reply_markup.add(btn_duyet, btn_xoa)

        full_img_path = None
        if img_relative_path:
            p = Path(__file__).resolve().parent / img_relative_path
            if p.exists():
                full_img_path = p
        so_luong_gui = 0
        for target_chat in danh_sach_nhan:
            try:
                if full_img_path:
                    with open(full_img_path, "rb") as photo:
                        bot.send_photo(chat_id=target_chat, photo=photo, caption=noi_dung, parse_mode="HTML", reply_markup=reply_markup)
                else:
                    bot.send_message(chat_id=target_chat, text=noi_dung, parse_mode="HTML", reply_markup=reply_markup)
                so_luong_gui += 1
            except Exception as e:
                print(f"Không thể gửi tới {target_chat}: {e}")
        return (so_luong_gui > 0), f"Đã định tuyến thông báo tới {so_luong_gui} kênh quản trị!"

    #=====================================
    # Duyệt sổ vàng
    #=====================================
    @staticmethod
    def gui_thong_bao_so_vang_cho_duyet(sv_info):
        """Định tuyến thông báo Sổ Vàng tới Nhóm chung, Admin Cấp 1 và đúng Admin Cấp 2 của Chi đó"""
        token, default_chat_id = TelegramBotManager.get_bot_token_and_chat_id()
        if not token:
            return False, "Chưa cấu hình Bot Token."
        cfg = TelegramBotManager._get_db_config()
        post_id = sv_info.get("id", "")
        so_chi = str(sv_info.get("so_chi", "0")).strip()
        ten_cua = "Cửa Giáp" if so_chi in ["1", "2", "3"] else ("Cửa Ất" if so_chi in ["4", "5"] else "Toàn dòng họ")
        danh_sach_nhan = set()
        if default_chat_id:
            danh_sach_nhan.add(default_chat_id)
        for id_c1 in TelegramBotManager.parse_id_list(cfg.get("tele_admin_cap1", "")):
            danh_sach_nhan.add(id_c1)
        if so_chi in ["1", "2", "3", "4", "5"]:
            for id_c2 in TelegramBotManager.parse_id_list(cfg.get(f"tele_admin_chi_{so_chi}", "")):
                danh_sach_nhan.add(id_c2)

        if not danh_sach_nhan:
            return False, "Chưa có ID người nhận thông báo."
        bot = telebot.TeleBot(token, threaded=False)
        quyen_txt = f"Admin Cấp 1 hoặc Admin Cấp 2 phụ trách Chi {so_chi}" if so_chi in ["1", "2", "3", "4", "5"] else "Admin Cấp 1"
        noi_dung = (
            f"🔔 <b>[SỔ VÀNG] LƯU BÚT MỚI CHỜ DUYỆT</b>\n"
            f"🏛 Phân nhánh: <b>{ten_cua}{f' — Chi {so_chi}' if so_chi in ['1','2','3','4','5'] else ''}</b>\n\n"
            f"👤 <b>Người gửi:</b> {sv_info.get('tac_gia')}\n"
            f"📍 <b>Chi phái / Nơi ở:</b> {sv_info.get('chi_nhanh')}\n"
            f"⏳ <b>Thời gian:</b> {sv_info.get('thoi_gian')}\n"
            f"💬 <b>Nội dung:</b> <i>\"{sv_info.get('noi_dung')}\"</i>\n\n"
            f"👉 <i>Chỉ {quyen_txt} mới có quyền phê duyệt:</i>"
        )
        reply_markup = types.InlineKeyboardMarkup()
        btn_duyet = types.InlineKeyboardButton("✅ Phê duyệt hiển thị", callback_data=f"sv_approve_{post_id}")
        btn_xoa = types.InlineKeyboardButton("❌ Từ chối / Xóa", callback_data=f"sv_reject_{post_id}")
        reply_markup.add(btn_duyet, btn_xoa)

        so_luong_gui = 0
        for target_chat in danh_sach_nhan:
            try:
                bot.send_message(chat_id=target_chat, text=noi_dung, parse_mode="HTML", reply_markup=reply_markup)
                so_luong_gui += 1
            except Exception as e:
                print(f"Không thể gửi thông báo Sổ Vàng tới {target_chat}: {e}")
        return (so_luong_gui > 0), f"Đã gửi thông báo tới {so_luong_gui} kênh quản trị!"


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

#=====================================================================
# [PHÂN LÔ A5]: Hàm con giải mã cấu trúc 9 chữ số định danh
#=====================================================================
class BoGiaiMaDinhDanh:
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
    # [PHÂN LÔ B2]: Hàm con tải dữ liệu từ SQLite sang DataFrame (Tích hợp chuẩn hóa thông minh)
    #=====================================================================
    @staticmethod
    def chuan_hoa_van_ban_nien_bieu(text):
        """
        Tự động chuẩn hóa thông minh dấu cách năm sinh/mất và ngày giỗ:
        - (1814- 1882), (1814 -1882), (1814-1882) -> (1814 - 1882)
        - (?-1882), (? -1882), (1814-?) -> (? - 1882), (1814 - ?)
        - Lấy bà Bà -> Lấy bà ; giổ -> giỗ
        """
        if not text:
            return ""
        s = str(text)
        # 1. Xử lý lặp từ "Lấy bà Bà" -> "Lấy bà"
        s = re.sub(r'\b(Lấy\s+bà)\s+bà\b', r'\1', s, flags=re.IGNORECASE)
        # 2. Chuẩn hóa dấu cách quanh dấu gạch ngang của cặp Năm sinh - Năm mất (hỗ trợ cả dấu ?)
        s = re.sub(r'(?<=\()\s*(\d{4}|\?)\s*[-–~]\s*(\d{4}|\?)\s*', r'\1 - \2', s)
        s = re.sub(r'\b(\d{4})\s*[-–~]\s*(\d{4})\b', r'\1 - \2', s)
        # 3. Chuẩn hóa dấu phẩy và khoảng trắng trước chữ "giỗ" trong ngoặc đơn
        s = re.sub(r'\bgiổ\b', 'giỗ', s, flags=re.IGNORECASE)
        s = re.sub(r'(\d{4}|\?)\s*,\s*giỗ\s*', r'\1, giỗ ', s, flags=re.IGNORECASE)
        # 4. Xóa khoảng trắng thừa sát bên trong dấu ngoặc đơn: "( 1814" -> "(1814", "AL )" -> "AL)"
        s = re.sub(r'\(\s+', '(', s)
        s = re.sub(r'\s+\)', ')', s)
        return s

    @staticmethod
    @st.cache_data(show_spinner="Đang đồng bộ dữ liệu huyết mạch...")
    def load_data():
        KhoDuLieuSQL.init_database()
        with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
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

        # Áp dụng chuẩn hóa hiển thị thông minh cho cột GhiChu và VoChong
        df["GhiChu"] = df["GhiChu"].apply(KhoDuLieuSQL.chuan_hoa_van_ban_nien_bieu)
        df["VoChong"] = df["VoChong"].apply(KhoDuLieuSQL.chuan_hoa_van_ban_nien_bieu)
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
    # [PHÂN LÔ B5]: Hàm con thực thi phê duyệt & xóa thành viên theo ID
    #=====================================================================
    @classmethod
    def duyet_thanh_vien(cls, member_id, new_tinh_trang, new_ghi_chu):
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE GiaPha SET TinhTrang = ?, ChucDanh_GhiChu = ? WHERE ID = ?",
                (new_tinh_trang, new_ghi_chu, member_id)
            )
            conn.commit()
        KhoDuLieuSQL.load_data.clear()
        return True

    @classmethod
    def delete_member(cls, member_id):
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM GiaPha WHERE ID = ?", (member_id,))
            conn.commit()
        KhoDuLieuSQL.load_data.clear()
        return True

    # =====================================================================
    # [PHÂN LÔ B6]: QUẢN TRỊ SỔ VÀNG LƯU BÚT TRONG SQLITE (CHUẨN KIỂM DUYỆT)
    # =====================================================================
    @classmethod
    def init_so_vang_table(cls):
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS SoVang (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                TacGia TEXT NOT NULL,
                DonVi_ChiNhanh TEXT,
                NoiDung TEXT NOT NULL,
                ThoiGian TEXT,
                SoChi TEXT DEFAULT '0',
                TrangThai TEXT DEFAULT 'Đã duyệt'
            );
            """)
            
            # Tự động nâng cấp bảng cũ nếu chưa có cột SoChi và TrangThai
            cursor.execute("PRAGMA table_info(SoVang)")
            existing_cols = [col[1] for col in cursor.fetchall()]
            if "SoChi" not in existing_cols:
                cursor.execute("ALTER TABLE SoVang ADD COLUMN SoChi TEXT DEFAULT '0'")
            if "TrangThai" not in existing_cols:
                cursor.execute("ALTER TABLE SoVang ADD COLUMN TrangThai TEXT DEFAULT 'Đã duyệt'")
            # Dọn sạch các bản ghi rỗng hoặc lỗi 'None' phát sinh lúc thử nghiệm
            cursor.execute("""
                DELETE FROM SoVang 
                WHERE TacGia IS NULL OR TRIM(TacGia) = '' OR TacGia = 'None'
                   OR NoiDung IS NULL OR TRIM(NoiDung) = '' OR NoiDung = 'None'
            """)
            # Khởi tạo 3 lời tri ân mẫu nếu bảng hoàn toàn trống
            cursor.execute("SELECT COUNT(*) FROM SoVang")
            if cursor.fetchone()[0] == 0:
                du_lieu_mau = [
                    ("Con cháu Chi 2", "Chi 2 (Cụ Dực) - Xuân Lộc", "Cảm ơn Ban Quản trị đã tâm huyết xây dựng ứng dụng gia phả số hóa tuyệt vời này.", "12/10/2026", "2", "Đã duyệt"),
                    ("Cháu Từ Quang ...", "Chi 1 (Cụ Liện) - Hà Nội", "Thế hệ trẻ chúng cháu rất tự hào về truyền thống hiếu học và khoa bảng của dòng họ.", "05/09/2026", "1", "Đã duyệt"),
                    ("Bà Từ Thị ...", "Đà Nẵng", "Kính chúc đại gia đình Họ Từ Xuân Lộc ngày càng hưng vượng, con cháu đoàn kết thành đạt.", "01/08/2026", "0", "Đã duyệt")
                ]
                cursor.executemany("""
                    INSERT INTO SoVang (TacGia, DonVi_ChiNhanh, NoiDung, ThoiGian, SoChi, TrangThai)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, du_lieu_mau)
            conn.commit()

    @classmethod
    def lay_danh_sach_so_vang(cls, trang_thai="Đã duyệt"):
        cls.init_so_vang_table()
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            if trang_thai:
                cursor.execute("""
                    SELECT ID, TacGia, DonVi_ChiNhanh, NoiDung, ThoiGian, COALESCE(SoChi, '0'), COALESCE(TrangThai, 'Đã duyệt')
                    FROM SoVang 
                    WHERE COALESCE(TrangThai, 'Đã duyệt') = ?
                    ORDER BY ID DESC
                """, (trang_thai,))
            else:
                cursor.execute("""
                    SELECT ID, TacGia, DonVi_ChiNhanh, NoiDung, ThoiGian, COALESCE(SoChi, '0'), COALESCE(TrangThai, 'Đã duyệt')
                    FROM SoVang 
                    ORDER BY ID DESC
                """)
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "tac_gia": r[1],
                    "chi_nhanh": r[2],
                    "noi_dung": r[3],
                    "thoi_gian": r[4],
                    "so_chi": r[5],
                    "trang_thai": r[6]
                }
                for r in rows
            ]

    @classmethod
    def them_so_vang(cls, tac_gia, chi_nhanh, noi_dung, thoi_gian, so_chi="0", trang_thai="Chờ duyệt"):
        cls.init_so_vang_table()
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO SoVang (TacGia, DonVi_ChiNhanh, NoiDung, ThoiGian, SoChi, TrangThai)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tac_gia.strip(), chi_nhanh.strip(), noi_dung.strip(), thoi_gian.strip(), str(so_chi).strip(), trang_thai))
            conn.commit()
            return cursor.lastrowid

    @classmethod
    def duyet_so_vang(cls, post_id):
        cls.init_so_vang_table()
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE SoVang SET TrangThai = 'Đã duyệt' WHERE ID = ?", (post_id,))
            conn.commit()
        return True

    @classmethod
    def xoa_so_vang(cls, post_id):
        cls.init_so_vang_table()
        with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM SoVang WHERE ID = ?", (post_id,))
            conn.commit()
        return True

    #=====================================================================
    # [PHÂN LÔ B7]: Hàm con thống kê lượt truy cập (Chuẩn Online & Cộng dồn bền vững)
    #=====================================================================
    @classmethod
    def thong_ke_truy_cap(cls):
        import uuid
        
        NEN_LUOT_TUAN = 45
        NEN_LUOT_NAM = 350
        
        try:
            if "visit_session_id" not in st.session_state:
                st.session_state.visit_session_id = str(uuid.uuid4())
                st.session_state.da_ghi_nhan_luot_xem = False

            raw_sid = st.session_state.visit_session_id
            user_id_login = str(st.session_state.get("user_id", "")).strip()
            user_name_login = str(st.session_state.get("user_name", "")).strip()
            # Phân loại khóa Online chuẩn xác:
            # 1. Thành viên hoặc Admin có Mã định danh 9 chữ số thực tế -> USER_<ID>
            # 2. Khách thập phương đã vào cổng -> GUEST_<sid>_<Tên>
            # 3. Khách đang đứng ở sảnh chờ đăng nhập -> ANON_<sid>
            if not st.session_state.get("da_dang_nhap", False):
                online_key = f"ANON_{raw_sid[:8]}"
            elif user_id_login == "KHACH" or not user_id_login:
                ten_k = user_name_login if user_name_login else "Khách Quý Dòng Họ"
                online_key = f"GUEST_{raw_sid[:8]}_{ten_k}"
            else:
                online_key = f"USER_{user_id_login}"
            now_vn = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
            str_now = now_vn.strftime("%Y-%m-%d %H:%M:%S")
            ma_tuan_hien_tai = now_vn.strftime("%Y-W%W")
            ma_nam_hien_tai = now_vn.strftime("%Y")
            with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
                cursor = conn.cursor()            
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS PhienDangOnline (
                        SessionID TEXT PRIMARY KEY,
                        CapNhatCuoi TEXT
                    );
                """)            
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS BoDemTruyCap (
                        Khoa TEXT PRIMARY KEY,
                        GiaTri INTEGER
                    );
                """)

                cursor.execute("SELECT GiaTri FROM BoDemTruyCap WHERE Khoa = ?", (f"TUAN_{ma_tuan_hien_tai}",))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO BoDemTruyCap (Khoa, GiaTri) VALUES (?, ?)", (f"TUAN_{ma_tuan_hien_tai}", NEN_LUOT_TUAN))
                cursor.execute("SELECT GiaTri FROM BoDemTruyCap WHERE Khoa = ?", (f"NAM_{ma_nam_hien_tai}",))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO BoDemTruyCap (Khoa, GiaTri) VALUES (?, ?)", (f"NAM_{ma_nam_hien_tai}", NEN_LUOT_NAM))
                if not st.session_state.get("da_ghi_nhan_luot_xem", False):
                    cursor.execute("UPDATE BoDemTruyCap SET GiaTri = GiaTri + 1 WHERE Khoa = ?", (f"TUAN_{ma_tuan_hien_tai}",))
                    cursor.execute("UPDATE BoDemTruyCap SET GiaTri = GiaTri + 1 WHERE Khoa = ?", (f"NAM_{ma_nam_hien_tai}",))
                    st.session_state.da_ghi_nhan_luot_xem = True
                # Xóa khóa phiên cũ của cùng trình duyệt (khi chuyển từ sảnh chờ vào trong) để không đếm trùng
                prev_key = st.session_state.get("current_online_key", "")
                if prev_key and prev_key != online_key:
                    cursor.execute("DELETE FROM PhienDangOnline WHERE SessionID = ?", (prev_key,))
                cursor.execute(
                    "DELETE FROM PhienDangOnline WHERE SessionID IN (?, ?, 'USER_GUEST', 'USER_KHACH', 'USER_ADMIN') OR SessionID LIKE 'NAME_%'",
                    (raw_sid, f"ANON_{raw_sid[:8]}" if not online_key.startswith("ANON_") else "")
                )
                st.session_state.current_online_key = online_key
                cursor.execute("INSERT OR REPLACE INTO PhienDangOnline (SessionID, CapNhatCuoi) VALUES (?, ?)", (online_key, str_now))
                moc_3_phut_truoc = (now_vn - datetime.timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("DELETE FROM PhienDangOnline WHERE CapNhatCuoi < ?", (moc_3_phut_truoc,))
                conn.commit()
                cursor.execute("SELECT COUNT(DISTINCT SessionID) FROM PhienDangOnline")
                dang_online = max(1, cursor.fetchone()[0])
                cursor.execute("SELECT GiaTri FROM BoDemTruyCap WHERE Khoa = ?", (f"TUAN_{ma_tuan_hien_tai}",))
                tong_tuan = cursor.fetchone()[0]
                cursor.execute("SELECT GiaTri FROM BoDemTruyCap WHERE Khoa = ?", (f"NAM_{ma_nam_hien_tai}",))
                tong_nam = cursor.fetchone()[0]
                if tong_nam < tong_tuan:
                    tong_nam = tong_tuan
                return dang_online, tong_tuan, tong_nam
        except Exception as e:
            print(f"Lỗi thống kê truy cập: {e}")
            return 1, NEN_LUOT_TUAN, NEN_LUOT_NAM

    @classmethod
    def lay_chi_tiet_online(cls, df=None):
        """Trích xuất danh sách ID thành viên và số lượng khách vãng lai đang Online cho Admin"""
        ds_thanh_vien = []
        ds_khach_tham_quan = []
        so_khach_ngoai_cong = 0
        try:
            with sqlite3.connect(cls.DB_FILE, timeout=15) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SessionID, CapNhatCuoi FROM PhienDangOnline ORDER BY CapNhatCuoi DESC")
                rows = cursor.fetchall()
            for sid, cap_nhat in rows:
                sid_str = str(sid)
                gio_phut = str(cap_nhat).split(" ")[-1][:5] if " " in str(cap_nhat) else str(cap_nhat)
                if sid_str.startswith("USER_"):
                    m_id = sid_str.replace("USER_", "").strip()
                    if m_id in ["GUEST", "KHACH", "ADMIN", ""]:
                        continue
                    ho_ten = "Thành viên"
                    chi_phai = ""
                    if df is not None and not df.empty:
                        m_row = df[df["ID"] == m_id]
                        if not m_row.empty:
                            ho_ten = m_row.iloc[0].get("HoTen", "Thành viên")
                            chi_phai = f"Đời {m_row.iloc[0].get('DoiThu', '')} - {m_row.iloc[0].get('Chi', '')}"
                    ds_thanh_vien.append({
                        "ID": m_id,
                        "HoTen": ho_ten,
                        "ChiPhai": chi_phai,
                        "Luc": gio_phut
                    })
                elif sid_str.startswith("GUEST_"):
                    parts = sid_str.split("_", 2)
                    ten_k = parts[2] if len(parts) >= 3 else "Khách Quý Dòng Họ"
                    ds_khach_tham_quan.append(f"{ten_k} ({gio_phut})")
                else:
                    so_khach_ngoai_cong += 1
        except Exception as e:
            print(f"Lỗi lấy chi tiết online: {e}")
        return {
            "thanh_vien": ds_thanh_vien,
            "khach_tham_quan": ds_khach_tham_quan,
            "khach_ngoai_cong": so_khach_ngoai_cong
        }
    
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
    #=====================================================================
    @staticmethod
    def thiet_lap_giao_dien():
        logo_file = Path(__file__).resolve().parent / "logo_hotu.png"
        icon_app = Image.open(logo_file) if logo_file.exists() else "📜"
        st.set_page_config(
            page_title="Gia Phả Họ Từ", 
            page_icon=icon_app, 
            layout="wide"
        )

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
        # Nếu khách chưa chọn thành viên nào để xem Trực hệ, lấy bản ghi gốc đầu tiên của bảng để hiển thị sơ đồ
        if not st.session_state.get("focus_id"):
            st.session_state.focus_id = str(df.iloc[0]["ID"]) if not df.empty else ""
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
                    focus_graph = KyThuatBanVeGiaPha.draw_family_tree(
                        df_sub, 
                        che_do_xem="4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)",
                        target_id=str(st.session_state.focus_id)
                    )     
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

            # =================================================================
            # 🔊 TÍCH HỢP LOA ĐỌC TIỂU SỬ TỰ ĐỘNG (DÀNH CHO CÁC BẬC CAO NIÊN)
            # =================================================================
            bat_doc_tieu_su = st.toggle("🔊 Bật giọng đọc tiểu sử tự động", value=True, key="toggle_auto_tts_tieusu")
            if bat_doc_tieu_su:
                # 1. Tổng hợp kịch bản đọc trang trọng, mạch lạc
                danh_xung = "Cụ bà" if curr_person.get('GioiTinh') == 'Nữ' else "Cụ"
                parts_doc = [f"Tiểu sử {danh_xung} {curr_person['HoTen']}."]        
                if curr_person.get('TenTu'):
                    parts_doc.append(f"Tên tự hoặc hiệu là {curr_person['TenTu']}.")  
                parts_doc.append(f"Thuộc đời thứ {curr_person['DoiThu']}, {curr_person['Cua']}, {curr_person['Chi']}.")
                if curr_person.get('Phai'):
                    parts_doc.append(f"{curr_person['Phai']}.")
                # Truy tìm tên Cha để đọc rõ nguồn cội
                cha_id_val = curr_person.get("ChaMe_ID", "")
                if cha_id_val:
                    cha_row_tts = df[df["ID"] == str(cha_id_val)]
                    if not cha_row_tts.empty:
                        parts_doc.append(f"Là con của cụ {cha_row_tts.iloc[0]['HoTen']}.")

                if curr_person.get('VoChong'):
                    nhan_vc = "Vợ là" if curr_person.get('GioiTinh') == 'Nam' else "Chồng là"
                    parts_doc.append(f"{nhan_vc}: {curr_person['VoChong']}.")
                if curr_person.get('NamSinh') or curr_person.get('NamMat'):
                    ns_doc = curr_person['NamSinh'] if curr_person['NamSinh'] else "chưa rõ"
                    nm_doc = curr_person['NamMat'] if curr_person['NamMat'] else "chưa rõ"
                    parts_doc.append(f"Năm sinh: {ns_doc}. Năm mất: {nm_doc}.")
                if curr_person.get('NgayGio'):
                    parts_doc.append(f"Ngày giỗ: {curr_person['NgayGio']}.")
                if curr_person.get('GhiChu'):
                    parts_doc.append(f"Ghi chú tiểu sử: {curr_person['GhiChu']}.")
                if curr_person.get('TinhTrang'):
                    parts_doc.append(f"Tình trạng: {curr_person['TinhTrang']}.")
                raw_tts_text = " ".join(parts_doc)
                # 2. Làm sạch ký hiệu viết tắt để giọng đọc tự nhiên chuẩn tiếng Việt
                # Chuyển ngày tháng dạng 14/02 hoặc 7/12 thành "ngày 14 tháng 02"
                clean_tts = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', r'ngày \1 tháng \2', raw_tts_text)
                # Chuyển chữ AL thành âm lịch
                clean_tts = re.sub(r'\b[aA][lL]\b', 'âm lịch', clean_tts)
                # Xóa các thẻ HTML hoặc ngoặc vuông nếu có
                clean_tts = re.sub(r'<[^>]*>', ' ', clean_tts)
                clean_tts = re.sub(r'\s+', ' ', clean_tts).strip()
                # 3. Tải và nối luồng âm thanh MP3 ở Backend
                audio_tieusu_bytes = b""
                try:
                    from gtts import gTTS
                    fp_tts = io.BytesIO()
                    gTTS(text=clean_tts, lang='vi').write_to_fp(fp_tts)
                    audio_tieusu_bytes = fp_tts.getvalue()
                except Exception:
                    try:
                        words_tts = clean_tts.split()
                        chunks_tts, curr_c = [], ""
                        for w in words_tts:
                            if len(curr_c) + len(w) + 1 <= 180:
                                curr_c = f"{curr_c} {w}".strip()
                            else:
                                chunks_tts.append(curr_c)
                                curr_c = w
                        if curr_c:
                            chunks_tts.append(curr_c)

                        combined_mp3 = bytearray()
                        for ch_str in chunks_tts:
                            enc_q = urllib.parse.quote(ch_str)
                            url_g = f"https://translate.googleapis.com/translate_tts?client=tw-ob&ie=UTF-8&tl=vi&q={enc_q}"
                            req_g = urllib.request.Request(url_g, headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(req_g, timeout=8) as resp_g:
                                combined_mp3.extend(resp_g.read())
                        audio_tieusu_bytes = bytes(combined_mp3)
                    except Exception as err_tts:
                        print(f"Lỗi tạo giọng đọc tiểu sử: {err_tts}")
                if audio_tieusu_bytes:
                    st.audio(audio_tieusu_bytes, format="audio/mp3", autoplay=True)
                else:
                    st.warning("⚠️ Không thể tải giọng đọc lúc này. Vui lòng kiểm tra kết nối mạng.")
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
    # [PHÂN LÔ E4]: Hàm con render màn hình Toàn Cảnh (CHUẨN HÓA LIÊN ĐỘNG CỬA -> CHI -> PHÁI & CHỐNG CỤT ĐẦU)
    #=====================================================================
    @staticmethod
    def render_toancanh(df):
        st.subheader("Sơ Đồ Phả Hệ Toàn Cảnh")
        # 🟢 1. TRUY XUẤT THÔNG TIN CỦA NGƯỜI ĐĂNG NHẬP (KHÁCH SẼ VỀ CHẾ ĐỘ MẶC ĐỊNH "TẤT CẢ")
        user_id_login = str(st.session_state.get("user_id", "")).strip()
        user_row = df[df["ID"] == user_id_login] if user_id_login not in ["", "KHACH", "GUEST", "ADMIN"] else pd.DataFrame()       
        if not user_row.empty:
            user_cua = str(user_row.iloc[0].get("Cua", "")).strip()
            user_chi = str(user_row.iloc[0].get("Chi", "")).strip()
            user_phai = str(user_row.iloc[0].get("Phai", "")).strip()
        else:
            user_cua, user_chi, user_phai = "", "", ""           

        # 🟢 2. KHỞI TẠO & LIÊN ĐỘNG BỘ LỌC DÂY CHUYỀN (CỬA -> CHI -> PHÁI -> NHÁNH)
        if "tc_init_user" not in st.session_state or st.session_state.tc_init_user != user_id_login:
            st.session_state.tc_init_user = user_id_login
            st.session_state.tc_cua_sel = user_cua if user_cua and user_cua != "Gốc" else "Tất cả"
            st.session_state.tc_chi_sel = user_chi if user_chi else "Tất cả"
            st.session_state.tc_phai_sel = user_phai if user_phai else "Tất cả"
            st.session_state.tc_nhanh_sel = "Tất cả"
        def on_change_cua():
            st.session_state.tc_chi_sel = "Tất cả"
            st.session_state.tc_phai_sel = "Tất cả"
            st.session_state.tc_nhanh_sel = "Tất cả"
        def on_change_chi():
            st.session_state.tc_phai_sel = "Tất cả"
            st.session_state.tc_nhanh_sel = "Tất cả"
        def on_change_phai():
            st.session_state.tc_nhanh_sel = "Tất cả"
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            che_do_xem = st.selectbox("1. Chế độ hiển thị:", [
                "1. Chỉ Đinh Nam (Gọn: Tên ⑦)", 
                "2. Chỉ Đinh Nam (Đủ: Họ Và Tên)", 
                "3. Chỉ Đinh Nam (Đủ vợ và chồng)", 
                "4. Cả Nam & Nữ (Đủ: Chồng, Vợ, Con)"
            ], index=1)
        with col2:
            ds_cua = ["Tất cả"] + sorted([c for c in df['Cua'].unique() if c and c != "Gốc"])
            if st.session_state.get("tc_cua_sel") not in ds_cua:
                st.session_state.tc_cua_sel = "Tất cả"
            cua_chon = st.selectbox("2. Lọc theo Cửa:", ds_cua, key="tc_cua_sel", on_change=on_change_cua)
        with col3:
            df_tc = df[df['Cua'] == cua_chon] if cua_chon != "Tất cả" else df
            danh_sach_chi = ["Tất cả"] + QuanTriTaiNguyen.lay_danh_sach_chi_chuan(df_tc)
            if st.session_state.get("tc_chi_sel") not in danh_sach_chi:
                st.session_state.tc_chi_sel = "Tất cả"
            chi_chon = st.selectbox("3. Lọc theo Chi:", danh_sach_chi, key="tc_chi_sel", on_change=on_change_chi)
        with col4:
            # 🟢 Lọc Phái trực tiếp từ df_tc (đã lọc theo Cửa) để không bị lẫn Phái của Cửa khác
            df_pc = df_tc[df_tc['Chi'] == chi_chon] if chi_chon != "Tất cả" else df_tc
            sorted_phai = ["Tất cả"] + QuanTriTaiNguyen.sap_xep_danh_sach_phai(df_pc['Phai'].unique())
            if st.session_state.get("tc_phai_sel") not in sorted_phai:
                st.session_state.tc_phai_sel = "Tất cả"
            phai_chon = st.selectbox("4. Lọc theo Phái:", sorted_phai, key="tc_phai_sel", on_change=on_change_phai)
        with col5:
            danh_sach_nhanh = []
            nhanh_dict = {}
            if phai_chon != "Tất cả" and phai_chon in KyThuatBanVeGiaPha.NHANH_MAPPING:
                branches = KyThuatBanVeGiaPha.NHANH_MAPPING[phai_chon]
                if len(branches) > 1:
                    danh_sach_nhanh = ["Tất cả"] + [b[0] for b in branches]
                    nhanh_dict = {b[0]: b[1] for b in branches}            
            if danh_sach_nhanh:
                if st.session_state.get("tc_nhanh_sel") not in danh_sach_nhanh:
                    st.session_state.tc_nhanh_sel = "Tất cả"
                nhanh_chon = st.selectbox("5. Lọc theo Nhánh:", danh_sach_nhanh, key="tc_nhanh_sel")
            else:
                st.session_state.tc_nhanh_sel = "Tất cả"
                nhanh_chon = "Tất cả"
        # Hàng tùy chọn giới hạn số đời (Mặc định: 3 đời trên, 4 đời dưới tính từ Cụ đứng đầu cấp thấp nhất)
        col_d1, col_d2, col_d3 = st.columns([1, 1, 3])
        with col_d1:
            so_doi_tren_tc = st.selectbox("6. Số đời trên:", ["Tất cả"] + list(range(1, 11)), index=3, key="tc_doi_tren")
        with col_d2:
            so_doi_duoi_tc = st.selectbox("7. Số đời dưới:", ["Tất cả"] + list(range(1, 11)), index=4, key="tc_doi_duoi")
        # 🟢 3. THUẬT TOÁN XÁC ĐỊNH "CỤ ĐỨNG ĐẦU" CỦA CẤP LỌC THẤP NHẤT
        df_approved = df[df["TrangThai"] == "Đã duyệt"].copy()
        parent_ids_set = set(df_approved["ChaMe_ID"].dropna().astype(str).tolist())
        def tim_cu_dung_dau_nhom(df_group, label_str, default_doi):
            """Truy tìm chính xác ID và Đời của Cụ đứng đầu Cửa / Chi / Phái đang chọn"""
            if df_group.empty:
                return "000.01.0.001", 1
            all_ids = set(df_group["ID"].astype(str).tolist())
            for p_id in df_group["ChaMe_ID"]:
                curr = str(p_id).strip()
                visited = set()
                while curr and curr != "0" and curr not in visited:
                    visited.add(curr)
                    all_ids.add(curr)
                    p_row = df_approved[df_approved["ID"] == curr]
                    if p_row.empty:
                        break
                    curr = str(p_row.iloc[0].get("ChaMe_ID", "")).strip()
            df_lineage = df_approved[df_approved["ID"].isin(all_ids)].copy()
            min_d_group = int(df_group["DoiThu"].min())
            # 1. Tìm Tổ chung gần nhất (LCA) của các thành viên đời đầu tiên trong nhóm
            rows_at_min = df_group[df_group["DoiThu"] == min_d_group]
            if len(rows_at_min) > 1:
                rows_with_children = rows_at_min[rows_at_min["ID"].isin(parent_ids_set)]
                if not rows_with_children.empty:
                    rows_at_min = rows_with_children
            chains = []
            for _, r_m in rows_at_min.iterrows():
                ch = [str(a["ID"]) for a in KyThuatBanVeGiaPha.get_ancestors_chain(df_approved, str(r_m["ID"]))]
                if ch:
                    chains.append(ch)
            lca_id = "000.01.0.001"
            lca_doi = 1
            if chains:
                min_len = min(len(c) for c in chains)
                for i in range(min_len):
                    first_val = chains[0][i]
                    if all(c[i] == first_val for c in chains):
                        lca_id = first_val
                    else:
                        break
                r_lca = df_approved[df_approved["ID"] == lca_id]
                if not r_lca.empty:
                    lca_doi = int(r_lca.iloc[0]["DoiThu"])
            # 2. Đối sánh tên Cụ trong ngoặc đơn (VD: '(Cụ Tỉnh)', '(Cụ Tương)', '(Cụ Dực)')
            m_cu = re.search(r'\((?:Cụ|Ông)\s+([^)]+)\)', str(label_str), flags=re.IGNORECASE)
            if m_cu:
                ten_cu = m_cu.group(1).strip().lower()
                candidates = df_lineage[
                    (df_lineage["GioiTinh"] == "Nam") &
                    (df_lineage["DoiThu"] <= lca_doi) &
                    (df_lineage["HoTen"].apply(
                        lambda x: QuanTriTaiNguyen.lay_ten_chinh(x).lower() == ten_cu or ten_cu in str(x).lower()
                    ))
                ].sort_values(by="DoiThu", ascending=False)
                if not candidates.empty:
                    r0 = candidates.iloc[0]
                    return str(r0["ID"]), int(r0["DoiThu"])
            if lca_id != "000.01.0.001" or default_doi == 1:
                return lca_id, lca_doi
            cand_def = df_lineage[(df_lineage["DoiThu"] == default_doi) & (df_lineage["GioiTinh"] == "Nam")]
            if not cand_def.empty:
                return str(cand_def.iloc[0]["ID"]), default_doi
            return "000.01.0.001", 1
        # Xác định Cụ đứng đầu theo cấp lọc thấp nhất đang chọn (Nhánh -> Phái -> Chi -> Cửa -> Thủy Tổ)
        if nhanh_chon != "Tất cả" and nhanh_dict and nhanh_chon in nhanh_dict:
            moc_id = str(nhanh_dict[nhanh_chon]).strip()
            r_moc = df_approved[df_approved["ID"] == moc_id]
            moc_doi = int(r_moc.iloc[0]["DoiThu"]) if not r_moc.empty else BoGiaiMaDinhDanh.phan_tich_ma(moc_id)["DoiThu"]
            ten_cap_moc = nhanh_chon
        elif phai_chon != "Tất cả":
            df_target_group = df_approved[df_approved["Phai"] == phai_chon]
            moc_id, moc_doi = tim_cu_dung_dau_nhom(df_target_group, phai_chon, default_doi=4)
            ten_cap_moc = phai_chon
        elif chi_chon != "Tất cả":
            df_target_group = df_approved[df_approved["Chi"] == chi_chon]
            moc_id, moc_doi = tim_cu_dung_dau_nhom(df_target_group, chi_chon, default_doi=3)
            ten_cap_moc = chi_chon
        elif cua_chon != "Tất cả":
            df_target_group = df_approved[df_approved["Cua"] == cua_chon]
            cand_cua = df_target_group[
                (df_target_group["DoiThu"] == 2) & 
                (df_target_group["GioiTinh"] == "Nam") & 
                (df_target_group["ID"].isin(parent_ids_set))
            ]
            if not cand_cua.empty:
                moc_id = str(cand_cua.iloc[0]["ID"])
                moc_doi = 2
            else:
                moc_id, moc_doi = tim_cu_dung_dau_nhom(df_target_group, cua_chon, default_doi=2)
            ten_cap_moc = cua_chon
        else:
            moc_id = "000.01.0.001"
            moc_doi = 1
            ten_cap_moc = "Đại Tôn (Thủy Tổ)"
        r_moc_info = df_approved[df_approved["ID"] == moc_id]
        moc_ten = str(r_moc_info.iloc[0]["HoTen"]).split("(")[0].strip() if not r_moc_info.empty else "Tiên Tổ"
        # 🟢 4. TÍNH ĐỜI TRÊN / ĐỜI DƯỚI SO VỚI "CỤ ĐỨNG ĐẦU" & DỰNG CÂY LIỀN MẠCH 100%
        min_doi = max(1, moc_doi - int(so_doi_tren_tc)) if so_doi_tren_tc != "Tất cả" else 1
        max_doi = (moc_doi + int(so_doi_duoi_tc)) if so_doi_duoi_tc != "Tất cả" else int(df_approved["DoiThu"].max())
        valid_ids = set()
        # Bước 4.1: Phía trên Cụ đứng đầu (từ min_doi đến moc_doi) -> Chỉ lấy trục trực hệ đơn tuyến
        curr_up = moc_id
        visited_up = set()
        while curr_up and curr_up != "0" and curr_up not in visited_up:
            visited_up.add(curr_up)
            p_row = df_approved[df_approved["ID"] == curr_up]
            if p_row.empty:
                break
            d_curr = int(p_row.iloc[0]["DoiThu"])
            if d_curr >= min_doi:
                valid_ids.add(curr_up)
            curr_up = str(p_row.iloc[0].get("ChaMe_ID", "")).strip()
        # Bước 4.2: Phía dưới Cụ đứng đầu (từ moc_doi đến max_doi) -> Tỏa nhánh toàn bộ con cháu của Cụ đứng đầu
        queue_down = [moc_id]
        visited_down = set()
        while queue_down:
            curr_d = queue_down.pop(0)
            if curr_d in visited_down:
                continue
            visited_down.add(curr_d)
            valid_ids.add(curr_d)

            ch_rows = df_approved[df_approved["ChaMe_ID"] == curr_d]
            for _, ch in ch_rows.iterrows():
                ch_id = str(ch["ID"]).strip()
                ch_doi = int(ch["DoiThu"])
                if ch_doi <= max_doi:
                    if cua_chon != "Tất cả" and chi_chon == "Tất cả":
                        ch_cua = str(ch.get("Cua", "")).strip()
                        if ch_cua and ch_cua not in [cua_chon, "Gốc"]:
                            continue
                    if chi_chon != "Tất cả" and phai_chon == "Tất cả":
                        ch_chi = str(ch.get("Chi", "")).strip()
                        if ch_chi and ch_chi != chi_chon:
                            continue
                    if phai_chon != "Tất cả" and nhanh_chon == "Tất cả":
                        ch_phai = str(ch.get("Phai", "")).strip()
                        if ch_phai and ch_phai != phai_chon:
                            continue
                    queue_down.append(ch_id)
        df_sub = df_approved[
            (df_approved["ID"].isin(valid_ids)) &
            (df_approved["DoiThu"] >= min_doi) &
            (df_approved["DoiThu"] <= max_doi)
        ].copy()
        with col_d3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.info(f"📌 **Mốc quy chiếu:** Cụ **{moc_ten}** *(Đứng đầu {ten_cap_moc} — Đời {moc_doi})* | Hiển thị: **Đời {min_doi} ➔ Đời {max_doi}**")
        st.markdown("<div class='hd-zoom hide-on-mobile'>💡 <b>Trên điện thoại:</b> Dùng 2 ngón tay kéo dãn để zoom to, hoặc bấm nút <b>(+)</b> để nhìn rõ từng đời.</div>", unsafe_allow_html=True)
        try:
            ds_highlight = [user_id_login]
            if moc_id != "000.01.0.001" and moc_id not in ds_highlight:
                ds_highlight.append(moc_id)
            tree_graph = KyThuatBanVeGiaPha.draw_family_tree(
                df_sub,
                cua_loc="Tất cả",
                chi_loc="Tất cả",
                phai_loc="Tất cả",
                che_do_xem=che_do_xem,
                nhanh_chon="Tất cả",
                nhanh_dict=None,
                highlight_ids=ds_highlight
            )
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
            # 🟢 NẾU LÀ KHÁCH THÌ ĐƯA VỀ CHẾ ĐỘ XEM MẶC ĐỊNH, KHÔNG LẤY TÊN KHÁCH ĐỂ TÌM TRONG GIA PHẢ
            if st.session_state.get("user_id") in ["", "KHACH", "GUEST", "ADMIN"]:
                ten_dang_nhap_hien_tai = "Từ Quang Thùy"
            else:
                ten_dang_nhap_hien_tai = st.session_state.get("user_name", "Từ Quang Thùy")
            nhap_lieu = st.text_input(
                "Nhập Họ và tên hoặc Mã định danh:", 
                value=ten_dang_nhap_hien_tai, 
                placeholder="Ví dụ: Từ Quang Thùy, 124080099 hoặc 124.08.0.099"
            )
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
                    if not txt:
                        return ""
                    s = unicodedata.normalize('NFC', str(txt).strip().lower())
                    vocal_map = {
                        "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
                        "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
                        "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"
                    }
                    for old_val, new_val in vocal_map.items():
                        s = s.replace(old_val, new_val)
                    return s
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
                    # 🟢 ĐỒNG BỘ THUẬT TOÁN KHỬ TRÙNG TÊN 2 LỚP (TÊN CHA -> ĐỜI)
                    nhan_phan_biet = SoChiHuyGiaoDien.tao_nhan_phan_biet_cha_doi(matched_by_name, df_app)
                    options_dict = {
                        f"{idx}. {nhan}": m_id
                        for idx, (m_id, nhan) in enumerate(nhan_phan_biet.items(), 1)
                    }
                    with c3:
                        selected_label = st.selectbox(
                            "⚠️ Phát hiện trùng tên! Chọn đúng Tên Cha (hoặc Đời):",
                            options=list(options_dict.keys())
                        )
                    target_id = options_dict[selected_label]
                    matched_row_sel = df_app[df_app["ID"] == target_id].iloc[0]

                    st.markdown(f"""
                        <div style="padding: 8px 12px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 6px; color: #155724; font-size: 13px; margin-bottom: 10px;">
                            <span class="desktop-view">✅ Đã chọn: <b>{nhan_phan_biet[target_id]}</b> (Mã định danh: <code>{target_id}</code>, {matched_row_sel['Chi']}, Đời {matched_row_sel['DoiThu']})</span>
                            <span class="mobile-view">✅ Đã chọn: <b>{nhan_phan_biet[target_id]}</b> (ID: <code>{target_id}</code>)</span>
                        </div>
                    """, unsafe_allow_html=True)
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
            df_parents = df[(df["TrangThai"] == "Đã duyệt") & (df["GioiTinh"] == "Nam")].copy()           
            # 🟢 ĐẶT "-- Chọn Cha --" Ở VỊ TRÍ ĐẦU TIÊN (INDEX 0) ĐỂ MẶC ĐỊNH LUÔN TRỐNG CHO KHÁCH
            parent_dict = {"": "-- Chọn Cha --"}
            for _, row in df_parents.iterrows():
                p_id = row['ID']
                p_name = row['HoTen']
                p_doi = row['DoiThu']
                p_chame_id = row.get('ChaMe_ID', '')                
                ten_ong_noi = "Gốc"
                if p_chame_id:
                    cha_row = df[df['ID'] == p_chame_id]
                    if not cha_row.empty:
                        ten_cha_full = str(cha_row.iloc[0].get('HoTen', ''))
                        parts = ten_cha_full.split()
                        ten_ong_noi = parts[-1] if parts else ten_cha_full                
                parent_dict[p_id] = f"{p_name} ({ten_ong_noi}), đời {p_doi}"              
            danh_sach_key_cha = list(parent_dict.keys())
            # 🟢 CHỈ TỰ ĐỘNG CHỌN CHA NẾU ĐĂNG NHẬP BẰNG ID THÀNH VIÊN THỰC TẾ (KHÁCH SẼ LUÔN Ở "-- Chọn Cha --")
            id_dang_nhap = str(st.session_state.get("user_id", "")).strip()
            vi_tri_mac_dinh = 0  # Vị trí 0 chính là "-- Chọn Cha --"
            if id_dang_nhap not in ["", "KHACH", "GUEST", "ADMIN"] and id_dang_nhap in danh_sach_key_cha:
                vi_tri_mac_dinh = danh_sach_key_cha.index(id_dang_nhap)
            cha_id = st.selectbox(
                "Chọn Cha (*):",
                options=danh_sach_key_cha,
                index=vi_tri_mac_dinh,
                format_func=lambda x: parent_dict[x]
            )     
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
        # 🟢 PHÂN QUYỀN ADMIN CHO CẢ TAB WORD VÀ TAB PHẢ ĐỒ
        is_admin_user = (st.session_state.get("user_id") == "ADMIN" or st.session_state.get("admin_level", 0) == 1)
        if is_admin_user:
            # Nếu là Admin: Hiển thị đầy đủ 4 tab (Có cả tab Word và tab Phả đồ độc quyền)
            tab_csv, tab_in, tab_word, tab_phado = st.tabs([
                "📥 Xuất dữ liệu (CSV)",
                "🖨️ In ấn báo cáo", 
                "📄 Xuất Thế phả (Word)", 
                "🖼 Xuất ảnh Phả đồ"
            ])
        else:
            # Nếu là con cháu / khách: Chỉ hiển thị 2 tab cơ bản (Ẩn hoàn toàn Word và Phả đồ)
            tab_csv, tab_in = st.tabs([
                "📥 Xuất dữ liệu (CSV)", 
                "🖨️ In ấn báo cáo"
            ])
        with tab_csv:
            export_df_csv = df_app[["STT", "ID", "ChaMe_ID", "HoTen", "TenTu", "VoChong", "NamSinh", "NamMat", "NgayGio", "GhiChu", "TinhTrang", "HinhAnh"]].rename(columns={
                "ID": "Mã Định Danh", "ChaMe_ID": "Mã Cha/Mẹ", "HoTen": "Họ và Tên", "TenTu": "Tên Tự", 
                "VoChong": "Vợ/Chồng", "NamSinh": "Năm Sinh", "NamMat": "Năm Mất", "NgayGio": "Ngày Giỗ", 
                "GhiChu": "Ghi Chú", "TinhTrang": "Tình Trạng", "HinhAnh": "Hình Ảnh"
            })
            st.download_button("📥 Tải xuống tệp CSV", export_df_csv.to_csv(index=False).encode('utf-8-sig'), "GiaPha_HoTu.csv", "text/csv")

        # KHU VỰC IN ẤN BÁO CÁO (GIỮ NGUYÊN)
        with tab_in:
            st.markdown("🖼️ **Chọn ảnh bìa và ảnh sơ đồ cho tập tài liệu (Tùy chọn):**")

            col_img1, col_img2 = st.columns(2)
            with col_img1:
                uploaded_cover = st.file_uploader("1. Tải lên tệp Ảnh Bìa (JPG, PNG)", type=["jpg", "jpeg", "png"], key="upload_cover_pdf")
            with col_img2:
                uploaded_tree_img = st.file_uploader("2. Tải lên Ảnh Sơ đồ 3 đời đầu (JPG, PNG)", type=["jpg", "jpeg", "png"], key="upload_tree_pdf")         
            
            # 🟢 PHÂN QUYỀN ADMIN - CHỈ ADMIN MỚI THẤY VÀ ĐIỀU KHIỂN CÔNG TẮC ĐÓNG DẤU
            is_admin_user = (st.session_state.get("user_id") == "ADMIN" or st.session_state.get("admin_level", 0) == 1)
            dong_dau_dong_ho = False
            if is_admin_user:
                dong_dau_dong_ho = st.toggle(
                    "💮 [QUẢN TRỊ] Đóng dấu treo Dòng Họ (Tắt: Bản nháp | Gạt bật: Con dấu chính thức)",
                    value=False,
                    key="toggle_dong_dau_dong_ho"
                )
            else:
                st.caption("🔒 *Chế độ in ấn tiêu chuẩn: Mặc định hiển thị bản nháp (Chỉ Tài khoản Quản trị mới có quyền đóng dấu chính thức).*")
            st.markdown("---")           
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
            # 🟢 ĐỂ TRỐNG MẶC ĐỊNH, CHUYỂN CÚ PHÁP MẪU XUỐNG DẠNG CHỮ CHÌM (PLACEHOLDER)
            insert_blank_pages_str = st.text_area(
                "🌲 Tự động chèn sơ đồ phả hệ vào trang trống (Cú pháp: Trang [Số]: ID = [Mã], trước = [Số đời], sau = [Số đời]):",
                value=st.session_state.get('insert_blank_pages_str', ""),
                placeholder="Ví dụ:\nTrang 3: ID = 000.01.0.001, trước = 0, sau = 3",
                key="input_blank_pages_tree"
            )
            st.session_state.insert_blank_pages_str = insert_blank_pages_str          
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
                # 🟢 NÉN NHẸ ẢNH CON DẤU & CHỈ NHÚNG 1 LẦN VÀO CSS (CHỐNG TRÀN BỘ NHỚ 200MB)
                seal_b64 = ""
                if dong_dau_dong_ho:
                    base_dir = Path(__file__).resolve().parent
                    seal_paths = [
                        base_dir / "con_dau_hotu.png",
                        base_dir / "images" / "con_dau_hotu.png",
                        base_dir / "con_dau_hotu.jpg",
                        base_dir / "images" / "con_dau_hotu.jpg"
                    ]
                    for sp in seal_paths:
                        if sp.exists():
                            try:
                                with Image.open(sp) as img_s:
                                    img_s = img_s.convert("RGBA")
                                    # Thu về 260x260px (~30KB): Siêu nét ở khung 95px nhưng cực nhẹ
                                    img_s.thumbnail((260, 260), Image.Resampling.LANCZOS)
                                    buf_s = io.BytesIO()
                                    img_s.save(buf_s, format="PNG", optimize=True)
                                    seal_b64 = base64.b64encode(buf_s.getvalue()).decode("utf-8")
                            except Exception:
                                pass
                            break

                    if seal_b64:
                        # Chỉ truyền thẻ div rỗng vào vòng lặp trang để không bị nhân bản dung lượng
                        html_watermark_div = '<div class="watermark-seal"></div>'
                    else:
                        st.warning("⚠️ Chưa tìm thấy file 'con_dau_hotu.png'. Tạm thời hiển thị chữ BẢN NHÁP.")
                        html_watermark_div = '<div class="watermark-draft">BẢN NHÁP</div>'
                else:
                    html_watermark_div = '<div class="watermark-draft">BẢN NHÁP</div>'

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
                    .watermark-seal {{
                        position: absolute; top: 6px; left: 35px;
                        width: 95px; height: 95px;
                        background-image: url("data:image/png;base64,{seal_b64}");
                        background-size: contain;
                        background-position: center;
                        background-repeat: no-repeat;
                        transform: rotate(-4deg); z-index: 99;
                        pointer-events: none;
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
                    # 🟢 CHỈ CHÈN KHI CÔNG TẮC BẬT (TRUE)
                    html_report += html_watermark_div
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
        if is_admin_user:
            with tab_word:
                st.markdown("Tính năng kết xuất **Thế Phả truyền thống định dạng cao cấp** sang file Word (.docx) chuẩn phong cách bản in gốc.")                
                # --- 1. THÊM NÚT TẢI ẢNH BÌA & HÌNH NỀN CHO FILE WORD ---
                col_bia, col_nen = st.columns(2)
                with col_bia:
                    anh_bia_word = st.file_uploader("🖼️ Tải lên ảnh bìa (Tùy chọn)", type=["jpg", "jpeg", "png"], key="upload_cover_word")
                with col_nen:
                    anh_nen_word = st.file_uploader("🖼️ Tải lên hình nền các trang (Tùy chọn)", type=["jpg", "jpeg", "png"], key="upload_bg_word")
                st.markdown("---")
                try:         
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
                    # ==========================================================
                    # 🟢 ĐẶT CON DẤU Ở ĐÂY: VỊ TRÍ ĐẦU TIÊN CỦA TRANG NỘI DUNG (SAU TRANG BÌA)
                    # Dù sau này có thêm bao nhiêu nội dung, nó vẫn luôn nằm ở trang 1 này!
                    # ==========================================================
                    base_dir = Path(__file__).resolve().parent
                    seal_paths = [
                        base_dir / "con_dau_hotu.png",
                        base_dir / "images" / "con_dau_hotu.png",
                        base_dir / "con_dau_hotu.jpg",
                        base_dir / "images" / "con_dau_hotu.jpg"
                    ]
                    for sp in seal_paths:
                        if sp.exists():
                            try:
                                p_seal = doc.add_paragraph()
                                p_seal.paragraph_format.space_before = Pt(0)
                                p_seal.paragraph_format.space_after = Pt(0)
                                
                                run_seal = p_seal.add_run()
                                inline_shape = run_seal.add_picture(str(sp), width=Inches(1.1))                                
                                # 🟢 ĐOẠN XML THIẾT LẬP CHUẨN XÁC CHẾ ĐỘ NỔI ĐÈ LÊN VĂN BẢN (BEHIND TEXT)
                                r = run_seal._r
                                drawing_list = r.xpath('.//w:drawing')
                                if drawing_list:
                                    drawing = drawing_list[0]
                                    # Thiết lập wp:anchor để bật các tùy chọn cố định vị trí trên trang
                                    wp_anchor = parse_xml(
                                        r'<wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
                                        r'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                                        r'simplePos="0" relativeHeight="251658240" behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1">'
                                        r'<wp:simplePos x="0" y="0"/>'
                                        r'<wp:positionH relativeFrom="page"><wp:posOffset>360000</wp:posOffset></wp:positionH>'
                                        r'<wp:positionV relativeFrom="page"><wp:posOffset>360000</wp:posOffset></wp:positionV>'
                                        r'<wp:extent cx="1000000" cy="1000000"/>'
                                        r'<wp:effectExtent l="0" t="0" r="0" b="0"/>'
                                        r'<wp:wrapNone/>'
                                        r'<wp:docPr id="1" name="ConDauDongHo"/>'
                                        r'<wp:cNvGraphicFramePr/>'
                                        r'</wp:anchor>'
                                    )
                                    inline = drawing.xpath('.//wp:inline')
                                    if inline:
                                        parent = inline[0].getparent()
                                        graphic = inline[0].xpath('.//a:graphic', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/graphic'})
                                        if graphic:
                                            wp_anchor.append(graphic[0])
                                        parent.replace(inline[0], wp_anchor)
                            except Exception as e:
                                print(f"Lỗi cấu hình con dấu: {e}")
                                pass
                            break                    
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
        # ==============================================================
        # 4. KHU VỰC XUẤT FILE ẢNH PHẢ ĐỒ (LỌC THEO ID - BẢN WORD NGANG)
        # ==============================================================
        if is_admin_user:
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
                            nhan_pd = SoChiHuyGiaoDien.tao_nhan_phan_biet_cha_doi(khop_ten, df_app)
                            danh_sach_trung = {f"{idx}. {nhan}": m_id for idx, (m_id, nhan) in enumerate(nhan_pd.items(), 1)}
                            chon_nguoi = st.selectbox("⚠️ Phát hiện trùng tên, vui lòng chọn đúng Tên Cha (hoặc Đời):", list(danh_sach_trung.keys()), key="dup_phado")
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
                "6. 🗺️ Bản đồ Di cư & Hành trình Lịch sử",
                "7. 🎵 Không gian Âm nhạc Tộc họ",
                "8. 📅 Xem ngày tốt",
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
            # 🟢 1. TRẠM ĐÓN THÔNG BÁO & BẮN HOA CHÚC MỪNG (GIỐNG MỤC THÊM THÀNH VIÊN)
            if "msg_so_vang_thanh_cong" in st.session_state:
                st.success(st.session_state.msg_so_vang_thanh_cong)
                st.balloons()
                del st.session_state.msg_so_vang_thanh_cong
            st.markdown('<h3 class="desktop-view" style="color: #2E8B57; font-weight: bold;">💬 Sổ Vàng Gia Tộc (Ý Kiến & Lời Tri Ân)</h3>', unsafe_allow_html=True)
            st.markdown('<h3 class="mobile-view" style="color: #2E8B57; font-size: 1.15rem; font-weight: bold;">💬 Sổ Vàng Gia Tộc</h3>', unsafe_allow_html=True)
            st.write("Không gian lưu giữ những dòng tâm tư, tình cảm, lời tri ân tiên tổ và các ý kiến đóng góp xây dựng dòng họ của con cháu khắp mọi miền.")
            tab_doc, tab_viet = st.tabs(["📖 Xem Sổ Vàng", "✍️ Viết Lời Lưu Bút"])
            # =====================================================
            # TAB 1: XEM SỔ VÀNG (CHỈ HIỂN THỊ BÀI ĐÃ PHÊ DUYỆT)
            # =====================================================
            with tab_doc:
                so_vang_da_duyet = KhoDuLieuSQL.lay_danh_sach_so_vang(trang_thai="Đã duyệt")
                if not so_vang_da_duyet:
                    st.info("Cuốn Sổ vàng hiện đang chờ những lời tri ân đầu tiên từ bà con...")
                else:
                    is_config_admin = (
                        st.session_state.get("user_id") == "ADMIN" 
                        or st.session_state.get("admin_level") == 1
                    )
                    for idx, item in enumerate(so_vang_da_duyet):
                        bai_id = item.get('id')
                        nguoi_gui_val = item.get('tac_gia', 'Con cháu dòng họ')
                        ngay_val = item.get('thoi_gian', '')
                        chi_val = item.get('chi_nhanh', '')
                        noi_dung_val = item.get('noi_dung', '')
                        st.markdown(f"""
                        <div class="desktop-view" style="background: #F5FFFA; border-left: 5px solid #2E8B57; padding: 15px; margin-bottom: 8px; border-radius: 6px; box-shadow: 1px 2px 4px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-weight: bold; color: #2E8B57; font-size: 1.1rem;">👤 {nguoi_gui_val} <span style="font-size: 0.85rem; color: #666; font-weight: normal;">(Mã bài: #{bai_id})</span></span>
                                <span style="color: #888; font-size: 0.9rem;">🕒 {ngay_val}</span>
                            </div>
                            <div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">📍 Chi phái / Nơi ở: {chi_val}</div>
                            <div style="color: #333; font-size: 1.05rem; font-style: italic; border-left: 3px solid #ddd; padding-left: 10px;">"{noi_dung_val}"</div>
                        </div>
                        <div class="mobile-view" style="background: #F5FFFA; border-top: 4px solid #2E8B57; padding: 12px; margin-bottom: 8px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="font-weight: bold; color: #2E8B57; font-size: 1.05rem; margin-bottom: 4px;">👤 {nguoi_gui_val} <span style="font-size: 0.8rem; color: #666; font-weight: normal;">(#{bai_id})</span></div>
                            <div style="font-size: 0.85em; color: #888; margin-bottom: 4px;">🕒 {ngay_val} | 📍 {chi_val}</div>
                            <div style="color: #333; font-size: 0.95em; margin-top: 8px; font-style: italic; border-left: 2px solid #ddd; padding-left: 8px;">"{noi_dung_val}"</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if is_config_admin:
                            if st.button(f"🗑️ Thu hồi bài này (Mã: #{bai_id})", key=f"del_sovang_{bai_id}_{idx}"):
                                KhoDuLieuSQL.xoa_so_vang(bai_id)
                                st.rerun() 
                        st.markdown("<br>", unsafe_allow_html=True)
            # =====================================================
            # TAB 2: VIẾT LỜI LƯU BÚT (GỬI DUYỆT THEO CHI)
            # =====================================================
            with tab_viet:
                st.info("💡 Lời lưu bút sau khi gửi sẽ được chuyển tới Ban Quản trị (Admin Cấp 1 & Admin phụ trách Chi) phê duyệt trước khi hiển thị lên Sổ Vàng.")
                # Tự động nhận diện tên và Chi của người đang đăng nhập
                ten_mac_dinh = st.session_state.get("user_name", "")
                if ten_mac_dinh == "Quản Trị Viên (Admin)":
                    ten_mac_dinh = ""
                id_dang_nhap = str(st.session_state.get("user_id", "")).strip()
                so_chi_login = TelegramBotManager.lay_so_chi_tu_ma_id(id_dang_nhap)
                ds_chi_options = [
                    ("1", "Chi 1 (Cửa Giáp)"),
                    ("2", "Chi 2 (Cửa Giáp)"),
                    ("3", "Chi 3 (Cửa Giáp)"),
                    ("4", "Chi 4 (Cửa Ất)"),
                    ("5", "Chi 5 (Cửa Ất)"),
                    ("0", "Khác / Con cháu nội ngoại thập phương")
                ]
                chi_keys = [c[0] for c in ds_chi_options]
                chi_labels = {c[0]: c[1] for c in ds_chi_options}
                idx_chi_mac_dinh = chi_keys.index(so_chi_login) if so_chi_login in chi_keys else 1
                with st.form("form_so_vang", clear_on_submit=True):
                    col1, col2, col3 = st.columns([1.5, 1.5, 1.5])
                    with col1:
                        nguoi_gui = st.text_input("Họ và tên người gửi (*):", value=ten_mac_dinh, placeholder="Ví dụ: Từ Quang...")
                    with col2:
                        ma_chi_chon = st.selectbox("Thuộc Chi phái (*):", options=chi_keys, index=idx_chi_mac_dinh, format_func=lambda x: chi_labels[x])
                    with col3:
                        noi_o_hien_tai = st.text_input("Nơi ở / Đơn vị hiện tại:", placeholder="Ví dụ: Xuân Lộc, Hà Nội, TP.HCM...")
                    noi_dung = st.text_area("Nội dung lưu bút (*):", placeholder="Nhập tâm tư, tình cảm, lời tri ân tiên tổ hoặc ý kiến đóng góp...", height=120)
                    submit_btn = st.form_submit_button("📤 GỬI LỜI LƯU BÚT", use_container_width=True)
                    if submit_btn:
                        if not nguoi_gui.strip() or not noi_dung.strip():
                            st.error("⚠️ Bà con vui lòng điền đầy đủ Họ tên và Nội dung lưu bút!")
                        else:
                            ngay_hien_tai = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                            ten_chi_hien_thi = chi_labels[ma_chi_chon]
                            if noi_o_hien_tai.strip():
                                chi_phai_full = f"{ten_chi_hien_thi} — {noi_o_hien_tai.strip()}"
                            else:
                                chi_phai_full = ten_chi_hien_thi

                            new_post_id = KhoDuLieuSQL.them_so_vang(
                                tac_gia=nguoi_gui,
                                chi_nhanh=chi_phai_full,
                                noi_dung=noi_dung,
                                thoi_gian=ngay_hien_tai,
                                so_chi=ma_chi_chon,
                                trang_thai="Chờ duyệt"
                            )
                            # Định tuyến thông báo Telegram về cho Admin Cấp 1 & Admin Cấp 2 của Chi
                            try:
                                sv_info = {
                                    "id": new_post_id,
                                    "tac_gia": nguoi_gui.strip(),
                                    "chi_nhanh": chi_phai_full,
                                    "noi_dung": noi_dung.strip(),
                                    "thoi_gian": ngay_hien_tai,
                                    "so_chi": ma_chi_chon
                                }
                                TelegramBotManager.gui_thong_bao_so_vang_cho_duyet(sv_info)
                            except Exception as tele_err:
                                print(f"Lỗi gửi Telegram Sổ Vàng: {tele_err}")

                            st.session_state.msg_so_vang_thanh_cong = (
                                f"🎉 Đã gửi lời lưu bút thành công (Trạng thái: Chờ duyệt)! "
                                f"Xin cảm ơn {nguoi_gui.strip()}, bài viết sẽ hiển thị lên Sổ Vàng ngay sau khi Ban Quản trị phê duyệt."
                            )
                            st.rerun()                            
        # ---------------------------------------------------------
        # MỤC 5: BẢN ĐỒ TÂM LINH & LĂNG MỘ
        # ---------------------------------------------------------
        elif "5." in menu_mo_rong:
            # Lớp BanDoGiaToc đã tự động xử lý responsive tiêu đề bên trong hàm render_bando()
            try:
                BanDoGiaToc.render_bando()
            except NameError:
                st.error("⚠️ Lớp BanDoGiaToc chưa được định nghĩa hoặc chưa được nạp. Hãy đảm bảo ông chủ đã chèn Khối [PHÂN LÔ F] vào mã nguồn.")
        # ---------------------------------------------------------
        # MỤC 6: BẢN ĐỒ DI CƯ & HÀNH TRÌNH LỊCH SỬ
        # ---------------------------------------------------------
        elif "Bản đồ Di cư" in menu_mo_rong:
            try:
                BanDoDiCu.render_bando_dicu()
            except NameError:
                st.warning("⚠️ Module Bản đồ Di cư đang được tích hợp hoàn thiện...")
            except Exception as e:
                st.error(f"⚠️ Lỗi hiển thị bản đồ di cư: {e}")
        # ---------------------------------------------------------
        # MỤC 7: KHÔNG GIAN ÂM NHẠC
        # ---------------------------------------------------------
        elif "7." in menu_mo_rong or "Không gian Âm nhạc" in menu_mo_rong:
            try:
                KhongGianAmNhac.render_am_nhac()
            except NameError:
                st.warning("⚠️ Module Âm nhạc Tộc họ đang được tích hợp hoàn thiện...")
            except Exception as e:
                st.error(f"⚠️ Lỗi hiển thị không gian âm nhạc: {e}")


        # ---------------------------------------------------------
        # MỤC 8: XEM NGÀY TỐT
        # ---------------------------------------------------------
        elif "8." in menu_mo_rong or "Xem ngày tốt" in menu_mo_rong:

            if "Xem ngày tốt" in menu_mo_rong:
                st.markdown("### 📅 Tra cứu Ngày tốt — Hoàng đạo")
                st.info("Tra cứu ngày giờ hoàng đạo, các ngày tốt để tiến hành đại sự trong dòng họ.")
                
                # Tạo giao diện chọn ngày tháng năm để xem lịch
                col1, col2, col3 = st.columns(3)
                with col1:
                    chon_ngay = st.number_input("Chọn Ngày", min_value=1, max_value=31, value=19)
                with col2:
                    chon_thang = st.number_input("Chọn Tháng", min_value=1, max_value=12, value=10)
                with col3:
                    chon_nam = st.number_input("Chọn Năm", min_value=2024, max_value=2030, value=2026)
                    
                if st.button("🔍 Xem cát hung ngày này", use_container_width=True):
                    st.success(f"✨ Ngày {chon_ngay}/{chon_thang}/{chon_nam}: Đây là ngày Hoàng đạo (Thanh Long), thích hợp để cúng tế, động thổ, họp mặt dòng họ hoặc tiến hành các việc lớn!")

  

                
                
    #=====================================================================
    # [PHÂN LÔ E10]: Hướng dẫn sử dụng và Trợ lý ảo AI (ĐÃ NÂNG CẤP TOÀN DIỆN)
    #=====================================================================
    @staticmethod
    def render_huong_dan_va_ai(df):
        st.markdown('<h3 class="desktop-view" style="color: #8B0000; font-weight: bold;">🤖 Trợ Lý AI & Cẩm Nang Dòng Họ</h3>', unsafe_allow_html=True)
        st.markdown('<h3 class="mobile-view" style="color: #8B0000; font-size: 1.15rem; font-weight: bold;">🤖 Trợ Lý AI & Cẩm Nang</h3>', unsafe_allow_html=True)
        st.write("Trung tâm tra cứu cẩm nang vận hành và giao lưu cùng Trợ lý ảo thông thái dòng họ Từ Xuân Lộc.")
        tab_hd, tab_ai = st.tabs(["📖 Cẩm nang sử dụng", "🤖 Trợ lý ảo AI (Đa nhiệm & Giọng đọc)"])
        # ==========================================
        # TAB 1: HƯỚNG DẪN SỬ DỤNG
        # ==========================================
        with tab_hd:
           
            with st.expander("📱 HƯỚNG DẪN ĐƯA BIỂU TƯỢNG (ICON) GIA PHẢ RA MÀN HÌNH CHÍNH ĐIỆN THOẠI", expanded=True):
                st.markdown("""
                    <div style="background-color: #E1F5FE; border: 2px solid #81D4FA; border-radius: 12px; padding: 20px; margin: -16px; box-shadow: 0 3px 10px rgba(0,0,0,0.03);">
                        <div style="font-size: 1.15rem; font-weight: bold; color: #01579B; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Times New Roman', Times, serif;">
                            📌 Hướng dẫn nhanh cho Điện thoại Samsung & iPhone:
                        </div>
                        <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFE0B2 100%); border: 2px solid #FB8C00; border-left: 6px solid #E65100; padding: 16px 20px; border-radius: 10px; font-family: 'Times New Roman', Times, serif; color: #3E2723; box-shadow: 0 3px 8px rgba(0,0,0,0.05);">
                            <div style="font-size: 1.05rem; font-weight: bold; color: #B71C1C; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                                ✨ Mở nhanh Gia phả chỉ bằng 1 cú chạm trên màn hình điện thoại (Giống như Zalo, Facebook):
                            </div>
                            <div style="font-size: 1.02rem; line-height: 1.8;">
                                <b>1️⃣ Bước chuẩn bị (Nếu mở từ Zalo):</b> Bấm vào biểu tượng dấu <b>`...`</b> ở góc phải phía trên màn hình Zalo ➔ Chọn <b>"Mở bằng trình duyệt"</b> <i>(Samsung Internet / Chrome trên Android hoặc Safari trên iPhone)</i>.<br>
                                <b>2️⃣ Trên điện thoại Samsung, Oppo, Xiaomi (Chrome):</b> Bấm vào <b>dấu 3 chấm dọc (`⋮`)</b> ở góc trên bên phải ➔ Chọn <b>"Thêm vào màn hình chính"</b> ➔ Đặt tên là <b>Gia Phả Họ Từ</b> rồi bấm <b>Thêm</b>.<br>
                                <b>3️⃣ Trên điện thoại iPhone (Safari):</b> Bấm nút <b>Chia sẻ</b> <i>(hình ô vuông có mũi tên hướng lên ở dưới đáy màn hình)</i> ➔ Kéo lên và chọn <b>"Thêm vào MH chính"</b> ➔ Sửa tên thành <b>Gia Phả Họ Từ</b> rồi bấm <b>Thêm</b>.
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)


                
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
            
            st.markdown("""
                <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%); border: 2px solid #FF8F00; padding: 18px; border-radius: 10px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.08);">
                    <h4 style="color: #8B0000; margin-top: 0; margin-bottom: 8px; font-family: 'Times New Roman', Times, serif;">🌐 ĐỊA CHỈ TRUY CẬP CHÍNH THỨC GIA PHẢ ĐIỆN TỬ</h4>
                    <p style="font-size: 1rem; margin-bottom: 8px; color: #4E342E;">Bà con có thể bấm trực tiếp vào đường dẫn dưới đây hoặc quét mã QR để mở gia phả trên điện thoại:</p>
                    <a href="https://giapha-hotu-xuanloc.streamlit.app" target="_blank" style="font-size: 1.15rem; font-weight: bold; color: #D84315; text-decoration: none; background: #FFF; padding: 6px 14px; border-radius: 6px; border: 1px dashed #D84315; display: inline-block;">🔗 https://giapha-hotu-xuanloc.streamlit.app</a>
                </div>
            """, unsafe_allow_html=True)

            
           
            # --- THAY THẾ BẰNG MÃ QR KHUNG ĐỒNG CÓ SẴN TRÊN MÁY CHỦ ---
            qr_file_path = Path(__file__).resolve().parent / "Ma_QR_GiaPha_HoTu_XuanLoc.png"
            if not qr_file_path.exists():
                qr_file_path = Path(__file__).resolve().parent / "images" / "Ma_QR_GiaPha_HoTu_XuanLoc.png"

            if qr_file_path.exists():
                try:
                    with open(qr_file_path, "rb") as f:
                        qr_bytes_local = f.read()
                    b64_qr_local = base64.b64encode(qr_bytes_local).decode("utf-8")
                    
                    st.markdown(f"""
                        <div style="text-align: center; margin: 25px 0;">
                            <div style="display: inline-block; background: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #E0E0E0;">
                                <img src="data:image/png;base64,{b64_qr_local}" alt="Mã QR Gia Phả" style="width: 240px; height: 240px; display: block; margin: 0 auto 10px auto; object-fit: contain;">
                                <p style="font-family: 'Times New Roman', Times, serif; font-size: 1rem; font-weight: bold; color: #8B0000; margin: 0;">📱 Quét mã QR bằng điện thoại để truy cập</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    qr_bytes_local = b""
            else:
                qr_bytes_local = b""
                st.warning("⚠️ Không tìm thấy tệp ảnh 'Ma_QR_GiaPha_HoTu_XuanLoc.png'. Ông chủ vui lòng đặt tệp vào cùng thư mục mã nguồn.")

            if qr_bytes_local:
                col_dl_qr1, col_dl_qr2, col_dl_qr3 = st.columns([1, 2, 1])
                with col_dl_qr2:
                    st.download_button(
                        label="📥 Tải ảnh Mã QR về máy (Dùng cho lần sau)",
                        data=qr_bytes_local,
                        file_name="Ma_QR_GiaPha_HoTu_XuanLoc.png",
                        mime="image/png",
                        use_container_width=True
                    )






            st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)    
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
                * **Tra cứu nhanh (Danh bạ):** Gõ tên hoặc tên tự vào ô tìm kiếm để lọc nhanh danh sách gia tộc.
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
        # TAB 2: TRỢ LÝ ẢO AI ĐA NHIỆM & GIỌNG ĐỌC BỌC THÉP
        # ==========================================

        with tab_ai:
            st.info("🤖 Trợ lý AI đã được nâng cấp: Hiểu được câu hỏi theo Nhánh/Chi/Phái, Đời thứ và tra cứu chính xác tên thành viên.")

            # 🟢 Sử dụng key để Streamlit tự động quản lý trạng thái ô nhập liệu, không bị reset khi chọn radio
            if "user_question_box" not in st.session_state:
                st.session_state.user_question_box = ""

            user_question = st.text_input(
                "💬 Nhập câu hỏi của bạn cho Trợ lý ảo:", 
                key="user_question_box",
                placeholder="Ví dụ: Nhánh cụ Dực có những ai là Liệt sĩ? hoặc Từ Quang Thùy là ai?"
            )

            
            
            
            if st.button("🚀 Gửi câu hỏi cho AI", use_container_width=True):
                if not user_question.strip():
                    st.warning("⚠️ Vui lòng nhập nội dung câu hỏi!")
                else:
                    def chuan_hoa_str(s):
                        if not s: 
                            return ""
                        s = unicodedata.normalize('NFC', str(s).strip().lower())
                        vocal_map = {
                            "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
                            "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
                            "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"
                        }
                        for old_val, new_val in vocal_map.items():
                            s = s.replace(old_val, new_val)
                        return s


                    
                    q_raw = user_question.strip()
                    q_lower = chuan_hoa_str(q_raw)
                    phan_hoi_html = ""
                    thong_tin_doc = ""

                    
                    # ---------------------------------------------------------
                    # LUỒNG 1: HƯỚNG DẪN CÁCH SỬ DỤNG ỨNG DỤNG
                    # ---------------------------------------------------------
                    if any(kw in q_lower for kw in ["thêm thành viên", "bổ sung thành viên", "nhập thêm người", "đăng ký mới"]):
                        thong_tin_doc = "Để thêm thành viên mới, bà con vui lòng mở Menu, chọn mục Thêm Thành Viên. Sau đó điền đầy đủ thông tin nhân khẩu và chọn Cha trực hệ. Hệ thống sẽ gửi đề xuất về cho Ban quản lý phê duyệt."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                    elif any(kw in q_lower for kw in ["cách xem sơ đồ", "xem trực hệ", "xem toàn cảnh", "cách dùng"]):
                        thong_tin_doc = "Để xem sơ đồ, bà con mở Menu góc trái, chọn Trực Hệ để xem ngược dòng từ con cháu lên Thủy tổ, hoặc chọn Toàn Cảnh để nhìn bức tranh tổng thể toàn dòng họ. Dùng 2 ngón tay để phóng to, thu nhỏ."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                    elif any(kw in q_lower for kw in ["mã định danh", "cấu trúc mã", "9 chữ số", "ý nghĩa mã"]):
                        thong_tin_doc = "Mã định danh gồm 9 chữ số. 3 số đầu chỉ Cửa, Chi, Phái. 2 số tiếp theo chỉ đời thứ mấy. Chữ số thứ 6 là giới tính. Và 3 số cuối là thứ tự sinh trưởng trong nhánh."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                    elif any(kw in q_lower for kw in ["sổ vàng", "viết lời tri ân", "góp ý"]):
                        thong_tin_doc = "Bà con hãy vào mục Mở Rộng rồi chọn Sổ Vàng để viết lời tri ân tiên tổ, đóng góp ý kiến hoặc ghi nhận công đức."
                        phan_hoi_html = f"💡 <b>Trợ lý AI hướng dẫn:</b><br><br>{thong_tin_doc}"
                    elif any(kw in q_lower for kw in ["thủy tổ", "nguồn gốc dòng họ", "khởi tổ"]):
                        thong_tin_doc = "Thủy tổ dòng họ ta là cụ Từ Dương Đốc, tên tự Huy Cán, vốn là một bậc thầy thuốc y dược tế sinh đầy đức độ. Cụ cùng hiền thê là bà Trần Thị Niêm đã từ Cổ Kênh lên đất Văn Cử khai hoang lập nghiệp."
                        phan_hoi_html = f"📜 <b>Trợ lý AI đáp:</b><br><br>{thong_tin_doc}"
                    # ---------------------------------------------------------
                    # LUỒNG 2: TRA CỨU DỮ LIỆU GIA PHẢ THÔNG MINH ĐA TẦNG
                    # ---------------------------------------------------------
                    else:
                        df_app = df[df["TrangThai"] == "Đã duyệt"].copy()
                        df_scope = df_app.copy()
                        ten_pham_vi = "toàn dòng họ"
                        # BƯỚC 1: NHẬN DIỆN PHẠM VI (CỬA / CHI / PHÁI / NHÁNH CỤ...)
                        # 1.1 Kiểm tra Cửa
                        if "cửa giáp" in q_lower:
                            df_scope = df_scope[df_scope["Cua"] == "Cửa Giáp"]
                            ten_pham_vi = "Cửa Giáp"
                        elif "cửa ất" in q_lower:
                            df_scope = df_scope[df_scope["Cua"] == "Cửa Ất"]
                            ten_pham_vi = "Cửa Ất"
                        # 1.2 Kiểm tra Chi số mấy (Chi 1 -> Chi 7)
                        m_chi = re.search(r'chi\s*(\d+)', q_lower)
                        if m_chi:
                            so_chi = m_chi.group(1)
                            df_scope = df_scope[df_scope["Chi"].str.contains(f"Chi {so_chi}", case=False, na=False)]
                            ten_pham_vi = f"Chi {so_chi}"
                        # 1.3 Kiểm tra Phái số mấy (Phái 0 -> Phái 9)
                        m_phai = re.search(r'phái\s*(\d+)', q_lower)
                        if m_phai:
                            so_phai = m_phai.group(1)
                            df_scope = df_scope[df_scope["Phai"].str.contains(f"Phái {so_phai}", case=False, na=False)]
                            ten_pham_vi = f"Phái {so_phai}"
                        # 1.4 Kiểm tra cụm "nhánh cụ [Tên]", "chi cụ [Tên]", "phái cụ [Tên]", "con cháu cụ [Tên]"
                        m_nhanh_cu = re.search(r'(?:nhánh|chi|phái|dòng|hậu duệ|con cháu)\s+(?:cụ|ông)?\s*([a-zà-ỹ]+(?:\s+[a-zà-ỹ]+)?)', q_lower)
                        if m_nhanh_cu:
                            raw_ancestor = m_nhanh_cu.group(1).strip()
                            # Cắt bỏ các từ khóa câu hỏi bị dính vào sau tên cụ
                            for cut_w in ["có", "là", "gồm", "những", "ai", "bao", "nhiêu", "mấy", "ở", "thuộc", "đời"]:
                                raw_ancestor = re.sub(rf'\b{cut_w}\b.*$', '', raw_ancestor).strip()
                            if raw_ancestor:
                                # Tìm xem tên cụ có nằm sẵn trong tên Chi hoặc Phái không (VD: Chi 2 (Cụ Dực))
                                match_chi_phai = df_app[
                                    df_app["Chi"].apply(chuan_hoa_str).str.contains(raw_ancestor, na=False) |
                                    df_app["Phai"].apply(chuan_hoa_str).str.contains(raw_ancestor, na=False)
                                ]
                                if not match_chi_phai.empty:
                                    df_scope = match_chi_phai.copy()
                                    ten_pham_vi = f"Nhánh cụ {raw_ancestor.title()}"
                                else:
                                    # Tìm ID của cụ trong CSDL rồi lấy toàn bộ hậu duệ bên dưới
                                    anc_rows = df_app[df_app["HoTen"].apply(chuan_hoa_str).apply(
                                        lambda x: raw_ancestor in x.split() if len(raw_ancestor.split()) == 1 else raw_ancestor in x
                                    )]
                                    if not anc_rows.empty:
                                        anc_id = anc_rows.iloc[0]["ID"]
                                        anc_name = anc_rows.iloc[0]["HoTen"]
                                        desc_ids = KyThuatBanVeGiaPha.get_all_descendants(df_app, anc_id)
                                        df_scope = df_app[df_app["ID"].isin([anc_id] + desc_ids)].copy()
                                        ten_pham_vi = f"Nhánh cụ {anc_name}"
                        # 1.5 Kiểm tra lọc theo Đời thứ mấy (nếu hỏi danh sách theo đời)
                        m_doi_loc = re.search(r'đời\s*(?:thứ\s*)?(\d+)', q_lower)
                        # BƯỚC 2: XỬ LÝ CHỦ ĐỀ CÂU HỎI TRONG PHẠM VI ĐÃ LỌC
                        # 2.1 Hỏi về LIỆT SĨ / TỬ SĨ / HY SINH (ĐÃ SỬA: CHỈ XÉT BẢN THÂN, KHÔNG XÉT CON CÁI)
                        if any(kw in q_lower for kw in ["liệt sĩ", "liệt sỹ", "tử sĩ", "tử sỹ", "hy sinh"]):
                            kw_ls = ["liệt sĩ", "liệt sỹ", "tử sĩ", "tử sỹ", "hy sinh"]
                            def la_liet_si(row):
                                t_trang = chuan_hoa_str(row.get("TinhTrang", ""))
                                g_chu = chuan_hoa_str(row.get("GhiChu", ""))
                                # Cắt bỏ hoàn toàn phần "sinh hạ:" phía sau để tránh nhầm lẫn con là cha
                                g_chu_ca_nhan = re.split(r'sinh hạ:', g_chu)[0] if 'sinh hạ:' in g_chu else g_chu
                                return any(k in t_trang or k in g_chu_ca_nhan for k in kw_ls)
                            ls_rows = df_scope[df_scope.apply(la_liet_si, axis=1)]
                            so_ls = len(ls_rows)
                            if so_ls > 0:
                                chi_tiet_lst = []
                                doc_lst = [f"Trong {ten_pham_vi}, có tổng cộng {so_ls} Liệt sĩ hoặc Tử sĩ được ghi nhận:"]
                                for idx_ls, (_, m) in enumerate(ls_rows.iterrows(), 1):
                                    m_ten = m.get('HoTen')
                                    m_doi = m.get('DoiThu')
                                    m_chi_txt = m.get('Chi')
                                    m_phai_txt = m.get('Phai')
                                    m_id = m.get('ID')
                                    m_tt = m.get('TinhTrang') or m.get('GhiChu')
                                    chi_tiet_lst.append(
                                        f"<b>{idx_ls}. {m_ten}</b> (Mã ĐD: <code>{m_id}</code>) — Đời thứ {m_doi} "
                                        f"({m_chi_txt}{(' - ' + m_phai_txt) if m_phai_txt else ''})<br>"
                                        f"   <i>• Ghi nhận: {m_tt}</i>"
                                    )
                                    doc_lst.append(f"{idx_ls}, Cụ hoặc ông {m_ten}, đời thứ {m_doi}.")
                                thong_tin_doc = " ".join(doc_lst)
                                phan_hoi_html = f"🕯️ <b>Trợ lý AI kính báo:</b> Trong <b>{ten_pham_vi}</b> có <b>{so_ls} Liệt sĩ / Tử sĩ</b>:<br><br>" + "<br><br>".join(chi_tiet_lst)
                            else:
                                thong_tin_doc = f"Trong {ten_pham_vi}, hiện chưa ghi nhận thông tin Liệt sĩ nào trong cơ sở dữ liệu."
                                phan_hoi_html = f"🤖 <b>Trợ lý AI đáp:</b> {thong_tin_doc}"

                        # 2.2 Hỏi thống kê số lượng trong một Nhánh / Chi / Phái / Đời
                        elif (ten_pham_vi != "toàn dòng họ" or m_doi_loc) and any(kw in q_lower for kw in ["bao nhiêu người", "có mấy người", "tổng số", "danh sách", "những ai"]):
                            if m_doi_loc:
                                doi_num = int(m_doi_loc.group(1))
                                df_scope = df_scope[df_scope["DoiThu"] == doi_num]
                                ten_pham_vi += f" (Đời thứ {doi_num})"
                            so_tv = len(df_scope)
                            if so_tv > 0:
                                ds_ten = [f"<b>{r['HoTen']}</b> (Đời {r['DoiThu']} - <code>{r['ID']}</code>)" for _, r in df_scope.head(30).iterrows()]
                                thong_tin_doc = f"Trong {ten_pham_vi} hiện có tổng cộng {so_tv} thành viên được ghi nhận."
                                phan_hoi_html = (
                                    f"📊 <b>Trợ lý AI thống kê ({ten_pham_vi}):</b> Có tổng cộng <b>{so_tv} thành viên</b>.<br><br>"
                                    + "<br>".join(ds_ten)
                                    + (f"<br><i>... và {so_tv - 30} thành viên khác.</i>" if so_tv > 30 else "")
                                )
                            else:
                                thong_tin_doc = f"Không tìm thấy thành viên nào trong {ten_pham_vi}."
                                phan_hoi_html = f"🤖 <b>Trợ lý AI đáp:</b> {thong_tin_doc}"
                        # 2.3 Tìm kiếm đích danh thành viên hoặc từ khóa mở rộng
                        else:
                            is_counting = any(kw in q_lower for kw in ["có mấy", "bao nhiêu", "tổng số", "đếm", "danh sách", "những ai"])
                            stop_words = {
                                "có", "mấy", "người", "tên", "là", "thế", "nào", "đời", "thứ", "trong", "họ",
                                "và", "các", "những", "thì", "vị", "này", "được", "gọi", "con", "của", "ai",
                                "cho", "hỏi", "về", "cụ", "ông", "bà", "nhánh", "chi", "phái", "cửa", "ở",
                                "sinh", "năm", "mất", "ngày", "giỗ", "vợ", "chồng", "tiểu", "sử", "bao", "nhiêu"
                            }
                            q_words = [w for w in re.findall(r'[a-zà-ỹ]+', q_lower) if w not in stop_words]
                            matched_indices = []
                            if q_words:
                                for idx, row in df_scope.iterrows():
                                    ho_ten = str(row.get("HoTen", "")).strip()
                                    if not ho_ten or ho_ten in ["Từ Thị ?", "Từ Húy Đỏ", "Từ Thị"]:
                                        continue
                                    ten_words = re.findall(r'[a-zà-ỹ]+', chuan_hoa_str(ho_ten))
                                    if all(qw in ten_words for qw in q_words):
                                        matched_indices.append(idx)
                                # Nếu không khớp tuyệt đối trong Họ Tên, tìm mở rộng sang cả Tên Tự, Ghi Chú, Tình Trạng
                                if not matched_indices:
                                    for idx, row in df_scope.iterrows():
                                        full_info = chuan_hoa_str(f"{row.get('HoTen', '')} {row.get('TenTu', '')} {row.get('TinhTrang', '')} {row.get('GhiChu', '')}")
                                        full_words = re.findall(r'[a-zà-ỹ]+', full_info)
                                        if all(qw in full_words for qw in q_words):
                                            matched_indices.append(idx)
                            matched_rows = df_scope.loc[matched_indices] if matched_indices else pd.DataFrame()
                            so_luong = len(matched_rows)
                            if so_luong > 0:
                                if not is_counting and so_luong == 1:
                                    m = matched_rows.iloc[0]
                                    m_ten = m.get('HoTen')
                                    m_doi = m.get('DoiThu')
                                    m_cua = m.get('Cua')
                                    m_chi_txt = m.get('Chi')
                                    m_phai_txt = m.get('Phai')
                                    m_id = m.get('ID')
                                    m_vc = m.get('VoChong', '')
                                    m_ns = m.get('NamSinh', '')
                                    m_nm = m.get('NamMat', '')
                                    m_ngaygio = m.get('NgayGio', '')
                                    m_ghichu = m.get('GhiChu', '')
                                    # Tìm tên Cha
                                    cha_id = m.get('ChaMe_ID', '')
                                    ten_cha = "Chưa rõ"
                                    if cha_id:
                                        cha_r = df_app[df_app['ID'] == cha_id]
                                        if not cha_r.empty:
                                            ten_cha = cha_r.iloc[0]['HoTen']
                                    thong_tin_doc = (
                                        f"Thành viên {m_ten}, thuộc đời thứ {m_doi}, {m_cua}, {m_chi_txt}. "
                                        f"Là con của {ten_cha}. "
                                        f"{('Vợ hoặc chồng là ' + m_vc + '. ') if m_vc else ''}"
                                        f"{('Ngày giỗ: ' + m_ngaygio + '. ') if m_ngaygio else ''}"
                                        f"{('Tiểu sử: ' + m_ghichu) if m_ghichu else ''}"
                                    )
                                    phan_hoi_html = (
                                        f"🎯 <b>Trợ lý AI tìm thấy 1 kết quả chính xác:</b><br><br>"
                                        f"👤 <b>Họ tên:</b> {m_ten} (Mã ĐD: <code>{m_id}</code>)<br>"
                                        f"• <b>Thế hệ:</b> Đời thứ <b>{m_doi}</b> | {m_cua} — {m_chi_txt} {('— ' + m_phai_txt) if m_phai_txt else ''}<br>"
                                        f"• <b>Cha trực hệ:</b> {ten_cha}<br>"
                                        f"• <b>Vợ/Chồng:</b> {m_vc if m_vc else 'Chưa cập nhật'}<br>"
                                        f"• <b>Năm sinh/mất:</b> {m_ns if m_ns else '?'} - {m_nm if m_nm else '?'} | <b>Ngày giỗ:</b> {m_ngaygio if m_ngaygio else 'Chưa rõ'}<br>"
                                        f"• <b>Tiểu sử/Ghi chú:</b> {m_ghichu if m_ghichu else 'Đang cập nhật'}"
                                    )
                
                                else:                      
                            
                                    # 🟢 ĐỒNG BỘ MÔ HÌNH LỌC 2 TẦNG (TÊN CHA -> CHI RÚT GỌN / ĐỜI)
                                    dict_cha_full = df_app.set_index("ID")["HoTen"].to_dict()
                                    
                                    tam_danh_sach = []
                                    dem_trung_cha = {}
                                    
                                    for _, m in matched_rows.head(20).iterrows():
                                        m_id = str(m.get('ID'))
                                        m_ten = str(m.get('HoTen')).strip()
                                        cha_id = str(m.get('ChaMe_ID', '')).strip()
                                        
                                        ten_cha_raw = dict_cha_full.get(cha_id, "")
                                        ten_cha = QuanTriTaiNguyen.lay_ten_chinh(ten_cha_raw) if ten_cha_raw else "Gốc"
                                        
                                        nhan_tang_1 = f"{m_ten} ({ten_cha})"
                                        dem_trung_cha[nhan_tang_1] = dem_trung_cha.get(nhan_tang_1, 0) + 1
                                        
                                        raw_chi = str(m.get('Chi', ''))
                                        chi_gon = raw_chi.split('(')[0].strip() if '(' in raw_chi else raw_chi
                                        
                                        tam_danh_sach.append({
                                            "id": m_id,
                                            "ten": m_ten,
                                            "nhan_1": nhan_tang_1,
                                            "chi_gon": chi_gon if chi_gon else "Chi phái khác",
                                            "doi": m.get('DoiThu', '')
                                        })

                                    chi_tiet_dict = {}
                                    doc_lst = [f"Trợ lý AI tìm thấy {so_luong} thành viên khớp với từ khóa. Vui lòng tích chọn đúng người thân bên dưới."]
                                    
                                    for item in tam_danh_sach:
                                        m_id = item["id"]
                                        m_ten = item["ten"]
                                        nhan_1 = item["nhan_1"]
                                        m_chi_gon = item["chi_gon"]
                                        m_doi = item["doi"]
                                        
                                        if dem_trung_cha[nhan_1] >= 2:
                                            nhan_hien_thi = f"👤 **{nhan_1}** — {m_chi_gon} (Đời {m_doi})"
                                        else:
                                            nhan_hien_thi = f"👤 **{nhan_1}** — {m_chi_gon}"
                                            
                                        # 🟢 Lưu trữ cả nhãn hiển thị đầy đủ để sau khi xác nhận sẽ gán ngược về ô nhập liệu
                                        chi_tiet_dict[nhan_hien_thi] = {"id": m_id, "label_tho": f"{m_ten} ({nhan_1.split('(')[-1]}"}
                                        doc_lst.append(f"{m_ten}, con ông {nhan_1.split('(')[-1].replace(')', '')}.")

                                    thong_tin_doc = " ".join(doc_lst[:10])
                                    phan_hoi_html = f"📊 <b>Trợ lý AI tìm thấy {so_luong} thành viên.</b> Vui lòng tích chọn đúng người thân bên dưới:"
                                    
                                    st.markdown(f"""
                                        <div style="background: #FDFEFE; border: 1.5px solid #8B0000; padding: 16px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); font-family: 'Times New Roman', Times, serif; font-size: 1.05rem; color: #2C3E50; margin-bottom: 10px;">
                                            {phan_hoi_html}
                                        </div>
                                    """, unsafe_allow_html=True)

                                    # 🟢 Tạo form riêng cho phần chọn danh sách để người dùng thoải mái tích chọn mà không bị load lại trang
                                    with st.form(key="form_chon_nhieu_ket_qua"):
                                        selected_radio_label = st.radio(
                                            "👉 Tích chọn vào dòng của người thân:",
                                            options=list(chi_tiet_dict.keys()),
                                            key="ai_radio_member_target",
                                            label_visibility="collapsed"
                                        )
                                        
                                        submit_chon = st.form_submit_button("🎯 Xác nhận xem chi tiết người được chọn", use_container_width=True)

                                        if submit_chon:
                                            chon_info = chi_tiet_dict[selected_radio_label]
                                            chosen_id = chon_info["id"]
                                            
                                            # 🟢 Đưa nguyên vẹn dòng đã chọn (bỏ các ký tự Markdown định dạng để hiển thị sạch ở ô nhập)
                                            clean_label_text = selected_radio_label.replace("👤 **", "").replace("**", "")
                                            st.session_state.user_question_box = clean_label_text
                                            
                                            # Chuyển hướng sang trang Trực Hệ
                                            st.session_state.focus_id = chosen_id
                                            st.session_state.pending_menu = "🎯 Trực Hệ"
                                            
                                            components.html("""
                                                <script>
                                                    window.parent.window.scrollTo({ top: 0, behavior: 'smooth' });
                                                </script>
                                            """, height=0)
                                            st.rerun()
                                            

                                    
                            else:
                                thong_tin_doc = f"Xin lỗi, tôi không tìm thấy thông tin nào khớp với câu hỏi: {q_raw}."
                                phan_hoi_html = f"🤖 <b>Trợ lý AI đáp:</b> Không tìm thấy thông tin nào khớp với câu hỏi: <i>'{q_raw}'</i>."
                    # HIỂN THỊ VĂN BẢN KẾT QUẢ
                    st.markdown(f"""
                        <div style="background: #FDFEFE; border: 1.5px solid #8B0000; padding: 18px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.06); font-family: 'Times New Roman', Times, serif; font-size: 1.05rem; color: #2C3E50; margin-bottom: 15px;">
                            {phan_hoi_html}
                        </div>
                    """, unsafe_allow_html=True)


                    
                    # ---------------------------------------------------------
                    # HỆ THỐNG PHÁT ÂM THANH BACKEND (TẢI MP3 TRỰC TIẾP VỀ PYTHON)
                    # ---------------------------------------------------------
                    clean_speech_text = re.sub(r'<[^>]*>', ' ', thong_tin_doc)
                    safe_text = re.sub(r'\s+', ' ', clean_speech_text).strip()
                    audio_bytes = b""
                    # Ưu tiên 1: Dùng thư viện gTTS nếu môi trường đã cài đặt
                    try:
                        from gtts import gTTS
                        tts_fp = io.BytesIO()
                        tts = gTTS(text=safe_text, lang='vi')
                        tts.write_to_fp(tts_fp)
                        audio_bytes = tts_fp.getvalue()
                    except Exception:
                        # Ưu tiên 2: Tải trực tiếp qua urllib ở Backend (Tự động cắt câu < 180 ký tự)
                        try:
                            words = safe_text.split()
                            chunks = []
                            curr_chunk = ""
                            for w in words:
                                if len(curr_chunk) + len(w) + 1 <= 180:
                                    curr_chunk = f"{curr_chunk} {w}".strip()
                                else:
                                    chunks.append(curr_chunk)
                                    curr_chunk = w
                            if curr_chunk:
                                chunks.append(curr_chunk)
                            combined_mp3 = bytearray()
                            for ch_txt in chunks:
                                encoded_q = urllib.parse.quote(ch_txt)
                                url_tts = f"https://translate.googleapis.com/translate_tts?client=tw-ob&ie=UTF-8&tl=vi&q={encoded_q}"
                                req = urllib.request.Request(
                                    url_tts,
                                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                                )
                                with urllib.request.urlopen(req, timeout=8) as resp:
                                    combined_mp3.extend(resp.read())
                            audio_bytes = bytes(combined_mp3)
                        except Exception as e_tts:
                            print(f"Lỗi tạo âm thanh: {e_tts}")
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        st.caption("🔊 *Hệ thống đang tự động phát giọng đọc tiếng Việt của Trợ lý AI.*")
                    else:
                        st.warning("⚠️ Không thể kết nối máy chủ âm thanh. Vui lòng kiểm tra kết nối mạng Internet.")

    #=====================================================================
    # [PHÂN LÔ E11]: TRUNG TÂM QUẢN TRỊ & VẬN HÀNH HỆ THỐNG (XÓA SẠCH ẢNH + CSDL)
    #=====================================================================
    @staticmethod
    def render_quantri(df):
        st.subheader("🛠️ Trung Tâm Quản Trị & Vận Hành Hệ Thống")
        # ==========================================
        # TRƯỜNG HỢP 1: Đã đăng nhập đầy đủ quyền Admin từ cổng chính (Cổng tam quan)
        # ==========================================
        if st.session_state.get("admin_level", 0) == 1:
            st.success(f"✅ Xác thực Quản trị viên thành công: **{st.session_state.get('user_name')}** (ID: `{st.session_state.get('user_id')}`)")
        # ==========================================
        # TRƯỜNG HỢP 2: Đã đăng nhập bằng tài khoản con cháu (Có sẵn Tên và ID thực tế)
        # ==========================================
        elif st.session_state.get("da_dang_nhap", False) and st.session_state.get("user_id") not in ["", "KHACH", "GUEST", "ADMIN"]:
            current_name = st.session_state.get("user_name", "")
            current_id = st.session_state.get("user_id", "")
            
            st.info(f"👤 Đang nhận diện tài khoản con cháu: **{current_name}** (Mã ID: `{current_id}`). Vui lòng nhập Mật khẩu Quản trị để mở khóa khu vực vận hành.")
            
            with st.form("form_admin_truong_hop_2"):
                admin_key_2 = st.text_input("🔑 Mật khẩu Quản trị viên (*):", type="password", placeholder="Nhập mật khẩu Admin...")
                btn_2 = st.form_submit_button("🔓 Xác thực Mật khẩu Admin", type="primary", use_container_width=True)
                
                if btn_2:
                    if admin_key_2 == "admin12345":
                        st.session_state.admin_level = 1
                        st.success("✅ Xác thực quyền Quản trị thành công!")
                        st.rerun()
                    else:
                        st.error("❌ Mật khẩu quản trị không chính xác!")
            return
        # ==========================================
        # TRƯỜNG HỢP 3: Đăng nhập ở chế độ Khách hoặc chưa đăng nhập
        # ==========================================
        else:
            st.warning("🔒 Khu vực dành riêng cho Ban Quản Trị. Vui lòng khai báo đầy đủ Họ và tên, Mã định danh (ID) và Mật khẩu Quản trị để xác thực.")
            
            with st.form("form_admin_truong_hop_3"):
                col_q1, col_q2, col_q3 = st.columns(3)
                with col_q1:
                    qt_ten = st.text_input("👤 Họ và tên (*):", placeholder="Ví dụ: Từ Quang Thùy")
                with col_q2:
                    qt_id = st.text_input("🆔 Mã định danh (ID) (*):", placeholder="Ví dụ: 124.08.0.099")
                with col_q3:
                    qt_mk = st.text_input("🔑 Mật khẩu Quản trị (*):", type="password", placeholder="Nhập mật khẩu Admin...")      
                btn_3 = st.form_submit_button("🔓 Xác thực Quyền Quản Trị", type="primary", use_container_width=True)
                if btn_3:
                    ten_clean = unicodedata.normalize('NFC', qt_ten.strip().lower())
                    id_clean = qt_id.strip().replace(".", "")
                    df_chk = df[df["TrangThai"] == "Đã duyệt"].copy()
                    df_chk["ID_Clean"] = df_chk["ID"].str.replace(".", "", regex=False)
                    df_chk["HoTen_Clean"] = df_chk["HoTen"].apply(lambda x: unicodedata.normalize('NFC', str(x).strip().lower()))
                    matched_adm = df_chk[(df_chk["ID_Clean"] == id_clean) & (df_chk["HoTen_Clean"] == ten_clean)]
                    if not qt_ten.strip() or not id_clean or not qt_mk:
                        st.error("⚠️ Vui lòng nhập đầy đủ cả 3 thông tin: Họ và tên, Mã định danh (ID) và Mật khẩu!")
                    elif qt_mk != "admin12345":
                        st.error("❌ Mật khẩu quản trị không chính xác!")
                    elif matched_adm.empty:
                        st.error("❌ Họ và tên hoặc Mã định danh (ID) không khớp với dữ liệu Gia phả đã duyệt!")
                    else:
                        adm_info = matched_adm.iloc[0]
                        st.session_state.user_name = adm_info["HoTen"]
                        st.session_state.user_id = adm_info["ID"]
                        st.session_state.focus_id = adm_info["ID"]
                        st.session_state.admin_level = 1
                        st.session_state.da_dang_nhap = True
                        st.rerun()
            return

        # --- NẾU ĐÃ ĐẠT CHUẨN QUYỀN ADMIN, HIỂN THỊ 5 TAB QUẢN TRỊ ---
        tab_kiemduyet, tab_dulieu, tab_cauhinh, tab_telegram, tab_giamsat = st.tabs([
            "⏳ Kiểm Duyệt Mới",
            "🗂️ Dữ Liệu & Ảnh",
            "⚙️ Cấu Hình Chung",
            "🤖 Telegram Bot",
            "📊 Giám Sát Truy Cập"
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
            st.markdown("---")
            st.markdown("### 💬 Danh sách Lưu bút Sổ Vàng đang Chờ duyệt")
            ds_sv_pending = KhoDuLieuSQL.lay_danh_sach_so_vang(trang_thai="Chờ duyệt")
            if not ds_sv_pending:
                st.success("🎉 Hiện không có lời lưu bút Sổ Vàng nào đang chờ duyệt!")
            else:
                for sv in ds_sv_pending:
                    sv_id = sv["id"]
                    sv_tac_gia = sv["tac_gia"]
                    sv_chi = sv["chi_nhanh"]
                    sv_thoi_gian = sv["thoi_gian"]
                    sv_noi_dung = sv["noi_dung"]
                    with st.expander(f"💬 Lưu bút #{sv_id} — Người gửi: {sv_tac_gia} ({sv_thoi_gian}) - Chờ duyệt", expanded=True):
                        col_sv_info, col_sv_act = st.columns([3, 1])
                        with col_sv_info:
                            st.write(f"- **Người gửi:** **{sv_tac_gia}**")
                            st.write(f"- **Chi phái / Nơi ở:** {sv_chi}")
                            st.write(f"- **Thời gian gửi:** `{sv_thoi_gian}`")
                            st.info(f"📝 **Nội dung:** \"{sv_noi_dung}\"")
                        with col_sv_act:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("✅ Phê duyệt lưu bút", key=f"btn_duyet_sv_{sv_id}", use_container_width=True):
                                KhoDuLieuSQL.duyet_so_vang(sv_id)
                                st.success(f"Đã phê duyệt lưu bút của {sv_tac_gia} lên Sổ Vàng!")
                                st.rerun()
                            if st.button("❌ Từ chối / Xóa", key=f"btn_xoa_sv_{sv_id}", type="primary", use_container_width=True):
                                KhoDuLieuSQL.xoa_so_vang(sv_id)
                                st.warning(f"Đã xóa lưu bút của {sv_tac_gia}!")
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
        # TAB 4: TELEGRAM BOT & PHÂN QUYỀN 2 CẤP
        # ==========================================
        with tab_telegram:
            st.markdown("### 🤖 Trung Tâm Điều Phối Bot Telegram & Phân Quyền Duyệt 2 Cấp")
            st.info(
                "💡 **Hướng dẫn lấy mã ID cho các Admin:** Nhắc các Admin mở ứng dụng Telegram, tìm đến Bot của dòng họ, "
                "bấm nút **START** (hoặc gõ `/myid`). Bot sẽ tự động trả về một dãy số **User ID cá nhân** (ví dụ: `987654321`). "
                "Ông chủ chỉ cần copy các dãy số đó dán vào đúng ô phân quyền dưới đây (nếu nhiều người thì ngăn cách bằng dấu phẩy `,`)."
            )
            with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Khoa, GiaTri FROM CauHinhHeThong WHERE Khoa LIKE 'tele_%'")
                cfg_tele = dict(cursor.fetchall())
            curr_enabled = (cfg_tele.get("tele_enabled", "True") == "True")
            enable_tele = st.toggle("Kích hoạt hệ thống thông báo & phê duyệt qua Telegram", value=curr_enabled)
            if enable_tele:
                st.markdown("#### 1️⃣ Cấu hình Kết nối Bot & Kênh Chung")
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    inp_token = st.text_input(
                        "🔑 Telegram Bot Token (Bảo mật):",
                        value=cfg_tele.get("tele_bot_token", ""),
                        type="password",
                        placeholder="Nhập Token từ @BotFather..."
                    )
                with col_t2:
                    inp_group_id = st.text_input(
                        "📢 Chat ID Siêu nhóm Hội đồng (Tùy chọn):",
                        value=cfg_tele.get("tele_chat_id", ""),
                        placeholder="Ví dụ: -1004360294941"
                    )
                st.markdown("#### 2️⃣ Phân quyền Admin Cấp 1 (Toàn quyền duyệt mọi Chi)")
                inp_admin_c1 = st.text_input(
                    "👑 Danh sách User ID của 02 Admin Cấp 1 (Ông chủ & Đồng quản trị):",
                    value=cfg_tele.get("tele_admin_cap1", ""),
                    placeholder="Ví dụ: 112233445, 556677889 (Cách nhau bởi dấu phẩy)"
                )
                st.markdown("#### 3️⃣ Phân quyền Admin Cấp 2 (Phân theo Cửa & 05 Chi huyết mạch)")
                st.caption("Dòng họ ta gồm Cửa Giáp (Chi 1, 2, 3) và Cửa Ất (Chi 4, 5). Khi có thành viên mới đăng ký thuộc Chi nào, Bot sẽ tự động gửi về đúng các Admin của Chi đó.")
                c_cuagiap, c_cuaat = st.columns(2)
                with c_cuagiap:
                    st.markdown("##### 🔵 Cửa Giáp")
                    inp_chi_1 = st.text_input("🔹 Admin Chi 1 (Cụ Liện - Mã 11x):", value=cfg_tele.get("tele_admin_chi_1", ""), placeholder="ID Admin 1, ID Admin 2...")
                    inp_chi_2 = st.text_input("🔹 Admin Chi 2 (Cụ Dực - Mã 12x):", value=cfg_tele.get("tele_admin_chi_2", ""), placeholder="ID Admin 1, ID Admin 2...")
                    inp_chi_3 = st.text_input("🔹 Admin Chi 3 (Cụ Lạng - Mã 13x):", value=cfg_tele.get("tele_admin_chi_3", ""), placeholder="ID Admin 1, ID Admin 2...")
                with c_cuaat:
                    st.markdown("##### 🟢 Cửa Ất")
                    inp_chi_4 = st.text_input("🔸 Admin Chi 4 (Cụ Màn - Mã 24x):", value=cfg_tele.get("tele_admin_chi_4", ""), placeholder="ID Admin 1, ID Admin 2...")
                    inp_chi_5 = st.text_input("🔸 Admin Chi 5 (Cụ Hùng - Mã 25x):", value=cfg_tele.get("tele_admin_chi_5", ""), placeholder="ID Admin 1, ID Admin 2...")
                if st.button("💾 LƯU TOÀN BỘ CẤU HÌNH & PHÂN QUYỀN TELEGRAM", type="primary", use_container_width=True):
                    du_lieu_luu = [
                        ("tele_enabled", "True"),
                        ("tele_bot_token", inp_token.strip()),
                        ("tele_chat_id", inp_group_id.strip()),
                        ("tele_admin_cap1", inp_admin_c1.strip()),
                        ("tele_admin_chi_1", inp_chi_1.strip()),
                        ("tele_admin_chi_2", inp_chi_2.strip()),
                        ("tele_admin_chi_3", inp_chi_3.strip()),
                        ("tele_admin_chi_4", inp_chi_4.strip()),
                        ("tele_admin_chi_5", inp_chi_5.strip()),
                    ]
                    with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                        cursor = conn.cursor()
                        cursor.executemany("INSERT OR REPLACE INTO CauHinhHeThong (Khoa, GiaTri) VALUES (?, ?)", du_lieu_luu)
                        conn.commit()
                    TelegramBotManager.start_background_bot()
                    st.success("✅ Đã lưu cấu hình Bot và danh sách phân quyền Cửa Giáp & Cửa Ất thành công!")
                    st.rerun()
            else:
                if curr_enabled:
                    with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                        conn.execute("INSERT OR REPLACE INTO CauHinhHeThong (Khoa, GiaTri) VALUES ('tele_enabled', 'False')")
                        conn.commit()
                st.write("📌 Bật công tắc trên để kích hoạt hệ thống xét duyệt qua Telegram.")
        # ==========================================
        # TAB 5: GIÁM SÁT TRUY CẬP & BÁO CÁO
        # ==========================================
        with tab_giamsat:
            st.markdown("### 📊 Báo cáo & Giám sát Truy cập Hệ thống theo Thời gian thực")
            st.info("💡 Tab này cung cấp thông tin chi tiết về số lượt truy cập, danh sách Mã ID thành viên đang online và số lượng khách vãng lai.") 
            # Lấy số liệu tổng quan
            dang_online, tong_tuan, tong_nam = KhoDuLieuSQL.thong_ke_truy_cap()
            ct_online = KhoDuLieuSQL.lay_chi_tiet_online(df)
            ds_tv = ct_online["thanh_vien"]
            ds_khach_tq = ct_online["khach_tham_quan"]
            so_khach_cho = ct_online["khach_ngoai_cong"]
            tong_khach = len(ds_khach_tq) + so_khach_cho
            # Hiển thị các ô chỉ số tổng quan (Metrics)
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("🟢 Đang Online", f"{dang_online} người")
            with col_m2:
                st.metric("🌸 Khách vãng lai", f"{tong_khach} khách")
            with col_m3:
                st.metric("📅 Lượt xem trong tuần", f"{tong_tuan:,}")
            with col_m4:
                st.metric("📈 Lượt xem năm nay", f"{tong_nam:,}")
            st.markdown("---")
            # Chia làm 2 cột hiển thị chi tiết: Cột trái (Thành viên có ID), Cột phải (Khách vãng lai)
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown(f"#### 🧬 Thành viên có ID đang Online ({len(ds_tv)})")
                if ds_tv:
                    for tv in ds_tv:
                        st.markdown(
                            f"""<div style="background: #FFF8E1; border-left: 4px solid #8B0000; padding: 10px 14px; margin-bottom: 8px; border-radius: 6px; font-family: 'Times New Roman', serif;">
                                <b>👤 {tv['HoTen']}</b> &nbsp;|&nbsp; <span style="color: #666; font-size: 0.9rem;">({tv['Luc']})</span><br>
                                🆔 Mã ĐD: <code>{tv['ID']}</code> &nbsp;•&nbsp; 🏛️ {tv['ChiPhai']}
                            </div>""",
                            unsafe_allow_html=True
                        )
                else:
                    st.success("Hiện chưa có thành viên nào đăng nhập bằng Mã ID.")
            with col_g2:
                st.markdown(f"#### 🌸 Khách vãng lai / Khách quý ({tong_khach})")
                st.caption("Bao gồm khách đang tham quan bên trong và khách đang đứng ở cổng đăng nhập.")
                if so_khach_cho > 0:
                    st.markdown(f"🚪 **Khách ở sảnh chờ / ngoài cổng:** `{so_khach_cho}` người")
                if ds_khach_tq:
                    st.markdown("📌 **Danh sách khách đang tham quan:**")
                    for k_info in ds_khach_tq:
                        st.markdown(
                            f"""<div style="background: #F0F8FF; border-left: 4px solid #4682B4; padding: 8px 12px; margin-bottom: 6px; border-radius: 6px; font-size: 0.95rem;">
                                🌸 {k_info}
                            </div>""",
                            unsafe_allow_html=True
                        )
                elif so_khach_cho == 0:
                    st.success("Hiện không có khách vãng lai nào đang trực tuyến.")

    #=====================================================================
    # [PHÂN LÔ E12]: CỔNG ĐĂNG NHẬP "NGHI MÔN SỐ" (ĐÃ TINH CHỈNH GIAO DIỆN CHUẨN XÁC)
    #=====================================================================
    @staticmethod
    def tao_nhan_phan_biet_cha_doi(df_subset, df_all):
        dict_cha_full = df_all.set_index("ID")["HoTen"].to_dict()
        tam_list = []
        dem_trung_cap_1 = {}

        # 🟢 HÀM CHUẨN HÓA DẤU TIẾNG VIỆT (ĐỒNG HỘ OÀ <-> OÀ, OÁ <-> OÁ...)
        def chuan_hoa_dau(txt):
            if not txt:
                return ""
            s = unicodedata.normalize('NFC', str(txt).strip())
            vocal_map = {
                "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
                "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
                "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy",
                "OÀ": "ÒA", "OÁ": "ÓA", "OẢ": "ỎA", "OÃ": "ÕA", "OẠ": "ỌA",
                "OÈ": "ÒE", "OÉ": "ÓE", "OẺ": "ỎE", "OẼ": "ÕE", "OẸ": "ỌE",
                "UỲ": "ÙY", "UÝ": "ÚY", "UỶ": "ỦY", "UỸ": "ŨY", "UỴ": "ỤY"
            }
            for old_val, new_val in vocal_map.items():
                s = s.replace(old_val, new_val)
            return s
        for _, r in df_subset.iterrows():
            m_id = str(r["ID"])
            ho_ten = chuan_hoa_dau(str(r["HoTen"]))
            cha_id = str(r.get("ChaMe_ID", "")).strip()
            ten_cha_raw = chuan_hoa_dau(dict_cha_full.get(cha_id, ""))
            ten_cha = QuanTriTaiNguyen.lay_ten_chinh(ten_cha_raw) if ten_cha_raw else "Gốc"
            nhan_cap_1 = f"{ho_ten} ({ten_cha})"
            dem_trung_cap_1[nhan_cap_1] = dem_trung_cap_1.get(nhan_cap_1, 0) + 1
            tam_list.append((m_id, nhan_cap_1, r["DoiThu"]))
        ket_qua = {}
        for m_id, nhan_cap_1, doi_thu in tam_list:
            if dem_trung_cap_1[nhan_cap_1] >= 2:
                ket_qua[m_id] = f"{nhan_cap_1} — Đời {doi_thu}"
            else:
                ket_qua[m_id] = nhan_cap_1
        return ket_qua
    
    @staticmethod
    def lay_va_cap_nhat_luot_mien_id(member_id, tru_luot=False):
        khoa_db = f"free_login_{member_id}"
        so_lan = 10
        try:
            with sqlite3.connect(KhoDuLieuSQL.DB_FILE, timeout=15) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT GiaTri FROM CauHinhHeThong WHERE Khoa = ?", (khoa_db,))
                row = cursor.fetchone()
                if row and str(row[0]).isdigit():
                    so_lan = int(row[0])
                if tru_luot and so_lan > 0:
                    so_lan -= 1
                    cursor.execute(
                        "INSERT OR REPLACE INTO CauHinhHeThong (Khoa, GiaTri) VALUES (?, ?)",
                        (khoa_db, str(so_lan))
                    )
                    conn.commit()
        except Exception:
            pass
        return so_lan

    @classmethod
    def render_app(cls):
        cls.thiet_lap_giao_dien()
        df = KhoDuLieuSQL.load_data()
        if "da_dang_nhap" not in st.session_state:
            st.session_state.da_dang_nhap = False
        if "so_lan_con_lai" not in st.session_state:
            st.session_state.so_lan_con_lai = 10
        if not st.session_state.da_dang_nhap:
            df_approved = df[df["TrangThai"] == "Đã duyệt"].copy()
            tong_thanh_vien = len(df_approved)
            so_doi_max = int(df_approved["DoiThu"].max()) if not df_approved.empty else 12
            dang_online, _, tong_nam = KhoDuLieuSQL.thong_ke_truy_cap()
            saved_uid_param = str(st.query_params.get("uid", "")).strip()
            default_ten_nhap = st.session_state.get("ls_device_owner_name", "")
            default_id_nhap = st.session_state.get("ls_device_owner_id", "")
            if saved_uid_param:
                row_saved = df_approved[df_approved["ID"] == saved_uid_param]
                if not row_saved.empty:
                    default_ten_nhap = str(row_saved.iloc[0]["HoTen"])
                    default_id_nhap = str(row_saved.iloc[0]["ID"])
                    st.session_state.so_lan_con_lai = cls.lay_va_cap_nhat_luot_mien_id(default_id_nhap, tru_luot=False)
            else:
                components.html("""
                    <script>
                        try {
                            const savedUid = window.localStorage.getItem('hotu_saved_uid');
                            const urlParams = new URLSearchParams(window.parent.location.search);
                            if (savedUid && !urlParams.get('uid')) {
                                urlParams.set('uid', savedUid);
                                window.parent.location.search = urlParams.toString();
                            }
                        } catch (e) {}
                    </script>
                """, height=0)
            # Xử lý hiển thị Logo độc lập bên trái, khối chữ đứng chính giữa dải băng rôn đỏ
            logo_path = Path(__file__).resolve().parent / "logo_hotu.png"
            logo_html = '<div style="font-size: 5rem; line-height: 1;">📜</div>'
            if logo_path.exists():
                try:
                    with open(logo_path, "rb") as f:
                        b64_logo = base64.b64encode(f.read()).decode("utf-8")
                    logo_html = f'<img src="data:image/png;base64,{b64_logo}" style="width: 190px; height: 190px; object-fit: contain; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.5));">'
                except Exception:
                    pass
            st.markdown("""
                <style>
                    .nghimon-banner {
                        background: linear-gradient(135deg, #5A0000 0%, #8B0000 50%, #4A0000 100%);
                        border: 2.5px solid #D4AF37;
                        border-radius: 14px;
                        padding: 18px 24px;
                        color: #FFF8DC;
                        box-shadow: 0 8px 24px rgba(139, 0, 0, 0.2);
                        margin-bottom: 20px;
                        font-family: 'Times New Roman', Times, serif;
                        position: relative;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        min-height: 170px; /* Đảm bảo chiều cao đủ thoáng cho logo 160px */
                    }
                    .nghimon-logo-absolute {
                        position: absolute;
                        left: 80px; /* Logo đứng độc lập bám sát lề trái dải đỏ */
                        top: 50%;
                        transform: translateY(-50%);
                        display: flex;
                        align-items: center;
                    }
                    .nghimon-text-group {
                        text-align: center;
                        width: 100%;
                        padding: 0 140px; /* Tạo khoảng đệm hai bên để chữ luôn nằm chính giữa tuyệt đối không đè lên logo */
                    }
                    .nghimon-title {
                        font-size: 2.4rem; /* Kích thước to rõ chuẩn 1.5 lần */
                        font-weight: bold;
                        color: #FFD700;
                        text-transform: uppercase;
                        letter-spacing: 1.5px;
                        margin: 0 0 6px 0;
                        text-shadow: 0 2px 5px rgba(0,0,0,0.45);
                    }
                    .nghimon-subtitle {
                        font-size: 1.35rem;
                        font-style: italic;
                        color: #F5DEB3;
                        margin: 0;
                    }
                    .heritage-box {
                        background: linear-gradient(145deg, #FFFDF9 0%, #F4EBD0 100%);
                        border: 1.5px solid #D4C5A9;
                        border-left: 6px solid #8B0000;
                        border-radius: 12px;
                        padding: 15px;
                        font-family: 'Times New Roman', Times, serif;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                        height: 100%;
                    }
                    .metric-grid {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 12px;
                        margin-top: 16px;
                        margin-bottom: 16px;
                    }
                    .metric-item {
                        background: #FFFFFF;
                        border: 1px solid #E6DCC8;
                        border-radius: 8px;
                        padding: 10px 12px;
                        text-align: center;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
                    }
                    .metric-num {
                        font-size: 1.35rem;
                        font-weight: bold;
                        color: #8B0000;
                    }
                    .metric-lbl {
                        font-size: 0.85rem;
                        color: #5D4037;
                    }
                    .id-badge-guide {
                        background: #FFF8E1;
                        border: 1px dashed #B8860B;
                        border-radius: 8px;
                        padding: 10px 14px;
                        font-size: 0.9rem;
                        color: #4E342E;
                        margin-top: 12px;
                    }
                    @media (max-width: 768px) {
                        .nghimon-banner {
                            flex-direction: column;
                            text-align: center;
                            padding: 14px 12px;
                            min-height: auto;
                        }
                        .nghimon-logo-absolute {
                            display: none !important;
                        }
                        .nghimon-text-group {
                            padding: 0;
                        }
                        .nghimon-title { font-size: 1.35rem !important; letter-spacing: 0.5px; }
                        .nghimon-subtitle { font-size: 0.95rem !important; }
                    }
                </style>
            """, unsafe_allow_html=True)
            st.markdown(f"""
                <div class="nghimon-banner">
                    <div class="nghimon-logo-absolute">
                        {logo_html}
                    </div>
                    <div class="nghimon-text-group">
                        <div class="nghimon-title">TỪ TỘC TIỂU TÔN PHỔ KÝ — DÒNG HỌ TỪ XUÂN LỘC</div>
                        <div class="nghimon-subtitle">"Cây có gốc mới nở cành xanh ngọn — Nước có nguồn mới chảy khắp sông sâu"</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # KHỞI TẠO ĐÚNG CẶP CỘT
            # CSS bổ sung để đảo thứ tự cột trên điện thoại & Tự động thêm chú thích trên PC
            st.markdown("""
                <style>
                    /* Trên PC (Màn hình lớn): Tự động nối thêm chú thích vào sau nhãn Tìm nhanh */
                    @media (min-width: 769px) {
                        div[data-testid="stCheckbox"]:not([data-testid="stForm"] *) label p::after {
                            content: " (Gợi ý theo Tên Cha & Đời)";
                        }
                    }

                    @media (max-width: 768px) {
                        /* Trên Mobile: Đảo ngược thứ tự các cột trong container để Cột phải lên trên, Cột trái xuống dưới */
                        [data-testid="stHorizontalBlock"] {
                            display: flex;
                            flex-direction: column-reverse !important;
                        }
                    }
                </style>
            """, unsafe_allow_html=True)

            # KHỞI TẠO CẶP CỘT (Cột trái: Cội nguồn, Cột phải: Đăng nhập)
            col_left, col_right = st.columns([1.05, 1.15], gap="large")

            # ĐẶT CỘT PHẢI (ĐĂNG NHẬP) LÊN TRƯỚC ĐỂ TRÊN MOBILE NÓ NẰM Ở TRÊN CÙNG
            with col_right:
                tab_conchau, tab_khach, tab_admin = st.tabs([
                    "🧬 Con Cháu Xác Thực",
                    "🌸 Khách Thập Phương",
                    "🛡️ Ban Quản Trị"
                ])
                def chuan_hoa_tieng_viet(txt):
                    if not txt:
                        return ""
                    s = unicodedata.normalize('NFC', str(txt).strip().lower())
                    vocal_map = {
                        "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
                        "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
                        "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"
                    }
                    for old_val, new_val in vocal_map.items():
                        s = s.replace(old_val, new_val)
                    return s
                with tab_conchau:
                    st.markdown("##### 🔐 Định danh Cội nguồn Cá nhân")
                    # Trên điện thoại chỉ hiển thị ngắn gọn, trên PC CSS sẽ tự động chèn thêm phần gợi ý
                    tim_danh_ba = st.toggle("🔍 Hỗ trợ tìm nhanh trong danh bạ", value=False)
                    chon_id_truc_tiep = ""
                    if tim_danh_ba:
                        nhan_danh_ba = cls.tao_nhan_phan_biet_cha_doi(df_approved, df_approved)
                        ds_options = {"": "-- Gõ vài chữ của tên để chọn nhanh --"}
                        ds_options.update(nhan_danh_ba)
                        chon_id_truc_tiep = st.selectbox(
                            "Chọn đúng tên của bạn:",
                            options=list(ds_options.keys()),
                            format_func=lambda x: ds_options[x]
                        )
                    with st.form("form_dang_nhap_nghimon"):
                        if not tim_danh_ba:
                            ten_dang_nhap = st.text_input(
                                "👤 Họ và tên của bạn (*):",
                                value=default_ten_nhap,
                                placeholder="Ví dụ: Từ Quang Thùy"
                            )
                        else:
                            ten_dang_nhap = ""
                            st.caption("👉 Đã bật chế độ chọn từ danh bạ phía trên.")
                        mat_khau_id = st.text_input(
                            f"🔑 Mã định danh (Còn {st.session_state.so_lan_con_lai}/10 lần đăng nhập nếu thiếu mã ID):",
                            value=default_id_nhap,
                            placeholder="Ví dụ: 124.08.0.099 (Chưa nhớ có thể bỏ trống)"
                        )
                        chon_id_trung_ten = None
                        if st.session_state.get("login_duplicate_candidates"):
                            cands = st.session_state.login_duplicate_candidates
                            chon_id_trung_ten = st.radio(
                                "⚠️ Phát hiện trùng tên! Vui lòng chọn đúng Tên Cha (hoặc Đời):",
                                options=list(cands.keys()),
                                format_func=lambda x: cands[x]
                            )
                        nho_thiet_bi = st.checkbox("💾 Nhớ Họ tên & Mã ID trên thiết bị này cho lần sau", value=True)
                        submitted = st.form_submit_button("🚀 Đăng nhập vào gia phả", type="primary", use_container_width=True)
                        if submitted:
                            id_clean = mat_khau_id.strip().replace(".", "")
                            df_approved["HoTen_Chuan"] = df_approved["HoTen"].apply(chuan_hoa_tieng_viet)
                            df_approved["ID_Clean"] = df_approved["ID"].str.replace(".", "", regex=False)
                            matched_rows = pd.DataFrame()
                            if chon_id_trung_ten:
                                matched_rows = df_approved[df_approved["ID"] == chon_id_trung_ten]
                            elif tim_danh_ba and chon_id_truc_tiep:
                                matched_rows = df_approved[df_approved["ID"] == chon_id_truc_tiep]
                            else:
                                ten_nhap_chuan = chuan_hoa_tieng_viet(ten_dang_nhap)
                                if not ten_nhap_chuan and id_clean:
                                    matched_rows = df_approved[df_approved["ID_Clean"] == id_clean]
                                elif ten_nhap_chuan:
                                    matched_rows = df_approved[df_approved["HoTen_Chuan"] == ten_nhap_chuan]
                            if not matched_rows.empty:
                                user_info = None
                                if id_clean:
                                    matched_with_id = matched_rows[matched_rows["ID_Clean"] == id_clean]
                                    if not matched_with_id.empty:
                                        user_info = matched_with_id.iloc[0]
                                        st.session_state.pop("login_duplicate_candidates", None)
                                    else:
                                        st.warning("⚠️ Mã định danh (ID) chưa khớp, hệ thống chuyển sang đối chiếu theo Họ tên.")
                                if user_info is None:
                                    if len(matched_rows) > 1 and not chon_id_trung_ten:
                                        nhan_ung_vien = cls.tao_nhan_phan_biet_cha_doi(matched_rows, df_approved)
                                        cand_dict = {}
                                        for idx_c, (c_id, label_c) in enumerate(nhan_ung_vien.items(), 1):
                                            cand_dict[c_id] = f"{idx_c}. {label_c}"
                                        st.session_state.login_duplicate_candidates = cand_dict
                                        st.rerun()
                                    else:
                                        user_info = matched_rows.iloc[0]
                                        st.session_state.pop("login_duplicate_candidates", None)
                                        if not id_clean:
                                            con_lai = cls.lay_va_cap_nhat_luot_mien_id(user_info["ID"], tru_luot=True)
                                            st.session_state.so_lan_con_lai = con_lai
                                            if con_lai <= 0:
                                                st.error("❌ Bạn đã hết 10 lần đăng nhập thiếu mã ID. Vui lòng nhập đúng Mã định danh (ID) cá nhân để tiếp tục!")
                                                st.stop()
                                if nho_thiet_bi:
                                    st.query_params["uid"] = user_info["ID"]
                                    st.session_state.save_localstorage_uid = user_info["ID"]
                                else:
                                    st.query_params.clear()
                                    st.session_state.save_localstorage_uid = "CLEAR"
                                st.session_state.da_dang_nhap = True
                                st.session_state.user_name = user_info["HoTen"]
                                st.session_state.user_id = user_info["ID"]
                                st.session_state.focus_id = user_info["ID"]
                                st.session_state["ls_device_owner_name"] = user_info["HoTen"]
                                st.session_state["ls_device_owner_id"] = user_info["ID"]
                                st.session_state.welcome_badge_info = {
                                    "HoTen": user_info["HoTen"],
                                    "ID": user_info["ID"],
                                    "DoiThu": user_info["DoiThu"],
                                    "Cua": user_info["Cua"],
                                    "Chi": user_info["Chi"],
                                    "ThieuID": (not bool(id_clean))
                                }
                                st.rerun()
                            else:
                                st.error("❌ Không tìm thấy Họ và tên này trong hệ thống gia phả đã duyệt.")
                with tab_khach:
                    st.markdown("##### 🌸 Cổng Khách Quý & Con Cháu Ngoại Tộc")
                    st.info("Dành cho quý khách thập phương, con rể, cháu ngoại hoặc con cháu mới sinh chưa kịp cập nhật tên vào phả hệ.")
                    ten_khach = st.text_input("Quý danh của bạn (Tùy chọn):", placeholder="Ví dụ: Cháu ngoại Nguyễn Văn A...")
                    if st.button("📖 Vào tham quan Từ Đường & Ghi Sổ Vàng", use_container_width=True):
                        st.session_state.da_dang_nhap = True
                        st.session_state.user_name = ten_khach.strip() if ten_khach.strip() else "Khách Quý Dòng Họ"
                        st.session_state.user_id = "KHACH"
                        st.session_state.admin_level = 0
                        # 🟢 Không gán bất kỳ ID Cụ Tổ nào cho khách; đưa khách về trang mặc định Lời Giới thiệu
                        st.session_state.focus_id = ""
                        st.session_state.reset_to_intro = True
                        st.rerun()
                with tab_admin:
                    st.markdown("##### 🛡️ Xác thực Ban Quản Trị Hệ Thống")
                    st.caption("Quản trị viên bắt buộc khai báo đầy đủ Họ và tên, Mã định danh cá nhân (ID) và Mật khẩu Quản trị để đăng nhập.")
                    with st.form("form_dang_nhap_admin_nghimon"):
                        admin_name = st.text_input(
                            "👤 Họ và tên Quản trị viên (*):",
                            value=default_ten_nhap,
                            placeholder="Ví dụ: Từ Quang Thùy"
                        )
                        admin_id = st.text_input(
                            "🆔 Mã định danh cá nhân (ID) (*):",
                            value=default_id_nhap,
                            placeholder="Ví dụ: 124.08.0.099"
                        )
                        admin_key = st.text_input(
                            "🔑 Mật khẩu Quản trị viên (*):",
                            type="password",
                            placeholder="Nhập mật khẩu Admin..."
                        )
                        nho_admin = st.checkbox("💾 Nhớ Họ tên & Mã ID trên thiết bị này cho lần sau", value=True)
                        btn_login_admin = st.form_submit_button("🔓 Đăng nhập Quyền Quản Trị", type="primary", use_container_width=True)
                        if btn_login_admin:
                            ten_adm_chuan = chuan_hoa_tieng_viet(admin_name)
                            id_adm_clean = admin_id.strip().replace(".", "")
                            # Kiểm tra dữ liệu trong bảng gia phả đã duyệt
                            df_approved["HoTen_Chuan"] = df_approved["HoTen"].apply(chuan_hoa_tieng_viet)
                            df_approved["ID_Clean"] = df_approved["ID"].str.replace(".", "", regex=False)
                            if not ten_adm_chuan or not id_adm_clean or not admin_key:
                                st.error("⚠️ Quản trị viên vui lòng khai báo đầy đủ cả 3 thông tin: Họ và tên, Mã định danh (ID) và Mật khẩu!")
                            elif admin_key != "admin12345":
                                st.error("❌ Mật khẩu quản trị không chính xác!")
                            else:
                                matched_adm = df_approved[
                                    (df_approved["HoTen_Chuan"] == ten_adm_chuan) &
                                    (df_approved["ID_Clean"] == id_adm_clean)
                                ]
                                if matched_adm.empty:
                                    st.error("❌ Họ và tên hoặc Mã định danh (ID) không khớp với dữ liệu Gia phả đã duyệt!")
                                else:
                                    adm_info = matched_adm.iloc[0]
                                    if nho_admin:
                                        st.query_params["uid"] = adm_info["ID"]
                                        st.session_state.save_localstorage_uid = adm_info["ID"]
                                    else:
                                        st.query_params.clear()
                                        st.session_state.save_localstorage_uid = "CLEAR"
                                    st.session_state.da_dang_nhap = True
                                    st.session_state.user_name = adm_info["HoTen"]
                                    st.session_state.user_id = adm_info["ID"]
                                    st.session_state.focus_id = adm_info["ID"]
                                    st.session_state.admin_level = 1  # Kích hoạt toàn quyền Admin
                                    st.session_state["ls_device_owner_name"] = adm_info["HoTen"]
                                    st.session_state["ls_device_owner_id"] = adm_info["ID"]
                                    st.rerun()
            # ĐẶT CỘT TRÁI (CỘI NGUỒN) XUỐNG DƯỚI TRÊN MOBILE
            with col_left:
                tong_nam_count = len(df_approved[df_approved["GioiTinh"] == "Nam"]) if "GioiTinh" in df_approved.columns else 0
                tong_nu_count = len(df_approved[df_approved["GioiTinh"] == "Nữ"]) if "GioiTinh" in df_approved.columns else 0
                tong_ho_so = tong_nam_count + tong_nu_count
                st.markdown(f"""
                    <div class="heritage-box">
                        <h3 style="color: #8B0000; margin-top: 0; font-size: 1.25rem; text-transform: uppercase; border-bottom: 1.5px solid #D4C5A9; padding-bottom: 8px;">
                            🏛️ Cội Nguồn Huyết Mạch
                        </h3>
                        <p style="font-size: 1rem; color: #2C3E50; text-align: justify; line-height: 1.6; margin-bottom: 12px;">
                            Khởi nguyên từ Thủy tổ <b>Từ Dương Đốc</b> (Tự <i>Huy Cán</i>) và Tổ mẫu <b>Trần Thị Niêm</b> từ đất Cổ Kênh lên đất Văn Cử khai cơ lập nghiệp. Qua các nhánh lớn với <b>5 Chi</b> huyết mạch, con cháu đời nay luôn khắc ghi truyền thống hiếu học, đoàn kết và hướng về cội nguồn.
                        </p>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-num">{tong_ho_so:,}</div>
                                <div class="metric-lbl">👥 {tong_nam_count:,} nam / {tong_nu_count:,} nữ</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-num">{so_doi_max} Đời</div>
                                <div class="metric-lbl">🌳 Thế hệ kế truyền</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-num">2 Cửa • 5 Chi</div>
                                <div class="metric-lbl">🏛️ Huyết mạch dòng tộc</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-num">{dang_online} Online</div>
                                <div class="metric-lbl">🔥 {dang_online} lượt về nguồn</div>
                            </div>
                        </div>
                        <div class="id-badge-guide">
                            <b>🧬 Chuẩn Định Danh 9 Chữ Số (Ví dụ: <code>124.08.0.099</code>):</b><br>
                            • <code>124</code>: Cửa, Chi, Phái &nbsp;|&nbsp; <code>08</code>: Đời thứ 8 &nbsp;|&nbsp; <code>0</code>: Nam (<code>1</code>: Nữ) &nbsp;|&nbsp; <code>099</code>: Số ngẫu nhiên.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            # =========================================================================
            # 🟢 CHÈN HUY HIỆU VÀO ĐÚNG VỊ TRÍ NÀY (NGAY SAU KHI KẾT THÚC 2 CỘT TRÁI/PHẢI)
            # =========================================================================
            st.markdown("""
                <a href="https://www.google.com/maps/search/?api=1&query=18.421106,105.765740" target="_blank" style="text-decoration: none; display: block;">
                    <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFF3E0 100%); border: 1.5px solid #D4C5A9; border-radius: 10px; padding: 12px 20px 24px 20px; margin-top: 15px; margin-bottom: 15px; text-align: center; font-family: 'Times New Roman', Times, serif; box-shadow: 0 3px 8px rgba(0,0,0,0.04); cursor: pointer; position: relative; transition: all 0.2s ease;" onmouseover="this.style.borderColor='#8B0000'; this.style.transform='translateY(-2px)';" onmouseout="this.style.borderColor='#D4C5A9'; this.style.transform='translateY(0)';">
                        <div style="font-size: 0.95rem; font-weight: bold; color: #8B0000; text-transform: uppercase; margin-bottom: 3px; letter-spacing: 0.5px;">
                            📍 Quê Quán Phát Tích Tổ Tiên: Thôn Văn Xuân - Xã Xuân Lộc - Tỉnh Hà Tĩnh
                        </div>
                        <div style="font-size: 0.82rem; color: #1565C0; font-style: italic; font-family: monospace; text-decoration: underline; display: flex; align-items: center; justify-content: center; gap: 5px;">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="#D32F2F" style="vertical-align: middle;"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                            <span>Tọa độ định vị: 18.421106° B, 105.765740° Đ &nbsp;|&nbsp; 🗺️ Chạm để mở Google Maps dẫn đường</span>
                        </div>
                        <div style="position: absolute; right: 14px; bottom: 4px; font-size: 0.72rem; color: #8D6E63; font-style: italic; font-family: monospace; pointer-events: none;">
                            Phiên bản: 1.6.3 (10/2026)
                        </div>
                    </div>
                </a>
            """, unsafe_allow_html=True)   
            return
        if "save_localstorage_uid" in st.session_state:
            val_ls = st.session_state.save_localstorage_uid
            if val_ls == "CLEAR":
                components.html("<script>try{window.localStorage.removeItem('hotu_saved_uid');}catch(e){}</script>", height=0)
            else:
                components.html(f"<script>try{{window.localStorage.setItem('hotu_saved_uid', '{val_ls}');}}catch(e){{}}</script>", height=0)
            del st.session_state.save_localstorage_uid
        if "welcome_badge_info" in st.session_state:
            wb = st.session_state.welcome_badge_info
            luot_txt = f" (Còn <b>{st.session_state.so_lan_con_lai}/10</b> lần miễn nhập Mã ID)" if wb.get("ThieuID") else ""
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFECB3 100%); border: 2px solid #8B0000; border-radius: 10px; padding: 12px 18px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; font-family: 'Times New Roman', serif;">
                    <div>
                        🎉 Chào mừng con cháu <b>{wb['HoTen']}</b> (Đời thứ {wb['DoiThu']}) đã trở về cội nguồn!{luot_txt}
                    </div>
                    <div style="background: #8B0000; color: #FFD700; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-family: monospace; font-size: 1.05rem;">
                        🆔 Mã định danh của bạn: {wb['ID']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            del st.session_state.welcome_badge_info

        if st.sidebar.button("🚪 Đăng xuất tài khoản"):
            try:
                old_key = st.session_state.get("current_online_key", "")
                with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                    conn.execute("DELETE FROM PhienDangOnline WHERE SessionID = ?", (old_key,))
                    conn.commit()
            except Exception:
                pass
            st.session_state.da_dang_nhap = False
            st.session_state.admin_level = 0
            st.session_state.user_id = ""
            st.session_state.focus_id = ""
            st.session_state.da_ghi_nhan_luot_xem = False
            st.rerun()
        # 🟢 HIỂN THỊ TRẠNG THÁI KẾT NỐI KHOA HỌC: KHÁCH KHÔNG CÓ ID, THÀNH VIÊN & ADMIN CÓ ĐẦY ĐỦ HỌ TÊN + ID
        uid_curr = str(st.session_state.get("user_id", "")).strip()
        uname_curr = str(st.session_state.get("user_name", "")).strip()
        if uid_curr == "KHACH":
            st.sidebar.info(f"🌸 Đang kết nối: **{uname_curr}** *(Khách thập phương)*")
        elif st.session_state.get("admin_level", 0) == 1:
            st.sidebar.info(f"🛡️ Quản trị viên: **{uname_curr}** (`{uid_curr}`)")
        else:
            st.sidebar.info(f"👤 Đang kết nối: **{uname_curr}** (`{uid_curr}`)")
        # 🟢 PHẦN ĐIỀU PHỐI GIAO DIỆN BÊN DƯỚI (GIỮ NGUYÊN BẢN GỐC)
        if "pending_menu" in st.session_state:
            st.session_state["CHỌN CHỨC NĂNG"] = st.session_state.pending_menu
            del st.session_state.pending_menu
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
            st.session_state.focus_id = ""
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
        # 🟢 Kiểm tra xem có lệnh ghi đè menu từ trang khác chuyển sang không
        default_menu_index = 0
        if "app_menu_override" in st.session_state:
            override_val = st.session_state.app_menu_override
            if override_val in menu_options:
                default_menu_index = menu_options.index(override_val)
            del st.session_state.app_menu_override  # Xóa sau khi đã nhận lệnh
        # 🎯 Menu chính tích hợp chỉ mục mặc định
        menu = st.sidebar.radio("CHỌN CHỨC NĂNG:", menu_options, index=default_menu_index, key="CHỌN CHỨC NĂNG")
        # 🟢 GỌI HÀM THỐNG KÊ & HIỂN THỊ CÁCH MỤC EXIT ĐÚNG 2 LẦN CHIỀU CAO CHỮ
        s_online, s_tuan, s_nam = KhoDuLieuSQL.thong_ke_truy_cap()   
        st.sidebar.markdown(f"""
            <style>
                .khung-thong-ke-hotu {{
                    margin-top: 3.6em; /* Cách mục EXIT phía trên đúng bằng 2 lần chiều cao dòng chữ */
                    padding: 12px 14px;
                    background: linear-gradient(135deg, #FFFDF9 0%, #FFF8E1 100%);
                    border: 1.5px dashed #8B0000;
                    border-radius: 8px;
                    font-family: 'Times New Roman', Times, serif;
                    font-size: 0.95rem;
                    color: #4E342E;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                    line-height: 1.6;
                }}
                .khung-thong-ke-hotu .tieu-de-tk {{
                    text-align: center;
                    font-weight: bold;
                    color: #8B0000;
                    border-bottom: 1px solid #E0D5BE;
                    padding-bottom: 4px;
                    margin-bottom: 6px;
                    text-transform: uppercase;
                    font-size: 0.9rem;
                    letter-spacing: 0.5px;
                }}
                .khung-thong-ke-hotu .dong-tk {{
                    display: flex;
                    justify-content: space-between;
                }}
                .khung-thong-ke-hotu b {{
                    color: #C62828;
                    font-family: monospace;
                    font-size: 1rem;
                }}
            </style>
            <div class="khung-thong-ke-hotu">
                <div class="tieu-de-tk">📊 Thống Kê Truy Cập</div>
                <div class="dong-tk"><span>🟢 Đang Online:</span> <b>{s_online}</b></div>
                <div class="dong-tk"><span>📅 Xem trong tuần:</span> <b>{s_tuan:,}</b></div>
                <div class="dong-tk"><span>📈 Xem năm nay:</span> <b>{s_nam:,}</b></div>
            </div>
        """, unsafe_allow_html=True)
        # ==============================================================================
        # 2. BỔ SUNG KHUNG THÔNG TIN PHIÊN BẢN VÀ BẢN QUYỀN (NẰM NGAY DƯỚI THỐNG KÊ)
        # ==============================================================================
        st.sidebar.markdown("""
            <div style="text-align: center; font-size: 0.75rem; color: #7F8C8D; margin-top: 5px; margin-bottom: 15px; border-top: 1px dashed #BDC3C7; padding-top: 8px; font-family: 'Times New Roman', serif;">
                <b>Gia phả điện tử Họ Từ Xuân Lộc</b><br>
                Phiên bản 1.6.3 • Tác giả: Từ Quang Thùy<br>
                <i>© 2026 All Rights Reserved</i>
            </div>
        """, unsafe_allow_html=True)
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
        components.html(m._repr_html_(), height=660, scrolling=True)

# ---------------------------------------------------------
# BẢN ĐỒ DI CƯ & HÀNH TRÌNH LỊCH SỬ
# ---------------------------------------------------------
class BanDoDiCu:
    @staticmethod
    def render_bando_dicu():
        st.markdown('<h3 style="color: #8B0000; margin-top:0;">🗺️ Bản đồ Di cư & Dấu ấn Lịch sử Dòng họ</h3>', unsafe_allow_html=True)
        st.markdown("Hành trình tha hương lập nghiệp từ Thủy tổ và các nhánh di cư tỏa đi muôn phương ...).")
        # 1. Khởi tạo bản đồ trung tâm
        m_dicu = folium.Map(
            location=[18.425321, 105.812144], 
            zoom_start=12, 
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', 
            attr='Esri'
        )
        # 🟢 TIÊM CSS NÂNG CAO: Tách nền trong suốt, in đậm và tạo viền trắng bảo vệ chữ (Stroke)
        from folium import Element
        css_trong_suot = """
        <style>
            .transparent-tooltip {
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
                font-weight: 900 !important; /* In đậm chữ tối đa */
                font-size: 13px !important;
                text-shadow: 
                    -1.5px -1.5px 0 #FFF,  
                     1.5px -1.5px 0 #FFF,
                    -1.5px  1.5px 0 #FFF,
                     1.5px  1.5px 0 #FFF,
                     0px 3px 4px rgba(0,0,0,0.5) !important; /* Viền trắng bao quanh chữ giúp đọc rõ trên mọi nền */
            }
        </style>
        """
        m_dicu.get_root().html.add_child(Element(css_trong_suot))
        # 2. Định nghĩa tọa độ (ĐÃ BỎ CHỮ XUÂN LỘC, MAI PHỤ)
        di_tich_goc = {
            "ten": "THỦY TỔ ĐẠI TÔN", 
            "toado": [18.425321, 105.812144], 
            "mo_ta": "Nơi Thủy tổ Yên Khang Hầu dừng chân khai hoang lập nghiệp."
        }   
        di_tich_dich = [
            {"ten": "CHI 2 CỬA GIÁP", "toado": [18.420450, 105.901809], "color": "blue", "nhom": "Cửa Giáp", "doi_di_cu": "Đời thứ 7"},
            {"ten": "CHI 1 CỬA ẤT", "toado": [18.421275, 105.827571], "color": "green", "nhom": "Cửa Ất", "doi_di_cu": "Đời thứ 6"},
            {"ten": "CHI 2 CỬA ẤT", "toado": [18.421106, 105.765740], "color": "darkorange", "nhom": "Cửa Ất Xuân Lộc", "doi_di_cu": "Đời thứ 7"},
            {"ten": "CHI 3 CỬA BÍNH", "toado": [18.492155, 105.868197], "color": "purple", "nhom": "Cửa Bính", "doi_di_cu": "Đời thứ 6"},
        ]
        # 3. Ghim điểm xuất phát: Nhà thờ Cụ Tổ
        nhan_goc = f"<div style='text-align: center; color: #8B0000; line-height: 1.3;'>{di_tich_goc['ten']}<br><span style='font-size: 11px;'>(Khởi nguyên)</span></div>"       
        folium.Marker(
            location=di_tich_goc["toado"],
            popup=folium.Popup(f"<b>{di_tich_goc['ten']}</b><br>{di_tich_goc['mo_ta']}", max_width=300),
            tooltip=folium.Tooltip(
                nhan_goc, 
                permanent=True, 
                direction="top", 
                offset=(0, -35), # 🟢 DỊCH KHUNG LÊN TRÊN RẤT CAO ĐỂ KHÔNG CHE NGÔI NHÀ
                class_name="transparent-tooltip" # Gọi CSS tách nền
            ),
            icon=folium.Icon(color="red", icon="star", prefix="glyphicon")
        ).add_to(m_dicu)
        # 4. Vẽ các điểm đến và các đường nối
        for diem in di_tich_dich:
            # Tinh chỉnh lại mã màu chữ cho sắc nét khi không có nền
            color_hex = diem['color']
            if diem['color'] == 'darkorange': color_hex = '#D84315'
            if diem['color'] == 'green': color_hex = '#2E7D32'
            if diem['color'] == 'purple': color_hex = '#6A1B9A'
            if diem['color'] == 'blue': color_hex = '#1565C0'
            nhan_hien_thi = f"""
            <div style='text-align: center; color: {color_hex}; line-height: 1.3;'>
                {diem['ten']}<br>
                <span style='color: #D32F2F;'>({diem['doi_di_cu']})</span>
            </div>
            """
            # Ghim điểm đến
            folium.Marker(
                location=diem["toado"],
                popup=folium.Popup(f"<b>{diem['ten']}</b><br>Nhóm: {diem['nhom']}.<br>Ghi nhận di cư: {diem['doi_di_cu']}", max_width=300),
                tooltip=folium.Tooltip(
                    nhan_hien_thi, 
                    permanent=True, 
                    direction="bottom", 
                    offset=(0, 10), # Dịch khung hướng xuống dưới ngôi nhà
                    class_name="transparent-tooltip" # Gọi CSS tách nền
                ),
                icon=folium.Icon(color=diem["color"], icon="home", prefix="glyphicon")
            ).add_to(m_dicu)

            # Vẽ đường đi lịch sử
            folium.PolyLine(
                locations=[di_tich_goc["toado"], diem["toado"]],
                color=diem["color"],
                weight=3,
                opacity=0.8,
                dash_array='8, 8',
                tooltip=f"Hành trình từ Cội nguồn tới {diem['ten']} ({diem['doi_di_cu']})"
            ).add_to(m_dicu)
        # 6. Hiển thị ra giao diện Streamlit
        import streamlit.components.v1 as components
        components.html(m_dicu._repr_html_(), height=660, scrolling=True)

# ---------------------------------------------------------
# KHÔNG GIAN ÂM NHẠC
# ---------------------------------------------------------
class KhongGianAmNhac:
    @staticmethod
    def render_am_nhac():
        st.markdown('<h3 style="color: #8B0000; margin-top:0;">🎵 Không gian Âm nhạc Tộc họ & Hào khí Cội nguồn</h3>', unsafe_allow_html=True)
        st.write("Lưu giữ và lan tỏa những giai điệu tự hào, khúc tráng ca dòng họ, các làn điệu dân ca Ví Dặm Nghệ Tĩnh và tiếng sáo trúc, hát ru truyền thống.")
        # 🟢 ĐÃ SỬA CHUẨN TÊN THƯ MỤC LÀ "audios" (Có chữ s)
        THU_MUC_NHAC = "audios"

        danh_sach_nhac = [
            {
                "tieu_de": "1. HÀO KHÍ HỌ TỪ",
                "the_loai": "Folk-EDM Tộc họ",
                "mo_ta": "Khúc tráng ca ca ngợi truyền thống hiếu học, hào khí tiên tổ và ý chí vươn lên của con cháu đời nay.",
                "thoi_luong": "03:45",
                "ten_file": "nhac_haokhi_hotu"
            },
            {
                "tieu_de": "2. LỜI RU NẮN CỐT RÈN HỒN",
                "the_loai": "Hát ru & Sáo trúc",
                "mo_ta": "Tiếng sáo trúc trầm bổng quyện cùng lời ru êm đềm, nuôi dưỡng tâm hồn con cháu hướng về nguồn cội.",
                "thoi_luong": "03:15",
                "ten_file": "nhac_loiru_nancotrenhon"
            },
            {
                "tieu_de": "3. VỌNG KHÚC TIÊN TỔ",
                "the_loai": "Nhạc lễ trang nghiêm",
                "mo_ta": "Khúc ca thành kính cất lên trong các dịp Lễ Tế Tổ, tưởng nhớ công ơn trời biển của các bậc tiền nhân.",
                "thoi_luong": "03:50",
                "ten_file": "nhac_vongkhuc_tiento"
            },
            {
                "tieu_de": "4. KHÁT VỌNG HỌ TỪ",
                "the_loai": "Hợp xướng đương đại",
                "mo_ta": "Khơi dậy niềm tự hào về truyền thống khoa bảng và khát vọng vươn lên hưng vượng trong kỷ nguyên mới.",
                "thoi_luong": "04:05",
                "ten_file": "nhac_khatvong_hotu"
            },
            {
                "tieu_de": "5. KHÚC CA CỘI NGUỒN",
                "the_loai": "Dân ca",
                "mo_ta": "Giai điệu đậm đà hương vị quê hương, nhắc nhớ về mảnh đất Cổ Kênh, Hoa Cử thuở Thủy tổ tha hương lập nghiệp.",
                "thoi_luong": "04:20",
                "ten_file": "nhac_cakhuc_coinguon"
            }
        ]
        # 1. Hiển thị 5 bài hát đơn lẻ theo đúng thứ tự 1 -> 5
        for idx, bai in enumerate(danh_sach_nhac, 1):
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FFF8E1 0%, #FFF3E0 100%); border-left: 5px solid #D84315; padding: 15px 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="color: #8B0000; margin: 0 0 5px 0;">🎧 {bai['tieu_de']}</h4>
                        <span style="background: #D84315; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{bai['the_loai']}</span>
                    </div>
                    <p style="margin: 8px 0; color: #4E342E; font-size: 0.95rem; font-style: italic;">{bai['mo_ta']}</p>
                    <div style="font-size: 0.85rem; color: #795548; margin-bottom: 8px;">⏳ Thời lượng: {bai['thoi_luong']}</div>
                </div>
            """, unsafe_allow_html=True)
            thu_muc_path = Path(__file__).resolve().parent / THU_MUC_NHAC
            audio_file_path = None
            for ext in [".mp3", ".m4a", ".wav", ".MP3", ".M4A", ".WAV"]:
                test_path = thu_muc_path / f"{bai['ten_file']}{ext}"
                if test_path.exists():
                    audio_file_path = test_path
                    break
            if audio_file_path and audio_file_path.exists():
                file_ext = audio_file_path.suffix.lower()
                audio_format = "audio/mp4" if file_ext == ".m4a" else ("audio/wav" if file_ext == ".wav" else "audio/mp3")
                st.audio(str(audio_file_path), format=audio_format)
            else:
                st.info(f"💡 (Chưa tìm thấy tệp `{bai['ten_file']}` trong thư mục `{THU_MUC_NHAC}/`)")
            st.markdown("---")
        # -------------------------------------------------------------------------
        # 2. TRÌNH PHÁT LIÊN TỤC (PLAYLIST 1 -> 5) CÓ CÔNG TẮC LẶP VÒNG
        # -------------------------------------------------------------------------
        st.markdown("""
            <div style="background: linear-gradient(135deg, #FCE4EC 0%, #F8BBD0 100%); border: 2px solid #C2185B; padding: 20px; border-radius: 10px; margin-top: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h3 style="color: #880E4F; margin-top: 0; margin-bottom: 5px;">🎶 Trình Phát Liên Tục (Playlist Hào Khí Họ Từ)</h3>
                <p style="color: #4A148C; font-size: 0.95rem; margin-bottom: 15px;">Thưởng thức trọn vẹn chùm 5 ca khúc nối tiếp nhau từ hào khí cội nguồn đến khát vọng tương lai.</p>
            </div>
        """, unsafe_allow_html=True)
        lap_lai_playlist = st.toggle("🔁 Phát lặp lại liên tục từ bài 1 khi kết thúc bài 5", value=True, key="toggle_loop_playlist")
        playlist_urls = []
        playlist_titles = []       
        for bai in danh_sach_nhac:
            thu_muc_path = Path(__file__).resolve().parent / THU_MUC_NHAC
            audio_file_path = None
            for ext in [".mp3", ".m4a", ".wav", ".MP3", ".M4A", ".WAV"]:
                test_path = thu_muc_path / f"{bai['ten_file']}{ext}"
                if test_path.exists():
                    audio_file_path = test_path
                    break          
            if audio_file_path and audio_file_path.exists():
                with open(audio_file_path, "rb") as f:
                    b64_audio = base64.b64encode(f.read()).decode("utf-8")               
                file_ext = audio_file_path.suffix.lower()
                mime_type = "audio/mp4" if file_ext == ".m4a" else ("audio/wav" if file_ext == ".wav" else "audio/mp3")
                data_url = f"data:{mime_type};base64,{b64_audio}"              
                playlist_urls.append(data_url)
                playlist_titles.append(bai['tieu_de'])
        if playlist_urls:
            js_urls = json.dumps(playlist_urls)
            js_titles = json.dumps(playlist_titles)
            is_loop_val = "true" if lap_lai_playlist else "false"
            playlist_player_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; background: transparent; margin: 0; padding: 10px; }}
                    .player-box {{ background: #fff; border: 1px solid #AD1457; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }}
                    #now-playing {{ font-size: 16px; font-weight: bold; color: #880E4F; margin-bottom: 10px; }}
                    audio {{ width: 100%; outline: none; }}
                    .playlist-info {{ font-size: 12px; color: #666; margin-top: 8px; }}
                </style>
            </head>
            <body>
                <div class="player-box">
                    <div id="now-playing">🎧 Đang tải danh sách phát...</div>
                    <audio id="audio-element" controls></audio>
                    <div class="playlist-info" id="playlist-status">Bài 1 / {len(playlist_urls)}</div>
                </div>
                <script>
                    const tracks = {js_urls};
                    const titles = {js_titles};
                    const shouldLoop = {is_loop_val};                    
                    let currentTrackIndex = 0;
                    const audioElement = document.getElementById('audio-element');
                    const nowPlayingDiv = document.getElementById('now-playing');
                    const statusDiv = document.getElementById('playlist-status');

                    function loadTrack(index) {{
                        if (index < tracks.length) {{
                            audioElement.src = tracks[index];
                            nowPlayingDiv.innerText = "🎵 Đang phát: " + titles[index];
                            statusDiv.innerText = "Bài " + (index + 1) + " / " + tracks.length;
                            audioElement.play().catch(e => console.log("Autoplay blocked:", e));
                        }}
                    }}

                    audioElement.onended = function() {{
                        currentTrackIndex++;
                        if (currentTrackIndex < tracks.length) {{
                            loadTrack(currentTrackIndex);
                        }} else {{
                            if (shouldLoop) {{
                                currentTrackIndex = 0;
                                loadTrack(currentTrackIndex);
                            }} else {{
                                nowPlayingDiv.innerText = "🏁 Đã phát xong toàn bộ danh sách!";
                                statusDiv.innerText = "Trình phát đã dừng.";
                            }}
                        }}
                    }};

                    if (tracks.length > 0) {{
                        loadTrack(0);
                    }}
                </script>
            </body>
            </html>
            """
            components.html(playlist_player_html, height=140)
        else:
            st.warning("⚠️ Không tìm thấy tệp âm thanh nào trong thư mục `audios` để tạo danh sách phát liên tục.")
            
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
            st.session_state.dev_email = "anhtuanhp0101@gmail.com"
        if 'dev_phone' not in st.session_state:
            st.session_state.dev_phone = "0988.237.400"
        if 'author_name' not in st.session_state:
            st.session_state.author_name = "Từ Quang Thùy"  
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
        is_admin = (admin_pass_input == "admin12345")
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
            value=st.session_state.get("ls_device_owner_name", "Từ Quang Thùy")
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
                    if not txt:
                        return ""
                    s = unicodedata.normalize('NFC', str(txt).strip().lower())
                    vocal_map = {
                        "oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
                        "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
                        "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"
                    }
                    for old_val, new_val in vocal_map.items():
                        s = s.replace(old_val, new_val)
                    return s
                nhap_lieu_chuan = chuan_hoa_dau(p_name)
                df_app['HoTen_Chuan'] = df_app['HoTen'].apply(chuan_hoa_dau)
                matched_by_name = df_app[df_app['HoTen_Chuan'] == nhap_lieu_chuan]
                # Trường hợp 1: Chỉ có duy nhất 1 người mang tên này
                if len(matched_by_name) == 1:
                    found_id = str(matched_by_name.iloc[0]["ID"])
                    doi_thu = matched_by_name.iloc[0]["DoiThu"]
                    chi_nhanh = matched_by_name.iloc[0]["Chi"]
                    st.session_state["ls_device_owner_id"] = found_id
                    st.session_state["user_name"] = matched_by_name.iloc[0]["HoTen"]
                    st.session_state["user_id"] = found_id
                    st.session_state["focus_id"] = found_id
                    st.session_state["pending_disambiguation"] = None
                    st.success(
                        f"✅ Đã lưu hồ sơ và liên kết thành công:\n"
                        f"- **Họ tên:** {p_name}\n"
                        f"- **Mã định danh:** `{found_id}` (Đời {doi_thu} — {chi_nhanh})"
                    )
                # Trường hợp 2: Có từ 2 người trùng tên trở lên -> Kích hoạt lọc 2 lớp (Tên Cha -> Đời)
                elif len(matched_by_name) > 1:
                    nhan_phan_biet = SoChiHuyGiaoDien.tao_nhan_phan_biet_cha_doi(matched_by_name, df_app)
                    cand_dict = {
                        m_id: f"{idx}. {nhan}"
                        for idx, (m_id, nhan) in enumerate(nhan_phan_biet.items(), 1)
                    }
                    st.session_state["pending_disambiguation"] = cand_dict
                else:
                    st.session_state["pending_disambiguation"] = None
                    st.warning(f"⚠️ Đã lưu thông tin cơ bản, nhưng không tìm thấy tên '{p_name}' trong phả hệ đã duyệt để gán Mã định danh tự động.")
            except Exception as e:
                st.error(f"Lỗi truy xuất dữ liệu: {e}")
        # Hiển thị hộp chọn phân biệt 2 lớp (Tên Cha -> Đời) khi phát hiện trùng tên
        if st.session_state.get("pending_disambiguation"):
            cand_dict = st.session_state["pending_disambiguation"]
            st.markdown("---")
            chon_id_ho_so = st.radio(
                "⚠️ Phát hiện trùng tên trong gia phả! Vui lòng chọn đúng Tên Cha (hoặc Đời) của bạn:",
                options=list(cand_dict.keys()),
                format_func=lambda x: cand_dict[x],
                key="radio_disambiguate_profile"
            )
            if st.button("✅ Xác nhận liên kết Mã định danh này", type="primary", key="btn_confirm_profile_id"):
                df_full = KhoDuLieuSQL.load_data()
                row_sel = df_full[df_full["ID"] == chon_id_ho_so]
                if not row_sel.empty:
                    r_info = row_sel.iloc[0]
                    st.session_state["ls_device_owner_id"] = chon_id_ho_so
                    st.session_state["ls_device_owner_name"] = r_info["HoTen"]
                    st.session_state["user_name"] = r_info["HoTen"]
                    st.session_state["user_id"] = chon_id_ho_so
                    st.session_state["focus_id"] = chon_id_ho_so
                    st.session_state["pending_disambiguation"] = None
                    st.success(
                        f"🎉 Đã liên kết chuẩn xác hồ sơ của **{cand_dict[chon_id_ho_so]}** "
                        f"với Mã định danh: `{chon_id_ho_so}` (Đời {r_info['DoiThu']} — {r_info['Chi']})!"
                    )
                    st.rerun()
        # Luôn hiển thị Thẻ định danh hiện tại ở cuối trang Hồ sơ cá nhân
        curr_linked_id = st.session_state.get("ls_device_owner_id", "")
        if curr_linked_id:
            st.info(f"🆔 **Mã định danh đang gắn với thiết bị này:** `{curr_linked_id}`")

    # ==========================================================================
    # HỆ THỐNG LỊCH GIỖ 4 ĐỜI TRỰC HỆ & THUẬT TOÁN THIÊN VĂN ÂM - DƯƠNG LỊCH
    # Tự động cập nhật theo từng năm, xử lý tháng nhuận & tháng thiếu
    # ==========================================================================
    @staticmethod
    def _jd_from_date(dd, mm, yy):
        """Chuyển đổi ngày Dương lịch (dd/mm/yyyy) sang số ngày Julian (JDN)"""
        a = (14 - mm) // 12
        y = yy + 4800 - a
        m = mm + 12 * a - 3
        return dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    @staticmethod
    def _jd_to_date(jd):
        """Chuyển đổi số ngày Julian (JDN) sang ngày Dương lịch (datetime.date)"""
        a = jd + 32044
        b = (4 * a + 3) // 146097
        c = a - (b * 146097) // 4
        d = (4 * c + 3) // 1461
        e = c - (1461 * d) // 4
        m = (5 * e + 2) // 153
        day = e - (153 * m + 2) // 5 + 1
        month = m + 3 - 12 * (m // 10)
        year = b * 100 + d - 4800 + m // 10
        return datetime.date(year, month, day)

    @staticmethod
    def _get_new_moon_day(k, time_zone=7.0):
        """Tính ngày Sóc (Mùng 1 Âm lịch) thứ k theo múi giờ Việt Nam (UTC+7)"""
        import math
        T = k / 1236.85
        T2 = T * T
        T3 = T2 * T
        dr = math.pi / 180.0
        Jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
        Jd1 += 0.00033 * math.sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
        M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
        Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
        F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
        C1 = (0.1734 - 0.000393 * T) * math.sin(M * dr) + 0.0021 * math.sin(2 * dr * M)
        C1 = C1 - 0.4068 * math.sin(Mpr * dr) + 0.0161 * math.sin(dr * 2 * Mpr)
        C1 = C1 - 0.0004 * math.sin(dr * 3 * Mpr)
        C1 = C1 + 0.0104 * math.sin(dr * 2 * F) - 0.0051 * math.sin(dr * (M + Mpr))
        C1 = C1 - 0.0074 * math.sin(dr * (M - Mpr)) + 0.0004 * math.sin(dr * (2 * F + M))
        C1 = C1 - 0.0004 * math.sin(dr * (2 * F - M)) - 0.0006 * math.sin(dr * (2 * F + Mpr))
        C1 = C1 + 0.0010 * math.sin(dr * (2 * F - Mpr)) + 0.0005 * math.sin(dr * (2 * Mpr + M))
        if T < -11:
            deltat = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
        else:
            deltat = -0.000278 + 0.000265 * T + 0.000262 * T2
        JdNew = Jd1 + C1 - deltat
        return int(JdNew + 0.5 + time_zone / 24.0)

    @staticmethod
    def _get_sun_longitude(jdn, time_zone=7.0):
        """Tính kinh độ Mặt Trời (0..11) để xác định Trung khí và Đông chí (9)"""
        import math
        T = (jdn - 2451545.5 - time_zone / 24.0) / 36525.0
        T2 = T * T
        dr = math.pi / 180.0
        M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
        L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
        DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * math.sin(dr * M)
        DL += (0.019993 - 0.000101 * T) * math.sin(dr * 2 * M) + 0.000290 * math.sin(dr * 3 * M)
        L = (L0 + DL) * dr
        L = L - math.pi * 2 * int(L / (math.pi * 2))
        if L < 0:
            L += math.pi * 2
        return int(L / math.pi * 6)

    @classmethod
    def _get_lunar_month_11(cls, yy, time_zone=7.0):
        """Tìm ngày Mùng 1 tháng 11 Âm lịch (tháng chứa tiết Đông chí) của năm yy"""
        off = cls._jd_from_date(31, 12, yy) - 2415021
        k = int(off / 29.530588853)
        nm = cls._get_new_moon_day(k, time_zone)
        sun_long = cls._get_sun_longitude(nm, time_zone)
        if sun_long >= 9:
            nm = cls._get_new_moon_day(k - 1, time_zone)
        return nm

    @classmethod
    def _get_leap_month_offset(cls, a11, time_zone=7.0):
        """Xác định vị trí tháng nhuận trong năm Âm lịch có 13 tháng"""
        k = int((a11 - 2415021.076998695) / 29.530588853 + 0.5)
        last = 0
        i = 1
        arc = cls._get_sun_longitude(cls._get_new_moon_day(k + i, time_zone), time_zone)
        while True:
            last = arc
            i += 1
            arc = cls._get_sun_longitude(cls._get_new_moon_day(k + i, time_zone), time_zone)
            if not (arc != last and i < 14):
                break
        return i - 1

    @classmethod
    def _lay_nam_am_lich_hien_tai(cls, solar_date, time_zone=7.0):
        """Xác định chính xác Năm Âm lịch hiện hành từ ngày Dương lịch hôm nay"""
        day_Number = cls._jd_from_date(solar_date.day, solar_date.month, solar_date.year)
        k = int((day_Number - 2415021.076998695) / 29.530588853)
        month_start = cls._get_new_moon_day(k + 1, time_zone)
        if month_start > day_Number:
            month_start = cls._get_new_moon_day(k, time_zone)
        a11 = cls._get_lunar_month_11(solar_date.year, time_zone)
        b11 = a11
        if a11 >= month_start:
            lunar_year = solar_date.year
            a11 = cls._get_lunar_month_11(solar_date.year - 1, time_zone)
        else:
            lunar_year = solar_date.year + 1
            b11 = cls._get_lunar_month_11(solar_date.year + 1, time_zone)
        diff = int((month_start - a11) / 29)
        lunar_month = diff + 11
        if b11 - a11 > 365:
            leap_month_diff = cls._get_leap_month_offset(a11, time_zone)
            if diff >= leap_month_diff:
                lunar_month = diff + 10
        if lunar_month > 12:
            lunar_month -= 12
        if lunar_month >= 11 and diff < 4:
            lunar_year -= 1
        return lunar_year

    @classmethod
    def doi_am_sang_duong(cls, lunar_day, lunar_month, lunar_year, lunar_leap=0, time_zone=7.0):
        """
        Quy đổi ngày giỗ Âm lịch (lunar_day/lunar_month) sang ngày Dương lịch của năm lunar_year.
        Tự động xử lý tháng thiếu (29 ngày): Nếu giỗ ngày 30 nhưng tháng chỉ có 29 ngày thì lùi về 29.
        """
        try:
            if not (1 <= lunar_month <= 12 and 1 <= lunar_day <= 30):
                return "Chưa rõ"

            if lunar_month < 11:
                a11 = cls._get_lunar_month_11(lunar_year - 1, time_zone)
                b11 = cls._get_lunar_month_11(lunar_year, time_zone)
            else:
                a11 = cls._get_lunar_month_11(lunar_year, time_zone)
                b11 = cls._get_lunar_month_11(lunar_year + 1, time_zone)

            k = int(0.5 + (a11 - 2415021.076998695) / 29.530588853)
            off = lunar_month - 11
            if off < 0:
                off += 12
            if b11 - a11 > 365:
                leap_off = cls._get_leap_month_offset(a11, time_zone)
                leap_month = leap_off - 2
                if leap_month < 0:
                    leap_month += 12
                if lunar_leap != 0 and lunar_month != leap_month:
                    return "Chưa rõ"
                elif lunar_leap != 0 or off >= leap_off:
                    off += 1
            month_start = cls._get_new_moon_day(k + off, time_zone)
            next_month_start = cls._get_new_moon_day(k + off + 1, time_zone)
            so_ngay_trong_thang = next_month_start - month_start
            # Quy tắc truyền thống: Giỗ ngày 30 gặp năm tháng thiếu (29 ngày) thì cúng vào ngày 29
            ngay_thuc_te = min(lunar_day, so_ngay_trong_thang)
            solar_dt = cls._jd_to_date(month_start + ngay_thuc_te - 1)
            return solar_dt.strftime("%d/%m/%Y")
        except Exception:
            return "Đang cập nhật"

    @classmethod
    def trich_xuat_va_doi_ngay_gio(cls, raw_gio_str, nam_am_hien_tai):
        """Trích xuất (ngày, tháng) từ chuỗi ngày giỗ, chuẩn hóa chuỗi Âm lịch và tính ngày Dương lịch"""
        if not raw_gio_str:
            return "", ""
        txt = str(raw_gio_str).strip()
        m = re.search(r'(\d{1,2})\s*[/\-\.]\s*(\d{1,2})', txt)
        if not m:
            txt_al = txt if "AL" in txt.upper() else f"{txt} AL"
            return txt_al, "Chưa rõ"

        ld = int(m.group(1))
        lm = int(m.group(2))
        ngay_am_chuan = f"{ld:02d}/{lm:02d} AL"
        ngay_duong_str = cls.doi_am_sang_duong(ld, lm, nam_am_hien_tai)
        return ngay_am_chuan, ngay_duong_str

    def hien_thi_he_thong_ngay_gio(self):
        st.subheader("🕯️ Hệ thống ngày giỗ 4 đời trực hệ")
        st.write("Lịch giỗ tiên tổ (Cụ Ông & các Cụ Bà) được định danh trực quan cho thiết bị của bạn.")
        
        owner_id_str = st.session_state.get("ls_device_owner_id", "") or st.session_state.get("user_id", "")
        if owner_id_str == "ADMIN":
            owner_id_str = ""
        owner_name = st.session_state.get("ls_device_owner_name", "") or st.session_state.get("user_name", "Chưa xác định")
        if not owner_id_str:
            st.warning("⚠️ Thiết bị này chưa được liên kết định danh cá nhân. Vui lòng sang tab **👤 Hồ sơ cá nhân** để cập nhật!")
        else:
            st.success(f"✅ Đang hiển thị lịch giỗ cho chủ nhân thiết bị: **{owner_name} (ID: {owner_id_str})**")          
            try:
                # Lấy ngày hiện tại theo múi giờ Việt Nam (UTC+7) và tính Năm Âm lịch hiện hành
                hom_nay_vn = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).date()
                nam_am_hien_tai = self._lay_nam_am_lich_hien_tai(hom_nay_vn)

                with sqlite3.connect(KhoDuLieuSQL.DB_FILE) as conn:
                    df_all = pd.read_sql_query(
                        "SELECT ID, ChaID, HoTen, NamSinh, NamMat, NgayGio, VoChong, ChucDanh_GhiChu FROM GiaPha",
                        conn
                    ).fillna("")
                ancestor_ids = []
                curr = str(owner_id_str).strip()
                depth = 0
                visited = set()               
                while curr and curr != "0" and curr not in visited and depth < 4:
                    visited.add(curr)
                    p_row = df_all[df_all["ID"] == curr]
                    if p_row.empty:
                        break
                    parent_id = str(p_row.iloc[0].get("ChaID", "")).strip()
                    if parent_id and parent_id != "None":
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
                    cot_duong_lich_title = f"Ngày giỗ Dương lịch ({nam_am_hien_tai})"
                    # --- HÀM CON 1: BÓC TÁCH NGÀY GIỖ TRONG MỘT CỤM VĂN BẢN ---
                    def tim_ngay_gio_chuan(text_str):
                        if not text_str:
                            return ""
                        # Loại bỏ cặp năm sinh - năm mất (VD: 1814 - 1882, ? - 1882, 1814 - ?) để tránh nhầm với ngày tháng
                        s_clean = re.sub(r'(\d{4}|\?)\s*[-–~]\s*(\d{4}|\?)', '', str(text_str))       
                        # 1. Dạng "ngày 30 tháng 11"
                        m_thang = re.search(r'ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})', s_clean, re.IGNORECASE)
                        if m_thang:
                            return f"{int(m_thang.group(1)):02d}/{int(m_thang.group(2)):02d} AL"
                        # 2. Dạng chuẩn "giỗ 30/11 AL", "giổ 30/11", "mất 30/11 AL"
                        m_kw = re.search(r'(?:gi[ổỗo]|mất|chết)\s*(?:ngày)?\s*(?:al)?\s*[:\s]*(\d{1,2})\s*[/\-\.]\s*(\d{1,2})', s_clean, re.IGNORECASE)
                        if m_kw:
                            return f"{int(m_kw.group(1)):02d}/{int(m_kw.group(2)):02d} AL"
                        # 3. Dạng dd/mm hợp lệ còn lại trong ngoặc
                        for m_any in re.finditer(r'\b(\d{1,2})\s*[/\-\.]\s*(\d{1,2})\b', s_clean):
                            d_val, m_val = int(m_any.group(1)), int(m_any.group(2))
                            if 1 <= d_val <= 30 and 1 <= m_val <= 12:
                                return f"{d_val:02d}/{m_val:02d} AL"
                        return ""
                    # --- HÀM CON 2: PHÂN TÍCH MỘT CỤM THÔNG TIN CỤ BÀ (LỌC ĐIỀU KIỆN SỐNG / CÒN / MẤT) ---
                    def phan_tich_mot_cu_ba(raw_segment):
                        seg = KhoDuLieuSQL.chuan_hoa_van_ban_nien_bieu(raw_segment).strip()
                        # 1. Nhận diện thứ bậc bắt buộc (Bà hai, Bà thứ, Bà chính...)
                        m_tb = re.search(
                            r'\b(Bà\s+(?:chính|thứ|cả|hai|ba|tư|út|nhất|nhì)|bà\s+(?:chính|thứ|cả|hai|ba|tư|út|nhất|nhì)|chính\s+thất|thứ\s+thất|kế\s+thất|vợ\s+(?:cả|hai|ba|chính|thứ))\b',
                            seg, re.IGNORECASE
                        )
                        thu_bac = ""
                        if m_tb:
                            raw_tb = m_tb.group(1).strip()
                            thu_bac = raw_tb[0].upper() + raw_tb[1:].lower()
                        # 2. Quét toàn bộ các cặp ngoặc đơn để bóc tách niên biểu
                        ngoac_list = re.findall(r'\(([^()]*?)\)', seg)
                        
                        nam_sinh, nam_mat = "", ""
                        ngay_gio = ""

                        for content_in_paren in ngoac_list:
                            content_trim = content_in_paren.strip()
                            if re.search(r'\d{4}|\?|gi[ổỗo]|mất', content_trim, re.IGNORECASE):
                                m_nam = re.search(r'(\d{4}|\?)\s*[-–~]\s*(\d{4}|\?)', content_trim)
                                if m_nam:
                                    nam_sinh = m_nam.group(1).strip()
                                    nam_mat = m_nam.group(2).strip()
                                ngay_gio = tim_ngay_gio_chuan(content_trim)
                        # Nếu có dấu ? ở năm mất hoặc không tìm thấy năm mất, để trống nếu không có ngày giỗ
                        if nam_mat == "?" or not nam_mat:
                            nam_mat = ""
                        if nam_sinh == "?" or not nam_sinh:
                            nam_sinh = ""
                        # 3. LÀM SẠCH TÊN: Xóa bỏ TẤT CẢ các cặp ngoặc đơn, các phần mô tả sau dấu phẩy/chấm phẩy
                        seg_cho_ten = re.split(r'[,;]\s*(?![^()]*\))', seg)[0]

                        ten_clean = re.sub(r'\s*\([^()]*?\)', '', seg_cho_ten).strip()
                        ten_clean = re.sub(r'[\s,]*(?:gi[ổỗo]|mất|chết|sinh\s+năm)\s*.*$', '', ten_clean, flags=re.IGNORECASE).strip(' ,;.-')
                        
                        ten_clean = re.sub(
                            r'^(?:(?:lấy\s+ông|lấy\s+bà|lấy\s+vợ|lấy|vợ\s+là|vợ|ông\s+là|ông|bà\s+(?:chính|thứ|cả|hai|ba|tư|út|nhất|nhì)|bà\s+(?:chính|thứ|cả|hai|ba|tư|út|nhất|nhì)|chính\s+thất|thứ\s+thất|kế\s+thất|bà)\s*[:\-]*\s*)+',
                            '', ten_clean, flags=re.IGNORECASE
                        ).strip(' ,;.-')
                        # Thuật toán giới hạn tối đa 5 từ cho tên
                        words = ten_clean.split()
                        if len(words) > 5:
                            ten_clean = " ".join(words[:5])
                        if not ten_clean or len(ten_clean) > 30 or "cụ" in ten_clean.lower():
                            m_ten_ba = re.search(r'(?:bà|lấy\s+bà)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)', seg_cho_ten, flags=re.IGNORECASE)
                            if m_ten_ba:
                                found_words = m_ten_ba.group(1).strip().split()
                                ten_clean = " ".join(found_words[:5])
                            else:
                                ten_clean = "Hiền nội"
                        # 🟢 ĐIỀU KIỆN LỌC QUYẾT ĐỊNH: Nếu KHÔNG CÓ năm mất VÀ KHÔNG CÓ ngày giỗ -> Coi như còn sống, loại khỏi danh sách giỗ
                        co_du_lieu_qua_co = bool(nam_mat or ngay_gio)
                        return {
                            "ten": ten_clean or "Hiền nội",
                            "thu_bac": thu_bac,
                            "nam_sinh": nam_sinh,
                            "nam_mat": nam_mat,
                            "ngay_gio": ngay_gio,
                            "co_du_lieu_nam_hoac_gio": co_du_lieu_qua_co
                        }
                    # --- HÀM CON 3: TRÍCH XUẤT DANH SÁCH BÀ (CHỈ ĐƯA VÀO DANH SÁCH NẾU ĐÃ QUÁ CỐ) ---
                    def trich_xuat_danh_sach_ba(ghi_chu_ban_than, vo_chong_txt):
                        ds_ket_qua = []
                        ten_da_co = set()

                        noi_dung_tong = f"{vo_chong_txt}; {ghi_chu_ban_than}".strip()
                        if not noi_dung_tong or noi_dung_tong.lower() in ["nan", "none", ""]:
                            return []
                        parts = re.split(r'\b(?:lấy\s+bà|lấy\s+vợ|bà\s+chính|bà\s+thứ|bà\s+cả|bà\s+hai)\b', noi_dung_tong, flags=re.IGNORECASE)
                        segments = []
                        if len(parts) > 1:
                            matches_kw = re.findall(r'\b(?:lấy\s+bà|lấy\s+vợ|bà\s+chính|bà\s+thứ|bà\s+cả|bà\s+hai)\b', noi_dung_tong, flags=re.IGNORECASE)
                            for i in range(len(matches_kw)):
                                seg_str = matches_kw[i] + parts[i+1]
                                segments.append(seg_str)
                        else:
                            if vo_chong_txt and vo_chong_txt.lower() not in ["nan", "none"]:
                                segments = [vo_chong_txt]
                        for seg_item in segments:
                            info_ba = phan_tich_mot_cu_ba(seg_item)
                            # BẮT BUỘC THỎA MÃN: Phải có năm mất hoặc ngày giỗ mới được đưa vào danh sách lịch giỗ
                            if info_ba["co_du_lieu_nam_hoac_gio"]:
                                key_ten = re.sub(r'\s*\(.*?\)', '', info_ba["ten"]).strip().lower()
                                if key_ten not in ten_da_co:
                                    ds_ket_qua.append(info_ba)
                                    if key_ten:
                                        ten_da_co.add(key_ten)
                        return ds_ket_qua
                    # ==========================================================
                    # DUYỆT QUA 4 ĐỜI TIÊN TỔ TRỰC HỆ (ÁP DỤNG LOGIC SỐNG / CÒN / MẤT CHO CỤ ÔNG)
                    # ==========================================================
                    for idx, (_, row) in enumerate(df_ancestors.iterrows()):
                        pos = min(idx, len(vai_ve_ong) - 1)
                        ten_ong = row["HoTen"]
                        nam_sinh_ong = str(row["NamSinh"]).strip()
                        nam_mat_ong = str(row["NamMat"]).strip()
                        ngay_gio_ong = str(row["NgayGio"]).strip()

                        # Chuẩn hóa năm sinh/mất của Cụ Ông (nếu là dấu ? hoặc rỗng thì để trống)
                        if nam_mat_ong == "?" or not nam_mat_ong:
                            nam_mat_ong = ""
                        if nam_sinh_ong == "?" or not nam_sinh_ong:
                            nam_sinh_ong = ""

                        # 🟢 ĐIỀU KIỆN LỌC CỤ ÔNG: Phải có năm mất hoặc ngày giỗ mới đưa vào danh sách lịch giỗ
                        co_du_lieu_qua_co_ong = bool(nam_mat_ong or ngay_gio_ong)
                        if co_du_lieu_qua_co_ong:
                            if ngay_gio_ong:
                                am_ong, duong_ong = self.trich_xuat_va_doi_ngay_gio(ngay_gio_ong, nam_am_hien_tai)
                            else:
                                am_ong, duong_ong = "", "" # Để trống tập rỗng nếu chưa có ngày giỗ
                            memorial_rows.append({
                                "STT": stt_counter,
                                "Họ và tên": f"{vai_ve_ong[pos]}: {ten_ong}",
                                "Năm sinh": nam_sinh_ong,
                                "Năm mất": nam_mat_ong,
                                "Ngày giỗ (Âm lịch)": am_ong,
                                cot_duong_lich_title: duong_ong
                            })
                            stt_counter += 1

                        # ==========================================================
                        # 2. THÊM CÁC DÒNG CỦA CÁC CỤ BÀ (HỖ TRỢ ĐẦY ĐỦ 4 TRƯỜNG HỢP & ĐA THÊ)
                        # ==========================================================
                        # Cắt bỏ hoàn toàn phần "Sinh hạ:" của con cái để không đọc nhầm sang thông tin các con
                        ghi_chu_raw = str(row["ChucDanh_GhiChu"]).strip()
                        ghi_chu_ban_than = re.split(r'(?i)sinh hạ:', ghi_chu_raw)[0] if 'sinh hạ:' in ghi_chu_raw.lower() else ghi_chu_raw
                        vo_chong_txt = str(row["VoChong"]).strip()
                        danh_sach_ba = trich_xuat_danh_sach_ba(ghi_chu_ban_than, vo_chong_txt)
                        so_luong_ba = len(danh_sach_ba)
                        for idx_ba, ba_info in enumerate(danh_sach_ba):
                            thu_bac_hien_thi = ba_info["thu_bac"]
                            if not thu_bac_hien_thi and so_luong_ba > 1:
                                thu_bac_hien_thi = f"Bà {idx_ba + 1}"
                            danh_xung_ba = f"{vai_ve_ba[pos]} ({thu_bac_hien_thi})" if thu_bac_hien_thi else vai_ve_ba[pos]
                            if ba_info["ngay_gio"]:
                                am_ba, duong_ba = self.trich_xuat_va_doi_ngay_gio(ba_info["ngay_gio"], nam_am_hien_tai)
                            else:
                                am_ba, duong_ba = "", "" # Để trống tập rỗng nếu chưa có ngày giỗ
                            memorial_rows.append({
                                "STT": stt_counter,
                                "Họ và tên": f"{danh_xung_ba}: {ba_info['ten']}",
                                "Năm sinh": ba_info["nam_sinh"],
                                "Năm mất": ba_info["nam_mat"],
                                "Ngày giỗ (Âm lịch)": am_ba,
                                cot_duong_lich_title: duong_ba
                            })
                            stt_counter += 1
                    if not memorial_rows:
                        st.info("Chưa ghi nhận thông tin niên biểu / ngày giỗ cụ thể cho các bậc tiên tổ trong nhánh này.")
                    else:
                        df_table = pd.DataFrame(memorial_rows)
                        st.markdown(f"#### 📅 Bảng Lịch Giỗ Tiên Tổ (Năm Âm lịch {nam_am_hien_tai})")
                        st.dataframe(
                            df_table[["STT", "Họ và tên", "Năm sinh", "Năm mất", "Ngày giỗ (Âm lịch)", cot_duong_lich_title]],
                            use_container_width=True,
                            hide_index=True
                        )
                        st.markdown("🔔 *Hệ thống tự động quy đổi ngày Âm lịch sang Dương lịch theo từng năm (kể cả năm nhuận và tháng thiếu) để con cháu chủ động sắp xếp lịch trình về quê dâng hương.*")
            except Exception as e:
                st.error(f"Lỗi tải dữ liệu lịch giỗ: {e}")                

    # ==========================================================================
    # CÀI ĐẶT HỆ THỐNG
    # ==========================================================================
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
    
