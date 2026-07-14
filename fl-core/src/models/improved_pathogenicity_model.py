import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    """Residual block with batch normalization and dropout, supports input_dim != output_dim"""
    def __init__(self, input_dim, output_dim, dropout=0.3):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, output_dim),
            nn.BatchNorm1d(output_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(output_dim, output_dim),
            nn.BatchNorm1d(output_dim)
        )
        self.relu = nn.ReLU()
        # Projection for residual if needed
        if input_dim != output_dim:
            self.projection = nn.Linear(input_dim, output_dim)
        else:
            self.projection = nn.Identity()

    def forward(self, x):
        residual = self.projection(x)
        out = self.layers(x)
        out += residual
        return self.relu(out)

class AttentionModule(nn.Module):
    """Self-attention mechanism for feature importance"""
    def __init__(self, input_dim, num_heads=8):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = input_dim // num_heads
        assert self.head_dim * num_heads == input_dim, "input_dim must be divisible by num_heads"
        
        self.query = nn.Linear(input_dim, input_dim)
        self.key = nn.Linear(input_dim, input_dim)
        self.value = nn.Linear(input_dim, input_dim)
        self.output = nn.Linear(input_dim, input_dim)
        
    def forward(self, x):
        batch_size = x.size(0)
        
        # Reshape for multi-head attention
        Q = self.query(x).view(batch_size, self.num_heads, self.head_dim)
        K = self.key(x).view(batch_size, self.num_heads, self.head_dim)
        V = self.value(x).view(batch_size, self.num_heads, self.head_dim)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attention_weights = F.softmax(scores, dim=-1)
        attended = torch.matmul(attention_weights, V)
        
        # Reshape and apply output projection
        attended = attended.view(batch_size, -1)
        output = self.output(attended)
        return output

class FeatureExtractor(nn.Module):
    """Separate feature extractor for different data types"""
    def __init__(self, input_dim, embedding_dim=128):
        super().__init__()
        self.feature_projection = nn.Sequential(
            nn.Linear(input_dim, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
    def forward(self, x):
        return self.feature_projection(x)

class ImprovedPathogenicityClassifier(nn.Module):
    """
    Advanced pathogenicity classifier with attention mechanisms, 
    residual connections, and improved architecture for genomic data.
    """
    
    def __init__(self, input_size, output_size, hidden_dims=[512, 256, 128], dropout=0.3):
        super().__init__()
        
        self.input_size = input_size
        self.output_size = output_size
        
        # Feature extraction layers
        self.feature_extractor = FeatureExtractor(input_size, hidden_dims[0])
        
        # Attention mechanism
        self.attention = AttentionModule(hidden_dims[0])
        
        # Main network with residual connections
        self.layers = nn.ModuleList()
        for i in range(len(hidden_dims) - 1):
            if i == 0:
                # First layer after attention
                layer = nn.Sequential(
                    nn.Linear(hidden_dims[i], hidden_dims[i+1]),
                    nn.BatchNorm1d(hidden_dims[i+1]),
                    nn.ReLU(),
                    nn.Dropout(dropout)
                )
            elif i < len(hidden_dims) - 2:
                # Residual blocks for intermediate layers
                layer = ResidualBlock(hidden_dims[i], hidden_dims[i+1], dropout)
            else:
                # Last layer: standard linear projection
                layer = nn.Sequential(
                    nn.Linear(hidden_dims[i], hidden_dims[i+1]),
                    nn.BatchNorm1d(hidden_dims[i+1]),
                    nn.ReLU(),
                    nn.Dropout(dropout)
                )
            self.layers.append(layer)
        
        # Final classification layers (generalized)
        classifier_layers = []
        in_dim = hidden_dims[-1]
        # You can add more layers here if desired
        classifier_layers.append(nn.Linear(in_dim, in_dim // 2))
        classifier_layers.append(nn.BatchNorm1d(in_dim // 2))
        classifier_layers.append(nn.ReLU())
        classifier_layers.append(nn.Dropout(dropout * 0.5))
        classifier_layers.append(nn.Linear(in_dim // 2, output_size))
        self.classifier = nn.Sequential(*classifier_layers)
        
        # Initialize weights
        self._initialize_weights()
        
    def _initialize_weights(self):
        """Initialize model weights with better initialization"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                # Use Kaiming initialization for ReLU activations
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, x):
        # Feature extraction
        features = self.feature_extractor(x)
        
        # Apply attention
        attended_features = self.attention(features)
        
        # Pass through main network
        current = attended_features
        for layer in self.layers:
            current = layer(current)
        
        # Final classification
        output = self.classifier(current)
        return output
    
    def get_num_parameters(self):
        """Get total number of parameters"""
        return sum(p.numel() for p in self.parameters())
    
    def get_trainable_parameters(self):
        """Get number of trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

class LightweightPathogenicityClassifier(nn.Module):
    """
    Lightweight version of the pathogenicity classifier for resource-constrained environments
    """
    
    def __init__(self, input_size, output_size, hidden_dims=[256, 128, 64], dropout=0.2):
        super().__init__()
        
        self.input_size = input_size
        self.output_size = output_size
        
        # Simplified feature extractor
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_size, hidden_dims[0]),
            nn.BatchNorm1d(hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        # Main network (no attention for efficiency)
        self.layers = nn.ModuleList()
        for i in range(len(hidden_dims) - 1):
            layer = nn.Sequential(
                nn.Linear(hidden_dims[i], hidden_dims[i+1]),
                nn.BatchNorm1d(hidden_dims[i+1]),
                nn.ReLU(),
                nn.Dropout(dropout)
            )
            self.layers.append(layer)
        
        # Final classification
        self.classifier = nn.Linear(hidden_dims[-1], output_size)
        
        self._initialize_weights()
        
    def _initialize_weights(self):
        """Initialize model weights"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, x):
        # Feature extraction
        features = self.feature_extractor(x)
        
        # Pass through main network
        current = features
        for layer in self.layers:
            current = layer(current)
        
        # Final classification
        output = self.classifier(current)
        return output
    
    def get_num_parameters(self):
        """Get total number of parameters"""
        return sum(p.numel() for p in self.parameters())
    
    def get_trainable_parameters(self):
        """Get number of trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

class EnsemblePathogenicityClassifier(nn.Module):
    """
    Ensemble of multiple pathogenicity classifiers for improved performance
    """
    
    def __init__(self, input_size, output_size, num_models=3, ensemble_member_type='improved'):
        super().__init__()
        
        self.input_size = input_size
        self.output_size = output_size
        self.num_models = num_models
        
        # Create ensemble of models
        self.models = nn.ModuleList()
        for i in range(num_models):
            if ensemble_member_type == 'improved':
                model = ImprovedPathogenicityClassifier(
                    input_size=input_size,
                    output_size=output_size
                )
            else:
                model = LightweightPathogenicityClassifier(
                    input_size=input_size,
                    output_size=output_size
                )
            self.models.append(model)
        
        # Ensemble weights (learnable)
        self.ensemble_weights = nn.Parameter(torch.ones(num_models) / num_models)
        
    def forward(self, x):
        # Get predictions from all models
        predictions = []
        for model in self.models:
            pred = model(x)
            predictions.append(pred)
        
        # Weighted ensemble
        weighted_preds = []
        for i, pred in enumerate(predictions):
            weighted_preds.append(self.ensemble_weights[i] * pred)
        
        # Sum weighted predictions
        ensemble_output = sum(weighted_preds)
        return ensemble_output
    
    def get_num_parameters(self):
        """Get total number of parameters"""
        return sum(p.numel() for p in self.parameters())
    
    def get_trainable_parameters(self):
        """Get number of trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

def create_model(model_type='improved', input_size=None, output_size=2, **kwargs):
    """
    Factory function to create different types of pathogenicity models
    
    Args:
        model_type: Type of model ('improved', 'lightweight', 'ensemble')
        input_size: Input feature dimension
        output_size: Output classes (default: 2 for binary classification)
        **kwargs: Additional arguments for specific model types
    
    Returns:
        nn.Module: The created model
    """
    
    if input_size is None:
        raise ValueError("input_size must be specified")
    
    if model_type == 'improved':
        return ImprovedPathogenicityClassifier(
            input_size=input_size,
            output_size=output_size,
            **kwargs
        )
    elif model_type == 'lightweight':
        return LightweightPathogenicityClassifier(
            input_size=input_size,
            output_size=output_size,
            **kwargs
        )
    elif model_type == 'ensemble':
        return EnsemblePathogenicityClassifier(
            input_size=input_size,
            output_size=output_size,
            **kwargs
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def get_model_summary(model):
    """
    Get a detailed summary of the model architecture
    
    Args:
        model: PyTorch model
        
    Returns:
        dict: Model summary information
    """
    summary = {
        'model_type': model.__class__.__name__,
        'total_parameters': model.get_num_parameters(),
        'trainable_parameters': model.get_trainable_parameters(),
        'input_size': getattr(model, 'input_size', 'Unknown'),
        'output_size': getattr(model, 'output_size', 'Unknown'),
        'model_size_mb': model.get_num_parameters() * 4 / (1024 * 1024)  # Assuming float32
    }
    
    return summary 