import { Copy, MessageCircle, Trash2, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button, EmptyState, Input, LoadingState, Select } from '../components/ui';
import { organizationService } from '../services/work';
import type { Organization, OrganizationMembership } from '../types';
import { Link } from 'react-router-dom';
import { useToast } from '../components/Toast';
import { getApiErrorDetails } from '../services/api';

export function TeamPage() {
  const toast = useToast();
  const [organization, setOrganization] = useState<Organization>();
  const [members, setMembers] = useState<OrganizationMembership[]>([]);
  const [invitations, setInvitations] = useState<
    Array<{ id: number; email: string; role: 'ADMIN' | 'MEMBER'; expires_at: string }>
  >([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [removingMemberId, setRemovingMemberId] = useState<number | null>(null);
  const [cancelingInvitationId, setCancelingInvitationId] = useState<number | null>(null);
  const load = async () => {
    const org = await organizationService.ensure();
    setOrganization(org);
    if (org?.role === 'OWNER') {
      const [memberData, invitationData] = await Promise.all([
        organizationService.members(org.id),
        organizationService.invitations(org.id),
      ]);
      setMembers(memberData.results);
      setInvitations(invitationData);
    }
    setLoading(false);
  };
  useEffect(() => {
    void load();
  }, []);
  if (loading) return <LoadingState />;
  if (!organization || organization.role !== 'OWNER')
    return (
      <EmptyState
        title="Acesso restrito"
        description="Somente o Primário pode gerenciar a equipe."
      />
    );
  return (
    <>
      <div className="page-head team-page-head">
        <div>
          <h1>Equipe</h1>
          <p>
            <b>Primário</b>: responsável principal. <b>Secundário</b>: funcionário ou membro. O
            próprio usuário não pode se promover.
          </p>
        </div>
        <div className="actions">
          <Link className="button team-chat-button" to="/team/chat">
            <MessageCircle size={18} strokeWidth={2} aria-hidden="true" />
            Chat da equipe
          </Link>
        </div>
      </div>
      {error && <div className="form-error">{error}</div>}
      <section className="panel">
        <div className="table-wrap flat">
          <table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>Email</th>
                <th>Função</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.id}>
                  <td>
                    {`${member.user.first_name} ${member.user.last_name}`.trim() || 'Sem nome'}
                  </td>
                  <td>{member.user.email}</td>
                  <td>
                    {member.role === 'OWNER' ? (
                      'Primário'
                    ) : (
                      <Select
                        value={member.role}
                        onChange={async (event) => {
                          try {
                            await organizationService.updateMember(
                              organization.id,
                              member.id,
                              event.target.value as 'ADMIN' | 'MEMBER',
                            );
                            await load();
                          } catch {
                            setError('Não foi possível alterar a função.');
                          }
                        }}
                      >
                        <option value="ADMIN">Admin</option>
                        <option value="MEMBER">Membro</option>
                      </Select>
                    )}
                  </td>
                  <td>
                    <span className="status status-active">
                      {member.approval_status === 'PENDING'
                        ? 'Aguardando aprovação'
                        : member.is_active
                          ? 'Ativo'
                          : 'Desativado'}
                    </span>
                  </td>
                  <td>
                    <div className="team-row-actions">
                      {member.approval_status === 'PENDING' && (
                        <Button
                          className="secondary"
                          onClick={async () => {
                            await organizationService.approveMember(organization.id, member.id);
                            await load();
                          }}
                        >
                          Aprovar novo email
                        </Button>
                      )}
                      {member.role !== 'OWNER' && member.is_active && (
                        <Button
                          className="team-destructive-button"
                          aria-label={`Remover ${member.user.email}`}
                          disabled={removingMemberId === member.id}
                          onClick={async () => {
                            const memberName =
                              `${member.user.first_name} ${member.user.last_name}`.trim();
                            const identity = memberName
                              ? `${memberName} (${member.user.email})`
                              : member.user.email;
                            if (
                              !confirm(
                                `Tem certeza de que deseja remover este membro da equipe?\n\n${identity}`,
                              )
                            )
                              return;
                            setRemovingMemberId(member.id);
                            setError('');
                            try {
                              await organizationService.removeMember(organization.id, member.id);
                              setMembers((current) =>
                                current.filter((item) => item.id !== member.id),
                              );
                              toast(`${identity} foi removido da equipe.`);
                            } catch (requestError) {
                              const message = getApiErrorDetails(
                                requestError,
                                'Não foi possível remover o membro.',
                              ).message;
                              setError(message);
                              toast(message, 'error');
                            } finally {
                              setRemovingMemberId(null);
                            }
                          }}
                        >
                          <Trash2 size={16} aria-hidden="true" />
                          {removingMemberId === member.id ? 'Removendo…' : 'Remover da equipe'}
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {!!invitations.length && (
        <section className="panel section-gap">
          <h2>Convites pendentes</h2>
          {invitations.map((invite) => (
            <div className="project-row team-invitation-row" key={invite.id}>
              <span className="team-invitation-identity">
                <b>{invite.email}</b>
                <small>{invite.role === 'ADMIN' ? 'Admin' : 'Membro'}</small>
              </span>
              <span className="team-invitation-expiry">
                Expira em {new Date(invite.expires_at).toLocaleDateString('pt-BR')}
              </span>
              <Button
                className="team-destructive-button"
                disabled={cancelingInvitationId === invite.id}
                onClick={async () => {
                  if (
                    !confirm(`Tem certeza de que deseja cancelar este convite?\n\n${invite.email}`)
                  )
                    return;
                  setCancelingInvitationId(invite.id);
                  setError('');
                  try {
                    await organizationService.cancelInvitation(organization.id, invite.id);
                    setInvitations((current) => current.filter((item) => item.id !== invite.id));
                    toast(`Convite para ${invite.email} cancelado.`);
                  } catch (requestError) {
                    const message = getApiErrorDetails(
                      requestError,
                      'Não foi possível cancelar o convite.',
                    ).message;
                    setError(message);
                    toast(message, 'error');
                  } finally {
                    setCancelingInvitationId(null);
                  }
                }}
              >
                <XCircle size={16} aria-hidden="true" />
                {cancelingInvitationId === invite.id ? 'Cancelando…' : 'Cancelar convite'}
              </Button>
            </div>
          ))}
        </section>
      )}
      {open && (
        <InviteModal organization={organization} onClose={() => setOpen(false)} onInvited={load} />
      )}
    </>
  );
}

function InviteModal({
  organization,
  onClose,
  onInvited,
}: {
  organization: Organization;
  onClose: () => void;
  onInvited: () => Promise<void>;
}) {
  const [email, setEmail] = useState(''),
    [role, setRole] = useState<'ADMIN' | 'MEMBER'>('MEMBER'),
    [url, setUrl] = useState(''),
    [error, setError] = useState(''),
    [sending, setSending] = useState(false);
  return (
    <div className="modal-backdrop">
      <div className="form-modal">
        <div>
          <h2>Convidar membro</h2>
          <button onClick={onClose}>×</button>
        </div>
        {url ? (
          <div className="invite-result">
            <p>Convite criado e enviado por email.</p>
            <Input readOnly value={url} />
            <Button onClick={() => navigator.clipboard.writeText(url)}>
              <Copy size={17} /> Copiar link
            </Button>
            <Button className="secondary" onClick={onClose}>
              Fechar
            </Button>
          </div>
        ) : (
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setSending(true);
              setError('');
              try {
                const result = await organizationService.invite(organization.id, { email, role });
                setUrl(result.invite_url);
                await onInvited();
              } catch {
                setError('Não foi possível enviar o convite.');
              } finally {
                setSending(false);
              }
            }}
          >
            <label>
              Email
              <Input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label>
              Função
              <Select value={role} onChange={(e) => setRole(e.target.value as 'ADMIN' | 'MEMBER')}>
                <option value="MEMBER">Membro</option>
                <option value="ADMIN">Admin</option>
              </Select>
            </label>
            {error && <div className="form-error">{error}</div>}
            <footer>
              <Button type="button" className="secondary" onClick={onClose}>
                Cancelar
              </Button>
              <Button disabled={sending}>{sending ? 'Enviando…' : 'Enviar convite'}</Button>
            </footer>
          </form>
        )}
      </div>
    </div>
  );
}
