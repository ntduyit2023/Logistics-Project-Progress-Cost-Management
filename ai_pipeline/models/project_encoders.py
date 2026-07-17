import torch
import torch.nn as nn
from typing import Dict, Any

class BaseProjectEncoder(nn.Module):
    """
    Abstract base class for all Project-Specific Feature Encoders.
    Converts a variable-size raw feature vector into a standardized Latent Space.
    """
    def __init__(self, latent_dim: int = 64):
        super().__init__()
        self.latent_dim = latent_dim
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Projects raw features into the shared latent space.
        Args:
            x (torch.Tensor): Raw feature tensor of shape [Batch, NumNodes, RawDim] or [Batch, RawDim]
        Returns:
            torch.Tensor: Projected tensor of shape [..., latent_dim]
        """
        raise NotImplementedError

class LogisticsStandardEncoder(BaseProjectEncoder):
    """
    Encoder for the Standard Logistics Project Type (34-D input schema).
    """
    def __init__(self, input_dim: int = 36, latent_dim: int = 64):
        super().__init__(latent_dim)
        self.input_dim = input_dim
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.GELU(),
            nn.LayerNorm(128),
            nn.Dropout(0.1),
            nn.Linear(128, latent_dim),
            nn.GELU(),
            nn.LayerNorm(latent_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Ensures that NaN values from random initializations don't break the encoder
        x = torch.nan_to_num(x, nan=0.0, posinf=1.0, neginf=-1.0)
        return self.encoder(x)

class SoftwareDevEncoder(BaseProjectEncoder):
    """
    Example Encoder for a different project type (e.g., Software Development).
    Suppose it only has 15 dimensions.
    """
    def __init__(self, input_dim: int = 34, latent_dim: int = 64):
        super().__init__(latent_dim)
        self.input_dim = input_dim
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.GELU(),
            nn.LayerNorm(64),
            nn.Linear(64, latent_dim),
            nn.GELU(),
            nn.LayerNorm(latent_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.nan_to_num(x, nan=0.0, posinf=1.0, neginf=-1.0)
        return self.encoder(x)

class EncoderRegistry:
    """Registry to dynamically fetch the correct encoder based on Project Type string."""
    _registry = {
        "logistics_standard": {"encoder": LogisticsStandardEncoder, "num_groups": 8},
        "software_dev": {"encoder": SoftwareDevEncoder, "num_groups": 5}
    }
    
    @classmethod
    def get_encoder(cls, project_type: str, latent_dim: int = 64):
        """
        Fetches the encoder and the corresponding num_groups.
        """
        config = cls._registry.get(project_type.lower())
        if config is None:
            print(f"[WARNING] Project Type '{project_type}' not found in EncoderRegistry. Falling back to 'logistics_standard'.")
            config = cls._registry["logistics_standard"]
            
        encoder = config["encoder"](latent_dim=latent_dim)
        return encoder, config["num_groups"]
