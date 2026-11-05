"""Run Hugging Face models with inputs from the command line or a prompt.

Setup:
    uv sync --extra hf

Optional login (needed for private or gated models):
    export HF_TOKEN=your_token_here

Examples:
    uv run python scripts/hf_pipeline_demo.py sentiment "This setup is easy."
    uv run python scripts/hf_pipeline_demo.py generate "Once upon a time" --max-new-tokens 40
    uv run python scripts/hf_pipeline_demo.py summarize "Paste a long text here."
    uv run python scripts/hf_pipeline_demo.py classify "I need a refund" \
        --labels billing,support,sales
    uv run python scripts/hf_pipeline_demo.py sentiment            (interactive mode)
"""

import argparse
import os
import sys

from huggingface_hub import login
from transformers import pipeline

# Each task name maps to a pipeline type and a small default model.
TASKS = {
    "sentiment": (
        "sentiment-analysis",
        "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    ),
    "generate": ("text-generation", "distilgpt2"),
    "summarize": ("summarization", "sshleifer/distilbart-cnn-12-6"),
    "classify": ("zero-shot-classification", "facebook/bart-large-mnli"),
}


def parse_args():
    parser = argparse.ArgumentParser(description="Run a Hugging Face model.")
    parser.add_argument("task", choices=TASKS.keys(), help="The task to run.")
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Input text. If you omit it, the script asks for input.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID from the Hub. This replaces the default model.",
    )
    parser.add_argument(
        "--labels",
        default="positive,negative,neutral",
        help="Comma-separated labels. Used only with the classify task.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=50,
        help="Length limit for the generate task.",
    )
    return parser.parse_args()


def run_once(pipe, args, text):
    """Run the model one time and print the result."""
    if args.task == "generate":
        result = pipe(text, max_new_tokens=args.max_new_tokens, do_sample=True)
        print(result[0]["generated_text"])
    elif args.task == "summarize":
        result = pipe(text, max_length=60, min_length=10, truncation=True)
        print(result[0]["summary_text"])
    elif args.task == "classify":
        labels = [label.strip() for label in args.labels.split(",")]
        result = pipe(text, candidate_labels=labels)
        for label, score in zip(result["labels"], result["scores"], strict=True):
            print(f"{label}: {score:.3f}")
    else:
        result = pipe(text)[0]
        print(f"{result['label']}: {result['score']:.3f}")


def main():
    args = parse_args()

    # Log in only if a token is set.
    token = os.environ.get("HF_TOKEN")
    if token:
        login(token=token)

    pipeline_name, default_model = TASKS[args.task]
    model_id = args.model or default_model

    print(f"Loading model: {model_id}")
    pipe = pipeline(pipeline_name, model=model_id)

    # One-shot mode: the user gave the text on the command line.
    if args.text:
        run_once(pipe, args, args.text)
        return

    # Interactive mode: ask for text until the user types quit or presses Enter.
    print("Type your text and press Enter. Type quit or press Enter on an empty line to stop.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text or text.lower() == "quit":
            break
        run_once(pipe, args, text)


if __name__ == "__main__":
    sys.exit(main())
