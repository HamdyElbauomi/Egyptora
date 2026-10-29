import { useState } from 'react'
import { TextField } from '@/components/ui/TextField'
import { BUDGETS, tierForAmount } from '../draft'
import { usePlan } from '../PlanContext'
import { StepFrame } from '../StepFrame'

export function BudgetStep() {
  const { draft, update } = usePlan()
  const [amount, setAmount] = useState(draft.budgetTotal ? draft.budgetTotal.toLocaleString('en-US') : '')

  const onAmount = (text: string) => {
    const digits = text.replace(/[^\d]/g, '').slice(0, 9)
    setAmount(digits ? Number(digits).toLocaleString('en-US') : '')
    if (!digits) {
      update({ budgetTotal: null })
      return
    }
    const value = Number(digits)
    update({ budgetTotal: value, budgetLevel: tierForAmount(value) })
  }

  return (
    <StepFrame
      step="budget"
      title="What’s your budget?"
      subtitle="Per person, for the whole trip — hotels, transport and tickets included."
      hint="You can fine-tune this later in chat"
    >
      <div role="radiogroup" aria-label="Budget" className="grid gap-4 sm:grid-cols-3">
        {BUDGETS.map((b) => {
          const selected = draft.budgetLevel === b.level
          return (
            <button
              key={b.level}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => {
                update({ budgetLevel: b.level, budgetTotal: null })
                setAmount('')
              }}
              className={`rounded-[18px] border-[1.5px] p-[26px] text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-terracotta ${
                selected ? 'border-terracotta bg-selected' : 'border-line bg-card hover:border-line-strong'
              }`}
            >
              <span className="block text-sm font-bold tracking-[0.06em] text-nile uppercase">{b.tier}</span>
              <span className="mt-3 block font-display text-[26px] leading-tight">{b.price}</span>
              <span className="mt-3 block text-[15px] leading-normal text-ink-2">{b.description}</span>
            </button>
          )
        })}
      </div>

      <div className="mt-10 flex flex-col gap-x-4 sm:flex-row sm:items-end">
        <TextField
          className="w-full sm:w-[320px]"
          label="Or type an exact amount (EGP per person)"
          inputMode="numeric"
          placeholder="e.g. 15,000"
          value={amount}
          onChange={(e) => onAmount(e.target.value)}
        />
        <p className="mt-2 text-sm text-ink-2 sm:mt-0 sm:pb-[18px]">
          We’ll keep the plan within it and tell you if something can’t fit.
        </p>
      </div>
    </StepFrame>
  )
}
