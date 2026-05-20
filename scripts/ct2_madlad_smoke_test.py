import argparse
from pathlib import Path

import ctranslate2
from huggingface_hub import snapshot_download
from sentencepiece import SentencePieceProcessor


DEFAULT_REPO_ID = "Heng666/madlad400-3b-mt-ct2-int8"
DEFAULT_MODEL_DIR = "models/madlad400-3b-mt-ct2-int8"


def download_model(repo_id: str, model_dir: str) -> Path:
    model_path = Path(model_dir)

    print(f"Model repo: {repo_id}")
    print(f"Local model path: {model_path}")

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(model_path),
        allow_patterns=[
            "config.json",
            "model.bin",
            "shared_vocabulary.json",
            "spiece.model",
        ],
    )

    return model_path


def load_tokenizer(model_path: Path) -> SentencePieceProcessor:
    tokenizer_path = model_path / "spiece.model"

    if not tokenizer_path.exists():
        raise FileNotFoundError(f"Tokenizer bulunamadı: {tokenizer_path}")

    tokenizer = SentencePieceProcessor()
    tokenizer.load(str(tokenizer_path))
    return tokenizer


def translate_text(
    model_path: Path,
    text: str,
    target_lang: str,
    device: str,
    compute_type: str,
) -> str:
    tokenizer = load_tokenizer(model_path)

    translator = ctranslate2.Translator(
        str(model_path),
        device=device,
        compute_type=compute_type,
    )

    # MADLAD/Mia formatında hedef dil etiketi input başına eklenir.
    # Örnek: <2en> Merhaba
    input_text = f"<2{target_lang}> {text}"
    input_tokens = tokenizer.encode(input_text, out_type=str)

    results = translator.translate_batch(
        [input_tokens],
        beam_size=1,
        max_decoding_length=128,
        repetition_penalty=2,
        no_repeat_ngram_size=1,
    )

    output_tokens = results[0].hypotheses[0]
    translated_text = tokenizer.decode(output_tokens)

    return translated_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MADLAD CTranslate2 int8 smoke test."
    )

    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help="Hugging Face CTranslate2 model repo id.",
    )
    parser.add_argument(
        "--model-dir",
        default=DEFAULT_MODEL_DIR,
        help="Local model directory.",
    )
    parser.add_argument(
        "--text",
        default="Merhaba, nasılsın?",
        help="Text to translate.",
    )
    parser.add_argument(
        "--target-lang",
        default="en",
        help="Target language code. Example: en, tr, ar, de, fr",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device: cpu or cuda",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="Compute type. For this PC first try int8 on CPU.",
    )

    args = parser.parse_args()

    model_path = download_model(args.repo_id, args.model_dir)

    print()
    print("Smoke test başlıyor...")
    print(f"Input: {args.text}")
    print(f"Target language: {args.target_lang}")
    print(f"Device: {args.device}")
    print(f"Compute type: {args.compute_type}")

    translated_text = translate_text(
        model_path=model_path,
        text=args.text,
        target_lang=args.target_lang,
        device=args.device,
        compute_type=args.compute_type,
    )

    print()
    print("Çeviri sonucu")
    print("-------------")
    print(translated_text)


if __name__ == "__main__":
    main()