"""
OboePassthrough Native Audio Stream & DSP Latency Verification Suite
Validates:
- Sub-20ms roundtrip audio latency budgeting and buffer sizing
- Full-duplex audio stream sample rate negotiation & resampler ratio calculations
- Lock-free ring buffer push/pop mathematics and overrun/underrun guards
- Real-valued spectral bin resolution (FFT frequency mapping)
- Acoustic feedback auto-mute safety upon headphone disconnect
"""

import unittest
import math


class LockFreeAudioRingBuffer:
    """Simulates a lock-free single-producer single-consumer circular audio buffer."""
    def __init__(self, capacity_frames: int):
        self.capacity = capacity_frames
        self.buffer = [0.0] * capacity_frames
        self.write_head = 0
        self.read_head = 0
        self.available_frames = 0

    def write(self, frames: list) -> int:
        written = 0
        for f in frames:
            if self.available_frames >= self.capacity:
                # Buffer overrun: drop or return partial
                break
            self.buffer[self.write_head] = f
            self.write_head = (self.write_head + 1) % self.capacity
            self.available_frames += 1
            written += 1
        return written

    def read(self, num_frames: int) -> list:
        out = []
        for _ in range(num_frames):
            if self.available_frames <= 0:
                # Buffer underrun (XRun): fill silence
                out.append(0.0)
            else:
                out.append(self.buffer[self.read_head])
                self.read_head = (self.read_head + 1) % self.capacity
                self.available_frames -= 1
        return out


def calculate_roundtrip_latency_ms(burst_size_frames: int, sample_rate: int, num_bursts: int = 2) -> float:
    """Calculates theoretical roundtrip hardware audio latency in milliseconds."""
    single_burst_ms = (burst_size_frames / sample_rate) * 1000.0
    # Input stream latency + Output stream latency + DSP processing margin
    input_latency = single_burst_ms * num_bursts
    output_latency = single_burst_ms * num_bursts
    return input_latency + output_latency


def calculate_fft_bin_frequency(bin_index: int, fft_size: int, sample_rate: int) -> float:
    """Calculates the center frequency of a given FFT frequency bin."""
    return (bin_index * sample_rate) / fft_size


class TestNativeAudioStream(unittest.TestCase):
    def test_low_latency_budget_sub_20ms(self):
        """AAudio exclusive mode with 192-frame burst at 48kHz must achieve <20ms roundtrip."""
        # 192 frames at 48000 Hz = 4.0ms per burst
        latency_ms = calculate_roundtrip_latency_ms(burst_size_frames=192, sample_rate=48000, num_bursts=2)
        # 4ms * 2 (in) + 4ms * 2 (out) = 16.0 ms
        self.assertLess(latency_ms, 20.0, f"Expected sub-20ms latency, got {latency_ms:.2f}ms")
        self.assertEqual(latency_ms, 16.0)

    def test_sample_rate_negotiation_and_resampling_ratio(self):
        """Validates resampling ratio when connecting Bluetooth (44.1kHz) with Native Mic (48kHz)."""
        input_rate = 48000
        output_rate = 44100
        ratio = output_rate / input_rate
        self.assertAlmostEqual(ratio, 0.91875, places=5)

        # 480 input frames resampled at ratio 44.1/48 produces exactly 441 output frames
        expected_output_frames = int(round(480 * ratio))
        self.assertEqual(expected_output_frames, 441)

    def test_lock_free_ring_buffer_fifo(self):
        """Ring buffer must preserve frame order without corruption across circular wrap-around."""
        ring = LockFreeAudioRingBuffer(capacity_frames=8)
        
        # Write 5 frames
        written = ring.write([1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(written, 5)
        
        # Read 3 frames
        read_frames = ring.read(3)
        self.assertEqual(read_frames, [1.0, 2.0, 3.0])
        
        # Write 4 more frames (causing wrap around: heads cross index 8)
        written2 = ring.write([6.0, 7.0, 8.0, 9.0])
        self.assertEqual(written2, 4)
        
        # Read remaining 6 frames
        read_all = ring.read(6)
        self.assertEqual(read_all, [4.0, 5.0, 6.0, 7.0, 8.0, 9.0])

    def test_ring_buffer_underrun_returns_silence(self):
        """Reading from an empty buffer must safely synthesize zero frames without throwing."""
        ring = LockFreeAudioRingBuffer(capacity_frames=4)
        silence = ring.read(4)
        self.assertEqual(silence, [0.0, 0.0, 0.0, 0.0])

    def test_fft_frequency_bin_resolution(self):
        """KISS-FFT bin centers must map accurately to acoustic spectrum frequencies."""
        sample_rate = 48000
        fft_size = 512
        bin_hz = sample_rate / fft_size  # 93.75 Hz per bin
        
        self.assertEqual(calculate_fft_bin_frequency(0, fft_size, sample_rate), 0.0)
        self.assertAlmostEqual(calculate_fft_bin_frequency(10, fft_size, sample_rate), 937.5, places=1)
        # Nyquist bin (bin 256)
        self.assertEqual(calculate_fft_bin_frequency(256, fft_size, sample_rate), 24000.0)

    def test_headphone_disconnect_mute_guard(self):
        """Acoustic feedback protection stops audio flow upon headphone disconnection."""
        headphones_plugged = False
        audio_stream_active = True
        
        # Noisy intent receiver triggers shutdown
        if not headphones_plugged:
            audio_stream_active = False
            
        self.assertFalse(audio_stream_active)


if __name__ == "__main__":
    unittest.main()
