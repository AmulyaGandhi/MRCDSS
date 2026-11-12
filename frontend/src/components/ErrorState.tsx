interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="error-state" role="alert">
      <p className="error-message">{message}</p>
      <button type="button" className="filter-clear" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
