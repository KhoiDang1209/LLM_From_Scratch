import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from datasets import load_from_disk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import numpy as np
from tqdm import tqdm
import json
import re

def load_model_and_tokenizer(base_model_name, adapter_path):
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    model = PeftModel.from_pretrained(model, adapter_path)
    return model, tokenizer

def extract_prompt_and_response(text):
    # Extract prompt from [INST] tags
    prompt_match = re.search(r'\[INST\](.*?)\[/INST\]', text)
    if prompt_match:
        prompt = prompt_match.group(1).strip()
    else:
        prompt = ""
    
    # Extract response after [/INST]
    response_match = re.search(r'\[/INST\](.*?)(?:</s>|$)', text, re.DOTALL)
    if response_match:
        response = response_match.group(1).strip()
    else:
        response = ""
    
    return prompt, response

def generate_response(model, tokenizer, prompt, max_new_tokens=256):  # Reduced max tokens
    messages = [{"role": "user", "content": prompt}]
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Disabled sampling for faster generation
            num_beams=1,  # Use greedy search
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response.split("Assistant: ")[-1].strip()
    return response

def calculate_metrics(predictions, references):
    # Initialize metrics
    bleu_scores = []
    rouge_scores = {
        'rouge1': [],
        'rouge2': [],
        'rougeL': []
    }
    
    # Initialize ROUGE scorer
    rouge_scorer_obj = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    smoothie = SmoothingFunction().method1
    
    # Calculate metrics for each prediction-reference pair
    for pred, ref in zip(predictions, references):
        # BLEU Score
        bleu_score = sentence_bleu([ref.split()], pred.split(), smoothing_function=smoothie)
        bleu_scores.append(bleu_score)
        
        # ROUGE Scores
        scores = rouge_scorer_obj.score(ref, pred)
        for metric in rouge_scores.keys():
            rouge_scores[metric].append(scores[metric].fmeasure)
    
    # Calculate averages
    metrics = {
        'bleu': np.mean(bleu_scores),
        'rouge1': np.mean(rouge_scores['rouge1']),
        'rouge2': np.mean(rouge_scores['rouge2']),
        'rougeL': np.mean(rouge_scores['rougeL'])
    }
    
    return metrics

def evaluate_model(model, tokenizer, test_dataset, num_samples=None):
    predictions = []
    references = []
    prompts = []
    
    # If num_samples is provided, limit the evaluation
    if num_samples:
        test_dataset = test_dataset.select(range(min(num_samples, len(test_dataset))))
    
    print("Generating predictions...")
    for item in tqdm(test_dataset):
        # Extract prompt and reference from the text field
        prompt, reference = extract_prompt_and_response(item['text'])
        
        if prompt and reference:  # Only process if both prompt and reference are found
            # Generate prediction
            prediction = generate_response(model, tokenizer, prompt)
            
            predictions.append(prediction)
            references.append(reference)
            prompts.append(prompt)
    
    # Calculate metrics
    print("Calculating metrics...")
    metrics = calculate_metrics(predictions, references)
    
    return metrics, predictions, references, prompts

def save_results(metrics, predictions, references, prompts, output_file):
    results = {
        'metrics': metrics,
        'examples': [
            {
                'prompt': p,
                'prediction': pred,
                'reference': ref
            }
            for p, pred, ref in zip(prompts, predictions, references)
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def main():
    # Model paths
    base_model_name = "Viet-Mistral/Vistral-7B-Chat"
    adapter_path = "./vistral-lora-checkpoint"
    
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer(base_model_name, adapter_path)
    
    # Load test dataset
    print("Loading test dataset...")
    test_dataset = load_from_disk("/content/sample_instruction_following_dataset")
    
    # Evaluate model
    print("Starting evaluation...")
    metrics, predictions, references, prompts = evaluate_model(
        model, 
        tokenizer, 
        test_dataset,
        num_samples=20  # Reduced number of samples for faster evaluation
    )
    
    # Print metrics
    print("\nEvaluation Metrics:")
    print(f"BLEU Score: {metrics['bleu']:.4f}")
    print(f"ROUGE-1: {metrics['rouge1']:.4f}")
    print(f"ROUGE-2: {metrics['rouge2']:.4f}")
    print(f"ROUGE-L: {metrics['rougeL']:.4f}")
    
    # Save results
    save_results(metrics, predictions, references, prompts, "evaluation_results.json")
    print("\nResults saved to evaluation_results.json")

if __name__ == "__main__":
    main() 