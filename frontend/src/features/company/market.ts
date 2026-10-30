export interface MarketView {
  others: number
  lowest: number | null
  average: number | null
  /** 1 = cheapest; ties count as cheapest, like the backend */
  position: number
  total: number
}

/** Where a price would rank against the other companies' live prices for the same hotel and room. */
export function marketFor(myPrice: number, otherPrices: number[]): MarketView {
  const others = otherPrices.length
  const lowest = others ? Math.min(...otherPrices) : null
  const average = others ? Math.round(otherPrices.reduce((a, b) => a + b, 0) / others) : null
  const position = 1 + otherPrices.filter((p) => p < myPrice).length
  return { others, lowest, average, position, total: others + 1 }
}
