"use client";
import { FormEvent, useState } from "react";
import { Evidence, Investigation, investigations, errorMessage, dateLabel } from "@/lib/investigations";
const statusNames: Record<string, string> = { unreviewed: "Por rever", reviewed: "Revista", contested: "Contestada" };
const identityNames: Record<string, string> = { unverified: "Por verificar", matches: "Corresponde segundo a revisão", does_not_match: "Não corresponde", uncertain: "Incerta" };
export default function EvidenceReviewForm({ entry, investigationId, onReviewed }: { entry: Evidence; investigationId: string; onReviewed: (data: Investigation) => void }) {
  const [status, setStatus] = useState(entry.review?.status || "unreviewed");
  const [identity, setIdentity] = useState(entry.review?.identity_status || "unverified");
  const [note, setNote] = useState(entry.review?.note || "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      const result = await investigations.review(investigationId, entry.id, { status, identity_status: identity, note, previous_review_id: entry.review?.id ?? null });
      onReviewed(result); setMessage("Revisão guardada no histórico. A síntese anterior pode requerer atualização.");
    } catch (error) { setMessage(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <details className="wb-disclosure"><summary>Revisão humana · {statusNames[entry.review?.status || "unreviewed"]}</summary><p className="muted smallNote">Anotação do autor da investigação. Rever não confirma intrusão nem valida automaticamente a identidade.</p>{entry.review && !entry.review.is_current ? <p className="notice">A evidência mudou desde a última revisão. Revê o conteúdo atual.</p> : null}<form onSubmit={submit} className="form"><label htmlFor={"review-status-" + entry.id}>Estado da revisão</label><select id={"review-status-" + entry.id} className="input" value={status} onChange={(event) => setStatus(event.target.value)}>{Object.entries(statusNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select><label htmlFor={"review-identity-" + entry.id}>Relação com a organização</label><select id={"review-identity-" + entry.id} className="input" value={identity} onChange={(event) => setIdentity(event.target.value)}>{Object.entries(identityNames).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select><label htmlFor={"review-note-" + entry.id}>Notas e fundamento</label><textarea id={"review-note-" + entry.id} className="input" maxLength={2000} value={note} onChange={(event) => setNote(event.target.value)} /><p className="muted smallNote">Não incluir passwords, chaves ou dados pessoais desnecessários.</p><button className="btn" type="submit" disabled={busy}>{busy ? "A guardar…" : "Guardar revisão"}</button><p role="status">{message}</p></form>{entry.reviews?.length ? <details><summary>Histórico de revisões ({entry.reviews.length})</summary><ol>{entry.reviews.map((review) => <li key={review.id}><p>{statusNames[review.status]} · {identityNames[review.identity_status]} · {review.author} · {dateLabel(review.created_at)}{review.is_current ? "" : " · Conteúdo anterior"}</p><p>{review.note}</p></li>)}</ol></details> : null}</details>;
}
