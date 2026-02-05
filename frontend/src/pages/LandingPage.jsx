import { useState, useRef } from "react";
import { motion, useInView } from "framer-motion";
import { toast } from "sonner";
import axios from "axios";
import {
  CreditCard,
  Scale,
  Heart,
  BarChart3,
  Image,
  Bell,
  ArrowRight,
  Camera,
  Sparkles,
  ChevronDown,
  Share2,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import ShareModal from "../components/ShareModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

// Feature data
const features = [
  {
    icon: CreditCard,
    title: "Seamless Payments",
    description: "Stripe-powered entry fees and instant winner payouts. No spreadsheets.",
    color: "violet",
    span: false,
  },
  {
    icon: Scale,
    title: "Fair Judging",
    description: "Blind panels, weighted scores, public voting. You pick the method.",
    color: "violet",
    span: false,
  },
  {
    icon: Heart,
    title: "Charity Integration",
    description: "Donate 5-50% of fees to 100+ verified nonprofits. Instant tax receipts.",
    color: "emerald",
    span: false,
  },
  {
    icon: Image,
    title: "Beautiful Galleries",
    description: "Stunning, responsive showcases for photographers. Your work deserves the spotlight.",
    color: "amber",
    span: true,
    image: "https://images.unsplash.com/photo-1764922168474-8048361bc764?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBhcnQlMjBnYWxsZXJ5JTIwaW50ZXJpb3IlMjBtaW5pbWFsaXN0fGVufDB8fHx8MTc3MDMyMjYxMnww&ixlib=rb-4.1.0&q=85&w=800",
  },
  {
    icon: BarChart3,
    title: "Real-time Dashboard",
    description: "Track entries, revenue, engagement. Full transparency.",
    color: "violet",
    span: false,
  },
  {
    icon: Bell,
    title: "Smart Notifications",
    description: "Automated updates, on-brand. Zero manual work.",
    color: "violet",
    span: false,
  },
];

// Impact stats
const impactStats = [
  { value: "5-50%", label: "Customizable donation" },
  { value: "100+", label: "Verified nonprofits" },
  { value: "Instant", label: "Tax receipts & reports" },
];

// AnimatedSection component
const AnimatedSection = ({ children, className = "", delay = 0 }) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
      variants={fadeInUp}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

// Feature Card component
const FeatureCard = ({ feature, index }) => {
  const colorClasses = {
    violet: "feature-card",
    emerald: "feature-card feature-card-emerald",
    amber: "feature-card feature-card-amber",
  };

  const iconColors = {
    violet: "text-purple-400",
    emerald: "text-emerald-400",
    amber: "text-amber-400",
  };

  return (
    <motion.div
      variants={fadeInUp}
      className={`${colorClasses[feature.color]} rounded-2xl p-8 relative overflow-hidden ${
        feature.span ? "bento-span-2 min-h-[320px]" : ""
      }`}
    >
      {feature.image && (
        <div className="absolute inset-0 opacity-20">
          <img
            src={feature.image}
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/80 to-transparent" />
        </div>
      )}
      <div className="relative z-10">
        <div className={`feature-card-icon w-14 h-14 rounded-xl flex items-center justify-center mb-6`}>
          <feature.icon className={`w-6 h-6 ${iconColors[feature.color]}`} strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-semibold mb-3 text-white">{feature.title}</h3>
        <p className="text-gray-400 text-base leading-relaxed">{feature.description}</p>
      </div>
    </motion.div>
  );
};

// Main Landing Page
export default function LandingPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [hasJoinedWaitlist, setHasJoinedWaitlist] = useState(false);
  const featuresRef = useRef(null);

  const scrollToFeatures = () => {
    featuresRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToWaitlist = () => {
    document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth" });
  };

  const isValidEmail = (email) => {
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailPattern.test(email);
  };

  const handleWaitlistSubmit = async (e) => {
    e.preventDefault();
    const trimmedEmail = email.trim();
    
    if (!trimmedEmail) {
      toast.error("Please enter your email address");
      return;
    }
    
    if (!isValidEmail(trimmedEmail)) {
      toast.error("Please enter a valid email address");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await axios.post(`${API}/waitlist`, { email: trimmedEmail });
      if (response.data.success) {
        toast.success(response.data.message);
        setEmail("");
        setHasJoinedWaitlist(true);
        // Show share modal after successful signup
        setTimeout(() => setShowShareModal(true), 500);
      }
    } catch (error) {
      if (error.response?.status === 422) {
        toast.error("Please enter a valid email address");
      } else {
        toast.error("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#050505] text-white">
      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col justify-center overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1763356766882-4e6fbe10412c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1ODR8MHwxfHNlYXJjaHwxfHxkcmFtYXRpYyUyMGxhbmRzY2FwZSUyMHBob3RvZ3JhcGh5JTIwZGFyayUyMG1vb2R5fGVufDB8fHx8MTc3MDMyMjYwNHww&ixlib=rb-4.1.0&q=85"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="hero-gradient absolute inset-0" />
        </div>

        {/* Glow Effect */}
        <div className="hero-glow absolute inset-0 pointer-events-none" />

        {/* Content */}
        <div className="relative z-10 max-w-6xl mx-auto px-6 md:px-12 py-32 text-center">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-300">Early Access Now Open</span>
            </div>

            {/* Title */}
            <h1
              data-testid="hero-title"
              className="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-bold tracking-tight mb-6"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
            >
              Shutter<span className="text-purple-400">score</span>
            </h1>

            {/* Subtitle */}
            <p className="text-lg sm:text-xl md:text-2xl text-gray-300 max-w-2xl mx-auto mb-4">
              Run photo contests that inspire — and give back.
            </p>
            <p className="text-base md:text-lg text-gray-400 max-w-xl mx-auto mb-12">
              Seamless payments, fair judging, automated donations. Launch your first contest today.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button
                data-testid="get-early-access-btn"
                onClick={scrollToWaitlist}
                className="btn-primary px-10 py-6 text-lg"
              >
                Get Early Access
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button
                data-testid="explore-features-btn"
                onClick={scrollToFeatures}
                variant="ghost"
                className="btn-secondary px-10 py-6 text-lg"
              >
                Explore Features
              </Button>
            </div>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5, duration: 0.5 }}
            className="absolute bottom-12 left-1/2 -translate-x-1/2"
          >
            <button
              onClick={scrollToFeatures}
              className="text-gray-500 hover:text-white transition-colors"
              aria-label="Scroll to features"
            >
              <ChevronDown className="w-8 h-8 animate-bounce" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section
        ref={featuresRef}
        id="features"
        className="py-24 md:py-32 px-6 md:px-12 max-w-7xl mx-auto"
      >
        <AnimatedSection className="text-center mb-20">
          <h2
            data-testid="features-title"
            className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            Everything You Need
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            No enterprise complexity. Clean tools that just work.
          </p>
        </AnimatedSection>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
          className="bento-grid"
        >
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} feature={feature} index={index} />
          ))}
        </motion.div>
      </section>

      {/* Impact Section */}
      <section className="py-24 md:py-32 px-6 md:px-12 relative">
        <div className="impact-glow absolute inset-0 pointer-events-none" />
        <div className="max-w-5xl mx-auto relative z-10">
          <AnimatedSection className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8">
              <Heart className="w-4 h-4 text-emerald-400" />
              <span className="text-sm text-gray-300">Impact Driven</span>
            </div>
            <h2
              data-testid="impact-title"
              className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
            >
              Contests with <span className="italic">Purpose</span>
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Every photo tells a story. Every contest supports a cause.
            </p>
          </AnimatedSection>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={staggerContainer}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            {impactStats.map((stat, index) => (
              <motion.div
                key={stat.label}
                variants={fadeInUp}
                className="glass rounded-2xl p-8 text-center"
              >
                <div
                  data-testid={`stat-value-${index}`}
                  className="stat-number text-5xl md:text-6xl font-bold mb-3"
                >
                  {stat.value}
                </div>
                <p className="text-gray-400">{stat.label}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Waitlist CTA Section */}
      <section id="waitlist" className="py-24 md:py-32 px-6 md:px-12 relative">
        <div className="cta-glow absolute inset-0 pointer-events-none" />
        <div className="max-w-2xl mx-auto text-center relative z-10">
          <AnimatedSection>
            <Camera className="w-12 h-12 text-purple-400 mx-auto mb-8" />
            <h2
              data-testid="waitlist-title"
              className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
            >
              Ready to Launch?
            </h2>
            <p className="text-lg text-gray-400 mb-12">
              Join early — get lifetime discounts as a founding creator. Launching soon.
            </p>

            <form
              onSubmit={handleWaitlistSubmit}
              className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto"
              data-testid="waitlist-form"
            >
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="waitlist-input px-6 py-6 text-base flex-1"
                data-testid="waitlist-email-input"
              />
              <Button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary px-8 py-6 text-base animate-pulse-glow"
                data-testid="waitlist-submit-btn"
              >
                {isSubmitting ? "Joining..." : "Join Waitlist"}
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </form>
          </AnimatedSection>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer-gradient py-16 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Camera className="w-5 h-5 text-purple-400" />
            <span
              className="text-xl font-semibold"
              style={{ fontFamily: "'Cormorant Garamond', serif" }}
            >
              Shutterscore
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            © 2026 Shutterscore. Built with 📷 in Chicago.
          </p>
        </div>
      </footer>
    </main>
  );
}
