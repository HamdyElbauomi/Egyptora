import type { CSSProperties } from 'react'

/* The design's icon set, exported unchanged from Figma. Each icon is painted with
   the current text colour through a CSS mask, so `text-*` classes recolour it. */
const files = import.meta.glob('../../assets/icons/*.svg', { eager: true, query: '?url', import: 'default' }) as Record<
  string,
  string
>

const urls: Record<string, string> = Object.fromEntries(
  Object.entries(files).map(([path, url]) => [path.split('/').pop()!.replace('.svg', ''), url]),
)

export type IconName =
  | 'alert' | 'arrowL' | 'arrowR' | 'bed' | 'bookmark' | 'briefcase' | 'bus' | 'cal' | 'camera' | 'chart'
  | 'chat' | 'check' | 'chev' | 'clock' | 'code' | 'download' | 'edit' | 'eye' | 'file' | 'filter' | 'flip'
  | 'food' | 'history' | 'image' | 'leaf' | 'link' | 'list' | 'mic' | 'minus' | 'moon' | 'more' | 'mountain'
  | 'music' | 'pin' | 'plus' | 'search' | 'send' | 'share' | 'shield' | 'sliders' | 'spark' | 'star' | 'train'
  | 'trendDown' | 'upload' | 'user' | 'waves' | 'x' | 'zap'

interface IconProps {
  name: IconName
  size?: number
  className?: string
  /** Text for screen readers. Leave empty for decorative icons. */
  label?: string
}

export function Icon({ name, size = 20, className = '', label }: IconProps) {
  const url = urls[name]
  const style: CSSProperties = {
    width: size,
    height: size,
    backgroundColor: 'currentColor',
    maskImage: `url("${url}")`,
    WebkitMaskImage: `url("${url}")`,
    maskSize: 'contain',
    WebkitMaskSize: 'contain',
    maskRepeat: 'no-repeat',
    WebkitMaskRepeat: 'no-repeat',
    maskPosition: 'center',
    WebkitMaskPosition: 'center',
  }
  return (
    <span
      className={`inline-block shrink-0 ${className}`}
      style={style}
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    />
  )
}
