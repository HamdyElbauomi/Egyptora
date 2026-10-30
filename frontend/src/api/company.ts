import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, asForm, formData, unwrap, type Schemas } from './client'

export type Company = Schemas['CompanyOut']
export type Dashboard = Schemas['DashboardOut']
export type MyOffer = Schemas['MyOfferOut']
export type OfferInput = Schemas['OfferIn']
export type OfferPatch = Schemas['OfferUpdateIn']
export type Market = Schemas['MarketOut']
export type Alert = Schemas['AlertOut']
export type Insights = Schemas['ReviewInsightsOut']

export interface CompanySignUp {
  owner_name: string
  email: string
  password: string
  company_name: string
  license_no: string
  phone?: string
  website?: string
  license_file: File
}

export async function registerCompany(body: CompanySignUp) {
  return unwrap(
    await api.POST('/api/v1/company/register', {
      body: formData({ ...body }) as never,
      ...asForm,
    }),
  )
}

export function useMyCompany(enabled = true) {
  return useQuery({
    queryKey: ['company-me'],
    queryFn: async () => unwrap(await api.GET('/api/v1/company/me')),
    enabled,
    // while the application is reviewed, check now and then so approval shows up without a reload
    refetchInterval: (query) => (query.state.data?.status === 'pending' ? 60_000 : false),
  })
}

export function useUpdateCompany() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: Schemas['CompanyUpdateIn']) => unwrap(await api.PATCH('/api/v1/company/me', { body })),
    onSuccess: (company) => queryClient.setQueryData(['company-me'], company),
  })
}

export function useUploadLicense() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) =>
      unwrap(await api.POST('/api/v1/company/me/documents', { body: formData({ file }) as never, ...asForm })),
    onSuccess: (company) => queryClient.setQueryData(['company-me'], company),
  })
}

export function useDashboard() {
  return useQuery({ queryKey: ['company-dashboard'], queryFn: async () => unwrap(await api.GET('/api/v1/company/dashboard')) })
}

export function useMyOffers() {
  return useQuery({ queryKey: ['company-offers'], queryFn: async () => unwrap(await api.GET('/api/v1/company/offers')) })
}

/** After any offer change, the list, the dashboard numbers and the alerts can all move. */
function useOfferChange<V, R>(call: (vars: V) => Promise<R>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: call,
    onSuccess: () => {
      for (const key of ['company-offers', 'company-dashboard', 'company-alerts', 'offer-market', 'hotel-offers'])
        void queryClient.invalidateQueries({ queryKey: [key] })
    },
  })
}

export function useCreateOffer() {
  return useOfferChange(async (body: OfferInput) => unwrap(await api.POST('/api/v1/company/offers', { body })))
}

export function useUpdateOffer() {
  return useOfferChange(async ({ id, body }: { id: number; body: OfferPatch }) =>
    unwrap(await api.PATCH('/api/v1/company/offers/{offer_id}', { params: { path: { offer_id: id } }, body })),
  )
}

export function usePauseOffer() {
  return useOfferChange(async ({ id, pause }: { id: number; pause: boolean }) => {
    const params = { params: { path: { offer_id: id } } }
    return unwrap(
      pause
        ? await api.POST('/api/v1/company/offers/{offer_id}/pause', params)
        : await api.POST('/api/v1/company/offers/{offer_id}/resume', params),
    )
  })
}

export function useDeleteOffer() {
  return useOfferChange(async (id: number) =>
    unwrap(await api.DELETE('/api/v1/company/offers/{offer_id}', { params: { path: { offer_id: id } } })),
  )
}

export function useImportOffers() {
  return useOfferChange(async (file: File) =>
    unwrap(await api.POST('/api/v1/company/offers/import', { body: formData({ file }) as never, ...asForm })),
  )
}

export function useOfferMarket(offerId: number | undefined) {
  return useQuery({
    queryKey: ['offer-market', offerId],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/company/offers/{offer_id}/market', { params: { path: { offer_id: offerId! } } })),
    enabled: offerId !== undefined,
  })
}

export function useCatalogHotels(search: string) {
  return useQuery({
    queryKey: ['catalog-hotels', search],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/company/hotels', { params: { query: { search: search || undefined, limit: 20 } } })),
  })
}

export function useAlerts() {
  return useQuery({ queryKey: ['company-alerts'], queryFn: async () => unwrap(await api.GET('/api/v1/company/alerts')) })
}

export function useReadAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) =>
      unwrap(await api.POST('/api/v1/company/alerts/{alert_id}/read', { params: { path: { alert_id: id } } })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['company-alerts'] })
      void queryClient.invalidateQueries({ queryKey: ['company-dashboard'] })
    },
  })
}

export function useMyReviews(page: number) {
  return useQuery({
    queryKey: ['company-my-reviews', page],
    queryFn: async () => unwrap(await api.GET('/api/v1/company/reviews', { params: { query: { page, limit: 10 } } })),
  })
}

export function useInsights() {
  return useQuery({ queryKey: ['company-insights'], queryFn: async () => unwrap(await api.GET('/api/v1/company/reviews/insights')) })
}
