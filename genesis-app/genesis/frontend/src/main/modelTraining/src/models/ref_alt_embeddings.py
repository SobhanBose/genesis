import pandas as pd
from gensim.models import Word2Vec
import os

class KmerGenerator:
    """Generate k-mers from DNA sequences"""
    
    def __init__(self, k=3):
        self.k = k
    
    def generate_kmers(self, sequence):
        """Generate k-mers from a sequence"""
        if len(sequence) < self.k:
            return [sequence]
        
        kmers = []
        for i in range(len(sequence) - self.k + 1):
            kmers.append(sequence[i:i + self.k])
        return kmers
    
    def sequences_to_kmers(self, sequences):
        """Convert list of sequences to list of k-mer lists"""
        all_kmers = []
        for seq in sequences:
            kmers = self.generate_kmers(str(seq).upper())
            all_kmers.append(kmers)
        return all_kmers

class Word2VecModelTrainer:
    """Separate class for training and managing Word2Vec models"""
    
    def __init__(self, vector_size=50, window=3, min_count=1, workers=4, k=3):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.workers = workers
        self.k = k
        self.kmer_gen = KmerGenerator(k=k)
    
    def train_model(self, sequences, model_name="word2vec_model"):
        """Train Word2Vec model on sequences"""
        print(f"Training Word2Vec model: {model_name}")
        print(f"Training on {len(sequences)} sequences...")
        
        # Generate k-mers
        kmers_list = self.kmer_gen.sequences_to_kmers(sequences)
        
        # Train Word2Vec model
        model = Word2Vec(
            sentences=kmers_list,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            workers=self.workers,
            sg=1  # Skip-gram
        )
        
        print(f"Model '{model_name}' trained with vocabulary size: {len(model.wv.key_to_index)}")
        return model
    
    def save_model(self, model, filepath):
        """Save Word2Vec model"""
        model.save(filepath)
        print(f"Word2Vec model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load Word2Vec model"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Word2Vec model not found at {filepath}")
        model = Word2Vec.load(filepath)
        print(f"Word2Vec model loaded from {filepath}")
        return model

def train_and_save_word2vec_models(df, output_dir="../../models/global_models/", vector_size=50, window=3, k=3):
    """Train and save Word2Vec models for Ref and Alt columns"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    trainer = Word2VecModelTrainer(vector_size=vector_size, window=window, k=k)
    
    # Train model for 'ref' column
    print("Training Word2Vec model for 'ref' column...")
    ref_sequences = df['Ref'].dropna().tolist()
    ref_model = trainer.train_model(ref_sequences, "ref_word2vec")
    ref_model_path = os.path.join(output_dir, "ref_word2vec.model")
    trainer.save_model(ref_model, ref_model_path)
    
    # Train model for 'alt' column
    print("Training Word2Vec model for 'alt' column...")
    alt_sequences = df['Alt'].dropna().tolist()
    alt_model = trainer.train_model(alt_sequences, "alt_word2vec")
    alt_model_path = os.path.join(output_dir, "alt_word2vec.model")
    trainer.save_model(alt_model, alt_model_path)
    
    return ref_model_path, alt_model_path

def main():
    df = pd.read_csv('../../data/raw/train.csv')

    ref_model_path, alt_model_path = train_and_save_word2vec_models(
        df, output_dir="../../models/global_models/", vector_size=50, window=3, k=3
    )


if __name__ == "__main__":
    main()