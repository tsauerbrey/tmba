export const Sources = Object.freeze({
  AIRPLAY: 'airplay',
  WEBRADIO: 'webradio',
  BLUETOOTH: 'bluetooth',
  USB: 'usb',
})

export const SourceList = Object.freeze([
  {
    id: Sources.AIRPLAY,
    label: 'AirPlay',
    icon: '',
    accent: '#168cff',
    position: 'left',
  },
  {
    id: Sources.WEBRADIO,
    label: 'Webradio',
    icon: '◎',
    accent: '#80c43b',
    position: 'left',
  },
  {
    id: Sources.BLUETOOTH,
    label: 'Bluetooth',
    icon: '∞',
    accent: '#168cff',
    position: 'right',
  },
  {
    id: Sources.USB,
    label: 'USB/NAS',
    icon: '▣',
    accent: '#ffc21a',
    position: 'right',
  },
])

export function isValidSource(source) {
  return Object.values(Sources).includes(source)
}