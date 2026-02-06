import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useSearchParams, Link } from "react-router-dom";
import axios from "axios";
import {
  Camera,
  CheckCircle,
  Heart,
  ArrowRight,
  Loader2,
  XCircle,
} from "lucide-react";
import { Button } from "../components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  
  const [status, setStatus] = useState("loading"); // loading, success, failed
  const [paymentData, setPaymentData] = useState(null);

  useEffect(() => {
    const checkPayment = async () => {
      if (!sessionId) {
        setStatus("failed");
        return;
      }

      try {
        const response = await axios.get(`${API}/payments/status/${sessionId}`);
        setPaymentData(response.data);
        
        if (response.data.status === "paid" || response.data.payment_status === "paid") {
          setStatus("success");
        } else if (response.data.status === "expired" || response.data.status === "failed") {
          setStatus("failed");
        } else {
          // Still pending, poll again
          setTimeout(checkPayment, 2000);
        }
      } catch (error) {
        console.error("Failed to check payment:", error);
        setStatus("failed");
      }
    };

    checkPayment();
  }, [sessionId]);

  return (
    <main className="min-h-screen bg-[#050505] text-white flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full"
      >
        <div className="glass rounded-2xl p-8 text-center">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2 mb-8">
            <Camera className="w-6 h-6 text-purple-400" />
            <span className="text-xl font-semibold" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
              Shutterscore
            </span>
          </div>

          {/* Status Icon */}
          {status === "loading" && (
            <div className="mb-6">
              <Loader2 className="w-16 h-16 text-purple-400 mx-auto animate-spin" />
            </div>
          )}
          
          {status === "success" && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", damping: 15 }}
              className="mb-6"
            >
              <div className="w-20 h-20 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto">
                <CheckCircle className="w-12 h-12 text-emerald-400" />
              </div>
            </motion.div>
          )}
          
          {status === "failed" && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="mb-6"
            >
              <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mx-auto">
                <XCircle className="w-12 h-12 text-red-400" />
              </div>
            </motion.div>
          )}

          {/* Status Message */}
          {status === "loading" && (
            <>
              <h1 className="text-2xl font-bold mb-2">Processing Payment...</h1>
              <p className="text-gray-400">Please wait while we confirm your payment.</p>
            </>
          )}
          
          {status === "success" && (
            <>
              <h1 className="text-2xl font-bold mb-2 text-emerald-400">Payment Successful!</h1>
              <p className="text-gray-400 mb-6">Thank you for entering the contest.</p>
              
              {/* Payment Details */}
              <div className="bg-white/5 rounded-xl p-4 mb-6 text-left space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Amount Paid</span>
                  <span className="text-white font-bold">${paymentData?.amount?.toFixed(2)}</span>
                </div>
                {paymentData?.charity_amount > 0 && (
                  <div className="flex justify-between items-center">
                    <span className="text-emerald-400 flex items-center gap-1">
                      <Heart className="w-4 h-4" /> Donated to Charity
                    </span>
                    <span className="text-emerald-400 font-bold">${paymentData?.charity_amount?.toFixed(2)}</span>
                  </div>
                )}
              </div>
              
              <p className="text-gray-500 text-sm mb-6">
                You can now submit your photo to the contest.
              </p>
              
              <Link to="/contests">
                <Button className="w-full bg-purple-600 hover:bg-purple-700">
                  Continue to Contests
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </>
          )}
          
          {status === "failed" && (
            <>
              <h1 className="text-2xl font-bold mb-2 text-red-400">Payment Failed</h1>
              <p className="text-gray-400 mb-6">
                Your payment could not be processed. Please try again.
              </p>
              
              <Link to="/contests">
                <Button className="w-full bg-purple-600 hover:bg-purple-700">
                  Back to Contests
                </Button>
              </Link>
            </>
          )}
        </div>
      </motion.div>
    </main>
  );
}
