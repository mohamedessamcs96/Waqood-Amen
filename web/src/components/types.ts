export interface Car {
  id: string;
  vehicleId?: string; // For updating plate text
  brand: string;
  brandAr: string;
  color: string;
  colorEn: string;
  license: string;
  licenseEn: string;
  image: string;
  driver: string;
  driverEn: string;
  driverImage: string;
  paid: boolean;
  timestamp: string;
  unpaidAmount?: number;
  plateText?: string; // From DetectedVehicle.plate_text
  carColor?: string; // From DetectedVehicle.car_color
  vehicleConfidence?: number; // From DetectedVehicle.vehicle_confidence
  plateImage?: string; // From DetectedVehicle.plate_image
}