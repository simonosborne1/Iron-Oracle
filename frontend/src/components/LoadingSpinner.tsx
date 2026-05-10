interface Props { label?: string; }

export default function LoadingSpinner({ label }: Props) {
  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <div className="w-10 h-10 border-4 border-orange-500 border-t-transparent rounded-full animate-spin" />
      {label && <p className="text-gray-400 text-sm">{label}</p>}
    </div>
  );
}
