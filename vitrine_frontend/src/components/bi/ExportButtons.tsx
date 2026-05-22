import Button from '../ui/Button'

interface Props {
  onExcel?: () => void
  onCsv?: () => void
  disabled?: boolean
}

export default function ExportButtons({ onExcel, onCsv, disabled }: Props) {
  return (
    <div className="flex gap-2">
      {onExcel && (
        <Button size="sm" variant="secondary" onClick={onExcel} disabled={disabled}>
          Excel
        </Button>
      )}
      {onCsv && (
        <Button size="sm" variant="secondary" onClick={onCsv} disabled={disabled}>
          CSV
        </Button>
      )}
    </div>
  )
}
