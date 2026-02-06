import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Camera,
  Image,
  Clock,
  Trophy,
  ArrowLeft,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Stat Card
const StatCard = ({ icon: Icon, label, value, color }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass rounded-2xl p-6"
  >
    <div className="flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-6 h-6" strokeWidth={1.5} />
      </div>
      <div>
        <p className="text-gray-400 text-sm">{label}</p>
        <p className="text-3xl font-bold text-white">{value}</p>
      </div>
    </div>
  </motion.div>
);

// Photo Card
const PhotoCard = ({ photo }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="glass rounded-xl overflow-hidden group"
  >
    <div className="aspect-square relative overflow-hidden">
      <img
        src={photo.photo_url}
        alt={photo.title}
        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="absolute bottom-0 left-0 right-0 p-4 translate-y-full group-hover:translate-y-0 transition-transform">
        <p className="text-white font-medium truncate">{photo.title}</p>
        <p className="text-gray-300 text-sm">{photo.photographer_name}</p>
      </div>
      <div className="absolute top-3 right-3">
        <span className="px-2 py-1 rounded-full bg-amber-500/90 text-white text-xs font-medium">
          PENDING
        </span>
      </div>
    </div>
    <div className="p-4">
      <p className="text-gray-400 text-sm mb-3">{photo.contest_title}</p>
      <Link to={`/judge/${photo.id}`}>
        <Button className="w-full bg-purple-600 hover:bg-purple-700" data-testid={`judge-${photo.id}`}>
          <Sparkles className="w-4 h-4 mr-2" />
          Judge Now
        </Button>
      </Link>
    </div>
  </motion.div>
);

export default function JudgeDashboard() {
  const [photos, setPhotos] = useState([]);
  const [stats, setStats] = useState({ total_pending: 0, total_judged: 0, active_contests: 0, my_judgments: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [judgeEmail, setJudgeEmail] = useState("");

  // Get judge email from localStorage or prompt
  useEffect(() => {
    const storedEmail = localStorage.getItem("judgeEmail");
    if (storedEmail) {
      setJudgeEmail(storedEmail);
    }
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [photosRes, statsRes] = await Promise.all([
        axios.get(`${API}/judge/pending${judgeEmail ? `?judge_email=${encodeURIComponent(judgeEmail)}` : ""}`),
        axios.get(`${API}/judge/stats${judgeEmail ? `?judge_email=${encodeURIComponent(judgeEmail)}` : ""}`)
      ]);
      setPhotos(photosRes.data.photos || []);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [judgeEmail]);

  const handleSetEmail = () => {
    const email = prompt("Enter your email to track your judgments:");
    if (email) {
      localStorage.setItem("judgeEmail", email);
      setJudgeEmail(email);
    }
  };

  return (
    <main className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-lg sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-purple-400" />
              <span className="text-lg font-semibold" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                Judge Dashboard
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {judgeEmail ? (
              <span className="text-sm text-gray-400">{judgeEmail}</span>
            ) : (
              <Button variant="outline" size="sm" onClick={handleSetEmail} className="border-white/10 text-white">
                Set Your Email
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={fetchData} className="text-gray-400 hover:text-white">
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <StatCard icon={Image} label="Pending Photos" value={stats.total_pending} color="bg-amber-500/20 text-amber-400" />
          <StatCard icon={Trophy} label="Judged Photos" value={stats.total_judged} color="bg-emerald-500/20 text-emerald-400" />
          <StatCard icon={Camera} label="Active Contests" value={stats.active_contests} color="bg-purple-500/20 text-purple-400" />
          <StatCard icon={Sparkles} label="Your Points" value={(stats.my_judgments || 0) * 5} color="bg-blue-500/20 text-blue-400" />
        </div>

        {/* Photos Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            Photos Awaiting Judgment
          </h2>
          
          {isLoading ? (
            <div className="text-center py-12 text-gray-400">Loading photos...</div>
          ) : photos.length === 0 ? (
            <div className="text-center py-16 glass rounded-2xl">
              <Clock className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No Photos to Judge</h3>
              <p className="text-gray-500 mb-6">All caught up! Check back later for new submissions.</p>
              <Link to="/contests">
                <Button className="bg-purple-600 hover:bg-purple-700">View Contests</Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {photos.map((photo) => (
                <PhotoCard key={photo.id} photo={photo} />
              ))}
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="flex gap-4 justify-center">
          <Link to="/contests">
            <Button variant="outline" className="btn-secondary">View All Contests</Button>
          </Link>
          <Link to="/leaderboard">
            <Button variant="outline" className="btn-secondary">View Leaderboard</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
