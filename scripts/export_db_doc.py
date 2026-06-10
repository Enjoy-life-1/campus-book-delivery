"""从 SQLAlchemy models 导出数据库设计文档"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sqlalchemy import Boolean, Float, Integer, String, Text
from models import db

TYPE_MAP = {
    String: lambda c: f'VARCHAR({c.type.length})' if c.type.length else 'VARCHAR',
    Text: lambda c: 'TEXT',
    Integer: lambda c: 'INTEGER',
    Float: lambda c: 'REAL',
    Boolean: lambda c: 'BOOLEAN',
}


def sql_type(col):
    if isinstance(col.type, Text):
        return 'TEXT'
    for cls, fn in TYPE_MAP.items():
        if cls is Text:
            continue
        if isinstance(col.type, cls):
            return fn(col)
    return str(col.type)


def col_remark(col):
    parts = []
    if col.primary_key:
        parts.append('主键')
    for fk in col.foreign_keys:
        ref = list(fk.column.table.name + '.' + fk.column.name for _ in [1])
        ondel = fk.ondelete or 'SET NULL'
        parts.append(f'外键→{fk.column.table.name}.id ON DELETE {ondel}')
    if not col.nullable and not col.primary_key:
        parts.append('非空')
    if col.unique:
        parts.append('唯一')
    if col.index:
        parts.append('索引')
    if col.default is not None and not col.primary_key:
        dv = col.default.arg if hasattr(col.default, 'arg') else col.default
        parts.append(f'默认={dv!r}')
    return '；'.join(parts) if parts else '-'


def table_comment(model):
    return (model.__doc__ or model.__tablename__).strip()


def gen_er_mermaid():
    entities = {
        'users': '用户',
        'books': '书籍',
        'orders': '订单',
        'collections': '收藏',
        'cart': '购物车',
        'comments': '评论',
        'reviews': '评价',
        'conversations': '会话',
        'messages': '消息',
        'campus_schools': '学校',
        'categories': '分类',
        'announcements': '公告',
        'wanted_posts': '求购',
        'price_offers': '议价',
        'notifications': '通知',
        'campus_spots': '面交点',
        'reports': '举报',
    }
    lines = ['erDiagram']
    rels = []
    seen = set()
    for model in db.Model.registry.mappers:
        cls = model.class_
        if not hasattr(cls, '__tablename__'):
            continue
        t = cls.__tablename__
        if t not in entities:
            continue
        for col in cls.__table__.columns:
            for fk in col.foreign_keys:
                rt = fk.column.table.name
                if rt in entities:
                    key = (t, rt)
                    if key not in seen:
                        seen.add(key)
                        card = '}o--||' if col.nullable else '}|--||'
                        rels.append(f'    {t} {card} {rt} : "{col.name}"')
    for t, label in entities.items():
        lines.append(f'    {t} {{')
        lines.append(f'        string id PK "{label}"')
        lines.append('    }')
    lines.extend(rels)
    return '\n'.join(lines)


def gen_ddl_sample():
    samples = ['users', 'books', 'orders', 'collections', 'messages']
    lines = []
    for name in samples:
        t = db.metadata.tables.get(name)
        if t is None:
            continue
        cols = []
        fks = []
        for col in t.columns:
            s = f'  {col.name} {sql_type(col)}'
            if not col.nullable:
                s += ' NOT NULL'
            if col.primary_key:
                s += ' PRIMARY KEY'
            cols.append(s)
            for fk in col.foreign_keys:
                ondel = fk.ondelete or 'SET NULL'
                fks.append(
                    f'  FOREIGN KEY ({col.name}) REFERENCES {fk.column.table.name}(id) ON DELETE {ondel}'
                )
        lines.append(f'CREATE TABLE {name} (')
        lines.append(',\n'.join(cols + fks))
        lines.append(');')
        lines.append('')
    return '\n'.join(lines)


def main():
    """导出 docs/数据库设计.md"""
    out = os.path.join(ROOT, 'docs', '数据库设计.md')
    tables = sorted(db.metadata.tables.items(), key=lambda x: x[0])

    buf = ['# 第 3 章 数据库设计\n']
    buf.append('> 自动生成，数据源：`models.py`（SQLAlchemy ORM）\n')

    buf.append('## 3.1 数据库概念设计\n')
    buf.append('系统核心实体及关系如下（E-R 图）：\n')
    buf.append('```mermaid')
    buf.append(gen_er_mermaid())
    buf.append('```\n')
    buf.append('**实体说明**：用户（users）发布书籍（books）、下单（orders）、收藏（collections）、评论（comments）、私信（messages）；书籍归属用户与学校（campus_schools）；订单关联买卖双方与书籍；会话（conversations）承载消息与面交预约。\n')

    buf.append('## 3.2 数据库逻辑设计\n')
    buf.append(f'共 **{len(tables)}** 张数据表，字段类型以 SQLite/MySQL 通用写法表示。\n')

    for tname, table in tables:
        model = None
        for m in db.Model.registry.mappers:
            if getattr(m.class_, '__tablename__', None) == tname:
                model = m.class_
                break
        title = table_comment(model) if model else tname
        buf.append(f'### 表 {tname}（{title}）\n')
        buf.append('| 字段 | 数据类型 | 备注 |')
        buf.append('|------|----------|------|')
        for col in table.columns:
            buf.append(f'| {col.name} | {sql_type(col)} | {col_remark(col)} |')
        for c in table.constraints:
            if c.__class__.__name__ == 'UniqueConstraint':
                cols = ', '.join(col.name for col in c.columns)
                name = c.name or f'uq_{tname}_{cols.replace(", ", "_")}'
                buf.append(f'\n唯一约束：`{name}`（{cols}）')
        buf.append('')

    buf.append('## 3.3 数据库物理结构实现\n')
    buf.append('数据库名：`campus_book_delivery`（SQLite 文件 `campus_book_delivery.db` 或 MySQL 库）。\n')
    buf.append('建表通过 `db.create_all()` / `upgrade_db.py` / `alembic upgrade head` 执行。代表性 DDL 如下（非全部代码）：\n')
    buf.append('```sql')
    buf.append(gen_ddl_sample())
    buf.append('```\n')
    buf.append('**索引**：各表外键字段及常用查询字段（如 `books.status`、`orders.status`、`users.username`）已建索引。\n')
    buf.append('**外键策略**：子表删除时 `CASCADE`（收藏/评论/消息等）或 `SET NULL`（书籍归属用户删除后保留记录）。\n')

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(buf))
    print(f'已生成: {out} ({len(tables)} 张表)')


if __name__ == '__main__':
    main()
