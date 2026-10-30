import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, asForm, formData, unwrap, type Schemas } from './client'

export type ScanResult = Schemas['ScanOut']
export type PlaceDetail = Schemas['PlaceDetailOut']
export type ScanItem = Schemas['ScanListItem']
export type Answer = Schemas['AnswerOut']

export function useScan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (photo: Blob) =>
      unwrap(await api.POST('/api/v1/scans', { body: formData({ photo }) as never, ...asForm })),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['scans'] }),
  })
}

export function useMyScans(page: number) {
  return useQuery({
    queryKey: ['scans', page],
    queryFn: async () => unwrap(await api.GET('/api/v1/scans', { params: { query: { page, limit: 24 } } })),
  })
}

export function usePlace(placeId: number | undefined) {
  return useQuery({
    queryKey: ['place', placeId],
    queryFn: async () => unwrap(await api.GET('/api/v1/places/{place_id}', { params: { path: { place_id: placeId! } } })),
    enabled: placeId !== undefined && Number.isFinite(placeId),
  })
}

export function useAskPlace(placeId: number) {
  return useMutation({
    mutationFn: async (question: string) =>
      unwrap(await api.POST('/api/v1/places/{place_id}/ask', { params: { path: { place_id: placeId } }, body: { question } })),
  })
}
