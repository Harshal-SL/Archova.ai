"""AI Software Architecture Engine (SAE) v2 - Lean Design Engine Package."""

import sys
from app.sae.pipeline import SAEPipeline
from app.sae.models.response_models import SoftwareArchitecturePackageResponse

__version__ = "2.0.0"

# Register module alias so `import design_engine` points to `app.sae`
sys.modules["design_engine"] = sys.modules[__name__]

__all__ = ["SAEPipeline", "SoftwareArchitecturePackageResponse"]
