import { useState, useEffect, useRef } from 'react';
import { getCarsWithAnalysis, markCarPaid } from '../api';
import { CarTable } from './CarTable';
import { Car } from './types';
import { XCircle, Loader } from 'lucide-react';

const API_URL = "http://127.0.0.1:8000";

export function AllCars({ language }: { language: 'ar' | 'en' }) {
  const [allVehicles, setAllVehicles] = useState<Car[]>([]);
  const [loading, setLoading] = useState(true);
  const vehicleToCarMap = useRef<{ [key: string]: number }>({});
  // Track payment status per vehicle ID locally
  const localPaymentStatus = useRef<{ [key: string]: boolean }>({});

  useEffect(() => {
    fetchCars();
  }, []);

  const fetchCars = async () => {
    try {
      const [carsData, vehiclesData] = await Promise.all([
        getCarsWithAnalysis(),
        fetch(`${API_URL}/detected-vehicles`).then(r => r.json())
      ]);

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
      setAllVehicles(transformedCars);
    } catch (error) {
      console.error('Error fetching cars:', error);
      setAllVehicles([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentToggle = async (id: string, unpaidAmount?: number) => {
    // Update local state ONLY for this specific vehicle
    const currentStatus = allVehicles.find(v => v.id === id)?.paid || false;
    const newStatus = !currentStatus;
    
    // Store the new status locally
    localPaymentStatus.current[id] = newStatus;
    
    // Update UI immediately for ONLY this vehicle
    setAllVehicles(prevVehicles =>
      prevVehicles.map(vehicle =>
        vehicle.id === id ? { ...vehicle, paid: newStatus } : vehicle
      )
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
      <div className="bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 rounded-2xl shadow-xl p-8 text-white border border-blue-400/30">
        <div className="flex items-center gap-4">
          <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 border border-blue-300/50">
            <XCircle className="w-12 h-12 text-blue-200" />
          </div>
          <div>
            <p className="text-blue-100 text-sm uppercase tracking-wide mb-1">{t.total}</p>
            <p className="text-5xl font-bold">{vehiclesToDisplay.length}</p>
          </div>
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
