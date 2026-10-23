export type User = {
  id: number;
  username: string;
  email: string;
  created_at: string;
};

export type Finding = {
  id: number;
  title: string;
  severity: string;
  category: string;
  description: string;
  recommendation: string;
};

export type ScanListItem = {
  id: number;
  url: string;
  domain: string;
  created_at: string;
  score: number;
  risk_level: string;
  summary: string;
  findings_count: number;
};

export type ScanDetail = ScanListItem & {
  details: Record<string, any>;
  findings: Finding[];
};

export type ScanStats = {
  total_scans: number;
  average_score: number;
  best_score: number | null;
  worst_score: number | null;
  last_scan_date: string | null;
  top_domains: { domain: string; count: number }[];
};

export type ScanComparison = {
  current_scan_id: number;
  previous_scan_id: number | null;
  current_score: number;
  previous_score: number | null;
  score_delta: number | null;
  current_findings_count: number;
  previous_findings_count: number | null;
  findings_delta: number | null;
  message: string;
};
