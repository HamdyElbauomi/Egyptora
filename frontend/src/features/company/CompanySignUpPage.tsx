import { useRef, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { registerCompany } from '@/api/company'
import { useAuth } from '@/auth/AuthProvider'
import { homeFor } from '@/auth/tokens'
import { Button } from '@/components/ui/Button'
import { Icon, type IconName } from '@/components/ui/Icon'
import { Logo } from '@/components/ui/Logo'
import { TextField } from '@/components/ui/TextField'
import pattern from '@/assets/pattern-mashrabiya.svg'

const MAX_LICENSE_MB = 10
const LICENSE_TYPES = 'application/pdf,image/jpeg,image/png,image/webp'

const WHY: { icon: IconName; title: string; text: string }[] = [
  { icon: 'search', title: 'Travelers find you by asking', text: 'Our AI matches your offers to what travelers type, like “quiet hotel near Karnak”.' },
  { icon: 'chart', title: 'See where you stand', text: 'Know right away whether you have the lowest price on each hotel.' },
  { icon: 'shield', title: 'Trust that grows with you', text: 'Start with a score from your license and reviews, then earn traveler ratings.' },
]

/** C1 · Companies apply with their tourism license. They can sign in at once; offers go live after approval. */
export function CompanySignUpPage() {
  const { session, adoptTokens } = useAuth()
  const navigate = useNavigate()
  const fileInput = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({ company_name: '', license_no: '', owner_name: '', email: '', password: '', phone: '', website: '' })
  const [license, setLicense] = useState<File | null>(null)
  const [agreed, setAgreed] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (session && !busy) return <Navigate to={homeFor(session.role)} replace />

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [key]: e.target.value }))
  const tooBig = license !== null && license.size > MAX_LICENSE_MB * 1024 * 1024

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!license || tooBig || !agreed) return
    setError(null)
    setBusy(true)
    try {
      const out = await registerCompany({ ...form, license_file: license })
      adoptTokens(out)
      navigate('/company', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-dvh">
      <div className="flex-1 px-4 py-6 sm:px-10 lg:px-[60px]">
        <div className="flex items-center gap-3">
          <Logo size="md" />
          <span className="rounded-full bg-nile-soft px-3 py-1 text-[13px] font-semibold text-nile-strong">For travel companies</span>
        </div>
        <h1 className="mt-8 font-display text-[34px] leading-tight sm:text-[40px]">List your hotel offers on Egyptora</h1>
        <p className="mt-2 text-[15px] text-ink-2">Tell us about your company. We review every application before your offers go live.</p>

        <form onSubmit={submit} className="mt-7 grid max-w-[680px] gap-x-4 gap-y-5 sm:grid-cols-2">
          <TextField label="Company name" required minLength={2} value={form.company_name} onChange={set('company_name')} />
          <TextField label="Tourism license number" required value={form.license_no} onChange={set('license_no')} />
          <TextField label="Your name" required minLength={2} autoComplete="name" value={form.owner_name} onChange={set('owner_name')} />
          <TextField label="Phone (optional)" type="tel" autoComplete="tel" placeholder="+20 …" value={form.phone} onChange={set('phone')} />
          <TextField label="Contact email" type="email" required autoComplete="email" placeholder="name@company.com" value={form.email} onChange={set('email')} />
          <TextField label="Password" type="password" required minLength={8} autoComplete="new-password" hint="At least 8 characters" value={form.password} onChange={set('password')} />

          <div className="sm:col-span-2">
            <div className="flex flex-col items-center rounded-[18px] border-[1.5px] border-dashed border-line-strong bg-raised px-6 py-6 text-center">
              <span className="grid size-11 place-items-center rounded-full bg-terracotta-soft text-terracotta">
                <Icon name={license ? 'file' : 'upload'} size={20} />
              </span>
              <p className="mt-3 font-bold">{license ? license.name : 'Upload your tourism license'}</p>
              <p className={`mt-1 text-sm ${tooBig ? 'font-semibold text-terracotta' : 'text-ink-3'}`}>
                {tooBig ? `That file is over ${MAX_LICENSE_MB} MB` : `PDF or photo · up to ${MAX_LICENSE_MB} MB`}
              </p>
              <Button size="sm" variant="outline" className="mt-3" onClick={() => fileInput.current?.click()}>
                {license ? 'Choose another file' : 'Choose file'}
              </Button>
              <input
                ref={fileInput}
                type="file"
                accept={LICENSE_TYPES}
                className="hidden"
                data-testid="license-input"
                onChange={(e) => setLicense(e.target.files?.[0] ?? null)}
              />
            </div>
          </div>

          <TextField className="sm:col-span-2" label="Website or social page (optional)" type="url" placeholder="https://" value={form.website} onChange={set('website')} />

          <label className="flex items-start gap-3 text-[15px] text-ink-2 sm:col-span-2">
            <input type="checkbox" className="mt-1 size-4 accent-[#a64b28]" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
            I confirm this information is accurate and that I may list offers for this company.
          </label>

          {error && (
            <p role="alert" className="flex gap-2 rounded-xl bg-terracotta-soft px-4 py-3 text-[15px] text-terracotta-strong sm:col-span-2">
              <Icon name="alert" size={18} className="mt-0.5" />
              {error}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-5 sm:col-span-2">
            <Button type="submit" size="lg" icon="arrowR" loading={busy} disabled={!license || tooBig || !agreed}>
              Submit for review
            </Button>
            <Link to="/sign-in" className="text-[15px] font-bold text-terracotta hover:text-terracotta-strong">
              Already a partner? Sign in
            </Link>
          </div>
        </form>
      </div>

      <aside
        className="relative hidden w-[40%] max-w-[560px] shrink-0 bg-terracotta p-10 text-white lg:block"
        style={{ backgroundImage: `url("${pattern}")`, backgroundSize: 'cover' }}
      >
        <h2 className="font-display text-[30px]">Why partner with Egyptora</h2>
        <ul className="mt-6 space-y-6">
          {WHY.map((w) => (
            <li key={w.title} className="flex gap-4">
              <span className="grid size-11 shrink-0 place-items-center rounded-full bg-gold text-ink">
                <Icon name={w.icon} size={20} />
              </span>
              <span>
                <span className="block font-bold">{w.title}</span>
                <span className="mt-1 block text-[15px] text-white/85">{w.text}</span>
              </span>
            </li>
          ))}
        </ul>
        <div className="mt-8 rounded-[20px] bg-card p-6 text-ink">
          <p className="font-bold">How approval works</p>
          <ol className="mt-3 space-y-3 text-[15px]">
            {['Apply with your company details', 'We check your tourism license', 'Add offers and go live'].map((t, i) => (
              <li key={t} className="flex items-center gap-3">
                <span className="grid size-7 place-items-center rounded-full bg-terracotta text-sm font-bold text-white">{i + 1}</span>
                {t}
              </li>
            ))}
          </ol>
        </div>
      </aside>
    </div>
  )
}
