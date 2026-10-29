import { useMatch } from 'react-router-dom'
import { AppShell, type NavItem } from './AppShell'

/** Inside a trip the bar shows that trip's screens; elsewhere it shows the traveler's home links. */
export function TravelerShell() {
  const match = useMatch('/trips/:tripId/*')
  const tripId = match?.params.tripId
  const nav: NavItem[] = tripId
    ? [
        { to: `/trips/${tripId}`, label: 'My trip', end: true },
        { to: `/trips/${tripId}/chat`, label: 'Chat' },
        { to: `/trips/${tripId}/summary`, label: 'Summary' },
      ]
    : [
        { to: '/trips', label: 'My trips', end: true },
        { to: '/plan/interests', label: 'Plan a trip' },
      ]
  return <AppShell nav={nav} home="/trips" />
}
