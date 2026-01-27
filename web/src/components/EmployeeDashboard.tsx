import { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, TrendingUp, Target, Loader, BarChart3, Users } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getCarsWithAnalysis } from '../api';

const API_URL = "http://127.0.0.1:8000";

export function EmployeeDashboard({ language }: { language: 'ar' | 'en' }) {
  const [carsData, setCarsData] = useState<any[]>([]);
  const [vehiclesData, setVehiclesData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEmployeeData();
  }, []);

  const fetchEmployeeData = async () => {
    try {
      const [cars, vehicles] = await Promise.all([
        getCarsWithAnalysis(),
        fetch(`${API_URL}/detected-vehicles`).then(r => r.json())
      ]);
      setCarsData(cars);
      setVehiclesData(vehicles);
    } catch (error) {
      console.error('Error fetching employee data:', error);
    } finally {
      setLoading(false);
    }
  };
  const translations = {
    ar: {
      title: 'لوحة الموظف',
      myStats: 'إحصائياتي اليوم',
      carsServed: 'السيارات المخدومة',
      paid: 'مدفوع',
      unpaid: 'غير مدفوع',
      avgTime: 'متوسط وقت الخدمة',
      minutes: 'دقيقة',
      performance: 'مستوى الأداء',
      excellent: 'ممتاز',
      good: 'جيد جداً',
      completionRate: 'نسبة الإنجاز',
      hourlyTraffic: 'حركة السيارات بالساعة',
      paymentStatus: 'حالة الدفع',
      weeklyActivity: 'نشاط الأسبوع',
      topBrands: 'أكثر العلامات التجارية',
      cars: 'سيارة',
      employees: 'أداء الموظفين',
      employeeName: 'اسم الموظف',
      carsServedTable: 'السيارات المخدومة',
      rating: 'التقييم'
    },
    en: {
      title: 'Employee Dashboard',
      myStats: 'My Stats Today',
      carsServed: 'Cars Served',
      paid: 'Paid',
      unpaid: 'Unpaid',
      avgTime: 'Avg. Service Time',
      minutes: 'min',
      performance: 'Performance Level',
      excellent: 'Excellent',
      good: 'Very Good',
      completionRate: 'Completion Rate',
      hourlyTraffic: 'Hourly Traffic',
      paymentStatus: 'Payment Status',
      weeklyActivity: 'Weekly Activity',
      topBrands: 'Top Car Brands',
      cars: 'cars',
      employees: 'Employee Performance',
      employeeName: 'Employee Name',
      carsServedTable: 'Cars Served',
      rating: 'Rating'
    }
  };

  const t = translations[language];

  // Calculate real employee stats from API data
  const carsServed = vehiclesData.length;
  const paidCars = carsData.filter((car: any) => car.paid).length;
  const unpaidCars = carsData.filter((car: any) => !car.paid).length;
  const avgServiceTime = 7; // Fixed at 7 minutes
  
  // Calculate performance score based on payment rate
  const performanceScore = carsServed > 0 ? Math.round((paidCars / carsServed) * 100) : 0;
  const completionRate = carsServed > 0 ? ((paidCars / carsServed) * 100).toFixed(1) : '0.0';
  const completionRateNum = parseFloat(completionRate);

  // Payment Status Data for Pie Chart
  const paymentData = [
    { name: t.paid, value: paidCars, color: '#10b981' },
    { name: t.unpaid, value: unpaidCars, color: '#ef4444' }
  ];

  // Hourly data
  const hourlyData = [
    { hour: '08:00', cars: Math.floor(carsServed * 0.1) || 1 },
    { hour: '10:00', cars: Math.floor(carsServed * 0.2) || 2 },
    { hour: '12:00', cars: Math.floor(carsServed * 0.25) || 3 },
    { hour: '14:00', cars: Math.floor(carsServed * 0.18) || 2 },
    { hour: '16:00', cars: Math.floor(carsServed * 0.2) || 2 },
    { hour: '18:00', cars: Math.floor(carsServed * 0.15) || 1 }
  ];

  // Weekly data
  const weeklyData = [
    { day: language === 'ar' ? 'السبت' : 'Sat', cars: Math.floor(carsServed * 1.2) || 5 },
    { day: language === 'ar' ? 'الأحد' : 'Sun', cars: Math.floor(carsServed * 1.3) || 6 },
    { day: language === 'ar' ? 'الاثنين' : 'Mon', cars: Math.floor(carsServed * 1.1) || 4 },
    { day: language === 'ar' ? 'الثلاثاء' : 'Tue', cars: Math.floor(carsServed * 1.4) || 7 },
    { day: language === 'ar' ? 'الأربعاء' : 'Wed', cars: Math.floor(carsServed * 1.5) || 8 },
    { day: language === 'ar' ? 'الخميس' : 'Thu', cars: Math.floor(carsServed * 1.2) || 5 },
    { day: language === 'ar' ? 'الجمعة' : 'Fri', cars: Math.floor(carsServed * 1.0) || 4 }
  ];

  // Top Brands data
  const brandData = [
    { brand: 'Toyota', count: Math.floor(carsServed * 0.25) || 3 },
    { brand: 'BMW', count: Math.floor(carsServed * 0.18) || 2 },
    { brand: 'Mercedes', count: Math.floor(carsServed * 0.15) || 2 },
    { brand: 'Nissan', count: Math.floor(carsServed * 0.12) || 1 },
    { brand: 'Hyundai', count: Math.floor(carsServed * 0.15) || 2 }
  ];

  // Employee performance data
  const employeeData = [
    { name: language === 'ar' ? 'أحمد محمد' : 'Ahmed Mohammed', cars: Math.floor(carsServed * 0.35) || 4, paid: Math.floor(paidCars * 0.35) || 2, rating: 4.8 },
    { name: language === 'ar' ? 'فاطمة علي' : 'Fatima Ali', cars: Math.floor(carsServed * 0.3) || 3, paid: Math.floor(paidCars * 0.32) || 2, rating: 4.9 },
    { name: language === 'ar' ? 'خالد سعيد' : 'Khalid Saeed', cars: Math.floor(carsServed * 0.25) || 3, paid: Math.floor(paidCars * 0.2) || 1, rating: 4.7 },
    { name: language === 'ar' ? 'نورة حسن' : 'Noura Hassan', cars: Math.floor(carsServed * 0.2) || 2, paid: Math.floor(paidCars * 0.15) || 1, rating: 4.6 }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 text-blue-500 animate-spin mr-3" />
        <p className="text-slate-600">Loading employee dashboard...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h2 className="text-3xl text-slate-900">{t.title}</h2>

      {/* Employee Stats */}
      <div className="bg-gradient-to-br from-blue-900 via-slate-800 to-slate-900 rounded-2xl shadow-2xl p-8 text-white border border-cyan-500/30">
        <h3 className="text-2xl mb-8 flex items-center gap-3">
          <Target className="w-8 h-8 text-cyan-400" />
          {t.myStats}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-cyan-500/30 transform hover:scale-105 transition-all">
            <div className="flex items-center justify-center gap-3 mb-3">
              <TrendingUp className="w-10 h-10 text-cyan-400" />
            </div>
            <p className="text-cyan-200 text-sm text-center mb-2">{t.carsServed}</p>
            <p className="text-4xl text-center">{carsServed}</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-green-500/30 transform hover:scale-105 transition-all">
            <div className="flex items-center justify-center gap-3 mb-3">
              <CheckCircle className="w-10 h-10 text-green-400" />
            </div>
            <p className="text-green-200 text-sm text-center mb-2">{t.paid}</p>
            <p className="text-4xl text-center">{paidCars}</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-red-500/30 transform hover:scale-105 transition-all">
            <div className="flex items-center justify-center gap-3 mb-3">
              <XCircle className="w-10 h-10 text-red-400" />
            </div>
            <p className="text-red-200 text-sm text-center mb-2">{t.unpaid}</p>
            <p className="text-4xl text-center">{unpaidCars}</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30 transform hover:scale-105 transition-all">
            <div className="flex items-center justify-center gap-3 mb-3">
              <Clock className="w-10 h-10 text-purple-400" />
            </div>
            <p className="text-purple-200 text-sm text-center mb-2">{t.avgTime}</p>
            <p className="text-4xl text-center">{avgServiceTime}</p>
            <p className="text-purple-200 text-xs text-center mt-1">{t.minutes}</p>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 shadow-2xl transform hover:scale-105 transition-all">
            <p className="text-green-100 text-sm text-center mb-3">{t.completionRate}</p>
            <p className="text-5xl text-center mb-3">{completionRate}%</p>
            <div className="w-full bg-white/30 rounded-full h-3 mb-3">
              <div
                className="bg-white h-3 rounded-full shadow-inner transition-all duration-500"
                style={{ width: `${completionRate}%` }}
              />
            </div>
            <p className="text-green-100 text-sm text-center">✨ {completionRateNum >= 90 ? t.excellent : t.good}</p>
          </div>
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
                <linearGradient id="colorCarsEmployee" x1="0" y1="0" x2="0" y2="1">
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
              <Bar dataKey="cars" fill="url(#colorCarsEmployee)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Weekly Activity */}
        <div className="bg-white rounded-2xl shadow-xl p-6 border border-slate-200">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-6 h-6 text-green-600" />
            <h3 className="text-xl text-slate-900">{t.weeklyActivity}</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={weeklyData}>
              <defs>
                <linearGradient id="colorWeeklyEmployee" x1="0" y1="0" x2="0" y2="1">
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
              <Bar dataKey="cars" fill="url(#colorWeeklyEmployee)" radius={[8, 8, 0, 0]} />
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
                label={(entry) => `${entry.value} (${((entry.value / (carsServed || 1)) * 100).toFixed(1)}%)`}
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
                      style={{ width: `${(brand.count / (Math.max(...brandData.map(b => b.count)) || 1)) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Employee Performance Table */}
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">
        <div className="px-6 py-5 bg-gradient-to-r from-slate-800 to-slate-900 text-white flex items-center gap-3">
          <Users className="w-7 h-7 text-cyan-400" />
          <h3 className="text-xl">{t.employees}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b-2 border-slate-200">
                <th className="px-6 py-4 text-slate-700 text-sm">#</th>
                <th className="px-6 py-4 text-slate-700">{t.employeeName}</th>
                <th className="px-6 py-4 text-slate-700">{t.carsServedTable}</th>
                <th className="px-6 py-4 text-slate-700">{t.paid}</th>
                <th className="px-6 py-4 text-slate-700">{t.completionRate}</th>
                <th className="px-6 py-4 text-slate-700">{t.rating}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {employeeData.map((employee, index) => (
                <tr key={employee.name} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-5 text-center">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 text-white flex items-center justify-center mx-auto shadow-md">
                      {index + 1}
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <span className="text-slate-900">{employee.name}</span>
                  </td>
                  <td className="px-6 py-5 text-center">
                    <span className="bg-blue-100 text-blue-800 px-4 py-1.5 rounded-full text-sm">
                      {employee.cars} {language === 'ar' ? 'سيارة' : 'cars'}
                    </span>
                  </td>
                  <td className="px-6 py-5 text-center">
                    <span className="bg-green-100 text-green-800 px-4 py-1.5 rounded-full text-sm">
                      {employee.paid} {t.paid}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-slate-200 rounded-full h-3">
                        <div
                          className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full shadow-inner"
                          style={{ width: `${employee.cars > 0 ? (employee.paid / employee.cars) * 100 : 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-slate-700 font-mono w-12">
                        {employee.cars > 0 ? ((employee.paid / employee.cars) * 100).toFixed(0) : 0}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-5 text-center">
                    <span className="bg-yellow-100 text-yellow-800 px-3 py-1.5 rounded-full text-sm inline-flex items-center gap-1">
                      ⭐ {employee.rating}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}