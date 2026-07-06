import { createClient, type SupabaseClient, type User } from "@supabase/supabase-js";

type PublicAuthConfig = {
  enabled: boolean;
  supabase_url: string;
  publishable_key: string;
};

let clientPromise: Promise<SupabaseClient | null> | null = null;

export function getAuthClient(): Promise<SupabaseClient | null> {
  if (!clientPromise) {
    clientPromise = fetch("/api/auth/config")
      .then(async (response) => {
        if (!response.ok) throw new Error("Unable to load authentication settings");
        const config = await response.json() as PublicAuthConfig;
        if (!config.enabled) return null;
        return createClient(config.supabase_url, config.publishable_key, {
          auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
        });
      });
  }
  return clientPromise;
}

export async function currentUser(): Promise<User | null> {
  const client = await getAuthClient();
  if (!client) return null;
  const { data, error } = await client.auth.getUser();
  if (error) return null;
  return data.user;
}

export async function signInWithGoogle(): Promise<void> {
  const client = await getAuthClient();
  if (!client) throw new Error("Authentication has not been configured yet.");
  const { error } = await client.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: window.location.origin },
  });
  if (error) throw error;
}

export async function sendMagicLink(email: string): Promise<void> {
  const client = await getAuthClient();
  if (!client) throw new Error("Authentication has not been configured yet.");
  const { error } = await client.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: window.location.origin, shouldCreateUser: true },
  });
  if (error) throw error;
}

export async function signOut(): Promise<void> {
  const client = await getAuthClient();
  if (!client) return;
  const { error } = await client.auth.signOut();
  if (error) throw error;
}

export async function subscribeToAuth(onUser: (user: User | null) => void): Promise<() => void> {
  const client = await getAuthClient();
  if (!client) return () => undefined;
  const { data } = client.auth.onAuthStateChange((_event, session) => onUser(session?.user ?? null));
  return () => data.subscription.unsubscribe();
}
