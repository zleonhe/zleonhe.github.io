/** Prefix local links with Astro's configured hosting path. */
export function localUrl(url: string): string {
  return url.startsWith('/') && !url.startsWith('//')
    ? import.meta.env.BASE_URL.replace(/\/$/, '') + url
    : url;
}
