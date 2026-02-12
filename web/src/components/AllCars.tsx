import { useState, useEffect, useRef } from 'react';
import { getCarsWithAnalysis, markCarPaid, markCarUnpaid } from '../api';
import { CarTable } from './CarTable';
import { Car } from './types';
import { XCircle, Loader, RefreshCw } from 'lucide-react';

const API_URL = "http://127.0.0.1:8000";

export function AllCars({ language }: { language: 'ar' | 'en' }) {
  const [allVehicles, setAllVehicles] = useState<Car[]>([]);
  const [loading, setLoading] = useState(true);
  const vehicleToCarMap = useRef<{ [key: string]: number }>({});
  const localPaymentStatus = useRef<{ [key: string]: boolean }>({});

  useEffect(() => {
    fetchCars();
    // Auto-refresh every 15 seconds to catch background analysis results
    const interval = setInterval(fetchCars, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchCars = async () => {
    try {
      const [carsData, vehiclesResponse] = await Promise.all([
        getCarsWithAnalysis(),
        fetch(`${API_URL}/api/detected-vehicles/`).then(r => r.json()).catch(() => ({ results: [] }))
      ]);

      // Handle paginated response: API returns {count, results} not a plain array
      const vehiclesData = Array.isArray(vehiclesResponse) ? vehiclesResponse : (vehiclesResponse.results || []);

      const carMap: { [key: number]: any } = {};
      carsData.forEach((car: any) => {
        carMap[car.id] = car;
      });

      vehicleToCarMap.current = {};

      // Only include vehicles that have a detected plate text
      const vehiclesWithPlates = vehiclesData.filter((vehicle: any) => {
        const plateText = vehicle.plate_text?.trim();
        return plateText && plateText !== '' && plateText !== 'N/A' && !plateText.startsWith('UNKNOWN');
      });

      const transformedCars: Car[] = vehiclesWithPlates.map((vehicle: any) => {
        const car = carMap[vehicle.video_id];
        const vehicleId = String(vehicle.id);
        vehicleToCarMap.current[vehicleId] = vehicle.video_id;
        
        // Use local payment status if set, otherwise use API value
        const isPaid = localPaymentStatus.current[vehicleId] !== undefined 
          ? localPaymentStatus.current[vehicleId] 
          : (car ? Boolean(car.paid) : false);
        
        return {
          id: vehicleId,
          vehicleId: vehicleId,
          brand: vehicle.plate_text || car?.plate || 'Unknown',
          brandAr: vehicle.plate_text || car?.plate || 'غير معروف',
          color: vehicle.car_color || 'N/A',
          colorEn: vehicle.car_color || 'Unknown',
          license: vehicle.plate_text || car?.plate || 'N/A',
          licenseEn: vehicle.plate_text || car?.plate || 'N/A',
          image: vehicle.crop_image ? `${API_URL}/car_crops/${vehicle.crop_image}` : '',
          driver: 'Driver',
          driverEn: 'Driver',
          driverImage: vehicle.driver_face_image ? `${API_URL}/face_crops/${vehicle.driver_face_image}` : '',
          paid: isPaid,
          timestamp: vehicle.created_at 
            ? new Date(vehicle.created_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          plateText: vehicle.plate_text || car?.plate,
          carColor: vehicle.car_color,
          vehicleConfidence: vehicle.vehicle_confidence,
          plateImage: vehicle.plate_image ? `${API_URL}/plate_crops/${vehicle.plate_image}` : '',
          _createdAt: vehicle.created_at || ''
        };
      });

      // Sort by date (newest first)
      transformedCars.sort((a: any, b: any) => {
        const dateA = a._createdAt ? new Date(a._createdAt).getTime() : 0;
        const dateB = b._createdAt ? new Date(b._createdAt).getTime() : 0;
        return dateB - dateA;
      });

      setAllVehicles(transformedCars);
    } catch (error) {
      console.error('Error fetching cars:', error);
      setAllVehicles([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentToggle = async (id: string, unpaidAmount?: number) => {
    const currentStatus = allVehicles.find(v => v.id === id)?.paid || false;
    const newStatus = !currentStatus;
    
    localPaymentStatus.current[id] = newStatus;
    
    setAllVehicles(prevVehicles =>
      prevVehicles.map(vehicle =>
        vehicle.id === id ? { ...vehicle, paid: newStatus } : vehicle
      )
    );
    
    try {
      const carId = vehicleToCarMap.current[id];
      if (carId) {
        if (newStatus) {
          await markCarPaid(carId);
        } else {
          await markCarUnpaid(carId);
        }
      }
    } catch (error) {
      console.error('Error updating payment in backend:', error);
    }
  };

  const translations = {
    ar: {
      title: 'جميع السيارات',
      total: 'إجمالي السيارات',
    },
    en: {
      title: 'All Cars',
      total: 'Total Cars',
    }
  };

  const t = translations[language];
  const vehiclesToDisplay = allVehicles;
  const unpaidCount = allVehicles.filter(v => !v.paid).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-8 h-8 text-blue-500 animate-spin mr-3" />
        <p className="text-slate-600">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Unpaid Alert Banner */}
      {unpaidCount > 0 && (
        <div className="bg-red-50 border-2 border-red-400 rounded-2xl p-4 flex items-center gap-3 animate-pulse shadow-lg">
          <div className="bg-red-500 text-white rounded-full p-2">
            <XCircle className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <p className="text-red-800 font-bold text-lg">
              {language === 'ar' 
                ? `⚠️ تنبيه: ${unpaidCount} سيارة غير مدفوعة!` 
                : `⚠️ Alert: ${unpaidCount} unpaid vehicle(s)!`}
            </p>
            <p className="text-red-600 text-sm">
              {language === 'ar' 
                ? 'السيارات الغير مدفوعة مميزة باللون الأحمر' 
                : 'Unpaid vehicles are highlighted in red'}
            </p>
          </div>
        </div>
      )}

      <div className="bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 text-white border border-blue-400/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-blue-300/50">
              <XCircle className="w-12 h-12 text-blue-200" />
            </div>
            <div>
              <p className="text-blue-100 text-sm uppercase tracking-wide mb-1">{t.total}</p>
              <p className="text-5xl font-bold">{vehiclesToDisplay.length}</p>
            </div>
          </div>
          <button
            onClick={() => { setLoading(true); fetchCars(); }}
            className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-5 h-5" />
            {language === 'ar' ? 'تحديث' : 'Refresh'}
          </button>
        </div>
      </div>

      {vehiclesToDisplay.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-12 text-center text-slate-500">
          No vehicles found
        </div>
      ) : (
        <CarTable
          cars={vehiclesToDisplay}
          language={language}
          onPaymentToggle={handlePaymentToggle}
        />
      )}
    </div>
  );
}
