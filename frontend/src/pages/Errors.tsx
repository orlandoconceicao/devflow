import{Link}from'react-router-dom';
export function NotFoundPage(){return <main className="state"><h1>Página não encontrada</h1><p>O endereço informado não existe ou foi movido.</p><Link className="button" to="/dashboard">Voltar ao dashboard</Link></main>}
export function ForbiddenPage(){return <main className="state"><h1>Acesso não autorizado</h1><p>Você não possui permissão para acessar esta área.</p><Link className="button" to="/dashboard">Voltar ao dashboard</Link></main>}
