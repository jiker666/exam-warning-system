export const RISK_META = {
  high: { label: '高风险', cls: 'risk-high' },
  medium: { label: '中风险', cls: 'risk-medium' },
  low: { label: '低风险', cls: 'risk-low' },
}

export const ANALYSIS_META = {
  pending: { label: '待分析', cls: 'ana-pending' },
  processing: { label: 'AI 分析中', cls: 'ana-processing' },
  completed: { label: '分析完成', cls: 'ana-completed' },
  failed: { label: '分析失败', cls: 'ana-failed' },
}

export const STATUS_META = {
  draft: { label: '草稿', cls: 'st-draft' },
  published: { label: '已发布', cls: 'st-published' },
  in_progress: { label: '进行中', cls: 'st-progress' },
  submitted: { label: '已提交', cls: 'st-submitted' },
}

export function RiskBadge({ level }) {
  const m = RISK_META[level] || RISK_META.low
  return <span className={`badge ${m.cls}`}>{m.label}</span>
}

export function AnalysisBadge({ status, isMock }) {
  const m = ANALYSIS_META[status] || ANALYSIS_META.pending
  return (
    <span className="badge-group">
      <span className={`badge ${m.cls}`}>{m.label}</span>
      {status === 'completed' && <MockBadge isMock={isMock} />}
    </span>
  )
}

export function StatusBadge({ status }) {
  const m = STATUS_META[status] || { label: status, cls: '' }
  return <span className={`badge ${m.cls}`}>{m.label}</span>
}

export function MockBadge({ isMock }) {
  return isMock ? (
    <span className="badge mock">⚠ Demo 模拟分析</span>
  ) : (
    <span className="badge real">AssemblyAI 真实分析</span>
  )
}
