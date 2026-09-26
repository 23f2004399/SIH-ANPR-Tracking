import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
from typing import List, Protocol

class BaseReID(Protocol):
    """
    Interface for Re-ID models. Any new model (e.g., OSNet, MobileNet) 
    must implement this `get_embedding` method.
    """
    def get_embedding(self, image: np.ndarray) -> List[float]:
        ...

class ResNet18ReID:
    """
    Lightweight ResNet18-based feature extractor for Vehicle Re-ID.
    """
    def __init__(self, device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[VehicleReID] Initializing ResNet18 Re-ID model on {self.device}...")
        
        base_model = models.resnet18(pretrained=True)
        
        # Remove the classification head (fc)
        self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])
        self.feature_extractor = self.feature_extractor.to(self.device)
        self.feature_extractor.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225])
        ])
        
    @torch.no_grad()
    def get_embedding(self, image: np.ndarray) -> List[float]:
        if image is None or image.size == 0:
            return [0.0] * 512
            
        if len(image.shape) == 3 and image.shape[2] == 3:
            img_rgb = image[:, :, ::-1].copy()
        else:
            img_rgb = image
            
        pil_img = Image.fromarray(img_rgb)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        features = self.feature_extractor(input_tensor)
        feature_vector = features.squeeze().cpu().numpy()
        
        # L2 Normalize
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector = feature_vector / norm
            
        return feature_vector.tolist()

# Factory function for easy swapping
def get_reid_model(model_name: str = "resnet18", device: str = None) -> BaseReID:
    """
    Factory to load Re-ID models. Allows easy drop-in replacements later (e.g., 'osnet').
    """
    model_name = model_name.lower()
    if model_name == "resnet18":
        return ResNet18ReID(device)
    else:
        raise ValueError(f"Unknown Re-ID model type: {model_name}. Please implement it in reid.py!")
