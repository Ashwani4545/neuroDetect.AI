export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface AnalysisSummary {
  id: string;
  created_at: string;
  original_filename: string;
  status: AnalysisStatus;
  detected: boolean | null;
  confidence: string | null;
}

export interface RegionMeasurement {
  region_id: number;
  area_px: number;
  bounding_box: { x: number; y: number; width: number; height: number };
  centroid: { x: number; y: number };
}

export interface Measurements {
  available: boolean;
  reason?: string;
  image_dimensions?: { width: number; height: number };
  total_foreground_pixels?: number;
  foreground_percentage?: number;
  region_count?: number;
  regions?: RegionMeasurement[];
  region_size_distribution?: {
    min_px: number | null;
    max_px: number | null;
    mean_px: number | null;
    median_px: number | null;
  };
  pixel_spacing_available?: boolean;
  physical_units_note?: string;
}

export interface AnalysisDetail extends AnalysisSummary {
  model_used: string | null;
  error_message: string | null;
  processing_time_ms: number | null;
  measurements: Measurements | null;
  mask_available: boolean;
  overlay_available: boolean;
}

export interface AnalysisHistoryResponse {
  total: number;
  page: number;
  page_size: number;
  results: AnalysisSummary[];
}

export interface ModelStatus {
  checkpoint_loaded: boolean;
  architecture: string;
  fallback_pipeline: string;
  message: string;
}

export interface HealthStatus {
  status: string;
  database: string;
}

export interface ApiError {
  detail: string;
}
