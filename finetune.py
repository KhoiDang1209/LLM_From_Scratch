import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import (
    prepare_model_for_kbit_training,
    LoraConfig,
    get_peft_model
)
from trl import SFTTrainer
from datasets import load_from_disk
from transformers.utils import logging
logging.set_verbosity_info()

# 1. Model ID
model_id = "Viet-Mistral/Vistral-7B-Chat"

# 2. Configure 8-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_use_double_quant=True,
    bnb_8bit_quant_type="nf8",
    bnb_8bit_compute_dtype=torch.float16
)

# 3. Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
# Set padding token if not set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    quantization_config=bnb_config,
    trust_remote_code=True
)

# 4. Prepare model for PEFT + LoRA
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)

# Configure LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
)

# Apply LoRA
model = get_peft_model(model, lora_config)

# Load the prepared dataset
dataset = load_from_disk("/content/sample_instruction_following_dataset")

# Configure training arguments
training_args = TrainingArguments(
    output_dir="./vistral-lora-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    warmup_ratio=0.1,
    weight_decay=0.01,
    max_grad_norm=0.3,
    report_to="none"  # Disable WandB if not used
)

# Initialize the trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
    packing=True  # Enable packing for more efficient training
)

# Start training
trainer.train()

# Save the final model and tokenizer
model.save_pretrained("./vistral-lora-checkpoint")
tokenizer.save_pretrained("./vistral-lora-checkpoint") 