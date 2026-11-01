import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, asForm, formData, unwrap, type Schemas } from './client'

export type Stats = Schemas['StatsOut']
export type AdminCompany = Schemas['CompanyAdminOut']
export type Checklist = Schemas['ApproveChecklistIn']
export type AdminOffer = Schemas['AdminOfferOut']
export type AdminPlace = Schemas['PlaceOut']
export type PlaceInput = Schemas['PlaceIn']
export type HotelInput = Schemas['HotelIn']
export type CityInput = Schemas['CityIn']
export type InterestInput = Schemas['InterestIn']
export type NLQuery = Schemas['NLQueryOut']
export type AdminScan = Schemas['AdminScanOut']
export type Metrics = Schemas['MetricsOut']

/** Run a mutation, then refresh every query whose first key is listed. */
function useAdminMutation<V, R>(call: (vars: V) => Promise<R>, refresh: string[]) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: call,
    onSuccess: () => {
      for (const key of [...refresh, 'admin-stats']) void queryClient.invalidateQueries({ queryKey: [key] })
    },
  })
}

export const useStats = () =>
  useQuery({ queryKey: ['admin-stats'], queryFn: async () => unwrap(await api.GET('/api/v1/admin/stats')) })

/* ---------------------------------------------------------------- companies */

export function useAdminCompanies(status: string) {
  return useQuery({
    queryKey: ['admin-companies', status],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/admin/companies', { params: { query: { status: status as never, limit: 100 } } })),
  })
}

export function useApproveCompany() {
  return useAdminMutation(
    async ({ id, body }: { id: number; body: Checklist }) =>
      unwrap(await api.POST('/api/v1/admin/companies/{company_id}/approve', { params: { path: { company_id: id } }, body })),
    ['admin-companies'],
  )
}

export function useRejectCompany() {
  return useAdminMutation(
    async ({ id, reason }: { id: number; reason: string }) =>
      unwrap(
        await api.POST('/api/v1/admin/companies/{company_id}/reject', { params: { path: { company_id: id } }, body: { reason } }),
      ),
    ['admin-companies'],
  )
}

export function useSuspendCompany() {
  return useAdminMutation(
    async (id: number) =>
      unwrap(await api.POST('/api/v1/admin/companies/{company_id}/suspend', { params: { path: { company_id: id } } })),
    ['admin-companies', 'admin-offers'],
  )
}

export function useAnalyzeReviews() {
  return useMutation({
    mutationFn: async ({ id, reviews }: { id: number; reviews: string[] }) =>
      unwrap(
        await api.POST('/api/v1/admin/companies/{company_id}/analyze-reviews', {
          params: { path: { company_id: id } },
          body: { reviews },
        }),
      ),
  })
}

/* ---------------------------------------------------------------- catalog */

export function useAdminHotels(search: string, cityId?: number) {
  return useQuery({
    queryKey: ['admin-hotels', search, cityId],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/admin/hotels', { params: { query: { search: search || undefined, city_id: cityId, limit: 100 } } }),
      ),
  })
}

export function useSaveHotel() {
  return useAdminMutation(
    async ({ id, body }: { id?: number; body: HotelInput }) =>
      id
        ? unwrap(await api.PATCH('/api/v1/admin/hotels/{hotel_id}', { params: { path: { hotel_id: id } }, body }))
        : unwrap(await api.POST('/api/v1/admin/hotels', { body })),
    ['admin-hotels', 'hotels'],
  )
}

export function useDeleteHotel() {
  return useAdminMutation(
    async (id: number) => unwrap(await api.DELETE('/api/v1/admin/hotels/{hotel_id}', { params: { path: { hotel_id: id } } })),
    ['admin-hotels'],
  )
}

export function useImportHotels() {
  return useAdminMutation(
    async (file: File) => unwrap(await api.POST('/api/v1/admin/hotels/import', { body: formData({ file }) as never, ...asForm })),
    ['admin-hotels'],
  )
}

export function useAdminOffers(filter: { status?: string; hotel_id?: number }, enabled = true) {
  return useQuery({
    queryKey: ['admin-offers', filter],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/admin/offers', { params: { query: { ...filter, status: filter.status as never, limit: 100 } } })),
    enabled,
  })
}

export function useFlagOffer() {
  return useAdminMutation(
    async ({ id, reason }: { id: number; reason: string | null }) =>
      reason === null
        ? unwrap(await api.POST('/api/v1/admin/offers/{offer_id}/unflag', { params: { path: { offer_id: id } } }))
        : unwrap(await api.POST('/api/v1/admin/offers/{offer_id}/flag', { params: { path: { offer_id: id } }, body: { reason } })),
    ['admin-offers', 'admin-hotels'],
  )
}

export function useSaveCity() {
  return useAdminMutation(
    async ({ id, body }: { id?: number; body: CityInput }) =>
      id
        ? unwrap(await api.PATCH('/api/v1/admin/cities/{city_id}', { params: { path: { city_id: id } }, body }))
        : unwrap(await api.POST('/api/v1/admin/cities', { body })),
    ['cities'],
  )
}

export function useSaveInterest() {
  return useAdminMutation(
    async ({ id, body }: { id?: number; body: InterestInput }) =>
      id
        ? unwrap(await api.PATCH('/api/v1/admin/interests/{interest_id}', { params: { path: { interest_id: id } }, body }))
        : unwrap(await api.POST('/api/v1/admin/interests', { body })),
    ['interests'],
  )
}

export function useAdminPlaces(filter: { search: string; city_id?: number; type?: string }) {
  return useQuery({
    queryKey: ['admin-places', filter],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/admin/places', {
          params: { query: { search: filter.search || undefined, city_id: filter.city_id, type: filter.type || undefined, limit: 100 } },
        }),
      ),
  })
}

export function useSavePlace() {
  return useAdminMutation(
    async ({ id, body }: { id?: number; body: PlaceInput }) =>
      id
        ? unwrap(await api.PATCH('/api/v1/admin/places/{place_id}', { params: { path: { place_id: id } }, body }))
        : unwrap(await api.POST('/api/v1/admin/places', { body })),
    ['admin-places', 'place', 'city-places', 'cities'],
  )
}

export function useDeletePlace() {
  return useAdminMutation(
    async (id: number) => unwrap(await api.DELETE('/api/v1/admin/places/{place_id}', { params: { path: { place_id: id } } })),
    ['admin-places', 'cities'],
  )
}

export function useUploadPlaceImages() {
  return useAdminMutation(
    async ({ id, files }: { id: number; files: File[] }) => {
      const form = new FormData()
      for (const f of files) form.append('files', f)
      return unwrap(await api.POST('/api/v1/admin/places/{place_id}/images', { params: { path: { place_id: id } }, body: form as never, ...asForm }))
    },
    ['place'],
  )
}

export function useDeletePlaceImage() {
  return useAdminMutation(
    async (id: number) =>
      unwrap(await api.DELETE('/api/v1/admin/place-images/{image_id}', { params: { path: { image_id: id } } })),
    ['place'],
  )
}

/* ---------------------------------------------------------------- AI quality */

export const useMetrics = () =>
  useQuery({ queryKey: ['admin-metrics'], queryFn: async () => unwrap(await api.GET('/api/v1/admin/ai/metrics')) })

export function useQueries(status: 'failed' | 'flagged' | 'ok' | 'all') {
  return useQuery({
    queryKey: ['admin-queries', status],
    queryFn: async () => unwrap(await api.GET('/api/v1/admin/ai/queries', { params: { query: { status, limit: 100 } } })),
  })
}

export function useFixQuery() {
  return useAdminMutation(
    async ({ id, sql }: { id: number; sql: string }) =>
      unwrap(await api.POST('/api/v1/admin/ai/queries/{query_id}/fix', { params: { path: { query_id: id } }, body: { sql } })),
    ['admin-queries', 'admin-metrics'],
  )
}

export function useAddToTraining() {
  return useAdminMutation(
    async (id: number) =>
      unwrap(await api.POST('/api/v1/admin/ai/queries/{query_id}/add-to-training', { params: { path: { query_id: id } } })),
    ['admin-queries', 'admin-training', 'admin-metrics'],
  )
}

export const useTrainingExamples = () =>
  useQuery({ queryKey: ['admin-training'], queryFn: async () => unwrap(await api.GET('/api/v1/admin/ai/training-examples')) })

export function useDeleteExample() {
  return useAdminMutation(
    async (id: number) =>
      unwrap(await api.DELETE('/api/v1/admin/ai/training-examples/{example_id}', { params: { path: { example_id: id } } })),
    ['admin-training', 'admin-metrics'],
  )
}

export function useScanQueue(onlyUnlabeled: boolean) {
  return useQuery({
    queryKey: ['admin-scans', onlyUnlabeled],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/admin/ai/scans', { params: { query: { only_unlabeled: onlyUnlabeled, limit: 60 } } })),
  })
}

export function useLabelScan() {
  return useAdminMutation(
    async ({ id, placeId, train }: { id: number; placeId: number; train: boolean }) =>
      unwrap(
        await api.POST('/api/v1/admin/ai/scans/{scan_id}/label', {
          params: { path: { scan_id: id } },
          body: { place_id: placeId, add_to_training: train },
        }),
      ),
    ['admin-scans', 'admin-metrics'],
  )
}
