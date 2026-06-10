"""数据库结构升级 + 评论/评价 JSON 迁移到 SQLite"""

import json

import os

import time

from flask import Flask

from sqlalchemy import text

from models import db, Category, Comment, Review, Order, CampusSpot, CourseTextbook, SemesterCampaign, NotificationOutbox, CampusSchool, SensitiveWord, IsbnBlacklist, User, Book
from services.admin_compliance import seed_compliance_data
import json

from services.campus_seed import seed_campus_data
from db_schema import column_names as _column_names, dialect_name


app = Flask(__name__)

from database_config import get_sqlalchemy_uri
app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_DIR = os.path.join(BASE_DIR, 'database')



DEFAULT_CATEGORIES = [

    ('textbook', '教材教辅', 1),

    ('postgraduate', '考研资料', 2),

    ('literature', '文学小说', 3),

    ('professional', '专业书籍', 4),

    ('other', '其他书籍', 5),

]


def migrate_book_base64_images():
    """历史 data URL 封面转 static/uploads 文件"""
    import json
    import random
    from models import Book
    from services.book_media import normalize_book_images

    def gid():
        return str(int(time.time() * 1000) + random.randint(0, 9999))

    n = 0
    for book in Book.query.all():
        if not book.imgs:
            continue
        try:
            imgs = json.loads(book.imgs) if isinstance(book.imgs, str) else book.imgs
        except (json.JSONDecodeError, TypeError):
            continue
        if not imgs or not any(str(x).startswith('data:image') for x in imgs):
            continue
        try:
            new_imgs = normalize_book_images(app, imgs, gid)
        except ValueError:
            continue
        book.imgs = json.dumps(new_imgs, ensure_ascii=False)
        if new_imgs:
            book.image = new_imgs[0]
            book.cover_url = new_imgs[0]
        n += 1
    if n:
        db.session.commit()
        print(f'  + 书籍图片 base64→文件 {n} 本')
    return n


def migrate_json_comments():
    """database/comments.json → comments 表"""
    path = os.path.join(DB_DIR, 'comments.json')

    if not os.path.exists(path):

        return 0

    with open(path, 'r', encoding='utf-8') as f:

        items = json.load(f)

    count = 0

    for item in items:

        cid = str(item.get('id', ''))

        if not cid or Comment.query.filter_by(id=cid).first():
            continue
        book_id = str(item.get('book_id', '') or '')
        user_id = str(item.get('user_id', '') or '')
        if not book_id or not user_id:
            continue
        if not Book.query.filter_by(id=book_id).first() or not User.query.filter_by(id=user_id).first():
            continue

        db.session.add(Comment(

            id=cid,

            book_id=book_id,

            book_title=item.get('book_title', ''),

            user_id=user_id,

            username=item.get('username', ''),

            content=item.get('content', ''),

            likes=int(item.get('likes', 0) or 0),

            is_deleted=bool(item.get('is_deleted', False)),

            created_at=item.get('created_at', time.strftime('%Y-%m-%d %H:%M:%S'))

        ))

        count += 1

    if count:

        db.session.commit()

    return count





def migrate_json_reviews():
    """database/reviews.json → reviews 表"""
    path = os.path.join(DB_DIR, 'reviews.json')

    if not os.path.exists(path):

        return 0

    with open(path, 'r', encoding='utf-8') as f:

        items = json.load(f)

    count = 0

    for item in items:

        rid = str(item.get('id', ''))

        if not rid or Review.query.filter_by(id=rid).first():

            continue

        oid = str(item.get('order_id', ''))
        reviewer_id = str(item.get('reviewer_id', ''))
        book_id = str(item.get('book_id', '') or '')
        reviewed_user_id = str(item.get('reviewed_user_id', '') or '')

        if Review.query.filter_by(order_id=oid, reviewer_id=reviewer_id).first():
            continue
        if not oid or not reviewer_id:
            continue
        if not User.query.filter_by(id=reviewer_id).first():
            continue
        if not Order.query.filter_by(id=oid).first():
            continue
        if book_id and not Book.query.filter_by(id=book_id).first():
            continue
        if reviewed_user_id and not User.query.filter_by(id=reviewed_user_id).first():
            continue

        db.session.add(Review(

            id=rid,

            order_id=oid,

            book_id=book_id or None,

            reviewer_id=reviewer_id,

            reviewer_name=item.get('reviewer_name', ''),

            reviewer_role=item.get('reviewer_role', ''),

            reviewed_user_id=reviewed_user_id or None,

            service_rating=int(item.get('service_rating', 5) or 5),

            condition_rating=int(item.get('condition_rating', 5) or 5),

            efficiency_rating=int(item.get('efficiency_rating', 5) or 5),

            review_content=item.get('review_content', ''),

            created_at=item.get('created_at', time.strftime('%Y-%m-%d %H:%M:%S'))

        ))

        count += 1

    if count:

        db.session.commit()

    return count





def upgrade():
    """create_all + 增量 ALTER + 种子数据 + JSON 迁移"""
    with app.app_context():

        db.create_all()

        print(f'数据库类型: {dialect_name(db.engine)}')

        conn = db.engine.connect()

        book_cols = _column_names(conn, 'books')

        for col, ddl in [

            ('condition', 'ALTER TABLE books ADD COLUMN condition VARCHAR(50)'),

            ('isbn', 'ALTER TABLE books ADD COLUMN isbn VARCHAR(30)'),

            ('edition', 'ALTER TABLE books ADD COLUMN edition VARCHAR(80)'),

            ('course_code', 'ALTER TABLE books ADD COLUMN course_code VARCHAR(50)'),

            ('campus_zone', 'ALTER TABLE books ADD COLUMN campus_zone VARCHAR(100)'),

            ('dorm_building', 'ALTER TABLE books ADD COLUMN dorm_building VARCHAR(50)'),

            ('campaign_tag', 'ALTER TABLE books ADD COLUMN campaign_tag VARCHAR(50)'),

            ('original_price', 'ALTER TABLE books ADD COLUMN original_price FLOAT'),

            ('price_drop_until', 'ALTER TABLE books ADD COLUMN price_drop_until VARCHAR(50)'),

        ]:

            if col not in book_cols:

                conn.execute(text(ddl))

                print(f'  + books.{col}')

        user_cols = _column_names(conn, 'users')

        for col, ddl in [

            ('campus_zone', "ALTER TABLE users ADD COLUMN campus_zone VARCHAR(100) DEFAULT '西校区'"),

            ('dorm_building', 'ALTER TABLE users ADD COLUMN dorm_building VARCHAR(50)'),

            ('notify_email', 'ALTER TABLE users ADD COLUMN notify_email BOOLEAN DEFAULT 1'),

            ('notify_sms', 'ALTER TABLE users ADD COLUMN notify_sms BOOLEAN DEFAULT 1'),
            ('school_id', 'ALTER TABLE users ADD COLUMN school_id VARCHAR(50)'),
            ('student_id', 'ALTER TABLE users ADD COLUMN student_id VARCHAR(50)'),
            ('campus_email', 'ALTER TABLE users ADD COLUMN campus_email VARCHAR(120)'),
            ('campus_verified', 'ALTER TABLE users ADD COLUMN campus_verified BOOLEAN DEFAULT 0'),
            ('role', "ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'student'"),
            ('ban_level', "ALTER TABLE users ADD COLUMN ban_level VARCHAR(20) DEFAULT 'none'"),
            ('ban_until', 'ALTER TABLE users ADD COLUMN ban_until VARCHAR(50)'),
            ('ban_reason', 'ALTER TABLE users ADD COLUMN ban_reason TEXT'),
            ('subscribe_price_drop', 'ALTER TABLE users ADD COLUMN subscribe_price_drop BOOLEAN DEFAULT 1'),

        ]:

            if col not in user_cols:

                conn.execute(text(ddl))

                print(f'  + users.{col}')

        order_cols = _column_names(conn, 'orders')

        if 'cancel_reason' not in order_cols:

            conn.execute(text('ALTER TABLE orders ADD COLUMN cancel_reason VARCHAR(300)'))

            print('  + orders.cancel_reason')

        for col, ddl in [
            ('order_type', "ALTER TABLE orders ADD COLUMN order_type VARCHAR(20) DEFAULT 'sale'"),
            ('exchange_book_title', 'ALTER TABLE orders ADD COLUMN exchange_book_title VARCHAR(200)'),
            ('exchange_note', 'ALTER TABLE orders ADD COLUMN exchange_note TEXT'),
        ]:
            if col not in order_cols:
                conn.execute(text(ddl))
                print(f'  + orders.{col}')

        comment_cols = _column_names(conn, 'comments')
        if 'audit_status' not in comment_cols:
            conn.execute(text("ALTER TABLE comments ADD COLUMN audit_status VARCHAR(20) DEFAULT 'approved'"))
            print('  + comments.audit_status')

        col_cols = _column_names(conn, 'collections')

        if 'collected_price' not in col_cols:

            conn.execute(text('ALTER TABLE collections ADD COLUMN collected_price FLOAT'))

            print('  + collections.collected_price')

        msg_cols = _column_names(conn, 'messages')
        for col, ddl in [
            ('media_url', 'ALTER TABLE messages ADD COLUMN media_url VARCHAR(500)'),
            ('media_meta', 'ALTER TABLE messages ADD COLUMN media_meta TEXT'),
            ('read_at', 'ALTER TABLE messages ADD COLUMN read_at VARCHAR(50)'),
            ('is_recalled', 'ALTER TABLE messages ADD COLUMN is_recalled BOOLEAN DEFAULT 0'),
            ('recalled_at', 'ALTER TABLE messages ADD COLUMN recalled_at VARCHAR(50)'),
        ]:
            if col not in msg_cols:
                conn.execute(text(ddl))
                print(f'  + messages.{col}')

        book_cols = _column_names(conn, 'books')
        for col, ddl in [
            ('price_drop_plan', 'ALTER TABLE books ADD COLUMN price_drop_plan TEXT'),
            ('listing_type', "ALTER TABLE books ADD COLUMN listing_type VARCHAR(20) DEFAULT 'single'"),
            ('bundle_items', 'ALTER TABLE books ADD COLUMN bundle_items TEXT'),
            ('view_count', 'ALTER TABLE books ADD COLUMN view_count INTEGER DEFAULT 0'),
        ]:
            if col not in book_cols:
                conn.execute(text(ddl))
                print(f'  + books.{col}')

        col_cols2 = _column_names(conn, 'collections')
        if 'price_alert' not in col_cols2:
            conn.execute(text('ALTER TABLE collections ADD COLUMN price_alert BOOLEAN DEFAULT 1'))
            print('  + collections.price_alert')

        user_cols2 = _column_names(conn, 'users')
        for col, ddl in [
            ('schedule_json', 'ALTER TABLE users ADD COLUMN schedule_json TEXT'),
            ('no_show_count', 'ALTER TABLE users ADD COLUMN no_show_count INTEGER DEFAULT 0'),
        ]:
            if col not in user_cols2:
                conn.execute(text(ddl))
                print(f'  + users.{col}')

        book_cols3 = _column_names(conn, 'books')
        if 'school_id' not in book_cols3:
            conn.execute(text('ALTER TABLE books ADD COLUMN school_id VARCHAR(50)'))
            print('  + books.school_id')
            conn.execute(text(
                'UPDATE books SET school_id = (SELECT school_id FROM users WHERE users.id = books.owner_id) '
                'WHERE school_id IS NULL OR school_id = ""'
            ))

        spot_cols = _column_names(conn, 'campus_spots')
        for col, ddl in [
            ('map_x', 'ALTER TABLE campus_spots ADD COLUMN map_x FLOAT'),
            ('map_y', 'ALTER TABLE campus_spots ADD COLUMN map_y FLOAT'),
        ]:
            if col not in spot_cols:
                conn.execute(text(ddl))
                print(f'  + campus_spots.{col}')

        review_cols = _column_names(conn, 'reviews')
        if 'description_rating' not in review_cols:
            conn.execute(text('ALTER TABLE reviews ADD COLUMN description_rating INTEGER DEFAULT 5'))
            conn.execute(text(
                'UPDATE reviews SET description_rating = service_rating WHERE description_rating IS NULL'
            ))
            print('  + reviews.description_rating')

        conn.commit()

        conn.close()



        for code, name, order in DEFAULT_CATEGORIES:

            if not Category.query.filter_by(code=code).first():

                db.session.add(Category(

                    id=str(int(time.time() * 1000) + order),

                    code=code,

                    name=name,

                    sort_order=order,

                    created_at=time.strftime('%Y-%m-%d %H:%M:%S')

                ))

        db.session.commit()



        seed_campus_data(db, CampusSpot, CourseTextbook, SemesterCampaign, User=User, Book=Book)

        if not CampusSchool.query.first():
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            for sid, name, domains, order in [
                ('school_demo', '示例大学', ['edu.cn', 'stu.demo.edu.cn'], 1),
                ('school_default', '默认校园', ['campus.local'], 2),
            ]:
                db.session.add(CampusSchool(
                    id=sid, name=name,
                    email_domains=json.dumps(domains, ensure_ascii=False),
                    is_active=True, sort_order=order, created_at=ts
                ))
            db.session.commit()
            print('  + campus_schools 种子数据')

        db.create_all()
        seed_compliance_data(db, SensitiveWord, IsbnBlacklist)
        db.session.commit()

        c = migrate_json_comments()

        r = migrate_json_reviews()

        n_img = migrate_book_base64_images()

        print(f'数据库升级完成（迁移评论 {c} 条，评价 {r} 条，书籍图片 {n_img} 本）')





if __name__ == '__main__':

    upgrade()

