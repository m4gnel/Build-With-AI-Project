import { motion } from 'framer-motion';
import { Card } from '@/components/ui/card';
import { LineChart, AlertTriangle, Route } from 'lucide-react';

const features = [
  {
    title: "Predict Demand with AI",
    description: "Supervised learning models parse historical patterns to forecast supply chain demand with up to 95% accuracy.",
    icon: <LineChart className="w-12 h-12 text-[#8A2BE2]" />,
    image: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop"
  },
  {
    title: "Detect Risks Before They Happen",
    description: "Our Gemini RAG Engine scans weather APIs, news, and history to flag delivery disruptions instantly.",
    icon: <AlertTriangle className="w-12 h-12 text-[#FF7A00]" />,
    image: "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop"
  },
  {
    title: "Optimize Routes in Real-Time",
    description: "Graph algorithms dynamically compute the fastest, safest delivery paths to mitigate active failures.",
    icon: <Route className="w-12 h-12 text-[#00F5FF]" />,
    image: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop"
  }
];

export default function FeaturesChess() {
  return (
    <section id="features" className="py-32 px-4 max-w-7xl mx-auto relative z-20">
      <div className="text-center mb-24">
        <h2 className="text-5xl md:text-6xl font-heading font-bold italic mb-6">Intelligence Built In.</h2>
        <p className="text-white/50 text-xl font-sans max-w-2xl mx-auto">The smart way to handle supply chain chaos.</p>
      </div>

      <div className="space-y-32">
        {features.map((feature, i) => (
          <motion.div 
            key={i}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className={`flex flex-col md:flex-row items-center gap-16 ${i % 2 !== 0 ? 'md:flex-row-reverse' : ''}`}
          >
            {/* Text Side */}
            <div className="flex-1 space-y-6">
              <div className="w-20 h-20 rounded-2xl bg-glass border border-glass-border flex items-center justify-center shadow-glass backdrop-blur-md">
                {feature.icon}
              </div>
              <h3 className="text-4xl font-heading font-bold italic">{feature.title}</h3>
              <p className="text-white/60 text-lg leading-relaxed">{feature.description}</p>
            </div>

            {/* Visual Side */}
            <div className="flex-1 w-full">
              <Card className="overflow-hidden p-0 border-white/10 group relative h-[350px]">
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent z-10 opacity-80"></div>
                <img 
                  src={feature.image} 
                  alt={feature.title}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 opacity-60 mix-blend-screen"
                />
              </Card>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  )
}
