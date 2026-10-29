import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { ApiError } from '@/api/client'
import { AuthProvider } from '@/auth/AuthProvider'
import { RequireRole } from '@/auth/RequireRole'
import { AppShell, type NavItem } from '@/components/layout/AppShell'
import { AuthPage } from '@/features/auth/AuthPage'
import { NotFoundPage } from '@/features/NotFoundPage'
import { BuildPage } from '@/features/plan/BuildPage'
import { PlanProvider } from '@/features/plan/PlanContext'
import { BudgetStep } from '@/features/plan/steps/BudgetStep'
import { DestinationsStep } from '@/features/plan/steps/DestinationsStep'
import { InterestsStep } from '@/features/plan/steps/InterestsStep'
import { LengthStep } from '@/features/plan/steps/LengthStep'
import { ComingSoon } from '@/features/portal/ComingSoon'
import { SharedTripPage } from '@/features/shared/SharedTripPage'
import { MyTripsPage } from '@/features/trips/MyTripsPage'
import { TripPage } from '@/features/trips/TripPage'
import { WelcomePage } from '@/features/welcome/WelcomePage'

const TRAVELER_NAV: NavItem[] = [
  { to: '/trips', label: 'My trips' },
  { to: '/plan/interests', label: 'Plan a trip' },
]

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // client errors (404, 403…) won't fix themselves; retry only network and server errors
      retry: (count, error) => count < 2 && !(error instanceof ApiError && error.status < 500),
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<WelcomePage />} />
            <Route path="/sign-in" element={<AuthPage mode="sign-in" />} />
            <Route path="/sign-up" element={<AuthPage mode="sign-up" />} />
            <Route path="/shared/:token" element={<SharedTripPage />} />

            {/* Planning works without an account; building the trip asks to sign in. */}
            <Route
              path="/plan"
              element={
                <PlanProvider>
                  <Outlet />
                </PlanProvider>
              }
            >
              <Route index element={<Navigate to="interests" replace />} />
              <Route path="interests" element={<InterestsStep />} />
              <Route path="budget" element={<BudgetStep />} />
              <Route path="length" element={<LengthStep />} />
              <Route path="destinations" element={<DestinationsStep />} />
              <Route path="build" element={<BuildPage />} />
            </Route>

            <Route
              element={
                <RequireRole role="traveler">
                  <AppShell nav={TRAVELER_NAV} home="/trips" />
                </RequireRole>
              }
            >
              <Route path="/trips" element={<MyTripsPage />} />
              <Route path="/trips/:tripId" element={<TripPage />} />
            </Route>

            <Route
              path="/company/*"
              element={
                <RequireRole role="company">
                  <AppShell nav={[{ to: '/company', label: 'Dashboard' }]} home="/company">
                    <ComingSoon area="Company portal" />
                  </AppShell>
                </RequireRole>
              }
            />
            <Route
              path="/admin/*"
              element={
                <RequireRole role="admin">
                  <AppShell nav={[{ to: '/admin', label: 'Overview' }]} home="/admin">
                    <ComingSoon area="Admin" />
                  </AppShell>
                </RequireRole>
              }
            />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
