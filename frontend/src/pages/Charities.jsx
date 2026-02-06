import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import axios from "axios";
import {
  Camera,
  ArrowLeft,
  Heart,
  DollarSign,
  Users,
  TrendingUp,
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Charity Card
const CharityCard = ({ charity }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="glass rounded-2xl p-6 hover:border-emerald-500/30 transition-colors"
  >
    <div className="flex items-start gap-4">
      <div className="w-14 h-14 rounded-xl bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
        <Heart className="w-7 h-7 text-emerald-400" />
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="text-xl font-bold text-white mb-1">{charity.name}</h3>
        <p className="text-gray-400 text-sm mb-4">{charity.description}</p>
        
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-emerald-400" />
            <span className="text-white font-bold">${charity.total_raised?.toFixed(2) || "0.00"}</span>
            <span className="text-gray-500">raised</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-400" />
            <span className="text-white font-bold">{charity.donation_count || 0}</span>
            <span className="text-gray-500">donations</span>
          </div>
        </div>
      </div>
    </div>
  </motion.div>
);

export default function Charities() {
  const [charities, setCharities] = useState([]);
  const [totalRaised, setTotalRaised] = useState(0);
  const [totalDonations, setTotalDonations] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCharities = async () => {
      try {
        const response = await axios.get(`${API}/charities`);
        setCharities(response.data.charities || []);
        setTotalRaised(response.data.total_raised || 0);
        setTotalDonations(response.data.total_donations || 0);
      } catch (error) {
        console.error("Failed to fetch charities:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCharities();
  }, []);

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
                Charity Impact
              </span>
            </div>
          </div>
          <Link to="/contests">
            <Button className="bg-purple-600 hover:bg-purple-700">Enter a Contest</Button>
          </Link>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/20 mb-6">
            <Heart className="w-10 h-10 text-emerald-400" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            Contests with <span className="italic text-emerald-400">Purpose</span>
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Every contest entry can make a difference. A portion of entry fees goes directly to verified charities.
          </p>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid md:grid-cols-2 gap-6 mb-12"
        >
          <div className="glass rounded-2xl p-8 text-center">
            <DollarSign className="w-10 h-10 text-emerald-400 mx-auto mb-4" />
            <p className="text-4xl font-bold text-white mb-2">${totalRaised.toFixed(2)}</p>
            <p className="text-gray-400">Total Raised</p>
          </div>
          <div className="glass rounded-2xl p-8 text-center">
            <TrendingUp className="w-10 h-10 text-purple-400 mx-auto mb-4" />
            <p className="text-4xl font-bold text-white mb-2">{totalDonations}</p>
            <p className="text-gray-400">Total Donations</p>
          </div>
        </motion.div>

        {/* Charities List */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            Supported Charities
          </h2>
          
          {isLoading ? (
            <div className="text-center py-12 text-gray-400">Loading charities...</div>
          ) : (
            <div className="space-y-4">
              {charities.map((charity, index) => (
                <motion.div
                  key={charity.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <CharityCard charity={charity} />
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center"
        >
          <p className="text-gray-400 mb-4">Ready to make an impact?</p>
          <Link to="/contests">
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <Heart className="w-4 h-4 mr-2" />
              Enter a Contest & Donate
            </Button>
          </Link>
        </motion.div>
      </div>
    </main>
  );
}
