import { Button } from '../components/ui';
import { api } from '../services/api';
import { useToast } from '../components/Toast';
export function PricingPage() {
  const toast = useToast();
  const checkout = async () => {
    try {
      const { data } = await api.post<{ url: string }>('/billing/checkout/');
      location.assign(data.url);
    } catch {
      toast('Configure o Mercado Pago em modo de teste para iniciar a assinatura.', 'warning');
    }
  };
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Planos</h1>
          <p>Escolha o plano adequado para o seu trabalho.</p>
        </div>
      </div>
      <div className="plans">
        <article className="plan-card">
          <h2>Free</h2>
          <div className="price">
            <strong>R$ 0</strong>
            <span>/mês</span>
          </div>
          <p>Para começar e testar o DevFlow.</p>
          <ul>
            <li>3 projetos ativos</li>
            <li>2 membros</li>
            <li>500 MB</li>
          </ul>
        </article>
        <article className="plan-card recommended">
          <span className="recommend">RECOMENDADO</span>
          <h2>DevFlow Pro</h2>
          <div className="price">
            <strong>R$ 25</strong>
            <span>/mês</span>
          </div>
          <p>Para freelancers e pequenas equipes.</p>
          <ul>
            <li>Projetos ilimitados</li>
            <li>20 membros</li>
            <li>10 GB</li>
            <li>Portal e relatórios avançados</li>
          </ul>
          <Button onClick={checkout}>Assinar Pro</Button>
        </article>
      </div>
    </>
  );
}
export function BillingResult({ cancel = false }: { cancel?: boolean }) {
  return (
    <section className="settings-card">
      <h1>{cancel ? 'Pagamento não concluído' : 'Estamos confirmando sua assinatura'}</h1>
      <p>
        {cancel
          ? 'Você pode tentar novamente quando quiser.'
          : 'O Pro será ativado somente após a confirmação segura do webhook.'}
      </p>
      <a className="button" href={cancel ? '/pricing' : '/settings/billing'}>
        {cancel ? 'Tentar novamente' : 'Ver assinatura'}
      </a>
    </section>
  );
}
