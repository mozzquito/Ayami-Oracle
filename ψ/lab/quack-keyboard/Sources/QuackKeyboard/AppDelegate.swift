import AppKit
import IOKit.hid

final class AppDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private var globalMonitor: Any?
    private var localMonitor: Any?
    private let soundEngine = QuackSoundEngine()

    private var enabledMenuItem: NSMenuItem!

    private var isEnabled = true {
        didSet {
            UserDefaults.standard.set(isEnabled, forKey: "quack.enabled")
            enabledMenuItem?.state = isEnabled ? .on : .off
            statusItem?.button?.appearsDisabled = !isEnabled
            updateMonitors()
        }
    }

    private var volume: Float = 0.8 {
        didSet {
            soundEngine.volume = volume
            UserDefaults.standard.set(volume, forKey: "quack.volume")
        }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        DebugLog.write("applicationDidFinishLaunching")
        let defaults = UserDefaults.standard
        volume = defaults.object(forKey: "quack.volume") as? Float ?? 0.8
        soundEngine.volume = volume

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        statusItem.button?.title = "🦆"

        buildMenu()

        // Set after buildMenu so the didSet side effects (menu state, monitors) run once UI exists.
        isEnabled = defaults.object(forKey: "quack.enabled") as? Bool ?? true

        if !soundEngine.hasSounds {
            NSLog("QuackKeyboard: no sound files found in Resources/Sounds — bundle a few .wav quacks before shipping.")
        }

        // Give the NSEvent global monitor's own internal Input Monitoring request
        // (triggered from updateMonitors() above) a moment to land before we do our
        // own read-only status check, so the two don't race.
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            self?.checkInputMonitoringPermission()
        }
    }

    private func buildMenu() {
        let menu = NSMenu()

        enabledMenuItem = NSMenuItem(title: "เปิดเสียงเป็ด", action: #selector(toggleEnabled), keyEquivalent: "")
        enabledMenuItem.target = self
        menu.addItem(enabledMenuItem)

        menu.addItem(.separator())

        let volumeItem = NSMenuItem()
        let container = NSView(frame: NSRect(x: 0, y: 0, width: 200, height: 24))
        let slider = NSSlider(value: Double(volume), minValue: 0, maxValue: 1,
                               target: self, action: #selector(volumeChanged(_:)))
        slider.frame = NSRect(x: 20, y: 2, width: 160, height: 20)
        container.addSubview(slider)
        volumeItem.view = container
        menu.addItem(volumeItem)

        menu.addItem(.separator())

        let permItem = NSMenuItem(title: "เปิด Input Monitoring Settings…",
                                   action: #selector(openPermissionSettings), keyEquivalent: "")
        permItem.target = self
        menu.addItem(permItem)

        menu.addItem(.separator())

        let quitItem = NSMenuItem(title: "ออกจากโปรแกรม", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

        statusItem.menu = menu
    }

    @objc private func toggleEnabled() {
        isEnabled.toggle()
    }

    @objc private func volumeChanged(_ sender: NSSlider) {
        volume = Float(sender.doubleValue)
    }

    @objc private func openPermissionSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent") {
            NSWorkspace.shared.open(url)
        }
    }

    @objc private func quit() {
        NSApp.terminate(nil)
    }

    private func updateMonitors() {
        removeMonitors()
        guard isEnabled else { return }
        DebugLog.write("installing key monitors")
        // Global monitor covers keystrokes in other apps; local covers keystrokes
        // while this app's own menu/UI has focus (global monitor doesn't fire then).
        globalMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            DebugLog.write("global keyDown fired (keyCode=\(event.keyCode))")
            self?.soundEngine.playRandomQuack()
        }
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            DebugLog.write("local keyDown fired (keyCode=\(event.keyCode))")
            self?.soundEngine.playRandomQuack()
            return event
        }
    }

    private func removeMonitors() {
        if let m = globalMonitor { NSEvent.removeMonitor(m); globalMonitor = nil }
        if let m = localMonitor { NSEvent.removeMonitor(m); localMonitor = nil }
    }

    private func checkInputMonitoringPermission() {
        // Read-only check, and deliberately NOT paired with IOHIDRequestAccess here:
        // NSEvent.addGlobalMonitorForEvents (called in updateMonitors, just before this)
        // already performs its own internal Input Monitoring TCC request. Calling
        // IOHIDRequestAccess again immediately after is a redundant second request to
        // the same sensitive service within milliseconds, which tccd can treat as abuse
        // and refuse to prompt for ("does not allow prompting; returning denied") even
        // though nothing was actually decided. So: just observe status, don't request.
        let checkResult = IOHIDCheckAccess(kIOHIDRequestTypeListenEvent)
        DebugLog.write("IOHIDCheckAccess -> \(checkResult.rawValue)")

        if checkResult != kIOHIDAccessTypeGranted {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
                self?.showPermissionAlert()
            }
        }
    }

    private func showPermissionAlert() {
        let alert = NSAlert()
        alert.messageText = "ต้องเปิด Input Monitoring ก่อน 🦆"
        alert.informativeText = """
        Quack Keyboard ต้องขอสิทธิ์ฟัง keyboard เพื่อเล่นเสียงเป็ดตอนพิมพ์

        ไปที่ System Settings → Privacy & Security → Input Monitoring แล้วเปิดสวิตช์ให้ Quack Keyboard แล้วเปิดแอปใหม่อีกครั้ง
        """
        alert.addButton(withTitle: "เปิด System Settings")
        alert.addButton(withTitle: "ไว้ทีหลัง")
        if alert.runModal() == .alertFirstButtonReturn {
            openPermissionSettings()
        }
    }
}
