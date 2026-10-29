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
