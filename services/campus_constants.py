"""校区常量（广东白云学院：西校区 / 北校区）"""
DEFAULT_CAMPUS_ZONE = '西校区'
CAMPUS_ZONES = ('西校区', '北校区', '校外')
LEGACY_ZONES = ('主校区', '生活区')  # 旧版种子，迁移为西校区
LEGACY_SPOT_IDS = tuple(f'spot{i}' for i in range(1, 9))  # 旧面交点 id
LEGACY_COURSE_IDS = (
    'course_MATH101', 'course_CS201', 'course_SE301', 'course_EE101',
    'course_ECON101', 'course_CHI101', 'course_ENG201',
)
