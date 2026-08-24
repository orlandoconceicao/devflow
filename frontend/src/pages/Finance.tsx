import { Copy, ExternalLink, Plus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button, EmptyState, Input, LoadingState, Select } from '../components/ui';
import {
  useCreateInvoice,
  useExpenses,
  useFinanceDashboard,
  useGeneratePayment,
  useInvoices,
  useRevenues,
} from '../features/finance/hooks';
import { useClients, useProjects } from '../features/work/hooks';
import type { Expense, Invoice, Revenue } from '../types';
import { Link, useSearchParams } from 'react-router-dom';
import { useToast } from '../components/Toast';

const money = (v: string | number) =>
  Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const today = () => new Date().toISOString().slice(0, 10);

export function FinancePage() {
  const [params] = useSearchParams();
  const [tab, setTab] = useState('overview');
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (params.get('tab') === 'invoices') setTab('invoices');
    if (params.get('new') === '1') setOpen(true);
  }, [params]);
  const dashboard = useFinanceDashboard(),
    expenses = useExpenses(),
    revenues = useRevenues(),
    invoices = useInvoices();
  if (dashboard.isLoading) return <LoadingState />;
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Financeiro</h1>
          <p>Receitas, despesas e cobranças Pix dos clientes.</p>
        </div>
        {tab === 'invoices' && (
          <Button onClick={() => setOpen(true)}>
            <Plus size={18} /> Nova cobrança
          </Button>
        )}
      </div>
      <div className="tabs">
        {[
          ['overview', 'Visão geral'],
          ['revenues', 'Receitas'],
          ['expenses', 'Despesas'],
          ['invoices', 'Cobranças'],
        ].map(([key, label]) => (
          <button key={key} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>
      {tab === 'overview' && (
        <div className="stats">
          <article>
            <div>
              <span>Receita</span>
              <strong>{money(dashboard.data?.revenue || 0)}</strong>
            </div>
          </article>
          <article>
            <div>
              <span>Despesas</span>
              <strong>{money(dashboard.data?.expenses || 0)}</strong>
            </div>
          </article>
          <article>
            <div>
              <span>Custo de horas</span>
              <strong>{money(dashboard.data?.labor_cost || 0)}</strong>
            </div>
          </article>
          <article>
            <div>
              <span>Lucro estimado</span>
              <strong>{money(dashboard.data?.profit || 0)}</strong>
            </div>
          </article>
        </div>
      )}
      {tab === 'revenues' && <DataTable rows={revenues.data?.results || []} kind="Receitas" />}
      {tab === 'expenses' && <DataTable rows={expenses.data?.results || []} kind="Despesas" />}
      {tab === 'invoices' && <InvoiceTable rows={invoices.data?.results || []} />}
      {open && (
        <ChargeForm initialClient={params.get('client') || ''} onClose={() => setOpen(false)} />
      )}
    </>
  );
}

function InvoiceTable({ rows }: { rows: Invoice[] }) {
  const generate = useGeneratePayment();
  const toast = useToast();
  if (!rows.length)
    return (
      <EmptyState
        title="Nenhuma cobrança"
        description="Crie uma cobrança para gerar um link Pix público, sem login para o cliente."
      />
    );
  return (
    <section className="panel">
      <div className="table-wrap flat">
        <table>
          <thead>
            <tr>
              <th>Número</th>
              <th>Cliente</th>
              <th>Vencimento</th>
              <th>Status</th>
              <th>Total</th>
              <th>Pagamento</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((x) => (
              <tr key={x.id}>
                <td>{x.number}</td>
                <td>{x.client_name}</td>
                <td>{new Date(`${x.due_on}T00:00`).toLocaleDateString('pt-BR')}</td>
                <td>
                  <span className="badge">{x.payment?.status || x.status}</span>
                </td>
                <td>{money(x.total)}</td>
                <td className="payment-actions">
                  {x.payment ? (
                    <>
                      <button
                        title="Copiar link"
                        onClick={async () => {
                          await navigator.clipboard.writeText(x.payment!.public_url);
                          toast('Link da cobrança copiado.');
                        }}
                      >
                        <Copy size={16} />
                      </button>
                      <a
                        title="Abrir página"
                        href={x.payment.public_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <ExternalLink size={16} />
                      </a>
                      {['EXPIRED', 'FAILED'].includes(x.payment.status) && (
                        <Button
                          className="secondary"
                          onClick={() => generate.mutate({ id: x.id, regenerate: true })}
                        >
                          Gerar novo Pix
                        </Button>
                      )}
                    </>
                  ) : (
                    <Button
                      className="secondary"
                      onClick={() => generate.mutate({ id: x.id })}
                      disabled={generate.isPending}
                    >
                      Gerar agora
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ChargeForm({ onClose, initialClient }: { onClose: () => void; initialClient: string }) {
  const clients = useClients(),
    projects = useProjects(),
    create = useCreateInvoice(),
    generate = useGeneratePayment();
  const [form, setForm] = useState({
    client: initialClient,
    project: '',
    description: '',
    amount: '',
    due_on: '',
    payment_release_on: today(),
    auto: false,
    now: true,
  });
  const set = (key: string, value: string | boolean) =>
    setForm((old) => ({ ...old, [key]: value }));
  return (
    <div className="modal-backdrop">
      <div className="form-modal">
        <div>
          <h2>Nova cobrança</h2>
          <button onClick={onClose}>×</button>
        </div>
        {!clients.isLoading && !clients.data?.results.length ? (
          <EmptyState
            title="Nenhum cliente cadastrado"
            description="Para criar uma cobrança, primeiro cadastre o cliente."
            action={
              <Link className="button" to="/clients?new=1&returnTo=%2Ffinance%3Ftab%3Dinvoices%26new%3D1">
                Cadastrar cliente
              </Link>
            }
          />
        ) : (
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              const invoice = await create.mutateAsync({
                client: Number(form.client),
                project: form.project ? Number(form.project) : null,
                number: `COB-${Date.now()}`,
                issued_on: today(),
                due_on: form.due_on,
                payment_release_on: form.payment_release_on,
                auto_generate_payment: form.auto,
                items: [{ description: form.description, quantity: '1', unit_price: form.amount }],
              });
              if (form.now) {
                const payment = await generate.mutateAsync({ id: invoice.id });
                location.assign(payment.public_url);
                return;
              }
              onClose();
            }}
          >
            <label>
              Cliente
              <Select required value={form.client} onChange={(e) => set('client', e.target.value)}>
                <option value="">Selecione</option>
                {clients.data?.results.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </label>
            <label>
              Projeto (opcional)
              <Select value={form.project} onChange={(e) => set('project', e.target.value)}>
                <option value="">Sem projeto</option>
                {projects.data?.results
                  .filter((p) => !form.client || p.client === Number(form.client))
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
              </Select>
            </label>
            <label>
              Descrição
              <Input
                required
                minLength={2}
                value={form.description}
                onChange={(e) => set('description', e.target.value)}
              />
            </label>
            <div className="form-row">
              <label>
                Valor (R$)
                <Input
                  required
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.amount}
                  onChange={(e) => set('amount', e.target.value)}
                />
              </label>
              <label>
                Vencimento
                <Input
                  required
                  type="date"
                  min={today()}
                  value={form.due_on}
                  onChange={(e) => set('due_on', e.target.value)}
                />
              </label>
            </div>
            <label>
              Disponibilizar a partir de
              <Input
                required
                type="date"
                min={today()}
                value={form.payment_release_on}
                onChange={(e) => set('payment_release_on', e.target.value)}
              />
            </label>
            <label className="check-row">
              <input
                type="checkbox"
                checked={form.now}
                onChange={(e) => set('now', e.target.checked)}
              />{' '}
              Gerar cobrança Pix agora
            </label>
            <label className="check-row">
              <input
                type="checkbox"
                checked={form.auto}
                onChange={(e) => set('auto', e.target.checked)}
              />{' '}
              Gerar automaticamente na data de liberação
            </label>
            {(create.error || generate.error) && (
              <small>
                Não foi possível criar a cobrança. Confira os dados e a configuração do Mercado Pago.
              </small>
            )}
            <footer>
              <Button type="button" className="secondary" onClick={onClose}>
                Cancelar
              </Button>
              <Button disabled={create.isPending || generate.isPending}>Criar cobrança</Button>
            </footer>
          </form>
        )}
      </div>
    </div>
  );
}

function DataTable({ rows, kind }: { rows: Array<Expense | Revenue>; kind: string }) {
  return (
    <section className="panel">
      <h2>{kind}</h2>
      {rows.length ? (
        <div className="table-wrap flat">
          <table>
            <thead>
              <tr>
                <th>Descrição</th>
                <th>Data</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((x) => (
                <tr key={x.id}>
                  <td>{x.description}</td>
                  <td>{new Date(`${x.occurred_on}T00:00`).toLocaleDateString('pt-BR')}</td>
                  <td>{money(x.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title={`Nenhuma ${kind.toLowerCase()} registrada`} />
      )}
    </section>
  );
}
