import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { PlanCard } from '../components/PlanCard';
import { Button, ErrorState, Input, LoadingState } from '../components/ui';
import { api, getApiErrorDetails } from '../services/api';
import type { Plan } from '../types';
const schema = z.object({ name: z.string().min(2, 'Informe o nome do workspace') });
type Form = z.infer<typeof schema>;
function Steps({ step }: { step: number }) {
  return (
    <div className="steps">
      <span className="done">✓</span>
      <i />
      <span className={step >= 2 ? 'active' : ''}>2</span>
      <i />
      <span className={step >= 3 ? 'active' : ''}>3</span>
      <div>
        <b>Conta</b>
        <b>Workspace</b>
        <b>Plano</b>
      </div>
    </div>
  );
}
export function WorkspacePage() {
  const nav = useNavigate();
  const [serverError, setServerError] = useState('');
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Form>({ resolver: zodResolver(schema) });
  return (
    <div className="onboarding">
      <div className="logo">
        <i>⌁</i>DevFlow
      </div>
      <Steps step={2} />
      <section>
        <span className="eyebrow">SEU ESPAÇO DE TRABALHO</span>
        <h1>Como vamos chamar seu workspace?</h1>
        <p>Você poderá convidar sua equipe e ajustar isso depois.</p>
        <form
          onSubmit={handleSubmit(async (v) => {
            setServerError('');
            try {
              const { data } = await api.post<{ id: number }>('/organizations/', v);
              localStorage.setItem('organization_id', String(data.id));
              nav('/onboarding/plan');
            } catch (requestError) {
              setServerError(
                getApiErrorDetails(requestError, 'Não foi possível criar o workspace.').message,
              );
            }
          })}
        >
          <label>
            Nome do workspace
            <Input placeholder="Ex: Studio Aurora" {...register('name')} />
            <small>{errors.name?.message}</small>
          </label>
          {serverError && <div className="form-error">{serverError}</div>}
          <Button disabled={isSubmitting}>Continuar →</Button>
        </form>
      </section>
    </div>
  );
}
export function PlanPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const nav = useNavigate();
  const loadPlans = () => {
    setError('');
    api
      .get<Plan[]>('/plans/')
      .then((response) => setPlans(response.data))
      .catch(() => setError('Não foi possível carregar os planos.'));
  };
  useEffect(() => {
    loadPlans();
  }, []);
  return (
    <div className="onboarding plan-page">
      <div className="logo">
        <i>⌁</i>DevFlow
      </div>
      <Steps step={3} />
      <section>
        <span className="eyebrow">ESCOLHA SEU PLANO</span>
        <h1>Comece no seu ritmo</h1>
        <p>Você pode mudar de plano quando quiser.</p>
        {error ? (
          <ErrorState message={error} />
        ) : !plans.length ? (
          <LoadingState />
        ) : (
          <div className="plans">
            {plans.map((p) => (
              <PlanCard
                key={p.id}
                plan={p}
                recommended={p.slug === 'pro'}
                onSelect={() =>
                  p.slug === 'free'
                    ? nav('/dashboard')
                    : setNotice('Os pagamentos do DevFlow Pro serão disponibilizados em breve.')
                }
              />
            ))}
          </div>
        )}
        {notice && <div className="notice">{notice}</div>}
      </section>
    </div>
  );
}
