/**
 * Acceso centralizado a variables de entorno. Nada de credenciales
 * hardcodeadas: todo sale de acá y falla con mensaje claro si falta.
 */

export function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Falta la variable de entorno ${name}. Revisá .env.example para el listado completo.`
    );
  }
  return value;
}

export function optionalEnv(name: string): string | undefined {
  return process.env[name] || undefined;
}

/** true si Supabase está configurado (la UI degrada a aviso de setup si no). */
export function hasSupabaseEnv(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY
  );
}
