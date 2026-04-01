import { Link } from 'react-router-dom';
import Navbar from '@/components/landing/Navbar';
import Hero from '@/components/landing/Hero';
import FeaturesChess from '@/components/landing/FeaturesChess';
import { motion } from 'framer-motion';
import { Brain, Route, AlertTriangle, Database } from 'lucide-react';
import { Card } from '@/components/ui/card';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-primary/30">
      <Navbar />
      
      <main>
        <Hero />
        
        {/* Partners Marquee */}
        <section className="py-20 border-y border-white/5 overflow-hidden bg-black/50 relative">
          <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-black to-transparent z-10"></div>
          <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-black to-transparent z-10"></div>
          <motion.div 
            animate={{ x: [0, -1000] }}
            transition={{ repeat: Infinity, ease: "linear", duration: 20 }}
            className="flex items-center gap-32 whitespace-nowrap opacity-40 font-heading text-3xl italic tracking-widest"
          >
            {["LOGISTICS INC.", "GLOBAL RETAIL", "MANUFACTURING CO.", "E-COMMERCE M", "GOV SYSTEMS", "LOGISTICS INC.", "GLOBAL RETAIL", "MANUFACTURING CO."].map((p,i) => (
              <span key={i}>{p}</span>
            ))}
          </motion.div>
        </section>

        <FeaturesChess />

        {/* Features Grid */}
        <section className="py-32 px-4 max-w-7xl mx-auto">
          <h2 className="text-center text-4xl md:text-5xl font-heading font-bold italic mb-16">The Architecture</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { i: <Brain className="w-8 h-8 text-primary"/>, t: "AI Intelligence", d: "ML & RAG powered making smart micro-decisions." },
              { i: <Route className="w-8 h-8 text-secondary"/>, t: "Dynamic Routing", d: "Adapts to weather and port delays instantly." },
              { i: <AlertTriangle className="w-8 h-8 text-accent"/>, t: "Risk Prediction", d: "Advanced disruption tracking system." },
              { i: <Database className="w-8 h-8 text-primary"/>, t: "Data-Driven", d: "Insights mapped via K-Means clustering." }
            ].map((f, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1, duration: 0.5 }}
                viewport={{ once: true }}
              >
                <Card className="h-full hover:bg-[rgba(255,255,255,0.05)] transition-colors cursor-default">
                  <div className="p-6 space-y-4">
                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center border border-white/10">{f.i}</div>
                    <h3 className="text-xl font-heading italic font-bold">{f.t}</h3>
                    <p className="text-white/50 text-sm leading-relaxed">{f.d}</p>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Stats */}
        <section id="stats" className="py-24 relative overflow-hidden">
          <div className="absolute inset-0 bg-primary/5 blur-[150px]"></div>
          <div className="max-w-7xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-8 divide-x divide-white/10 text-center relative z-10">
            {[
              { v: "95%", l: "Delivery Accuracy" },
              { v: "3x", l: "Faster Decisions" },
              { v: "40%", l: "Cost Reduction" },
              { v: "< 2s", l: "Real-Time Adjustments" },
            ].map((s,i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="space-y-2"
              >
                <div className="text-5xl font-heading italic font-bold text-glow text-white">{s.v}</div>
                <div className="text-sm uppercase tracking-widest text-white/50">{s.l}</div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Footer CTA */}
        <footer className="py-40 text-center relative border-t border-white/5">
           <div className="max-w-3xl mx-auto px-4 space-y-8 relative z-20">
             <h2 className="text-5xl md:text-7xl font-heading italic font-bold tracking-tight">The Future Starts Here.</h2>
             <p className="text-xl text-white/50 font-sans">Experience AI-driven logistics intelligence.</p>
             <div className="pt-8">
               <Link to="/dashboard">
                 <button className="glass-pill text-xl font-bold italic font-heading tracking-wide px-12 py-4 hover:shadow-glow transition-all duration-300">
                   Launch Dashboard →
                 </button>
               </Link>
             </div>
           </div>
           {/* Background decorative glow */}
           <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-[400px] bg-secondary/10 blur-[120px] rounded-full pointer-events-none"></div>
        </footer>
      </main>
    </div>
  )
}
