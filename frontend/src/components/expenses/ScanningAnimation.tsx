import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ScanningAnimationProps {
  isScanning: boolean;
  onScanComplete?: () => void;
  className?: string;
}

const ScanningAnimation: React.FC<ScanningAnimationProps> = ({
  isScanning,
  onScanComplete,
  className
}) => {
  const [scanPosition, setScanPosition] = useState(0);

  useEffect(() => {
    if (!isScanning) {
      setScanPosition(0);
      return;
    }

    let animationFrame: number;
    let startTime: number;

    // Use a shorter scan duration for better user experience
    const scanDuration = 3000; // 3 seconds for full scan

    // Track if we've triggered scan complete
    let triggeredScanComplete = false;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = (timestamp - startTime) / scanDuration;

      if (progress <= 1) {
        setScanPosition(progress);

        // Trigger scan complete at 80% of the animation
        // This will allow field population to start while animation is still visible
        if (progress >= 0.8 && !triggeredScanComplete) {
          triggeredScanComplete = true;
          console.log("Scanning animation at 80%, triggering scan complete");
          onScanComplete?.();
        }

        animationFrame = requestAnimationFrame(animate);
      } else {
        setScanPosition(1);
        if (!triggeredScanComplete) {
          console.log("Scanning animation complete, triggering scan complete");
          onScanComplete?.();
        }
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrame);
    };
  }, [isScanning, onScanComplete]);

  if (!isScanning && scanPosition === 0) {
    return null;
  }

  return (
    <div className={cn("relative w-full h-full overflow-hidden", className)}>
      <motion.div
        className="absolute left-0 w-full h-1 bg-primary opacity-70"
        style={{
          top: `${scanPosition * 100}%`,
          boxShadow: '0 0 10px 2px rgba(var(--primary), 0.5), 0 0 20px 10px rgba(var(--primary), 0.2)'
        }}
      />
      <motion.div
        className="absolute left-0 w-full h-20 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none"
        style={{ top: `${scanPosition * 100}%`, translateY: '-50%' }}
      />
    </div>
  );
};

export default ScanningAnimation;
