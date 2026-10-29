import type { IconName } from '@/components/ui/Icon'

/** How each backend interest looks on its card. Keyed by the interest's `icon` field. */
const META: Record<string, { icon: IconName; description: string }> = {
  pyramid: { icon: 'history', description: 'Temples, tombs and the pyramids' },
  museum: { icon: 'image', description: 'Treasures, mummies and old masters' },
  utensils: { icon: 'food', description: 'Street food, cooking and bazaars' },
  waves: { icon: 'leaf', description: 'Felucca rides, gardens and islands' },
  'shopping-bag': { icon: 'briefcase', description: 'Souks, crafts and spices' },
  moon: { icon: 'moon', description: 'Rooftops and evening Nile cruises' },
  landmark: { icon: 'pin', description: 'Mosques, churches and old quarters' },
  camera: { icon: 'camera', description: 'Viewpoints and golden hours' },
  umbrella: { icon: 'waves', description: 'Red Sea and Mediterranean coast' },
}

export function interestMeta(icon: string | null | undefined): { icon: IconName; description: string } {
  return (icon && META[icon]) || { icon: 'spark', description: 'Something we’ll fit into your days' }
}
