export default function LoadingState() {
  return (
    <div className="loading-state" role="status" aria-label="Loading">
      <div className="loading-spinner" aria-hidden="true" />
      <p>Loading data...</p>
    </div>
  );
}
