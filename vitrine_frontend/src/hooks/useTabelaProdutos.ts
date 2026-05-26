import { useState, useEffect, useRef, useCallback } from 'react'
import { fetchTabelaProdutos } from '../api/bi'
import type { ProdutoTabelaResponse, SortByProduto } from '../types'

export function useTabelaProdutos() {
  const [items, setItems] = useState<ProdutoTabelaResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [grupo, setGrupo] = useState('')
  const [familia, setFamilia] = useState('')

  const [sortBy, setSortBy] = useState<SortByProduto>('nome')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')

  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(50)

  const [filtrosDisponiveis, setFiltros] = useState<{ grupos: string[]; familias: string[] }>({
    grupos: [],
    familias: [],
  })

  const searchTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const fetchData = useCallback(async () => {
    setLoading(true)
    setErro(null)
    try {
      const data = await fetchTabelaProdutos({
        grupo: grupo || undefined,
        familia: familia || undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: pageSize,
        offset: page * pageSize,
      })
      if (!mountedRef.current) return
      setItems(data.items)
      setTotal(data.total)
      if (data.filtros_disponiveis) {
        setFiltros(data.filtros_disponiveis)
      }
    } catch (err) {
      if (!mountedRef.current) return
      setErro('Erro ao carregar tabela de preços.')
      console.error('Erro fetchTabelaProdutos:', err)
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [grupo, familia, search, sortBy, sortOrder, page, pageSize])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: data fetching on dependency change (setState calls are async after await)
    fetchData()
  }, [fetchData])

  const setSearchDebounced = useCallback((value: string) => {
    if (searchTimer.current) clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setSearch(value)
      setPage(0)
    }, 300)
  }, [])

  const totalPages = Math.ceil(total / pageSize)

  return {
    items, total, loading, erro,
    search, setSearch: setSearchDebounced,
    grupo, setGrupo, familia, setFamilia,
    sortBy, setSortBy, sortOrder, setSortOrder,
    page, setPage, pageSize, setPageSize,
    filtrosDisponiveis, totalPages, fetchData,
  }
}
