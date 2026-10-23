import type { Metadata } from "next";
import NavBar from "@/components/NavBar";
import { AuthConfigurationProvider } from "@/components/AuthConfiguration";
import "./globals.css";
import "./workbench.css";

export const metadata: Metadata = {
  title: "WebSecAI",
  description: "Threat Intelligence, OSINT e análise de segurança com evidências",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-PT">
      <body>
        <AuthConfigurationProvider>
          <NavBar />
          {children}
        </AuthConfigurationProvider>
      </body>
    </html>
  );
}
