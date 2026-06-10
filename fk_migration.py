"""外键迁移：孤儿数据清理 + 约束添加"""
from sqlalchemy import text


def _null_empty(conn, table, col):
    """空字符串外键列置 NULL，避免 FK 校验失败"""
    conn.execute(text(f"UPDATE {table} SET {col} = NULL WHERE {col} = ''"))

def clean_orphans(conn):
    """清理悬空引用（兼容 MySQL / SQLite）"""
    for table, col in (
        ('users', 'school_id'), ('books', 'owner_id'), ('books', 'sellerId'),
        ('books', 'school_id'), ('orders', 'book_id'), ('orders', 'buyer_id'),
        ('orders', 'seller_id'), ('reviews', 'book_id'), ('reviews', 'reviewed_user_id'),
        ('ban_appeals', 'handled_by'),
    ):
        _null_empty(conn, table, col)

    stmts = [
        ("users", "school_id", "campus_schools"),
        ("books", "owner_id", "users"),
        ("books", "sellerId", "users"),
        ("books", "school_id", "campus_schools"),
        ("orders", "book_id", "books"),
        ("orders", "buyer_id", "users"),
        ("orders", "seller_id", "users"),
        ("reviews", "book_id", "books"),
        ("reviews", "reviewed_user_id", "users"),
        ("ban_appeals", "handled_by", "users"),
    ]
    for table, col, ref in stmts:
        conn.execute(text(
            f"UPDATE {table} SET {col} = NULL WHERE {col} IS NOT NULL "
            f"AND NOT EXISTS (SELECT 1 FROM {ref} r WHERE r.id = {table}.{col})"
        ))
    conn.execute(text(
        "DELETE FROM admin_audit_logs WHERE NOT EXISTS "
        "(SELECT 1 FROM users r WHERE r.id = admin_audit_logs.admin_id)"
    ))

    deletes = [
        ("collections", "user_id", "users", "book_id", "books"),
        ("cart", "user_id", "users", "book_id", "books"),
        ("comments", "user_id", "users", "book_id", "books"),
        ("wanted_posts", "user_id", "users", None, None),
        ("notifications", "user_id", "users", None, None),
        ("notification_outbox", "user_id", "users", None, None),
        ("reports", "reporter_id", "users", None, None),
        ("publish_templates", "user_id", "users", None, None),
        ("book_views", "book_id", "books", "user_id", "users"),
    ]
    for spec in deletes:
        table, c1, r1, c2, r2 = spec
        if c2:
            conn.execute(text(
                f"DELETE FROM {table} WHERE NOT EXISTS (SELECT 1 FROM {r1} r WHERE r.id = {table}.{c1}) "
                f"OR ({table}.{c2} IS NOT NULL AND {table}.{c2} != '' "
                f"AND NOT EXISTS (SELECT 1 FROM {r2} r2 WHERE r2.id = {table}.{c2}))"
            ))
        else:
            conn.execute(text(
                f"DELETE FROM {table} WHERE NOT EXISTS (SELECT 1 FROM {r1} r WHERE r.id = {table}.{c1})"
            ))

    conn.execute(text(
        "DELETE FROM reviews WHERE NOT EXISTS (SELECT 1 FROM orders r WHERE r.id = reviews.order_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = reviews.reviewer_id)"
    ))
    conn.execute(text(
        "DELETE FROM price_offers WHERE NOT EXISTS (SELECT 1 FROM books r WHERE r.id = price_offers.book_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = price_offers.buyer_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = price_offers.seller_id)"
    ))
    conn.execute(text(
        "DELETE FROM user_blocks WHERE NOT EXISTS (SELECT 1 FROM users r WHERE r.id = user_blocks.blocker_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = user_blocks.blocked_id)"
    ))
    conn.execute(text(
        "DELETE FROM user_follows WHERE NOT EXISTS (SELECT 1 FROM users r WHERE r.id = user_follows.follower_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = user_follows.seller_id)"
    ))
    conn.execute(text(
        "DELETE FROM ban_appeals WHERE NOT EXISTS (SELECT 1 FROM users r WHERE r.id = ban_appeals.user_id)"
    ))
    conn.execute(text(
        "DELETE FROM conversations WHERE NOT EXISTS (SELECT 1 FROM users r WHERE r.id = conversations.user_a_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = conversations.user_b_id)"
    ))
    conn.execute(text(
        "DELETE FROM messages WHERE NOT EXISTS (SELECT 1 FROM conversations r WHERE r.id = messages.conversation_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = messages.sender_id)"
    ))
    conn.execute(text(
        "DELETE FROM meeting_appointments WHERE NOT EXISTS (SELECT 1 FROM conversations r "
        "WHERE r.id = meeting_appointments.conversation_id) "
        "OR NOT EXISTS (SELECT 1 FROM users r WHERE r.id = meeting_appointments.proposer_id)"
    ))


FK_SPECS = [
    # (表, 本地列, 引用表, 引用列, ON DELETE, 约束名)
    ('users', ['school_id'], 'campus_schools', ['id'], 'SET NULL', 'fk_users_school'),    ('books', ['owner_id'], 'users', ['id'], 'SET NULL', 'fk_books_owner'),
    ('books', ['sellerId'], 'users', ['id'], 'SET NULL', 'fk_books_seller'),
    ('books', ['school_id'], 'campus_schools', ['id'], 'SET NULL', 'fk_books_school'),
    ('orders', ['book_id'], 'books', ['id'], 'SET NULL', 'fk_orders_book'),
    ('orders', ['buyer_id'], 'users', ['id'], 'SET NULL', 'fk_orders_buyer'),
    ('orders', ['seller_id'], 'users', ['id'], 'SET NULL', 'fk_orders_seller'),
    ('collections', ['book_id'], 'books', ['id'], 'CASCADE', 'fk_collections_book'),
    ('collections', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_collections_user'),
    ('cart', ['book_id'], 'books', ['id'], 'CASCADE', 'fk_cart_book'),
    ('cart', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_cart_user'),
    ('comments', ['book_id'], 'books', ['id'], 'CASCADE', 'fk_comments_book'),
    ('comments', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_comments_user'),
    ('reviews', ['order_id'], 'orders', ['id'], 'CASCADE', 'fk_reviews_order'),
    ('reviews', ['book_id'], 'books', ['id'], 'SET NULL', 'fk_reviews_book'),
    ('reviews', ['reviewer_id'], 'users', ['id'], 'CASCADE', 'fk_reviews_reviewer'),
    ('reviews', ['reviewed_user_id'], 'users', ['id'], 'SET NULL', 'fk_reviews_reviewed'),
    ('wanted_posts', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_wanted_user'),
    ('conversations', ['user_a_id'], 'users', ['id'], 'CASCADE', 'fk_conv_user_a'),
    ('conversations', ['user_b_id'], 'users', ['id'], 'CASCADE', 'fk_conv_user_b'),
    ('messages', ['conversation_id'], 'conversations', ['id'], 'CASCADE', 'fk_msg_conv'),
    ('messages', ['sender_id'], 'users', ['id'], 'CASCADE', 'fk_msg_sender'),
    ('meeting_appointments', ['conversation_id'], 'conversations', ['id'], 'CASCADE', 'fk_appt_conv'),
    ('meeting_appointments', ['proposer_id'], 'users', ['id'], 'CASCADE', 'fk_appt_proposer'),
    ('price_offers', ['book_id'], 'books', ['id'], 'CASCADE', 'fk_offers_book'),
    ('price_offers', ['buyer_id'], 'users', ['id'], 'CASCADE', 'fk_offers_buyer'),
    ('price_offers', ['seller_id'], 'users', ['id'], 'CASCADE', 'fk_offers_seller'),
    ('notifications', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_notify_user'),
    ('notification_outbox', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_outbox_user'),
    ('user_blocks', ['blocker_id'], 'users', ['id'], 'CASCADE', 'fk_block_blocker'),
    ('user_blocks', ['blocked_id'], 'users', ['id'], 'CASCADE', 'fk_block_blocked'),
    ('user_follows', ['follower_id'], 'users', ['id'], 'CASCADE', 'fk_follow_follower'),
    ('user_follows', ['seller_id'], 'users', ['id'], 'CASCADE', 'fk_follow_seller'),
    ('reports', ['reporter_id'], 'users', ['id'], 'CASCADE', 'fk_reports_reporter'),
    ('admin_audit_logs', ['admin_id'], 'users', ['id'], 'RESTRICT', 'fk_audit_admin'),
    ('ban_appeals', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_appeal_user'),
    ('ban_appeals', ['handled_by'], 'users', ['id'], 'SET NULL', 'fk_appeal_handler'),
    ('book_views', ['book_id'], 'books', ['id'], 'CASCADE', 'fk_views_book'),
    ('publish_templates', ['user_id'], 'users', ['id'], 'CASCADE', 'fk_tpl_user'),
]


def _existing_fk_names(conn):
    """MySQL 查 information_schema；SQLite 暂不精确匹配"""
    if conn.dialect.name == 'mysql':
        db = conn.execute(text('SELECT DATABASE()')).scalar()
        rows = conn.execute(text(
            "SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA = :db AND CONSTRAINT_TYPE = 'FOREIGN KEY'"
        ), {'db': db}).fetchall()
        return {r[0] for r in rows}
    rows = conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND sql LIKE '%REFERENCES%'"
    )).fetchall()
    return set()


def add_foreign_keys(op):
    """按 FK_SPECS 批量 create_foreign_key（跳过已存在）"""
    conn = op.get_bind()
    existing = _existing_fk_names(conn)
    by_table = {}
    for spec in FK_SPECS:
        by_table.setdefault(spec[0], []).append(spec)
    for table, specs in by_table.items():
        pending = [s for s in specs if s[5] not in existing]
        if not pending:
            continue
        with op.batch_alter_table(table) as batch:
            for _, local, ref, ref_cols, ondelete, name in pending:
                batch.create_foreign_key(name, ref, local, ref_cols, ondelete=ondelete)


def drop_foreign_keys(op):
    """降级：逆序 drop_constraint"""
    by_table = {}
    for spec in FK_SPECS:
        by_table.setdefault(spec[0], []).append(spec)
    for table, specs in by_table.items():
        with op.batch_alter_table(table) as batch:
            for spec in reversed(specs):
                batch.drop_constraint(spec[5], type_='foreignkey')
