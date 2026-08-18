"""Launch the animal-sound spectral analyzer desktop application (item 8).

Requires the optional GUI dependencies: `customtkinter`, `librosa`,
`soundfile`. Drop recordings into `audio_samples/<gato|perro|gallo>/`
before loading them from the app (see `readme.md`).
"""

from animal_analyzer.gui import main

if __name__ == "__main__":
    main()
