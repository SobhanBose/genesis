import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class FocalLoss(nn.Module):
    """
    Focal Loss for addressing class imbalance in genomic data
    """
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
        
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

class LabelSmoothingLoss(nn.Module):
    """
    Label smoothing for better generalization
    """
    def __init__(self, classes, smoothing=0.1, dim=-1):
        super().__init__()
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing
        self.cls = classes
        self.dim = dim

    def forward(self, pred, target):
        pred = F.log_softmax(pred, dim=self.dim)
        with torch.no_grad():
            true_dist = torch.zeros_like(pred)
            true_dist.fill_(self.smoothing / (self.cls - 1))
            true_dist.scatter_(1, target.data.unsqueeze(1), self.confidence)
        return torch.mean(torch.sum(-true_dist * pred, dim=self.dim))

class CombinedLoss(nn.Module):
    """
    Combined loss function with focal loss and label smoothing
    """
    def __init__(self, alpha=1, gamma=2, smoothing=0.1, focal_weight=0.7):
        super().__init__()
        self.focal_loss = FocalLoss(alpha=alpha, gamma=gamma)
        self.label_smoothing_loss = LabelSmoothingLoss(classes=2, smoothing=smoothing)
        self.focal_weight = focal_weight
        
    def forward(self, inputs, targets):
        focal = self.focal_loss(inputs, targets)
        smooth = self.label_smoothing_loss(inputs, targets)
        return self.focal_weight * focal + (1 - self.focal_weight) * smooth

class FedProxLoss(nn.Module):
    """
    FedProx loss with proximal term for federated learning
    """
    def __init__(self, mu=0.01, base_loss='cross_entropy'):
        super().__init__()
        self.mu = mu
        if base_loss == 'cross_entropy':
            self.base_loss = nn.CrossEntropyLoss()
        elif base_loss == 'focal':
            self.base_loss = FocalLoss()
        elif base_loss == 'combined':
            self.base_loss = CombinedLoss()
        else:
            self.base_loss = nn.CrossEntropyLoss()
            
    def forward(self, inputs, targets, global_params, local_params):
        # Base loss
        base_loss = self.base_loss(inputs, targets)
        
        # Proximal term
        proximal_term = 0.0
        for name, param in local_params.items():
            if name in global_params:
                proximal_term += torch.norm(param - global_params[name]) ** 2
        proximal_term = (self.mu / 2) * proximal_term
        
        return base_loss + proximal_term

class UncertaintyLoss(nn.Module):
    """
    Loss function that accounts for prediction uncertainty
    """
    def __init__(self, num_classes=2, uncertainty_weight=0.1):
        super().__init__()
        self.num_classes = num_classes
        self.uncertainty_weight = uncertainty_weight
        
    def forward(self, logits, targets):
        # Standard cross-entropy loss
        ce_loss = F.cross_entropy(logits, targets)
        
        # Uncertainty penalty (entropy of predictions)
        probs = F.softmax(logits, dim=1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-8), dim=1).mean()
        
        return ce_loss + self.uncertainty_weight * entropy

class AdaptiveLoss(nn.Module):
    """
    Adaptive loss that adjusts based on training progress
    """
    def __init__(self, initial_weight=1.0, decay_rate=0.95):
        super().__init__()
        self.initial_weight = initial_weight
        self.decay_rate = decay_rate
        self.current_epoch = 0
        
    def update_epoch(self, epoch):
        self.current_epoch = epoch
        
    def forward(self, inputs, targets):
        # Adjust loss weight based on training progress
        weight = self.initial_weight * (self.decay_rate ** self.current_epoch)
        return weight * F.cross_entropy(inputs, targets)

def get_loss_function(loss_type='cross_entropy', **kwargs):
    """
    Factory function to get loss function based on type
    """
    if loss_type == 'cross_entropy':
        return nn.CrossEntropyLoss()
    elif loss_type == 'focal':
        return FocalLoss(**kwargs)
    elif loss_type == 'label_smoothing':
        return LabelSmoothingLoss(classes=2, **kwargs)
    elif loss_type == 'combined':
        return CombinedLoss(**kwargs)
    elif loss_type == 'uncertainty':
        return UncertaintyLoss(**kwargs)
    elif loss_type == 'adaptive':
        return AdaptiveLoss(**kwargs)
    else:
        return nn.CrossEntropyLoss() 