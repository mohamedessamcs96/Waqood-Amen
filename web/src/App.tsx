import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { AllCars } from './components/AllCars';
import { UnpaidCars } from './components/UnpaidCars';
import { AdminDashboard } from './components/AdminDashboard';
import { EmployeeDashboard } from './components/EmployeeDashboard';
import { Login } from './components/Login';
import { Globe, LogOut, Shield } from 'lucide-react';

function App() {
  const [language, setLanguage] = useState<'ar' | 'en'>('ar');
  const [user, setUser] = useState<{ role: 'admin' | 'employee' | null; name: string } | null>(null);

  const translations = {
    ar: {
      title: 'وقود آمن',
      subtitle: 'نظام المراقبة والحماية الذكي',
      allCars: 'جميع السيارات',
      unpaidCars: 'السيارات الغير مدفوعة',
      admin: 'لوحة الإدارة',
      employee: 'لوحة الموظف',
      logout: 'تسجيل الخروج',
      toggleLanguage: 'English'
    },
    en: {
      title: 'Waqood Secure',
      subtitle: 'Smart Monitoring & Protection System',
      allCars: 'All Cars',
      unpaidCars: 'Unpaid Cars',
      admin: 'Admin Dashboard',
      employee: 'Employee Dashboard',
      logout: 'Logout',
      toggleLanguage: 'العربية'
    }
  };

  const t = translations[language];

  const handleLogout = () => {
    setUser(null);
  };

  if (!user) {
    return <Login language={language} setLanguage={setLanguage} onLogin={setUser} />;
  }

  return (
    <Router>
      <div className={`min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 ${language === 'ar' ? 'rtl' : 'ltr'}`} dir={language === 'ar' ? 'rtl' : 'ltr'}>
        {/* Header */}
        <header className="bg-gradient-to-r from-blue-900 via-slate-800 to-slate-900 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <Shield className="w-10 h-10 text-cyan-400" />
                <div>
                  <h1 className="text-3xl mb-1">{t.title}</h1>
                  <p className="text-cyan-200 opacity-90">{t.subtitle}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-sm text-cyan-200">
                  {user.name} ({user.role === 'admin' ? t.admin : t.employee})
                </div>
                <button
                  onClick={() => setLanguage(language === 'ar' ? 'en' : 'ar')}
                  className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors"
                >
                  <Globe className="w-5 h-5" />
                  <span>{t.toggleLanguage}</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 bg-red-500/80 hover:bg-red-600 px-4 py-2 rounded-lg transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span>{t.logout}</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation language={language} translations={t} userRole={user.role} />

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={user.role === 'admin' ? <Navigate to="/admin" /> : <Navigate to="/employee" />} />
            <Route path="/admin" element={user.role === 'admin' ? <AdminDashboard language={language} /> : <Navigate to="/employee" />} />
            <Route path="/employee" element={<EmployeeDashboard language={language} />} />
            <Route path="/all-cars" element={<AllCars language={language} />} />
            <Route path="/unpaid" element={<UnpaidCars language={language} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function Navigation({ language, translations, userRole }: { language: 'ar' | 'en'; translations: any; userRole: 'admin' | 'employee' | null }) {
  const location = useLocation();

  return (
    <nav className="bg-gradient-to-r from-slate-800 to-slate-900 shadow-md border-b border-cyan-500/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex gap-4">
          {userRole === 'admin' && (
            <Link
              to="/admin"
              className={`px-6 py-4 border-b-4 transition-colors ${
                location.pathname === '/admin'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-300 hover:text-cyan-400 hover:border-cyan-500/50'
              }`}
            >
              {translations.admin}
            </Link>
          )}
          {userRole === 'employee' && (
            <Link
              to="/employee"
              className={`px-6 py-4 border-b-4 transition-colors ${
                location.pathname === '/employee'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-300 hover:text-cyan-400 hover:border-cyan-500/50'
              }`}
            >
              {translations.employee}
            </Link>
          )}
          <Link
            to="/all-cars"
            className={`px-6 py-4 border-b-4 transition-colors ${
              location.pathname === '/all-cars'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-300 hover:text-cyan-400 hover:border-cyan-500/50'
            }`}
          >
            {translations.allCars}
          </Link>
          <Link
            to="/unpaid"
            className={`px-6 py-4 border-b-4 transition-colors ${
              location.pathname === '/unpaid'
                ? 'border-red-400 text-red-300'
                : 'border-transparent text-slate-300 hover:text-red-400 hover:border-red-500/50'
            }`}
          >
            {translations.unpaidCars}
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default App;