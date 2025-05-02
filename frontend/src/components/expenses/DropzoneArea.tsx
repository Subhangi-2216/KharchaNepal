import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, ScanLine, FileText, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface DropzoneAreaProps {
  onFileAccepted: (file: File) => void;
  isLoading: boolean;
  maxSize?: number; // in bytes
  acceptedFileTypes?: string[];
  className?: string;
}

const DropzoneArea: React.FC<DropzoneAreaProps> = ({
  onFileAccepted,
  isLoading,
  maxSize = 5 * 1024 * 1024, // 5MB default
  acceptedFileTypes = ['image/jpeg', 'image/png', 'image/webp'],
  className,
}) => {
  const [previewFile, setPreviewFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0];

        // Create preview
        const objectUrl = URL.createObjectURL(file);
        setPreviewFile(file);
        setPreviewUrl(objectUrl);

        // Pass file to parent component
        onFileAccepted(file);
      }
    },
    [onFileAccepted]
  );

  const clearPreview = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewFile(null);
    setPreviewUrl(null);
  };

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
  } = useDropzone({
    onDrop,
    accept: acceptedFileTypes.reduce((acc, type) => {
      acc[type] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize,
    disabled: isLoading,
    multiple: false,
  });

  return (
    <div className={cn('w-full', className)}>
      {previewFile && previewUrl ? (
        <div className="relative rounded-md border-2 border-dashed border-primary/50 bg-primary/5 p-6 text-center">
          <div className="absolute right-2 top-2">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={clearPreview}
              disabled={isLoading}
              className="h-6 w-6 rounded-full hover:bg-destructive/10 hover:text-destructive"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex flex-col items-center justify-center gap-3">
            <div className="overflow-hidden rounded-md border bg-background p-1 shadow-sm">
              <img
                src={previewUrl}
                alt="Receipt preview"
                className="mx-auto max-h-48 max-w-full object-contain"
              />
            </div>
            <div className="text-sm text-muted-foreground">
              {previewFile.name} ({(previewFile.size / 1024).toFixed(1)} KB)
            </div>
            {isLoading ? (
              <div className="flex items-center gap-2 text-sm font-medium text-primary">
                <ScanLine className="h-4 w-4 animate-pulse" />
                Processing receipt...
              </div>
            ) : (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => onFileAccepted(previewFile)}
              >
                <ScanLine className="mr-2 h-4 w-4" />
                Scan Again
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div
          {...getRootProps()}
          className={cn(
            'flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-8 text-center transition-colors',
            isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25',
            isDragAccept && 'border-primary bg-primary/5',
            isDragReject && 'border-destructive bg-destructive/5',
            isLoading && 'pointer-events-none opacity-60',
            'hover:border-primary hover:bg-primary/5'
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center gap-4">
            <div className={cn(
              "rounded-full p-3",
              isDragActive ? "bg-primary/20" : "bg-muted"
            )}>
              {isLoading ? (
                <ScanLine className="h-6 w-6 animate-pulse text-primary" />
              ) : (
                <Upload className={cn(
                  "h-6 w-6",
                  isDragActive ? "text-primary" : "text-muted-foreground"
                )} />
              )}
            </div>
            <div className="space-y-1 text-center">
              <p className="text-sm font-medium">
                {isLoading ? 'Processing receipt...' : 'Drag & drop receipt image here'}
              </p>
              <p className="text-xs text-muted-foreground">
                {isLoading
                  ? 'Please wait while we extract data from your receipt'
                  : `JPG, PNG or WebP (max. ${maxSize / 1024 / 1024}MB)`}
              </p>
            </div>
            {!isLoading && (
              <Button type="button" variant="secondary" size="sm">
                <FileText className="mr-2 h-4 w-4" />
                Select File
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DropzoneArea;