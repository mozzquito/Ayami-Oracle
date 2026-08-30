import Foundation

/// Temporary plain-file logger for local debugging (unified `log show` was
/// unreliable for NSLog lines from this process during testing). Remove once
/// the Input Monitoring / playback flow is confirmed working.
enum DebugLog {
    static let path = "/tmp/quack-debug-app.log"

    static func write(_ message: String) {
        let line = "\(Date()) \(message)\n"
        NSLog("%@", message)
        guard let data = line.data(using: .utf8) else { return }
        if FileManager.default.fileExists(atPath: path) {
            if let handle = FileHandle(forWritingAtPath: path) {
                handle.seekToEndOfFile()
                handle.write(data)
                try? handle.close()
            }
        } else {
            try? data.write(to: URL(fileURLWithPath: path))
        }
    }
}
