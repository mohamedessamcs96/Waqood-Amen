import { X } from 'lucide-react';
import { useState } from 'react';
import { updateVehiclePlate } from '../api';

interface PlateEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (newPlate: string) => void;
  language: 'ar' | 'en';
  currentPlate: string;
  vehicleId: string;
}

export function PlateEditModal({
  isOpen,
  onClose,
  onConfirm,
  language,
  currentPlate,
  vehicleId,
}: PlateEditModalProps) {
  const [newPlate, setNewPlate] = useState(currentPlate);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const translations = {
    ar: {
      editPlate: 'تحرير رقم اللوحة',
      currentPlate: 'رقم اللوحة الحالي',
      newPlate: 'رقم اللوحة الجديد',
      cancel: 'إلغاء',
      save: 'حفظ',
      saving: 'جاري الحفظ...',
    },
    en: {
      editPlate: 'Edit License Plate',
      currentPlate: 'Current License Plate',
      newPlate: 'New License Plate',
      cancel: 'Cancel',
      save: 'Save',
      saving: 'Saving...',
    },
  };

  const t = translations[language];

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!newPlate.trim()) {
        setError(language === 'ar' ? 'الرجاء إدخال رقم لوحة' : 'Please enter a license plate');
        return;
      }

      const vehicleIdNum = parseInt(vehicleId, 10);
      await updateVehiclePlate(vehicleIdNum, newPlate.trim());
      onConfirm(newPlate.trim());
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update plate');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl w-96 p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-slate-900">{t.editPlate}</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t.currentPlate}
            </label>
            <div className="w-full px-4 py-3 bg-slate-100 border border-slate-300 rounded-lg text-slate-900">
              {currentPlate}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              {t.newPlate}
            </label>
            <input
              type="text"
              value={newPlate}
              onChange={(e) => setNewPlate(e.target.value)}
              placeholder={currentPlate}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent uppercase"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
              {error}
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-8">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50 font-medium transition"
          >
            {t.cancel}
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 font-medium transition"
          >
            {loading ? t.saving : t.save}
          </button>
        </div>
      </div>
    </div>
  );
}
