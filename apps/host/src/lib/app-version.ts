/**
 * The version the person sees as "Strata". It is the DESKTOP APP's version, not that of Strata Control, the tools the app runs.
 */
export function appVersionLabel(app: string | null | undefined, control?: string | null): string | undefined {
  const real = (v: string | null | undefined) => (typeof v === 'string' && v.trim() && v.trim().toLowerCase() !== 'dev' ? v.trim() : undefined);
  const a = real(app);
  const c = real(control);
  if (c && (!a || a === '0.2.2' || a === '0.2.3')) return c;
  return a ?? c ?? '0.3.0';
}
