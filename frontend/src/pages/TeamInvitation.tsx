import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Button, Input, LoadingState } from '../components/ui';
import { api, getApiErrorDetails } from '../services/api';

interface Invitation { email:string; role:string; organization_name:string; expires_at:string; status:string }
export function TeamInvitationPage() {
  const [params]=useSearchParams(), token=params.get('token')||'';
  const [invite,setInvite]=useState<Invitation>(), [loading,setLoading]=useState(true), [error,setError]=useState(''), [done,setDone]=useState(false);
  const [firstName,setFirstName]=useState(''), [lastName,setLastName]=useState(''), [password,setPassword]=useState('');
  useEffect(()=>{api.get<Invitation>(`/organizations/team-invitations/${token}/`).then((r)=>setInvite(r.data)).catch(()=>setError('Convite inválido ou expirado.')).finally(()=>setLoading(false));},[token]);
  if(loading)return <LoadingState/>;
  return <main className="payment-shell"><section className="auth-card team-invite-card"><h1>Entrar na equipe</h1>{error?<div className="form-error">{error}</div>:done?<><p>Convite aceito. Use seu email e sua senha no login normal.</p><Link to="/login">Ir para /login</Link></>:invite&&<><p>Você foi convidado para <b>{invite.organization_name}</b> como {invite.role==='ADMIN'?'Admin':'Membro'}.</p><form onSubmit={async(e)=>{e.preventDefault();setError('');try{await api.post('/organizations/team-invitations/accept/',{token,first_name:firstName,last_name:lastName,password});setDone(true);}catch(requestError){setError(getApiErrorDetails(requestError,'Não foi possível aceitar o convite.').message);}}}><label>Email<Input value={invite.email} readOnly/></label><div className="form-row"><label>Nome<Input value={firstName} onChange={(e)=>setFirstName(e.target.value)}/></label><label>Sobrenome<Input value={lastName} onChange={(e)=>setLastName(e.target.value)}/></label></div><label>Sua senha<Input required minLength={8} type="password" value={password} onChange={(e)=>setPassword(e.target.value)}/><small>Se sua conta já existe, informe a senha atual. Caso contrário, esta será sua nova senha.</small></label><Button>Aceitar convite</Button></form></>}</section></main>;
}
