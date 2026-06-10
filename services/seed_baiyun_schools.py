"""导入广州市白云区高校至 campus_schools（学籍认证 / 注册选校）"""
import json
import os
import time

from flask import Flask
from database_config import get_sqlalchemy_uri
from models import db, CampusSchool

# 广州市白云区主要高等院校（按 sort_order 排序）
BAIYUN_SCHOOLS = [
    (
        'school_gdufs',
        '广东外语外贸大学',
        ['gdufs.edu.cn', 'mail.gdufs.edu.cn', 'stu.gdufs.edu.cn'],
        10,
    ),
    (
        'school_baiyunu',
        '广东白云学院',
        ['baiyunu.edu.cn', 'stu.baiyunu.edu.cn'],
        20,
    ),
    (
        'school_nfu',
        '广州南方学院',
        ['nfu.edu.cn', 'stu.nfu.edu.cn'],
        30,
    ),
    (
        'school_gzcaac',
        '广州民航职业技术学院',
        ['gzcaac.edu.cn', 'caac.net.cn'],
        40,
    ),
    (
        'school_gdyouth',
        '广东青年职业学院',
        ['gdyouth.edu.cn', 'gdqy.edu.cn'],
        50,
    ),
    (
        'school_scbt',
        '广州华南商贸职业学院',
        ['scbt.edu.cn', 'gznanshang.edu.cn'],
        60,
    ),
    (
        'school_gdppla',
        '广东司法警官职业学院',
        ['gdppla.edu.cn', 'stu.gdppla.edu.cn'],
        70,
    ),
    (
        'school_gcp',
        '广州城市职业学院',
        ['gcp.edu.cn', 'stu.gcp.edu.cn'],
        80,
    ),
    (
        'school_gdipi',
        '广东理工职业学院',
        ['gdpt.edu.cn', 'gdipi.edu.cn'],
        90,
    ),
    (
        'school_gzucm',
        '广州中医药大学',
        ['gzucm.edu.cn', 'stu.gzucm.edu.cn'],
        100,
    ),
]


def upsert_baiyun_schools():
    """白云区高校 upsert 到 campus_schools"""
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    added, updated = 0, 0
    for sid, name, domains, order in BAIYUN_SCHOOLS:
        domains_json = json.dumps(domains, ensure_ascii=False)
        row = CampusSchool.query.filter_by(id=sid).first()
        if row:
            row.name = name
            row.email_domains = domains_json
            row.is_active = True
            row.sort_order = order
            updated += 1
        else:
            db.session.add(CampusSchool(
                id=sid,
                name=name,
                email_domains=domains_json,
                is_active=True,
                sort_order=order,
                created_at=ts,
            ))
            added += 1
    db.session.commit()
    return added, updated


def main():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        added, updated = upsert_baiyun_schools()
        total = CampusSchool.query.filter_by(is_active=True).count()
        print(f'白云区高校导入完成：新增 {added} 所，更新 {updated} 所，当前启用 {total} 所')
        for s in CampusSchool.query.order_by(CampusSchool.sort_order).all():
            print(f'  - {s.name} ({", ".join(s.domain_list())})')


if __name__ == '__main__':
    main()
