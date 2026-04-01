import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface DemoOverlayProps {
  isDemoRunning: boolean;
}

const STEPS = [
  "Fetching Historical Models...",
  "Running Demand Predictor...",
  "Clustering Supplier Risk Profiles...",
  "Activating Route Optimization Engine...",
  "Retrieving RAG Context & Generating Decisions..."
];

export function DemoOverlay({ isDemoRunning }: DemoOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!isDemoRunning) {
      setCurrentStep(0);
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 1200);

    return () => clearInterval(interval);
  }, [isDemoRunning]);

  return (
    <AnimatePresence>
      {isDemoRunning && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20, transition: { delay: 0.5 } }}
          className="fixed top-24 left-1/2 -translate-x-1/2 z-50 bg-black/80 backdrop-blur-md border border-primary/30 p-6 rounded-2xl shadow-[0_0_30px_rgba(0,245,255,0.2)] w-[400px]"
        >
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <h3 className="font-heading italic text-xl text-white m-0">Neural Link Executing...</h3>
          </div>
          <div className="space-y-3">
            {STEPS.map((step, idx) => (
              <div 
                key={idx} 
                className={`text-sm transition-all duration-300 font-sans flex items-center space-x-2 
                  ${idx < currentStep ? 'text-green-400' : idx === currentStep ? 'text-primary animate-pulse' : 'text-gray-600'}`}
              >
                <div className={`w-2 h-2 rounded-full ${idx < currentStep ? 'bg-green-400' : idx === currentStep ? 'bg-primary' : 'bg-gray-700'}`} />
                <span>{step}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
