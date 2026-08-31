import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import { Button, Input } from '../components/ui';
import { useAuth } from '../features/auth/AuthContext';
import { api, getApiErrorDetails } from '../services/api';
const loginSchema = z.object({
  email: z.email('Email inválido'),
  password: z.string().min(1, 'Informe a senha'),
});
type Login = z.infer<typeof loginSchema>;
const registerSchema = z
  .object({
    first_name: z.string().min(2, 'Informe seu nome'),
    last_name: z.string().min(2, 'Informe seu sobrenome'),
    email: z.email('Email inválido'),
    password: z
      .string()
      .min(8, 'Use pelo menos 8 caracteres')
      .regex(/[A-Za-zÀ-ÿ]/, 'A senha não pode ser apenas numérica'),
    password_confirm: z.string(),
  })
  .refine((v) => v.password === v.password_confirm, {
    message: 'As senhas não coincidem',
    path: ['password_confirm'],
  });
type Register = z.infer<typeof registerSchema>;
function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="logo">
          <i>⌁</i>DevFlow
        </div>
        <h1>
          Organize o trabalho.
          <br />
          Entregue com clareza.
        </h1>
        <p>Seu espaço para projetos, equipe e resultados — tudo em um só fluxo.</p>
      </div>
      <main className="auth-panel">
        <section className="auth-card">
          <h2>{title}</h2>
          <p>{subtitle}</p>
          {children}
        </section>
      </main>
    </div>
  );
}
export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const [params] = useSearchParams();
  const [serverError, setServerError] = useState('');
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Login>({ resolver: zodResolver(loginSchema) });
  const requestedPath = params.get('next');
  const destination =
    requestedPath?.startsWith('/') && !requestedPath.startsWith('//')
      ? requestedPath
      : '/dashboard';
  if (isAuthenticated) return <Navigate to={destination} />;
  return (
    <AuthShell title="Bem-vindo de volta" subtitle="Entre para continuar no seu workspace.">
      <form
        onSubmit={handleSubmit(async (v) => {
          setServerError('');
          try {
            await login(v.email, v.password);
          } catch (error) {
            setServerError(getApiErrorDetails(error, 'Não foi possível entrar.').message);
          }
        })}
      >
        <label>
          Email
          <Input type="email" {...register('email')} />
          <small>{errors.email?.message}</small>
        </label>
        <label>
          <span className="auth-label-row">
            <span>Senha</span>
            <Link to="/password-reset">Esqueci minha senha</Link>
          </span>
          <Input type="password" {...register('password')} />
          <small>{errors.password?.message}</small>
        </label>
        {serverError && <div className="form-error">{serverError}</div>}
        <Button disabled={isSubmitting}>{isSubmitting ? 'Entrando…' : 'Entrar'}</Button>
      </form>
      <footer className="auth-login-footer">
        <span className="auth-divider">ou</span>
        <span>Não tem uma conta? <Link to="/register">Criar conta</Link></span>
      </footer>
    </AuthShell>
  );
}
export function RegisterPage() {
  const { register: signUp } = useAuth();
  const nav = useNavigate();
  const [serverError, setServerError] = useState('');
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Register>({ resolver: zodResolver(registerSchema) });
  return (
    <AuthShell title="Crie sua conta" subtitle="Comece gratuitamente. Leva menos de um minuto.">
      <form
        onSubmit={handleSubmit(async (v) => {
          setServerError('');
          try {
            await signUp(v);
            nav('/onboarding/workspace');
          } catch (error) {
            const apiError = getApiErrorDetails(
              error,
              'Não foi possível criar a conta. Verifique os dados.',
            );
            const registerFields = [
              'first_name',
              'last_name',
              'email',
              'password',
              'password_confirm',
            ] as const;
            registerFields.forEach((field) => {
              if (apiError.fields[field]) {
                setError(field, { type: 'server', message: apiError.fields[field] });
              }
            });
            setServerError(apiError.message);
          }
        })}
      >
        <div className="form-row">
          <label>
            Nome
            <Input {...register('first_name')} />
            <small>{errors.first_name?.message}</small>
          </label>
          <label>
            Sobrenome
            <Input {...register('last_name')} />
            <small>{errors.last_name?.message}</small>
          </label>
        </div>
        <label>
          Email
          <Input type="email" {...register('email')} />
          <small>{errors.email?.message}</small>
        </label>
        <label>
          Senha
          <Input type="password" {...register('password')} />
          <small>{errors.password?.message}</small>
          {!errors.password && (
            <small>Use 8 ou mais caracteres e evite senhas comuns ou apenas números.</small>
          )}
        </label>
        <label>
          Confirmar senha
          <Input type="password" {...register('password_confirm')} />
          <small>{errors.password_confirm?.message}</small>
        </label>
        {serverError && <div className="form-error">{serverError}</div>}
        <Button disabled={isSubmitting}>Criar conta</Button>
      </form>
      <footer>
        Já tem uma conta? <Link to="/login">Entrar</Link>
      </footer>
    </AuthShell>
  );
}

export function PasswordResetPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  return (
    <AuthShell title="Redefinir senha" subtitle="Enviaremos as instruções para seu email.">
      <form
        onSubmit={async (event) => {
          event.preventDefault();
          setError('');
          setSubmitting(true);
          try {
            const { data } = await api.post<{ detail: string }>('/auth/password-reset/', {
              email: email.trim().toLowerCase(),
            });
            setMessage(data.detail);
          } catch (requestError) {
            setError(
              getApiErrorDetails(requestError, 'Não foi possível enviar as instruções.').message,
            );
          } finally {
            setSubmitting(false);
          }
        }}
      >
        <label>
          Email
          <Input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        {message && <div>{message}</div>}
        {error && <div className="form-error">{error}</div>}
        <Button disabled={submitting}>{submitting ? 'Enviando…' : 'Enviar instruções'}</Button>
      </form>
      <footer>
        <Link to="/login">Voltar ao login</Link>
      </footer>
    </AuthShell>
  );
}

export function PasswordResetConfirmPage() {
  const [params] = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const uid = params.get('uid') ?? '';
  const token = params.get('token') ?? '';
  return (
    <AuthShell title="Criar nova senha" subtitle="Escolha uma senha segura para sua conta.">
      {!uid || !token ? (
        <div className="form-error">Link de redefinição inválido.</div>
      ) : message ? (
        <>
          <div>{message}</div>
          <footer>
            <Link to="/login">Entrar</Link>
          </footer>
        </>
      ) : (
        <form
          onSubmit={async (event) => {
            event.preventDefault();
            setError('');
            if (password !== confirmation) {
              setError('As senhas não coincidem.');
              return;
            }
            setSubmitting(true);
            try {
              const { data } = await api.post<{ detail: string }>('/auth/password-reset/confirm/', {
                uid,
                token,
                password,
              });
              setMessage(data.detail);
            } catch (requestError) {
              setError(
                getApiErrorDetails(requestError, 'Não foi possível redefinir a senha.').message,
              );
            } finally {
              setSubmitting(false);
            }
          }}
        >
          <label>
            Nova senha
            <Input
              type="password"
              minLength={8}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <label>
            Confirmar senha
            <Input
              type="password"
              minLength={8}
              required
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
            />
          </label>
          {error && <div className="form-error">{error}</div>}
          <Button disabled={submitting}>{submitting ? 'Salvando…' : 'Salvar nova senha'}</Button>
        </form>
      )}
    </AuthShell>
  );
}
