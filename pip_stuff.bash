#!/bin/bash

echo "Setting up Conda environment for RAG pipeline..."

# Step 1: Create a new Conda environment called 'ai'
echo "Creating 'ai' environment..."
conda create -n ai -y python=3.9

# Step 2: Activate the 'ai' environment
echo "Activating 'ai' environment..."
conda activate ai

# Step 3: Install required libraries
echo "Installing required libraries for RAG pipeline..."
pip install torch numpy transformers scikit-learn pandas networkx sqlite3

# Step 4: Download pre-trained models for Roberta
echo "Downloading pre-trained Roberta model..."
python -c "
from transformers import RobertaTokenizer, RobertaModel
RobertaTokenizer.from_pretrained('roberta-base')
RobertaModel.from_pretrained('roberta-base')
"

# Step 5: Verify installation
echo "Verifying installations..."
pip list

echo "RAG pipeline environment setup is complete! Activate it using 'conda activate ai'."
