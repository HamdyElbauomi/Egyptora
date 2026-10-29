import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, unwrap, type Schemas } from './client'

export type Interest = Schemas['InterestOut']
export type City = Schemas['CityCardOut']
export type Trip = Schemas['TripOut']
export type TripCard = Schemas['TripCardOut']
export type TripDay = Schemas['TripDayOut']
export type TripItem = Schemas['TripItemOut']
export type SharedTrip = Schemas['SharedTripOut']
export type GenerateTrip = Schemas['GenerateTripIn']

const HOUR = 60 * 60_000

export function useInterests() {
  return useQuery({
    queryKey: ['interests'],
    queryFn: async () => unwrap(await api.GET('/api/v1/interests')),
    staleTime: HOUR,
  })
}

export function useCities() {
  return useQuery({
    queryKey: ['cities'],
    queryFn: async () => unwrap(await api.GET('/api/v1/cities')),
    staleTime: HOUR,
  })
}

export function useMyTrips() {
  return useQuery({
    queryKey: ['trips'],
    queryFn: async () => unwrap(await api.GET('/api/v1/trips')),
  })
}

export function useTrip(id: number) {
  return useQuery({
    queryKey: ['trip', id],
    queryFn: async () => unwrap(await api.GET('/api/v1/trips/{trip_id}', { params: { path: { trip_id: id } } })),
    enabled: Number.isFinite(id),
  })
}

export function useSharedTrip(token: string) {
  return useQuery({
    queryKey: ['shared', token],
    queryFn: async () => unwrap(await api.GET('/api/v1/shared/{token}', { params: { path: { token } } })),
    retry: false,
  })
}

export function useGenerateTrip() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: GenerateTrip) => unwrap(await api.POST('/api/v1/trips/generate', { body })),
    onSuccess: (trip) => {
      queryClient.setQueryData(['trip', trip.id], trip)
      void queryClient.invalidateQueries({ queryKey: ['trips'] })
    },
  })
}

/* ------------------------------------------------------------------ day 2: editing a trip */

export type Place = Schemas['PlaceOut']
export type HotelCard = Schemas['HotelCardOut']
export type HotelOffer = Schemas['PublicOfferOut']
export type ChatMessage = Schemas['MessageOut']
export type TripChange = Schemas['ChangeOut']
export type Summary = Schemas['SummaryOut']
export type AddItem = Schemas['AddItemIn']
export type UpdateItem = Schemas['UpdateItemIn']
export type UpdateTrip = Schemas['UpdateTripIn']

/** Every edit returns the whole updated trip: put it in the cache and let the summary reload. */
function useTripEdit<V>(tripId: number, call: (vars: V) => Promise<Trip | undefined>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: call,
    onSuccess: (trip) => {
      if (trip) queryClient.setQueryData(['trip', tripId], trip)
      else void queryClient.invalidateQueries({ queryKey: ['trip', tripId] })
      void queryClient.invalidateQueries({ queryKey: ['summary', tripId] })
      void queryClient.invalidateQueries({ queryKey: ['trips'] })
    },
  })
}

export function useAddItem(tripId: number) {
  return useTripEdit(tripId, async ({ dayId, body }: { dayId: number; body: AddItem }) =>
    unwrap(await api.POST('/api/v1/trips/{trip_id}/days/{day_id}/items', { params: { path: { trip_id: tripId, day_id: dayId } }, body })),
  )
}

export function useUpdateItem(tripId: number) {
  return useTripEdit(tripId, async ({ itemId, body }: { itemId: number; body: UpdateItem }) =>
    unwrap(await api.PATCH('/api/v1/trip-items/{item_id}', { params: { path: { item_id: itemId } }, body })),
  )
}

export function useDeleteItem(tripId: number) {
  return useTripEdit(tripId, async (itemId: number) => {
    unwrap(await api.DELETE('/api/v1/trip-items/{item_id}', { params: { path: { item_id: itemId } } }))
    return undefined
  })
}

export function useReorderDay(tripId: number) {
  return useTripEdit(tripId, async ({ dayId, itemIds }: { dayId: number; itemIds: number[] }) =>
    unwrap(
      await api.PUT('/api/v1/trips/{trip_id}/days/{day_id}/order', {
        params: { path: { trip_id: tripId, day_id: dayId } },
        body: { item_ids: itemIds },
      }),
    ),
  )
}

export function useChooseOffer(tripId: number) {
  return useTripEdit(tripId, async ({ dayId, offerId }: { dayId: number; offerId: number | null }) =>
    unwrap(
      await api.PUT('/api/v1/trips/{trip_id}/days/{day_id}/offer', {
        params: { path: { trip_id: tripId, day_id: dayId } },
        body: { offer_id: offerId },
      }),
    ),
  )
}

export function useUpdateTrip(tripId: number) {
  return useTripEdit(tripId, async (body: UpdateTrip) =>
    unwrap(await api.PATCH('/api/v1/trips/{trip_id}', { params: { path: { trip_id: tripId } }, body })),
  )
}

export function useRegenerateTrip(tripId: number) {
  return useTripEdit(tripId, async () =>
    unwrap(await api.POST('/api/v1/trips/{trip_id}/regenerate', { params: { path: { trip_id: tripId } } })),
  )
}

export function useSaveTrip(tripId: number) {
  return useTripEdit(tripId, async () =>
    unwrap(await api.POST('/api/v1/trips/{trip_id}/save', { params: { path: { trip_id: tripId } } })),
  )
}

export function useDeleteTrip() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (tripId: number) =>
      unwrap(await api.DELETE('/api/v1/trips/{trip_id}', { params: { path: { trip_id: tripId } } })),
    onSuccess: (_, tripId) => {
      queryClient.removeQueries({ queryKey: ['trip', tripId] })
      void queryClient.invalidateQueries({ queryKey: ['trips'] })
    },
  })
}

export function useCityPlaces(cityId: number | undefined) {
  return useQuery({
    queryKey: ['city-places', cityId],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/cities/{city_id}/places', { params: { path: { city_id: cityId! } } })),
    enabled: cityId !== undefined,
    staleTime: HOUR,
  })
}

export function useCityHotels(cityId: number | undefined) {
  return useQuery({
    queryKey: ['city-hotels', cityId],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/hotels', { params: { query: { city_id: cityId, sort: 'price', limit: 50 } } })),
    enabled: cityId !== undefined,
  })
}

export function useHotelOffers(hotelId: number | undefined, sort: 'best_value' | 'lowest') {
  return useQuery({
    queryKey: ['hotel-offers', hotelId, sort],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/hotels/{hotel_id}/offers', { params: { path: { hotel_id: hotelId! }, query: { sort } } }),
      ),
    enabled: hotelId !== undefined,
  })
}

/* ------------------------------------------------------------------ chat */

export function useMessages(tripId: number) {
  return useQuery({
    queryKey: ['messages', tripId],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/trips/{trip_id}/messages', { params: { path: { trip_id: tripId } } })),
  })
}

export function useSendMessage(tripId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (content: string) =>
      unwrap(await api.POST('/api/v1/trips/{trip_id}/messages', { params: { path: { trip_id: tripId } }, body: { content } })),
    onSuccess: ({ message, reply }) => {
      queryClient.setQueryData<ChatMessage[]>(['messages', tripId], (old = []) => [...old, message, reply])
    },
  })
}

/** Keep or undo a proposed change. Both return the change with its new status and the updated trip. */
export function useDecideChange(tripId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ changeId, decision }: { changeId: number; decision: 'keep' | 'undo' }) => {
      const params = { params: { path: { change_id: changeId } } }
      return unwrap(
        decision === 'keep'
          ? await api.POST('/api/v1/trip-changes/{change_id}/keep', params)
          : await api.POST('/api/v1/trip-changes/{change_id}/undo', params),
      )
    },
    onSuccess: ({ change, trip }) => {
      queryClient.setQueryData(['trip', tripId], trip)
      queryClient.setQueryData<ChatMessage[]>(['messages', tripId], (old = []) =>
        old.map((m) => (m.change?.id === change.id ? { ...m, change } : m)),
      )
      void queryClient.invalidateQueries({ queryKey: ['summary', tripId] })
      void queryClient.invalidateQueries({ queryKey: ['trips'] })
    },
    onError: () => {
      // the change may be stale (409): reload so its status and the trip are current
      void queryClient.invalidateQueries({ queryKey: ['messages', tripId] })
      void queryClient.invalidateQueries({ queryKey: ['trip', tripId] })
    },
  })
}

/* ------------------------------------------------------------------ summary and sharing */

export function useSummary(tripId: number) {
  return useQuery({
    queryKey: ['summary', tripId],
    queryFn: async () =>
      unwrap(await api.GET('/api/v1/trips/{trip_id}/summary', { params: { path: { trip_id: tripId } } })),
  })
}

export function useShareTrip(tripId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (on: boolean) => {
      const params = { params: { path: { trip_id: tripId } } }
      if (on) return unwrap(await api.POST('/api/v1/trips/{trip_id}/share', params))
      unwrap(await api.DELETE('/api/v1/trips/{trip_id}/share', params))
      return null
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['summary', tripId] }),
  })
}
