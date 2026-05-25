import { FileSpreadsheet, FileDown } from 'lucide-react'
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
          <FileSpreadsheet size={14} />
          Excel
        </Button>
      )}
      {onCsv && (
        <Button size="sm" variant="ghost" onClick={onCsv} disabled={disabled}>
          <FileDown size={14} />
          CSV
        </Button>
      )}
    </div>
  )
}
