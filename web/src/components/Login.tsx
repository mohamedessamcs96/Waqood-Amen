import { useState } from 'react';
import { Shield, Globe, User, Lock } from 'lucide-react';
import { login as apiLogin, register as apiRegister } from '../api';

interface LoginProps {
  language: 'ar' | 'en';
  setLanguage: (lang: 'ar' | 'en') => void;
  onLogin: (user: { role: 'admin' | 'employee'; name: string }) => void;
}

export function Login({ language, setLanguage, onLogin }: LoginProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'admin' | 'employee'>('employee');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const translations = {
    ar: {
      title: 'وقود آمن',
      subtitle: 'نظام المراقبة والحماية الذكي',
      welcome: 'مرحباً بك',
      loginPrompt: 'الرجاء تسجيل الدخول للمتابعة',
      registerPrompt: 'إنشاء حساب جديد',
      username: 'اسم المستخدم',
      password: 'كلمة المرور',
      confirmPassword: 'تأكيد كلمة المرور',
      role: 'الدور',
      login: 'تسجيل الدخول',
      register: 'إنشاء حساب',
      adminDemo: 'تسجيل دخول كمدير',
      employeeDemo: 'تسجيل دخول كموظف',
      error: 'اسم المستخدم أو كلمة المرور غير صحيحة',
      demoNote: 'للتجربة: admin/admin أو employee/employee',
      toggleLanguage: 'English',
      switchToRegister: 'ليس لديك حساب؟ سجل هنا',
      switchToLogin: 'هل لديك حساب؟ سجل دخول',
      passwordMismatch: 'كلمات المرور غير متطابقة'
    },
    en: {
      title: 'Waqood Secure',
      subtitle: 'Smart Monitoring & Protection System',
      welcome: 'Welcome',
      loginPrompt: 'Please login to continue',
      registerPrompt: 'Create a new account',
      username: 'Username',
      password: 'Password',
      confirmPassword: 'Confirm Password',
      role: 'Role',
      login: 'Login',
      register: 'Register',
      adminDemo: 'Login as Admin',
      employeeDemo: 'Login as Employee',
      error: 'Invalid username or password',
      demoNote: 'Demo: admin/admin or employee/employee',
      toggleLanguage: 'العربية',
      switchToRegister: "Don't have an account? Register here",
      switchToLogin: 'Have an account? Login',
      passwordMismatch: 'Passwords do not match'
    }
  };

  const t = translations[language];

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const user = await apiLogin(username, password);
      onLogin(user);
    } catch (err: any) {
      setError(err.message || t.error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError(t.passwordMismatch);
      return;
    }
    setLoading(true);
    try {
      await apiRegister(username, password, role);
      setError('');
      alert('Registration successful! Please login with your credentials.');
      setIsRegister(false);
      setUsername('');
      setPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (demoRole: 'admin' | 'employee') => {
    setLoading(true);
    try {
      const user = await apiLogin(demoRole, demoRole);
      onLogin(user);
    } catch (err: any) {
      setError(err.message || t.error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen bg-gradient-to-br from-blue-950 via-slate-900 to-slate-950 flex items-center justify-center ${language === 'ar' ? 'rtl' : 'ltr'}`} dir={language === 'ar' ? 'rtl' : 'ltr'}>
      {/* Language Toggle */}
      <button
        onClick={() => setLanguage(language === 'ar' ? 'en' : 'ar')}
        className="absolute top-6 right-6 flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-colors"
      >
        <Globe className="w-5 h-5" />
        <span>{t.toggleLanguage}</span>
      </button>

      <div className="max-w-md w-full mx-4">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-br from-cyan-400 to-blue-600 p-4 rounded-2xl shadow-2xl">
              <Shield className="w-16 h-16 text-white" />
            </div>
          </div>
          <h1 className="text-4xl text-white mb-2 font-bold">{t.title}</h1>
          <p className="text-cyan-300">{t.subtitle}</p>
        </div>

        {/* Login Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl shadow-2xl p-8 border border-cyan-500/30">
          <h2 className="text-2xl text-white mb-2 font-semibold">
            {isRegister ? t.registerPrompt : t.welcome}
          </h2>
          <p className="text-slate-300 mb-6">
            {isRegister ? t.registerPrompt : t.loginPrompt}
          </p>

          <form onSubmit={isRegister ? handleRegister : handleLogin} className="space-y-4 mb-6">
            {error && (
              <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label className="block text-slate-300 mb-2">{t.username}</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-white/10 border border-cyan-500/30 text-white placeholder-gray-400 px-10 py-3 rounded-lg focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/50"
                  placeholder={t.username}
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-300 mb-2">{t.password}</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white/10 border border-cyan-500/30 text-white placeholder-gray-400 px-10 py-3 rounded-lg focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/50"
                  placeholder={t.password}
                  disabled={loading}
                />
              </div>
            </div>

            {isRegister && (
              <>
                <div>
                  <label className="block text-slate-300 mb-2">{t.confirmPassword}</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full bg-white/10 border border-cyan-500/30 text-white placeholder-gray-400 px-10 py-3 rounded-lg focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/50"
                      placeholder={t.confirmPassword}
                      disabled={loading}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 mb-2">{t.role}</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as 'admin' | 'employee')}
                    className="w-full bg-white/10 border border-cyan-500/30 text-white px-4 py-3 rounded-lg focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/50"
                    disabled={loading}
                  >
                    <option value="employee" className="bg-slate-900 text-white">{t.adminDemo}</option>
                    <option value="admin" className="bg-slate-900 text-white">Admin</option>
                  </select>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white py-3 rounded-lg transition-all shadow-lg hover:shadow-xl font-semibold"
            >
              {loading ? '...' : (isRegister ? t.register : t.login)}
            </button>
          </form>

          {/* Toggle between Login and Register */}
          <div className="border-t border-white/10 pt-6 space-y-3">
            <button
              onClick={() => {
                setIsRegister(!isRegister);
                setError('');
                setUsername('');
                setPassword('');
                setConfirmPassword('');
              }}
              className="w-full text-cyan-400 hover:text-cyan-300 text-sm font-medium"
            >
              {isRegister ? t.switchToLogin : t.switchToRegister}
            </button>

            {!isRegister && (
              <>
                <p className="text-center text-slate-400 text-sm mb-3">{t.demoNote}</p>
                <button
                  onClick={() => handleDemoLogin('admin')}
                  disabled={loading}
                  className="w-full bg-purple-600/80 hover:bg-purple-700 text-white py-2 rounded-lg transition-all font-medium"
                >
                  {t.adminDemo}
                </button>
                <button
                  onClick={() => handleDemoLogin('employee')}
                  disabled={loading}
                  className="w-full bg-green-600/80 hover:bg-green-700 text-white py-2 rounded-lg transition-all font-medium"
                >
                  {t.employeeDemo}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
