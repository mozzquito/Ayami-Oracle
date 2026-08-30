// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "QuackKeyboard",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "QuackKeyboard",
            path: "Sources/QuackKeyboard"
        )
    ]
)
