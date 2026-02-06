import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AdminPanel from "./pages/AdminPanel";
import Leaderboard from "./pages/Leaderboard";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" richColors />
      <div className="noise-overlay" aria-hidden="true" />
    </div>
  );
}

export default App;
