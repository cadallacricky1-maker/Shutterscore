import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Camera,
  ArrowLeft,
  Plus,
  Trophy,
  Calendar,
  Image,
  DollarSign,
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Status badge colors
const statusColors = {
  active: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  judging: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  completed: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

// Contest Card
const ContestCard = ({ contest }) => {
  const endDate = new Date(contest.end_date);
  const isExpired = endDate < new Date();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl p-6 hover:border-purple-500/30 transition-colors"
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium border ${statusColors[contest.status]}`}>
            {contest.status.toUpperCase()}
          </span>
        </div>
        {contest.prize_amount > 0 && (
          <div className="flex items-center gap-1 text-emerald-400">
            <DollarSign className="w-4 h-4" />
            <span className="font-bold">{contest.prize_amount}</span>
          </div>
        )}
      </div>
      
      <h3 className="text-xl font-bold text-white mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
        {contest.title}
      </h3>
      <p className="text-gray-400 text-sm mb-4 line-clamp-2">{contest.description}</p>
      
      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <Image className="w-4 h-4" />
          <span>{contest.photo_count || 0} photos</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-4 h-4" />
          <span>{isExpired ? "Ended" : `Ends ${endDate.toLocaleDateString()}`}</span>
        </div>
      </div>
      
      <div className="pt-4 border-t border-white/10">
        <p className="text-xs text-gray-500 mb-3">
          Theme: <span className="text-purple-400">{contest.theme}</span>
        </p>
        <Link to={`/contests/${contest.id}`}>
          <Button className="w-full bg-purple-600 hover:bg-purple-700">
            View Contest
          </Button>
        </Link>
      </div>
    </motion.div>
  );
};

export default function Contests() {
  const [contests, setContests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const fetchContests = async () => {
      try {
        const params = filter !== "all" ? `?status=${filter}` : "";
        const response = await axios.get(`${API}/contests${params}`);
        setContests(response.data.contests || []);
      } catch (error) {
        console.error("Failed to fetch contests:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchContests();
  }, [filter]);

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
                Photo Contests
              </span>
            </div>
          </div>
          <Link to="/judge">
            <Button variant="outline" className="border-purple-500/30 text-purple-400 hover:bg-purple-500/10">
              <Trophy className="w-4 h-4 mr-2" />
              Judge Photos
            </Button>
          </Link>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            Photo Contests
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Compete, showcase your photography, and win prizes. Join active contests or judge submissions.
          </p>
        </div>

        {/* Filters */}
        <div className="flex gap-2 justify-center mb-8">
          {["all", "active", "judging", "completed"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                filter === status
                  ? "bg-purple-600 text-white"
                  : "bg-white/5 text-gray-400 hover:bg-white/10"
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {/* Contests Grid */}
        {isLoading ? (
          <div className="text-center py-12 text-gray-400">Loading contests...</div>
        ) : contests.length === 0 ? (
          <div className="text-center py-16 glass rounded-2xl">
            <Trophy className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-300 mb-2">No Contests Found</h3>
            <p className="text-gray-500 mb-6">
              {filter === "all" ? "No contests available yet." : `No ${filter} contests at the moment.`}
            </p>
            <Link to="/judge">
              <Button className="bg-purple-600 hover:bg-purple-700">
                Start Judging Instead
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {contests.map((contest) => (
              <ContestCard key={contest.id} contest={contest} />
            ))}
          </div>
        )}

        {/* Quick Links */}
        <div className="mt-12 text-center">
          <p className="text-gray-500 mb-4">Want to help judge photos?</p>
          <Link to="/judge">
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Trophy className="w-4 h-4 mr-2" />
              Go to Judge Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
