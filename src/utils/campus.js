// 校区/宿舍楼工具：与后端 campus_dorms、User.campus_zone 对齐
export const CAMPUS_ZONES = ['西校区', '北校区', '校外']
export const CAMPUS_ADDRESSES = {
  西校区: '广州市白云区江高镇学苑路1号',
  北校区: '广州市白云区钟落潭镇九佛西路280号',
  校外: ''
}

/** 旧数据「主校区/生活区」→ 西校区 */
export function normalizeCampusZone(zone) {
  if (!zone || zone === '主校区' || zone === '生活区') return '西校区'
  return zone
}

/** catalog: GET /api/campus/dorms 返回体（含 by_zone） */
export function dormsForZone(catalog, zone) {
  const z = normalizeCampusZone(zone)
  if (!catalog?.by_zone) return catalog?.dorms || []
  return catalog.by_zone[z] || []
}

const DORM_ALIASES = {
  '4栋': '4号楼', '5栋': '5号楼', '6栋': '6号楼', '7栋': '7号楼', '8栋': '8号楼',
  '9栋': '9号楼', '10栋': '10号楼', '10A栋': '10A',
  '1号学生公寓': '1号楼', '2号学生公寓': '2号楼', '特色公寓': '特色公寓·双人间',
}

export function normalizeDormName(name) {
  const n = (name || '').trim()
  return DORM_ALIASES[n] || n
}

export function syncDormToZone(form, catalog) {
  // 切换校区时校验 dorm_building 是否属于该 zone
  const allowed = dormsForZone(catalog, form.campus_zone)
  if (form.dorm_building) {
    form.dorm_building = normalizeDormName(form.dorm_building)
    if (allowed.length && !allowed.includes(form.dorm_building)) {
      form.dorm_building = ''
    }
  }
}
