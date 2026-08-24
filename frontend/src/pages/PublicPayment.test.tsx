import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { publicPaymentService } from '../services/finance';
import { PublicPaymentPage } from './PublicPayment';

vi.mock('../services/finance', () => ({ publicPaymentService: { get: vi.fn() } }));
const getPayment = vi.mocked(publicPaymentService.get);

function renderPage() {
  const query = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={query}><MemoryRouter initialEntries={['/pagar/test-token']}><Routes><Route path="/pagar/:token" element={<PublicPaymentPage/>}/></Routes></MemoryRouter></QueryClientProvider>);
}

describe('página pública de pagamento', () => {
  beforeEach(() => {
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
  });
  it('mostra QR, valor e copia o Pix sem autenticação', async () => {
    getPayment.mockResolvedValue({ client:'Cliente Teste', description:'Projeto X', amount:'1500.00', due_date:'2026-08-25', status:'PENDING', pix_code:'000201PIX', qr_code:'https://example.test/qr.png', expires_at:'2026-08-25T12:00:00Z' });
    renderPage();
    expect(await screen.findByText(/1\.500,00/)).toBeInTheDocument();
    expect(screen.getByAltText('QR Code Pix da cobrança')).toHaveAttribute('src','https://example.test/qr.png');
    await userEvent.click(screen.getByRole('button',{name:'Copiar código Pix'}));
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('000201PIX');
    expect(screen.getByText('Código Pix copiado')).toBeInTheDocument();
  });
  it('remove QR e código quando pago', async () => {
    getPayment.mockResolvedValue({ client:'Cliente Teste', description:'Projeto X', amount:'1500.00', due_date:'2026-08-25', status:'PAID', pix_code:'secret', qr_code:'https://example.test/qr.png', expires_at:'2026-08-25T12:00:00Z' });
    renderPage();
    expect(await screen.findByText('Pagamento confirmado')).toBeInTheDocument();
    expect(screen.queryByAltText('QR Code Pix da cobrança')).not.toBeInTheDocument();
  });
});
