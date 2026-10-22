"use client";
import { useParams } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import InvestigationDetail from "@/components/InvestigationDetail";

export default function InvestigationPage() {
  const params = useParams<{ id: string }>();
  return <AuthGuard><InvestigationDetail id={params.id} /></AuthGuard>;
}
