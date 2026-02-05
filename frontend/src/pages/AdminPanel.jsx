import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  Users,
  TrendingUp,
  Calendar,
  Download,
  Search,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Camera,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Stat Card Component
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

export default function AdminPanel() {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState({ total_signups: 0, today_signups: 0, this_week_signups: 0 });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [deleteId, setDeleteId] = useState(null);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/waitlist/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  const fetchEntries = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({ page, page_size: 10 });
      if (search) params.append("search", search);
      
      const response = await axios.get(`${API}/admin/waitlist?${params}`);
      setEntries(response.data.entries);
      setTotalPages(response.data.total_pages);
      setTotal(response.data.total);
    } catch (error) {
      toast.error("Failed to fetch waitlist entries");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchEntries();
  }, [page]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchEntries();
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleExport = async () => {
    try {
      const response = await axios.get(`${API}/admin/waitlist/export`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "waitlist_export.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("Waitlist exported successfully!");
    } catch (error) {
      toast.error("Failed to export waitlist");
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/admin/waitlist/${id}`);
      toast.success("Entry deleted successfully");
      fetchStats();
      fetchEntries();
    } catch (error) {
      toast.error("Failed to delete entry");
    }
    setDeleteId(null);
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <main className="min-h-screen bg-[#050505] text-white p-6 md:p-12">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-12">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-6 h-6" />
            </Link>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Camera className="w-6 h-6 text-purple-400" />
                <h1
                  className="text-3xl font-bold"
                  style={{ fontFamily: "'Cormorant Garamond', serif" }}
                  data-testid="admin-title"
                >
                  Admin Panel
                </h1>
              </div>
              <p className="text-gray-400">Manage your waitlist signups</p>
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={() => { fetchStats(); fetchEntries(); }}
              variant="outline"
              className="border-white/10 text-white hover:bg-white/10"
              data-testid="refresh-btn"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button
              onClick={handleExport}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="export-btn"
            >
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <StatCard
            icon={Users}
            label="Total Signups"
            value={stats.total_signups}
            color="bg-purple-500/20 text-purple-400"
          />
          <StatCard
            icon={Calendar}
            label="Today"
            value={stats.today_signups}
            color="bg-emerald-500/20 text-emerald-400"
          />
          <StatCard
            icon={TrendingUp}
            label="This Week"
            value={stats.this_week_signups}
            color="bg-amber-500/20 text-amber-400"
          />
        </div>

        {/* Search & Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass rounded-2xl p-6"
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <h2 className="text-xl font-semibold">Waitlist Entries ({total})</h2>
            <div className="relative w-full md:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search by email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                data-testid="search-input"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-12 text-gray-400">Loading...</div>
          ) : entries.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              {search ? "No matching entries found" : "No waitlist entries yet"}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10">
                      <TableHead className="text-gray-400">Email</TableHead>
                      <TableHead className="text-gray-400">Signed Up</TableHead>
                      <TableHead className="text-gray-400 text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {entries.map((entry) => (
                      <TableRow key={entry.id} className="border-white/10">
                        <TableCell className="text-white font-medium" data-testid={`email-${entry.id}`}>
                          {entry.email}
                        </TableCell>
                        <TableCell className="text-gray-400">
                          {formatDate(entry.created_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <AlertDialog open={deleteId === entry.id} onOpenChange={(open) => !open && setDeleteId(null)}>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-gray-400 hover:text-red-400 hover:bg-red-500/10"
                                onClick={() => setDeleteId(entry.id)}
                                data-testid={`delete-${entry.id}`}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent className="bg-[#0A0A0A] border-white/10">
                              <AlertDialogHeader>
                                <AlertDialogTitle className="text-white">Delete Entry?</AlertDialogTitle>
                                <AlertDialogDescription className="text-gray-400">
                                  This will permanently remove {entry.email} from the waitlist.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel className="bg-white/5 border-white/10 text-white hover:bg-white/10">
                                  Cancel
                                </AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDelete(entry.id)}
                                  className="bg-red-600 hover:bg-red-700"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-6 border-t border-white/10">
                  <p className="text-sm text-gray-400">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(Math.max(1, page - 1))}
                      disabled={page === 1}
                      className="border-white/10 text-white hover:bg-white/10 disabled:opacity-50"
                      data-testid="prev-page-btn"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(Math.min(totalPages, page + 1))}
                      disabled={page === totalPages}
                      className="border-white/10 text-white hover:bg-white/10 disabled:opacity-50"
                      data-testid="next-page-btn"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>
      </div>
    </main>
  );
}
