import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Send } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, ErrorState, Input, LoadingState, Select } from '../components/ui';
import { useToast } from '../components/Toast';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';
import type { TeamMessage } from '../types';

export function SettingsHome() {
  const sections = [
    ['/settings/profile', 'Perfil', 'Foto, nome, biografia e email'],
    ['/settings/preferences', 'Preferências', 'Idioma, fuso horário e tema'],
    ['/settings/notifications', 'Notificações', 'Canais de atualização'],
    ['/password-reset', 'Segurança', 'Redefinição segura de senha'],
    ['/team', 'Equipe', 'Membros Primários e Secundários'],
    ['/settings/billing', 'Cobranças', 'Plano e pagamentos da conta'],
    ['/help', 'Ajuda', 'Perguntas frequentes e suporte'],
  ];
  return <><div className="page-head"><div><h1>Configurações</h1><p>Gerencie sua conta e seu workspace em um só lugar.</p></div></div><div className="settings-grid">{sections.map(([to,title,text]) => <Link className="panel settings-link" to={to} key={to}><h2>{title}</h2><p>{text}</p></Link>)}</div></>;
}

export function PreferencesPage() {
  const { user, refreshUser } = useAuth();
  const toast = useToast();
  const [form, setForm] = useState({ language: 'pt-BR', timezone: 'America/Cuiaba', theme: 'system' });
  useEffect(() => { if (user) setForm({ language: user.language, timezone: user.timezone, theme: user.theme }); }, [user]);
  const set = (key: string, value: string) => setForm((old) => ({ ...old, [key]: value }));
  return <><div className="page-head"><div><h1>Preferências</h1><p>Personalize idioma, datas e aparência.</p></div></div><section className="settings-card"><form onSubmit={async (event) => { event.preventDefault(); await api.patch('/auth/me/', form); await refreshUser(); toast('Preferências salvas com sucesso.'); }}><label>Idioma<Select value={form.language} onChange={(e) => set('language', e.target.value)}><option value="pt-BR">Português</option><option value="en">English</option></Select></label><label>Fuso horário<Select value={form.timezone} onChange={(e) => set('timezone', e.target.value)}><option value="America/Cuiaba">Cuiabá (America/Cuiaba)</option><option value="America/Campo_Grande">Campo Grande (America/Campo_Grande)</option><option value="America/Sao_Paulo">São Paulo (America/Sao_Paulo)</option><option value="UTC">Tempo Universal (UTC)</option></Select></label><label>Tema<Select value={form.theme} onChange={(e) => set('theme', e.target.value)}><option value="system">Sistema</option><option value="light">Claro</option><option value="dark">Escuro</option></Select></label><Button>Salvar preferências</Button></form></section></>;
}

export function TeamChatPage() {
  const [message, setMessage] = useState('');
  const queryClient = useQueryClient();
  const messages = useQuery({ queryKey: ['team-chat'], queryFn: () => api.get<TeamMessage[]>('/organizations/team-chat/').then((r) => r.data), refetchInterval: 5000 });
  if (messages.isLoading) return <LoadingState />;
  if (messages.isError) return <ErrorState message="Não foi possível carregar o chat." />;
  return <><div className="page-head"><div><h1>Chat da equipe</h1><p>Conversa interna e exclusiva deste workspace.</p></div></div><section className="panel chat"><div className="chat-messages">{messages.data?.map((item) => <article key={item.id}><b>{item.author.first_name || item.author.email}</b><p>{item.message}</p><time>{new Date(item.created_at).toLocaleString('pt-BR')}</time></article>)}</div><form onSubmit={async (event) => { event.preventDefault(); if (!message.trim()) return; await api.post('/organizations/team-chat/', { message }); setMessage(''); await queryClient.invalidateQueries({ queryKey: ['team-chat'] }); }}><Input value={message} maxLength={2000} onChange={(e) => setMessage(e.target.value)} placeholder="Digite uma mensagem..." aria-label="Mensagem"/><Button disabled={!message.trim()}><Send size={17}/> Enviar</Button></form></section></>;
}

export function HelpPage() {
  const faq = [
    ['Como criar um cliente?', 'Acesse Clientes e escolha Novo cliente. Owners e Admins podem cadastrar.'],
    ['Como criar um projeto?', 'Acesse Projetos e escolha Novo projeto. Todo projeto precisa de um cliente.'],
    ['Como criar tarefas?', 'Abra um projeto, entre no Kanban e adicione a tarefa.'],
    ['Como adicionar alguém à equipe?', 'O Primário acessa Equipe e envia um convite para Admin ou Membro.'],
    ['Como criar uma cobrança?', 'Em Financeiro, abra Cobranças e escolha Nova cobrança. O Pix usa o Stripe configurado.'],
    ['Como funciona o Pix?', 'O backend solicita um Pix real ao Stripe e fornece uma página pública com QR Code e Copia e Cola.'],
    ['Como alterar meu perfil?', 'Clique no avatar ou acesse Configurações > Perfil.'],
    ['Qual a diferença entre Primário e Secundário?', 'Primário é o Owner responsável pelo workspace. Admins e membros são Secundários e não podem se promover.'],
  ];
  return <><div className="page-head"><div><h1>Ajuda</h1><p>Encontre respostas sobre o funcionamento real do DevFlow.</p></div></div><section className="panel faq"><h2>Perguntas frequentes</h2>{faq.map(([question,answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}</section><section className="panel section-gap support"><h2>Não encontrou o que precisava?</h2><p>Entre em contato com o suporte.</p><a className="button" href="mailto:orlandoconceicao94@gmail.com">Enviar e-mail</a></section></>;
}
