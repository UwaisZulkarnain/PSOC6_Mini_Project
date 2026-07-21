WAV files are gitignored and not stored in the repository.

After cloning, generate them by running from the host/ directory:

    python make_samples.py

This will create: kick.wav, snare.wav, hihat_closed.wav, hihat_open.wav,
crash.wav, tom.wav, ride.wav

Replace any of these files with recorded samples if desired — keep the
same filename and format (mono, 44100 Hz, 16-bit PCM).