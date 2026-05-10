import { useEffect, useRef, useState } from "react";
import { useCamera } from "../hooks/useCamera";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

interface Props {
  onCapture: (blob: Blob) => void;
  isProcessing: boolean;
}

export default function CameraCapture({ onCapture, isProcessing }: Props) {
  const { videoRef, stream, error, start, stop, capture } = useCamera();
  const [preview, setPreview] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    start();
    return () => stop();
  }, [start, stop]);

  async function handleCapture() {
    const blob = await capture();
    if (!blob) return;
    setCapturedBlob(blob);
    setPreview(URL.createObjectURL(blob));
  }

  function handleRetake() {
    setPreview(null);
    setCapturedBlob(null);
  }

  function handleUse() {
    if (capturedBlob) onCapture(capturedBlob);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setCapturedBlob(file);
    setPreview(URL.createObjectURL(file));
  }

  if (isProcessing) {
    return <LoadingSpinner label="Reading serial plate..." />;
  }

  return (
    <div className="flex flex-col gap-4">
      {error && <ErrorBanner message={error} />}

      {!preview ? (
        <div className="relative rounded-xl overflow-hidden bg-gray-900 aspect-video">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          {/* Guide overlay */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="border-2 border-orange-400/70 rounded-lg w-4/5 h-1/2" />
          </div>
          <p className="absolute bottom-3 left-0 right-0 text-center text-xs text-gray-300">
            Frame the serial plate within the box
          </p>
        </div>
      ) : (
        <div className="rounded-xl overflow-hidden bg-gray-900">
          <img src={preview} alt="Captured plate" className="w-full object-contain max-h-80" />
        </div>
      )}

      <div className="flex gap-3">
        {!preview ? (
          <>
            {stream && (
              <button
                onClick={handleCapture}
                className="flex-1 bg-orange-500 hover:bg-orange-600 active:bg-orange-700 text-white font-semibold py-4 rounded-xl text-lg transition-colors"
              >
                Capture
              </button>
            )}
            <button
              onClick={() => fileRef.current?.click()}
              className="px-4 py-4 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl transition-colors"
            >
              Upload
            </button>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
          </>
        ) : (
          <>
            <button
              onClick={handleRetake}
              className="flex-1 py-4 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl transition-colors"
            >
              Retake
            </button>
            <button
              onClick={handleUse}
              className="flex-1 py-4 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl transition-colors"
            >
              Analyse
            </button>
          </>
        )}
      </div>
    </div>
  );
}
