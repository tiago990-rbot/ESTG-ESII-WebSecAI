export default function StatCard({ title, value, description }: { title: string; value: string | number; description?: string }) {
  return (
    <div className="statCard">
      <span>{title}</span>
      <strong>{value}</strong>
      {description && <small>{description}</small>}
    </div>
  );
}
