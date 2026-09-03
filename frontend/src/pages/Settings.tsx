import { zodResolver } from '@hookform/resolvers/zod';
import axios from 'axios';
import { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Avatar, Button, EmptyState, Input, LoadingState } from '../components/ui';
import { useToast } from '../components/Toast';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';
import type { Subscription, SubscriptionPayment } from '../types';
const schema = z.object({
  first_name: z.string().min(2),
  last_name: z.string().min(2),
  avatar: z.string().optional(),
  email: z.email('Email inválido'),
  bio: z.string().max(500, 'Use no máximo 500 caracteres'),
});
type Form = z.infer<typeof schema>;
export const MAX_AVATAR_SIZE = 10 * 1024 * 1024;
export function avatarValidationError(file: File) {
  if (file.size > MAX_AVATAR_SIZE) return 'A imagem deve ter no máximo 10 MB.';
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type))
    return 'Use uma imagem JPG, PNG ou WebP válida.';
  return '';
}
export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [avatar, setAvatar] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarError, setAvatarError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const toast = useToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting },
  } = useForm<Form>({ resolver: zodResolver(schema) });
  useEffect(() => {
    if (user)
      reset({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email,
        bio: user.bio,
        avatar: '',
      });
  }, [user, reset]);
  useEffect(
    () => () => {
      if (avatarPreview) URL.revokeObjectURL(avatarPreview);
    },
    [avatarPreview],
  );
  const selectAvatar = (file?: File) => {
    setAvatarError('');
    if (!file) return;
    const validationError = avatarValidationError(file);
    if (validationError) {
      setAvatarError(validationError);
      if (fileInput.current) fileInput.current.value = '';
      return;
    }
    if (avatarPreview) URL.revokeObjectURL(avatarPreview);
    setAvatar(file);
    setAvatarPreview(URL.createObjectURL(file));
  };
  const cancelAvatar = () => {
    if (avatarPreview) URL.revokeObjectURL(avatarPreview);
    setAvatar(null);
    setAvatarPreview(null);
    setAvatarError('');
    if (fileInput.current) fileInput.current.value = '';
  };
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Perfil</h1>
          <p>Gerencie suas informações pessoais.</p>
        </div>
      </div>
      <section className="settings-card">
        {user?.pending_workspace_approval && (
          <div className="notice">
            Aguardando aprovação do Primário após a alteração do email. Seus dados e histórico foram
            preservados.
          </div>
        )}
        <form
          onSubmit={handleSubmit(async (v) => {
            const body = new FormData();
            body.append('first_name', v.first_name);
            body.append('last_name', v.last_name);
            body.append('email', v.email);
            body.append('bio', v.bio);
            if (avatar) body.append('avatar', avatar);
            await api.patch('/auth/me/', body);
            await refreshUser();
            toast(
              v.email !== user?.email
                ? 'Perfil atualizado. A alteração de email pode exigir aprovação do Primário.'
                : 'Perfil atualizado com sucesso.',
            );
          })}
        >
          <div className="form-row">
            <label>
              Nome
              <Input {...register('first_name')} />
            </label>
            <label>
              Sobrenome
              <Input {...register('last_name')} />
            </label>
          </div>
          <label>
            Email
            <Input type="email" {...register('email')} />
            <small>Secundários precisam de nova aprovação do Primário ao alterar o email.</small>
          </label>
          <label>
            Biografia
            <textarea {...register('bio')} maxLength={500} />
          </label>
          <div className="avatar-picker">
            <Avatar name={user?.first_name || 'U'} url={avatarPreview || user?.avatar} />
            <div>
              <strong>Foto de perfil</strong>
              <small>JPG, PNG ou WebP, até 10 MB.</small>
              <div className="avatar-actions">
                <Button
                  type="button"
                  className="secondary"
                  onClick={() => fileInput.current?.click()}
                >
                  {avatar ? 'Escolher outra' : 'Selecionar imagem'}
                </Button>
                {avatar && (
                  <Button type="button" className="ghost" onClick={cancelAvatar}>
                    Cancelar seleção
                  </Button>
                )}
              </div>
            </div>
            <input
              ref={fileInput}
              className="visually-hidden"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => selectAvatar(event.target.files?.[0])}
            />
          </div>
          {avatarError && (
            <div className="form-error" role="alert">
              {avatarError}
            </div>
          )}
          <Button disabled={isSubmitting}>Salvar alterações</Button>
        </form>
      </section>
    </>
  );
}
export function BillingPage() {
  const [data, setData] = useState<Subscription | null>(null),
    [payments, setPayments] = useState<SubscriptionPayment[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(''),
    [forbidden, setForbidden] = useState(false),
    [actionLoading, setActionLoading] = useState(false);
  const toast = useToast();
  const load = async () => {
    setError('');
    setForbidden(false);
    try {
      const [subscription, history] = await Promise.all([
        api.get<Subscription>('/billing/subscription/'),
        api.get<SubscriptionPayment[]>('/billing/payments/'),
      ]);
      setData(subscription.data);
      setPayments(history.data);
    } catch (requestError) {
      if (axios.isAxiosError(requestError) && requestError.response?.status === 403) {
        setForbidden(true);
      } else {
        setError('Não foi possível carregar os dados de cobrança. Tente novamente.');
      }
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    void load();
  }, []);
  const checkout = async () => {
    setActionLoading(true);
    try {
      const { data: checkoutData } = await api.post<{ url: string }>('/billing/checkout/');
      location.assign(checkoutData.url);
    } catch (requestError) {
      toast(
        axios.isAxiosError(requestError) && requestError.response?.status === 403
          ? 'Somente o proprietário do workspace pode gerenciar a assinatura.'
          : 'Não foi possível iniciar a assinatura. Tente novamente.',
        'warning',
      );
    } finally {
      setActionLoading(false);
    }
  };
  const post = async (path: string) => {
    setActionLoading(true);
    try {
      await api.post(path);
      await load();
    } catch (requestError) {
      toast(
        axios.isAxiosError(requestError) && requestError.response?.status === 403
          ? 'Somente o proprietário do workspace pode gerenciar a assinatura.'
          : 'Não foi possível atualizar a assinatura. Tente novamente.',
        'warning',
      );
    } finally {
      setActionLoading(false);
    }
  };
  if (loading) return <LoadingState />;
  if (forbidden)
    return (
      <section className="panel state">
        <h2>Acesso restrito</h2>
        <p>
          Somente o proprietário do workspace pode consultar pagamentos e gerenciar a assinatura.
        </p>
      </section>
    );
  if (error)
    return (
      <section className="panel state error">
        <h2>Não foi possível carregar a assinatura</h2>
        <p>{error}</p>
        <Button
          className="secondary"
          onClick={() => {
            setLoading(true);
            void load();
          }}
        >
          Tentar novamente
        </Button>
      </section>
    );
  const pro = data?.plan.slug === 'pro' && data.status === 'ACTIVE';
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Assinatura</h1>
          <p>Gerencie seu plano e informações de cobrança.</p>
        </div>
        {pro ? (
          <Button
            className="secondary"
            disabled={actionLoading}
            onClick={() => void post('/billing/cancel/')}
          >
            Cancelar assinatura
          </Button>
        ) : (
          <Button disabled={actionLoading} onClick={() => void checkout()}>
            {actionLoading ? 'Processando…' : 'Assinar Pro — R$ 25/mês'}
          </Button>
        )}
      </div>
      <section className="billing-current">
        <span>PLANO ATUAL</span>
        <h2>
          {data?.plan.name ?? 'Free'} <small>{data?.status}</small>
        </h2>
        <strong>
          R$ {Number(data?.plan.price ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
          <small>/mês</small>
        </strong>
        {data?.current_period_end && (
          <p>Acesso até {new Date(data.current_period_end).toLocaleDateString('pt-BR')}</p>
        )}
      </section>
      <section className="panel">
        <h2>Histórico de pagamentos</h2>
        {payments.length ? (
          <div className="table-wrap flat">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Referência</th>
                  <th>Status</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td>{new Date(p.created_at).toLocaleDateString('pt-BR')}</td>
                    <td>{p.provider_payment_id}</td>
                    <td>{p.status}</td>
                    <td>R$ {Number(p.amount).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="Nenhum pagamento"
            description="Seu histórico aparecerá após a confirmação do gateway."
          />
        )}
      </section>
    </>
  );
}
export function NotificationSettings() {
  const [email, setEmail] = useState(true),
    [inside, setInside] = useState(true),
    [ready, setReady] = useState(false),
    [loadError, setLoadError] = useState('');
  const toast = useToast();
  useEffect(() => {
    api
      .get('/notification-preferences/')
      .then((response) => {
        setEmail(response.data.email_enabled);
        setInside(response.data.in_app_enabled);
      })
      .catch(() => setLoadError('Não foi possível carregar as preferências de notificações.'))
      .finally(() => setReady(true));
  }, []);
  if (!ready) return <LoadingState />;
  if (loadError) return <section className="panel state error">{loadError}</section>;
  return (
    <>
      <div className="page-head">
        <div>
          <h1>Preferências de notificações</h1>
          <p>Escolha como deseja receber atualizações.</p>
        </div>
      </div>
      <section className="settings-card">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            await api.patch('/notification-preferences/', {
              email_enabled: email,
              in_app_enabled: inside,
            });
            toast('Preferências de notificações salvas com sucesso.');
          }}
        >
          <label>
            <input type="checkbox" checked={inside} onChange={(e) => setInside(e.target.checked)} />{' '}
            Notificações dentro do DevFlow
          </label>
          <label>
            <input type="checkbox" checked={email} onChange={(e) => setEmail(e.target.checked)} />{' '}
            Notificações por email
          </label>
          <Button>Salvar preferências</Button>
        </form>
      </section>
    </>
  );
}
