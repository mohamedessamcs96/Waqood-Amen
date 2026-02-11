import { useState, useEffect, useRef } from 'react';
import { getCarsWithAnalysis, markCarPaid } from '../api';
import { CarTable } from './CarTable';
import { Car } from './types';
import { AlertCircle, Loader } from 'lucide-react';

const API_URL = "http://127.0.0.1:8000";

export function UnpaidCars({ language }: { language: 'ar' | 'en' }) {
  const [unpaidVehicles, setUnpaidVehicles] = useState<Car[]>([]);
  const [loading, setLoading] = useState(true);
  const vehicleToCarMap = useRef<{ [key: string]: number }>({});
  // Track payment status per vehicle ID locally
  const localPaymentStatus = useRef<{ [key: string]: boolean }>({});

  useEffect(() => {
    fetchCars();
  }, []);

  const fetchCars = async () => {
    try {
      const [carsData, vehiclesResponse] = await Promise.all([
        getCarsWithAnalysis(),
        fetch(`${API_URL}/api/detected-vehicles/`).then(r => r.json()).catch(() => ({ results: [] }))
      ]);

      // Handle paginated response
      const vehiclesData = Array.isArray(vehiclesResponse) ? vehiclesResponse : (vehiclesResponse.results || []);

      const carMap: { [key: number]: any } = {};
      carsData.forEach((car: any) => {
        carMap[car.id] = car;
      });

      vehicleToCarMap.current = {};

      const transformedCars: Car[] = vehiclesData.map((vehicle: any) => {
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
          timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          plateText: vehicle.plate_text || car?.plate,
          carColor: vehicle.car_color,
          vehicleConfidence: vehicle.vehicle_confidence,
          plateImage: vehicle.plate_image ? `${API_URL}/plate_crops/${vehicle.plate_image}` : ''
        };
      });

      // Filter only unpaid vehicles
      const unpaidOnly = transformedCars.filter(car => !car.paid);
      setUnpaidVehicles(unpaidOnly);
    } catch (error) {
      console.error('Error fetching cars:', error);
      setUnpaidVehicles([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentToggle = async (id: string, unpaidAmount?: number) => {
    // Mark this specific vehicle as paid locally
    localPaymentStatus.current[id] = true;
    
    // Remove ONLY this vehicle from unpaid list
    setUnpaidVehicles(prevVehicles =>
      prevVehicles.filter(vehicle => vehicle.id !== id)
    );
    
    // Also update backend (but don't refetch to avoid overwriting local state)
    try {
      const carId = vehicleToCarMap.current[id];
      if (carId) {
        await markCarPaid(carId);
      }
    } catch (error) {
      console.error('Error updating payment in backend:', error);
    }
  };

  const translations = {
    ar: {
      title: 'السيارات الغير مدفوعة',
      total: 'إجمالي السيارات الغير مدفوعة',
    },
    en: {
      title: 'Unpaid Cars',
      total: 'Total Unpaid Cars',
    }
  };

  const t = translations[language];

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
      <div className="bg-gradient-to-br from-red-500 via-red-600 to-red-700 rounded-2xl shadow-xl p-8 text-white border border-red-400/30">
        <div className="flex items-center gap-4">
          <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-red-300/50">
            <AlertCircle className="w-12 h-12 text-red-200" />
          </div>
          <div>
            <p className="text-red-100 text-sm uppercase tracking-wide mb-1">{t.total}</p>
            <p className="text-5xl font-bold">{unpaidVehicles.length}</p>
          </div>
        </div>
      </div>

      {unpaidVehicles.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-12 text-center text-slate-500">
          No unpaid vehicles found
        </div>
      ) : (
        <CarTable
          cars={unpaidVehicles}
          language={language}
          onPaymentToggle={handlePaymentToggle}
        />
      )}
    </div>
  );
}
