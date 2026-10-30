import { useRef } from 'react'
import { useUploadLicense, type Company } from '@/api/company'
import { ButtonLink, Button } from '@/components/ui/Button'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { formatDate } from '@/lib/format'

type StepState = 'done' | 'current' | 'todo' | 'failed'

/** C2 · What happens while the application is reviewed (or why it was stopped). */
export function PendingPage({ company }: { company: Company }) {
  const upload = useUploadLicense()
  const toast = useToast()
  const input = useRef<HTMLInputElement>(null)
  const stopped = company.status === 'rejected' || company.status === 'suspended'

  const steps: { title: string; text: string; state: StepState }[] = [
    { title: 'Application submitted', text: formatDate(company.created_at.slice(0, 10), true), state: 'done' },
    {
      title: 'License check',
      text: stopped ? (company.reject_reason ?? 'Our team could not approve this license.') : 'In progress: our team is reviewing your tourism license',
      state: stopped ? 'failed' : 'current',
    },
    { title: 'Trust score', text: 'Built from your license, Google rating and years in business', state: 'todo' },
    { title: 'Offers go live', text: 'Add hotel offers and start appearing to travelers', state: 'todo' },
  ]

  return (
    <div className="mx-auto max-w-[560px] rounded-[24px] border border-line bg-card p-7 sm:p-9">
      <span className={`grid size-14 place-items-center rounded-full ${stopped ? 'bg-terracotta-soft text-terracotta' : 'bg-gold-soft text-warning'}`}>
        <Icon name={stopped ? 'alert' : 'clock'} size={26} />
      </span>
      <h1 className="mt-5 font-display text-[30px] leading-tight">
        {company.status === 'suspended'
          ? `${company.name} is suspended`
          : stopped
            ? `We couldn’t approve ${company.name} yet`
            : `Thanks — we’re reviewing ${company.name}`}
      </h1>
      <p className="mt-3 text-[15px] text-ink-2">
        {stopped
          ? 'Your offers are hidden from travelers. Upload a new license or contact the Egyptora team.'
          : 'Most applications are reviewed within a few business days. This page updates as soon as you’re approved.'}
      </p>

      <ol className="mt-6">
        {steps.map((s, i) => (
          <li key={s.title} className="relative flex gap-4 pb-5 last:pb-0">
            {i < steps.length - 1 && <span className={`absolute top-8 left-[13px] h-[calc(100%-28px)] w-0.5 ${s.state === 'done' ? 'bg-nile' : 'bg-line'}`} />}
            <span
              className={`relative grid size-7 shrink-0 place-items-center rounded-full border-2 ${
                s.state === 'done'
                  ? 'border-nile bg-nile text-white'
                  : s.state === 'current'
                    ? 'border-terracotta bg-card'
                    : s.state === 'failed'
                      ? 'border-terracotta bg-terracotta text-white'
                      : 'border-line-muted bg-card'
              }`}
            >
              {s.state === 'done' && <Icon name="check" size={14} />}
              {s.state === 'current' && <span className="size-2.5 rounded-full bg-terracotta" />}
              {s.state === 'failed' && <Icon name="x" size={14} />}
            </span>
            <div>
              <p className={`font-bold ${s.state === 'todo' ? 'text-ink-2' : ''}`}>{s.title}</p>
              <p className="mt-0.5 text-sm text-ink-3">{s.text}</p>
            </div>
          </li>
        ))}
      </ol>

      {!stopped && (
        <p className="mt-6 flex gap-3 rounded-2xl bg-muted px-4 py-3.5 text-sm text-ink-2">
          <Icon name="spark" size={16} className="mt-0.5 text-terracotta" />
          While you wait, prepare nightly prices for your main hotels. Adding them takes a few minutes once you’re approved.
        </p>
      )}

      <div className="mt-6 flex flex-wrap gap-3">
        <ButtonLink to="/company/profile" variant="outline" leadingIcon="edit">
          Edit details
        </ButtonLink>
        <Button variant="outline" leadingIcon="upload" loading={upload.isPending} onClick={() => input.current?.click()}>
          Upload a new license
        </Button>
        <input
          ref={input}
          type="file"
          accept="application/pdf,image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f)
              upload.mutate(f, {
                onSuccess: () => toast('License uploaded — we’ll review it again'),
                onError: (err) => toast(err.message, 'error'),
              })
            e.target.value = ''
          }}
        />
      </div>
    </div>
  )
}
