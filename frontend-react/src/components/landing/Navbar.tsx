import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { BrainCircuit } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Navbar() {
  return (
    <motion.nav 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4 pointer-events-none"
    >
      <div className="glass-pill pointer-events-auto flex items-center gap-8 px-6 py-3">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-6 h-6 text-primary" />
          <span className="font-heading text-xl text-white font-bold italic tracking-wide">SupplyChain AI</span>
        </div>

        {/* Links */}
        <div className="hidden md:flex items-center gap-6 text-sm font-medium text-white/70">
          <a href="#features" className="hover:text-primary transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-primary transition-colors">AI Engine</a>
          <a href="#stats" className="hover:text-primary transition-colors">Performance</a>
        </div>

        {/* CTA */}
        <Link to="/dashboard">
          <Button variant="default" size="sm" className="font-bold">
            Launch Dashboard
          </Button>
        </Link>
      </div>
    </motion.nav>
  )
}
