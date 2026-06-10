// 营销落地页配置：/feature/:slug
export const FEATURE_PAGES = {
  genuine: {
    title: '正版保障',
    subtitle: '校园二手书，来源可查、交易可溯',
    icon: 'fa-check-circle',
    theme: 'success',
    benefits: [
      { icon: 'fa-shield', title: '审核上架', desc: '书籍发布需管理员审核，减少盗版风险' },
      { icon: 'fa-eye', title: '当面验货', desc: '校内面交点交易，付款前可检查品相' },
      { icon: 'fa-comments', title: '站内沟通', desc: '私信留痕，纠纷可追溯' }
    ],
    cta: { to: '/booksList', label: '浏览正版二手书' }
  },
  'low-price': {
    title: '低价转让',
    subtitle: '教材低至3折，省钱又环保',
    icon: 'fa-money',
    theme: 'warning',
    benefits: [
      { icon: 'fa-line-chart', title: '倒计时降价', desc: '卖家可开启72小时降价，捡漏更划算' },
      { icon: 'fa-handshake-o', title: '议价功能', desc: '买家出价，卖家一键接受生成订单' },
      { icon: 'fa-calendar', title: '学期专场', desc: '开学季/期末清仓主题集中淘书' }
    ],
    cta: { to: '/semester', label: '进入学期专场' }
  },
  'campus-trade': {
    title: '校园交易',
    subtitle: '同校同楼，面交更省心',
    icon: 'fa-map-marker',
    theme: 'primary',
    benefits: [
      { icon: 'fa-university', title: '同校筛选', desc: '仅看本校卖家，缩短交易距离' },
      { icon: 'fa-building', title: '楼栋标注', desc: '按宿舍楼筛选，楼下即可取书' },
      { icon: 'fa-map-pin', title: '面交点预约', desc: '图书馆、食堂等8个校内预设地点' }
    ],
    cta: { to: '/booksList?same_school=1', label: '同校书籍' }
  },
  'new-condition': {
    title: '9成新以上',
    subtitle: '成色标注清晰，买得放心',
    icon: 'fa-star',
    theme: 'success',
    benefits: [
      { icon: 'fa-tag', title: '成色分级', desc: '全新/九成新/八成新等标准标注' },
      { icon: 'fa-camera', title: '实拍上图', desc: '发布需上传实物照片' },
      { icon: 'fa-star-o', title: '评价体系', desc: '交易完成后双向评价' }
    ],
    cta: { to: '/booksList', label: '找成色好的书' }
  },
  exchange: {
    title: '支持互换',
    subtitle: '以书换书，让知识流动',
    icon: 'fa-exchange',
    theme: 'info',
    benefits: [
      { icon: 'fa-bullhorn', title: '求购广场', desc: '发布求购，系统自动匹配在售' },
      { icon: 'fa-envelope', title: '站内协商', desc: '私信沟通互换或补差价方案' },
      { icon: 'fa-graduation-cap', title: '按课找书', desc: '按学院专业课程找教材' }
    ],
    cta: { to: '/wanted', label: '去求购广场' }
  }
}
