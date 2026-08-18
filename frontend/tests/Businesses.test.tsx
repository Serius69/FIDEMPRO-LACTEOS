import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import Businesses from '@/pages/Businesses'
import { getOwnedBusinesses, createBusiness } from '@/lib/api'

// Businesses.tsx es la pantalla de selección/creación de negocio: cada
// negocio tiene sus propios datos y modelos, así que mostrar la empresa
// equivocada (de otro usuario) o esconder un fallo de carga detrás de una
// lista vacía serían fallas de "propiedad de datos", no solo estéticas.

vi.mock('@/lib/api', () => ({
  getOwnedBusinesses: vi.fn(),
  createBusiness: vi.fn(),
}))

const mockedGetOwnedBusinesses = vi.mocked(getOwnedBusinesses)
const mockedCreateBusiness = vi.mocked(createBusiness)

beforeEach(() => {
  mockedGetOwnedBusinesses.mockReset()
  mockedCreateBusiness.mockReset()
})

describe('Businesses — carga', () => {
  it('shows a loading indicator while the request is in flight, distinct from the empty-state message', async () => {
    let resolveFn: (v: { businesses: { id: number; name: string; sector: string }[] }) => void = () => {}
    mockedGetOwnedBusinesses.mockReturnValue(new Promise((resolve) => { resolveFn = resolve }))

    render(<Businesses />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByText('Crea tu primera empresa para comenzar.')).not.toBeInTheDocument()

    resolveFn({ businesses: [] })
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument())
    expect(screen.getByText('Crea tu primera empresa para comenzar.')).toBeInTheDocument()
  })

  it('renders only the businesses returned by the API — the real owned list, not fabricated placeholders', async () => {
    mockedGetOwnedBusinesses.mockResolvedValue({
      businesses: [
        { id: 1, name: 'Panadería Doña Carmen', sector: 'bakery' },
        { id: 2, name: 'Ferretería El Tornillo', sector: 'retail' },
      ],
    })

    render(<Businesses />)

    await waitFor(() => expect(screen.getByText('Panadería Doña Carmen')).toBeInTheDocument())
    expect(screen.getByText('Ferretería El Tornillo')).toBeInTheDocument()
    expect(screen.getByText('2 activa(s)')).toBeInTheDocument()
  })

  it('shows an explicit error and an EMPTY list on API failure — it must not leak a stale or fabricated business list', async () => {
    mockedGetOwnedBusinesses.mockRejectedValue(new Error('No autorizado para ver estas empresas.'))

    render(<Businesses />)

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('No autorizado para ver estas empresas.'))
    // Sin negocios reales cargados: la única tarjeta con encabezado (h3) es la
    // del formulario "Crear empresa" — ninguna tarjeta de negocio inventada.
    expect(screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent?.trim())).toEqual(['Crear empresa'])
    expect(screen.getByText('Crea tu primera empresa para comenzar.')).toBeInTheDocument()
  })
})

describe('Businesses — crear empresa', () => {
  it('adds the newly created business (as returned by the API) to the list without requiring a reload', async () => {
    mockedGetOwnedBusinesses.mockResolvedValue({ businesses: [] })
    mockedCreateBusiness.mockResolvedValue({ business: { id: 9, name: 'Textiles Andina', sector: 'textiles', type: 1 } })

    render(<Businesses />)
    await waitFor(() => expect(screen.getByText('Crea tu primera empresa para comenzar.')).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText('Ej. Panadería Central'), { target: { value: 'Textiles Andina' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear' }))

    await waitFor(() => expect(screen.getByText('Textiles Andina')).toBeInTheDocument())
    expect(mockedCreateBusiness).toHaveBeenCalledWith(expect.objectContaining({ name: 'Textiles Andina' }))
  })

  it('shows the real error message and does not add a business when creation fails', async () => {
    mockedGetOwnedBusinesses.mockResolvedValue({ businesses: [] })
    mockedCreateBusiness.mockRejectedValue(new Error('El nombre ya está en uso.'))

    render(<Businesses />)
    await waitFor(() => expect(screen.getByText('Crea tu primera empresa para comenzar.')).toBeInTheDocument())

    fireEvent.change(screen.getByPlaceholderText('Ej. Panadería Central'), { target: { value: 'Duplicada' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear' }))

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('El nombre ya está en uso.'))
    expect(screen.queryByText('Duplicada')).not.toBeInTheDocument()
    expect(screen.getByText('Crea tu primera empresa para comenzar.')).toBeInTheDocument()
  })
})
