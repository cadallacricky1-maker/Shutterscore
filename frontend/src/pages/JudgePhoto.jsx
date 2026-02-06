import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import {
  Camera,
  ArrowLeft,
  Sparkles,
  Send,
  Loader2,
  Star,
  Palette,
  Target,
  Heart,
  ChevronRight,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Score weights for display
const CRITERIA = [
  { key: "creativity", label: "Creativity & Originality", icon: Sparkles, weight: 3, maxPoints: 30, color: "purple" },
  { key: "composition", label: "Technical Composition", icon: Palette, weight: 2.5, maxPoints: 25, color: "blue" },
  { key: "theme_fit", label: "Theme Relevance", icon: Target, weight: 2.5, maxPoints: 25, color: "emerald" },
  { key: "impact", label: "Emotional Impact", icon: Heart, weight: 2, maxPoints: 20, color: "amber" },
];

// Score Button Component
const ScoreButton = ({ value, selected, onClick, color }) => (
  <button
    type="button"
    onClick={() => onClick(value)}
    className={`w-9 h-9 rounded-lg font-semibold text-sm transition-all ${
      selected
        ? `bg-${color}-500 text-white shadow-lg shadow-${color}-500/30`
        : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
    }`}
  >
    {value}
  </button>
);

// Criteria Row Component
const CriteriaRow = ({ criterion, score, onScoreChange }) => {
  const Icon = criterion.icon;
  const colorClasses = {
    purple: { bg: "bg-purple-500/20", text: "text-purple-400", selected: "bg-purple-500" },
    blue: { bg: "bg-blue-500/20", text: "text-blue-400", selected: "bg-blue-500" },
    emerald: { bg: "bg-emerald-500/20", text: "text-emerald-400", selected: "bg-emerald-500" },
    amber: { bg: "bg-amber-500/20", text: "text-amber-400", selected: "bg-amber-500" },
  };
  const colors = colorClasses[criterion.color];
  const weightedScore = (score * criterion.weight).toFixed(1);

  return (
    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center`}>
            <Icon className={`w-5 h-5 ${colors.text}`} />
          </div>
          <div>
            <p className="font-medium text-white">{criterion.label}</p>
            <p className="text-xs text-gray-500">Max {criterion.maxPoints} pts (×{criterion.weight})</p>
          </div>
        </div>
        <div className="text-right">
          <p className={`text-2xl font-bold ${colors.text}`}>{weightedScore}</p>
          <p className="text-xs text-gray-500">/{criterion.maxPoints}</p>
        </div>
      </div>
      <div className="flex gap-1.5 flex-wrap">
        {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((val) => (
          <ScoreButton
            key={val}
            value={val}
            selected={score === val}
            onClick={onScoreChange}
            color={criterion.color}
          />
        ))}
      </div>
    </div>
  );
};

export default function JudgePhoto() {
  const { photoId } = useParams();
  const navigate = useNavigate();
  
  const [photo, setPhoto] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAILoading, setIsAILoading] = useState(false);
  
  const [scores, setScores] = useState({
    creativity: 5,
    composition: 5,
    theme_fit: 5,
    impact: 5,
  });
  const [comments, setComments] = useState("");
  const [isAIGenerated, setIsAIGenerated] = useState(false);
  
  const [judgeName, setJudgeName] = useState("");
  const [judgeEmail, setJudgeEmail] = useState("");

  useEffect(() => {
    const storedName = localStorage.getItem("judgeName") || "";
    const storedEmail = localStorage.getItem("judgeEmail") || "";
    setJudgeName(storedName);
    setJudgeEmail(storedEmail);
  }, []);

  useEffect(() => {
    const fetchPhoto = async () => {
      try {
        const response = await axios.get(`${API}/photos/${photoId}`);
        setPhoto(response.data);
      } catch (error) {
        toast.error("Failed to load photo");
        navigate("/judge");
      } finally {
        setIsLoading(false);
      }
    };
    fetchPhoto();
  }, [photoId, navigate]);

  // Calculate total score
  const totalWeighted = CRITERIA.reduce((sum, c) => sum + scores[c.key] * c.weight, 0);
  const normalizedScore = ((totalWeighted / 100) * 40).toFixed(1);

  const handleGetAIScores = async () => {
    if (!photo) return;
    
    setIsAILoading(true);
    try {
      const response = await axios.post(`${API}/judge/ai-score`, {
        photo_url: photo.photo_url,
        contest_theme: photo.contest?.theme || "General photography"
      });
      
      setScores({
        creativity: Math.round(response.data.scores.creativity),
        composition: Math.round(response.data.scores.composition),
        theme_fit: Math.round(response.data.scores.theme_fit),
        impact: Math.round(response.data.scores.impact),
      });
      setComments(response.data.comments);
      setIsAIGenerated(true);
      toast.success("AI scores generated! Review and adjust as needed.");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to get AI scores");
    } finally {
      setIsAILoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!judgeName.trim() || !judgeEmail.trim()) {
      toast.error("Please enter your name and email");
      return;
    }
    
    // Save judge info
    localStorage.setItem("judgeName", judgeName);
    localStorage.setItem("judgeEmail", judgeEmail);
    
    setIsSubmitting(true);
    try {
      await axios.post(`${API}/judge/submit`, {
        photo_id: photoId,
        judge_name: judgeName,
        judge_email: judgeEmail,
        scores: scores,
        comments: comments,
        is_ai_generated: isAIGenerated
      });
      
      toast.success("Score submitted successfully!");
      navigate("/judge");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit score");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
      </main>
    );
  }

  if (!photo) return null;

  return (
    <main className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-lg sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/judge" className="text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-purple-400" />
              <span className="text-lg font-semibold" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                Judge Photo
              </span>
            </div>
          </div>
          <div className="text-sm text-gray-400">
            {photo.contest?.title || "Contest"}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Photo Preview */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass rounded-2xl overflow-hidden"
            >
              <div className="aspect-[4/3] relative">
                <img
                  src={photo.photo_url}
                  alt={photo.title}
                  className="w-full h-full object-contain bg-black"
                />
              </div>
              <div className="p-6">
                <h2 className="text-2xl font-bold mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                  {photo.title}
                </h2>
                <p className="text-gray-400 mb-4">by {photo.photographer_name}</p>
                {photo.description && (
                  <p className="text-gray-500 text-sm">{photo.description}</p>
                )}
                <div className="mt-4 pt-4 border-t border-white/10">
                  <p className="text-sm text-gray-500">
                    <span className="text-purple-400">Theme:</span> {photo.contest?.theme || "General"}
                  </p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Scoring Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* AI Score Button */}
              <div className="glass rounded-xl p-4">
                <Button
                  type="button"
                  onClick={handleGetAIScores}
                  disabled={isAILoading}
                  className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 py-6"
                  data-testid="ai-score-btn"
                >
                  {isAILoading ? (
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="w-5 h-5 mr-2" />
                  )}
                  {isAILoading ? "Analyzing Photo..." : "Get AI Scores"}
                </Button>
                <p className="text-center text-xs text-gray-500 mt-2">
                  AI will analyze and suggest scores. You can adjust them.
                </p>
              </div>

              {/* Score Total */}
              <div className="glass rounded-xl p-6 text-center">
                <p className="text-gray-400 text-sm mb-2">Total Score</p>
                <div className="flex items-baseline justify-center gap-2">
                  <span className="text-5xl font-bold text-white">{totalWeighted.toFixed(1)}</span>
                  <span className="text-gray-500">/100</span>
                </div>
                <p className="text-sm text-purple-400 mt-2">
                  Normalized: {normalizedScore}/40
                </p>
              </div>

              {/* Criteria Scores */}
              <div className="space-y-4">
                {CRITERIA.map((criterion) => (
                  <CriteriaRow
                    key={criterion.key}
                    criterion={criterion}
                    score={scores[criterion.key]}
                    onScoreChange={(val) => {
                      setScores({ ...scores, [criterion.key]: val });
                      setIsAIGenerated(false);
                    }}
                  />
                ))}
              </div>

              {/* Comments */}
              <div className="glass rounded-xl p-4">
                <label className="text-sm text-gray-400 mb-2 block">Feedback & Comments</label>
                <Textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Provide constructive feedback for the photographer..."
                  className="bg-white/5 border-white/10 text-white min-h-[100px]"
                  data-testid="comments-input"
                />
              </div>

              {/* Judge Info */}
              <div className="glass rounded-xl p-4 space-y-4">
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Your Name</label>
                  <input
                    type="text"
                    value={judgeName}
                    onChange={(e) => setJudgeName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white"
                    data-testid="judge-name-input"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 mb-2 block">Your Email</label>
                  <input
                    type="email"
                    value={judgeEmail}
                    onChange={(e) => setJudgeEmail(e.target.value)}
                    placeholder="Enter your email"
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white"
                    data-testid="judge-email-input"
                  />
                </div>
              </div>

              {/* Submit */}
              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-emerald-600 hover:bg-emerald-700 py-6 text-lg"
                data-testid="submit-score-btn"
              >
                {isSubmitting ? (
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                ) : (
                  <Send className="w-5 h-5 mr-2" />
                )}
                {isSubmitting ? "Submitting..." : "Submit Score"}
              </Button>
            </form>
          </motion.div>
        </div>
      </div>
    </main>
  );
}
