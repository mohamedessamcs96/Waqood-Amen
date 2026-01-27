import { Check, X, Clock, DollarSign, Edit2 } from 'lucide-react';
import { Car } from './types';
import { useState } from 'react';
import { PaymentModal } from './PaymentModal';
import { PlateEditModal } from './PlateEditModal';

interface CarTableProps {
  cars: Car[];
  language: 'ar' | 'en';
  onPaymentToggle: (id: string, unpaidAmount?: number) => void;
  onPlateUpdated?: () => void;
}

export function CarTable({ cars, language, onPaymentToggle, onPlateUpdated }: CarTableProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCar, setSelectedCar] = useState<Car | null>(null);
  const [plateModalOpen, setPlateModalOpen] = useState(false);
  const [selectedCarForPlate, setSelectedCarForPlate] = useState<Car | null>(null);

  const translations = {
    ar: {
      carImage: 'صورة السيارة',
      driverPhoto: 'صورة السائق',
      brand: 'العلامة التجارية',
      color: 'اللون',
      license: 'رقم اللوحة',
      time: 'الوقت',
      status: 'الحالة',
      amount: 'المبلغ',
      action: 'الإجراء',
      paid: 'مدفوع',
      notPaid: 'غير مدفوع',
      markPaid: 'تعيين كمدفوع',
      markUnpaid: 'تسجيل غير مدفوع',
      sar: 'ريال'
    },
    en: {
      carImage: 'Car Image',
      driverPhoto: 'Driver Photo',
      brand: 'Brand',
      color: 'Color',
      license: 'License Plate',
      time: 'Time',
      status: 'Status',
      amount: 'Amount',
      action: 'Action',
      paid: 'Paid',
      notPaid: 'Not Paid',
      markPaid: 'Mark as Paid',
      markUnpaid: 'Mark Unpaid',
      sar: 'SAR'
    }
  };

  const t = translations[language];

  const handleUnpaidClick = (car: Car) => {
    setModalOpen(false);
    setSelectedCar(null);
    // Use setTimeout to ensure clean state reset
    setTimeout(() => {
      setSelectedCar(car);
      setModalOpen(true);
    }, 0);
  };

  const handleConfirmUnpaid = (amount: number) => {
    if (selectedCar) {
      const carId = selectedCar.id;
      // Close and reset immediately
      setModalOpen(false);
      setSelectedCar(null);
      // Then trigger payment
      onPaymentToggle(carId, amount);
    }
  };

  const handlePlateEditClick = (car: Car) => {
    setSelectedCarForPlate(car);
    setPlateModalOpen(true);
  };

  const handlePlateConfirm = (newPlate: string) => {
    // The plate is updated in the backend by PlateEditModal
    // Trigger parent refetch to sync updated data
    onPlateUpdated?.();
  };

  return (
    <>
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200 w-full">
        <div className="overflow-x-auto w-full">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-blue-900 via-slate-800 to-slate-900 text-white sticky top-0">
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[120px]">صورة السيارة / Car Image</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[80px]">{t.driverPhoto}</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[100px]">صورة اللوحة / Plate Image</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[120px]">رقم اللوحة / Plate Number</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[100px]">درجة الثقة / Confidence Score</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[80px]">{t.color}</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[100px]">{t.time}</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[120px]">{t.status}</th>
                <th className="px-3 py-3 text-xs uppercase tracking-wider whitespace-nowrap min-w-[140px]">{t.action}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {cars.map((car) => (
                <tr 
                  key={car.id} 
                  className={`hover:bg-slate-50 transition-colors text-sm ${
                    car.paid ? 'bg-green-50/30' : 'bg-red-50/30'
                  }`}
                >
                  {/* Car Image */}
                  <td className="px-3 py-3">
                    <div className="w-24 h-16 rounded-lg overflow-hidden shadow-md bg-gradient-to-br from-slate-300 to-slate-400 ring-1 ring-slate-300 flex items-center justify-center flex-shrink-0">
                      {car.image ? (
                        <img
                          src={car.image}
                          alt={language === 'ar' ? car.brandAr : car.brand}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const div = document.createElement('div');
                            div.className = 'w-full h-full bg-gradient-to-br from-slate-400 to-slate-500 flex items-center justify-center text-white text-xs text-center';
                            div.textContent = 'No Image';
                            (e.target as HTMLImageElement).parentElement?.replaceChild(div, e.target as HTMLImageElement);
                          }}
                        />
                      ) : (
                        <span className="text-slate-500 text-xs font-semibold">No Image</span>
                      )}
                    </div>
                  </td>

                  {/* Driver Photo */}
                  <td className="px-3 py-3">
                    <div className="w-12 h-12 rounded-full overflow-hidden shadow-md bg-gradient-to-br from-slate-300 to-slate-400 mx-auto ring-2 ring-cyan-400/50 flex items-center justify-center flex-shrink-0">
                      {car.driverImage ? (
                        <img
                          src={car.driverImage}
                          alt="Driver"
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const div = document.createElement('div');
                            div.className = 'w-full h-full bg-gradient-to-br from-slate-400 to-slate-500 flex items-center justify-center text-white text-xs';
                            div.textContent = 'N/A';
                            (e.target as HTMLImageElement).parentElement?.replaceChild(div, e.target as HTMLImageElement);
                          }}
                        />
                      ) : (
                        <span className="text-slate-500 text-xs font-semibold">N/A</span>
                      )}
                    </div>
                  </td>

                  {/* Plate Image */}
                  <td className="px-3 py-3">
                    <div className="w-20 h-10 rounded-lg overflow-hidden shadow-md bg-gradient-to-br from-slate-300 to-slate-400 ring-1 ring-slate-300 flex items-center justify-center flex-shrink-0">
                      {car.plateImage ? (
                        <img
                          src={car.plateImage}
                          alt="Plate"
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const div = document.createElement('div');
                            div.className = 'w-full h-full bg-gradient-to-br from-slate-400 to-slate-500 flex items-center justify-center text-white text-xs';
                            div.textContent = 'No Plate';
                            (e.target as HTMLImageElement).parentElement?.replaceChild(div, e.target as HTMLImageElement);
                          }}
                        />
                      ) : (
                        <span className="text-slate-500 text-xs font-semibold">No Plate</span>
                      )}
                    </div>
                  </td>

                  {/* Plate Number */}
                  <td className="px-3 py-3">
                    <button
                      onClick={() => handlePlateEditClick(car)}
                      className="text-slate-900 tracking-wider font-semibold bg-yellow-100 hover:bg-blue-100 px-3 py-1.5 rounded-lg inline-flex items-center gap-1 transition-colors text-xs border border-yellow-300 whitespace-nowrap"
                    >
                      {car.plateText || car.licenseEn || 'N/A'}
                      <Edit2 className="w-3 h-3 text-blue-600" />
                    </button>
                  </td>

                  {/* Confidence Score */}
                  <td className="px-3 py-3">
                    <div className="text-center">
                      <span className="text-sm font-bold text-blue-600 block">
                        {car.vehicleConfidence ? (car.vehicleConfidence * 100).toFixed(1) : '0'}%
                      </span>
                      <div className="text-xs text-slate-500">Conf</div>
                    </div>
                  </td>

                  {/* Color */}
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2 justify-center">
                      {car.carColor ? (
                        <div
                          className="w-4 h-4 rounded-full shadow-sm ring-1 ring-slate-300"
                          style={{
                            backgroundColor: car.carColor.toLowerCase().includes('red') ? '#dc2626' :
                                           car.carColor.toLowerCase().includes('blue') ? '#2563eb' :
                                           car.carColor.toLowerCase().includes('black') ? '#1f2937' :
                                           car.carColor.toLowerCase().includes('white') ? '#f5f5f5' :
                                           car.carColor.toLowerCase().includes('gray') ? '#9ca3af' :
                                           car.carColor.toLowerCase().includes('silver') ? '#d1d5db' :
                                           car.carColor.toLowerCase().includes('gold') ? '#f59e0b' :
                                           car.carColor.toLowerCase().includes('yellow') ? '#eab308' :
                                           car.carColor.toLowerCase().includes('green') ? '#22c55e' :
                                           '#94a3b8'
                          }}
                          title={car.carColor}
                        />
                      ) : (
                        <div className="w-4 h-4 rounded-full bg-slate-300 shadow-sm ring-1 ring-slate-300" />
                      )}
                      <span className="text-slate-700 text-xs truncate">
                        {car.carColor || 'N/A'}
                      </span>
                    </div>
                  </td>

                  {/* Time */}
                  <td className="px-3 py-3">
                    <div className="flex items-center justify-center gap-1 text-slate-700 text-xs">
                      <Clock className="w-3 h-3 text-purple-600 flex-shrink-0" />
                      <span className="truncate">{car.timestamp}</span>
                    </div>
                  </td>

                  {/* Status (Combined Status + Amount) */}
                  <td className="px-3 py-3">
                    <div className="flex justify-center items-center">
                      {car.paid ? (
                        <span className="px-3 py-1.5 rounded-full text-white text-xs flex items-center gap-1 shadow-md bg-gradient-to-r from-green-500 to-green-600 font-semibold whitespace-nowrap">
                          <Check className="w-4 h-4" />
                          {t.paid}
                        </span>
                      ) : (
                        <span className="px-3 py-1.5 rounded-full text-white text-xs flex items-center gap-1 shadow-md bg-gradient-to-r from-red-500 to-red-600 font-semibold whitespace-nowrap">
                          {t.notPaid}
                          {car.unpaidAmount && (
                            <>
                              <span>-</span>
                              <DollarSign className="w-3 h-3" />
                              {car.unpaidAmount}
                            </>
                          )}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Action */}
                  <td className="px-3 py-3">
                    {car.paid ? (
                      <button
                        onClick={() => handleUnpaidClick(car)}
                        className="px-3 py-1.5 rounded-lg transition-all text-xs bg-slate-100 text-slate-700 hover:bg-slate-200 shadow-md hover:shadow-lg whitespace-nowrap"
                      >
                        {t.markUnpaid}
                      </button>
                    ) : (
                      <div className="flex gap-1 justify-center flex-wrap">
                        <button
                          onClick={() => onPaymentToggle(car.id)}
                          className="px-3 py-1.5 rounded-lg transition-all text-xs bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700 shadow-md hover:shadow-lg whitespace-nowrap"
                        >
                          {t.markPaid}
                        </button>
                        {!car.unpaidAmount && (
                          <button
                            onClick={() => handleUnpaidClick(car)}
                            className="px-3 py-1.5 rounded-lg transition-all text-xs bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg whitespace-nowrap"
                          >
                            {t.amount}
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <PaymentModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirmUnpaid}
        language={language}
        carBrand={language === 'ar' ? selectedCar?.brandAr || '' : selectedCar?.brand || ''}
        carLicense={language === 'ar' ? selectedCar?.license || '' : selectedCar?.licenseEn || ''}
      />

      <PlateEditModal
        isOpen={plateModalOpen}
        onClose={() => setPlateModalOpen(false)}
        onConfirm={handlePlateConfirm}
        language={language}
        currentPlate={language === 'ar' ? selectedCarForPlate?.license || '' : selectedCarForPlate?.licenseEn || ''}
        vehicleId={selectedCarForPlate?.vehicleId || ''}
      />
    </>
  );
}