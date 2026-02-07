import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AdminPanel from "./pages/AdminPanel";
import Leaderboard from "./pages/Leaderboard";
import JudgeDashboard from "./pages/JudgeDashboard";
import JudgePhoto from "./pages/JudgePhoto";
import Contests from "./pages/Contests";
import ContestDetail from "./pages/ContestDetail";
import Charities from "./pages/Charities";
import PaymentSuccess from "./pages/PaymentSuccess";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/contests" element={<Contests />} />
          <Route path="/contests/:contestId" element={<ContestDetail />} />
          <Route path="/judge" element={<JudgeDashboard />} />
          <Route path="/judge/:photoId" element={<JudgePhoto />} />
          <Route path="/charities" element={<Charities />} />
          <Route path="/payment/success" element={<PaymentSuccess />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
      <div className="noise-overlay" aria-hidden="true" />
    </div>
  );
}

export default App;
