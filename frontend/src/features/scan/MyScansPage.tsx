import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMyScans } from '@/api/scans'
import { Button, ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Icon } from '@/components/ui/Icon'
import { PageLoader } from '@/components/ui/Spinner'
import { formatDate } from '@/lib/format'

export function MyScansPage() {
  const [page, setPage] = useState(1)
  const scans = useMyScans(page)

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-[34px] leading-tight sm:text-[44px]">My scans</h1>
          <p className="mt-2 text-[17px] text-ink-2">Every monument you’ve photographed. Only you can see these.</p>
        </div>
        <ButtonLink to="/scan" leadingIcon="camera">
          Scan a monument
        </ButtonLink>
      </div>
      <div className="mt-8">
        {scans.isPending ? (
          <PageLoader />
        ) : scans.isError ? (
          <ErrorState title="We couldn’t load your scans" action={<Button onClick={() => scans.refetch()}>Try again</Button>} />
        ) : scans.data.total === 0 ? (
          <div className="flex flex-col items-center rounded-[22px] border border-dashed border-line-strong bg-raised px-6 py-16 text-center">
            <span className="grid size-14 place-items-center rounded-2xl bg-terracotta-soft text-terracotta">
              <Icon name="camera" size={26} />
            </span>
            <h2 className="mt-5 font-display text-[28px]">No scans yet</h2>
            <p className="mt-2 max-w-sm text-[15px] text-ink-2">Point your camera at a monument to hear its story.</p>
            <ButtonLink to="/scan" className="mt-6" icon="arrowR">
              Scan now
            </ButtonLink>
          </div>
        ) : (
          <>
            <ul className="grid grid-cols-2 gap-4 sm:grid-cols-[repeat(auto-fill,minmax(220px,1fr))]">
              {scans.data.data.map((s) => {
                const card = (
                  <>
                    <img src={s.image_url} alt="" className="aspect-[4/3] w-full rounded-t-[18px] bg-placeholder object-cover" />
                    <div className="p-3.5">
                      <p className="font-bold">{s.place_name ?? 'Not recognized'}</p>
                      <p className="mt-0.5 text-[13px] text-ink-3">
                        {[s.city_name, formatDate(s.created_at.slice(0, 10), true)].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                  </>
                )
                return (
                  <li key={s.id} className="overflow-hidden rounded-[18px] border border-line bg-card">
                    {s.place_id ? (
                      <Link to={`/places/${s.place_id}`} className="block hover:bg-raised">
                        {card}
                      </Link>
                    ) : (
                      <div className="opacity-80">{card}</div>
                    )}
                  </li>
                )
              })}
            </ul>
            {scans.data.total > scans.data.limit && (
              <div className="mt-6 flex justify-center gap-3">
                <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                  Newer
                </Button>
                <Button variant="outline" size="sm" disabled={page * scans.data.limit >= scans.data.total} onClick={() => setPage((p) => p + 1)}>
                  Older
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}
