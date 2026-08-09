import { EmptyState } from '../components/ui';
export function Placeholder({ title }: { title: string }) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <p>Este módulo está sendo preparado.</p>
        </div>
      </div>
      <section className="panel">
        <EmptyState
          title="Em breve"
          description={`O módulo de ${title.toLowerCase()} chegará nas próximas etapas.`}
        />
      </section>
    </>
  );
}
