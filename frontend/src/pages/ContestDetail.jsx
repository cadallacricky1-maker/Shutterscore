import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams, Link } from "react-router-dom";
import { toast } from "sonner";
import axios from "axios";
import {
  Camera,
  ArrowLeft,
  Trophy,
  Calendar,
  Image,
  DollarSign,
  Upload,
  Medal,
  Award,
  Crown,
  Target,
  Heart,
  CreditCard,
  Loader2,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Slider } from "../components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Rank badge
const RankBadge = ({ rank }) => {
  if (rank === 1) return <Crown className="w-5 h-5 text-amber-400" />;
  if (rank === 2) return <Medal className="w-5 h-5 text-gray-300" />;
  if (rank === 3) return <Award className="w-5 h-5 text-amber-600" />;
  return <span className="text-gray-500 font-bold">#{rank}</span>;
};

// Photo submission form with payment
const SubmitPhotoForm = ({ contestId, entryFee, onSuccess }) => {
  const [step, setStep] = useState(1); // 1: info, 2: payment, 3: upload
  const [formData, setFormData] = useState({
    photographer_name: "",
    photographer_email: "",
    photo_url: "",
    title: "",
    description: "",
  });
  const [packageId, setPackageId] = useState("standard");
  const [charityId, setCharityId] = useState("");
  const [charityPercentage, setCharityPercentage] = useState(10);
  const [charities, setCharities] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPaid, setIsPaid] = useState(false);

  useEffect(() => {
    // Fetch charities
    axios.get(`${API}/charities`).then(res => {
      setCharities(res.data.charities || []);
      if (res.data.charities?.length > 0) {
        setCharityId(res.data.charities[0].id);
      }
    }).catch(console.error);
  }, []);

  const packages = {
    free: { amount: 0, label: "Free Entry" },
    standard: { amount: 5, label: "Standard Entry ($5)" },
    premium: { amount: 10, label: "Premium Entry ($10)" },
  };

  const handlePayment = async () => {
    if (!formData.photographer_name || !formData.photographer_email) {
      toast.error("Please fill in your name and email first");
      setStep(1);
      return;
    }

    const pkg = packages[packageId];
    if (pkg.amount === 0) {
      setIsPaid(true);
      setStep(3);
      toast.success("Free entry! Now upload your photo.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await axios.post(`${API}/payments/create-checkout`, {
        contest_id: contestId,
        payer_name: formData.photographer_name,
        payer_email: formData.photographer_email,
        package_id: packageId,
        charity_id: charityId,
        charity_percentage: charityPercentage,
        origin_url: window.location.origin,
      });

      if (response.data.is_free) {
        setIsPaid(true);
        setStep(3);
        toast.success("Free entry confirmed!");
      } else if (response.data.checkout_url) {
        // Redirect to Stripe
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Payment failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitPhoto = async (e) => {
    e.preventDefault();
    if (!formData.photo_url || !formData.title) {
      toast.error("Please provide photo URL and title");
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.post(`${API}/photos`, {
        contest_id: contestId,
        ...formData,
      });
      toast.success("Photo submitted successfully!");
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit photo");
    } finally {
      setIsSubmitting(false);
    }
  };

  const charityAmount = packages[packageId]?.amount * (charityPercentage / 100);

  return (
    <div className="space-y-6">
      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-2 mb-6">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step === s
                ? "bg-purple-600 text-white"
                : step > s
                ? "bg-emerald-600 text-white"
                : "bg-white/10 text-gray-400"
            }`}
          >
            {s}
          </div>
        ))}
      </div>

      {/* Step 1: Basic Info */}
      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Your Information</h3>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Your Name *</label>
            <Input
              value={formData.photographer_name}
              onChange={(e) => setFormData({ ...formData, photographer_name: e.target.value })}
              placeholder="John Doe"
              className="bg-white/5 border-white/10 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Your Email *</label>
            <Input
              type="email"
              value={formData.photographer_email}
              onChange={(e) => setFormData({ ...formData, photographer_email: e.target.value })}
              placeholder="john@example.com"
              className="bg-white/5 border-white/10 text-white"
            />
          </div>
          <Button
            onClick={() => setStep(2)}
            disabled={!formData.photographer_name || !formData.photographer_email}
            className="w-full bg-purple-600 hover:bg-purple-700"
          >
            Continue to Payment
          </Button>
        </div>
      )}

      {/* Step 2: Payment */}
      {step === 2 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Entry Fee & Donation</h3>
          
          {/* Package Selection */}
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Entry Package</label>
            <Select value={packageId} onValueChange={setPackageId}>
              <SelectTrigger className="bg-white/5 border-white/10 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#0A0A0A] border-white/10">
                {Object.entries(packages).map(([id, pkg]) => (
                  <SelectItem key={id} value={id} className="text-white">
                    {pkg.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {packages[packageId]?.amount > 0 && (
            <>
              {/* Charity Selection */}
              <div>
                <label className="text-sm text-gray-400 mb-2 block">Donate to Charity</label>
                <Select value={charityId} onValueChange={setCharityId}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white">
                    <SelectValue placeholder="Select a charity" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0A0A0A] border-white/10">
                    {charities.map((charity) => (
                      <SelectItem key={charity.id} value={charity.id} className="text-white">
                        <div className="flex items-center gap-2">
                          <Heart className="w-4 h-4 text-emerald-400" />
                          {charity.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Charity Percentage */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm text-gray-400">Donation Percentage</label>
                  <span className="text-emerald-400 font-bold">{charityPercentage}%</span>
                </div>
                <Slider
                  value={[charityPercentage]}
                  onValueChange={(val) => setCharityPercentage(val[0])}
                  min={0}
                  max={50}
                  step={5}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  ${charityAmount.toFixed(2)} goes to charity
                </p>
              </div>
            </>
          )}

          {/* Summary */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Entry Fee</span>
              <span className="text-white font-bold">${packages[packageId]?.amount || 0}</span>
            </div>
            {charityAmount > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-emerald-400">→ To Charity</span>
                <span className="text-emerald-400">${charityAmount.toFixed(2)}</span>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep(1)} className="flex-1 border-white/10 text-white">
              Back
            </Button>
            <Button
              onClick={handlePayment}
              disabled={isSubmitting}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
            >
              {isSubmitting ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <CreditCard className="w-4 h-4 mr-2" />
              )}
              {packages[packageId]?.amount === 0 ? "Continue Free" : "Pay & Continue"}
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Upload Photo */}
      {step === 3 && (
        <form onSubmit={handleSubmitPhoto} className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Upload Your Photo</h3>
          
          <div className="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-sm">
            ✓ Payment confirmed! Now upload your photo.
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-1 block">Photo URL *</label>
            <Input
              value={formData.photo_url}
              onChange={(e) => setFormData({ ...formData, photo_url: e.target.value })}
              placeholder="https://example.com/photo.jpg"
              className="bg-white/5 border-white/10 text-white"
            />
            <p className="text-xs text-gray-500 mt-1">
              Paste a direct link to your photo (Unsplash, Imgur, Google Photos, etc.)
            </p>
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Photo Title *</label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Sunset Over Chicago"
              className="bg-white/5 border-white/10 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Description (optional)</label>
            <Textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Tell us about your photo..."
              className="bg-white/5 border-white/10 text-white"
            />
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep(2)} className="flex-1 border-white/10 text-white">
              Back
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-purple-600 hover:bg-purple-700"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Upload className="w-4 h-4 mr-2" />}
              Submit Photo
            </Button>
          </div>
        </form>
      )}
    </div>
  );
};

export default function ContestDetail() {
  const { contestId } = useParams();
  const [contest, setContest] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);

  const fetchData = async () => {
    try {
      const [contestRes, photosRes, leaderboardRes] = await Promise.all([
        axios.get(`${API}/contests/${contestId}`),
        axios.get(`${API}/photos?contest_id=${contestId}`),
        axios.get(`${API}/contests/${contestId}/leaderboard`),
      ]);
      setContest(contestRes.data);
      setPhotos(photosRes.data.photos || []);
      setLeaderboard(leaderboardRes.data.leaderboard || []);
    } catch (error) {
      toast.error("Failed to load contest");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [contestId]);

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#050505] text-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
      </main>
    );
  }

  if (!contest) return null;

  const endDate = new Date(contest.end_date);
  const isActive = contest.status === "active";

  return (
    <main className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-lg sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/contests" className="text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-purple-400" />
              <span className="text-lg font-semibold" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {contest.title}
              </span>
            </div>
          </div>
          {isActive && (
            <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
              <DialogTrigger asChild>
                <Button className="bg-purple-600 hover:bg-purple-700">
                  <Upload className="w-4 h-4 mr-2" />
                  Submit Photo
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#0A0A0A] border-white/10 max-w-md max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="text-white">Enter Contest</DialogTitle>
                </DialogHeader>
                <SubmitPhotoForm
                  contestId={contestId}
                  entryFee={contest.entry_fee}
                  onSuccess={() => {
                    setShowSubmitDialog(false);
                    fetchData();
                  }}
                />
              </DialogContent>
            </Dialog>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Contest Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-8 mb-12"
        >
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div className="flex-1 min-w-[300px]">
              <h1 className="text-4xl font-bold mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                {contest.title}
              </h1>
              <p className="text-gray-400 mb-6">{contest.description}</p>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/20">
                  <Target className="w-4 h-4 text-purple-400" />
                  <span className="text-purple-400">Theme: {contest.theme}</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-400">Ends {endDate.toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5">
                  <Image className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-400">{contest.photo_count || 0} entries</span>
                </div>
                {contest.prize_amount > 0 && (
                  <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/20">
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-400">${contest.prize_amount} prize</span>
                  </div>
                )}
              </div>
            </div>
            <div className={`px-4 py-2 rounded-full text-sm font-medium ${
              contest.status === "active" ? "bg-emerald-500/20 text-emerald-400" :
              contest.status === "judging" ? "bg-amber-500/20 text-amber-400" :
              "bg-gray-500/20 text-gray-400"
            }`}>
              {contest.status.toUpperCase()}
            </div>
          </div>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Leaderboard */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-6"
          >
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              <Trophy className="w-5 h-5 text-amber-400" />
              Leaderboard
            </h2>
            
            {leaderboard.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No judged photos yet</p>
            ) : (
              <div className="space-y-3">
                {leaderboard.slice(0, 10).map((entry) => (
                  <div
                    key={entry.photo_id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] hover:bg-white/5 transition-colors"
                  >
                    <div className="w-8 flex justify-center">
                      <RankBadge rank={entry.rank} />
                    </div>
                    <img
                      src={entry.photo_url}
                      alt={entry.title}
                      className="w-12 h-12 rounded-lg object-cover"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium truncate">{entry.title}</p>
                      <p className="text-gray-500 text-sm">{entry.photographer_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-purple-400 font-bold">{entry.total_score.toFixed(1)}</p>
                      <p className="text-gray-500 text-xs">{entry.judge_count} judges</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Photos Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            <h2 className="text-xl font-bold mb-6" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              All Entries ({photos.length})
            </h2>
            
            {photos.length === 0 ? (
              <div className="glass rounded-2xl p-12 text-center">
                <Image className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400">No photos submitted yet. Be the first!</p>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-4">
                {photos.map((photo) => (
                  <div key={photo.id} className="glass rounded-xl overflow-hidden group">
                    <div className="aspect-[4/3] relative overflow-hidden">
                      <img
                        src={photo.photo_url}
                        alt={photo.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                      <div className="absolute top-3 right-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          photo.status === "judged" 
                            ? "bg-emerald-500/90 text-white" 
                            : "bg-amber-500/90 text-white"
                        }`}>
                          {photo.status === "judged" ? `Score: ${photo.total_score.toFixed(1)}` : "PENDING"}
                        </span>
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-medium text-white truncate">{photo.title}</h3>
                      <p className="text-gray-500 text-sm">{photo.photographer_name}</p>
                      {photo.status === "pending" && (
                        <Link to={`/judge/${photo.id}`}>
                          <Button size="sm" className="mt-3 w-full bg-purple-600 hover:bg-purple-700">
                            Judge This Photo
                          </Button>
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </main>
  );
}
