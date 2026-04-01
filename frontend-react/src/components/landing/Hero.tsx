import { motion } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { Link } from 'react-router-dom';
import { Activity } from 'lucide-react';

export default function Hero() {
  return (
    <section className="relative w-full h-[1000px] flex flex-col items-center justify-center overflow-hidden">
      {/* Video Background */}
      <div className="absolute inset-0 z-0 w-full h-full">
        <div className="absolute inset-0 bg-black/70 z-10 backdrop-blur-[2px]"></div>
        <video 
          autoPlay 
          loop 
          muted 
          playsInline
          className="w-full h-full object-cover opacity-50"
          src="https://cdn.pixabay.com/video/2020/05/25/40141-424840810_tiny.mp4"
        />
        {/* Glow overlay */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-primary/20 blur-[120px] rounded-full z-10 pointer-events-none"></div>
      </div>

      <div className="relative z-20 flex flex-col items-center text-center px-4 max-w-5xl mt-24">
        {/* Badge */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/30 bg-primary/10 text-primary text-sm font-semibold mb-8"
        >
          <Activity className="w-4 h-4" />
          <span>AI Logistics Intelligence</span>
        </motion.div>

        {/* Heading */}
        <motion.h1 
          className="text-6xl md:text-8xl font-heading font-extrabold italic tracking-tight text-white leading-[1.1] mb-6"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
          }}
        >
          {["Predict.", "Optimize.", "Deliver", "Smarter."].map((word, i) => (
            <motion.span 
              key={i} 
              className={i === 3 ? "text-primary ml-4" : "mr-4"}
              variants={{
                hidden: { opacity: 0, filter: "blur(10px)", y: 20 },
                visible: { opacity: 1, filter: "blur(0px)", y: 0 }
              }}
            >
              {word}
            </motion.span>
          ))}
        </motion.h1>

        {/* Subtext */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-lg md:text-xl text-white/60 font-sans max-w-2xl mb-12"
        >
          An AI-powered system that predicts disruptions, optimizes routes, and makes intelligent supply chain decisions in real time.
        </motion.p>

        {/* CTAs */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="flex items-center gap-6"
        >
          <Link to="/dashboard">
            <Button size="lg" className="text-lg shadow-glow">Launch System</Button>
          </Link>
          <a href="#how-it-works">
            <Button variant="outline" size="lg" className="text-lg">Watch Simulation</Button>
          </a>
        </motion.div>
      </div>
    </section>
  )
}
