import asyncio
import edge_tts

# Toàn bộ nội dung Lời giới thiệu đã được trau chuốt dấu ngắt hơi chuẩn xác
NOI_DUNG = """
Lời giới thiệu dòng họ Từ Xuân Lộc.
Kính dâng anh linh tiên tổ, lưu truyền huyết mạch cho muôn đời con cháu.

Uống nước nhớ nguồn, ăn quả nhớ người trồng cây là đạo lý ngàn đời của dân tộc ta. Đối với mỗi dòng tộc, cuốn gia phả trước đây thường chỉ nằm lặng lẽ ở một góc tủ trong nhà, nay đã được số hóa toàn diện để vượt qua mọi giới hạn về không gian và thời gian. Ứng dụng Gia phả điện tử dòng Họ Từ Xuân Lộc ra đời với sứ mệnh đưa dữ liệu huyết mạch đến với tất cả mọi người; giúp con cháu dù đi làm ăn xa muôn phương hay ở bất cứ chân trời góc bể nào cũng có thể dễ dàng tiếp cận, tra cứu cội nguồn và hướng về tổ tiên với lòng thành kính sâu sắc nhất.

Theo tư liệu quý giá và các bản phổ ký do các bậc cao niên để lại, Thủy tổ dòng họ ta là cụ Từ Dương Đốc, huyết danh Huy Cán, một bậc thầy thuốc y dược tế sinh đầy đức độ. Nhân thời buổi binh đao ly loạn cuối thời Hậu Lê, Lê Mạt, Ngài cùng hiền thê là bà Trần Thị Niêm đã rời quê hương Cổ Kênh, Thạch Hà, tha hương lên làng Hoa Cử, Văn Cử khai hoang phá thạch, lập nghiệp sinh cơ.

Từ nền móng vững chắc ấy, trải qua bao thăng trầm lịch sử, dòng họ ta tự hào là một dòng tộc hiếu học, khoa bảng hiển hách, đời nào cũng có người hiển đạt, giữ trọng trách lớn trong triều đình phong kiến, làm quan to, tướng lĩnh quân đội, cán bộ lãnh đạo cấp cao, trí thức lớn và doanh nhân thành đạt trên mọi miền Tổ quốc. Từ hai ngọn nguồn chính là Cửa Giáp, do cụ Từ Hữu Trí thủ giữ, và Cửa Ất, do cụ Từ Hữu Mưu gánh vác, các thế hệ con cháu luôn nối tiếp truyền thống hào hùng, tôi luyện ý chí kiên trung, tô thắm thêm bảng vàng truyền thống vẻ vang của dòng họ Từ.

Để gìn giữ gia phong và giải quyết triệt để bài toán tránh tình trạng thế thứ hỗn đồ tung tích dán đoạn hay rủi ro hôn thú đồng tông, ứng dụng đã áp dụng chuẩn hóa cấu trúc Mã định danh chín chữ số, ví dụ một hai bốn, chấm không bảy, chấm không, chấm không bốn chín. Cấu trúc khoa học này được quy ước vô cùng chặt chẽ: trong đó một hai bốn là cửa, chi, phái; không bảy là đời; không hoặc một là giới tính; và các số tiếp theo là số thứ tự được sắp xếp theo đúng nguyên tắc sinh trưởng trong nhánh. Nhờ nền tảng này, hệ thống tự động liên kết huyết mạch minh bạch, tuyệt đối không bao giờ có sự nhầm lẫn thế hệ.

Bên cạnh đó, để trang sử gia phả thêm phần sống động, ứng dụng tích hợp tính năng lưu trữ và hiển thị ảnh chân dung. Khi cập nhật thành viên, hình ảnh tư liệu của các cụ hay người thân sẽ được tải lên và hiển thị trang trọng ngay bên cạnh tiểu sử, tại mục tra cứu trực hệ, giúp thế hệ mai sau được tận mắt ngắm nhìn dung mạo, thần thái oai nghiêm và hiền hậu của ông cha.

Cùng với các tính năng ưu việt như sơ đồ phả hệ trực hệ và toàn cảnh với nhiều góc chiếu trực quan, cho phép phóng to thu nhỏ, kéo lướt mượt mà trên điện thoại, máy tính, kết hợp cùng hệ thống ngày giỗ bốn đời trực hệ tự động nhắc nhở, ứng dụng chính là nhịp cầu công nghệ gắn kết sắt son tình dòng tộc cho con cháu muôn đời.

Vật bổ hồ thiên, nhân sinh do Tổ; cây cối được lá xanh cành rậm là do vun trồng rễ tốt gốc sâu, dòng dõi được cha truyền con nối là nhờ phúc phước của tổ tiên dồi dào ấm hậu.

Con cháu dòng họ Từ Xuân Lộc muôn đời sau, dù ở bất cứ cương vị nào, xin hãy luôn ghi nhớ công ơn trời biển của tổ tiên, phát huy truyền thống hiếu học và khoa bảng vẻ vang, đoàn kết đùm bọc lẫn nhau, giữ gìn đạo đức gia phong, cùng chung tay làm rạng danh hai tiếng Họ Từ Xuân Lộc trên bản đồ đất nước.
"""

# Chọn giọng nữ miền Bắc truyền cảm (Hoài My), tốc độ đọc trang nghiêm, thong thả
VOICE = "vi-VN-HoaiMyNeural"
OUTPUT_FILE = "giong_doc_gioi_thieu.mp3"

async def tao_am_thanh():
    # rate="-4%" để giọng đọc trầm ấm, chậm rãi và chuẩn nghi lễ
    communicate = edge_tts.Communicate(NOI_DUNG, VOICE, rate="-4%", pitch="+0Hz")
    await communicate.save(OUTPUT_FILE)
    print("✅ Đã xuất tệp âm thanh thành công: giong_doc_gioi_thieu.mp3")

if __name__ == "__main__":
    asyncio.run(tao_am_thanh())
