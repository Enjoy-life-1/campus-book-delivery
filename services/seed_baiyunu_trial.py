"""广东白云学院试用数据（来源：官网/招生网/总务处公开信息，2025）
参考：baiyunu.edu.cn、zsb.baiyunu.edu.cn、zwc.baiyunu.edu.cn
西校区：江高镇学苑路1号（智造/电气/大数据/曙光/华为ICT）
北校区：钟落潭九佛西路280号（其余本科院系）"""
import json
import time

from flask import Flask
from database_config import get_sqlalchemy_uri
from models import (
    db, CampusSchool, CampusSpot, CourseTextbook, SemesterCampaign,
    Setting, User, Book, Announcement, Category
)
from security import hash_password
from .seed_baiyun_schools import upsert_baiyun_schools

SCHOOL_ID = 'school_baiyunu'
SCHOOL_NAME = '广东白云学院'

# 2025招生：智造/电气/大数据/曙光/华为ICT→西校区；其余本科→北校区
# 西校区楼栋参考：教学楼7栋 + 宿舍11栋 + 图书馆/食堂/服务中心/医务室
BYU_SPOTS = [
    # 西校区·教学楼
    ('byu_w_gongxing', '西校区·躬行楼', '西校区', '实验、实训基地', 1, 18, 42),
    ('byu_w_zhishan', '西校区·至善楼', '西校区', '理论课与公共课', 2, 24, 44),
    ('byu_w_siqi', '西校区·思齐楼', '西校区', '专业课与公共课', 3, 30, 46),
    ('byu_w_xinda', '西校区·信达楼', '西校区', '英语类课程（配多媒体）', 4, 26, 50),
    ('byu_w_xingjian', '西校区·行健楼', '西校区', '健身房、乒乓球台、攀岩墙', 5, 32, 38),
    ('byu_w_boya', '西校区·博雅楼', '西校区', '计算机、设计相关课程', 6, 22, 48),
    ('byu_w_deyi', '西校区·德艺楼', '西校区', '艺术类专业课程', 7, 28, 52),
    # 西校区·生活与宿舍
    ('byu_w_lib', '西校区·图书馆', '西校区', '弧形7层建筑', 11, 20, 36),
    ('byu_w_yipin', '西校区·一品堂', '西校区', '食堂（宿舍区主力餐厅）', 12, 38, 64),
    ('byu_w_erya', '西校区·二雅厅', '西校区', '食堂（教工公寓首层）', 13, 32, 58),
    ('byu_w_service', '西校区·学生服务中心', '西校区', '位于8号楼一层', 14, 44, 70),
    ('byu_w_clinic', '西校区·医务室', '西校区', '校区医务室', 15, 16, 54),
    ('byu_w_gate', '西校区·正门', '西校区', '学苑路正门', 16, 8, 45),
    ('byu_w_dorm_hub', '西校区·宿舍区广场', '西校区', '1-12号宿舍楼之间广场', 17, 36, 74),
    ('byu_w_express', '西校区·宿舍快递点', '西校区', '宿舍区快递驿站', 18, 40, 66),
    ('byu_w_metro', '西校区·校门口便民车点', '西校区', '可乘便民车至滘心地铁站', 19, 6, 42),
    # 北校区（钟落潭九佛西路280号）
    ('byu_n_square', '北校区·日晷广场', '北校区', '校区中心日晷广场，近正门', 21, 78, 25),
    ('byu_n_lib', '北校区·图书馆', '北校区', '图书馆服务台（馆藏约322万册·两校区共享资源）', 22, 72, 38),
    ('byu_n_baiyun', '北校区·白云楼', '北校区', '白云楼行政办公区门前', 23, 76, 42),
    ('byu_n_boyi', '北校区·博艺楼', '北校区', '博艺楼（传媒与艺术学院）大厅', 24, 70, 48),
    ('byu_n_zhiyong', '北校区·致用楼', '北校区', '致用楼（会计与管理学院）', 25, 82, 50),
    ('byu_n_sanli', '北校区·三立园餐厅', '北校区', '学思苑三立园餐厅（粤式烧腊、麻辣烫等）', 26, 86, 55),
    ('byu_n_siji', '北校区·四季轩餐厅', '北校区', '创思苑四季轩餐厅（瑞幸/古茗等）', 27, 84, 58),
]

# 西校区宿舍11栋（1-10含10A、12）+ 特色公寓；标准6人间上床下桌
BYU_WEST_DORMS = [
    '1号楼', '2号楼', '3号楼', '4号楼', '5号楼', '6号楼', '7号楼', '8号楼', '9号楼',
    '10号楼', '10A', '12号楼',
    '特色公寓·单人间', '特色公寓·双人间',
]

BYU_NORTH_DORMS = ['学思苑', '慎思苑', '创思苑']

BYU_DORMS = BYU_WEST_DORMS + BYU_NORTH_DORMS + ['校外合租']

BYU_DORM_MAP = [
    {'name': '1号楼', 'zone': '西校区', 'x': 14, 'y': 78, 'near_spot': '西校区·宿舍区广场', 'note': '6人间·上床下桌·空调·独立卫浴'},
    {'name': '2号楼', 'zone': '西校区', 'x': 18, 'y': 80, 'near_spot': '西校区·宿舍区广场', 'note': '6人间·上床下桌'},
    {'name': '3号楼', 'zone': '西校区', 'x': 22, 'y': 76, 'near_spot': '西校区·二雅厅', 'note': '3#-10#电梯加装·2023暑期改造'},
    {'name': '4号楼', 'zone': '西校区', 'x': 26, 'y': 74, 'near_spot': '西校区·宿舍区广场', 'note': '3#-10#电梯加装·2023暑期改造'},
    {'name': '5号楼', 'zone': '西校区', 'x': 30, 'y': 76, 'near_spot': '西校区·一品堂', 'note': '2023首批改造·6人间'},
    {'name': '6号楼', 'zone': '西校区', 'x': 34, 'y': 74, 'near_spot': '西校区·一品堂', 'note': '2023首批改造·6人间'},
    {'name': '7号楼', 'zone': '西校区', 'x': 38, 'y': 78, 'near_spot': '西校区·宿舍区广场', 'note': '2023首批改造·6人间'},
    {'name': '8号楼', 'zone': '西校区', 'x': 42, 'y': 76, 'near_spot': '西校区·学生服务中心', 'note': '一层学生服务中心·2023首批改造'},
    {'name': '9号楼', 'zone': '西校区', 'x': 40, 'y': 70, 'near_spot': '西校区·行健楼', 'note': '3#-10#电梯加装·2023暑期改造'},
    {'name': '10号楼', 'zone': '西校区', 'x': 44, 'y': 68, 'near_spot': '西校区·宿舍区广场', 'note': '含10A·电梯加装·2023暑期改造'},
    {'name': '10A', 'zone': '西校区', 'x': 46, 'y': 72, 'near_spot': '西校区·宿舍区广场', 'note': '10号楼附楼·10A'},
    {'name': '12号楼', 'zone': '西校区', 'x': 36, 'y': 82, 'near_spot': '西校区·一品堂', 'note': '2023首批改造·6人间'},
    {'name': '特色公寓·单人间', 'zone': '西校区', 'x': 24, 'y': 62, 'near_spot': '西校区·图书馆', 'note': '特色公寓·单人间'},
    {'name': '特色公寓·双人间', 'zone': '西校区', 'x': 28, 'y': 60, 'near_spot': '西校区·图书馆', 'note': '特色公寓·双人间'},
    {'name': '学思苑', 'zone': '北校区', 'x': 86, 'y': 56, 'near_spot': '北校区·三立园餐厅'},
    {'name': '慎思苑', 'zone': '北校区', 'x': 80, 'y': 54, 'near_spot': '北校区·图书馆'},
    {'name': '创思苑', 'zone': '北校区', 'x': 84, 'y': 60, 'near_spot': '北校区·四季轩餐厅'},
    {'name': '校外合租', 'zone': '校外', 'x': 92, 'y': 82, 'near_spot': '西校区·正门'},
]

# 学院/专业/课程（对齐2025校区分配与官网院系设置）
BYU_COURSES = [
    ('智能制造工程学院', '机械设计制造及其自动化', 'ME101', '机械原理', '机械原理', '孙桓', '9787040396640'),
    ('智能制造工程学院', '智能车辆工程', 'AUTO101', '汽车构造', '汽车构造', '陈家瑞', '9787040396641'),
    ('电气与信息工程学院', '电气工程及其自动化', 'EE101', '电路分析', '电路', '邱关源', '9787040238969'),
    ('电气与信息工程学院', '自动化', 'AUTO201', '自动控制原理', '自动控制原理', '胡寿松', '9787040396642'),
    ('大数据与计算机学院', '软件工程', 'CS101', 'Python程序设计', 'Python编程：从入门到实践', 'Eric Matthes', '9787115428028'),
    ('大数据与计算机学院', '计算机科学与技术', 'CS201', '数据结构', '数据结构', '严蔚敏', '9787302147510'),
    ('大数据与计算机学院', '虚拟现实技术', 'VR101', '虚拟现实技术概论', '虚拟现实技术基础', '王金权', '9787040396643'),
    ('曙光大数据产业学院', '数据科学与大数据技术', 'BD101', '大数据技术概论', '大数据技术原理与应用', '林子雨', '9787040396644'),
    ('华为ICT学院', '物联网工程', 'IOT101', '物联网概论', '物联网技术概论', '马华东', '9787040396645'),
    ('数学与统计学院', '数学与应用数学', 'MATH101', '高等数学', '高等数学（上册）', '同济大学数学系', '9787040396638'),
    ('数学与统计学院', '数学与应用数学', 'MATH201', '线性代数', '线性代数', '同济大学数学系', '9787040396645'),
    ('物理与能源学院', '应用物理学', 'PHY101', '大学物理', '大学物理学', '程守洙', '9787040396652'),
    ('会计学院', '会计学', 'ACC101', '基础会计', '基础会计', '陈国辉', '9787563223456'),
    ('工商管理学院', '工商管理', 'MGT201', '管理学原理', '管理学', '周三多', '9787040458324'),
    ('传媒学院', '广播电视学', 'MEDIA101', '传播学概论', '传播学概论', '郭庆光', '9787300116589'),
    ('外国语学院', '英语', 'ENG101', '大学英语', '新视野大学英语', '郑树棠', '9787560012345'),
    ('艺术设计学院', '视觉传达设计', 'ART101', '设计基础', '设计基础', '尹定邦', '9787560012346'),
    ('应用经济学院', '国际经济与贸易', 'ECON101', '微观经济学', '微观经济学', '高鸿业', '9787300176797'),
    ('建筑工程学院', '土木工程', 'CIV101', '理论力学', '理论力学', '哈工大理论力学教研室', '9787040396646'),
    ('马克思主义学院', '思想政治教育', 'POL101', '思想道德与法治', '思想道德与法治', '本书编写组', '9787040568934'),
]

# title, author, price, code, condition, dorm, isbn, campus_zone
SAMPLE_BOOKS = [
    ('Python编程：从入门到实践', 'Eric Matthes', 45.0, 'CS101', '九成新', '5号楼', '9787115428028', '西校区'),
    ('数据结构', '严蔚敏', 35.0, 'CS201', '8成新', '6号楼', '9787302147510', '西校区'),
    ('虚拟现实技术基础', '王金权', 40.0, 'VR101', '9成新', '7号楼', '9787040396643', '西校区'),
    ('大数据技术原理与应用', '林子雨', 38.0, 'BD101', '9成新', '8号楼', '9787040396644', '西校区'),
    ('物联网技术概论', '马华东', 32.0, 'IOT101', '9成新', '10A', '9787040396645', '西校区'),
    ('电路（第5版）上册', '邱关源', 38.0, 'EE101', '8成新', '8号楼', '9787040238969', '西校区'),
    ('自动控制原理', '胡寿松', 42.0, 'AUTO201', '8成新', '7号楼', '9787040396642', '西校区'),
    ('机械原理', '孙桓', 30.0, 'ME101', '9成新', '4号楼', '9787040396640', '西校区'),
    ('汽车构造（上册）', '陈家瑞', 28.0, 'AUTO101', '8成新', '5号楼', '9787040396641', '西校区'),
    ('高等数学（上册）', '同济大学数学系', 22.0, 'MATH101', '8成新', '3号楼', '9787040396638', '西校区'),
    ('线性代数', '同济大学数学系', 18.0, 'MATH201', '9成新', '9号楼', '9787040396647', '西校区'),
    ('大学物理', '程守洙', 30.0, 'PHY101', '8成新', '12号楼', '9787040396652', '西校区'),
    ('新视野大学英语 读写教程1', '郑树棠', 18.0, 'ENG101', '9成新', '2号楼', '9787560012345', '西校区'),
    ('虚拟现实技术基础', '王金权', 36.0, 'VR101', '8成新', '1号楼', '9787040396643', '西校区'),
    ('设计基础', '尹定邦', 28.0, 'ART101', '9成新', '9号楼', '9787560012346', '西校区'),
    ('基础会计（第7版）', '陈国辉', 28.0, 'ACC101', '9成新', '学思苑', '9787563223456', '北校区'),
    ('管理学', '周三多', 32.0, 'MGT201', '9成新', '慎思苑', '9787040458324', '北校区'),
    ('传播学概论', '郭庆光', 22.0, 'MEDIA101', '9成新', '创思苑', '9787300116589', '北校区'),
    ('微观经济学', '高鸿业', 25.0, 'ECON101', '8成新', '学思苑', '9787300176797', '北校区'),
]

PLACEHOLDER = 'https://picsum.photos/seed/baiyunu/400/500'


def _set_setting(key, value):
    """Setting KV upsert（dict/list 自动 JSON）"""
    row = Setting.query.filter_by(key=key).first()
    val = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    if row:
        row.value = val
        row.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        db.session.add(Setting(key=key, value=val, updated_at=time.strftime('%Y-%m-%d %H:%M:%S')))


def migrate_west_dorm_aliases():
    """统一历史楼名到现行西/北校区楼栋"""
    from .campus_dorms import WEST_DORM_ALIASES, normalize_dorm_name

    west_set = set(BYU_WEST_DORMS)
    north_set = set(BYU_NORTH_DORMS)
    for row in User.query.filter_by(school_id=SCHOOL_ID).all():
        d = (row.dorm_building or '').strip()
        if not d:
            continue
        if d in WEST_DORM_ALIASES:
            row.dorm_building = normalize_dorm_name(d)
        z = row.campus_zone or '西校区'
        if z in ('主校区', '生活区'):
            z = '西校区'
            row.campus_zone = z
        if z == '西校区' and row.dorm_building not in west_set:
            row.dorm_building = WEST_DORM_ALIASES.get(d, row.dorm_building if row.dorm_building in west_set else '')
        if z == '北校区' and row.dorm_building not in north_set:
            row.dorm_building = WEST_DORM_ALIASES.get(d, row.dorm_building if row.dorm_building in north_set else '')
    for row in Book.query.filter_by(school_id=SCHOOL_ID).all():
        d = (row.dorm_building or '').strip()
        if not d:
            continue
        if d in WEST_DORM_ALIASES:
            row.dorm_building = normalize_dorm_name(d)
        z = row.campus_zone or '西校区'
        if z in ('主校区', '生活区'):
            z = '西校区'
        if z == '西校区' and row.dorm_building not in west_set:
            row.dorm_building = WEST_DORM_ALIASES.get(d, row.dorm_building if row.dorm_building in west_set else '')
        if z == '北校区' and row.dorm_building not in north_set:
            row.dorm_building = WEST_DORM_ALIASES.get(d, row.dorm_building if row.dorm_building in north_set else '')


def seed_trial():
    """写入白云学院面交点/课表/宿舍/演示账号与书籍"""
    from .campus_seed import migrate_legacy_zones, purge_legacy_campus_data
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    purge_legacy_campus_data(db, CampusSpot, CourseTextbook, SemesterCampaign)
    migrate_legacy_zones(db, User=User, Book=Book, CampusSpot=CampusSpot)
    migrate_west_dorm_aliases()
    upsert_baiyun_schools()

    school = CampusSchool.query.filter_by(id=SCHOOL_ID).first()
    if school:
        school.sort_order = 1
        school.is_active = True
    CampusSchool.query.filter(CampusSchool.id != SCHOOL_ID).update({'sort_order': 100})

    active_spot_ids = {s[0] for s in BYU_SPOTS}
    for sid, name, zone, desc, order, mx, my in BYU_SPOTS:
        row = CampusSpot.query.filter_by(id=sid).first()
        if row:
            row.name, row.zone, row.description = name, zone, desc
            row.sort_order, row.map_x, row.map_y = order, mx, my
        else:
            db.session.add(CampusSpot(
                id=sid, name=name, zone=zone, description=desc,
                sort_order=order, map_x=mx, map_y=my, created_at=ts
            ))
    for row in CampusSpot.query.filter(CampusSpot.id.like('byu_%')).all():
        if row.id not in active_spot_ids:
            db.session.delete(row)

    active_course_ids = {f'byu_{c[2]}' for c in BYU_COURSES}
    for college, major, code, cname, title, author, isbn in BYU_COURSES:
        cid = f'byu_{code}'
        row = CourseTextbook.query.filter_by(id=cid).first()
        if row:
            row.college, row.major, row.course_code = college, major, code
            row.course_name, row.textbook_title = cname, title
            row.textbook_author, row.textbook_isbn = author, isbn
        else:
            db.session.add(CourseTextbook(
                id=cid, college=college, major=major, course_code=code,
                course_name=cname, textbook_title=title, textbook_author=author,
                textbook_isbn=isbn, created_at=ts
            ))
    for row in CourseTextbook.query.filter(CourseTextbook.id.like('byu_%')).all():
        if row.id not in active_course_ids:
            db.session.delete(row)

    campaigns = [
        ('byu_camp_spring', '白云学院西校区·开学教材专场', 'back_to_school', '开学季', '02-20', '04-30',
         '西校区（学苑路1号）图书馆、明德楼、一品堂等面交；北校区学思苑/创思苑同学可选北区餐厅面交点。'),
        ('byu_camp_final', '白云学院西校区·期末清仓', 'clearance', '期末清仓', '06-01', '07-10',
         '西校区4-8栋、10A栋同学可在宿舍区或图书馆附近面交转让教材。'),
    ]
    for cid, title, ctype, tag, start, end, desc in campaigns:
        row = SemesterCampaign.query.filter_by(id=cid).first()
        if row:
            row.title, row.campaign_type, row.tag = title, ctype, tag
            row.start_date, row.end_date, row.description = start, end, desc
            row.is_active = True
        else:
            db.session.add(SemesterCampaign(
                id=cid, title=title, campaign_type=ctype, tag=tag,
                start_date=start, end_date=end, description=desc,
                is_active=True, created_at=ts
            ))

    _set_setting('default_school_id', SCHOOL_ID)
    _set_setting('default_campus_zone', '西校区')
    _set_setting('trial_school_name', SCHOOL_NAME)
    _set_setting('dorm_buildings', BYU_DORMS)
    _set_setting('dorm_map', BYU_DORM_MAP)
    _set_setting('west_dorm_buildings', BYU_WEST_DORMS)

    ann = Announcement.query.filter_by(id='ann_byu_trial').first()
    ann_text = (
        '西校区已录入教学楼（躬行/至善/思齐/信达/行健/博雅/德艺）、'
        '宿舍1-12号楼（含10A）及图书馆/一品堂/二雅厅/学生服务中心/医务室。'
        '认证 @stu.baiyunu.edu.cn 。'
    )
    if not ann:
        db.session.add(Announcement(
            id='ann_byu_trial', title='广东白云学院试用上线', content=ann_text,
            type='guide', is_active=True, created_at=ts, updated_at=ts
        ))
    else:
        ann.content = ann_text
        ann.updated_at = ts

    def ensure_user(uid, username, password, phone, dorm, campus_zone='西校区', verified=True):
        u = User.query.filter_by(id=uid).first()
        pwd = hash_password(password)
        if u:
            u.username = username
            u.password = pwd
            u.phone = phone
            u.school = SCHOOL_NAME
            u.school_id = SCHOOL_ID
            u.campus_zone = campus_zone
            u.dorm_building = dorm
            u.campus_email = f'{username}@stu.baiyunu.edu.cn'
            u.campus_verified = verified
            u.student_id = u.student_id or f'2024{uid[-4:]}'
        else:
            db.session.add(User(
                id=uid, username=username, password=pwd,
                email=f'{username}@baiyunu.edu.cn', phone=phone,
                school=SCHOOL_NAME, school_id=SCHOOL_ID,
                campus_zone=campus_zone, dorm_building=dorm,
                campus_email=f'{username}@stu.baiyunu.edu.cn',
                campus_verified=verified,
                student_id=f'2024{uid[-4:]}',
                created_at=ts, is_admin=False
            ))

    ensure_user('2', 'student1', 'student123', '13900139001', '6号楼', '西校区')
    ensure_user('byu_u1', 'baiyun_seller', 'baiyun123', '13800138001', '5号楼', '西校区')
    ensure_user('byu_u4', 'baiyun_west2', 'baiyun123', '13800138004', '10A', '西校区')
    ensure_user('byu_u2', 'baiyun_buyer', 'baiyun123', '13800138002', '学思苑', '北校区')
    u_n = User.query.filter_by(id='byu_u3').first()
    if u_n:
        u_n.campus_zone, u_n.dorm_building = '北校区', '慎思苑'

    seller_w = User.query.filter_by(id='byu_u1').first()
    seller_n = User.query.filter_by(id='byu_u2').first()
    for i, (title, author, price, code, cond, dorm, isbn, zone) in enumerate(SAMPLE_BOOKS):
        bid = f'byu_book_{i + 1}'
        owner = seller_n if zone == '北校区' else seller_w
        b = Book.query.filter_by(id=bid).first()
        if b:
            b.title, b.author, b.price = title, author, price
            b.condition, b.dorm_building, b.campus_zone = cond, dorm, zone
            b.isbn, b.course_code = isbn, code
            b.owner_id, b.owner_name = owner.id, owner.username
            b.seller, b.sellerId = owner.username, owner.id
            b.contact = owner.phone or ''
            b.status = 'available'
            continue
        db.session.add(Book(
            id=bid, title=title, author=author, category='textbook',
            price=price, desc=f'{SCHOOL_NAME}同学转让，课程 {code}',
            description=f'{SCHOOL_NAME}同学转让，课程 {code}',
            imgs=json.dumps([PLACEHOLDER], ensure_ascii=False),
            image=PLACEHOLDER, cover_url=PLACEHOLDER,
            contact=owner.phone or '13800138001',
            stock=1, status='available', condition=cond,
            isbn=isbn, course_code=code,
            campus_zone=zone, dorm_building=dorm,
            school_id=SCHOOL_ID,
            owner_id=owner.id, owner_name=owner.username,
            seller=owner.username, sellerId=owner.id,
            createTime=time.strftime('%Y-%m-%d'),
            created_at=ts, publish_date=time.strftime('%Y-%m-%d')
        ))
    for n in range(len(SAMPLE_BOOKS) + 1, 25):
        stale = Book.query.filter_by(id=f'byu_book_{n}').first()
        if stale:
            stale.status = 'sold'

    db.session.commit()


def main():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_trial()
        print(f'广东白云学院试用数据导入完成（school_id={SCHOOL_ID}）')
        w_spots = sum(1 for s in BYU_SPOTS if s[2] == '西校区')
        n_spots = sum(1 for s in BYU_SPOTS if s[2] == '北校区')
        print(f'  面交点 {len(BYU_SPOTS)} 个（西校区 {w_spots} · 北校区 {n_spots}）')
        w_books = sum(1 for b in SAMPLE_BOOKS if b[-1] == '西校区')
        print(f'  宿舍 {len(BYU_DORMS)} 个（西校区 {len(BYU_WEST_DORMS)}）· 课程 {len(BYU_COURSES)} 门 · 样例书 {len(SAMPLE_BOOKS)} 本（西{w_books}·北{len(SAMPLE_BOOKS)-w_books}）')
        print('  默认校区: 西校区 · 账号 baiyun_seller / baiyun_west2(西) / baiyun_buyer(北) 密码 baiyun123')
        print('  原测试账号 student1 已绑定本校 · 认证邮箱 @stu.baiyunu.edu.cn')


if __name__ == '__main__':
    main()
