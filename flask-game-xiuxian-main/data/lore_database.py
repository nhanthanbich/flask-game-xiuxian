"""
Vietnamese Lore Database - All NPC names, locations, and story text
"""

# ==============================================================================
# SECTION 1: NPC NAMES & BACKSTORIES
# ==============================================================================

NPC_DIRECTORY = {
    # === THANH VÂN TÔNG (清雲宗) ===
    'hoa_yen': {
        'name': 'Hoa Yên',
        'name_formal': 'Độc Tôn Hoa Yên',
        'role': 'Sư phụ, trưởng môn phái',
        'backstory': '''
Hoa Yên là trưởng môn Thanh Vân Tông thế hệ thứ ba mươi lăm.
Bà từng là tiêu binh được lựa chọn đặc biệt, chiến đấu với Ma tộc
ở biên giới Bắc Hoang. Với tâm huyết dành cho dòng phái,
bà đã góp phần tái sinh Thanh Vân sau cuộc chiến biên giới.
        ''',
        'relationships': ['truong_vu', 'thanh_duc', 'khai_minh']
    },

    'truong_vu': {
        'name': 'Trương Vũ',
        'name_formal': 'Vô Ức Trương Vũ',
        'role': 'Sư huynh cao cấp, huấn luyện viên chiến đấu',
        'backstory': '''
Trương Vũ là một trong những tiêu binh mạnh nhất của Thanh Vân Tông.
Hắn từng bị ma tộc giam giữ 5 năm ở hang Bắc Hoang, nhưng đã thoát thoát
và trở về với sức mạnh tăng gấp đôi. Bây giờ hắn dạy những chiêu thức
chiến đấu khắc nghiệt cho các đệ tử mới.
        ''',
        'relationships': ['hoa_yen', 'thanh_duc']
    },

    'thanh_duc': {
        'name': 'Thanh Đức',
        'name_formal': 'Thiên Bình Thanh Đức',
        'role': 'Sư huynh trung cấp, quản lý tàng thư viện',
        'backstory': '''
Thanh Đức từng là một nhà thư tịch nổi tiếng trước khi gia nhập Thanh Vân Tông.
Hắn biết hàng trăm bí quyết tu luyện và có thể đọc các chỉ dẫn cổ xưa.
Dù không mạnh về chiến đấu, trí tuệ của hắn là tài sản lớn nhất của tông phái.
        ''',
        'relationships': ['hoa_yen', 'khai_minh']
    },

    'khai_minh': {
        'name': 'Khai Minh',
        'name_formal': 'Hợp Duân Khai Minh',
        'role': 'Sư huynh trẻ, phó chủ tích',
        'backstory': '''
Khai Minh là thế hệ trẻ nhất trong lãnh đạo Thanh Vân Tông.
Mặc dù tuổi còn trẻ, hắn đã thể hiện tài năng quân sự và chính trị excepcional.
Có nhiều tin đồn rằng hắn sẽ trở thành trưởng môn tiếp theo của Thanh Vân.
        ''',
        'relationships': ['hoa_yen', 'thanh_duc', 'truong_vu']
    },

    # === HỖN TRÂM TÔNG (混沌宗) ===
    'tu_phuong': {
        'name': 'Tử Phong',
        'name_formal': 'Vô Lượng Tử Phong',
        'role': 'Trưởng môn Hỗn Trâm Tông, thợ luyện dược',
        'backstory': '''
Tử Phong là trưởng môn Hỗn Trâm Tông, một tông phái gợi cấu và linh hoạt.
Hắn là cao thủ về luyện dược và biết cách tạo ra các loại độc dược nguy hiểm.
Tử Phong không sợ sử dụng tà pháp nếu nó giúp tông phái của hắn thắng lợi.
        ''',
        'relationships': ['huong_tu', 'thuc_chi']
    },

    'huong_tu': {
        'name': 'Hương Tú',
        'name_formal': 'Lục Lâm Hương Tú',
        'role': 'Sư nữ cao cấp, chuyên môn độc dược',
        'backstory': '''
Hương Tú là nữ nhất của Tử Phong, có khả năng luyện độc vượt trội.
Cô là con gái của một nhà chế tác độc dược nổi tiếng, nên kế thừa tài năng từ cha.
Mặc dù tính cách lạnh lùng, cô vẫn tôn trọng những người yếu hơn.
        ''',
        'relationships': ['tu_phuong', 'thuc_chi', 'khai_minh']
    },

    'thuc_chi': {
        'name': 'Thục Chi',
        'name_formal': 'Linh Tà Thục Chi',
        'role': 'Sư huynh trẻ, chiến sĩ bạo lực',
        'backstory': '''
Thục Chi là một chiến sĩ điên cuồng của Hỗn Trâm Tông.
Hắn yêu thích chiến đấu hơn bất cứ điều gì khác, và không bao giờ từ chối một trận đấu.
Mối quan hệ giữa hắn và Thanh Vân Tông rất tương tác, nhưng luôn giữ ranh giới của tôn trọng chiến sĩ.
        ''',
        'relationships': ['tu_phuong', 'huong_tu', 'truong_vu']
    },

    # === MA TỘC (魔族) ===
    'linh_trai': {
        'name': 'Linh Trại',
        'name_formal': 'Linh Chúa Linh Trài',
        'role': 'Thủ lĩnh Ma tộc từ Bắc Hoang',
        'backstory': '''
Linh Trài là thủ lĩnh Ma tộc thế kỷ này. Hắn từng toàn thắng trong chiến đấu
với Triều đình, nhưng bại trận trước sức mạnh liên hợp của các tông phái.
Bây giờ hắn lên kế hoạch phục hồi thế lực Ma tộc và lấy lại lãnh địa Bắc Hoang.
        ''',
        'relationships': ['ma_nhan']
    },

    'ma_nhan': {
        'name': 'Ma Nhân',
        'name_formal': 'Nữ Vương Ma Nhân',
        'role': 'Nữ vương Ma tộc, cách mạng gia',
        'backstory': '''
Ma Nhân là nữ vương của Ma tộc, với sức mạnh không kém Linh Trài.
Cô theo đuổi con đường kháo nhân, muốn thay đổi mối quan hệ giữa Ma tộc
và loài người. Điều này tạo ra mâu thuẫn trong lãnh đạo Ma tộc.
        ''',
        'relationships': ['linh_trai']
    },

    # === TRIỀU ĐÌNH & NPC TRUNG LẬP ===
    'quoc_su': {
        'name': 'Quốc Sư',
        'name_formal': 'Quốc Sư Tinh Thông',
        'role': 'Cố vấn chính trị triều đình',
        'backstory': '''
Quốc Sư là cố vấn chính trị lâu năm của triều đình.
Hắn có thể dự đoán những động thái của các tông phái và Ma tộc.
Quốc Sư tin rằng sức mạnh không phải là tất cả - chiến lược và tài trí mới là chìa khóa.
        ''',
        'relationships': ['hoang_de', 'linh_trai']
    },

    'hoang_de': {
        'name': 'Hoàng Đế',
        'name_formal': 'Thiên Nhuận Hoàng Đế',
        'role': 'Vị vua của triều đình',
        'backstory': '''
Hoàng Đế hiện nay là vị vua công chính, nhưng yếu về sức mạnh tuyệt đỉnh.
Hắn dựa vào Quốc Sư và lãnh chúa để duy trì sự ổn định của đất nước.
Hắn mong muốn tìm ra một vị thánh nhân có thể giúp triều đình vượt qua thế khó.
        ''',
        'relationships': ['quoc_su', 'tu_phuong', 'hoa_yen']
    },

    'lang_doc': {
        'name': 'Lang Độc',
        'name_formal': 'Giả Khoa Lang Độc',
        'role': 'Thương nhân du mục, phân phối tin tức',
        'backstory': '''
Lang Độc là một thương nhân du mục nổi tiếng, biết mọi lore và tin tức của giang hồ.
Hắn không thuộc về bất kỳ tông phái nào, nhưng có liên hệ khắp nơi.
Người ta nói rằng hắn đã sống được 200 năm nhờ một bí quyết tu luyện bí mật.
        ''',
        'relationships': []
    },
}


# ==============================================================================
# SECTION 2: LOCATION NAMES & DESCRIPTIONS
# ==============================================================================

LOCATIONS = {
    # Regions
    'qing_yun_shan': {
        'name_vn': 'Thanh Vân Sơn',
        'name_chi': '清雲山',
        'region': '清雲',
        'description': 'Nơi đặt tông môn Thanh Vân Tông, ngọn núi cao phủ đầy mây trắng. Từ đây có thể nhìn thấy toàn bộ vùng đất Trung Nguyên.',
        'significance': 'Quê hương của các chiến sĩ Thanh Vân'
    },

    'hun_tram_dong': {
        'name_vn': 'Hỗn Trâm Động',
        'name_chi': '混沌洞',
        'region': '中原',
        'description': 'Động hang sâu dưới lòng đất, nơi đặt tông môn Hỗn Trâm Tông. Không khí tươi mát, quanh năm không có ánh sáng mặt trời.',
        'significance': 'Bộ tộc của những người tà pháp'
    },

    'bac_hoang_thuc_xa': {
        'name_vn': 'Bắc Hoang Thực Xã',
        'name_chi': '北荒雪嶺',
        'region': '北荒',
        'description': 'Dãy núi tuyết trắng dưới cực bắc, nơi Ma tộc hoạt động. Nhiệt độ quá lạnh khiến loài người khó tồn tại lâu.',
        'significance': 'Lãnh địa của Ma tộc, không ai dám xâm phạm'
    },

    'nam_man_rung': {
        'name_vn': 'Nam Man Rừng Sâu',
        'name_chi': '南蠻密林',
        'region': '南蠻',
        'description': 'Rừng sâu huyền bí ở phía nam, nơi các sinh vật hoang dã sống sót. Đó là một bí ẩn của tự nhiên.',
        'significance': 'Nơi tìm kiếm đặc biệt hiếm gặp'
    },

    'trung_nguyen_bang_thanh': {
        'name_vn': 'Trung Nguyên Thành Phố',
        'name_chi': '中原城邦',
        'region': '中原',
        'description': 'Thủ đô của triều đình, nơi quyền lực chính trị tập trung. Những tòa tháp cao chọc trời và công trình kiến trúc vĩ đại.',
        'significance': 'Trung tâm quyền lực của nhân giới'
    },

    'tay_gioi_bi_tich': {
        'name_vn': 'Tây Giới Bí Tích',
        'name_chi': '西界秘地',
        'region': '西界',
        'description': 'Vùng đất bí ẩn ở phía tây, nơi chứa các bí kíp cổ xưa và báu vật. Ít ai biết chính xác nó nằm ở đâu.',
        'significance': 'Chứa những bí kíp cổ nhất'
    },

    'ho_quyet_chinh': {
        'name_vn': 'Hồ Quyết Chính',
        'name_chi': '決澤湖',
        'region': '中原',
        'description': 'Hồ nước rộng lớn ở giữa đất nước, nơi các phe phái tập trung để chiến đấu.',
        'significance': 'Nơi diễn ra những trận chiến lịch sử'
    },
}


# ==============================================================================
# SECTION 3: SECT LORE & PHILOSOPHY
# ==============================================================================

SECT_LORE = {
    'thanh_van': {
        'name': 'Thanh Vân Tông',
        'name_chi': '清雲宗',
        'founding_year': 'Năm 0 (tính từ khởi thủy)',
        'philosophy': '''
Thanh Vân Tông là tông phái cổ nhất, được xây dựng dựa trên nguyên tắc
của "Thanh Tâm" (sáng suốt trong tâm hồn) và "Vân Hành" (hành động mà không vì lợi ích cá nhân).
Đệ tử của Thanh Vân tin rằng tu luyện là con đường để hiểu rõ bản chất của vũ trụ.
        ''',
        'enemies': ['hun_tram', 'ma_toc'],
        'allies': ['trinh_dau'],
        'characteristic': 'Chính thức, truyền thống, không chấp nhận tà pháp'
    },

    'hun_tram': {
        'name': 'Hỗn Trâm Tông',
        'name_chi': '混沌宗',
        'founding_year': 'Năm 150',
        'philosophy': '''
Hỗn Trâm Tông được thành lập bởi những người không muốn tuân theo quy tắc nghiêm ngặt.
Họ tin rằng sức mạnh không biết biên giới, và bất cứ phương tiện nào để đạt được nó đều là chính đáng.
Tông phái này lạm dụng tà pháp nhưng không phải là phe đối địch của nhân giới.
        ''',
        'enemies': ['thanh_van'],
        'allies': ['ma_toc'],
        'characteristic': 'Linh hoạt, táo bạo, chấp nhận tà pháp'
    },

    'trinh_dau': {
        'name': 'Trinh Đẩu Tông',
        'name_chi': '淨逗宗',
        'founding_year': 'Năm 200',
        'philosophy': '''
Trinh Đẩu Tông là tông phái về lành mạnh và hài hòa.
Họ tin rằng tu luyện nên mang lại hạnh phúc cho cộng đồng, không phải chỉ cho cá nhân.
Đây là tông phái nhỏ nhất nhưng có ảnh hưởng to lớn trong xã hội.
        ''',
        'enemies': [],
        'allies': ['thanh_van'],
        'characteristic': 'Hòa bình, cộng đồng, tập trung vào phúc lợi'
    },

    'ma_toc': {
        'name': 'Ma Tộc',
        'name_chi': '魔族',
        'founding_year': 'Thời cổ xưa, trước nhân giới',
        'philosophy': '''
Ma tộc là chủng tộc cổ xưa, từng thống trị toàn bộ thế giới trước khi nhân giới nổi lên.
Họ tin rằng sức mạnh tuyệt đối là quyền lực duy nhất, và họ sẽ lấy lại thế lực của mình.
Nhưng giữa Ma tộc cũng có những thành viên yêu thích hòa bình.
        ''',
        'enemies': ['thanh_van', 'trinh_dau', 'trinh_dau'],
        'allies': [],
        'characteristic': 'Cổ xưa, mạnh mẽ, mục tiêu phục hồi'
    },
}


# ==============================================================================
# SECTION 4: QUEST TEXT & DIALOGUE VIETNAMIZATION
# ==============================================================================

QUEST_DIALOGUE = {
    'join_sect_quest': {
        'intro': '''
Các câu chuyện về tu luyện trong giang hồ đều bắt đầu từ một lựa chọn.
Bạn đã gặp những cao thủ, học được những bí quyết.
Bây giờ, bạn phải quyết định: gia nhập tông phái nào để theo đuổi con đường của mình?
        ''',
        'success': '''
Chúc mừng bạn! Bạn đã chính thức trở thành một phần của tông phái.
Từ đây trở đi, bạn sẽ mang trách nhiệm của một chiến sĩ tu luyện.
Hãy cố gắng làm cho tông phái tự hào về sự lựa chọn của họ.
        '''
    },

    'breakthrough_quest': {
        'intro': '''
Linh lực của bạn đã đạt đến một ngưỡng mới.
Để đột phá lên cảnh giới tiếp theo, bạn cần vượt qua một thử thách kỳ lạ.
Hãy tìm đến Sư phụ để xin hướng dẫn.
        ''',
        'breakthrough_description': '''
Để đột phá từ Luyện Khí Sơ Kỳ lên Luyện Khí Trung Kỳ,
bạn cần phải hiểu được bản chất của linh khí và biến nó thành lực lượng của riêng mình.
Đó là một bước ngoặt trong cuộc hành trình tu luyện của bạn.
        ''',
        'success': '''
Bạn đã đột phá thành công!
Thế giới đã mở ra một cánh cửa mới cho bạn.
Tiếp tục cố gắng, và một ngày bạn sẽ trở thành một bậc thầy.
        '''
    },

    'npc_mission': {
        'intro': '''
Sư huynh giao cho bạn một nhiệm vụ:
"Những kẻ khác đạo đã xâm chiếm Động Linh Tuyệt.
Hãy đi tiêu diệt chúng để trả lại bình yên cho vùng đất này."
        ''',
        'success': '''
Bạn đã hoàn thành nhiệm vụ một cách anh dũng.
Sư huynh hài lòng với sức mạnh của bạn và cam kết sẽ dạy thêm bạn những bí quyết nâng cao.
        ''',
        'failure': '''
Bạn đã bại trận. Nhưng đó không phải là kết thúc.
Hãy luyện tập thêm và quay lại lần sau với sức mạnh mới.
        '''
    },
}


# ==============================================================================
# SECTION 5: ITEM & SKILL LORE NAMING
# ==============================================================================

ITEM_LORE = {
    'qing_yun_dan': {
        'name': 'Thanh Vân Đan',
        'description': '''
Viên đan quý báu được luyện công bằng tay của các cao thủ Thanh Vân Tông.
Nó chứa tinh hoa của linh khí từ đỉnh Thanh Vân Sơn.
Uống viên đan này sẽ giúp bạn phục hồi linh lực một cách nhanh chóng.
        '''
    },

    'hun_tram_noc': {
        'name': 'Hỗn Trâm Nọc',
        'description': '''
Một chất độc hiếm được tạo bởi Hương Tú của Hỗn Trâm Tông.
Nó có thể làm yếu sức mạnh của đối thủ nếu được tạo thành mũi tên hoặc phun ra.
Nhưng cảnh báo: nó cũng rất nguy hiểm đối với người sử dụng nó.
        '''
    },

    'ma_toc_vat': {
        'name': 'Ma Tộc Vật',
        'description': '''
Một vật thể bí ẩn lấy từ cơ thể của Ma tộc.
Nó vibrates với năng lượng độc hại. Người tu luyện con người không nên chạm vào nó trực tiếp.
Nhưng nếu được luyện công đúng cách, nó có thể trở thành một nguồn sức mạnh đáng sợ.
        '''
    },
}

SKILL_LORE = {
    'kiem_khi_lam_tran': {
        'name': 'Kiếm Khí Lâm Trần',
        'description': '''
Một chiêu thức cơ bản nhất của Thanh Vân Tông, được truyền dạy bởi Sư phụ Hoa Yên.
Nó dạy cách sử dụng linh khí để tăng cường độ sắc nhọn của mũi kiếm.
Mặc dù cơ bản, nhưng nó là nền tảng của tất cả các kỹ năng chiến đấu cao cấp.
        '''
    },

    'hoi_xuan_bao_vu': {
        'name': 'Hồi Xuân Báo Vũ',
        'description': '''
Một kỹ năng chữa lành cao cấp của Trinh Đẩu Tông.
Nó có thể kích hoạt lực sống trong cơ thể và chữa lành các vết thương mà không cần đến dược phẩm.
Để học được nó, bạn cần phải có tâm hồn sạch sẽ và nhân ái.
        '''
    },

    'thien_e_hut_huyet': {
        'name': 'Thiên E Hút Huyết',
        'description': '''
Một chiêu thức tà pháp của Hỗn Trâm Tông.
Nó cho phép bạn hút sức sống từ đối thủ và sử dụng nó để chữa lành bản thân.
Nhưng chính vì độc hại của nó, nó sẽ làm ô uế tâm hồn của người sử dụng.
        '''
    },
}


# ==============================================================================
# SECTION 6: WORLD EVENT STRINGS
# ==============================================================================

WORLD_EVENTS = {
    'sect_war_outbreak': '⚔️ Cuộc chiến giữa {sect_a} và {sect_b} đã bùng nổ!',
    'sect_dominant': '🏛️ {sect_name} đã trở thành tông phái cực mạnh!',
    'sect_decline': '📉 {sect_name} đang ở trong giai đoạn suy thoái nguy hiểm!',
    'sect_dissolved': '💀 {sect_name} đã chính thức giải thể!',
    'npc_promoted': '⬆️ {npc_name} đã thăng cấp lên {realm_name}!',
    'npc_death': '⚰️ {npc_name} đã hy sinh trong một nhiệm vụ!',
    'npc_retirement': '🧘 {npc_name} đã tuyên bố rút khỏi giang hồ!',
    'court_recognition': '📜 Triều đình chính thức công nhân {sect_name}!',
    'court_suppression': '⚖️ Triều đình chính thức cấm {sect_name}!',
    'regional_shift': '🗺️ {region_name}: {winner} đã chiến thắng {loser}!',
}
