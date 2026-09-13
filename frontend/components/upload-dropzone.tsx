"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function UploadDropzone({ onFileSelected, disabled }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0];
      if (file && (file.type === "image/jpeg" || file.type === "image/png")) {
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragActive(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed px-6 py-10 text-center transition-colors",
        dragActive ? "border-cyan bg-cyan/5" : "border-line hover:border-ink-faint",
        disabled && "pointer-events-none opacity-40"
      )}
    >
      <UploadCloud size={22} className="text-ink-faint" strokeWidth={1.5} />
      <p className="font-body text-sm text-ink-primary">
        Drop an MRI slice here, or click to browse
      </p>
      <p className="font-mono text-xs text-ink-faint">JPEG or PNG · up to 20 MB</p>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
}
