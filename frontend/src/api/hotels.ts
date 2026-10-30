import { useMutation, useQuery } from '@tanstack/react-query'
import { api, unwrap, type Schemas } from './client'

export type HotelSearchResult = Schemas['HotelSearchOut']
export type CompanyPublic = Schemas['CompanyPublicOut']
export type Review = Schemas['ReviewOut']

export interface HotelFilters {
  city_id?: number
  stars?: number
  max_price?: number
  sort: 'price' | 'stars' | 'name'
}

export function useHotelSearch() {
  return useMutation({
    mutationFn: async (body: Schemas['HotelSearchIn']) => unwrap(await api.POST('/api/v1/hotels/search', { body })),
  })
}

export function useFilteredHotels(filters: HotelFilters, enabled: boolean) {
  return useQuery({
    queryKey: ['hotels', filters],
    queryFn: async () => unwrap(await api.GET('/api/v1/hotels', { params: { query: { ...filters, limit: 50 } } })),
    enabled,
  })
}

export function useCompany(companyId: number) {
  return useQuery({
    queryKey: ['company', companyId],
    queryFn: async () => unwrap(await api.GET('/api/v1/companies/{company_id}', { params: { path: { company_id: companyId } } })),
    enabled: Number.isFinite(companyId),
  })
}

export function useCompanyReviews(companyId: number, page: number) {
  return useQuery({
    queryKey: ['company-reviews', companyId, page],
    queryFn: async () =>
      unwrap(
        await api.GET('/api/v1/companies/{company_id}/reviews', {
          params: { path: { company_id: companyId }, query: { page, limit: 10 } },
        }),
      ),
    enabled: Number.isFinite(companyId),
  })
}

export function useAddReview(companyId: number) {
  return useMutation({
    mutationFn: async (body: Schemas['ReviewIn']) =>
      unwrap(await api.POST('/api/v1/companies/{company_id}/reviews', { params: { path: { company_id: companyId } }, body })),
  })
}
