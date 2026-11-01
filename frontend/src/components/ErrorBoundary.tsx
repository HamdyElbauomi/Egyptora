import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Logo } from './ui/Logo'

interface State {
  error: Error | null
}

/** Last line of defence: a friendly page instead of a blank screen when a screen crashes. */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Screen crashed', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="min-h-dvh px-4 py-6 sm:px-10">
        <Logo size="md" />
        <div role="alert" className="mx-auto mt-24 max-w-md text-center">
          <h1 className="font-display text-[30px]">Something went wrong on this screen</h1>
          <p className="mt-3 text-[15px] text-ink-2">Your trips are safe. Reload the page, or go back to the start.</p>
          <div className="mt-6 flex justify-center gap-3">
            <button type="button" onClick={() => location.reload()} className="rounded-xl bg-terracotta px-5 py-3 font-bold text-white">
              Reload
            </button>
            <a href="/" className="rounded-xl border-[1.5px] border-line-strong px-5 py-3 font-bold">
              Go home
            </a>
          </div>
        </div>
      </div>
    )
  }
}
