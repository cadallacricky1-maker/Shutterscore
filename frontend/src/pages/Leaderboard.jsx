import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Trophy,
  Medal,
  Award,
  Users,
  ArrowLeft,
  Camera,
  Crown,
  RefreshCw,
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

// Rank badge component
const RankBadge = ({ rank }) => {
  if (rank === 1) {
    return (
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/30">
        <Crown className="w-6 h-6 text-white" />
      </div>
    );
  }
  if (rank === 2) {
    return (
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gray-300 to-gray-500 flex items-center justify-center">
        <Medal className="w-6 h-6 text-white" />
      </div>
    );
  }
  if (rank === 3) {
    return (
      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-600 to-amber-800 flex items-center justify-center">
        <Award className="w-6 h-6 text-white" />
      </div>
    );
  }
  return (
    <div className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
      <span className="text-lg font-bold text-gray-400">#{rank}</span>
    </div>
  );
};

// Leaderboard entry component
const LeaderboardEntry = ({ entry, index }) => {
  const isTopThree = entry.rank <= 3;
  
  return (
    <motion.div
      variants={fadeInUp}
      className={`flex items-center gap-4 p-4 rounded-xl transition-all ${
        isTopThree
          ? "bg-gradient-to-r from-white/5 to-transparent border border-white/10"
          : "bg-white/[0.02] hover:bg-white/5"
      }`}
    >
      <RankBadge rank={entry.rank} />
      
      <div className="flex-1 min-w-0">
        <p className={`font-medium truncate ${isTopThree ? "text-white" : "text-gray-300"}`}>
          {entry.email_masked}
        </p>
        <p className="text-sm text-gray-500 font-mono">{entry.referral_code}</p>
      </div>
      
      <div className="text-right">
        <p className={`text-2xl font-bold ${
          entry.rank === 1 ? "text-amber-400" :
          entry.rank === 2 ? "text-gray-300" :
          entry.rank === 3 ? "text-amber-600" :
          "text-purple-400"
        }`}>
          {entry.referral_count}
        </p>
        <p className="text-xs text-gray-500">referrals</p>
      </div>
    </motion.div>
  );
};

export default function Leaderboard() {
  const [entries, setEntries] = useState([]);
  const [totalParticipants, setTotalParticipants] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const fetchLeaderboard = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/leaderboard?limit=20`);
      setEntries(response.data.entries);
      setTotalParticipants(response.data.total_participants);
    } catch (error) {
      console.error("Failed to fetch leaderboard:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  return (
    <main className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-lg sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-purple-400" />
              <span
                className="text-lg font-semibold"
                style={{ fontFamily: "'Cormorant Garamond', serif" }}
              >
                Shutterscore
              </span>
            </div>
          </div>
          <Button
            onClick={fetchLeaderboard}
            variant="ghost"
            size="sm"
            className="text-gray-400 hover:text-white"
            data-testid="refresh-leaderboard"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 px-6 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-purple-500/10 to-transparent pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 mb-6 shadow-lg shadow-amber-500/30">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1
            className="text-4xl sm:text-5xl font-bold mb-4"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
            data-testid="leaderboard-title"
          >
            Top Referrers
          </h1>
          <p className="text-gray-400 max-w-md mx-auto">
            The champions who are spreading the word about Shutterscore
          </p>
          <div className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
            <Users className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-gray-300">
              {totalParticipants} people with referrals
            </span>
          </div>
        </motion.div>
      </section>

      {/* Leaderboard List */}
      <section className="max-w-2xl mx-auto px-6 pb-24">
        {isLoading ? (
          <div className="text-center py-12 text-gray-400">
            Loading leaderboard...
          </div>
        ) : entries.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
              <Trophy className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="text-xl font-semibold text-gray-300 mb-2">
              No Referrers Yet
            </h3>
            <p className="text-gray-500 mb-6">
              Be the first to refer friends and claim the top spot!
            </p>
            <Link to="/">
              <Button className="bg-purple-600 hover:bg-purple-700">
                Join Waitlist & Start Referring
              </Button>
            </Link>
          </motion.div>
        ) : (
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="space-y-3"
          >
            {entries.map((entry, index) => (
              <LeaderboardEntry key={entry.referral_code} entry={entry} index={index} />
            ))}
          </motion.div>
        )}

        {/* CTA */}
        {entries.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-12 text-center"
          >
            <p className="text-gray-400 mb-4">Want to climb the leaderboard?</p>
            <Link to="/">
              <Button className="bg-purple-600 hover:bg-purple-700" data-testid="join-cta">
                Join Waitlist & Start Referring
              </Button>
            </Link>
          </motion.div>
        )}
      </section>
    </main>
  );
}
