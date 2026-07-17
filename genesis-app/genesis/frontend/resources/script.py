import time
import random

EPOCHS = 10
BATCHES = 20

print("Starting fake training...", flush=True)

for epoch in range(1, EPOCHS + 1):
    epoch_loss = 0.0
    epoch_acc = 0.0

    for batch in range(1, BATCHES + 1):
        # Simulate batch training time
        time.sleep(0.15)  # ~0.15s per batch → ~30s total

        # Fake metrics
        loss = round(random.uniform(0.2, 1.0), 4)
        acc = round(random.uniform(60, 95), 2)

        epoch_loss += loss
        epoch_acc += acc

        # Progress percentage
        progress = int(((epoch - 1) * BATCHES + batch) / (EPOCHS * BATCHES) * 100)

        # Print log line (stdout, flushed)
        print(f"[Epoch {epoch}/{EPOCHS}] Batch {batch}/{BATCHES} "
              f"-> loss={loss}, acc={acc}% | progress={progress}%", flush=True)

    avg_loss = round(epoch_loss / BATCHES, 4)
    avg_acc = round(epoch_acc / BATCHES, 2)
    print(f"Completed Epoch {epoch} | avg_loss={avg_loss}, avg_acc={avg_acc}%", flush=True)

print("Training finished successfully!", flush=True)
