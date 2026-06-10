"""校园种子数据：广东白云学院西/北校区（不再使用主校区、生活区）"""
import time

from .campus_constants import LEGACY_COURSE_IDS, LEGACY_SPOT_IDS
from .seed_baiyunu_trial import BYU_DORMS, BYU_DORM_MAP, BYU_SPOTS, BYU_COURSES

DORM_BUILDINGS = BYU_DORMS
DORM_MAP = BYU_DORM_MAP


def migrate_legacy_zones(db, User=None, Book=None, CampusSpot=None):
    """将主校区/生活区迁移为西校区"""
    if User is not None:
        User.query.filter(User.campus_zone.in_(('主校区', '生活区'))).update(
            {'campus_zone': '西校区'}, synchronize_session=False
        )
    if Book is not None:
        Book.query.filter(Book.campus_zone.in_(('主校区', '生活区'))).update(
            {'campus_zone': '西校区'}, synchronize_session=False
        )
    if CampusSpot is not None:
        CampusSpot.query.filter(CampusSpot.zone == '主校区').update(
            {'zone': '西校区'}, synchronize_session=False
        )
        CampusSpot.query.filter(CampusSpot.zone == '生活区').update(
            {'zone': '西校区'}, synchronize_session=False
        )


def purge_legacy_campus_data(db, CampusSpot, CourseTextbook, SemesterCampaign):
    """删除旧版通用面交点/课表/学期活动种子"""
    for sid in LEGACY_SPOT_IDS:
        row = CampusSpot.query.filter_by(id=sid).first()
        if row:
            db.session.delete(row)
    for cid in LEGACY_COURSE_IDS:
        row = CourseTextbook.query.filter_by(id=cid).first()
        if row:
            db.session.delete(row)
    for cid in ('camp_back', 'camp_clear'):
        row = SemesterCampaign.query.filter_by(id=cid).first()
        if row and not SemesterCampaign.query.filter(SemesterCampaign.id.like('byu_%')).first():
            db.session.delete(row)


def seed_campus_data(db, CampusSpot, CourseTextbook, SemesterCampaign, User=None, Book=None):
    """清理旧版通用种子，校区数据由 seed_baiyunu_trial 写入"""
    purge_legacy_campus_data(db, CampusSpot, CourseTextbook, SemesterCampaign)
    migrate_legacy_zones(db, User=User, Book=Book, CampusSpot=CampusSpot)
    db.session.commit()
