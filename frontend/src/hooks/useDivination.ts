import { useState } from 'react'

// Legacy pages remain as upstream references, but their browser-credential and
// unreviewed streaming transport is disabled. The original is in upstream Git.
// New reading interfaces will use the independent audited server adapter.
export function useDivination(_promptType: string) {
  const [result, setResult] = useState('')
  const [showDrawer, setShowDrawer] = useState(false)

  const onSubmit = async (_params: Record<string, unknown>) => {
    setResult('此旧接口已停用，正式解卦服务尚未接入。')
    setShowDrawer(true)
  }

  return { result, loading: false, resultLoading: false, streaming: false,
    showDrawer, setShowDrawer, onSubmit }
}
