/** Every icon in src/assets/icons (exported unchanged from the Figma file). */
export const ICON_NAMES = [
  'alert',
  'arrowL',
  'arrowR',
  'bed',
  'bookmark',
  'briefcase',
  'bus',
  'cal',
  'camera',
  'chart',
  'chat',
  'check',
  'chev',
  'clock',
  'code',
  'download',
  'edit',
  'eye',
  'file',
  'filter',
  'flip',
  'food',
  'history',
  'image',
  'leaf',
  'link',
  'list',
  'mic',
  'minus',
  'moon',
  'more',
  'mountain',
  'music',
  'pin',
  'plus',
  'search',
  'send',
  'share',
  'shield',
  'sliders',
  'spark',
  'star',
  'train',
  'trendDown',
  'upload',
  'user',
  'waves',
  'x',
  'zap',
] as const

export type IconName = (typeof ICON_NAMES)[number]

export function isIconName(value: string | null | undefined): value is IconName {
  return !!value && (ICON_NAMES as readonly string[]).includes(value)
}

/** The icons an admin can give an interest (same list as the backend's INTEREST_ICONS). */
export const INTEREST_ICONS: IconName[] = [
  'history', 'image', 'food', 'leaf', 'waves', 'briefcase', 'moon', 'pin', 'camera', 'mountain',
  'music', 'spark', 'star', 'zap', 'train', 'bus', 'bed', 'shield', 'user', 'chat',
]
