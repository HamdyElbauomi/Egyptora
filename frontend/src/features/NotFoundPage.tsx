import { ButtonLink } from '@/components/ui/Button'
import { ErrorState } from '@/components/ui/ErrorState'
import { Logo } from '@/components/ui/Logo'

export function NotFoundPage() {
  return (
    <div className="min-h-dvh px-4 py-6 sm:px-10">
      <Logo size="md" />
      <ErrorState title="Page not found" action={<ButtonLink to="/">Go home</ButtonLink>}>
        The link may be old or mistyped.
      </ErrorState>
    </div>
  )
}
