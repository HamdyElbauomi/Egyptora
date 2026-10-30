import { useCallback, useEffect, useRef, useState } from 'react'
import { Icon } from '@/components/ui/Icon'

const ACCEPT = 'image/jpeg,image/png,image/webp'

/** Live camera when the browser allows it; otherwise (or on demand) a photo from the gallery. */
export function Camera({ onPhoto, busy, hint }: { onPhoto: (photo: Blob) => void; busy: boolean; hint: string }) {
  const video = useRef<HTMLVideoElement>(null)
  const file = useRef<HTMLInputElement>(null)
  const [facing, setFacing] = useState<'environment' | 'user'>('environment')
  const [live, setLive] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)

  useEffect(() => {
    let stream: MediaStream | null = null
    let cancelled = false
    if (!navigator.mediaDevices?.getUserMedia) return
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: facing }, audio: false })
      .then((s) => {
        if (cancelled) return s.getTracks().forEach((t) => t.stop())
        stream = s
        if (video.current) {
          video.current.srcObject = s
          void video.current.play().catch(() => undefined)
        }
        setLive(true)
      })
      .catch(() => setLive(false))
    return () => {
      cancelled = true
      stream?.getTracks().forEach((t) => t.stop())
    }
  }, [facing])

  useEffect(() => () => void (preview && URL.revokeObjectURL(preview)), [preview])

  const send = useCallback(
    (photo: Blob) => {
      setPreview(URL.createObjectURL(photo))
      onPhoto(photo)
    },
    [onPhoto],
  )

  const shoot = () => {
    const v = video.current
    if (!live || !v || !v.videoWidth) return file.current?.click()
    const canvas = document.createElement('canvas')
    canvas.width = v.videoWidth
    canvas.height = v.videoHeight
    canvas.getContext('2d')?.drawImage(v, 0, 0)
    canvas.toBlob((blob) => blob && send(blob), 'image/jpeg', 0.9)
  }

  return (
    <div className="relative flex min-h-[420px] flex-col overflow-hidden rounded-[24px] bg-inverse text-on-dark lg:min-h-[calc(100dvh-150px)]">
      <div className="relative flex-1">
        <video
          ref={video}
          playsInline
          muted
          className={`absolute inset-0 size-full object-cover ${live && !preview ? '' : 'hidden'}`}
          aria-label="Camera view"
        />
        {preview && (
          <img
            src={preview}
            alt="Your photo"
            onError={(e) => (e.currentTarget.style.visibility = 'hidden')}
            className="absolute inset-0 size-full object-cover"
          />
        )}
        {!live && !preview && (
          <div className="absolute inset-0 grid place-items-center p-8 text-center">
            <div>
              <span className="mx-auto grid size-16 place-items-center rounded-full bg-white/10">
                <Icon name="camera" size={28} />
              </span>
              <p className="mt-4 text-[15px] text-on-dark-muted">Take or choose a photo of a monument, statue or inscription.</p>
            </div>
          </div>
        )}
        {/* viewfinder corners */}
        <div aria-hidden className="pointer-events-none absolute inset-8 sm:inset-12">
          <span className="absolute top-0 left-0 size-9 border-t-[3px] border-l-[3px] border-white/90" />
          <span className="absolute top-0 right-0 size-9 border-t-[3px] border-r-[3px] border-white/90" />
          <span className="absolute bottom-0 left-0 size-9 border-b-[3px] border-l-[3px] border-white/90" />
          <span className="absolute right-0 bottom-0 size-9 border-r-[3px] border-b-[3px] border-white/90" />
        </div>
        {busy && (
          <div className="absolute inset-0 grid place-items-center bg-inverse/50">
            <p className="flex items-center gap-3 rounded-full bg-card px-5 py-3 font-semibold text-ink">
              <span className="size-4 animate-spin rounded-full border-2 border-terracotta border-r-transparent" />
              Recognizing…
            </p>
          </div>
        )}
      </div>

      <div className="bg-black/30 px-6 pt-4 pb-6 text-center">
        <p className="text-sm text-on-dark-muted">{hint}</p>
        <div className="mt-4 flex items-center justify-center gap-10">
          <button
            type="button"
            onClick={() => file.current?.click()}
            disabled={busy}
            aria-label="Choose a photo"
            className="grid size-12 place-items-center rounded-xl border border-white/20 bg-white/10 hover:bg-white/15 disabled:opacity-50"
          >
            <Icon name="image" size={22} />
          </button>
          <button
            type="button"
            onClick={preview ? () => setPreview(null) : shoot}
            disabled={busy}
            aria-label={preview ? 'Scan again' : 'Take photo'}
            className="grid size-[72px] place-items-center rounded-full border-4 border-white/90 disabled:opacity-50"
          >
            <span className="grid size-14 place-items-center rounded-full bg-gold text-ink">
              {preview && <Icon name="camera" size={22} />}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setFacing((f) => (f === 'environment' ? 'user' : 'environment'))}
            disabled={busy || !live}
            aria-label="Switch camera"
            className="grid size-12 place-items-center rounded-xl border border-white/20 bg-white/10 hover:bg-white/15 disabled:opacity-40"
          >
            <Icon name="flip" size={22} />
          </button>
        </div>
        <input
          ref={file}
          type="file"
          accept={ACCEPT}
          className="hidden"
          data-testid="photo-input"
          onChange={(e) => {
            const photo = e.target.files?.[0]
            if (photo) send(photo)
            e.target.value = ''
          }}
        />
      </div>
    </div>
  )
}
