import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as AlertDialog from "@radix-ui/react-alert-dialog";
import * as Tabs from "@radix-ui/react-tabs";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { toast, Toaster } from "sonner";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar,
} from "recharts";
import {
  MapPin, Calendar, Search, Star, Wifi, Wind, Car, Coffee,
  ChevronLeft, ChevronRight, Users, CreditCard, TrendingUp,
  Hotel, Settings, LayoutDashboard, BedDouble, X, CheckCircle,
  AlertCircle, DollarSign, BarChart2, Sparkles, ArrowRight,
  Shield, Globe, Edit2, ChevronDown, Phone, Mail, Check,
  LogOut, UserCircle, Eye, EyeOff, Lock, Plus, Trash2,
  ClipboardList, Wand2, PackageSearch, CalendarCheck,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────────

type Role = "guest" | "customer" | "admin" | "receptionist";

type View =
  | "auth"
  | "home"
  | "hotel-details"
  | "room"
  | "checkout"
  | "my-bookings"
  | "admin-dashboard"
  | "admin-settings"
  | "admin-inventory"
  | "receptionist-rooms";

type RoomStatus = "available" | "booked" | "in-use" | "maintenance";
type BookingStatus = "active" | "checked_in" | "completed" | "cancelled";

interface Room {
  id: number;
  number: string;
  type: string;
  floor: number;
  status: RoomStatus;
  price: number;
  capacity: number;
}

interface Booking {
  id: string;
  guest: string;
  room: string;
  roomName: string;
  hotel: string;
  check_in: string;
  check_out: string;
  status: BookingStatus;
  amount: number;
  phone: string;
}

interface SelectedRoom {
  hotelName: string;
  hotelLocation: string;
  roomName: string;
  pricePerNight: number;
  img: string;
}

// ── Mock Data ──────────────────────────────────────────────────────────────────

const TODAY = new Date("2026-07-21");

const HOTEL_CARDS = [
  { id: 1, name: "Grand Azure Resort", location: "Đà Nẵng, Việt Nam", rating: 4.9, reviews: 2341, price: 129, tags: ["Ven biển", "Hồ bơi", "Spa"], img: "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&h=380&fit=crop&auto=format", match: 98, desc: "Khu nghỉ dưỡng sang trọng bên bờ biển Mỹ Khê với dịch vụ đẳng cấp 5 sao và tầm nhìn tuyệt đẹp ra Biển Đông." },
  { id: 2, name: "Hanoi Heritage Hotel", location: "Hà Nội, Việt Nam", rating: 4.7, reviews: 1870, price: 99, tags: ["View phố cổ", "Nhà hàng", "Sân thượng"], img: "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&h=380&fit=crop&auto=format", match: 94, desc: "Khách sạn boutique nằm ngay trung tâm phố cổ Hà Nội, hòa quyện kiến trúc cổ điển và tiện nghi hiện đại." },
  { id: 3, name: "Saigon Sky Tower", location: "TP. Hồ Chí Minh, Việt Nam", rating: 4.8, reviews: 3102, price: 119, tags: ["Sky Bar", "Hội nghị", "Gym"], img: "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&h=380&fit=crop&auto=format", match: 91, desc: "Tòa tháp khách sạn hiện đại tại Quận 1 với tầm nhìn 360° toàn cảnh thành phố từ tầng 40." },
  { id: 4, name: "Hội An Riverside Inn", location: "Hội An, Việt Nam", rating: 4.6, reviews: 986, price: 79, tags: ["Di sản", "Vườn hoa", "Xe đạp"], img: "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=600&h=380&fit=crop&auto=format", match: 87, desc: "Nhà nghỉ ven sông Thu Bồn bao quanh bởi vườn hoa, cách phố cổ Hội An 5 phút đi bộ." },
];

const HOTEL_ROOM_TYPES: Record<number, { id: number; name: string; description: string; capacity: number; beds: string; price: number; available: number; total: number; img: string; }[]> = {
  1: [
    { id: 1, name: "Phòng Superior", description: "View vườn hoặc bể bơi, nội thất hiện đại", capacity: 2, beds: "1 giường đôi", price: 129, available: 4, total: 8, img: "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=500&h=300&fit=crop&auto=format" },
    { id: 2, name: "Phòng Deluxe hướng biển", description: "View trực diện biển, ban công riêng rộng rãi", capacity: 2, beds: "1 giường King", price: 189, available: 7, total: 12, img: "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=500&h=300&fit=crop&auto=format" },
    { id: 3, name: "Suite hướng biển", description: "Suite 52m² với phòng khách riêng và bồn tắm", capacity: 3, beds: "1 King + sofa bed", price: 320, available: 2, total: 4, img: "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop&auto=format" },
    { id: 4, name: "Penthouse Suite", description: "Tầng thượng, view 360°, bồn tắm ngoài trời", capacity: 4, beds: "2 giường King", price: 580, available: 1, total: 2, img: "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=500&h=300&fit=crop&auto=format" },
  ],
  2: [
    { id: 1, name: "Phòng Classic", description: "Phong cách cổ điển Hà Nội, view phố cổ", capacity: 2, beds: "1 giường đôi", price: 99, available: 5, total: 10, img: "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=500&h=300&fit=crop&auto=format" },
    { id: 2, name: "Phòng Deluxe Hồ Tây", description: "View Hồ Tây, nội thất gỗ truyền thống", capacity: 2, beds: "1 giường King", price: 139, available: 3, total: 8, img: "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=500&h=300&fit=crop&auto=format" },
    { id: 3, name: "Suite Heritage", description: "Tầng thượng, sân thượng riêng view phố cổ", capacity: 3, beds: "1 King + sofa", price: 259, available: 1, total: 3, img: "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop&auto=format" },
  ],
  3: [
    { id: 1, name: "Phòng Sky", description: "Tầng 20-30, view toàn thành phố", capacity: 2, beds: "1 giường Queen", price: 119, available: 8, total: 15, img: "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=500&h=300&fit=crop&auto=format" },
    { id: 2, name: "Phòng Sky Deluxe", description: "Tầng 31-40, view Sông Sài Gòn", capacity: 2, beds: "1 giường King", price: 189, available: 5, total: 10, img: "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=500&h=300&fit=crop&auto=format" },
    { id: 3, name: "Executive Suite", description: "Phòng họp riêng, lounge hạng thương gia", capacity: 3, beds: "1 King + sofa", price: 349, available: 2, total: 5, img: "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop&auto=format" },
  ],
  4: [
    { id: 1, name: "Phòng Garden", description: "View vườn hoa, không khí trong lành", capacity: 2, beds: "1 giường đôi", price: 79, available: 6, total: 10, img: "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=500&h=300&fit=crop&auto=format" },
    { id: 2, name: "Phòng Riverside", description: "View sông Thu Bồn, ban công riêng", capacity: 2, beds: "1 giường King", price: 119, available: 3, total: 8, img: "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=500&h=300&fit=crop&auto=format" },
    { id: 3, name: "Suite Riverside", description: "Suite 40m², bồn tắm ngoài trời view sông", capacity: 3, beds: "1 King + sofa", price: 229, available: 1, total: 3, img: "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=500&h=300&fit=crop&auto=format" },
  ],
};

const ROOM_GALLERY = [
  "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=900&h=560&fit=crop&auto=format",
  "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=900&h=560&fit=crop&auto=format",
  "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=900&h=560&fit=crop&auto=format",
  "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=900&h=560&fit=crop&auto=format",
];

const REVENUE_DATA = [
  { month: "Th1", revenue: 48200 }, { month: "Th2", revenue: 52100 },
  { month: "Th3", revenue: 61800 }, { month: "Th4", revenue: 58400 },
  { month: "Th5", revenue: 67300 }, { month: "Th6", revenue: 74200 },
  { month: "Th7", revenue: 81600 }, { month: "Th8", revenue: 78900 },
  { month: "Th9", revenue: 69400 }, { month: "Th10", revenue: 63100 },
  { month: "Th11", revenue: 58700 }, { month: "Th12", revenue: 85300 },
];

const PRICE_PREDICTION_DATA = [
  { week: "T1 Th1", current: 189, suggested: 199 }, { week: "T2 Th1", current: 189, suggested: 185 },
  { week: "T3 Th1", current: 189, suggested: 210 }, { week: "T4 Th1", current: 189, suggested: 225 },
  { week: "T1 Th2", current: 189, suggested: 195 }, { week: "T2 Th2", current: 189, suggested: 175 },
  { week: "T3 Th2", current: 189, suggested: 205 }, { week: "T4 Th2", current: 189, suggested: 240 },
];

const generateRooms = (): Room[] => {
  const types = ["Tiêu chuẩn", "Cao cấp", "Suite", "Hạng thương gia"];
  const statuses: RoomStatus[] = ["available", "booked", "in-use", "maintenance"];
  const weights = [0.40, 0.30, 0.20, 0.10];
  return Array.from({ length: 40 }, (_, i) => {
    const floor = Math.floor(i / 8) + 1;
    const num = (i % 8) + 1;
    const rand = Math.random();
    let cum = 0; let status: RoomStatus = "available";
    for (let j = 0; j < statuses.length; j++) { cum += weights[j]; if (rand < cum) { status = statuses[j]; break; } }
    const t = Math.floor(Math.random() * types.length);
    return { id: i + 1, number: `${floor}0${num}`, type: types[t], floor, status, price: [129, 189, 320, 259][t], capacity: [2, 2, 3, 2][t] };
  });
};

const INITIAL_ROOMS: Room[] = generateRooms();

const INITIAL_BOOKINGS: Booking[] = [
  { id: "BK-2401", guest: "Nguyễn Văn An", room: "302", roomName: "Suite Deluxe hướng biển", hotel: "Grand Azure Resort", check_in: "2026-07-28", check_out: "2026-07-31", status: "active", amount: 567, phone: "0912345678" },
  { id: "BK-2400", guest: "Trần Thị Bích", room: "415", roomName: "Phòng Deluxe Hồ Tây", hotel: "Hanoi Heritage Hotel", check_in: "2026-07-24", check_out: "2026-07-27", status: "active", amount: 380, phone: "0987654321" },
  { id: "BK-2399", guest: "Lê Minh Đức", room: "201", roomName: "Phòng Sky Deluxe", hotel: "Saigon Sky Tower", check_in: "2026-07-20", check_out: "2026-07-23", status: "checked_in", amount: 387, phone: "0901234567" },
  { id: "BK-2398", guest: "Phạm Hồng Nhung", room: "508", roomName: "Suite Riverside", hotel: "Hội An Riverside Inn", check_in: "2026-07-14", check_out: "2026-07-16", status: "cancelled", amount: 258, phone: "0976543210" },
  { id: "BK-2397", guest: "Hoàng Tuấn Anh", room: "104", roomName: "Phòng Superior", hotel: "Grand Azure Resort", check_in: "2026-07-12", check_out: "2026-07-14", status: "completed", amount: 258, phone: "0965432109" },
  { id: "BK-2396", guest: "Võ Thị Lan", room: "307", roomName: "Suite Heritage", hotel: "Hanoi Heritage Hotel", check_in: "2026-07-10", check_out: "2026-07-13", status: "completed", amount: 567, phone: "0954321098" },
];

// ── Helpers ────────────────────────────────────────────────────────────────────

const statusColor: Record<RoomStatus, string> = {
  available: "bg-emerald-500", booked: "bg-amber-400", "in-use": "bg-red-500", maintenance: "bg-slate-400",
};
const statusLabel: Record<RoomStatus, string> = {
  available: "Còn trống", booked: "Đã đặt", "in-use": "Đang dùng", maintenance: "Bảo trì",
};
const bookingStatusCfg: Record<string, { label: string; badge: string }> = {
  active: { label: "Đã đặt", badge: "bg-blue-100 text-blue-700" },
  checked_in: { label: "Đang ở", badge: "bg-emerald-100 text-emerald-700" },
  completed: { label: "Hoàn thành", badge: "bg-slate-100 text-slate-600" },
  cancelled: { label: "Đã hủy", badge: "bg-red-100 text-red-700" },
};
const roleLabel: Record<Role, string> = {
  guest: "Khách vãng lai", customer: "Khách hàng", admin: "Quản trị viên", receptionist: "Lễ tân",
};
const roleColor: Record<Role, string> = {
  guest: "bg-slate-100 text-slate-600", customer: "bg-blue-100 text-blue-700",
  admin: "bg-violet-100 text-violet-700", receptionist: "bg-emerald-100 text-emerald-700",
};

const canCancelBooking = (checkIn: string) => {
  const diff = Math.floor((new Date(checkIn).getTime() - TODAY.getTime()) / 86400000);
  return diff >= 7;
};
const fmtDate = (d: string) => new Date(d).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });

// ── Shared UI Primitives ───────────────────────────────────────────────────────

function Tip({ children, content }: { children: React.ReactNode; content: string }) {
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          className="bg-slate-900 text-white text-xs px-2.5 py-1.5 rounded-lg shadow-lg z-[100] max-w-[200px] text-center"
          sideOffset={5}
        >
          {content}
          <TooltipPrimitive.Arrow className="fill-slate-900" />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}

function ModalOverlay() {
  return <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in-0" />;
}

function DialogContent({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <Dialog.Content className={`fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl z-50 w-full focus:outline-none ${className}`}>
      {children}
    </Dialog.Content>
  );
}

function FakeQRCode({ amount, payMethod }: { amount: number; payMethod: string }) {
  const p = [
    [1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,0,1,1,0,1,1,0,0,0,0,0,1],
    [1,0,1,1,1,0,1,0,0,0,1,0,1,0,1,1,1,0,1],
    [1,0,1,1,1,0,1,0,1,0,0,1,1,0,1,1,1,0,1],
    [1,0,1,1,1,0,1,0,0,1,1,0,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,1,0,1,0,1,1,1,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,1,1,1,1],
    [0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0,0,0],
    [1,0,1,1,0,1,1,1,0,1,1,0,1,1,0,1,0,1,1],
    [0,1,1,0,1,0,0,0,1,0,1,1,0,0,1,0,1,1,0],
    [1,1,0,0,1,1,1,1,0,1,0,1,1,0,1,1,0,0,1],
    [0,0,1,1,0,0,0,0,1,1,0,0,0,1,0,1,0,1,0],
    [1,1,1,1,1,1,1,0,0,0,1,1,1,0,1,1,1,0,1],
    [0,0,0,0,0,0,0,0,1,0,0,1,0,1,0,0,0,1,0],
    [1,1,1,1,1,1,1,0,1,1,0,0,1,0,1,0,1,1,1],
    [1,0,0,0,0,0,1,0,0,0,1,1,0,1,0,0,0,0,1],
    [1,0,1,1,1,0,1,0,1,0,0,0,1,0,1,1,0,1,0],
    [1,0,1,1,1,0,1,0,0,1,1,0,0,1,0,0,1,0,1],
    [1,1,1,1,1,1,1,0,1,0,1,1,0,0,1,0,1,1,1],
  ];
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="bg-white p-3 rounded-xl border border-border shadow-inner">
        {p.map((row, ri) => (
          <div key={ri} className="flex">
            {row.map((c, ci) => <div key={ci} style={{ width: 10, height: 10 }} className={c ? "bg-slate-900" : "bg-white"} />)}
          </div>
        ))}
      </div>
      <div className="text-center">
        <p className="text-xs font-mono text-slate-500 bg-muted px-3 py-1 rounded-full">{payMethod} · ${amount.toLocaleString()}</p>
      </div>
    </div>
  );
}

function NavBtn({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${active ? "bg-secondary text-primary" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
      {icon}{children}
    </button>
  );
}

// ── AuthPage ──────────────────────────────────────────────────────────────────

function AuthPage({ setView, setRole }: { setView: (v: View) => void; setRole: (r: Role) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email || !password) { setError("Vui lòng nhập đầy đủ thông tin."); return; }
    if (password.length < 6) { setError("Mật khẩu phải có ít nhất 6 ký tự."); return; }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      const lower = email.toLowerCase();
      if (lower.includes("admin")) { setRole("admin"); setView("admin-dashboard"); }
      else if (lower.includes("letan")) { setRole("receptionist"); setView("receptionist-rooms"); }
      else { setRole("customer"); setView("home"); }
    }, 800);
  };

  const demos = [
    { label: "Khách hàng", email: "khach@staynow.com", cls: "bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100" },
    { label: "Quản trị viên", email: "admin@staynow.com", cls: "bg-violet-50 border-violet-200 text-violet-700 hover:bg-violet-100" },
    { label: "Lễ tân", email: "letan@staynow.com", cls: "bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-950 via-blue-900 to-blue-800 flex items-center justify-center p-4">
      <img src="https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=1600&h=900&fit=crop&auto=format" alt="" className="absolute inset-0 w-full h-full object-cover opacity-10" />
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-white/10 border border-white/20 backdrop-blur-sm mb-4">
            <Hotel size={28} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">StayNow</h1>
          <p className="text-blue-200 text-sm mt-1">Nền tảng đặt phòng khách sạn thông minh</p>
        </div>

        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          <div className="flex border-b border-border">
            {(["login", "register"] as const).map(m => (
              <button key={m} onClick={() => { setMode(m); setError(""); }} className={`flex-1 py-4 text-sm font-semibold transition-colors ${mode === m ? "text-primary border-b-2 border-primary bg-secondary/40" : "text-muted-foreground hover:text-foreground"}`}>
                {m === "login" ? "Đăng nhập" : "Đăng ký"}
              </button>
            ))}
          </div>

          <div className="p-8">
            <h2 className="text-xl font-bold text-foreground mb-1">{mode === "login" ? "Chào mừng trở lại!" : "Tạo tài khoản mới"}</h2>
            <p className="text-sm text-muted-foreground mb-6">{mode === "login" ? "Đăng nhập để tiếp tục trải nghiệm." : "Điền thông tin để bắt đầu hành trình."}</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === "register" && (
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Họ và tên</label>
                  <div className="relative">
                    <UserCircle size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input value={name} onChange={e => setName(e.target.value)} placeholder="Nguyễn Văn An" className="w-full bg-muted rounded-xl pl-10 pr-4 py-3 text-sm outline-none border border-transparent focus:border-primary/40 focus:bg-white transition-all" />
                  </div>
                </div>
              )}
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Địa chỉ Email</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="ban@email.com" className="w-full bg-muted rounded-xl pl-10 pr-4 py-3 text-sm outline-none border border-transparent focus:border-primary/40 focus:bg-white transition-all" />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Mật khẩu</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input type={showPass ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} placeholder="Tối thiểu 6 ký tự" className="w-full bg-muted rounded-xl pl-10 pr-12 py-3 text-sm outline-none border border-transparent focus:border-primary/40 focus:bg-white transition-all" />
                  <button type="button" onClick={() => setShowPass(v => !v)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              {error && (
                <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-xl px-3 py-2.5 text-sm text-red-600">
                  <AlertCircle size={14} />{error}
                </div>
              )}
              <button type="submit" disabled={loading} className="w-full bg-primary text-white font-semibold py-3.5 rounded-xl hover:bg-blue-700 active:scale-95 transition-all shadow-md flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed mt-2">
                {loading ? <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" /></svg> : <>{mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}<ArrowRight size={16} /></>}
              </button>
            </form>

            <div className="mt-5 pt-5 border-t border-border">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3 text-center">Thử nhanh với tài khoản demo</p>
              <div className="grid grid-cols-3 gap-2 mb-4">
                {demos.map(d => (
                  <button key={d.email} onClick={() => { setEmail(d.email); setPassword("password123"); }} className={`text-xs font-semibold py-2 px-2 rounded-xl border transition-colors text-center ${d.cls}`}>{d.label}</button>
                ))}
              </div>

              <button
                onClick={() => { setRole("guest"); setView("home"); }}
                className="w-full text-sm text-muted-foreground hover:text-primary font-medium py-2.5 rounded-xl border border-dashed border-border hover:border-primary/40 transition-all flex items-center justify-center gap-2"
              >
                <Globe size={15} />
                Khám phá ngay không cần đăng nhập
              </button>
            </div>
          </div>
        </div>
        <p className="text-blue-300/50 text-xs text-center mt-5">© 2026 StayNow · Nền tảng đặt phòng khách sạn thông minh.</p>
      </div>
    </div>
  );
}

// ── NavBar ────────────────────────────────────────────────────────────────────

function NavBar({ view, role, setView, setRole }: { view: View; role: Role; setView: (v: View) => void; setRole: (r: Role) => void }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const navLinks = () => {
    if (role === "customer") return (
      <>
        <NavBtn active={view === "home"} onClick={() => setView("home")}>Khám phá</NavBtn>
        <NavBtn active={view === "my-bookings"} onClick={() => setView("my-bookings")} icon={<ClipboardList size={14} />}>Đơn của tôi</NavBtn>
      </>
    );
    if (role === "guest") return (
      <NavBtn active={view === "home"} onClick={() => setView("home")}>Khám phá</NavBtn>
    );
    if (role === "admin") return (
      <>
        <NavBtn active={view === "admin-dashboard"} onClick={() => setView("admin-dashboard")} icon={<LayoutDashboard size={14} />}>Tổng quan</NavBtn>
        <NavBtn active={view === "admin-inventory"} onClick={() => setView("admin-inventory")} icon={<PackageSearch size={14} />}>Quản lý phòng</NavBtn>
        <NavBtn active={view === "admin-settings"} onClick={() => setView("admin-settings")} icon={<Settings size={14} />}>Cài đặt</NavBtn>
      </>
    );
    if (role === "receptionist") return (
      <NavBtn active={view === "receptionist-rooms"} onClick={() => setView("receptionist-rooms")} icon={<BedDouble size={14} />}>Quản lý phòng</NavBtn>
    );
    return null;
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <button onClick={() => setView("home")} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center"><Hotel size={16} className="text-white" /></div>
          <span className="text-lg font-bold text-foreground tracking-tight">StayNow</span>
        </button>
        <nav className="hidden md:flex items-center gap-1">{navLinks()}</nav>

        {role === "guest" ? (
          <button onClick={() => setView("auth")} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-blue-700 active:scale-95 transition-all shadow-sm">
            <UserCircle size={15} /> Đăng nhập / Đăng ký
          </button>
        ) : (
          <div className="relative">
            <button onClick={() => setMenuOpen(v => !v)} className="flex items-center gap-2.5 px-3 py-2 rounded-xl border border-border hover:bg-muted transition-colors">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center"><UserCircle size={18} className="text-primary" /></div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${roleColor[role]}`}>{roleLabel[role]}</span>
              <ChevronDown size={13} className="text-muted-foreground" />
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-full mt-2 w-52 bg-white border border-border rounded-2xl shadow-xl z-20 overflow-hidden">
                  <div className="px-4 py-3 border-b border-border bg-muted/40">
                    <p className="text-xs text-muted-foreground">Đang đăng nhập</p>
                    <p className={`text-xs font-bold mt-0.5 ${role === "admin" ? "text-violet-700" : role === "receptionist" ? "text-emerald-700" : "text-blue-700"}`}>{roleLabel[role]}</p>
                  </div>
                  <button onClick={() => { setMenuOpen(false); setRole("guest"); setView("auth"); }} className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors">
                    <LogOut size={15} />Đăng xuất
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

// ── Customer: HomePage ────────────────────────────────────────────────────────

function HomePage({ setView, setSelectedHotelId }: { setView: (v: View) => void; setSelectedHotelId: (id: number) => void }) {
  const [location, setLocation] = useState("");
  const [checkin, setCheckin] = useState("");
  const [checkout, setCheckout] = useState("");
  const [aiQuery, setAiQuery] = useState("");
  const [aiSearched, setAiSearched] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <section className="relative h-[580px] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-blue-800 to-blue-950" />
        <img src="https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=1600&h=700&fit=crop&auto=format" alt="Sảnh khách sạn" className="absolute inset-0 w-full h-full object-cover opacity-25" />
        <div className="absolute inset-0 bg-gradient-to-t from-blue-950/60 via-transparent to-transparent" />
        <div className="relative z-10 text-center px-6 w-full max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 text-sm text-blue-100 mb-6 backdrop-blur-sm">
            <Sparkles size={13} className="text-blue-300" />hơn 12.000 cơ sở lưu trú toàn quốc
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 leading-tight tracking-tight">Tìm chỗ nghỉ lý tưởng<br /><span className="text-blue-300">nhanh chóng &amp; thông minh</span></h1>
          <p className="text-blue-100/80 text-lg mb-10">Gợi ý thông minh dựa trên ngân sách và lịch sử đặt phòng của bạn</p>
          <div className="bg-white rounded-2xl shadow-2xl p-2 flex flex-col md:flex-row gap-2">
            <div className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-muted transition-colors">
              <MapPin size={18} className="text-primary flex-shrink-0" />
              <div className="flex flex-col text-left flex-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Địa điểm</span>
                <input value={location} onChange={e => setLocation(e.target.value)} placeholder="Bạn muốn đến đâu?" className="bg-transparent text-sm outline-none placeholder:text-slate-400 w-full" />
              </div>
            </div>
            <div className="w-px bg-border hidden md:block my-2" />
            <div className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-muted transition-colors">
              <Calendar size={18} className="text-primary flex-shrink-0" />
              <div className="flex flex-col text-left flex-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Nhận phòng</span>
                <input type="date" value={checkin} onChange={e => setCheckin(e.target.value)} className="bg-transparent text-sm outline-none w-full" />
              </div>
            </div>
            <div className="w-px bg-border hidden md:block my-2" />
            <div className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-muted transition-colors">
              <Calendar size={18} className="text-primary flex-shrink-0" />
              <div className="flex flex-col text-left flex-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Trả phòng</span>
                <input type="date" value={checkout} onChange={e => setCheckout(e.target.value)} className="bg-transparent text-sm outline-none w-full" />
              </div>
            </div>
            <button onClick={() => { setSelectedHotelId(1); setView("hotel-details"); }} className="flex items-center justify-center gap-2 bg-primary text-white font-semibold px-8 py-3 rounded-xl hover:bg-blue-700 active:scale-95 transition-all shadow-md">
              <Search size={18} />Tìm kiếm
            </button>
          </div>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 -mt-6 relative z-20">
        <div className="bg-white border border-border rounded-2xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center"><Sparkles size={15} className="text-white" /></div>
            <div>
              <h3 className="font-semibold text-foreground text-sm">Tìm kiếm ngữ nghĩa AI</h3>
              <p className="text-xs text-muted-foreground">Mô tả kỳ nghỉ lý tưởng bằng ngôn ngữ tự nhiên</p>
            </div>
          </div>
          <div className="flex gap-3">
            <input value={aiQuery} onChange={e => setAiQuery(e.target.value)} placeholder='Thử: "Khách sạn ven biển dưới 4tr, hồ bơi, spa, cuối tuần tháng 7"' className="flex-1 bg-muted rounded-xl px-4 py-3 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all placeholder:text-slate-400" />
            <button onClick={() => { setAiSearched(true); setSelectedHotelId(1); setView("hotel-details"); }} className="flex items-center gap-2 bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold px-6 py-3 rounded-xl hover:opacity-90 active:scale-95 transition-all text-sm whitespace-nowrap">
              <Sparkles size={15} />Hỏi AI
            </button>
          </div>
          {aiSearched && <div className="mt-3 text-xs text-violet-600 font-medium flex items-center gap-1.5"><Check size={12} />AI tìm thấy 8 cơ sở lưu trú phù hợp</div>}
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex items-end justify-between mb-8">
          <div>
            <div className="text-xs font-semibold text-primary uppercase tracking-widest mb-2">Gợi ý thông minh</div>
            <h2 className="text-3xl font-bold text-foreground">Phù hợp với ngân sách &amp; lịch sử của bạn</h2>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {HOTEL_CARDS.map(h => (
            <button key={h.id} onClick={() => { setSelectedHotelId(h.id); setView("hotel-details"); }} className="group bg-card border border-border rounded-2xl overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 text-left">
              <div className="relative h-48 bg-blue-100 overflow-hidden">
                <img src={h.img} alt={h.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                <div className="absolute top-3 left-3"><span className="bg-white/90 backdrop-blur-sm text-primary text-xs font-bold px-2.5 py-1 rounded-full">{h.match}% phù hợp</span></div>
              </div>
              <div className="p-4">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="font-semibold text-foreground text-sm leading-snug">{h.name}</h3>
                  <div className="flex items-center gap-1 flex-shrink-0"><Star size={12} className="text-amber-400 fill-amber-400" /><span className="text-xs font-semibold">{h.rating}</span></div>
                </div>
                <div className="flex items-center gap-1 mb-3"><MapPin size={11} className="text-muted-foreground" /><span className="text-xs text-muted-foreground">{h.location}</span></div>
                <div className="flex flex-wrap gap-1 mb-3">{h.tags.map(t => <span key={t} className="text-xs bg-secondary text-primary/80 px-2 py-0.5 rounded-full font-medium">{t}</span>)}</div>
                <div className="flex items-baseline gap-1"><span className="text-lg font-bold text-primary">từ ${h.price}</span><span className="text-xs text-muted-foreground">/đêm</span></div>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="bg-primary/5 border-y border-border py-12">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[{ icon: Hotel, label: "12.000+", sub: "Khách sạn xác minh" }, { icon: Users, label: "1,4 triệu+", sub: "Khách hàng hài lòng" }, { icon: Shield, label: "100%", sub: "Đặt phòng an toàn" }, { icon: Star, label: "4,8/5", sub: "Đánh giá trung bình" }].map(({ icon: Icon, label, sub }) => (
            <div key={sub} className="flex flex-col items-center text-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center"><Icon size={18} className="text-primary" /></div>
              <div className="text-2xl font-bold text-foreground">{label}</div>
              <div className="text-sm text-muted-foreground">{sub}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

// ── HotelDetailsPage (NEW) ────────────────────────────────────────────────────

function HotelDetailsPage({ setView, role, hotelId, setSelectedRoom }: { setView: (v: View) => void; role: Role; hotelId: number; setSelectedRoom: (r: SelectedRoom) => void }) {
  const [loginAlert, setLoginAlert] = useState(false);
  const hotel = HOTEL_CARDS.find(h => h.id === hotelId) ?? HOTEL_CARDS[0];
  const roomTypes = HOTEL_ROOM_TYPES[hotelId] ?? HOTEL_ROOM_TYPES[1];

  const handleBook = (rt: typeof roomTypes[0]) => {
    if (role === "guest") { setLoginAlert(true); return; }
    setSelectedRoom({ hotelName: hotel.name, hotelLocation: hotel.location, roomName: rt.name, pricePerNight: rt.price, img: rt.img });
    setView("checkout");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <div className="relative h-64 bg-blue-900 overflow-hidden">
        <img src={hotel.img} alt={hotel.name} className="w-full h-full object-cover opacity-60" />
        <div className="absolute inset-0 bg-gradient-to-t from-blue-950/80 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-6 max-w-7xl mx-auto">
          <nav className="flex items-center gap-2 text-sm text-blue-200/70 mb-3">
            <button onClick={() => setView("home")} className="hover:text-white transition-colors">Khám phá</button>
            <ChevronRight size={13} />
            <span className="text-white font-medium">{hotel.name}</span>
          </nav>
          <h1 className="text-3xl font-bold text-white mb-2">{hotel.name}</h1>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5"><MapPin size={13} className="text-blue-300" /><span className="text-sm text-blue-100">{hotel.location}</span></div>
            <div className="flex items-center gap-1"><Star size={13} className="text-amber-400 fill-amber-400" /><span className="text-sm text-white font-semibold">{hotel.rating}</span><span className="text-sm text-blue-200">({hotel.reviews.toLocaleString()} đánh giá)</span></div>
            {hotel.tags.map(t => <span key={t} className="text-xs bg-white/15 text-white px-2.5 py-1 rounded-full backdrop-blur-sm">{t}</span>)}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: info */}
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <h2 className="font-semibold text-foreground mb-3">Giới thiệu</h2>
              <p className="text-muted-foreground leading-relaxed text-sm">{hotel.desc}</p>
            </div>
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <h2 className="font-semibold text-foreground mb-4">Tiện ích khách sạn</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[{ icon: Wifi, label: "Wi-Fi miễn phí" }, { icon: Car, label: "Bãi đỗ xe" }, { icon: Coffee, label: "Nhà hàng" }, { icon: Wind, label: "Điều hòa" }, { icon: Shield, label: "Bảo vệ 24/7" }, { icon: Users, label: "Phòng hội nghị" }, { icon: Star, label: "Spa & Gym" }, { icon: Globe, label: "Đưa đón sân bay" }].map(({ icon: Icon, label }) => (
                  <div key={label} className="flex items-center gap-2 bg-secondary rounded-xl px-3 py-2.5">
                    <Icon size={14} className="text-primary flex-shrink-0" /><span className="text-xs font-medium">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Room types */}
            <div>
              <h2 className="font-bold text-foreground text-xl mb-4">Danh sách loại phòng</h2>
              <div className="space-y-4">
                {roomTypes.map(rt => (
                  <div key={rt.id} className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex flex-col md:flex-row">
                      <div className="relative w-full md:w-48 h-44 md:h-auto bg-blue-100 flex-shrink-0">
                        <img src={rt.img} alt={rt.name} className="w-full h-full object-cover" />
                        <div className={`absolute top-3 left-3 text-xs font-bold px-2.5 py-1 rounded-full ${rt.available > 0 ? "bg-emerald-500 text-white" : "bg-red-500 text-white"}`}>
                          {rt.available > 0 ? `${rt.available}/${rt.total} còn trống` : "Hết phòng"}
                        </div>
                      </div>
                      <div className="flex-1 p-5 flex flex-col justify-between">
                        <div>
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <h3 className="font-semibold text-foreground text-base">{rt.name}</h3>
                            <div className="flex items-baseline gap-1 flex-shrink-0">
                              <span className="text-xl font-bold text-primary">${rt.price}</span>
                              <span className="text-xs text-muted-foreground">/đêm</span>
                            </div>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{rt.description}</p>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1"><Users size={12} />{rt.capacity} khách</span>
                            <span className="flex items-center gap-1"><BedDouble size={12} />{rt.beds}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-end mt-4">
                          <button
                            onClick={() => handleBook(rt)}
                            disabled={rt.available === 0}
                            className="flex items-center gap-2 bg-primary text-white font-semibold px-6 py-2.5 rounded-xl hover:bg-blue-700 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed text-sm shadow-sm"
                          >
                            {rt.available > 0 ? <><CalendarCheck size={15} />Đặt phòng này</> : "Hết phòng"}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: quick info */}
          <div className="space-y-5">
            <div className="bg-card border border-border rounded-2xl p-5 shadow-sm sticky top-24">
              <h3 className="font-semibold text-foreground mb-4">Thông tin nhanh</h3>
              {[["Nhận phòng", "14:00"], ["Trả phòng", "12:00"], ["Loại", "Khách sạn 5 sao"], ["Chính sách hủy", "Miễn phí 48 giờ"], ["Thú cưng", "Không cho phép"]].map(([k, v]) => (
                <div key={k} className="flex justify-between py-2.5 border-b border-border/60 last:border-0 text-sm">
                  <span className="text-muted-foreground">{k}</span>
                  <span className="font-medium text-foreground">{v}</span>
                </div>
              ))}
              {role === "guest" && (
                <button onClick={() => setView("auth")} className="w-full mt-4 bg-primary text-white font-semibold py-3 rounded-xl hover:bg-blue-700 transition-colors text-sm flex items-center justify-center gap-2">
                  <UserCircle size={15} />Đăng nhập để đặt phòng
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Login required AlertDialog */}
      <AlertDialog.Root open={loginAlert} onOpenChange={setLoginAlert}>
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <AlertDialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl z-50 w-full max-w-sm p-6 focus:outline-none">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center"><Lock size={18} className="text-primary" /></div>
              <AlertDialog.Title className="font-bold text-foreground text-lg">Yêu cầu đăng nhập</AlertDialog.Title>
            </div>
            <AlertDialog.Description className="text-sm text-muted-foreground mb-6 leading-relaxed">
              Bạn cần đăng nhập hoặc tạo tài khoản để đặt phòng. Việc này chỉ mất vài giây!
            </AlertDialog.Description>
            <div className="flex gap-3">
              <AlertDialog.Cancel className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Để sau</AlertDialog.Cancel>
              <AlertDialog.Action onClick={() => setView("auth")} className="flex-1 py-2.5 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-blue-700 transition-colors">Đăng nhập ngay</AlertDialog.Action>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </div>
  );
}

// ── Customer: RoomPage ────────────────────────────────────────────────────────

function RoomPage({ setView, role }: { setView: (v: View) => void; role: Role }) {
  const [activeImg, setActiveImg] = useState(0);
  const [loginAlert, setLoginAlert] = useState(false);
  const AVAILABLE = 7; const TOTAL = 12;
  const pct = Math.round((AVAILABLE / TOTAL) * 100);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-10">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6">
          <button onClick={() => setView("home")} className="hover:text-primary transition-colors">Khám phá</button>
          <ChevronRight size={14} />
          <button onClick={() => setView("hotel-details")} className="hover:text-primary transition-colors">Grand Azure Resort</button>
          <ChevronRight size={14} />
          <span className="text-foreground font-medium">Phòng Deluxe hướng biển</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-10">
          <div className="lg:col-span-3 space-y-8">
            <div className="space-y-3">
              <div className="relative rounded-2xl overflow-hidden bg-blue-100 h-[400px]">
                <img src={ROOM_GALLERY[activeImg]} alt="Phòng" className="w-full h-full object-cover transition-opacity duration-300" />
                <button onClick={() => setActiveImg(i => (i - 1 + ROOM_GALLERY.length) % ROOM_GALLERY.length)} className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 rounded-full flex items-center justify-center shadow hover:bg-white transition-colors"><ChevronLeft size={18} /></button>
                <button onClick={() => setActiveImg(i => (i + 1) % ROOM_GALLERY.length)} className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-white/90 rounded-full flex items-center justify-center shadow hover:bg-white transition-colors"><ChevronRight size={18} /></button>
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5">
                  {ROOM_GALLERY.map((_, i) => <button key={i} onClick={() => setActiveImg(i)} className={`h-2 rounded-full transition-all ${i === activeImg ? "bg-white w-5" : "bg-white/50 w-2"}`} />)}
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {ROOM_GALLERY.map((img, i) => (
                  <button key={i} onClick={() => setActiveImg(i)} className={`rounded-xl overflow-hidden h-20 bg-blue-100 border-2 transition-all ${i === activeImg ? "border-primary" : "border-transparent"}`}>
                    <img src={img} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Suite Deluxe hướng biển</h1>
              <div className="flex items-center gap-3 flex-wrap mb-4">
                <div className="flex items-center gap-1">{[...Array(5)].map((_, i) => <Star key={i} size={14} className="text-amber-400 fill-amber-400" />)}</div>
                <span className="text-sm text-muted-foreground">4,9 · 2.341 đánh giá</span>
                <div className="flex items-center gap-1.5"><MapPin size={13} className="text-muted-foreground" /><span className="text-sm text-muted-foreground">Đà Nẵng, Việt Nam</span></div>
              </div>
              <p className="text-muted-foreground leading-relaxed mb-6">Thức dậy với tầm nhìn toàn cảnh ra biển từ suite rộng rãi 52m² có ban công riêng. Giường king-size, phòng tắm đá cẩm thạch với vòi hoa sen nhiệt đới và WiFi tốc độ cao.</p>
              <div>
                <h3 className="font-semibold text-foreground mb-3 text-sm uppercase tracking-wider">Tiện nghi</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[{ icon: Wifi, label: "Wi-Fi miễn phí" }, { icon: Wind, label: "Điều hòa" }, { icon: Car, label: "Bãi đỗ xe" }, { icon: Coffee, label: "Bữa sáng" }, { icon: Users, label: "Tối đa 2 khách" }, { icon: BedDouble, label: "Giường King" }, { icon: Globe, label: "Hướng biển" }, { icon: Shield, label: "Bảo vệ 24/7" }].map(({ icon: Icon, label }) => (
                    <div key={label} className="flex items-center gap-2.5 bg-secondary rounded-xl px-3 py-2.5">
                      <Icon size={15} className="text-primary flex-shrink-0" /><span className="text-xs font-medium">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-5">
            <div className="bg-white border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-foreground">Tình trạng phòng thực tế</h3>
                <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />Trực tiếp</span>
              </div>
              <div className="text-center mb-4">
                <div className="text-5xl font-bold text-foreground mb-1">{AVAILABLE}<span className="text-2xl text-muted-foreground font-normal">/{TOTAL}</span></div>
                <div className="text-sm text-muted-foreground">Phòng trống / Tổng sức chứa</div>
              </div>
              <div className="h-3 bg-muted rounded-full overflow-hidden mb-3">
                <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full" style={{ width: `${pct}%` }} />
              </div>
              <div className="flex justify-between text-xs text-muted-foreground mb-6">
                <span className="text-emerald-600 font-medium">{AVAILABLE} phòng còn trống</span>
                <span>{TOTAL - AVAILABLE} đã có khách</span>
              </div>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-3xl font-bold text-primary">$189</span>
                <span className="text-muted-foreground text-sm">/đêm</span>
              </div>
              <button
                onClick={() => role === "guest" ? setLoginAlert(true) : setView("checkout")}
                className="w-full bg-primary text-white font-semibold py-3.5 rounded-xl hover:bg-blue-700 active:scale-95 transition-all flex items-center justify-center gap-2 shadow-md"
              >
                {role === "guest" ? <><Lock size={15} />Đăng nhập để đặt phòng</> : <>Đặt phòng ngay<ArrowRight size={16} /></>}
              </button>
              {role === "guest" && <p className="text-xs text-center text-amber-600 mt-2 flex items-center justify-center gap-1"><AlertCircle size={11} />Yêu cầu tài khoản để đặt phòng</p>}
            </div>

            <div className="bg-white border border-border rounded-2xl p-5 shadow-sm">
              {[["Diện tích", "52 m²"], ["Sức chứa", "2 người lớn"], ["Loại giường", "King Size"], ["Tầng", "Tầng 8 – 15"], ["Hủy phòng", "Miễn phí trước 25/07"]].map(([k, v]) => (
                <div key={k} className="flex justify-between items-center py-2.5 border-b border-border last:border-0">
                  <span className="text-sm text-muted-foreground">{k}</span>
                  <span className="text-sm font-medium text-foreground">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <AlertDialog.Root open={loginAlert} onOpenChange={setLoginAlert}>
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <AlertDialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl z-50 w-full max-w-sm p-6 focus:outline-none">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center"><Lock size={18} className="text-primary" /></div>
              <AlertDialog.Title className="font-bold text-foreground text-lg">Yêu cầu đăng nhập</AlertDialog.Title>
            </div>
            <AlertDialog.Description className="text-sm text-muted-foreground mb-6 leading-relaxed">Bạn cần đăng nhập hoặc tạo tài khoản để đặt phòng.</AlertDialog.Description>
            <div className="flex gap-3">
              <AlertDialog.Cancel className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Để sau</AlertDialog.Cancel>
              <AlertDialog.Action onClick={() => setView("auth")} className="flex-1 py-2.5 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-blue-700 transition-colors">Đăng nhập ngay</AlertDialog.Action>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </div>
  );
}

// ── Customer: CheckoutPage ────────────────────────────────────────────────────

function CheckoutPage({ setView, selectedRoom, bookings, setBookings }: { setView: (v: View) => void; selectedRoom: SelectedRoom; bookings: Booking[]; setBookings: React.Dispatch<React.SetStateAction<Booking[]>> }) {
  const [quantity, setQuantity] = useState(1);
  const [payMethod, setPayMethod] = useState<"momo" | "vnpay">("momo");
  const [completed, setCompleted] = useState(false);
  const [qrOpen, setQrOpen] = useState(false);

  const nights = 3;
  const subtotal = selectedRoom.pricePerNight * nights * quantity;
  const tax = Math.round(subtotal * 0.1);
  const total = subtotal + tax;

  const handlePaySuccess = () => {
    setQrOpen(false);
    const newBooking: Booking = {
      id: `BK-${2402 + bookings.length}`,
      guest: "Nguyễn Văn An",
      room: "302",
      roomName: selectedRoom.roomName,
      hotel: selectedRoom.hotelName,
      check_in: "2026-07-25",
      check_out: "2026-07-28",
      status: "active",
      amount: total,
      phone: "0912345678",
    };
    setBookings(prev => [newBooking, ...prev]);
    setCompleted(true);
  };

  const handlePayFail = () => {
    setQrOpen(false);
    toast.error("Thanh toán thất bại. Vui lòng kiểm tra số dư ví và thử lại.");
  };

  if (completed) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-6"><CheckCircle size={40} className="text-emerald-500" /></div>
          <h2 className="text-3xl font-bold text-foreground mb-3">Đặt phòng thành công!</h2>
          <p className="text-muted-foreground mb-2">Xác nhận đã được gửi đến email của bạn.</p>
          <p className="text-sm text-muted-foreground mb-8">Mã đặt phòng: <span className="font-mono font-semibold text-foreground">BK-{2402 + bookings.length - 1}</span></p>
          <div className="bg-white border border-border rounded-2xl p-6 mb-8 text-left space-y-3">
            {[["Khách sạn", selectedRoom.hotelName], ["Loại phòng", selectedRoom.roomName], ["Nhận phòng", "25 tháng 7, 2026"], ["Trả phòng", "28 tháng 7, 2026"], ["Số lượng", `${quantity} phòng`], ["Tổng thanh toán", `$${total.toLocaleString()}`]].map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm"><span className="text-muted-foreground">{k}</span><span className="font-medium text-foreground">{v}</span></div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setView("my-bookings")} className="flex-1 border border-primary text-primary font-semibold py-3.5 rounded-xl hover:bg-secondary transition-colors flex items-center justify-center gap-2"><ClipboardList size={16} />Xem đơn của tôi</button>
            <button onClick={() => setView("home")} className="flex-1 bg-primary text-white font-semibold py-3.5 rounded-xl hover:bg-blue-700 transition-colors">Về trang chủ</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto px-6 py-10">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-8">
          <button onClick={() => setView("hotel-details")} className="hover:text-primary transition-colors">Chi tiết khách sạn</button>
          <ChevronRight size={14} /><span className="text-foreground font-medium">Thanh toán</span>
        </nav>
        <h1 className="text-3xl font-bold text-foreground mb-8">Hoàn tất đặt phòng</h1>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-white border border-border rounded-2xl p-6 shadow-sm">
              <h2 className="font-semibold text-foreground mb-5 flex items-center gap-2"><Users size={17} className="text-primary" />Thông tin khách hàng</h2>
              <div className="grid grid-cols-2 gap-4">
                {[{ label: "Họ", val: "Nguyễn" }, { label: "Tên", val: "Văn An" }].map(({ label, val }) => (
                  <div key={label}>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">{label}</label>
                    <input defaultValue={val} className="w-full bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" />
                  </div>
                ))}
                <div className="col-span-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Email</label>
                  <div className="relative"><Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" /><input defaultValue="nguyen.vanan@email.com" className="w-full bg-muted rounded-xl pl-10 pr-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" /></div>
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Số điện thoại</label>
                  <div className="relative"><Phone size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" /><input defaultValue="+84 912 345 678" className="w-full bg-muted rounded-xl pl-10 pr-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" /></div>
                </div>
              </div>
            </div>

            <div className="bg-white border border-border rounded-2xl p-6 shadow-sm">
              <h2 className="font-semibold text-foreground mb-5 flex items-center gap-2"><BedDouble size={17} className="text-primary" />Lựa chọn phòng</h2>
              <div className="flex items-center justify-between">
                <div><div className="font-medium text-foreground">{selectedRoom.roomName}</div><div className="text-sm text-muted-foreground">${selectedRoom.pricePerNight}/đêm · {nights} đêm</div></div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-muted-foreground">Số lượng (tối đa 5):</label>
                  <div className="relative">
                    <select value={quantity} onChange={e => setQuantity(Number(e.target.value))} className="appearance-none bg-secondary border border-border text-foreground font-semibold text-sm pl-4 pr-9 py-2.5 rounded-xl outline-none cursor-pointer">
                      {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n} phòng</option>)}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white border border-border rounded-2xl p-6 shadow-sm">
              <h2 className="font-semibold text-foreground mb-2 flex items-center gap-2"><CreditCard size={17} className="text-primary" />Phương thức thanh toán</h2>
              <p className="text-xs text-muted-foreground mb-5">Thanh toán 100% toàn bộ qua ví điện tử</p>
              <div className="grid grid-cols-2 gap-3 mb-5">
                {[{ id: "momo" as const, label: "MoMo", sub: "Ví điện tử MoMo", bg: "bg-[#ae2070]", abbr: "M" }, { id: "vnpay" as const, label: "VNPAY", sub: "Cổng thanh toán VNPAY", bg: "bg-[#0066b3]", abbr: "VN" }].map(pm => (
                  <button key={pm.id} onClick={() => setPayMethod(pm.id)} className={`relative flex flex-col items-center gap-3 p-5 rounded-2xl border-2 transition-all ${payMethod === pm.id ? "border-primary bg-secondary" : "border-border hover:border-primary/30"}`}>
                    <div className={`w-12 h-12 rounded-full ${pm.bg} flex items-center justify-center`}><span className="text-white font-bold text-sm">{pm.abbr}</span></div>
                    <div><div className="font-semibold text-foreground text-sm">{pm.label}</div><div className="text-xs text-muted-foreground">{pm.sub}</div></div>
                    {payMethod === pm.id && <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-primary flex items-center justify-center"><Check size={11} className="text-white" /></div>}
                  </button>
                ))}
              </div>
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-start gap-3 text-sm text-blue-700">
                <Shield size={16} className="flex-shrink-0 mt-0.5" />
                <span>Thanh toán bảo mật bằng mã hóa SSL 256-bit. Toàn bộ số tiền thu khi đặt phòng.</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white border border-border rounded-2xl p-6 shadow-sm sticky top-24">
              <h2 className="font-semibold text-foreground mb-5">Tóm tắt đặt phòng</h2>
              <div className="rounded-xl overflow-hidden mb-5 bg-blue-100 h-36"><img src={selectedRoom.img} alt="Phòng" className="w-full h-full object-cover" /></div>
              <div className="mb-4"><div className="font-semibold text-foreground">{selectedRoom.roomName}</div><div className="text-sm text-muted-foreground">{selectedRoom.hotelName} · {selectedRoom.hotelLocation}</div></div>
              <div className="space-y-2.5 mb-5">
                {[["Nhận phòng", "25 tháng 7, 2026"], ["Trả phòng", "28 tháng 7, 2026"], ["Lưu trú", `${nights} đêm`], ["Phòng", `${quantity}x ${selectedRoom.roomName.split(" ")[0]}`]].map(([k, v]) => (
                  <div key={k} className="flex justify-between text-sm"><span className="text-muted-foreground">{k}</span><span className="font-medium">{v}</span></div>
                ))}
              </div>
              <div className="border-t border-border pt-4 space-y-2 mb-5">
                <div className="flex justify-between text-sm"><span className="text-muted-foreground">${selectedRoom.pricePerNight} × {nights} đêm × {quantity}</span><span>${subtotal.toLocaleString()}</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted-foreground">Thuế &amp; phí (10%)</span><span>${tax.toLocaleString()}</span></div>
                <div className="flex justify-between font-bold text-lg pt-2 border-t border-border"><span>Tổng cộng</span><span className="text-primary">${total.toLocaleString()}</span></div>
              </div>
              <button onClick={() => setQrOpen(true)} className="w-full bg-primary text-white font-semibold py-4 rounded-xl hover:bg-blue-700 active:scale-95 transition-all shadow-md flex items-center justify-center gap-2 text-base">
                Thanh toán ${total.toLocaleString()} qua {payMethod === "momo" ? "MoMo" : "VNPAY"}
              </button>
              <p className="text-xs text-center text-muted-foreground mt-3">Khi đặt phòng, bạn đồng ý điều khoản dịch vụ.</p>
            </div>
          </div>
        </div>
      </div>

      {/* QR Payment Dialog */}
      <Dialog.Root open={qrOpen} onOpenChange={setQrOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <DialogContent className="max-w-sm p-0 overflow-hidden">
            <div className={`p-4 flex items-center gap-3 ${payMethod === "momo" ? "bg-[#ae2070]" : "bg-[#0066b3]"}`}>
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center"><span className="text-white font-bold text-lg">{payMethod === "momo" ? "M" : "VN"}</span></div>
              <div>
                <Dialog.Title className="font-bold text-white text-lg">{payMethod === "momo" ? "Thanh toán MoMo" : "Thanh toán VNPAY"}</Dialog.Title>
                <p className="text-white/80 text-sm">Quét mã QR để thanh toán</p>
              </div>
              <Dialog.Close className="ml-auto w-8 h-8 rounded-full bg-white/20 flex items-center justify-center hover:bg-white/30 transition-colors"><X size={14} className="text-white" /></Dialog.Close>
            </div>
            <div className="p-6 text-center">
              <FakeQRCode amount={total} payMethod={payMethod === "momo" ? "MoMo" : "VNPAY"} />
              <div className="mt-5 space-y-2">
                <div className="flex justify-between text-sm bg-muted rounded-xl px-4 py-2.5">
                  <span className="text-muted-foreground">Số tiền</span>
                  <span className="font-bold text-foreground">${total.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm bg-muted rounded-xl px-4 py-2.5">
                  <span className="text-muted-foreground">Nội dung</span>
                  <span className="font-medium text-foreground font-mono text-xs">STAYNOW-BK2402</span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-4 mb-5">Mã QR hết hạn sau <span className="font-semibold text-foreground">10:00</span> phút</p>
              <div className="grid grid-cols-2 gap-3">
                <button onClick={handlePayFail} className="py-3 rounded-xl border-2 border-red-200 bg-red-50 text-red-600 font-semibold text-sm hover:bg-red-100 transition-colors">Mô phỏng thất bại</button>
                <button onClick={handlePaySuccess} className={`py-3 rounded-xl text-white font-semibold text-sm hover:opacity-90 transition-all active:scale-95 ${payMethod === "momo" ? "bg-[#ae2070]" : "bg-[#0066b3]"}`}>Mô phỏng thành công</button>
              </div>
            </div>
          </DialogContent>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}

// ── Customer: MyBookingsPage (NEW) ────────────────────────────────────────────

function MyBookingsPage({ setView, bookings, setBookings }: { setView: (v: View) => void; bookings: Booking[]; setBookings: React.Dispatch<React.SetStateAction<Booking[]>> }) {
  const [cancelTarget, setCancelTarget] = useState<Booking | null>(null);
  const [filter, setFilter] = useState<"all" | BookingStatus>("all");

  const filtered = bookings.filter(b => filter === "all" || b.status === filter);

  const confirmCancel = () => {
    if (!cancelTarget) return;
    setBookings(prev => prev.map(b => b.id === cancelTarget.id ? { ...b, status: "cancelled" as BookingStatus } : b));
    toast.success(`Đã hủy đặt phòng ${cancelTarget.id} thành công.`);
    setCancelTarget(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Đơn đặt phòng của tôi</h1>
            <p className="text-muted-foreground text-sm mt-1">Quản lý và theo dõi tất cả đặt phòng</p>
          </div>
          <button onClick={() => setView("home")} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-blue-700 transition-colors">
            <Plus size={15} />Đặt phòng mới
          </button>
        </div>

        <div className="flex gap-2 mb-6 flex-wrap">
          {([["all", "Tất cả"], ["active", "Đã đặt"], ["checked_in", "Đang ở"], ["completed", "Hoàn thành"], ["cancelled", "Đã hủy"]] as [string, string][]).map(([val, label]) => (
            <button key={val} onClick={() => setFilter(val as typeof filter)} className={`text-sm px-4 py-1.5 rounded-xl font-medium transition-colors ${filter === val ? "bg-primary text-white" : "bg-white border border-border text-muted-foreground hover:border-primary/30"}`}>{label}</button>
          ))}
        </div>

        <div className="space-y-4">
          {filtered.length === 0 && (
            <div className="text-center py-16 text-muted-foreground">
              <ClipboardList size={40} className="mx-auto mb-3 opacity-30" />
              <p className="font-medium">Không có đơn đặt phòng nào</p>
            </div>
          )}
          {filtered.map(b => {
            const cancellable = canCancelBooking(b.check_in);
            const cfg = bookingStatusCfg[b.status] ?? bookingStatusCfg.active;
            return (
              <div key={b.id} className="bg-card border border-border rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex gap-4">
                    <div className="w-20 h-20 rounded-xl bg-blue-100 overflow-hidden flex-shrink-0">
                      <img src={HOTEL_CARDS.find(h => h.name === b.hotel)?.img ?? HOTEL_CARDS[0].img} alt="" className="w-full h-full object-cover" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-xs text-muted-foreground">{b.id}</span>
                        <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${cfg.badge}`}>{cfg.label}</span>
                      </div>
                      <h3 className="font-semibold text-foreground">{b.hotel}</h3>
                      <p className="text-sm text-muted-foreground">{b.roomName}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1"><Calendar size={11} />{fmtDate(b.check_in)} → {fmtDate(b.check_out)}</span>
                        <span className="font-semibold text-foreground">${b.amount.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  {b.status === "active" && (
                    cancellable ? (
                      <button onClick={() => setCancelTarget(b)} className="flex items-center gap-2 text-sm font-medium text-red-600 border border-red-200 bg-red-50 hover:bg-red-100 px-4 py-2 rounded-xl transition-colors whitespace-nowrap">
                        <X size={14} />Hủy đặt phòng
                      </button>
                    ) : (
                      <Tip content="Không thể hủy đơn trong vòng 7 ngày trước nhận phòng">
                        <div>
                          <button disabled className="flex items-center gap-2 text-sm font-medium text-slate-400 border border-slate-200 bg-slate-50 px-4 py-2 rounded-xl cursor-not-allowed whitespace-nowrap">
                            <X size={14} />Hủy đặt phòng
                          </button>
                        </div>
                      </Tip>
                    )
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <AlertDialog.Root open={!!cancelTarget} onOpenChange={open => !open && setCancelTarget(null)}>
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <AlertDialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl z-50 w-full max-w-sm p-6 focus:outline-none">
            <AlertDialog.Title className="font-bold text-foreground text-lg mb-2">Xác nhận hủy đặt phòng</AlertDialog.Title>
            <AlertDialog.Description className="text-sm text-muted-foreground mb-5 leading-relaxed">
              Bạn có chắc muốn hủy đặt phòng <span className="font-semibold text-foreground">{cancelTarget?.id}</span>? Theo chính sách, bạn sẽ được hoàn <strong>100%</strong> giá trị đặt phòng.
            </AlertDialog.Description>
            <div className="flex gap-3">
              <AlertDialog.Cancel className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Giữ đặt phòng</AlertDialog.Cancel>
              <AlertDialog.Action onClick={confirmCancel} className="flex-1 py-2.5 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors">Xác nhận hủy</AlertDialog.Action>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </div>
  );
}

// ── Admin: Dashboard ──────────────────────────────────────────────────────────

function AdminDashboard({ bookings }: { bookings: Booking[] }) {
  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-foreground">Tổng quan</h1><p className="text-sm text-muted-foreground">Grand Azure Resort · Tháng 7 năm 2026</p></div>
        <select className="bg-white border border-border rounded-xl px-4 py-2 text-sm outline-none"><option>12 tháng gần nhất</option><option>30 ngày gần nhất</option><option>Tuần này</option></select>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        {[
          { label: "Tổng doanh thu", value: "$819.300", change: "+12,4%", up: true, icon: DollarSign, color: "bg-blue-50 text-blue-600" },
          { label: "Tổng đặt phòng", value: bookings.length.toString(), change: "+8,1%", up: true, icon: Calendar, color: "bg-emerald-50 text-emerald-600" },
          { label: "Tỷ lệ lấp đầy", value: "78,3%", change: "+3,2%", up: true, icon: BarChart2, color: "bg-violet-50 text-violet-600" },
          { label: "Giá TB/đêm", value: "$189", change: "-2,1%", up: false, icon: TrendingUp, color: "bg-amber-50 text-amber-600" },
        ].map(({ label, value, change, up, icon: Icon, color }) => (
          <div key={label} className="bg-card border border-border rounded-2xl p-5 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}><Icon size={18} /></div>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${up ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"}`}>{change}</span>
            </div>
            <div className="text-2xl font-bold text-foreground mb-1">{value}</div>
            <div className="text-sm text-muted-foreground">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-card border border-border rounded-2xl p-6 shadow-sm">
          <h2 className="font-semibold text-foreground mb-1">Tổng quan doanh thu</h2>
          <p className="text-sm text-muted-foreground mb-5">Doanh thu theo tháng năm 2026</p>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={REVENUE_DATA} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs><linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#1d4ed8" stopOpacity={0.15} /><stop offset="95%" stopColor="#1d4ed8" stopOpacity={0} /></linearGradient></defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
              <RechartsTooltip contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "12px", fontSize: 12 }} formatter={(v: number) => [`$${v.toLocaleString()}`, "Doanh thu"]} />
              <Area type="monotone" dataKey="revenue" stroke="#1d4ed8" strokeWidth={2} fill="url(#revGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-blue-600 flex items-center justify-center"><Sparkles size={13} className="text-white" /></div>
            <h2 className="font-semibold text-foreground text-sm">Dự báo giá AI</h2>
          </div>
          <p className="text-xs text-muted-foreground mb-4">Đề xuất điều chỉnh giá theo mùa</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={PRICE_PREDICTION_DATA} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="week" tick={{ fontSize: 9, fill: "#64748b" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
              <RechartsTooltip contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "10px", fontSize: 11 }} />
              <Bar dataKey="current" fill="#dbeafe" name="Giá hiện tại" radius={[3, 3, 0, 0]} />
              <Bar dataKey="suggested" fill="#1d4ed8" name="AI đề xuất" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 bg-violet-50 border border-violet-100 rounded-xl p-3 text-xs text-violet-700">
            <span className="font-semibold">Nhận xét AI:</span> Tăng giá 12–26% trong tuần 3–4 tháng 1 &amp; 2 — nhu cầu cao dựa trên lịch sử và sự kiện sắp tới.
          </div>
        </div>
      </div>

      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5"><h2 className="font-semibold text-foreground">Đặt phòng gần đây</h2></div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-xs text-muted-foreground uppercase tracking-wide border-b border-border">{["Mã", "Khách hàng", "Phòng", "Nhận phòng", "Trả phòng", "Trạng thái", "Số tiền"].map(h => <th key={h} className="text-left pb-3 pr-6 font-semibold">{h}</th>)}</tr></thead>
            <tbody>
              {bookings.map(b => {
                const cfg = bookingStatusCfg[b.status] ?? bookingStatusCfg.active;
                return (
                  <tr key={b.id} className="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="py-3.5 pr-6 font-mono text-xs font-semibold">{b.id}</td>
                    <td className="py-3.5 pr-6 font-medium">{b.guest}</td>
                    <td className="py-3.5 pr-6 text-muted-foreground">{b.room}</td>
                    <td className="py-3.5 pr-6 text-muted-foreground">{fmtDate(b.check_in)}</td>
                    <td className="py-3.5 pr-6 text-muted-foreground">{fmtDate(b.check_out)}</td>
                    <td className="py-3.5 pr-6"><span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.badge}`}>{cfg.label}</span></td>
                    <td className="py-3.5 font-semibold">${b.amount}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Admin: Settings ───────────────────────────────────────────────────────────

function AdminSettings({ bookings, setBookings }: { bookings: Booking[]; setBookings: React.Dispatch<React.SetStateAction<Booking[]>> }) {
  const [cancelPolicy, setCancelPolicy] = useState("48");
  const [refundPct, setRefundPct] = useState("100");
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2500); toast.success("Đã lưu chính sách thành công."); };
  const cancelBooking = (id: string) => { setBookings(prev => prev.map(b => b.id === id ? { ...b, status: "cancelled" as BookingStatus } : b)); toast.success(`Đã hủy đặt phòng ${id}.`); };

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <div><h1 className="text-2xl font-bold text-foreground">Cài đặt</h1><p className="text-sm text-muted-foreground">Quản lý đặt phòng và cấu hình chính sách</p></div>

      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center"><Shield size={16} className="text-primary" /></div>
          <div><h2 className="font-semibold text-foreground">Chính sách hủy phòng</h2><p className="text-xs text-muted-foreground">Cấu hình quy tắc hủy và hoàn tiền</p></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 block">Thời hạn hủy miễn phí</label>
            <div className="relative">
              <select value={cancelPolicy} onChange={e => setCancelPolicy(e.target.value)} className="w-full appearance-none bg-muted border border-border rounded-xl px-4 py-2.5 text-sm outline-none cursor-pointer">
                <option value="24">Trước 24 giờ</option><option value="48">Trước 48 giờ</option><option value="72">Trước 72 giờ</option><option value="168">Trước 7 ngày</option>
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 block">Mức hoàn tiền</label>
            <div className="relative">
              <select value={refundPct} onChange={e => setRefundPct(e.target.value)} className="w-full appearance-none bg-muted border border-border rounded-xl px-4 py-2.5 text-sm outline-none cursor-pointer">
                <option value="100">Hoàn 100%</option><option value="80">Hoàn 80%</option><option value="50">Hoàn 50%</option><option value="0">Không hoàn</option>
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
            </div>
          </div>
          <div className="flex items-end">
            <button onClick={handleSave} className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all ${saved ? "bg-emerald-500 text-white" : "bg-primary text-white hover:bg-blue-700"}`}>
              {saved ? <><Check size={15} />Đã lưu!</> : "Lưu chính sách"}
            </button>
          </div>
        </div>
        <div className="mt-4 p-4 bg-blue-50 border border-blue-100 rounded-xl text-sm text-blue-700">
          <span className="font-semibold">Hiện tại:</span> Hủy trước <strong>{cancelPolicy} giờ</strong> được hoàn <strong>{refundPct}%</strong>.
        </div>
      </div>

      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center"><Calendar size={16} className="text-primary" /></div>
          <div><h2 className="font-semibold text-foreground">Quản lý đặt phòng</h2><p className="text-xs text-muted-foreground">Xem và quản lý tất cả đặt phòng</p></div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-xs text-muted-foreground uppercase tracking-wide border-b border-border">{["Mã", "Khách hàng", "Phòng", "Nhận phòng", "Trả phòng", "Số tiền", "Trạng thái", "Thao tác"].map(h => <th key={h} className="text-left pb-3 pr-4 font-semibold">{h}</th>)}</tr></thead>
            <tbody>
              {bookings.map(b => {
                const cfg = bookingStatusCfg[b.status] ?? bookingStatusCfg.active;
                return (
                  <tr key={b.id} className="border-b border-border/50 last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="py-3.5 pr-4 font-mono text-xs font-semibold">{b.id}</td>
                    <td className="py-3.5 pr-4 font-medium">{b.guest}</td>
                    <td className="py-3.5 pr-4 text-muted-foreground">{b.room}</td>
                    <td className="py-3.5 pr-4 text-muted-foreground text-xs">{fmtDate(b.check_in)}</td>
                    <td className="py-3.5 pr-4 text-muted-foreground text-xs">{fmtDate(b.check_out)}</td>
                    <td className="py-3.5 pr-4 font-semibold">${b.amount}</td>
                    <td className="py-3.5 pr-4"><span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.badge}`}>{cfg.label}</span></td>
                    <td className="py-3.5">
                      <div className="flex items-center gap-2">
                        {b.status === "active" && <button onClick={() => cancelBooking(b.id)} className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 px-2.5 py-1.5 rounded-lg transition-colors"><X size={11} />Hủy</button>}
                        <button className="flex items-center gap-1 text-xs font-medium text-muted-foreground bg-muted hover:bg-border px-2.5 py-1.5 rounded-lg transition-colors"><Edit2 size={11} />Sửa</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Admin: Inventory (NEW) ────────────────────────────────────────────────────

function AdminInventoryPage({ rooms, setRooms }: { rooms: Room[]; setRooms: React.Dispatch<React.SetStateAction<Room[]>> }) {
  const emptyForm = { number: "", type: "Tiêu chuẩn", floor: "1", capacity: "2", price: "129", status: "available" as RoomStatus };
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Room | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Room | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggested, setAiSuggested] = useState(false);
  const [search, setSearch] = useState("");

  const openAdd = () => { setForm(emptyForm); setEditTarget(null); setAiSuggested(false); setFormOpen(true); };
  const openEdit = (r: Room) => { setForm({ number: r.number, type: r.type, floor: String(r.floor), capacity: String(r.capacity), price: String(r.price), status: r.status }); setEditTarget(r); setAiSuggested(false); setFormOpen(true); };

  const handleSave = () => {
    if (!form.number.trim()) { toast.error("Vui lòng nhập số phòng."); return; }
    if (editTarget) {
      setRooms(prev => prev.map(r => r.id === editTarget.id ? { ...r, ...form, floor: Number(form.floor), capacity: Number(form.capacity), price: Number(form.price) } : r));
      toast.success(`Đã cập nhật phòng ${form.number}.`);
    } else {
      const newRoom: Room = { id: Date.now(), number: form.number, type: form.type, floor: Number(form.floor), status: form.status, price: Number(form.price), capacity: Number(form.capacity) };
      setRooms(prev => [newRoom, ...prev]);
      toast.success(`Đã thêm phòng ${form.number}.`);
    }
    setFormOpen(false);
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    setRooms(prev => prev.filter(r => r.id !== deleteTarget.id));
    toast.success(`Đã xóa phòng ${deleteTarget.number}.`);
    setDeleteTarget(null);
  };

  const handleAiPrice = () => {
    setAiLoading(true);
    setTimeout(() => {
      const suggested = Math.round(Number(form.price || "129") * 1.15);
      setForm(f => ({ ...f, price: String(suggested) }));
      setAiLoading(false);
      setAiSuggested(true);
    }, 1000);
  };

  const filtered = rooms.filter(r => !search || r.number.includes(search) || r.type.toLowerCase().includes(search.toLowerCase()));
  const isOccupied = (r: Room) => r.status === "booked" || r.status === "in-use";

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-foreground">Quản lý phòng</h1><p className="text-sm text-muted-foreground">{rooms.length} phòng · {rooms.filter(r => r.status === "available").length} còn trống</p></div>
        <button onClick={openAdd} className="flex items-center gap-2 bg-primary text-white font-semibold px-5 py-2.5 rounded-xl hover:bg-blue-700 active:scale-95 transition-all text-sm shadow-sm"><Plus size={16} />Thêm phòng mới</button>
      </div>

      <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="relative max-w-xs">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm theo số phòng hoặc loại..." className="w-full bg-muted rounded-xl pl-10 pr-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-xs text-muted-foreground uppercase tracking-wide border-b border-border bg-muted/30">{["Số phòng", "Loại phòng", "Tầng", "Sức chứa", "Giá/đêm", "Trạng thái", "Thao tác"].map(h => <th key={h} className="text-left px-4 py-3 font-semibold">{h}</th>)}</tr></thead>
            <tbody>
              {filtered.map(r => (
                <tr key={r.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3.5 font-bold font-mono text-foreground">{r.number}</td>
                  <td className="px-4 py-3.5 text-foreground">{r.type}</td>
                  <td className="px-4 py-3.5 text-muted-foreground">Tầng {r.floor}</td>
                  <td className="px-4 py-3.5 text-muted-foreground">{r.capacity} khách</td>
                  <td className="px-4 py-3.5 font-semibold text-foreground">${r.price}</td>
                  <td className="px-4 py-3.5">
                    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full
                      ${r.status === "available" ? "bg-emerald-100 text-emerald-700" : ""}
                      ${r.status === "booked" ? "bg-amber-100 text-amber-700" : ""}
                      ${r.status === "in-use" ? "bg-red-100 text-red-700" : ""}
                      ${r.status === "maintenance" ? "bg-slate-100 text-slate-600" : ""}
                    `}>
                      <div className={`w-1.5 h-1.5 rounded-full ${statusColor[r.status]}`} />
                      {statusLabel[r.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <button onClick={() => openEdit(r)} className="flex items-center gap-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 px-2.5 py-1.5 rounded-lg transition-colors"><Edit2 size={11} />Sửa</button>
                      {isOccupied(r) ? (
                        <Tip content="Không thể xóa phòng đang có khách">
                          <div><button disabled className="flex items-center gap-1 text-xs font-medium text-slate-400 bg-slate-50 px-2.5 py-1.5 rounded-lg cursor-not-allowed"><Trash2 size={11} />Xóa</button></div>
                        </Tip>
                      ) : (
                        <button onClick={() => setDeleteTarget(r)} className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 px-2.5 py-1.5 rounded-lg transition-colors"><Trash2 size={11} />Xóa</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add/Edit Dialog */}
      <Dialog.Root open={formOpen} onOpenChange={setFormOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <DialogContent className="max-w-md p-6">
            <div className="flex items-center justify-between mb-6">
              <Dialog.Title className="text-xl font-bold text-foreground">{editTarget ? `Sửa phòng ${editTarget.number}` : "Thêm phòng mới"}</Dialog.Title>
              <Dialog.Close className="w-8 h-8 rounded-full bg-muted flex items-center justify-center hover:bg-border transition-colors"><X size={15} /></Dialog.Close>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Số phòng</label>
                  <input value={form.number} onChange={e => setForm(f => ({ ...f, number: e.target.value }))} placeholder="101" className="w-full bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Tầng</label>
                  <input type="number" min="1" max="20" value={form.floor} onChange={e => setForm(f => ({ ...f, floor: e.target.value }))} className="w-full bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Loại phòng</label>
                <div className="relative">
                  <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))} className="w-full appearance-none bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all cursor-pointer">
                    {["Tiêu chuẩn", "Cao cấp", "Suite", "Hạng thương gia"].map(t => <option key={t}>{t}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Sức chứa</label>
                  <input type="number" min="1" max="10" value={form.capacity} onChange={e => setForm(f => ({ ...f, capacity: e.target.value }))} className="w-full bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Trạng thái</label>
                  <div className="relative">
                    <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value as RoomStatus }))} className="w-full appearance-none bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all cursor-pointer">
                      <option value="available">Còn trống</option><option value="maintenance">Bảo trì</option>
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground" />
                  </div>
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5 block">Giá / đêm ($)</label>
                <div className="flex gap-2">
                  <input type="number" min="0" value={form.price} onChange={e => { setForm(f => ({ ...f, price: e.target.value })); setAiSuggested(false); }} className="flex-1 bg-muted rounded-xl px-4 py-2.5 text-sm outline-none border border-transparent focus:border-primary/30 focus:bg-white transition-all" />
                  <button onClick={handleAiPrice} disabled={aiLoading} className="flex items-center gap-2 bg-gradient-to-r from-violet-600 to-blue-600 text-white font-semibold px-4 py-2.5 rounded-xl hover:opacity-90 active:scale-95 transition-all text-xs disabled:opacity-70 whitespace-nowrap">
                    {aiLoading ? <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" /></svg> : <Wand2 size={14} />}
                    Dự đoán AI
                  </button>
                </div>
                {aiSuggested && (
                  <p className="text-xs text-violet-600 font-medium mt-1.5 flex items-center gap-1"><Sparkles size={11} />AI đã đề xuất giá tối ưu theo mùa (+15%)</p>
                )}
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <Dialog.Close className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Hủy</Dialog.Close>
              <button onClick={handleSave} className="flex-1 py-2.5 rounded-xl bg-primary text-white text-sm font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
                <Check size={15} />{editTarget ? "Lưu thay đổi" : "Thêm phòng"}
              </button>
            </div>
          </DialogContent>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Delete confirm */}
      <AlertDialog.Root open={!!deleteTarget} onOpenChange={open => !open && setDeleteTarget(null)}>
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <AlertDialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl z-50 w-full max-w-sm p-6 focus:outline-none">
            <AlertDialog.Title className="font-bold text-foreground text-lg mb-2">Xóa phòng {deleteTarget?.number}?</AlertDialog.Title>
            <AlertDialog.Description className="text-sm text-muted-foreground mb-5">Hành động này không thể hoàn tác. Phòng sẽ bị xóa vĩnh viễn khỏi hệ thống.</AlertDialog.Description>
            <div className="flex gap-3">
              <AlertDialog.Cancel className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium text-muted-foreground hover:bg-muted transition-colors">Hủy</AlertDialog.Cancel>
              <AlertDialog.Action onClick={handleDelete} className="flex-1 py-2.5 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors">Xóa phòng</AlertDialog.Action>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </div>
  );
}

// ── Receptionist: Rooms (with Tabs) ──────────────────────────────────────────

function ReceptionistRooms({ rooms, setRooms, bookings, setBookings }: { rooms: Room[]; setRooms: React.Dispatch<React.SetStateAction<Room[]>>; bookings: Booking[]; setBookings: React.Dispatch<React.SetStateAction<Booking[]>> }) {
  const [popup, setPopup] = useState<Room | null>(null);
  const [filterStatus, setFilterStatus] = useState<RoomStatus | "all">("all");
  const [filterFloor, setFilterFloor] = useState<number | "all">("all");
  const [search, setSearch] = useState("");

  const counts = { available: rooms.filter(r => r.status === "available").length, booked: rooms.filter(r => r.status === "booked").length, "in-use": rooms.filter(r => r.status === "in-use").length, maintenance: rooms.filter(r => r.status === "maintenance").length };

  const filteredRooms = rooms.filter(r => (filterStatus === "all" || r.status === filterStatus) && (filterFloor === "all" || r.floor === filterFloor));

  const filteredBookings = bookings.filter(b => {
    if (!search) return true;
    const q = search.toLowerCase();
    return b.id.toLowerCase().includes(q) || b.guest.toLowerCase().includes(q) || b.phone.includes(q);
  });

  const updateRoomStatus = (id: number, status: RoomStatus) => { setRooms(prev => prev.map(r => r.id === id ? { ...r, status } : r)); setPopup(null); };

  const handleCheckin = (b: Booking) => {
    setBookings(prev => prev.map(bk => bk.id === b.id ? { ...bk, status: "checked_in" as BookingStatus } : bk));
    setRooms(prev => prev.map(r => r.number === b.room ? { ...r, status: "in-use" as RoomStatus } : r));
    toast.success(`Check-in thành công cho ${b.guest} — Phòng ${b.room}`);
  };

  const handleCheckout = (b: Booking) => {
    setBookings(prev => prev.map(bk => bk.id === b.id ? { ...bk, status: "completed" as BookingStatus } : bk));
    setRooms(prev => prev.map(r => r.number === b.room ? { ...r, status: "available" as RoomStatus } : r));
    toast.success(`Check-out thành công — Phòng ${b.room} đã được giải phóng`);
  };

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-foreground">Quản lý phòng — Lễ tân</h1><p className="text-sm text-muted-foreground">Xử lý check-in / check-out tại quầy</p></div>
        <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium bg-emerald-50 px-3 py-1.5 rounded-full"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />Cập nhật trực tiếp</span>
      </div>

      <Tabs.Root defaultValue="grid" className="space-y-5">
        <Tabs.List className="flex bg-muted p-1 rounded-xl w-fit gap-1">
          {[{ val: "grid", label: "Sơ đồ phòng", icon: <BedDouble size={14} /> }, { val: "bookings", label: "Danh sách đơn", icon: <ClipboardList size={14} /> }].map(t => (
            <Tabs.Trigger key={t.val} value={t.val} className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all text-muted-foreground data-[state=active]:bg-white data-[state=active]:text-foreground data-[state=active]:shadow-sm">
              {t.icon}{t.label}
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        {/* Tab 1: Room Grid */}
        <Tabs.Content value="grid" className="space-y-5 focus:outline-none">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(["available", "booked", "in-use", "maintenance"] as RoomStatus[]).map(s => (
              <button key={s} onClick={() => setFilterStatus(filterStatus === s ? "all" : s)} className={`flex items-center gap-3 bg-card border rounded-xl p-4 shadow-sm transition-all ${filterStatus === s ? "border-primary ring-2 ring-primary/20" : "border-border hover:border-primary/30"}`}>
                <div className={`w-4 h-4 rounded-full flex-shrink-0 ${statusColor[s]}`} />
                <div className="text-left"><div className="text-lg font-bold text-foreground">{counts[s]}</div><div className="text-xs text-muted-foreground">{statusLabel[s]}</div></div>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-muted-foreground font-medium">Tầng:</span>
            <div className="flex gap-1">
              {(["all", 1, 2, 3, 4, 5] as (number | "all")[]).map(f => (
                <button key={f} onClick={() => setFilterFloor(f)} className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-colors ${filterFloor === f ? "bg-primary text-white" : "bg-white border border-border text-muted-foreground hover:border-primary/30"}`}>
                  {f === "all" ? "Tất cả" : `T${f}`}
                </button>
              ))}
            </div>
            {filterStatus !== "all" && <button onClick={() => setFilterStatus("all")} className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"><X size={12} />Xóa lọc</button>}
          </div>
          <div className="space-y-4">
            {(filterFloor === "all" ? [1, 2, 3, 4, 5] : [filterFloor as number]).map(floor => {
              const fr = filteredRooms.filter(r => r.floor === floor);
              if (!fr.length) return null;
              return (
                <div key={floor} className="bg-card border border-border rounded-2xl p-5 shadow-sm">
                  <div className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wide">Tầng {floor}</div>
                  <div className="grid grid-cols-4 md:grid-cols-8 gap-2.5">
                    {fr.map(room => (
                      <button key={room.id} onClick={() => setPopup(room)} title={`Phòng ${room.number} — ${statusLabel[room.status]}`} className={`relative group flex flex-col items-center justify-center rounded-xl p-3 border-2 transition-all hover:scale-105 hover:shadow-md ${room.status === "available" ? "bg-emerald-50 border-emerald-200 hover:border-emerald-400" : ""} ${room.status === "booked" ? "bg-amber-50 border-amber-200 hover:border-amber-400" : ""} ${room.status === "in-use" ? "bg-red-50 border-red-200 hover:border-red-400" : ""} ${room.status === "maintenance" ? "bg-slate-100 border-slate-200 hover:border-slate-400" : ""}`}>
                        <div className={`w-3 h-3 rounded-full mb-1.5 ${statusColor[room.status]}`} />
                        <span className="text-xs font-bold text-foreground">{room.number}</span>
                        <span className="text-[10px] text-muted-foreground leading-tight hidden md:block">{room.type.split(" ")[0]}</span>
                        <div className="absolute -top-1 -right-1 opacity-0 group-hover:opacity-100 transition-opacity"><div className="w-4 h-4 rounded-full bg-primary flex items-center justify-center"><Edit2 size={9} className="text-white" /></div></div>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Tabs.Content>

        {/* Tab 2: Booking List */}
        <Tabs.Content value="bookings" className="focus:outline-none space-y-4">
          <div className="relative max-w-sm">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm theo mã, tên, số điện thoại..." className="w-full bg-white border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm outline-none focus:border-primary/40 transition-all" />
          </div>
          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-xs text-muted-foreground uppercase tracking-wide border-b border-border bg-muted/30">{["Mã đặt phòng", "Khách hàng", "SĐT", "Phòng", "Nhận phòng", "Trả phòng", "Trạng thái", "Thao tác"].map(h => <th key={h} className="text-left px-4 py-3 font-semibold">{h}</th>)}</tr></thead>
                <tbody>
                  {filteredBookings.map(b => {
                    const cfg = bookingStatusCfg[b.status] ?? bookingStatusCfg.active;
                    return (
                      <tr key={b.id} className="border-b border-border/50 last:border-0 hover:bg-muted/20 transition-colors">
                        <td className="px-4 py-3.5 font-mono text-xs font-semibold">{b.id}</td>
                        <td className="px-4 py-3.5 font-medium">{b.guest}</td>
                        <td className="px-4 py-3.5 text-muted-foreground">{b.phone}</td>
                        <td className="px-4 py-3.5 font-bold text-foreground">{b.room}</td>
                        <td className="px-4 py-3.5 text-muted-foreground text-xs">{fmtDate(b.check_in)}</td>
                        <td className="px-4 py-3.5 text-muted-foreground text-xs">{fmtDate(b.check_out)}</td>
                        <td className="px-4 py-3.5"><span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.badge}`}>{cfg.label}</span></td>
                        <td className="px-4 py-3.5">
                          {b.status === "active" && (
                            <button onClick={() => handleCheckin(b)} className="flex items-center gap-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap">
                              <CheckCircle size={12} />Check-in
                            </button>
                          )}
                          {b.status === "checked_in" && (
                            <button onClick={() => handleCheckout(b)} className="flex items-center gap-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap">
                              <LogOut size={12} />Check-out
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </Tabs.Content>
      </Tabs.Root>

      {/* Status Popup */}
      {popup && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setPopup(null)}>
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-5">
              <div><h3 className="font-bold text-foreground text-lg">Phòng {popup.number}</h3><p className="text-sm text-muted-foreground">{popup.type} · Tầng {popup.floor} · ${popup.price}/đêm</p></div>
              <button onClick={() => setPopup(null)} className="w-8 h-8 rounded-full bg-muted flex items-center justify-center hover:bg-border transition-colors"><X size={15} /></button>
            </div>
            <div className="mb-4">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Trạng thái hiện tại</div>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold ${popup.status === "available" ? "bg-emerald-100 text-emerald-700" : ""} ${popup.status === "booked" ? "bg-amber-100 text-amber-700" : ""} ${popup.status === "in-use" ? "bg-red-100 text-red-700" : ""} ${popup.status === "maintenance" ? "bg-slate-100 text-slate-700" : ""}`}>
                <div className={`w-2 h-2 rounded-full ${statusColor[popup.status]}`} />{statusLabel[popup.status]}
              </div>
            </div>
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Đổi trạng thái thủ công</div>
            <div className="grid grid-cols-2 gap-2">
              {(["available", "booked", "in-use", "maintenance"] as RoomStatus[]).map(s => s !== popup.status && (
                <button key={s} onClick={() => updateRoomStatus(popup.id, s)} className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border-2 font-medium text-sm transition-all hover:scale-105 ${s === "available" ? "border-emerald-200 bg-emerald-50 text-emerald-700 hover:border-emerald-400" : ""} ${s === "booked" ? "border-amber-200 bg-amber-50 text-amber-700 hover:border-amber-400" : ""} ${s === "in-use" ? "border-red-200 bg-red-50 text-red-700 hover:border-red-400" : ""} ${s === "maintenance" ? "border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-400" : ""}`}>
                  <div className={`w-3 h-3 rounded-full flex-shrink-0 ${statusColor[s]}`} />{statusLabel[s]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Root App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [role, setRole] = useState<Role>("guest");
  const [view, setView] = useState<View>("auth");
  const [selectedHotelId, setSelectedHotelId] = useState<number>(1);
  const [selectedRoom, setSelectedRoom] = useState<SelectedRoom>({
    hotelName: "Grand Azure Resort",
    hotelLocation: "Đà Nẵng, Việt Nam",
    roomName: "Phòng Deluxe hướng biển",
    pricePerNight: 189,
    img: ROOM_GALLERY[1],
  });
  const [rooms, setRooms] = useState<Room[]>(INITIAL_ROOMS);
  const [bookings, setBookings] = useState<Booking[]>(INITIAL_BOOKINGS);

  const renderView = () => {
    switch (view) {
      case "auth": return <AuthPage setView={setView} setRole={setRole} />;
      case "home": return <HomePage setView={setView} setSelectedHotelId={setSelectedHotelId} />;
      case "hotel-details": return <HotelDetailsPage setView={setView} role={role} hotelId={selectedHotelId} setSelectedRoom={setSelectedRoom} />;
      case "room": return <RoomPage setView={setView} role={role} />;
      case "checkout": return <CheckoutPage setView={setView} selectedRoom={selectedRoom} bookings={bookings} setBookings={setBookings} />;
      case "my-bookings": return <MyBookingsPage setView={setView} bookings={bookings} setBookings={setBookings} />;
      case "admin-dashboard": return <AdminDashboard bookings={bookings} />;
      case "admin-settings": return <AdminSettings bookings={bookings} setBookings={setBookings} />;
      case "admin-inventory": return <AdminInventoryPage rooms={rooms} setRooms={setRooms} />;
      case "receptionist-rooms": return <ReceptionistRooms rooms={rooms} setRooms={setRooms} bookings={bookings} setBookings={setBookings} />;
    }
  };

  return (
    <TooltipPrimitive.Provider delayDuration={300}>
      <div className="min-h-screen bg-background font-[Inter,sans-serif]">
        <Toaster position="top-right" richColors closeButton />
        {view !== "auth" && <NavBar view={view} role={role} setView={setView} setRole={setRole} />}
        <main className={view !== "auth" ? "pt-16" : ""}>{renderView()}</main>
      </div>
    </TooltipPrimitive.Provider>
  );
}
