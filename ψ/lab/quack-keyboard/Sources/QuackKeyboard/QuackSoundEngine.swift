import AVFoundation

/// Plays a random duck quack per keystroke using a small pool of AVAudioPlayer
/// instances so rapid typing doesn't cut sounds off mid-quack.
final class QuackSoundEngine {
    private var soundData: [Data] = []
    private var playerPool: [AVAudioPlayer] = []
    private var poolIndex = 0
    private let poolSize = 6

    var volume: Float = 0.8

    init() {
        loadSounds()
    }

    var hasSounds: Bool { !soundData.isEmpty }

    private func loadSounds() {
        guard let resourceURL = Bundle.main.resourceURL else {
            DebugLog.write("loadSounds: Bundle.main.resourceURL is nil")
            return
        }
        let soundsDir = resourceURL.appendingPathComponent("Sounds")
        let fm = FileManager.default
        guard let files = try? fm.contentsOfDirectory(at: soundsDir, includingPropertiesForKeys: nil) else {
            DebugLog.write("loadSounds: could not list \(soundsDir.path)")
            return
        }
        let audioFiles = files.filter { ["wav", "caf", "m4a", "aiff", "mp3"].contains($0.pathExtension.lowercased()) }
        for url in audioFiles {
            if let data = try? Data(contentsOf: url) {
                soundData.append(data)
            }
        }
        DebugLog.write("loadSounds: loaded \(soundData.count) file(s) from \(soundsDir.path)")
    }

    func playRandomQuack() {
        guard let data = soundData.randomElement() else {
            DebugLog.write("playRandomQuack called but soundData is empty")
            return
        }
        guard let player = try? AVAudioPlayer(data: data) else {
            DebugLog.write("AVAudioPlayer(data:) failed to init")
            return
        }
        player.volume = volume
        player.enableRate = true
        player.rate = Float.random(in: 0.92...1.08)
        player.prepareToPlay()
        let started = player.play()
        DebugLog.write("play() started=\(started) volume=\(volume)")

        // Keep a strong reference until it finishes; cycling a fixed-size pool
        // avoids unbounded growth while still allowing overlapping playback.
        if playerPool.count < poolSize {
            playerPool.append(player)
        } else {
            playerPool[poolIndex] = player
            poolIndex = (poolIndex + 1) % poolSize
        }
    }
}
