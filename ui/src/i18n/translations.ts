export const zhCN: Record<string, string> = {
  'Dashboard': '仪表盘', 'Scans': '扫描任务', 'Findings': '发现项',
  'Integrations': '集成', 'Settings': '设置', 'Logout': '退出登录',
  'New Scan': '新建扫描', 'Total Scans': '扫描总数', 'Total Findings': '发现项总数',
  'Active Scans': '活动扫描', 'View all scans': '查看全部扫描',
  'View all findings': '查看全部发现项', 'In progress or queued': '进行中或排队中',
  'Recent Scans': '最近扫描', 'Recent Findings': '最近发现项', 'View all': '查看全部',
  'Loading...': '加载中…', 'No scans yet': '暂无扫描',
  'Start by creating a new scan': '请先创建一个扫描任务', 'No findings yet': '暂无发现项',
  'Run a scan to discover security findings': '运行扫描以发现安全问题',
  'Organization Repositories': '组织仓库', 'Organization Users': '组织用户',
  'Search Code': '搜索代码', 'Search Commits': '搜索提交', 'Search Issues': '搜索议题',
  'Search Repositories': '搜索仓库', 'Search Users': '搜索用户',
  'QUEUED': '排队中', 'IN PROGRESS': '进行中', 'COMPLETED': '已完成', 'FAILED': '失败',
  'VALIDATED': '已验证', 'UNVALIDATED': '未验证', 'N/A': '无',
  'Automated security scanning for GitHub repositories': '面向 GitHub 仓库的自动化安全扫描',
  'Detect exposed secrets and sensitive information in your code using TruffleHog': '使用 TruffleHog 检测代码中泄露的密钥和敏感信息',
  'Go to Dashboard': '进入仪表盘', 'View Scans': '查看扫描', 'Get Started': '开始使用',
  'Sign in to GitAlerts': '登录 GitAlerts', 'Enter your credentials to access your account': '请输入凭据以访问您的账户',
  'Username': '用户名', 'Password': '密码', 'Enter your username': '请输入用户名',
  'Enter your password': '请输入密码', 'Signing in...': '正在登录…', 'Sign in': '登录',
  'Invalid username or password': '用户名或密码错误', 'Show Filters': '显示筛选条件',
  'Hide Filters': '隐藏筛选条件', 'Active filters:': '当前筛选：', 'Clear all': '全部清除',
  'Filter Scans': '筛选扫描', 'Filter Findings': '筛选发现项', 'Scan Type': '扫描类型',
  'All Types': '所有类型', 'Query Value': '查询值', 'Status': '状态',
  'All Statuses': '所有状态', 'Queued': '排队中', 'In Progress': '进行中',
  'Completed': '已完成', 'Failed': '失败', 'Created Date': '创建日期',
  'Completed Date': '完成日期', 'Apply Filters': '应用筛选', 'Cancel': '取消',
  'Delete': '删除', 'Deleting...': '正在删除…', 'Delete Selected': '删除所选项',
  'Select all': '全选', 'Type': '类型', 'Value': '值', 'Repository': '仓库',
  'Email': '电子邮箱', 'Validated': '已验证', 'Unvalidated': '未验证',
  'All': '全部', 'Actions': '操作', 'Details': '详情', 'Close': '关闭',
  'Created At': '创建时间', 'Completed At': '完成时间', 'Scan Details': '扫描详情',
  'Scan Information': '扫描信息', 'Error': '错误',
  'Back to Scans': '返回扫描列表', 'Create New Scan': '创建扫描任务',
  'Create Scan': '创建扫描', 'Creating...': '正在创建…', 'GitHub Integration': 'GitHub 集成',
  'Add Integration': '添加集成', 'Integration Name': '集成名称', 'GitHub Token': 'GitHub 令牌',
  'Connected': '已连接', 'Pending': '等待中', 'Disabled': '已禁用', 'Save': '保存',
  'Saving...': '正在保存…', 'Edit': '编辑', 'Remove': '移除', 'Add': '添加',
  'System Settings': '系统设置', 'Skip Recent Days': '跳过最近天数',
  'Verified Secrets Only': '仅扫描已验证密钥', 'Organization Repositories Only': '仅扫描组织仓库',
  'Save Settings': '保存设置', 'Settings saved!': '设置已保存！',
  'Failed to save settings': '设置保存失败', 'Ignore Finding Types': '忽略发现项类型',
  'Ignore Email Domains': '忽略邮箱域名', 'No ignored types yet': '暂无忽略类型',
  'No ignored domains yet': '暂无忽略域名', 'Language': '语言',
  'English': 'English', 'Simplified Chinese': '简体中文',
};

export function translateText(value: string): string {
  const exact = zhCN[value];
  if (exact) return exact;
  return value
    .replace(/^(\d+) findings?$/, '$1 个发现项')
    .replace(/^(\d+) scans? selected$/, '已选择 $1 个扫描任务')
    .replace(/^(\d+) findings? selected$/, '已选择 $1 个发现项')
    .replace(/^Delete Selected \((\d+)\)$/, '删除所选项（$1）');
}
