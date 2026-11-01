export const card = 'rounded-[20px] border border-line bg-card'

/** Clickable list row with a selected state, for master–detail screens. */
export function rowClass(selected: boolean): string {
  return `w-full border-t border-line px-4 py-3.5 text-left first:border-t-0 ${selected ? 'bg-selected' : 'hover:bg-raised'}`
}
