import type { ScanDetail } from "@/lib/types";
import { formatDate } from "@/lib/scan-helpers";

function yesNo(value: boolean | null | undefined) {
  if (value === true) return { label: "Sim", className: "status ok" };
  if (value === false) return { label: "Não", className: "status bad" };
  return { label: "N/A", className: "status neutral" };
}

function StatusBadge({ value }: { value: boolean | null | undefined }) {
  const status = yesNo(value);
  return <span className={status.className}>{status.label}</span>;
}

function InfoRow({ label, value }: { label: string; value: any }) {
  const text = value === null || value === undefined || value === "" ? "-" : String(value);
  return (
    <div className="infoRow">
      <span>{label}</span>
      <strong title={text}>{text}</strong>
    </div>
  );
}

function CheckRow({ label, value, help }: { label: string; value: boolean | null | undefined; help?: string }) {
  return (
    <div className="checkRow">
      <div>
        <strong>{label}</strong>
        {help && <small>{help}</small>}
      </div>
      <StatusBadge value={value} />
    </div>
  );
}

function ErrorBox({ error }: { error?: string | null }) {
  if (!error) return null;
  return <p className="miniError"><strong>Erro:</strong> {error}</p>;
}

export default function AnalysisDashboard({ scan }: { scan: ScanDetail }) {
  const details = scan.details || {};
  const dns = details.dns || {};
  const tls = details.tls || {};
  const http = details.http || {};
  const headers = http.headers || {};
  const cookies = http.cookies || {};
  const publicFiles = details.public_files || {};

  const headerLabels: { key: string; label: string; help: string }[] = [
    { key: "hsts", label: "HSTS", help: "Força o browser a usar HTTPS." },
    { key: "csp", label: "Content-Security-Policy", help: "Ajuda a reduzir XSS e injeção de scripts." },
    { key: "x_content_type_options", label: "X-Content-Type-Options", help: "Reduz interpretação indevida de ficheiros." },
    { key: "referrer_policy", label: "Referrer-Policy", help: "Controla informação enviada no referrer." },
    { key: "permissions_policy", label: "Permissions-Policy", help: "Limita permissões do browser." },
    { key: "x_frame_options", label: "X-Frame-Options", help: "Ajuda contra clickjacking." },
  ];

  return (
    <div className="analysisDashboard">
      <section className="analysisHero card">
        <div>
          <span className="eyebrow">Resultado da análise</span>
          <h2>{scan.domain}</h2>
          <p className="muted">Analisado em {formatDate(scan.created_at)}</p>
        </div>
        <div className="heroMeta">
          <InfoRow label="URL normalizado" value={details.normalized_url || scan.url} />
          <InfoRow label="IP principal" value={dns.resolved_ip} />
          <InfoRow label="URL final" value={http.final_url} />
        </div>
      </section>

      <div className="analysisGrid">
        <section className="miniCard">
          <div className="miniCardTitle">
            <span className="iconBubble">🌐</span>
            <div>
              <h3>DNS</h3>
              <p>Resolução do domínio e endereços encontrados.</p>
            </div>
          </div>
          <CheckRow label="Domínio resolveu" value={dns.dns_ok} />
          <CheckRow label="Tem IPv6" value={dns.has_ipv6} />
          <InfoRow label="IP principal" value={dns.resolved_ip} />
          <InfoRow label="Endereços" value={(dns.addresses || []).join(", ")} />
          <ErrorBox error={dns.error} />
        </section>

        <section className="miniCard">
          <div className="miniCardTitle">
            <span className="iconBubble">🔒</span>
            <div>
              <h3>TLS / Certificado</h3>
              <p>HTTPS, validade e certificado digital.</p>
            </div>
          </div>
          <CheckRow label="HTTPS suportado" value={tls.https_supported} />
          <CheckRow label="Certificado válido" value={tls.tls_ok} />
          <CheckRow label="Hostname corresponde" value={tls.hostname_match} />
          <CheckRow label="Certificado dentro da validade" value={tls.expired === null || tls.expired === undefined ? null : !tls.expired} help="Sim significa que o certificado ainda não expirou." />
          <InfoRow label="Emissor" value={tls.issuer} />
          <InfoRow label="Válido até" value={formatDate(tls.valid_to)} />
          <InfoRow label="Dias restantes" value={tls.days_remaining} />
          <ErrorBox error={tls.error} />
        </section>

        <section className="miniCard">
          <div className="miniCardTitle">
            <span className="iconBubble">↪️</span>
            <div>
              <h3>HTTP / HTTPS</h3>
              <p>Resposta do site e redirecionamento.</p>
            </div>
          </div>
          <CheckRow label="HTTP respondeu" value={http.http_ok} />
          <CheckRow label="HTTPS respondeu" value={http.https_ok} />
          <CheckRow label="HTTP redireciona para HTTPS" value={http.http_to_https_redirect} />
          <InfoRow label="Status code" value={http.status_code} />
          <InfoRow label="URL final" value={http.final_url} />
          <ErrorBox error={http.error} />
        </section>

        <section className="miniCard">
          <div className="miniCardTitle">
            <span className="iconBubble">🧱</span>
            <div>
              <h3>Headers de segurança</h3>
              <p>Proteções recomendadas no browser. “Não” significa que o header não foi detetado nesta resposta, não necessariamente que o site está vulnerável.</p>
            </div>
          </div>
          {headerLabels.map((item) => (
            <CheckRow key={item.key} label={item.label} value={headers[item.key]} help={item.help} />
          ))}
          <InfoRow label="Header Server" value={headers.server_header ? `Exposto: ${headers.server_header}` : "Não exposto"} />
          <InfoRow label="X-Powered-By" value={headers.x_powered_by ? `Exposto: ${headers.x_powered_by}` : "Não exposto"} />
        </section>

        <section className="miniCard">
          <div className="miniCardTitle">
            <span className="iconBubble">🍪</span>
            <div>
              <h3>Cookies</h3>
              <p>Atributos básicos de segurança dos cookies recebidos nesta resposta.</p>
            </div>
          </div>
          <CheckRow label="Existem cookies" value={cookies.has_cookies} />
          <InfoRow label="Total de cookies" value={cookies.total} />
          <CheckRow label="Todos com Secure" value={cookies.all_secure} help="Cookies só enviados por HTTPS." />
          <CheckRow label="Todos com HttpOnly" value={cookies.all_httponly} help="Bloqueia acesso por JavaScript." />
          <CheckRow label="Todos com SameSite" value={cookies.all_samesite} help="Ajuda a reduzir CSRF." />
        </section>

        <section className="miniCard">
          <div className="miniCardTitle">
            <span className="iconBubble">📄</span>
            <div>
              <h3>Ficheiros públicos</h3>
              <p>Ficheiros comuns expostos publicamente.</p>
            </div>
          </div>
          <CheckRow label="robots.txt encontrado" value={publicFiles.robots_txt_found} />
          <InfoRow label="Status robots.txt" value={publicFiles.robots_status_code} />
          <CheckRow label="sitemap.xml encontrado" value={publicFiles.sitemap_xml_found} />
          <InfoRow label="Status sitemap.xml" value={publicFiles.sitemap_status_code} />
          <ErrorBox error={publicFiles.robots_error} />
          <ErrorBox error={publicFiles.sitemap_error} />
        </section>
      </div>
    </div>
  );
}
