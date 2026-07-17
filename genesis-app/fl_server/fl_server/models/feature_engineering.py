import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from gensim.models import Word2Vec
import torch
import torch.nn as nn
from typing import List, Dict, Tuple, Optional
import warnings
import os
from pathlib import Path

warnings.filterwarnings("ignore")

from .ref_alt_embeddings import KmerGenerator


class GenomicFeatureEngineer:
    """
    Advanced feature engineering for genomic data
    """

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.scalers = {}
        self.feature_selectors = {}
        self.pca_models = {}
        self.feature_importance = {}
        self.label_encoders = {}
        self.word2vec_models = {}
        self.kmer_generator = None
        self.gene_vocab_size = None  # Initialize for gene embedding

        # Don't pre-fit chromosome label encoder - let it be fitted with actual data

    def create_sequence_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create sequence-based features from ref/alt columns
        """
        df = df.copy()

        # Sequence length features
        df["ref_length"] = df["ref"].str.len()
        df["alt_length"] = df["alt"].str.len()
        df["length_diff"] = df["alt_length"] - df["ref_length"]

        # GC content
        df["ref_gc_content"] = df["ref"].apply(lambda x: (x.count("G") + x.count("C")) / len(x) if len(x) > 0 else 0)
        df["alt_gc_content"] = df["alt"].apply(lambda x: (x.count("G") + x.count("C")) / len(x) if len(x) > 0 else 0)
        df["gc_content_diff"] = df["alt_gc_content"] - df["ref_gc_content"]

        # Nucleotide frequency features
        for nucleotide in ["A", "T", "G", "C"]:
            df[f"ref_{nucleotide}_freq"] = df["ref"].apply(lambda x: x.count(nucleotide) / len(x) if len(x) > 0 else 0)
            df[f"alt_{nucleotide}_freq"] = df["alt"].apply(lambda x: x.count(nucleotide) / len(x) if len(x) > 0 else 0)

        # Transition/transversion features
        df["is_transition"] = df.apply(self._is_transition, axis=1)
        df["is_transversion"] = df.apply(self._is_transversion, axis=1)

        return df

    def _is_transition(self, row):
        """Check if mutation is a transition (purine->purine or pyrimidine->pyrimidine)"""
        ref, alt = row["ref"], row["alt"]
        if len(ref) == 1 and len(alt) == 1:
            purines = {"A", "G"}
            pyrimidines = {"C", "T"}
            return (ref in purines and alt in purines) or (ref in pyrimidines and alt in pyrimidines)
        return False

    def _is_transversion(self, row):
        """Check if mutation is a transversion (purine->pyrimidine or vice versa)"""
        ref, alt = row["ref"], row["alt"]
        if len(ref) == 1 and len(alt) == 1:
            purines = {"A", "G"}
            pyrimidines = {"C", "T"}
            return (ref in purines and alt in pyrimidines) or (ref in pyrimidines and alt in purines)
        return False

    def create_conservation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create conservation-based features
        """
        df = df.copy()

        # Conservation score features
        conservation_cols = [col for col in df.columns if "phylop" in col or "phastcons" in col]

        if conservation_cols:
            # Aggregate conservation scores
            df["mean_conservation"] = df[conservation_cols].mean(axis=1)
            df["max_conservation"] = df[conservation_cols].max(axis=1)
            df["min_conservation"] = df[conservation_cols].min(axis=1)
            df["conservation_std"] = df[conservation_cols].std(axis=1)

            # Conservation categories
            df["highly_conserved"] = (df["mean_conservation"] > 0.8).astype(int)
            df["moderately_conserved"] = ((df["mean_conservation"] > 0.3) & (df["mean_conservation"] <= 0.8)).astype(int)
            df["poorly_conserved"] = (df["mean_conservation"] <= 0.3).astype(int)
        else:
            # If no conservation columns exist, create default values
            df["mean_conservation"] = 0.0
            df["max_conservation"] = 0.0
            df["min_conservation"] = 0.0
            df["conservation_std"] = 0.0
            df["highly_conserved"] = 0
            df["moderately_conserved"] = 0
            df["poorly_conserved"] = 1

        return df

    def create_functional_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create functional impact features
        """
        df = df.copy()

        # Functional impact scores
        impact_cols = [col for col in df.columns if "score" in col and col not in ["class"]]

        if impact_cols:
            # Aggregate impact scores
            df["mean_impact_score"] = df[impact_cols].mean(axis=1)
            df["max_impact_score"] = df[impact_cols].max(axis=1)
            df["impact_score_std"] = df[impact_cols].std(axis=1)

            # High impact mutations
            df["high_impact"] = (df["mean_impact_score"] > df["mean_impact_score"].quantile(0.8)).astype(int)
            df["low_impact"] = (df["mean_impact_score"] < df["mean_impact_score"].quantile(0.2)).astype(int)
        else:
            # If no impact columns exist, create default values
            df["mean_impact_score"] = 0.0
            df["max_impact_score"] = 0.0
            df["impact_score_std"] = 0.0
            df["high_impact"] = 0
            df["low_impact"] = 0

        return df

    def create_population_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create population frequency features
        """
        df = df.copy()

        # Allele frequency features
        af_cols = [col for col in df.columns if col.startswith("af_")]

        if af_cols:
            # Aggregate allele frequencies
            df["mean_af"] = df[af_cols].mean(axis=1)
            df["max_af"] = df[af_cols].max(axis=1)
            df["af_std"] = df[af_cols].std(axis=1)

            # Rare variant features
            df["rare_variant"] = (df["mean_af"] < 0.01).astype(int)
            df["common_variant"] = (df["mean_af"] > 0.05).astype(int)
        else:
            # If no allele frequency columns exist, create default values
            df["mean_af"] = 0.0
            df["max_af"] = 0.0
            df["af_std"] = 0.0
            df["rare_variant"] = 0
            df["common_variant"] = 0

        return df

    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between different feature groups
        """
        df = df.copy()

        # Conservation x Impact interaction
        if "mean_conservation" in df.columns and "mean_impact_score" in df.columns:
            df["conservation_impact_interaction"] = df["mean_conservation"] * df["mean_impact_score"]

        # Frequency x Impact interaction
        if "mean_af" in df.columns and "mean_impact_score" in df.columns:
            df["frequency_impact_interaction"] = df["mean_af"] * df["mean_impact_score"]

        # Conservation x Frequency interaction
        if "mean_conservation" in df.columns and "mean_af" in df.columns:
            df["conservation_frequency_interaction"] = df["mean_conservation"] * df["mean_af"]

        return df

    def select_features(self, X: pd.DataFrame, y: pd.Series, method="mutual_info", k=100) -> pd.DataFrame:
        """
        Feature selection using various methods
        """
        if method == "mutual_info":
            selector = SelectKBest(score_func=mutual_info_classif, k=min(k, X.shape[1]))
        elif method == "f_classif":
            selector = SelectKBest(score_func=f_classif, k=min(k, X.shape[1]))
        elif method == "random_forest":
            # Use Random Forest feature importance
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X, y)
            feature_importance = pd.DataFrame({"feature": X.columns, "importance": rf.feature_importances_}).sort_values("importance", ascending=False)
            selected_features = feature_importance.head(k)["feature"].tolist()
            return X[selected_features]
        else:
            return X

        X_selected = selector.fit_transform(X, y)
        selected_features = X.columns[selector.get_support()].tolist()

        self.feature_selectors[method] = selector
        self.feature_importance[method] = dict(zip(selected_features, selector.scores_))

        return pd.DataFrame(X_selected, columns=selected_features, index=X.index)

    def apply_pca(self, X: pd.DataFrame, n_components=50, method="pca") -> pd.DataFrame:
        """
        Apply dimensionality reduction
        """
        if method == "pca":
            pca = PCA(n_components=min(n_components, X.shape[1]))
            X_reduced = pca.fit_transform(X)
            self.pca_models[method] = pca

            # Create column names for PCA components
            pca_columns = [f"pca_{i}" for i in range(X_reduced.shape[1])]
            return pd.DataFrame(X_reduced, columns=pca_columns, index=X.index)

        return X

    def scale_features(self, X: pd.DataFrame, method="robust", is_train=True) -> pd.DataFrame:
        """
        Scale features using various methods
        """
        if is_train:
            if method == "standard":
                scaler = StandardScaler()
            elif method == "robust":
                scaler = RobustScaler()
            elif method == "minmax":
                scaler = MinMaxScaler()
            else:
                return X

            X_scaled = scaler.fit_transform(X)
            self.scalers[method] = scaler
        else:
            if method not in self.scalers:
                raise RuntimeError(f"Scaler '{method}' has not been fitted. Call scale_features with is_train=True first.")
            scaler = self.scalers[method]
            X_scaled = scaler.transform(X)

        return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)

    def engineer_all_features(self, df: pd.DataFrame, target_col="class") -> pd.DataFrame:
        """
        Feature engineering:
        - Label encode 'chr'
        - Optionally label encode 'gene' for embedding
        - Remove 'gene' if not using embedding
        - One-hot encode 'ref' and 'alt' sequences, drop originals
        - Keep all other columns (except 'gene', 'ref', 'alt') and the target 'class'
        - Fill NaN with 0
        """
        print("🔧 Feature engineering pipeline (gene embedding configurable, one-hot encoding for sequences)...")
        df = df.copy()

        # Label encode 'chr'
        if "chr" in df.columns:
            # Ensure chr column is string type for consistent encoding
            df['chr'] = df['chr'].astype(str)
            df = self.encode_categorical_features(df, categorical_cols=["chr"])

        use_gene_embedding = self.config.get("feature_engineering", {}).get("use_gene_embedding", False)
        if "gene" in df.columns:
            if use_gene_embedding:
                # Label encode gene as integer index for embedding
                df = self.encode_categorical_features(df, categorical_cols=["gene"])
                self.gene_vocab_size = df["gene"].nunique()
            else:
                df = df.drop(columns=["gene"])
                self.gene_vocab_size = None
        else:
            self.gene_vocab_size = None

        # One-hot encode 'ref' and 'alt' sequences, then drop originals
        df = self.embed_ref_alt_sequences(df)
        if "ref" in df.columns:
            df = df.drop(columns=["ref"])
        if "alt" in df.columns:
            df = df.drop(columns=["alt"])

        # Fill any NaN values with 0
        nan_count = df.isna().sum().sum()
        if nan_count > 0:
            print(f"    Found {nan_count} NaN values, filling with 0")
            df = df.fillna(0)

        print(f"✅ Feature engineering complete. Final shape: {df.shape}")
        return df

    def get_feature_summary(self) -> Dict:
        """
        Get summary of engineered features
        """
        summary = {"scalers": list(self.scalers.keys()), "feature_selectors": list(self.feature_selectors.keys()), "pca_models": list(self.pca_models.keys()), "feature_importance": self.feature_importance}
        return summary

    def encode_categorical_features(self, df: pd.DataFrame, categorical_cols: List[str] = None) -> pd.DataFrame:
        """
        Encode categorical features using label encoding
        """
        df = df.copy()
        if categorical_cols is None:
            categorical_cols = ["chr", "gene"]
        for col in categorical_cols:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    unique_values = df[col].unique()
                    self.label_encoders[col].fit(unique_values)
                df[col] = self.label_encoders[col].transform(df[col])
        return df

    def load_word2vec_models(self, ref_model_path: str = None, alt_model_path: str = None):
        """
        Load pre-trained Word2Vec models for ref and alt sequences
        """
        if ref_model_path is None:
            ref_model_path = "models/global_models/ref_word2vec.model"
        if alt_model_path is None:
            alt_model_path = "models/global_models/alt_word2vec.model"
        if os.path.exists(ref_model_path):
            self.word2vec_models["ref"] = Word2Vec.load(ref_model_path)
            print(f"✅ Loaded ref Word2Vec model from {ref_model_path}")
        else:
            print(f"⚠️ Ref Word2Vec model not found at {ref_model_path}")
        if os.path.exists(alt_model_path):
            self.word2vec_models["alt"] = Word2Vec.load(alt_model_path)
            print(f"✅ Loaded alt Word2Vec model from {alt_model_path}")
        else:
            print(f"⚠️ Alt Word2Vec model not found at {alt_model_path}")

    def create_kmer_generator(self, k: int = 3):
        """
        Create k-mer generator for sequence processing
        """
        self.kmer_generator = KmerGenerator(k=k)

    def embed_ref_alt_sequences(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create one-hot encodings for ref and alt sequences
        """
        df = df.copy()

        def one_hot_encode_sequence(seq):
            """One-hot encode a DNA sequence"""
            if seq is None or pd.isna(seq):
                return np.zeros(4)  # 4 nucleotides: A, T, G, C

            seq = str(seq).upper()
            # Simple one-hot encoding: A=0, T=1, G=2, C=3
            nucleotide_to_idx = {"A": 0, "T": 1, "G": 2, "C": 3}

            # For single nucleotides, return one-hot encoding
            if len(seq) == 1:
                one_hot = np.zeros(4)
                if seq in nucleotide_to_idx:
                    one_hot[nucleotide_to_idx[seq]] = 1
                return one_hot

            # For longer sequences, average the one-hot encodings
            encodings = []
            for char in seq:
                if char in nucleotide_to_idx:
                    one_hot = np.zeros(4)
                    one_hot[nucleotide_to_idx[char]] = 1
                    encodings.append(one_hot)

            if encodings:
                return np.mean(encodings, axis=0)
            else:
                return np.zeros(4)

        # Embed ref sequences
        if "ref" in df.columns:
            ref_embeddings = df["ref"].apply(one_hot_encode_sequence)
            ref_emb_df = pd.DataFrame(ref_embeddings.tolist(), columns=["ref_A", "ref_T", "ref_G", "ref_C"], index=df.index)
            df = pd.concat([df, ref_emb_df], axis=1)

        # Embed alt sequences
        if "alt" in df.columns:
            alt_embeddings = df["alt"].apply(one_hot_encode_sequence)
            alt_emb_df = pd.DataFrame(alt_embeddings.tolist(), columns=["alt_A", "alt_T", "alt_G", "alt_C"], index=df.index)
            df = pd.concat([df, alt_emb_df], axis=1)

        return df


class AdvancedEmbeddingGenerator:
    """
    Advanced embedding generation for genomic sequences
    """

    def __init__(self, embedding_dim=128, k_mer_sizes=[3, 4, 5]):
        self.embedding_dim = embedding_dim
        self.k_mer_sizes = k_mer_sizes
        self.embeddings = {}

    def generate_kmer_embeddings(self, sequences: List[str], k: int) -> np.ndarray:
        """
        Generate k-mer based embeddings
        """
        # Generate all possible k-mers
        kmers = set()
        for seq in sequences:
            for i in range(len(seq) - k + 1):
                kmers.add(seq[i : i + k])

        # Create embedding matrix
        kmer_to_idx = {kmer: idx for idx, kmer in enumerate(kmers)}
        embeddings = np.random.randn(len(kmers), self.embedding_dim)

        # Normalize embeddings
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        return embeddings, kmer_to_idx

    def embed_sequence(self, sequence: str, embeddings: np.ndarray, kmer_to_idx: Dict, k: int) -> np.ndarray:
        """
        Embed a single sequence using k-mer embeddings
        """
        sequence_embeddings = []
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i : i + k]
            if kmer in kmer_to_idx:
                sequence_embeddings.append(embeddings[kmer_to_idx[kmer]])

        if sequence_embeddings:
            return np.mean(sequence_embeddings, axis=0)
        else:
            return np.zeros(self.embedding_dim)

    def create_multi_scale_embeddings(self, ref_sequences: List[str], alt_sequences: List[str]) -> Dict:
        """
        Create multi-scale embeddings for ref and alt sequences
        """
        embeddings_dict = {}

        for k in self.k_mer_sizes:
            print(f"  🔤 Generating {k}-mer embeddings...")

            # Generate embeddings for ref sequences
            ref_embeddings, ref_kmer_to_idx = self.generate_kmer_embeddings(ref_sequences, k)
            alt_embeddings, alt_kmer_to_idx = self.generate_kmer_embeddings(alt_sequences, k)

            # Embed all sequences
            ref_embedded = np.array([self.embed_sequence(seq, ref_embeddings, ref_kmer_to_idx, k) for seq in ref_sequences])
            alt_embedded = np.array([self.embed_sequence(seq, alt_embeddings, alt_kmer_to_idx, k) for seq in alt_sequences])

            embeddings_dict[f"k{k}_ref"] = ref_embedded
            embeddings_dict[f"k{k}_alt"] = alt_embedded

        return embeddings_dict
