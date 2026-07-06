import { useState, type FormEvent } from "react";
import { ArrowRight, LockKeyhole, Mail, X } from "lucide-react";
import { sendMagicLink, signInWithGoogle } from "./auth";

export function AuthDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  if (!open) return null;

  const run = async (action: () => Promise<void>) => {
    setBusy(true); setStatus("");
    try { await action(); }
    catch (error) { setStatus(error instanceof Error ? error.message : "Unable to sign in"); }
    finally { setBusy(false); }
  };
  const submitEmail = (event: FormEvent) => {
    event.preventDefault();
    void run(async () => { await sendMagicLink(email); setStatus("Check your email for a secure sign-in link."); });
  };

  return <div className="auth-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title">
      <button className="auth-close" onClick={onClose} aria-label="Close sign in"><X size={20}/></button>
      <div className="auth-mark"><LockKeyhole size={22}/></div>
      <h2 id="auth-title">Save your shortlist.</h2>
      <p>Sign in only when you want your matches, tradeoffs, and alerts to follow you across devices.</p>
      <button className="google-button" aria-label="Continue with Google" disabled={busy} onClick={() => void run(signInWithGoogle)}><span aria-hidden="true">G</span> Continue with Google</button>
      <div className="auth-divider"><span>or use email</span></div>
      <form onSubmit={submitEmail}>
        <label htmlFor="auth-email">Email address</label>
        <div className="auth-email-row"><Mail size={19}/><input id="auth-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required/><button disabled={busy} aria-label="Send magic link"><ArrowRight size={19}/></button></div>
      </form>
      {status ? <p className="auth-status" role="status">{status}</p> : null}
      <small>No password to remember. Financial values remain local unless you explicitly save them.</small>
    </section>
  </div>;
}
