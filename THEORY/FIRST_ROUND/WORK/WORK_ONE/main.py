"""CLI entry point: generate and play a DTMF dial-tone WAV file for a phone number.

Usage:
    python main.py 7004191
    python main.py            # prompts interactively if no argument is given
"""

import os
import sys

from dtmf_dialer import DTMF_FREQUENCIES, generate_dtmf_sequence, play_wav, save_wav

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def get_phone_number() -> str:
    """Read the phone number to dial from the CLI argument, or prompt for it.

    Returns:
        The raw digit string entered by the user.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return input("Enter a phone number (digits 0-9): ").strip()


def main() -> None:
    """Generate, save, and play a dial-tone WAV file for a user-supplied number."""
    number = get_phone_number()
    valid_digits = "".join(d for d in number if d in DTMF_FREQUENCIES)
    if not valid_digits:
        print("No valid digits (0-9) found in the input. Nothing to dial.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    samples = generate_dtmf_sequence(valid_digits)
    output_path = os.path.join(OUTPUT_DIR, f"dial_{valid_digits}.wav")
    save_wav(samples, output_path)
    print(f"File generated successfully at: {output_path}")
    print(f"Playing dial tones for {valid_digits}...")
    play_wav(output_path)


if __name__ == "__main__":
    main()
