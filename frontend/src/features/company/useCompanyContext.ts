import { useOutletContext } from 'react-router-dom'
import type { Company } from '@/api/company'

export function useCurrentCompany(): Company {
  return useOutletContext<Company>()
}
