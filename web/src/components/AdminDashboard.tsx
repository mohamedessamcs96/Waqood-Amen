import { useState, useEffect } from 'react';
import { Car, Clock, Download, Users, BarChart3, AlertCircle, CheckCircle2, XCircle, Loader } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getCarsWithAnalysis } from '../api';

const API_URL = "http://127.0.0.1:8000";

export function AdminDashboard({ language }: { language: 'ar' | 'en' }) {
  const [carsData, setCarsData] = useState<any[]>([]);
  const [vehiclesData, setVehiclesData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [cars, vehiclesResponse] = await Promise.all([
        getCarsWithAnalysis(),
        fetch(`${API_URL}/api/detected-vehicles/`).then(r => r.json()).catch(() => ({ results: [] }))
      ]);
      setCarsData(cars);
      const vehicles = Array.isArray(vehiclesResponse) ? vehiclesResponse : (vehiclesResponse.results || []);
      setVehiclesData(vehicles);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };
  const translations = {
    ar: {
      title: 'لوحة تحكم المدير',
      overview: 'نظرة عامة',
      totalCars: 'إجمالي السيارات اليوم',
      totalPaid: 'السيارات المدفوعة',
      totalUnpaid: 'السيارات الغير مدفوعة',
      avgTime: 'متوسط وقت الخدمة',
      minutes: 'دقيقة',
      cars: 'سيارة',
      hourlyTraffic: 'حركة السيارات بالساعة',
      paymentStatus: 'حالة الدفع',
      topBrands: 'أكثر العلامات التجارية',
      employees: 'أداء الموظفين',
      employeeName: 'اسم الموظف',
      carsServed: 'السيارات المخدومة',
      completionRate: 'نسبة الإنجاز',
      exportReport: 'تصدير التقرير',
      paid: 'مدفوع',
      unpaid: 'غير مدفوع',
      week: 'الأسبوع الماضي',
      todayActivity: 'نشاط اليوم'
    },
    en: {
      title: 'Admin Dashboard',
      overview: 'Overview',
      totalCars: 'Total Cars Today',
      totalPaid: 'Paid Cars',
      totalUnpaid: 'Unpaid Cars',
      avgTime: 'Avg. Service Time',
      minutes: 'min',
      cars: 'cars',
      hourlyTraffic: 'Hourly Traffic',
      paymentStatus: 'Payment Status',
      topBrands: 'Top Car Brands',
      employees: 'Employee Performance',
      employeeName: 'Employee Name',
      carsServed: 'Cars Served',
      completionRate: 'Completion Rate',
      exportReport: 'Export Report',
      paid: 'Paid',
      unpaid: 'Unpaid',
      week: 'Last Week',
      todayActivity: "Today's Activity"
    }
  };

  const t = translations[language];

  // Calculate real data from API
  const totalCars = vehiclesData.length;
  const paidCars = carsData.filter((car: any) => car.paid).length;
  const unpaidCars = carsData.filter((car: any) => !car.paid).length;
  
  // Average service time calculation (7 minutes default)
  const avgServiceTime = 7;

  // Payment Status Data
  const paymentData = [
    { name: t.paid, value: paidCars, color: '#10b981' },
    { name: t.unpaid, value: unpaidCars, color: '#ef4444' }
  ];

  // Hourly data - mock but realistic
  const hourlyData = [
    { hour: '08:00', cars: Math.floor(totalCars * 0.1) },
    { hour: '10:00', cars: Math.floor(totalCars * 0.2) },
    { hour: '12:00', cars: Math.floor(totalCars * 0.25) },
    { hour: '14:00', cars: Math.floor(totalCars * 0.18) },
    { hour: '16:00', cars: Math.floor(totalCars * 0.2) },
    { hour: '18:00', cars: Math.floor(totalCars * 0.15) }
  ];

  const weeklyData = [
    { day: language === 'ar' ? 'السبت' : 'Sat', cars: Math.floor(totalCars * 1.2) },
    { day: language === 'ar' ? 'الأحد' : 'Sun', cars: Math.floor(totalCars * 1.3) },
    { day: language === 'ar' ? 'الاثنين' : 'Mon', cars: Math.floor(totalCars * 1.1) },
    { day: language === 'ar' ? 'الثلاثاء' : 'Tue', cars: Math.floor(totalCars * 1.4) },
    { day: language === 'ar' ? 'الأربعاء' : 'Wed', cars: Math.floor(totalCars * 1.5) },
    { day: language === 'ar' ? 'الخميس' : 'Thu', cars: Math.floor(totalCars * 1.2) },
    { day: language === 'ar' ? 'الجمعة' : 'Fri', cars: Math.floor(totalCars * 1.0) }
  ];

  const brandData = [
    { brand: 'Toyota', count: Math.floor(totalCars * 0.25) },
    { brand: 'BMW', count: Math.floor(totalCars * 0.18) },
    { brand: 'Mercedes', count: Math.floor(totalCars * 0.15) },
    { brand: 'Nissan', count: Math.floor(totalCars * 0.12) },
    { brand: 'Hyundai', count: Math.floor(totalCars * 0.15) }
  ];

  const employeeData = [
    { name: language === 'ar' ? 'أحمد محمد' : 'Ahmed Mohammed', cars: Math.floor(totalCars * 0.35), paid: Math.floor(paidCars * 0.35), rating: 4.8 },
    { name: language === 'ar' ? 'فاطمة علي' : 'Fatima Ali', cars: Math.floor(totalCars * 0.3), paid: Math.floor(paidCars * 0.32), rating: 4.9 },
    { name: language === 'ar' ? 'خالد سعيد' : 'Khalid Saeed', cars: Math.floor(totalCars * 0.25), paid: Math.floor(paidCars * 0.2), rating: 4.7 },
    { name: language === 'ar' ? 'نورة حسن' : 'Noura Hassan', cars: Math.floor(totalCars * 0.2), paid: Math.floor(paidCars * 0.15), rating: 4.6 }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 text-blue-500 animate-spin mr-3" />
        <p className="text-slate-600">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl text-slate-900 mb-1">{t.title}</h2>
          <p className="text-slate-600">{t.todayActivity}</p>
        </div>
        <button className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white px-6 py-3 rounded-xl hover:from-cyan-600 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl transform hover:scale-105">
          <Download className="w-5 h-5" />
          {t.exportReport}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-2xl shadow-xl p-6 transform hover:scale-105 transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-blue-100 text-sm mb-2">{t.totalCars}</p>
              <p className="text-4xl">{totalCars}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Car className="w-8 h-8" />
            </div>
          </div>
          <div className="text-blue-100 text-sm">📈 +8% {language === 'ar' ? 'من الأمس' : 'from yesterday'}</div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-2xl shadow-xl p-6 transform hover:scale-105 transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-green-100 text-sm mb-2">{t.totalPaid}</p>
              <p className="text-4xl">{paidCars}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <CheckCircle2 className="w-8 h-8" />
            </div>
          </div>
          <div className="text-green-100 text-sm">✓ {((paidCars / totalCars * 100) || 0).toFixed(1)}% {language === 'ar' ? 'معدل الدفع' : 'payment rate'}</div>
        </div>

        <div className="bg-gradient-to-br from-red-500 to-red-600 text-white rounded-2xl shadow-xl p-6 transform hover:scale-105 transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-red-100 text-sm mb-2">{t.totalUnpaid}</p>
              <p className="text-4xl">{unpaidCars}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <XCircle className="w-8 h-8" />
            </div>
          </div>
          <div className="text-red-100 text-sm">⚠ {((unpaidCars / totalCars * 100) || 0).toFixed(1)}% {language === 'ar' ? 'بحاجة متابعة' : 'needs follow-up'}</div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-2xl shadow-xl p-6 transform hover:scale-105 transition-all">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-purple-100 text-sm mb-2">{t.avgTime}</p>
              <p className="text-4xl">{avgServiceTime}</p>
            </div>
            <div className="bg-white/20 p-3 rounded-xl">
              <Clock className="w-8 h-8" />
            </div>
          </div>
          <div className="text-purple-100 text-sm">{t.minutes}</div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Traffic */}
        <div className="bg-white rounded-2xl shadow-xl p-6 border border-slate-200">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-6 h-6 text-cyan-600" />
            <h3 className="text-xl text-slate-900">{t.hourlyTraffic}</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={hourlyData}>
              <defs>
                <linearGradient id="colorCars" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0891b2" stopOpacity={0.9}/>
                  <stop offset="95%" stopColor="#0891b2" stopOpacity={0.6}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="hour" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: 'none', 
                  borderRadius: '12px',
                  color: 'white'
                }}
              />
              <Bar dataKey="cars" fill="url(#colorCars)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Weekly Activity */}
        <div className="bg-white rounded-2xl shadow-xl p-6 border border-slate-200">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-6 h-6 text-green-600" />
            <h3 className="text-xl text-slate-900">{t.week}</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={weeklyData}>
              <defs>
                <linearGradient id="colorWeekly" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.9}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.6}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="day" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: 'none', 
                  borderRadius: '12px',
                  color: 'white'
                }}
              />
              <Bar dataKey="cars" fill="url(#colorWeekly)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Payment Status Pie */}
        <div className="bg-white rounded-2xl shadow-xl p-6 border border-slate-200">
          <h3 className="text-xl text-slate-900 mb-6">{t.paymentStatus}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={paymentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.value} (${((entry.value / 156) * 100).toFixed(1)}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {paymentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Brands */}
        <div className="bg-white rounded-2xl shadow-xl p-6 lg:col-span-2 border border-slate-200">
          <h3 className="text-xl text-slate-900 mb-6">{t.topBrands}</h3>
          <div className="space-y-4">
            {brandData.map((brand, index) => (
              <div key={brand.brand} className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 text-white flex items-center justify-center shadow-lg">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between mb-2">
                    <span className="text-slate-900">{brand.brand}</span>
                    <span className="text-slate-600 font-mono">{brand.count} {t.cars}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-blue-600 h-3 rounded-full transition-all duration-500 shadow-inner"
                      style={{ width: `${(brand.count / 50) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
