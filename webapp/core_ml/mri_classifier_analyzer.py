"""
Bridges the Django app to ml/inference/mri_gradcam_inference.py.

Follows the same pattern as inference_service.py's brain-CT fallback: if no
trained checkpoint exists, this returns a clear, honest "not yet trained"
result instead of crashing OR silently returning a fabricated finding.
"""
import os
from django.conf import settings

CHECKPOINT_REL_PATH = 'checkpoints_mri_classifier/best_mri_classifier.pth'


class MRIClassifierAnalyzer:
    def __init__(self):
        self._engine = None
        self._checkpoint_path = os.path.join(settings.BASE_DIR, CHECKPOINT_REL_PATH)

    def _get_engine(self):
        if self._engine is None:
            from ml.inference.mri_gradcam_inference import MRIGradCAMInference
            self._engine = MRIGradCAMInference(self._checkpoint_path)
        return self._engine

    def process_image(self, file_path: str, output_dir: str) -> dict:
        if not os.path.exists(self._checkpoint_path):
            # Honest fallback — no fabricated finding. See ml/README.md for
            # how to actually train and install a checkpoint here.
            return {
                'confidence': '0%',
                'detected': False,
                'findings_text': (
                    "No trained MRI disease classifier checkpoint is installed yet. "
                    "This upload was accepted and identified as an MRI, but no "
                    "classification was performed — training requires a real, "
                    "licensed brain MRI dataset which is not bundled in this deployment. "
                    "See ml/README.md for how to train one."
                ),
                'model_not_trained': True,
            }

        try:
            engine = self._get_engine()
            result = engine.predict(file_path, output_dir=output_dir)
        except Exception as e:
            return {
                'confidence': '0%',
                'detected': False,
                'findings_text': f'MRI classification failed to run: {e}',
                'model_not_trained': False,
                'error': True,
            }

        class_names = {
            'no_tumor': 'no tumor pattern',
            'glioma': 'glioma',
            'meningioma': 'meningioma',
            'pituitary': 'pituitary tumor',
            'atrophy': 'brain atrophy',
            'wmi': 'white matter intensity changes',
            'ischemia': 'ischemia',
        }
        label = class_names.get(result['predicted_class'], result['predicted_class'])
        findings_text = (
            f"Classifier finding: pattern most consistent with {label} "
            f"(confidence {result['confidence']}). Approximate attended region: "
            f"{result['approximate_region']} (Grad-CAM heatmap location, not a "
            f"calibrated anatomical coordinate)."
        )

        return {
            'confidence': result['confidence'],
            'detected': result['detected'],
            'findings_text': findings_text,
            'overlay_path': result.get('overlay_path'),
            'all_class_probs': result.get('all_class_probs'),
            'model_not_trained': False,
        }


_analyzer = None

def get_mri_classifier_analyzer() -> MRIClassifierAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = MRIClassifierAnalyzer()
    return _analyzer
