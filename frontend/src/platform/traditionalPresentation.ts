import { type JudgementPreview } from './traditionalPreviewContract'

export const PRESENTATION_VERSION = 'traditional_presentation_v2'

// Display ONLY. Never run on source_quotes/source text, mutate the API value,
// trim conditions, or use a word in an ancient text to decide a direction.
export function displaySentence(text: string): string {
  return text.trim().replace(/。{2,}/g, '。').replace(/。；/g, '；')
}

export function previewOverview(value: JudgementPreview): string[] {
  const lines = value.review_status === 'bounded'
    ? ['这次有已审核的动爻依据。请把上方倾向与下方成立条件一起看，不能只凭倾向判断事情成败。']
    : value.review_status === 'branch_unresolved'
      ? ['这条爻有不同的条件分支。现有问题还不能确认该用哪一支，因此暂不确定综合方向。']
      : ['本次只采用可靠的卦象结构与基础卦义，不给出扩展综合结论。']
  if (value.strength_modifiers.some(item => item.id === 'strength.controlling_side_weak')) {
    lines.push('克体一方衰，其作用受时令限制；原有用克体关系仍在，不能理解为不利已消除。')
  }
  if (value.conflicts.length) lines.push('主要依据有条件性冲突，现阶段不能选定单一结果。')
  lines.push('现实条件尚未核实。传统倾向不代表现实事件一定发生。')
  return lines
}

export function factorDisplay(text: string, value: JudgementPreview): string {
  const branch = value.branches.findIndex(item => displaySentence(item.text) === displaySentence(text))
  return branch < 0 ? displaySentence(text) : `见下方${value.review_status === 'branch_unresolved' ? '条件分支' : '提醒'} ${branch + 1}，仅在对应条件范围内适用。`
}
