import { X } from 'lucide-react';
import { useState } from 'react';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (amount: number) => void;
  language: 'ar' | 'en';
  carBrand: string;
  carLicense: string;
}

export function PaymentModal({ isOpen, onClose, onConfirm, language, carBrand, carLicense }: PaymentModalProps) {
  const [amount, setAmount] = useState('');

  const translations = {
    ar: {
      title: 'تسجيل مبلغ غير مدفوع',
      carInfo: 'معلومات السيارة',
      brand: 'العلامة التجارية',
      license: 'رقم اللوحة',
      amount: 'المبلغ الغير مدفوع',
      sar: 'ريال سعودي',
      enterAmount: 'أدخل المبلغ',
      confirm: 'تأكيد',
      cancel: 'إلغاء',
      required: 'الرجاء إدخال المبلغ'
    },
    en: {
      title: 'Record Unpaid Amount',
      carInfo: 'Car Information',
      brand: 'Brand',
      license: 'License',
      amount: 'Unpaid Amount',
      sar: 'SAR',
      enterAmount: 'Enter amount',
      confirm: 'Confirm',
      cancel: 'Cancel',
      required: 'Please enter amount'
    }
  };

  const t = translations[language];

  if (!isOpen) return null;

  const handleConfirm = () => {
    const numAmount = parseFloat(amount);
    if (numAmount && numAmount > 0) {
      onConfirm(numAmount);
      setAmount('');
      onClose();
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div 
        className={`bg-white rounded-2xl shadow-2xl max-w-md w-full transform transition-all ${language === 'ar' ? 'rtl' : 'ltr'}`} 
        dir={language === 'ar' ? 'rtl' : 'ltr'}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-5 rounded-t-2xl flex justify-between items-center">
          <h3 className="text-xl">{t.title}</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Car Info */}
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
            <p className="text-sm text-slate-600 mb-3">{t.carInfo}</p>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-700">{t.brand}:</span>
                <span className="text-slate-900">{carBrand}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-700">{t.license}:</span>
                <span className="text-slate-900 tracking-wider">{carLicense}</span>
              </div>
            </div>
          </div>

          {/* Amount Input */}
          <div>
            <label className="block text-slate-700 mb-2">{t.amount}</label>
            <div className="relative">
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={t.enterAmount}
                className="w-full px-4 py-4 border-2 border-slate-300 rounded-xl focus:outline-none focus:border-red-500 focus:ring-4 focus:ring-red-500/20 text-lg transition-all"
                autoFocus
                min="0"
                step="0.01"
              />
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none">
                {t.sar}
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-6 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-all"
          >
            {t.cancel}
          </button>
          <button
            onClick={handleConfirm}
            disabled={!amount || parseFloat(amount) <= 0}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg disabled:shadow-none"
          >
            {t.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}
