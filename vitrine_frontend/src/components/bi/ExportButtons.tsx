import { FileSpreadsheet, FileDown, FileText } from 'lucide-react'
import Button from '../ui/Button'

interface Props {
  onExcel?: () => void
  onCsv?: () => void
  onPdf?: () => void
  disabled?: boolean
}

export default function ExportButtons({ onExcel, onCsv, onPdf, disabled }: Props) {
  return (
    <div className="flex gap-2">
      {onExcel && (
        <Button size="sm" variant="secondary" onClick={onExcel} disabled={disabled}>
          <FileSpreadsheet size={14} />
          Excel
        </Button>
      )}
      {onPdf && (
        <Button size="sm" variant="secondary" onClick={onPdf} disabled={disabled}>
          <FileText size={14} />
          PDF
        </Button>
      )}
      {onCsv && (
        <Button size="sm" variant="secondary" onClick={onCsv} disabled={disabled}>
          <FileDown size={14} />
          CSV
        </Button>
      )}
    </div>
  )
}
