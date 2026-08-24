export function ApiMessage({
  title,
  message,
}: {
  title: string;
  message: string;
}) {
  return (
    <div className="card apiMessage" role="status">
      <h3>{title}</h3>
      <p className="muted">{message}</p>
    </div>
  );
}
