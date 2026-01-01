import os

# -----------------------------
# Performance: limit CPU threads
# -----------------------------
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"

from flask import Flask, request, render_template, jsonify
from flask_cors import CORS

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# -----------------------------
# Flask app setup
# -----------------------------
app = Flask(__name__)
CORS(app)

# -----------------------------
# Model configuration
# -----------------------------
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="cpu",
    torch_dtype=torch.float32,
    trust_remote_code=True
)

# Se o tokenizer não tiver pad_token, usamos o eos_token
if tokenizer.pad_token_id is None:
    tokenizer.pad_token = tokenizer.eos_token

# Limit PyTorch CPU threads
torch.set_num_threads(2)

# -----------------------------
# Conversation memory
# -----------------------------
conversation_history = [
    {"role": "system", "content": "Reply in a helpful and detailed way. Use steps and examples when useful."}
]

MAX_TURNS = 4  # 4 turns = 8 messages (user+assistant)

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json(force=True) or {}
    user_text = (data.get("prompt") or "").strip()

    if not user_text:
        return jsonify({"response": "Envie um texto em 'prompt'."}), 400

    # 1) Add user message
    conversation_history.append({"role": "user", "content": user_text})

    # 2) Keep only last turns (system + last 2*MAX_TURNS messages)
    if len(conversation_history) > 1 + (MAX_TURNS * 2):
        conversation_history[:] = [conversation_history[0]] + conversation_history[-(MAX_TURNS * 2):]

    # 3) Tokenize with chat template
    input_ids = tokenizer.apply_chat_template(
        conversation_history,
        add_generation_prompt=True,
        return_tensors="pt"
    )

    # (CPU) garantir que está no mesmo device do model
    input_ids = input_ids.to(model.device)

    # 4) Generate response
    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=400,          # <- CORRIGIDO
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.pad_token_id
        )

    # 5) Decode only newly generated tokens
    new_tokens = output_ids[0][input_ids.shape[-1]:]
    assistant_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    # 6) Add assistant message
    conversation_history.append({"role": "assistant", "content": assistant_text})

    # 7) Limit again
    if len(conversation_history) > 1 + (MAX_TURNS * 2):
        conversation_history[:] = [conversation_history[0]] + conversation_history[-(MAX_TURNS * 2):]

    return jsonify({"response": assistant_text})


if __name__ == "__main__":
    # use_reloader=False evita carregar o modelo duas vezes
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
