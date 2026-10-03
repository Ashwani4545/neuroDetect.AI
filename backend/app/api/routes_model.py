from fastapi import APIRouter

from app.schemas import ModelStatus

router = APIRouter()


@router.get('/model/status', response_model=ModelStatus)
def model_status():
    from ml.inference.ct_pipeline import get_inference_service
    service = get_inference_service()
    checkpoint_loaded = getattr(service, 'model', None) is not None

    return ModelStatus(
        checkpoint_loaded=checkpoint_loaded,
        architecture='2.5D U-Net (ml/models/model.py)',
        fallback_pipeline='HU-windowing (WL=35/WW=100, HU 15-35 hypodense band) + adaptive median/MAD thresholding',
        message=(
            'A trained checkpoint is loaded and being used for inference.'
            if checkpoint_loaded else
            'No trained checkpoint is installed. Predictions are produced by the '
            'deterministic HU-windowing/thresholding fallback pipeline, not a '
            'trained model. See ml/README.md for how to train and install a checkpoint.'
        ),
    )
