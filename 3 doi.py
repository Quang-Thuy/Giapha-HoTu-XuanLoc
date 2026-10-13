from graphviz import Digraph

# Khởi tạo đồ thị
dot = Digraph(comment='Sơ đồ 3 đời đầu', format='png', node_attr={
    'shape': 'box', 
    'style': 'filled,rounded', 
    'fontname': 'Times-Bold', 
    'fontsize': '12',
    'margin': '0.08,0.03'
})
dot.attr(rankdir='TB', nodesep='0.5', ranksep='0.8', bgcolor='#FFFFFF', pad='0.4')

# Tiêu đề không viền, cân xứng tuyệt đối
dot.node("title_node", "SƠ ĐỒ PHẢ HỆ TRỰC HỆ 3 ĐỜI ĐẦU - DÒNG HỌ TỪ XUÂN LỘC", shape="plaintext", style="", fontname="Times-Bold", fontsize="17", fontcolor="#8B0000")

# Thủy Tổ hoành tráng
dot.node("node_1", "🌟 THỦY TỔ: TỪ DƯƠNG ĐỐC ① 🌟\n(Huy Cán - Người khai sơn phá thạch dòng họ)\n[ Cội nguồn linh thiêng - Đời thứ nhất ]", fillcolor="#FF5252:#B71C1C", style="filled,rounded,radial", gradientangle="45", color="#5F0000", fontcolor="#FFFFFF", penwidth="3.5", fontsize="13", margin="0.12,0.05")

dot.edge("title_node", "node_1", style="invis", minlen="1.0")

# Đời 2
dot.node("node_tri", "TỪ HỮU TRÍ ②\n(Đứng đầu Cửa Giáp)", fillcolor="#FFE0B2:#F57C00", style="filled,rounded,radial", gradientangle="45", color="#E65100", fontcolor="#FFFFFF", penwidth="2.0", fontsize="12")
dot.node("node_muu", "TỪ HỮU MƯU ②\n(Đứng đầu Cửa Ất)", fillcolor="#FFE0B2:#F57C00", style="filled,rounded,radial", gradientangle="45", color="#E65100", fontcolor="#FFFFFF", penwidth="2.0", fontsize="12")

dot.edge("node_1", "node_tri", color="#B71C1C", penwidth="2.8")
dot.edge("node_1", "node_muu", color="#B71C1C", penwidth="2.8")

# Đời 3 (7 Chi)
chi_list = [
    ("node_lien", "TỪ HỮU LIỆN ③\n★ CHI 1", "node_tri"),
    ("node_duc", "TỪ HỮU DỰC ③\n★ CHI 2", "node_tri"),
    ("node_lang", "TỪ HỮU LẠNG ③\n★ CHI 3", "node_tri"),
    ("node_man", "TỪ HỮU MÀN ③\n★ CHI 4", "node_muu"),
    ("node_hung", "TỪ HỮU HÙNG ③\n★ CHI 5", "node_muu"),
    ("node_lan", "TỪ HỮU LÂN ③\n★ CHI 6", "node_muu"),
    ("node_lac", "TỪ HỮU LẠC ③\n★ CHI 7", "node_muu")
]

for n_id, n_label, parent in chi_list:
    dot.node(n_id, n_label, fillcolor="#FFF9C4:#FBC02D", style="filled,rounded,radial", gradientangle="45", color="#F57F17", fontcolor="#3E2723", penwidth="1.5", fontsize="11")
    dot.edge(parent, n_id, color="#37474F", penwidth="1.6")

# Xuất ra file ảnh riêng biệt
dot.render(filename="so_do_3_doi_dau", cleanup=True)
print("Đã xuất file ảnh thành công: so_do_3_doi_dau.png")
