import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  X,
  Copy,
  Twitter,
  Facebook,
  Linkedin,
  Mail,
  Check,
  Share2,
} from "lucide-react";
import { Button } from "./ui/button";

const SHARE_URL = typeof window !== "undefined" ? window.location.origin : "https://shutterscore.com";
const SHARE_TEXT = "I just joined the Shutterscore waitlist! Run photo contests that inspire — and give back. Join me:";
const SHARE_TITLE = "Shutterscore — Photo Contests That Inspire & Give Back";

export default function ShareModal({ isOpen, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(SHARE_URL);
      setCopied(true);
      toast.success("Link copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error("Failed to copy link");
    }
  };

  const shareLinks = [
    {
      name: "Twitter",
      icon: Twitter,
      color: "bg-[#1DA1F2]/20 text-[#1DA1F2] hover:bg-[#1DA1F2]/30",
      url: `https://twitter.com/intent/tweet?text=${encodeURIComponent(SHARE_TEXT)}&url=${encodeURIComponent(SHARE_URL)}`,
    },
    {
      name: "Facebook",
      icon: Facebook,
      color: "bg-[#4267B2]/20 text-[#4267B2] hover:bg-[#4267B2]/30",
      url: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(SHARE_URL)}&quote=${encodeURIComponent(SHARE_TEXT)}`,
    },
    {
      name: "LinkedIn",
      icon: Linkedin,
      color: "bg-[#0A66C2]/20 text-[#0A66C2] hover:bg-[#0A66C2]/30",
      url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(SHARE_URL)}`,
    },
    {
      name: "Email",
      icon: Mail,
      color: "bg-purple-500/20 text-purple-400 hover:bg-purple-500/30",
      url: `mailto:?subject=${encodeURIComponent(SHARE_TITLE)}&body=${encodeURIComponent(SHARE_TEXT + " " + SHARE_URL)}`,
    },
  ];

  const handleShare = (url) => {
    window.open(url, "_blank", "noopener,noreferrer,width=600,height=400");
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-4"
          >
            <div className="bg-[#0A0A0A] border border-white/10 rounded-2xl p-6 shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Share2 className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3
                      className="text-xl font-semibold text-white"
                      style={{ fontFamily: "'Cormorant Garamond', serif" }}
                    >
                      Share with Friends
                    </h3>
                    <p className="text-sm text-gray-400">Help spread the word!</p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-white transition-colors"
                  data-testid="close-share-modal"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Share Buttons */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                {shareLinks.map((link) => (
                  <button
                    key={link.name}
                    onClick={() => handleShare(link.url)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${link.color}`}
                    data-testid={`share-${link.name.toLowerCase()}`}
                  >
                    <link.icon className="w-5 h-5" />
                    <span className="font-medium">{link.name}</span>
                  </button>
                ))}
              </div>

              {/* Copy Link */}
              <div className="space-y-2">
                <label className="text-sm text-gray-400">Or copy link</label>
                <div className="flex gap-2">
                  <div className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-gray-300 text-sm truncate">
                    {SHARE_URL}
                  </div>
                  <Button
                    onClick={handleCopy}
                    className={`px-4 transition-all ${
                      copied
                        ? "bg-emerald-600 hover:bg-emerald-700"
                        : "bg-purple-600 hover:bg-purple-700"
                    }`}
                    data-testid="copy-link-btn"
                  >
                    {copied ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
