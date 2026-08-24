import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, Clock3, Copy, TriangleAlert } from 'lucide-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { publicPaymentService } from '../services/finance';

const money = (value: string) =>
  Number(value).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export function PublicPaymentPage() {
  const token = useParams().token || '';
  const [copied, setCopied] = useState(false);
  const payment = useQuery({
    queryKey: ['public-payment', token], queryFn: () => publicPaymentService.get(token),
    retry: false, refetchInterval: (query) => query.state.data?.status === 'PENDING' ? 5000 : false,
  });
  if (payment.isLoading) return <main className="payment-shell"><p>Carregando cobrança…</p></main>;
  if (!payment.data) return <main className="payment-shell"><section className="payment-card"><TriangleAlert /><h1>Cobrança não encontrada</h1><p>Confira se o link recebido está completo.</p></section></main>;
  const data = payment.data;
  if (data.status === 'PAID') return <main className="payment-shell"><section className="payment-card payment-success"><CheckCircle2 /><h1>Pagamento confirmado</h1><strong>{money(data.amount)}</strong><p>Pagamento recebido com sucesso.</p></section></main>;
  const unavailable = data.status !== 'PENDING';
  return <main className="payment-shell"><section className="payment-card">
    <span className="payment-brand">DevFlow</span><h1>Pagamento</h1><p>{data.description}</p>
    <div className="payment-amount"><small>Valor</small><strong>{money(data.amount)}</strong></div>
    <p><b>Vencimento:</b> {new Date(`${data.due_date}T00:00`).toLocaleDateString('pt-BR')}</p>
    {unavailable ? <div className="payment-expired"><TriangleAlert /><h2>Cobrança {data.status === 'EXPIRED' ? 'expirada' : 'indisponível'}</h2><p>Solicite um novo link ao responsável.</p></div> : <>
      <img className="pix-qr" src={data.qr_code} alt="QR Code Pix da cobrança" />
      <p>Escaneie com o aplicativo do seu banco</p>
      <label className="pix-copy"><span>Pix Copia e Cola</span><textarea readOnly value={data.pix_code} /></label>
      <button className="copy-payment" onClick={async () => { await navigator.clipboard.writeText(data.pix_code); setCopied(true); }}><Copy size={18} />{copied ? 'Código Pix copiado' : 'Copiar código Pix'}</button>
      <p className="payment-status"><Clock3 size={16} /> Aguardando pagamento</p>
    </>}
  </section></main>;
}
