/** The product version shown in Settings; Control is a development fallback. */
export function appVersionLabel(app: string | null | undefined, control?: string | null): string | undefined {
  const real = (value: string | null | undefined): string | undefined =>
    typeof value === 'string' && value.trim() && value.trim().toLowerCase() !== 'dev' ? value.trim() : undefined;
  return real(app) ?? real(control) ?? (typeof app === 'string' && app.trim() ? app.trim() : undefined);
}

/** Display release badge with a leading `v` for numeric versions (e.g. `0.2.20` -> `v0.2.20`), leaving `dev` unchanged (#6602). */
export function releaseVersionBadge(version: string | null | undefined): string | undefined {
  const v = typeof version === 'string' ? version.trim() : '';
  if (!v) return undefined;
  return /^\d/.test(v) ? `v${v}` : v;
}
