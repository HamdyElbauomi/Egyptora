import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { loadDraft, saveDraft, type PlanDraft } from './draft'

interface PlanValue {
  draft: PlanDraft
  update: (change: Partial<PlanDraft>) => void
}

const PlanContext = createContext<PlanValue | null>(null)

export function PlanProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<PlanDraft>(loadDraft)
  useEffect(() => saveDraft(draft), [draft])
  const update = useCallback((change: Partial<PlanDraft>) => setDraft((d) => ({ ...d, ...change })), [])
  return <PlanContext.Provider value={{ draft, update }}>{children}</PlanContext.Provider>
}

// the hook lives next to its provider on purpose
// oxlint-disable-next-line react/only-export-components
export function usePlan(): PlanValue {
  const value = useContext(PlanContext)
  if (!value) throw new Error('usePlan must be used inside <PlanProvider>')
  return value
}
