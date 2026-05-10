interface Props { message: string; onDismiss?: () => void; }

export default function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className="bg-red-900/60 border border-red-500 rounded-lg p-4 flex items-start gap-3">
      <span className="text-red-400 text-xl shrink-0">⚠</span>
      <p className="text-red-200 text-sm flex-1">{message}</p>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-400 hover:text-red-200 shrink-0">✕</button>
      )}
    </div>
  );
}
