import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    """Residual block with batch normalization and dropout, supports input_dim != output_dim"""

    def __init__(self, input_dim, output_dim, dropout=0.3):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(input_dim, output_dim), nn.BatchNorm1d(output_dim), nn.ReLU(), nn.Dropout(dropout), nn.Linear(output_dim, output_dim), nn.BatchNorm1d(output_dim))
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
        scores = torch.matmul(Q, K.transpose(-2, -1)) / (self.head_dim**0.5)
        attention_weights = F.softmax(scores, dim=-1)
        attended = torch.matmul(attention_weights, V)

        # Reshape and apply output projection
        attended = attended.view(batch_size, -1)
        output = self.output(attended)
        return output


class FeatureExtractor(nn.Module):
    """Separate feature extractor for different data types, supports gene embedding"""

    def __init__(self, input_dim, embedding_dim=128, gene_vocab_size=None, gene_emb_dim=32, use_gene_embedding=False):
        super().__init__()
        self.use_gene_embedding = use_gene_embedding
        if use_gene_embedding and gene_vocab_size is not None:
            self.gene_embedding = nn.Embedding(gene_vocab_size, gene_emb_dim)
            self.feature_projection = nn.Sequential(nn.Linear(input_dim + gene_emb_dim, embedding_dim), nn.BatchNorm1d(embedding_dim), nn.ReLU(), nn.Dropout(0.2))
        else:
            self.gene_embedding = None
            self.feature_projection = nn.Sequential(nn.Linear(input_dim, embedding_dim), nn.BatchNorm1d(embedding_dim), nn.ReLU(), nn.Dropout(0.2))

    def forward(self, x, gene_idx=None):
        if self.use_gene_embedding and self.gene_embedding is not None and gene_idx is not None:
            gene_emb = self.gene_embedding(gene_idx)
            if gene_emb.dim() == 1:
                gene_emb = gene_emb.unsqueeze(0)
            x = torch.cat([x, gene_emb], dim=-1)
        return self.feature_projection(x)


class ImprovedPathogenicityClassifier(nn.Module):
    """
    Advanced pathogenicity classifier with attention mechanisms,
    residual connections, and improved architecture for genomic data.
    """

    def __init__(self, input_size, output_size, hidden_dims=[512, 256, 128], dropout=0.3, gene_vocab_size=None, use_gene_embedding=False, gene_emb_dim=32):
        super().__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.use_gene_embedding = use_gene_embedding
        self.gene_vocab_size = gene_vocab_size
        self.gene_emb_dim = gene_emb_dim
        # Feature extraction layers
        self.feature_extractor = FeatureExtractor(input_size, hidden_dims[0], gene_vocab_size=gene_vocab_size, gene_emb_dim=gene_emb_dim, use_gene_embedding=use_gene_embedding)
        # Attention mechanism
        self.attention = AttentionModule(hidden_dims[0])
        # Main network with residual connections
        self.layers = nn.ModuleList()
        for i in range(len(hidden_dims) - 1):
            if i == 0:
                layer = nn.Sequential(nn.Linear(hidden_dims[i], hidden_dims[i + 1]), nn.BatchNorm1d(hidden_dims[i + 1]), nn.ReLU(), nn.Dropout(dropout))
            elif i < len(hidden_dims) - 2:
                layer = ResidualBlock(hidden_dims[i], hidden_dims[i + 1], dropout)
            else:
                layer = nn.Sequential(nn.Linear(hidden_dims[i], hidden_dims[i + 1]), nn.BatchNorm1d(hidden_dims[i + 1]), nn.ReLU(), nn.Dropout(dropout))
            self.layers.append(layer)
        # Final classification layers (generalized)
        classifier_layers = []
        in_dim = hidden_dims[-1]
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
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)

    def forward(self, x, gene_idx=None):
        # Feature extraction
        features = self.feature_extractor(x, gene_idx=gene_idx)
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

    def __init__(self, input_size, output_size, hidden_dims=[256, 128, 64], dropout=0.2, gene_vocab_size=None, use_gene_embedding=False, gene_emb_dim=32):
        super().__init__()

        self.input_size = input_size
        self.output_size = output_size

        # Simplified feature extractor
        self.feature_extractor = FeatureExtractor(input_size, hidden_dims[0], gene_vocab_size=gene_vocab_size, gene_emb_dim=gene_emb_dim, use_gene_embedding=use_gene_embedding)

        # Main network (no attention for efficiency)
        self.layers = nn.ModuleList()
        for i in range(len(hidden_dims) - 1):
            layer = nn.Sequential(nn.Linear(hidden_dims[i], hidden_dims[i + 1]), nn.BatchNorm1d(hidden_dims[i + 1]), nn.ReLU(), nn.Dropout(dropout))
            self.layers.append(layer)

        # Final classification
        self.classifier = nn.Linear(hidden_dims[-1], output_size)

        self._initialize_weights()

    def _initialize_weights(self, gene_idx=None):
        """Initialize model weights"""

        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)

    def forward(self, x, gene_idx=None):
        # Feature extraction
        features = self.feature_extractor(x, gene_idx=gene_idx)

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

    def __init__(self, input_size, output_size, ensemble_member_type="improved", num_models=3, hidden_dims=[[512, 256, 64]], dropout=0.3, gene_vocab_size=None, use_gene_embedding=False, gene_emb_dim=32):
        super().__init__()

        self.input_size = input_size
        self.output_size = output_size
        self.num_models = num_models

        # Ensure hidden_dims is a list of lists with correct length
        if not isinstance(hidden_dims, list):
            hidden_dims = [[512, 256, 64]] * num_models
        elif len(hidden_dims) != num_models:
            # If length doesn't match, repeat the first config for all models
            if len(hidden_dims) > 0:
                # Check if hidden_dims is a list of integers (single config)
                if all(isinstance(dim, (int, float)) for dim in hidden_dims):
                    hidden_dims = [hidden_dims] * num_models
                else:
                    # It's already a list of lists, repeat the first one
                    first_config = hidden_dims[0] if isinstance(hidden_dims[0], list) else hidden_dims
                    hidden_dims = [first_config] * num_models
            else:
                hidden_dims = [[512, 256, 64]] * num_models
        else:
            # Length matches, but need to check if it's a list of integers
            if len(hidden_dims) > 0 and all(isinstance(dim, (int, float)) for dim in hidden_dims):
                # It's a list of integers with correct length, convert to list of lists
                hidden_dims = [hidden_dims] * num_models

        # Simplified feature extractor - use first dimension from hidden_dims[0]
        embedding_dim = hidden_dims[0][0] if isinstance(hidden_dims[0], list) else hidden_dims[0]
        self.feature_extractor = FeatureExtractor(input_size, embedding_dim, gene_vocab_size=gene_vocab_size, gene_emb_dim=gene_emb_dim, use_gene_embedding=use_gene_embedding)

        # Create ensemble of models
        self.models = nn.ModuleList()
        for i in range(num_models):
            if ensemble_member_type == "improved":
                model = ImprovedPathogenicityClassifier(input_size=input_size, output_size=output_size, hidden_dims=hidden_dims[i], dropout=0.3, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding)
            else:
                model = LightweightPathogenicityClassifier(input_size=input_size, output_size=output_size, hidden_dims=hidden_dims[i], dropout=0.3, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding)
            self.models.append(model)

        # Ensemble weights (learnable)
        self.ensemble_weights = nn.Parameter(torch.ones(num_models) / num_models)

    def forward(self, x, gene_idx=None):
        # Get predictions from all models
        predictions = []
        for model in self.models:
            pred = model(x, gene_idx=gene_idx)
            predictions.append(pred)

        # Weighted ensemble
        weighted_preds = []
        for i, pred in enumerate(predictions):
            weighted_preds.append(self.ensemble_weights[i] * pred)

        # Sum weighted predictions
        ensemble_output = sum(weighted_preds) / sum(self.ensemble_weights)
        return ensemble_output

    def get_num_parameters(self):
        """Get total number of parameters"""
        return sum(p.numel() for p in self.parameters())

    def get_trainable_parameters(self):
        """Get number of trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


def create_model(model_type="improved", input_size=None, output_size=2, gene_vocab_size=None, use_gene_embedding=False, **kwargs):
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

    if model_type == "improved":
        return ImprovedPathogenicityClassifier(input_size=input_size, output_size=output_size, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding, **kwargs)
    elif model_type == "lightweight":
        return LightweightPathogenicityClassifier(input_size=input_size, output_size=output_size, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding, **kwargs)
    elif model_type == "ensemble":
        return EnsemblePathogenicityClassifier(input_size=input_size, output_size=output_size, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding, **kwargs)
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
        "model_type": model.__class__.__name__,
        "total_parameters": model.get_num_parameters(),
        "trainable_parameters": model.get_trainable_parameters(),
        "input_size": getattr(model, "input_size", "Unknown"),
        "output_size": getattr(model, "output_size", "Unknown"),
        "model_size_mb": model.get_num_parameters() * 4 / (1024 * 1024),  # Assuming float32
    }

    return summary
