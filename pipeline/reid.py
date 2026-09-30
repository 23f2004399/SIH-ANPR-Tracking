import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import cv2
from typing import List, Protocol, Optional, Union

class BaseReID(Protocol):
    """
    Interface for Re-ID models. Any model (e.g. DINOv2, ResNet, Hybrid)
    must implement `get_embedding` and optional `get_batch_embeddings`.
    """
    def get_embedding(self, image: np.ndarray) -> List[float]:
        ...

    def get_batch_embeddings(self, images: List[np.ndarray], batch_size: int = 64) -> np.ndarray:
        ...


# =========================================================================
#  COLOR FEATURE EXTRACTION (HSV PALETTE)
# =========================================================================

def extract_vehicle_color_histogram(img: Optional[np.ndarray]) -> np.ndarray:
    """
    Extract normalized 16-d HSV color histogram from central vehicle body
    (central 60% crop to exclude road, sky, and vegetation).
    8 Hue bins, 4 Saturation bins, 4 Value bins.
    """
    if img is None or img.size == 0:
        return np.zeros(16, dtype=np.float32)

    h, w = img.shape[:2]
    crop = img[int(h * 0.2):int(h * 0.8), int(w * 0.2):int(w * 0.8)]
    if crop.size == 0:
        crop = img

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    h_hist = cv2.calcHist([hsv], [0], None, [8], [0, 180]).flatten()
    s_hist = cv2.calcHist([hsv], [1], None, [4], [0, 256]).flatten()
    v_hist = cv2.calcHist([hsv], [2], None, [4], [0, 256]).flatten()

    hist = np.concatenate([h_hist, s_hist, v_hist]).astype(np.float32)
    norm = np.linalg.norm(hist)
    return hist / norm if norm > 0 else hist


# =========================================================================
#  RESNET18 FEATURE EXTRACTOR (BASELINE)
# =========================================================================

class ResNet18ReID:
    """
    Lightweight ResNet18-based feature extractor (512-d normalized vector).
    """
    def __init__(self, device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[VehicleReID] Initializing ResNet18 Re-ID model on {self.device}...")
        
        try:
            from torchvision.models import ResNet18_Weights
            base_model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
        except Exception:
            base_model = models.resnet18(pretrained=True)
        
        self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])
        self.feature_extractor = self.feature_extractor.to(self.device)
        self.feature_extractor.eval()
        self.dim = 512
        
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
            return [0.0] * self.dim
            
        if len(image.shape) == 3 and image.shape[2] == 3:
            img_rgb = image[:, :, ::-1].copy()
        else:
            img_rgb = image
            
        pil_img = Image.fromarray(img_rgb)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        features = self.feature_extractor(input_tensor)
        feature_vector = features.squeeze().cpu().numpy()
        
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector = feature_vector / norm
            
        return feature_vector.tolist()

    @torch.no_grad()
    def get_batch_embeddings(self, images: List[np.ndarray], batch_size: int = 64) -> np.ndarray:
        if not images:
            return np.empty((0, self.dim), dtype=np.float32)

        all_features = []
        for i in range(0, len(images), batch_size):
            chunk = images[i:i + batch_size]
            tensors = []
            for img in chunk:
                if img is None or img.size == 0:
                    tensors.append(torch.zeros((3, 224, 224), dtype=torch.float32))
                    continue
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img_rgb = img[:, :, ::-1].copy()
                else:
                    img_rgb = img
                pil_img = Image.fromarray(img_rgb)
                tensors.append(self.transform(pil_img))

            batch_tensor = torch.stack(tensors).to(self.device)
            feats = self.feature_extractor(batch_tensor)  # (B, 512, 1, 1)
            feats = feats.squeeze(-1).squeeze(-1).cpu().numpy().astype(np.float32)
            
            if feats.ndim == 1:
                feats = feats.reshape(1, -1)

            norms = np.linalg.norm(feats, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            feats = feats / norms
            all_features.append(feats)

        return np.vstack(all_features)


# =========================================================================
#  RESNET50 FEATURE EXTRACTOR
# =========================================================================

class ResNet50ReID:
    """
    ResNet50-based feature extractor (2048-d normalized vector).
    """
    def __init__(self, device: str = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[VehicleReID] Initializing ResNet50 Re-ID model on {self.device}...")
        
        try:
            from torchvision.models import ResNet50_Weights
            base_model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
            self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])
            self.feature_extractor = self.feature_extractor.to(self.device)
            self.feature_extractor.eval()
            self.dim = 2048
            self.fallback = None
        except Exception as e:
            print(f"[VehicleReID] ⚠️ Could not load ResNet50 weights ({e}). Falling back to ResNet18...")
            self.fallback = ResNet18ReID(device=self.device)
            self.dim = 512
        
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225])
        ])
        
    @torch.no_grad()
    def get_embedding(self, image: np.ndarray) -> List[float]:
        if self.fallback is not None:
            return self.fallback.get_embedding(image)

        if image is None or image.size == 0:
            return [0.0] * self.dim
            
        if len(image.shape) == 3 and image.shape[2] == 3:
            img_rgb = image[:, :, ::-1].copy()
        else:
            img_rgb = image
            
        pil_img = Image.fromarray(img_rgb)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        features = self.feature_extractor(input_tensor)
        feature_vector = features.squeeze().cpu().numpy()
        
        norm = np.linalg.norm(feature_vector)
        if norm > 0:
            feature_vector = feature_vector / norm
            
        return feature_vector.tolist()

    @torch.no_grad()
    def get_batch_embeddings(self, images: List[np.ndarray], batch_size: int = 64) -> np.ndarray:
        if self.fallback is not None:
            return self.fallback.get_batch_embeddings(images, batch_size)

        if not images:
            return np.empty((0, self.dim), dtype=np.float32)

        all_features = []
        for i in range(0, len(images), batch_size):
            chunk = images[i:i + batch_size]
            tensors = []
            for img in chunk:
                if img is None or img.size == 0:
                    tensors.append(torch.zeros((3, 224, 224), dtype=torch.float32))
                    continue
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img_rgb = img[:, :, ::-1].copy()
                else:
                    img_rgb = img
                pil_img = Image.fromarray(img_rgb)
                tensors.append(self.transform(pil_img))

            batch_tensor = torch.stack(tensors).to(self.device)
            feats = self.feature_extractor(batch_tensor)
            feats = feats.squeeze(-1).squeeze(-1).cpu().numpy().astype(np.float32)
            
            if feats.ndim == 1:
                feats = feats.reshape(1, -1)

            norms = np.linalg.norm(feats, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            feats = feats / norms
            all_features.append(feats)

        return np.vstack(all_features)


# =========================================================================
#  DINOv2 VISION TRANSFORMER FEATURE EXTRACTOR (SOTA ZERO-SHOT RE-ID)
# =========================================================================

class DINOv2ReID:
    """
    Meta DINOv2 (Vision Transformer) feature extractor.
    Produces high-fidelity fine-grained representations capturing vehicle shape,
    grill, headlight geometry, and styling.
    - dinov2_vits14: 384 dimensions (fast, high precision)
    - dinov2_vitb14: 768 dimensions
    """
    def __init__(self, device: str = None, model_name: str = "dinov2_vits14"):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[VehicleReID] Initializing Meta DINOv2 [{model_name}] on {self.device}...")

        self.fallback = None
        try:
            self.model = torch.hub.load("facebookresearch/dinov2", model_name)
            self.model.eval()
            self.model.to(self.device)
            self.dim = 384 if "vits" in model_name else 768
            print(f"[VehicleReID] ✅ DINOv2 model loaded successfully ({self.dim}-d embedding).")
        except Exception as e:
            print(f"[VehicleReID] ⚠️ Could not load DINOv2 from PyTorch Hub ({e}).")
            print("[VehicleReID] Falling back to cached ResNet18 model...")
            self.fallback = ResNet18ReID(device=self.device)
            self.dim = self.fallback.dim

        self.transform = transforms.Compose([
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    @torch.no_grad()
    def get_embedding(self, image: np.ndarray) -> List[float]:
        if self.fallback is not None:
            return self.fallback.get_embedding(image)

        if image is None or image.size == 0:
            return [0.0] * self.dim

        if len(image.shape) == 3 and image.shape[2] == 3:
            img_rgb = image[:, :, ::-1].copy()
        else:
            img_rgb = image

        pil_img = Image.fromarray(img_rgb)
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        feats = self.model(input_tensor).squeeze(0).cpu().numpy().astype(np.float32)

        norm = np.linalg.norm(feats)
        if norm > 0:
            feats = feats / norm

        return feats.tolist()

    @torch.no_grad()
    def get_batch_embeddings(self, images: List[np.ndarray], batch_size: int = 64) -> np.ndarray:
        if self.fallback is not None:
            return self.fallback.get_batch_embeddings(images, batch_size)

        if not images:
            return np.empty((0, self.dim), dtype=np.float32)

        all_features = []
        for i in range(0, len(images), batch_size):
            chunk = images[i:i + batch_size]
            tensors = []
            for img in chunk:
                if img is None or img.size == 0:
                    tensors.append(torch.zeros((3, 224, 224), dtype=torch.float32))
                    continue
                if len(img.shape) == 3 and img.shape[2] == 3:
                    img_rgb = img[:, :, ::-1].copy()
                else:
                    img_rgb = img
                pil_img = Image.fromarray(img_rgb)
                tensors.append(self.transform(pil_img))

            batch_tensor = torch.stack(tensors).to(self.device)
            feats = self.model(batch_tensor).cpu().numpy().astype(np.float32)

            norms = np.linalg.norm(feats, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            feats = feats / norms
            all_features.append(feats)

        return np.vstack(all_features)


# =========================================================================
#  HYBRID COLOR-AWARE FEATURE FUSION
# =========================================================================

class HybridReID:
    """
    Fuses deep visual features (DINOv2 / ResNet) with normalized vehicle body
    HSV color histogram into a single L2-normalized composite vector:
    
        v_hybrid = L2_norm([ sqrt(0.85) * v_deep,  sqrt(0.15) * v_color ])
        
    Properties:
    1. ||v_hybrid|| = 1.0 (Unit L2 normalized)
    2. dot(v_A, v_B) = 0.85 * deep_sim + 0.15 * color_sim
    3. Guarantees instant physical color-consistency in standard vector databases
       or dot-product matrix operations!
    """
    def __init__(self, base_model: BaseReID, color_weight: float = 0.15):
        self.base_model = base_model
        self.color_weight = color_weight
        self.deep_weight = 1.0 - color_weight
        self.w_deep_sqrt = np.sqrt(self.deep_weight)
        self.w_color_sqrt = np.sqrt(self.color_weight)
        self.dim = getattr(base_model, "dim", 512) + 16
        print(f"[VehicleReID] ✨ Hybrid Color-Aware Fusion Enabled: {self.dim}-d embedding "
              f"({self.deep_weight*100:.0f}% Deep Structure + {self.color_weight*100:.0f}% HSV Palette)")

    def get_embedding(self, image: np.ndarray) -> List[float]:
        deep_feat = np.array(self.base_model.get_embedding(image), dtype=np.float32)
        color_feat = extract_vehicle_color_histogram(image)

        hybrid = np.concatenate([
            self.w_deep_sqrt * deep_feat,
            self.w_color_sqrt * color_feat
        ]).astype(np.float32)

        norm = np.linalg.norm(hybrid)
        if norm > 0:
            hybrid = hybrid / norm

        return hybrid.tolist()

    def get_batch_embeddings(self, images: List[np.ndarray], batch_size: int = 64) -> np.ndarray:
        if not images:
            return np.empty((0, self.dim), dtype=np.float32)

        deep_feats = self.base_model.get_batch_embeddings(images, batch_size=batch_size)
        color_feats = np.array([extract_vehicle_color_histogram(im) for im in images], dtype=np.float32)

        hybrid_feats = np.hstack([
            self.w_deep_sqrt * deep_feats,
            self.w_color_sqrt * color_feats
        ])

        norms = np.linalg.norm(hybrid_feats, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return hybrid_feats / norms


# =========================================================================
#  FACTORY FUNCTION
# =========================================================================

def get_reid_model(model_name: str = "dinov2", device: str = None, hybrid_color: bool = True) -> BaseReID:
    """
    Factory to instantiate Re-ID feature extractors.
    
    Supported backbones:
    - 'dinov2' / 'dinov2_vits14' : Meta DINOv2 ViT-S/14 (384-d, SOTA zero-shot Re-ID)
    - 'dinov2_vitb14'            : Meta DINOv2 ViT-B/14 (768-d)
    - 'resnet50'                 : ResNet50 (2048-d)
    - 'resnet18'                 : ResNet18 (512-d, lightweight baseline)
    
    If `hybrid_color=True`, wraps in `HybridReID` to bake normalized HSV body color
    palette into the embedding vector.
    """
    model_name = model_name.lower().strip()

    if "dinov2" in model_name:
        sub = "dinov2_vitb14" if "vitb" in model_name else "dinov2_vits14"
        base_model = DINOv2ReID(device=device, model_name=sub)
    elif model_name == "resnet50":
        base_model = ResNet50ReID(device=device)
    elif model_name == "resnet18":
        base_model = ResNet18ReID(device=device)
    else:
        # Default fallback to DINOv2 on GPU, ResNet18 on CPU
        print(f"[VehicleReID] Unknown model '{model_name}'. Defaulting to ResNet18...")
        base_model = ResNet18ReID(device=device)

    if hybrid_color:
        return HybridReID(base_model=base_model, color_weight=0.15)
    return base_model
