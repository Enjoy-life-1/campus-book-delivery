"""宿舍楼栋与校区对应关系（读取 settings.dorm_map）"""
import json

from .seed_baiyunu_trial import BYU_DORMS as DORM_BUILDINGS, BYU_DORM_MAP as DORM_MAP

# 与 seed_baiyunu_trial 保持一致
WEST_DORM_ALIASES = {
    '4栋': '4号楼', '5栋': '5号楼', '6栋': '6号楼', '7栋': '7号楼', '8栋': '8号楼',
    '9栋': '9号楼', '10栋': '10号楼', '10A栋': '10A', '10号楼(10A)': '10号楼',
    '1号学生公寓': '1号楼', '2号学生公寓': '2号楼',
    '西1栋': '1号楼', '西2栋': '2号楼', '西3栋': '3号楼', '西4栋': '4号楼',
    '西5栋': '5号楼', '西6栋': '6号楼', '西7栋': '7号楼', '西8栋': '8号楼',
    '西9栋': '9号楼', '西10栋': '10号楼', '西11栋': '12号楼', '西12栋': '12号楼',
    '若谷园': '6号楼', '璞园': '7号楼', '桂园': '8号楼', '思园': '9号楼',
    '特色公寓': '特色公寓·双人间', '招待所': '2号楼',
    '北1栋': '学思苑', '北2栋': '学思苑', '北3栋': '学思苑', '北4栋': '慎思苑',
    '北5栋': '慎思苑', '序园': '学思苑', '礼园': '创思苑', '和园': '创思苑',
}


def normalize_dorm_name(name):
    """别名 → 标准楼栋名（如 4栋→4号楼）"""
    n = (name or '').strip()
    return WEST_DORM_ALIASES.get(n, n)


def _parse_dorm_map(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
    return []


def load_dorm_catalog(Setting=None):
    """返回 items[{name,zone,...}], by_zone, all_names"""
    items = []
    if Setting is not None:
        row = Setting.query.filter_by(key='dorm_map').first()
        items = _parse_dorm_map(row.value if row else None)
    if not items:
        items = list(DORM_MAP)
    by_zone = {}
    names = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = (it.get('name') or '').strip()
        if not name:
            continue
        zone = (it.get('zone') or '西校区').strip()
        names.append(name)
        by_zone.setdefault(zone, []).append(name)
    if not names:
        names = list(DORM_BUILDINGS)
        for n in names:
            z = '校外' if n == '校外合租' else '西校区'
            by_zone.setdefault(z, []).append(n)
    return items, by_zone, names


def dorms_for_zone(by_zone, campus_zone):
    """某校区可选楼栋列表"""
    zone = campus_zone or '西校区'
    if zone in ('主校区', '生活区'):
        zone = '西校区'
    if zone == '校外':
        return list(by_zone.get('校外', ['校外合租']))
    return list(by_zone.get(zone, []))


def dorm_belongs_to_zone(dorm_name, campus_zone, by_zone):
    if not (dorm_name or '').strip():
        return True
    return normalize_dorm_name(dorm_name) in dorms_for_zone(by_zone, campus_zone)


def validate_dorm_zone(dorm_name, campus_zone, by_zone):
    """发布/编辑时校验楼栋是否属于所选校区"""
    dorm = normalize_dorm_name(dorm_name)
    zone = campus_zone or '西校区'
    if zone in ('主校区', '生活区'):
        zone = '西校区'
    if not dorm:
        return True, ''
    if dorm_belongs_to_zone(dorm, zone, by_zone):
        return True, ''
    allowed = '、'.join(dorms_for_zone(by_zone, zone)[:8])
    suffix = f'…等' if len(dorms_for_zone(by_zone, zone)) > 8 else ''
    return False, f'「{dorm}」不属于{zone}，可选：{allowed}{suffix}'
