import { useState, type FormEvent } from 'react'
import { useSaveCity, useSaveInterest, type InterestInput } from '@/api/admin'
import { useCities, useInterests, type City, type Interest } from '@/api/queries'
import { Button } from '@/components/ui/Button'
import { Dialog } from '@/components/ui/Dialog'
import { TextArea } from '@/components/ui/fields'
import { Icon } from '@/components/ui/Icon'
import { INTEREST_ICONS, isIconName, type IconName } from '@/components/ui/icons'
import { PageLoader } from '@/components/ui/Spinner'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/components/ui/Toast'
import { plural } from '@/lib/format'
import { card } from './styles'
import { AdminHeader } from './ui'

/** Cities travelers can visit and the interest cards of preference step 1. */
export function CatalogPage() {
  const cities = useCities()
  const interests = useInterests()
  const [city, setCity] = useState<City | 'new' | null>(null)
  const [interest, setInterest] = useState<Interest | 'new' | null>(null)

  return (
    <>
      <AdminHeader title="Cities & interests" subtitle="What travelers choose from when they plan a trip." />
      <div className="mt-7 grid gap-5 lg:grid-cols-2">
        <section className={`${card} p-5 sm:p-6`}>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Cities</h2>
            <Button size="sm" leadingIcon="plus" onClick={() => setCity('new')}>
              Add city
            </Button>
          </div>
          {cities.isPending ? (
            <PageLoader />
          ) : (
            <ul className="mt-3">
              {cities.data?.map((c) => (
                <li key={c.id} className="flex items-center gap-3 border-t border-line py-3 first:border-t-0">
                  <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-muted text-terracotta">
                    <Icon name="pin" size={18} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-bold">{c.name}</span>
                    <span className="block truncate text-[13px] text-ink-3">
                      {plural(c.places_count, 'place')}
                      {c.description ? ` · ${c.description}` : ''}
                    </span>
                  </span>
                  <Button size="sm" variant="ghost" onClick={() => setCity(c)}>
                    Edit
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className={`${card} p-5 sm:p-6`}>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Interests</h2>
            <Button size="sm" leadingIcon="plus" onClick={() => setInterest('new')}>
              Add interest
            </Button>
          </div>
          {interests.isPending ? (
            <PageLoader />
          ) : (
            <ul className="mt-3">
              {interests.data?.map((i) => (
                <li key={i.id} className="flex items-center gap-3 border-t border-line py-3 first:border-t-0">
                  <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-muted text-terracotta">
                    <Icon name={isIconName(i.icon) ? i.icon : 'spark'} size={18} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-bold">{i.name}</span>
                    <span className={`block truncate text-[13px] ${i.description ? 'text-ink-3' : 'text-terracotta'}`}>{i.description ?? 'No description yet'}</span>
                  </span>
                  <Button size="sm" variant="ghost" onClick={() => setInterest(i)}>
                    Edit
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <Dialog open={city !== null} onClose={() => setCity(null)} title={city === 'new' ? 'Add a city' : `Edit ${city?.name ?? ''}`}>
        {city !== null && <CityForm city={city === 'new' ? undefined : city} onDone={() => setCity(null)} />}
      </Dialog>
      <Dialog open={interest !== null} onClose={() => setInterest(null)} title={interest === 'new' ? 'Add an interest' : `Edit ${interest?.name ?? ''}`} size="lg">
        {interest !== null && <InterestForm interest={interest === 'new' ? undefined : interest} onDone={() => setInterest(null)} />}
      </Dialog>
    </>
  )
}

function CityForm({ city, onDone }: { city?: City; onDone: () => void }) {
  const save = useSaveCity()
  const toast = useToast()
  const [v, setV] = useState({
    name: city?.name ?? '',
    description: city?.description ?? '',
    image_url: city?.image_url ?? '',
    lat: city?.lat?.toString() ?? '',
    lng: city?.lng?.toString() ?? '',
  })
  const set = (k: keyof typeof v) => (e: { target: { value: string } }) => setV((x) => ({ ...x, [k]: e.target.value }))
  const num = (x: string) => (x.trim() === '' ? null : Number(x))
  const submit = (e: FormEvent) => {
    e.preventDefault()
    save.mutate(
      { id: city?.id, body: { name: v.name.trim(), description: v.description.trim() || null, image_url: v.image_url.trim() || null, lat: num(v.lat), lng: num(v.lng) } },
      { onSuccess: () => (toast(city ? 'City saved' : 'City added'), onDone()), onError: (err) => toast(err.message, 'error') },
    )
  }
  return (
    <form onSubmit={submit} className="flex flex-col gap-4">
      <TextField label="Name" required minLength={2} value={v.name} onChange={set('name')} />
      <TextArea label="Description" hint="Shown on the destination card" rows={2} value={v.description} onChange={set('description')} />
      <TextField label="Photo URL" type="url" value={v.image_url} onChange={set('image_url')} />
      <div className="grid grid-cols-2 gap-3">
        <TextField label="Latitude" inputMode="decimal" value={v.lat} onChange={set('lat')} />
        <TextField label="Longitude" inputMode="decimal" value={v.lng} onChange={set('lng')} />
      </div>
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={save.isPending} disabled={v.name.trim().length < 2}>
          Save
        </Button>
      </div>
    </form>
  )
}

function InterestForm({ interest, onDone }: { interest?: Interest; onDone: () => void }) {
  const save = useSaveInterest()
  const toast = useToast()
  const [name, setName] = useState(interest?.name ?? '')
  const [description, setDescription] = useState(interest?.description ?? '')
  const [icon, setIcon] = useState<IconName>(isIconName(interest?.icon) ? interest.icon : 'spark')
  const submit = (e: FormEvent) => {
    e.preventDefault()
    save.mutate(
      { id: interest?.id, body: { name: name.trim(), icon: icon as InterestInput['icon'], description: description.trim() || null } },
      { onSuccess: () => (toast(interest ? 'Interest saved' : 'Interest added'), onDone()), onError: (err) => toast(err.message, 'error') },
    )
  }
  return (
    <form onSubmit={submit} className="grid gap-5 sm:grid-cols-[1fr_220px]">
      <div className="flex flex-col gap-4">
        <TextField label="Name" required minLength={2} maxLength={60} value={name} onChange={(e) => setName(e.target.value)} />
        <TextField label="Description" maxLength={160} placeholder="Temples, tombs and the pyramids" hint="One short line under the name" value={description} onChange={(e) => setDescription(e.target.value)} />
        <fieldset>
          <legend className="mb-2 text-[15px] font-semibold text-ink-2">Icon</legend>
          <div role="radiogroup" className="grid grid-cols-7 gap-2 sm:grid-cols-10">
            {INTEREST_ICONS.map((n) => (
              <button
                key={n}
                type="button"
                role="radio"
                aria-checked={icon === n}
                aria-label={n}
                onClick={() => setIcon(n)}
                className={`grid aspect-square place-items-center rounded-xl border-[1.5px] ${icon === n ? 'border-terracotta bg-terracotta text-white' : 'border-line bg-raised text-terracotta hover:border-line-strong'}`}
              >
                <Icon name={n} size={18} />
              </button>
            ))}
          </div>
        </fieldset>
      </div>
      <div>
        <p className="mb-2 text-[15px] font-semibold text-ink-2">Preview</p>
        <div className="rounded-[18px] border-[1.5px] border-line bg-card p-[22px]">
          <span className="grid size-12 place-items-center rounded-[14px] bg-muted text-terracotta">
            <Icon name={icon} size={24} />
          </span>
          <p className="mt-[18px] text-lg leading-snug font-bold">{name || 'Interest name'}</p>
          <p className="mt-2.5 text-sm text-ink-3">{description || 'Short description'}</p>
        </div>
      </div>
      <div className="flex justify-end gap-3 sm:col-span-2">
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={save.isPending} disabled={name.trim().length < 2}>
          Save
        </Button>
      </div>
    </form>
  )
}
