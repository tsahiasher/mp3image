// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ID3Editor",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "ID3Editor", targets: ["ID3Editor"])
    ],
    dependencies: [
        .package(url: "https://github.com/chicio/ID3TagEditor.git", from: "4.0.0")
    ],
    targets: [
        .executableTarget(
            name: "ID3Editor",
            dependencies: [
                .product(name: "ID3TagEditor", package: "ID3TagEditor")
            ],
            path: "Sources/ID3Editor",
            resources: [
                .process("ID3Editor.xcassets")
            ]
        )
    ]
)
