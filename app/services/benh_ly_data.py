"""
Cơ sở dữ liệu bệnh lý phổ biến - Từ khóa triệu chứng → Bệnh → Chuyên khoa
"""

BENH_LY_DB = [
    # === NỘI TỔNG QUÁT / TIÊU HÓA ===
    {"benh":"Viêm dạ dày","tu_khoa":["đau bụng","đau dạ dày","đau thượng vị","ợ chua","ợ hơi","nóng rát","buồn nôn","đầy bụng","khó tiêu","ăn không tiêu","trào ngược"],"khoa":"Nội tổng quát","loi_khuyen":"Tránh ăn cay, chua, rượu bia. Ăn đúng giờ, chia nhỏ bữa. Nên khám tiêu hóa sớm.","muc_do":"trung bình"},
    {"benh":"Trào ngược dạ dày thực quản","tu_khoa":["trào ngược","ợ nóng","nóng rát ngực","nuốt nghẹn","ho đêm","đắng miệng","ợ chua"],"khoa":"Nội tổng quát","loi_khuyen":"Không nằm ngay sau ăn, kê cao đầu giường. Tránh đồ chua cay.","muc_do":"trung bình"},
    {"benh":"Viêm đại tràng","tu_khoa":["đau bụng dưới","tiêu chảy","táo bón","đi ngoài","phân lỏng","đau quặn bụng","chướng bụng","đầy hơi","sôi bụng"],"khoa":"Nội tổng quát","loi_khuyen":"Ăn nhiều chất xơ, uống đủ nước. Khám tiêu hóa nếu kéo dài.","muc_do":"trung bình"},
    {"benh":"Ngộ độc thực phẩm","tu_khoa":["nôn","tiêu chảy","đau bụng dữ dội","sốt","ớn lạnh","mệt lả","ngộ độc","ăn vào đau"],"khoa":"Nội tổng quát","loi_khuyen":"⚠️ Bù nước ngay (oresol). Nếu nôn nhiều, tiêu chảy nặng → cấp cứu.","muc_do":"cao"},
    {"benh":"Viêm ruột thừa","tu_khoa":["đau bụng bên phải","đau hố chậu phải","sốt nhẹ","buồn nôn","chán ăn","đau khi ấn bụng"],"khoa":"Ngoại tổng quát","loi_khuyen":"⚠️ Nghi ruột thừa cần khám CẤP CỨU ngay! Không tự uống thuốc giảm đau.","muc_do":"cao"},
    {"benh":"Sỏi thận","tu_khoa":["đau lưng dữ dội","đau hông","tiểu buốt","tiểu ra máu","tiểu khó","đau lan xuống bụng dưới","sỏi thận"],"khoa":"Tiết niệu","loi_khuyen":"Uống nhiều nước (2-3L/ngày). Khám tiết niệu để siêu âm kiểm tra.","muc_do":"cao"},
    {"benh":"Nhiễm trùng đường tiểu","tu_khoa":["tiểu buốt","tiểu rắt","tiểu nhiều lần","nước tiểu đục","đau bụng dưới","tiểu gấp","nóng rát khi tiểu"],"khoa":"Tiết niệu","loi_khuyen":"Uống nhiều nước, vệ sinh sạch sẽ. Cần khám và dùng kháng sinh theo chỉ định.","muc_do":"trung bình"},
    {"benh":"Cảm cúm","tu_khoa":["sốt","ho","sổ mũi","đau họng","nhức mỏi","ớn lạnh","hắt hơi","cảm","cúm","đau người","mệt mỏi","đau cơ"],"khoa":"Nội tổng quát","loi_khuyen":"Nghỉ ngơi, uống nhiều nước ấm. Sốt >39°C hoặc >3 ngày nên khám.","muc_do":"thấp"},
    {"benh":"Viêm phổi","tu_khoa":["ho có đờm","sốt cao","khó thở","đau ngực khi ho","thở nhanh","mệt","đờm xanh","đờm vàng"],"khoa":"Hô hấp","loi_khuyen":"⚠️ Viêm phổi cần điều trị kháng sinh. Khám ngay nếu sốt cao + khó thở.","muc_do":"cao"},
    {"benh":"Viêm phế quản","tu_khoa":["ho kéo dài","ho có đờm","đau rát ngực","khó thở nhẹ","sốt nhẹ","mệt"],"khoa":"Hô hấp","loi_khuyen":"Tránh khói bụi, giữ ấm. Khám hô hấp nếu ho >2 tuần.","muc_do":"trung bình"},
    {"benh":"Hen suyễn","tu_khoa":["khó thở","thở khò khè","tức ngực","ho đêm","ho khi gắng sức","hen","suyễn"],"khoa":"Hô hấp","loi_khuyen":"Tránh dị nguyên (bụi, phấn hoa). Luôn mang theo thuốc xịt cắt cơn.","muc_do":"trung bình"},
    {"benh":"Sốt xuất huyết","tu_khoa":["sốt cao đột ngột","đau đầu dữ dội","đau sau mắt","đau cơ khớp","nổi ban","chảy máu chân răng","xuất huyết"],"khoa":"Nội tổng quát","loi_khuyen":"⚠️ NGUY HIỂM! Không uống aspirin. Bù nước, theo dõi tiểu cầu. Khám ngay!","muc_do":"cao"},

    # === TIM MẠCH ===
    {"benh":"Tăng huyết áp","tu_khoa":["huyết áp cao","đau đầu","chóng mặt","nóng mặt","nhức đầu","ù tai","hoa mắt","huyết áp"],"khoa":"Tim mạch","loi_khuyen":"Giảm muối, tập thể dục, uống thuốc đều. Đo huyết áp hàng ngày.","muc_do":"trung bình"},
    {"benh":"Thiếu máu cơ tim","tu_khoa":["đau ngực","tức ngực","đau ngực trái","khó thở khi gắng sức","đau lan vai trái","tim đập nhanh","hồi hộp"],"khoa":"Tim mạch","loi_khuyen":"⚠️ NGUY HIỂM! Đau ngực kéo dài >15 phút → gọi cấp cứu 115 ngay!","muc_do":"cao"},
    {"benh":"Rối loạn nhịp tim","tu_khoa":["tim đập nhanh","tim đập chậm","hồi hộp","đánh trống ngực","ngất","xỉu","choáng"],"khoa":"Tim mạch","loi_khuyen":"Tránh cà phê, rượu bia. Khám tim mạch để đo ECG kiểm tra.","muc_do":"trung bình"},
    {"benh":"Huyết áp thấp","tu_khoa":["huyết áp thấp","choáng váng","xây xẩm","tay chân lạnh","mệt","ngất khi đứng dậy"],"khoa":"Tim mạch","loi_khuyen":"Uống đủ nước, ăn mặn hơn, đứng dậy từ từ.","muc_do":"thấp"},

    # === THẦN KINH ===
    {"benh":"Đau nửa đầu (Migraine)","tu_khoa":["đau đầu","đau nửa đầu","nhức đầu","đau đầu dữ dội","buồn nôn","sợ ánh sáng","hoa mắt","migraine"],"khoa":"Thần kinh","loi_khuyen":"Nghỉ ngơi trong phòng tối, yên tĩnh. Khám thần kinh nếu đau thường xuyên.","muc_do":"trung bình"},
    {"benh":"Rối loạn tiền đình","tu_khoa":["chóng mặt","hoa mắt","mất thăng bằng","buồn nôn","quay cuồng","đi không vững","tiền đình"],"khoa":"Thần kinh","loi_khuyen":"Nằm yên khi lên cơn, tránh quay đầu đột ngột. Khám thần kinh.","muc_do":"trung bình"},
    {"benh":"Mất ngủ mãn tính","tu_khoa":["mất ngủ","khó ngủ","ngủ không sâu","thức giấc giữa đêm","ngủ ít","trằn trọc"],"khoa":"Thần kinh","loi_khuyen":"Hạn chế caffein, tắt điện thoại trước 1h đi ngủ. Khám nếu mất ngủ >1 tháng.","muc_do":"trung bình"},
    {"benh":"Đau dây thần kinh tọa","tu_khoa":["đau lưng lan xuống chân","tê chân","đau mông","đau thắt lưng","tê bì","đau khi ngồi lâu","thần kinh tọa"],"khoa":"Thần kinh","loi_khuyen":"Tránh ngồi lâu, tập vật lý trị liệu. Khám nếu tê yếu chân.","muc_do":"trung bình"},
    {"benh":"Trầm cảm","tu_khoa":["buồn","trầm cảm","chán nản","mất hứng thú","khó tập trung","mệt mỏi","stress","lo âu","muốn chết","tự tử"],"khoa":"Tâm thần","loi_khuyen":"⚠️ Trầm cảm là bệnh cần điều trị. Hãy tìm bác sĩ tâm thần ngay.","muc_do":"cao"},

    # === XƯƠNG KHỚP ===
    {"benh":"Thoái hóa cột sống","tu_khoa":["đau lưng","đau cổ","đau vai gáy","cứng cổ","đau khi cúi","thoái hóa","đau cột sống"],"khoa":"Xương Khớp","loi_khuyen":"Tập thể dục nhẹ, tránh mang vác nặng. Khám xương khớp.","muc_do":"trung bình"},
    {"benh":"Viêm khớp","tu_khoa":["đau khớp","sưng khớp","cứng khớp buổi sáng","đau gối","đau ngón tay","viêm khớp","khớp sưng đỏ"],"khoa":"Xương Khớp","loi_khuyen":"Chườm ấm, vận động nhẹ nhàng. Khám để xét nghiệm viêm.","muc_do":"trung bình"},
    {"benh":"Gout","tu_khoa":["đau ngón chân cái","sưng đỏ khớp","gout","gút","đau khớp đột ngột","nóng đỏ khớp"],"khoa":"Xương Khớp","loi_khuyen":"Hạn chế bia rượu, nội tạng, hải sản. Uống nhiều nước.","muc_do":"trung bình"},
    {"benh":"Thoát vị đĩa đệm","tu_khoa":["đau lưng dữ dội","tê chân","đau lan chân","yếu chân","thoát vị","đĩa đệm"],"khoa":"Xương Khớp","loi_khuyen":"Nằm nghỉ, tránh vận động mạnh. Khám để chụp MRI.","muc_do":"cao"},

    # === TAI MŨI HỌNG ===
    {"benh":"Viêm họng","tu_khoa":["đau họng","rát họng","nuốt đau","sưng họng","đỏ họng","viêm họng","ho","khàn tiếng"],"khoa":"Tai Mũi Họng","loi_khuyen":"Súc miệng nước muối ấm, uống nhiều nước. Khám nếu sốt cao.","muc_do":"thấp"},
    {"benh":"Viêm amidan","tu_khoa":["đau họng","sưng amidan","nuốt đau","sốt","hạch cổ","amidan","mủ trắng họng"],"khoa":"Tai Mũi Họng","loi_khuyen":"Súc họng nước muối, uống thuốc theo chỉ định. Tái phát nhiều có thể cần phẫu thuật.","muc_do":"trung bình"},
    {"benh":"Viêm xoang","tu_khoa":["nghẹt mũi","đau đầu vùng trán","chảy mũi","đau mặt","sổ mũi kéo dài","viêm xoang","mũi có mùi hôi","nhức hốc mắt"],"khoa":"Tai Mũi Họng","loi_khuyen":"Rửa mũi bằng nước muối sinh lý. Khám TMH nếu >10 ngày.","muc_do":"trung bình"},
    {"benh":"Viêm tai giữa","tu_khoa":["đau tai","ù tai","nghe kém","chảy mủ tai","sốt","tai đau nhức","viêm tai"],"khoa":"Tai Mũi Họng","loi_khuyen":"Không ngoáy tai, giữ tai khô. Khám TMH ngay nếu chảy mủ.","muc_do":"trung bình"},

    # === DA LIỄU ===
    {"benh":"Viêm da dị ứng","tu_khoa":["ngứa","nổi mẩn","phát ban","mẩn đỏ","dị ứng","nổi mề đay","sưng phù","ngứa da","da đỏ"],"khoa":"Da liễu","loi_khuyen":"Tránh tiếp xúc dị nguyên, không gãi. Bôi kem dưỡng ẩm.","muc_do":"thấp"},
    {"benh":"Mụn trứng cá","tu_khoa":["mụn","mụn trứng cá","mụn viêm","mụn bọc","mụn đầu đen","da nhờn","mụn sưng đỏ"],"khoa":"Da liễu","loi_khuyen":"Rửa mặt sạch, tránh nặn mụn. Khám da liễu nếu mụn nặng.","muc_do":"thấp"},
    {"benh":"Nấm da","tu_khoa":["ngứa da","vảy da","lang ben","nấm","da bong tróc","vùng da tròn đỏ","hắc lào"],"khoa":"Da liễu","loi_khuyen":"Giữ da khô ráo, dùng thuốc bôi kháng nấm. Khám nếu lan rộng.","muc_do":"thấp"},
    {"benh":"Zona thần kinh","tu_khoa":["nổi mụn nước","đau rát da","mụn nước theo dải","zona","giời leo","đau nhức theo dây thần kinh"],"khoa":"Da liễu","loi_khuyen":"Cần dùng thuốc kháng virus sớm trong 72h. Khám ngay!","muc_do":"trung bình"},

    # === MẮT ===
    {"benh":"Viêm kết mạc (đau mắt đỏ)","tu_khoa":["đau mắt","mắt đỏ","chảy nước mắt","ngứa mắt","cộm mắt","mắt sưng","đau mắt đỏ","ghèn mắt"],"khoa":"Mắt","loi_khuyen":"Rửa mắt bằng nước muối sinh lý, không dụi mắt. Rất dễ lây!","muc_do":"thấp"},
    {"benh":"Cận thị / Loạn thị","tu_khoa":["mờ mắt","nhìn không rõ","nheo mắt","mỏi mắt","nhức mắt","cận thị","loạn thị"],"khoa":"Mắt","loi_khuyen":"Khám mắt để đo thị lực và cắt kính phù hợp.","muc_do":"thấp"},
    {"benh":"Tăng nhãn áp (Glaucoma)","tu_khoa":["đau mắt dữ dội","nhìn mờ đột ngột","đau đầu","buồn nôn","thấy quầng sáng","mắt căng tức"],"khoa":"Mắt","loi_khuyen":"⚠️ CẤP CỨU! Tăng nhãn áp có thể gây mù. Khám mắt ngay!","muc_do":"cao"},

    # === NỘI TIẾT ===
    {"benh":"Đái tháo đường (Tiểu đường)","tu_khoa":["khát nước nhiều","tiểu nhiều","sụt cân","mờ mắt","mệt mỏi","đường huyết cao","tiểu đường","chậm lành vết thương"],"khoa":"Nội tiết","loi_khuyen":"Kiểm soát đường huyết, ăn kiêng, tập thể dục đều đặn.","muc_do":"trung bình"},
    {"benh":"Cường giáp","tu_khoa":["sụt cân nhanh","tim đập nhanh","run tay","ra mồ hôi nhiều","bướu cổ","mắt lồi","hồi hộp","cường giáp"],"khoa":"Nội tiết","loi_khuyen":"Cần xét nghiệm hormone tuyến giáp và điều trị sớm.","muc_do":"trung bình"},
    {"benh":"Suy giáp","tu_khoa":["mệt mỏi","tăng cân","sợ lạnh","da khô","táo bón","rụng tóc","suy giáp","chậm chạp"],"khoa":"Nội tiết","loi_khuyen":"Xét nghiệm TSH, FT4 để chẩn đoán và điều trị thay thế hormone.","muc_do":"trung bình"},

    # === RĂNG HÀM MẶT ===
    {"benh":"Sâu răng / Viêm tủy","tu_khoa":["đau răng","nhức răng","ê buốt","sâu răng","đau khi nhai","sưng nướu","đau răng ban đêm"],"khoa":"Răng Hàm Mặt","loi_khuyen":"Đánh răng 2 lần/ngày, dùng chỉ nha khoa. Khám nha khoa ngay.","muc_do":"trung bình"},
    {"benh":"Viêm nướu / Viêm nha chu","tu_khoa":["chảy máu nướu","sưng nướu","hôi miệng","răng lung lay","nướu đỏ","đau nướu"],"khoa":"Răng Hàm Mặt","loi_khuyen":"Lấy cao răng định kỳ 6 tháng/lần. Khám nha khoa.","muc_do":"thấp"},

    # === NHI KHOA ===
    {"benh":"Sốt ở trẻ em","tu_khoa":["trẻ sốt","bé sốt","con sốt","trẻ em sốt","sốt cao trẻ em","co giật","trẻ quấy khóc"],"khoa":"Nhi khoa","loi_khuyen":"Hạ sốt bằng paracetamol đúng liều. Sốt >39°C hoặc co giật → cấp cứu!","muc_do":"cao"},
    {"benh":"Tiêu chảy ở trẻ","tu_khoa":["trẻ tiêu chảy","bé đi ngoài","con tiêu chảy","trẻ nôn","trẻ mất nước"],"khoa":"Nhi khoa","loi_khuyen":"Bù nước oresol, tiếp tục cho ăn. Khám ngay nếu bé lừ đừ.","muc_do":"trung bình"},

    # === SẢN PHỤ KHOA ===
    {"benh":"Thai kỳ / Khám thai","tu_khoa":["mang thai","thai","có bầu","trễ kinh","nghén","buồn nôn buổi sáng","đau bụng khi mang thai"],"khoa":"Sản phụ khoa","loi_khuyen":"Khám thai định kỳ, bổ sung acid folic, sắt, canxi.","muc_do":"trung bình"},
    {"benh":"Rối loạn kinh nguyệt","tu_khoa":["đau bụng kinh","kinh nguyệt không đều","trễ kinh","ra máu bất thường","đau bụng dưới","rong kinh"],"khoa":"Sản phụ khoa","loi_khuyen":"Theo dõi chu kỳ, khám phụ khoa nếu bất thường kéo dài.","muc_do":"thấp"},

    # === THẬN - TIẾT NIỆU ===
    {"benh":"Suy thận","tu_khoa":["phù chân","tiểu ít","mệt mỏi","buồn nôn","ngứa da","suy thận","phù mặt sáng"],"khoa":"Tiết niệu","loi_khuyen":"Hạn chế muối, đạm. Xét nghiệm chức năng thận định kỳ.","muc_do":"cao"},

    # === CƠ XƯƠNG KHỚP KHÁC ===
    {"benh":"Bong gân / Chấn thương","tu_khoa":["bong gân","trẹo chân","sưng mắt cá","đau khi đi","chấn thương","bầm tím","gãy xương"],"khoa":"Chấn thương chỉnh hình","loi_khuyen":"Chườm đá 20 phút, nghỉ ngơi, băng ép. Chụp X-quang nếu đau nhiều.","muc_do":"trung bình"},
]

# Từ đồng nghĩa để mở rộng matching
TU_DONG_NGHIA = {
    "đau bụng": ["bụng đau","đau bao tử","đau ruột","đau dạ","nhói bụng","quặn bụng","bụng quặn"],
    "đau đầu": ["nhức đầu","nhức đầu","đau đầu","cephalalgia","đầu đau","nặng đầu"],
    "đau họng": ["rát họng","họng đau","nuốt đau","viêm họng","đau khi nuốt","họng rát","họng sưng"],
    "ho": ["ho khan","ho có đờm","ho đêm","ho kéo dài","ho sặc"],
    "sốt": ["nóng sốt","sốt cao","sốt nhẹ","sốt kéo dài","nóng người"],
    "mệt": ["mệt mỏi","uể oải","kiệt sức","không có sức","yếu","suy nhược"],
    "chóng mặt": ["hoa mắt","xây xẩm","choáng","quay cuồng","lảo đảo"],
    "khó thở": ["thở mệt","hụt hơi","thở nặng","ngạt thở","thở gấp"],
    "ngứa": ["ngứa ngáy","bứt rứt","rát da","châm chích"],
    "đau lưng": ["lưng đau","nhức lưng","mỏi lưng","đau thắt lưng"],
    "đau ngực": ["tức ngực","nặng ngực","đau tim","nhói ngực"],
    "buồn nôn": ["muốn nôn","lợm giọng","buồn ói","ói"],
    "tiêu chảy": ["đi ngoài","đi lỏng","tiêu lỏng","xì xoẹt"],
    "táo bón": ["khó đi cầu","bón","không đi ngoài được"],
    "mất ngủ": ["khó ngủ","trằn trọc","thức đêm","ngủ không được"],
    "đau răng": ["nhức răng","ê răng","buốt răng"],
    "đau mắt": ["nhức mắt","mỏi mắt","cay mắt","rát mắt"],
    "đau tai": ["tai đau","nhức tai","ù tai"],
}
