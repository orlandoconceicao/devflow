const locale = () => localStorage.getItem('preferred_language') || 'pt-BR';
const timezone = () => localStorage.getItem('preferred_timezone') || 'America/Cuiaba';
export const formatCurrency = (value: string | number | null) =>
  new Intl.NumberFormat(locale(), { style: 'currency', currency: 'BRL' }).format(Number(value ?? 0));
export const formatDate = (value: string | null) =>
  value ? new Intl.DateTimeFormat(locale(), { timeZone: timezone() }).format(new Date(`${value}T12:00:00`)) : 'Sem prazo';
