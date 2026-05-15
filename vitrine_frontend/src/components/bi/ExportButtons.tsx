interface Props {
  onExcel?: () => void
  onCsv?: () => void
  disabled?: boolean
}

export default function ExportButtons({ onExcel, onCsv, disabled }: Props) {
  return (
    <div className="flex gap-2">
      {onExcel && (
        <button
          onClick={onExcel}
          disabled={disabled}
          className="text-xs bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
        >
          Excel
        </button>
      )}
      {onCsv && (
        <button
          onClick={onCsv}
          disabled={disabled}
          className="text-xs bg-gray-600 hover:bg-gray-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
        >
          CSV
        </button>
      )}
    </div>
  )
}
